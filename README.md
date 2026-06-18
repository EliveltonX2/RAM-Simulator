# RAM Simulator — Simulador de Alocação Dinâmica de Memória RAM

Este é um simulador interativo de alocação de memória RAM desenvolvido em **Python** utilizando **CustomTkinter** para a interface gráfica moderna (com suporte nativo ao modo escuro) e **Matplotlib** para visualização estatística em tempo real. 

O projeto foi projetado para fins didáticos na disciplina de **Sistemas Operacionais (SO)**, permitindo visualizar de forma prática e passo a passo os principais algoritmos de alocação contígua de memória:
*   **First Fit** (Primeiro Encaixe)
*   **Best Fit** (Melhor Encaixe)
*   **Worst Fit** (Pior Encaixe)

---

## 🚀 Funcionalidades Principal

*   **Visualização Gráfica Dinâmica**: Mapa interativo de blocos de memória física com indicação de endereços, blocos alocados (com cores exclusivas por processo) e brechas livres (buracos).
*   **Inspeção Interativa (Hover)**: Ao passar o mouse sobre a barra de memória física, os dados detalhados daquele bloco e o endereço relativo do ponteiro são mostrados na tela.
*   **Controles de Playback Completos**: Controle de fluxo de execução estilo player de vídeo (⏮ Reabrir/Reset, ◀ Passo Anterior, ▶ Reproduzir/Pausar, Próximo ▶, ⏭ Pular para o Fim).
*   **Controle de Velocidade**: Slider para configurar o tempo de transição automática entre passos.
*   **Gráficos Estatísticos**:
    *   Gráfico de linha mostrando a taxa de utilização da memória ao longo dos passos.
    *   Gráfico de pizza com o percentual consolidado de sucesso/falha de alocação, incluindo alertas específicos de **Fragmentação Externa** e **Memória Insuficiente**.
*   **Operações Manuais**: Painel dedicado para inserir solicitações avulsas de alocação (`A`) ou liberação (`D`) de processos a qualquer momento da execução.
*   **Leitor de Arquivos de Cenários**: Importação flexível de arquivos de teste no formato texto (`.txt`) estruturado.


## 📦 Método 1: Utilizando o Executável Pré-Compilado (Sem Instalação)

A forma mais simples e rápida de rodar o simulador no Windows é através do executável pré-compilado, que não exige nenhuma instalação do Python ou de bibliotecas em sua máquina.

### Como Executar:
1. Acesse a pasta `dist/` do projeto.
2. Dê um duplo clique no arquivo **`app.exe`** para abrir o simulador diretamente.
*(Caso esteja baixando pelo GitHub, você pode fazer o download do `app.exe` diretamente na aba **Releases** do repositório).*

### Guia de Utilização do Simulador:
1. **Selecionar Algoritmo**: No painel lateral esquerdo, selecione qual algoritmo de alocação dinâmica deseja simular (**First Fit**, **Best Fit** ou **Worst Fit**). O simulador recalcula o mapa em tempo real a qualquer momento que você alterar o algoritmo!
2. **Carregar Cenário**:
   * Clique em **"Carregar Arquivo .txt"** para abrir uma janela e selecionar um arquivo com a sequência de ações planejadas.
   * *(Opcional)* Clique em **"Gerar Arquivo de Exemplo"** para criar um arquivo `.txt` de testes estruturado pronto para rodar.
3. **Controlar a Simulação**:
   * Utilize os botões do player na parte inferior central para navegar pelos eventos:
     * `⏮ Reabrir`: Reseta o simulador ao passo 0 (estado inicial de memória limpa).
     * `◀ Anterior`: Retrocede um passo no tempo.
     * `▶ Reproduzir / ⏸ Pausar`: Inicia ou pausa a simulação automática.
     * `Próximo ▶`: Avança um único passo.
     * `⏭ Fim`: Avança instantaneamente até o último evento da lista.
   * Ajuste o controle deslizante de **Velocidade de Reprodução** no menu lateral para acelerar ou desacelerar a simulação automática.
4. **Operações Manuais**:
   * No menu lateral esquerdo, abaixo da divisória, você pode alocar ou liberar processos manualmente a qualquer momento.
   * Basta digitar o ID do processo (ex: `P9`) e o tamanho em Bytes (para alocação) e clicar no botão correspondente.
5. **Acompanhar os Resultados**:
   * **Mapa de Memória**: O topo do painel principal exibe a partição física da memória. Passe o mouse sobre ela para obter detalhes em tempo real sobre os blocos (endereço, tamanho, status).
   * **Logs do Simulador**: Aba que detalha o resultado lógico de cada operação realizada.
   * **Fila de Eventos**: Lista os eventos pendentes e marca com cores os que já foram executados com sucesso ou falha (Fragmentação Externa / Memória Insuficiente).
   * **Estatísticas & Gráficos**: Mostra a evolução histórica de uso da RAM e um gráfico consolidado com a proporção de sucesso e falha das operações realizadas.

### 📝 Formato dos Arquivos de Entrada (.txt)
Para criar e importar seus próprios cenários de teste, crie um arquivo de texto comum (`.txt`) seguindo o seguinte formato:
1. Linhas que começam com `#` são consideradas **comentários** e são completamente ignoradas.
2. A primeira linha de dados legível deve indicar o **tamanho total da memória física** em Bytes (ex: `1000`).
3. As linhas subsequentes devem conter as ações na estrutura:
   * **Alocação**: `A <ID_do_Processo> <Tamanho_Bytes>`
   * **Liberação**: `D <ID_do_Processo>` ou `L <ID_do_Processo>`

**Exemplo de Arquivo Válido:**
```text
# Cenário de Teste de Alocação
1024

A P1 200
A P2 350
D P1
A P3 100
A P4 400
```
*(Você pode testar usando os arquivos [caso_teste.txt](file:///c:/Users/Elive/OneDrive/Documentos/projetos/RamSimulator/caso_teste.txt) e [exemplo_memoria.txt](file:///c:/Users/Elive/OneDrive/Documentos/projetos/RamSimulator/exemplo_memoria.txt) que já acompanham o repositório).*

---

## 🛠️ Método 2: Executando a partir do Código-Fonte

Caso prefira rodar a aplicação diretamente pelo código em Python ou queira fazer modificações de desenvolvimento, siga as instruções abaixo:

### Pré-requisitos
* Python 3.8 ou superior instalado.
* Git instalado (opcional, para clonar).

### Passo 1: Baixar o Projeto
Clone o repositório através do Git:
```bash
git clone https://github.com/seu-usuario/RamSimulator.git
cd RamSimulator
```
*(Ou baixe e extraia o arquivo ZIP do projeto diretamente do GitHub).*

### Passo 2: Configurar o Ambiente Virtual (Recomendado)
Para evitar conflito de bibliotecas no seu sistema:

**No Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**No Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Passo 3: Instalar as Dependências
Com o ambiente virtual ativado, instale as dependências listadas em [requirements.txt](file:///c:/Users/Elive/OneDrive/Documentos/projetos/RamSimulator/requirements.txt):
```bash
pip install -r requirements.txt
```

### Passo 4: Executar a Aplicação
Inicie o simulador rodando o script principal [app.py](file:///c:/Users/Elive/OneDrive/Documentos/projetos/RamSimulator/app.py):
```bash
python app.py
```

