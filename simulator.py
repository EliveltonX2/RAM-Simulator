import copy
from typing import List, Dict, Any, Tuple, Optional

class MemoryBlock:
    def __init__(self, start: int, size: int, is_allocated: bool = False, process_id: str = None):
        self.start = start
        self.size = size
        self.is_allocated = is_allocated
        self.process_id = process_id

    @property
    def end(self) -> int:
        return self.start + self.size

    def __repr__(self) -> str:
        status = f"Processo {self.process_id}" if self.is_allocated else "Livre"
        return f"[{self.start}-{self.end}] ({self.size}) - {status}"

    def clone(self) -> 'MemoryBlock':
        return MemoryBlock(self.start, self.size, self.is_allocated, self.process_id)


class MemorySimulator:
    def __init__(self, total_size: int):
        self.total_size = total_size
        # A memória começa com um único grande bloco livre
        self.initial_block = MemoryBlock(start=0, size=total_size, is_allocated=False)
        self.blocks: List[MemoryBlock] = [self.initial_block]
        
        # Histórico de estados para navegação passo a passo
        # Cada item: {
        #   "blocks": List[MemoryBlock],
        #   "stats": Dict[str, Any],
        #   "log": str,
        #   "action": str,
        #   "success": bool
        # }
        self.history: List[Dict[str, Any]] = []
        
        # Registros gerais de execução
        self.stats = {
            "allocated_processes": set(),  # Conjunto de IDs de processos atualmente alocados
            "total_alloc_failures": 0,    # Total de falhas de alocação
            "external_frag_failures": 0,  # Falhas por fragmentação externa
            "insufficient_mem_failures": 0, # Falhas por memória insuficiente total
            "utilization_history": [0.0],  # Histórico de utilização (percentual)
            "average_utilization": 0.0,   # Utilização média
        }
        
        # Salva o estado inicial (passo 0) no histórico
        self._save_state(action="Inicialização da Memória", log=f"Memória inicializada com tamanho total {total_size}.", success=True)

    def get_current_utilization(self, blocks: List[MemoryBlock] = None) -> float:
        """Calcula o percentual de memória ocupada no estado atual."""
        target_blocks = blocks if blocks is not None else self.blocks
        allocated_sum = sum(b.size for b in target_blocks if b.is_allocated)
        return (allocated_sum / self.total_size) * 100.0

    def _save_state(self, action: str, log: str, success: bool):
        """Salva o estado atual no histórico."""
        blocks_copy = [b.clone() for b in self.blocks]
        stats_copy = {
            "allocated_processes": set(self.stats["allocated_processes"]),
            "total_alloc_failures": self.stats["total_alloc_failures"],
            "external_frag_failures": self.stats["external_frag_failures"],
            "insufficient_mem_failures": self.stats["insufficient_mem_failures"],
            "utilization_history": list(self.stats["utilization_history"]),
            "average_utilization": self.stats["average_utilization"],
        }
        
        self.history.append({
            "blocks": blocks_copy,
            "stats": stats_copy,
            "log": log,
            "action": action,
            "success": success
        })

    def restore_step(self, step: int) -> bool:
        """Restaura o estado do simulador para um passo específico do histórico."""
        if 0 <= step < len(self.history):
            state = self.history[step]
            self.blocks = [b.clone() for b in state["blocks"]]
            
            # Restaurar as estatísticas
            hist_stats = state["stats"]
            self.stats = {
                "allocated_processes": set(hist_stats["allocated_processes"]),
                "total_alloc_failures": hist_stats["total_alloc_failures"],
                "external_frag_failures": hist_stats["external_frag_failures"],
                "insufficient_mem_failures": hist_stats["insufficient_mem_failures"],
                "utilization_history": list(hist_stats["utilization_history"]),
                "average_utilization": hist_stats["average_utilization"],
            }
            return True
        return False

    def truncate_history_to(self, step: int):
        """Descarta os passos do histórico após o passo especificado."""
        if 0 <= step < len(self.history):
            self.history = self.history[:step + 1]

    def _coalesce(self) -> List[str]:
        """Funde blocos livres adjacentes. Retorna lista de logs das fusões."""
        logs = []
        i = 0
        while i < len(self.blocks) - 1:
            curr_b = self.blocks[i]
            next_b = self.blocks[i+1]
            if not curr_b.is_allocated and not next_b.is_allocated:
                logs.append(f"Fusão: blocos livres vizinhos [{curr_b.start}-{curr_b.end}] e [{next_b.start}-{next_b.end}] fundidos.")
                curr_b.size += next_b.size
                self.blocks.pop(i+1)
                # Não incrementa i para testar se o novo bloco fundido se funde com o próximo
            else:
                i += 1
        return logs

    def allocate(self, algorithm: str, process_id: str, size: int) -> bool:
        """
        Tenta alocar um processo usando o algoritmo especificado.
        Algoritmos: 'First Fit', 'Best Fit', 'Worst Fit'
        """
        # Trata o ID do processo como string limpa
        process_id = str(process_id).strip()
        
        # Verifica se o processo já está alocado
        if process_id in self.stats["allocated_processes"]:
            log_msg = f"Erro: Processo '{process_id}' já está na memória."
            self._save_state(
                action=f"Alocação {process_id} ({size})",
                log=log_msg,
                success=False
            )
            return False

        # Verifica tamanho inválido
        if size <= 0:
            log_msg = f"Erro: Tamanho de alocação inválido ({size})."
            self._save_state(
                action=f"Alocação {process_id} ({size})",
                log=log_msg,
                success=False
            )
            return False

        # Lista de índices de blocos livres que comportam o processo
        free_block_indices = [
            i for i, b in enumerate(self.blocks) 
            if not b.is_allocated and b.size >= size
        ]

        if not free_block_indices:
            # Falha de alocação: verificar tipo de falha
            total_free_space = sum(b.size for b in self.blocks if not b.is_allocated)
            self.stats["total_alloc_failures"] += 1
            
            if total_free_space >= size:
                # Falha por Fragmentação Externa
                self.stats["external_frag_failures"] += 1
                log_msg = (f"Falha de Alocação: {process_id} ({size}) não alocado devido a FRAGMENTAÇÃO EXTERNA. "
                           f"Espaço total livre disponível é {total_free_space}, mas não há nenhum bloco contíguo de {size}.")
            else:
                # Falha por Memória Insuficiente
                self.stats["insufficient_mem_failures"] += 1
                log_msg = (f"Falha de Alocação: {process_id} ({size}) não alocado por MEMÓRIA INSUFICIENTE. "
                           f"Espaço livre total {total_free_space} é menor que o tamanho solicitado {size}.")
            
            # Adiciona o valor atual ao histórico de utilização (não mudou)
            self.stats["utilization_history"].append(self.get_current_utilization())
            self._update_average_utilization()
            
            self._save_state(
                action=f"Alocação {process_id} ({size})",
                log=log_msg,
                success=False
            )
            return False

        # Escolhe o bloco de acordo com o algoritmo
        chosen_idx = -1
        alg_name = algorithm.strip().lower()

        if alg_name == "first fit":
            # Primeiro bloco livre que serve
            chosen_idx = free_block_indices[0]
            chosen_block = self.blocks[chosen_idx]
            decision_log = f"First Fit: selecionou a primeira brecha disponível [{chosen_block.start}-{chosen_block.end}] com tamanho {chosen_block.size}."
            
        elif alg_name == "best fit":
            # Bloco livre com menor tamanho que serve
            chosen_idx = min(free_block_indices, key=lambda idx: self.blocks[idx].size)
            chosen_block = self.blocks[chosen_idx]
            # Lista as brechas para o log detalhado
            all_options = [f"[{self.blocks[i].start}-{self.blocks[i].end}]({self.blocks[i].size})" for i in free_block_indices]
            decision_log = (f"Best Fit: analisou brechas disponíveis {', '.join(all_options)} e escolheu "
                            f"a menor que serve: [{chosen_block.start}-{chosen_block.end}] com tamanho {chosen_block.size}.")
            
        elif alg_name == "worst fit":
            # Bloco livre com maior tamanho que serve
            chosen_idx = max(free_block_indices, key=lambda idx: self.blocks[idx].size)
            chosen_block = self.blocks[chosen_idx]
            all_options = [f"[{self.blocks[i].start}-{self.blocks[i].end}]({self.blocks[i].size})" for i in free_block_indices]
            decision_log = (f"Worst Fit: analisou brechas disponíveis {', '.join(all_options)} e escolheu "
                            f"a maior que serve: [{chosen_block.start}-{chosen_block.end}] com tamanho {chosen_block.size}.")
        else:
            # Default to First Fit se o algoritmo for inválido
            chosen_idx = free_block_indices[0]
            chosen_block = self.blocks[chosen_idx]
            decision_log = f"Algoritmo desconhecido '{algorithm}'. Usando First Fit como padrão. Selecionou [{chosen_block.start}-{chosen_block.end}]."

        # Executa a alocação dividindo a partição
        block_to_split = self.blocks[chosen_idx]
        original_start = block_to_split.start
        original_size = block_to_split.size

        # Atualiza o bloco escolhido para ser ocupado pelo processo
        block_to_split.is_allocated = True
        block_to_split.process_id = process_id
        block_to_split.size = size

        log_lines = [decision_log, f"Alocado {process_id} ({size}) no intervalo [{original_start}-{original_start + size}]."]

        # Se sobrou espaço no bloco, cria uma nova brecha livre
        remaining_size = original_size - size
        if remaining_size > 0:
            new_free_block = MemoryBlock(
                start=original_start + size,
                size=remaining_size,
                is_allocated=False,
                process_id=None
            )
            self.blocks.insert(chosen_idx + 1, new_free_block)
            log_lines.append(f"Criada nova brecha de tamanho {remaining_size} no intervalo [{new_free_block.start}-{new_free_block.end}].")

        # Atualiza estatísticas
        self.stats["allocated_processes"].add(process_id)
        current_util = self.get_current_utilization()
        self.stats["utilization_history"].append(current_util)
        self._update_average_utilization()

        self._save_state(
            action=f"Alocação {process_id} ({size})",
            log="\n".join(log_lines),
            success=True
        )
        return True

    def release(self, process_id: str) -> bool:
        """Tenta desalocar o processo da memória."""
        process_id = str(process_id).strip()

        # Encontra o bloco ocupado pelo processo
        target_idx = -1
        for idx, block in enumerate(self.blocks):
            if block.is_allocated and block.process_id == process_id:
                target_idx = idx
                break

        if target_idx == -1:
            log_msg = f"Erro de Desalocação: Processo '{process_id}' não está carregado na memória."
            self._save_state(
                action=f"Liberação {process_id}",
                log=log_msg,
                success=False
            )
            return False

        # Desaloca
        block = self.blocks[target_idx]
        size = block.size
        start = block.start
        block.is_allocated = False
        block.process_id = None

        log_lines = [f"Processo {process_id} desalocado com sucesso do intervalo [{start}-{start + size}] (tamanho {size})."]

        # Coalescência de blocos vizinhos livres
        coalesce_logs = self._coalesce()
        log_lines.extend(coalesce_logs)

        # Atualiza estatísticas
        if process_id in self.stats["allocated_processes"]:
            self.stats["allocated_processes"].remove(process_id)
        
        current_util = self.get_current_utilization()
        self.stats["utilization_history"].append(current_util)
        self._update_average_utilization()

        self._save_state(
            action=f"Liberação {process_id}",
            log="\n".join(log_lines),
            success=True
        )
        return True

    def _update_average_utilization(self):
        """Atualiza a média histórica de utilização de memória."""
        history = self.stats["utilization_history"]
        if history:
            self.stats["average_utilization"] = sum(history) / len(history)
        else:
            self.stats["average_utilization"] = 0.0
