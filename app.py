import os
import re
import sys
import colorsys
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

# Matplotlib setup for Tkinter integration
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Simulator engine
from simulator import MemorySimulator, MemoryBlock

# Configuração de Aparência do CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configurações da Janela Principal
        self.title("Simulador de Alocação Dinâmica de Memória - SO 2026")
        self.geometry("1280x820")
        self.minsize(1100, 750)

        # Estado da Simulação
        self.sim = None
        self.total_memory = 1000
        self.events = []
        self.current_step = 0  # 0 significa inicial, sem eventos executados ainda
        self.is_playing = False
        self.after_id = None

        # Cores para o layout da aplicação
        self.bg_color_dark = "#1a1a1e"
        self.card_color_dark = "#242429"
        self.accent_blue = "#1f77b4"
        self.success_green = "#2ca02c"
        self.fail_red = "#d62728"
        self.warn_orange = "#ff7f0e"

        # Configurar Grid Principal
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Criação de Componentes da Interface
        self.create_sidebar()
        self.create_main_panel()

        # Inicia com dados padrão para visualização imediata
        self.load_default_simulation()

    def get_process_color(self, process_id: str) -> str:
        """Gera uma cor HSL única e vibrante a partir do ID do processo."""
        h_val = 0
        for char in str(process_id):
            h_val = (h_val * 31 + ord(char)) % 360
        
        hue = h_val / 360.0
        saturation = 0.80
        lightness = 0.55  # Ideal para fundo escuro com texto branco
        
        r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

    def create_sidebar(self):
        """Cria o painel lateral com configurações e inputs manuais."""
        self.sidebar_frame = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(9, weight=1) # Espaçador no fim

        # Título da Aplicação
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="RAM Simulator", 
            font=ctk.CTkFont(family="Outfit", size=26, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")

        self.subtitle_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="Sistemas Operacionais 2026", 
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="#888888"
        )
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")

        # Seção 1: Configuração do Algoritmo
        self.alg_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.alg_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        self.alg_title = ctk.CTkLabel(
            self.alg_frame, text="Algoritmo de Alocação", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.alg_title.pack(anchor="w", pady=2)
        
        self.algorithm_var = ctk.StringVar(value="First Fit")
        self.alg_menu = ctk.CTkOptionMenu(
            self.alg_frame,
            values=["First Fit", "Best Fit", "Worst Fit"],
            variable=self.algorithm_var,
            command=self.on_algorithm_change
        )
        self.alg_menu.pack(fill="x", pady=5)

        # Seção 2: Carregar Arquivo
        self.file_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.file_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        self.file_title = ctk.CTkLabel(
            self.file_frame, text="Arquivo de Configuração", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.file_title.pack(anchor="w", pady=2)
        
        self.load_file_btn = ctk.CTkButton(
            self.file_frame, 
            text="Carregar Arquivo .txt", 
            command=self.load_file,
            fg_color=self.accent_blue,
            hover_color="#185c8c"
        )
        self.load_file_btn.pack(fill="x", pady=5)
        
        self.filepath_label = ctk.CTkLabel(
            self.file_frame, 
            text="Nenhum arquivo ativo", 
            font=ctk.CTkFont(size=11),
            text_color="#888888"
        )
        self.filepath_label.pack(anchor="w", pady=2)

        self.example_file_btn = ctk.CTkButton(
            self.file_frame, 
            text="Gerar Arquivo de Exemplo", 
            command=self.generate_sample_file,
            fg_color="#3a3a3e",
            hover_color="#4f4f54"
        )
        self.example_file_btn.pack(fill="x", pady=5)

        # Divisor
        self.separator = ctk.CTkFrame(self.sidebar_frame, height=2, fg_color="#333333")
        self.separator.grid(row=4, column=0, padx=20, pady=15, sticky="ew")

        # Seção 3: Operações Manuais
        self.manual_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.manual_frame.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        
        self.manual_title = ctk.CTkLabel(
            self.manual_frame, text="Operações Manuais", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.manual_title.pack(anchor="w", pady=5)

        # TabView para Alocar / Liberar
        self.manual_tab = ctk.CTkTabview(self.manual_frame, height=180)
        self.manual_tab.pack(fill="x")
        self.manual_tab.add("Alocar")
        self.manual_tab.add("Liberar")

        # Widgets de Alocação Manual
        self.manual_tab.tab("Alocar").grid_columnconfigure(0, weight=1)
        self.entry_alloc_id = ctk.CTkEntry(self.manual_tab.tab("Alocar"), placeholder_text="ID do Processo (Ex: P9)")
        self.entry_alloc_id.grid(row=0, column=0, pady=5, sticky="ew")
        self.entry_alloc_size = ctk.CTkEntry(self.manual_tab.tab("Alocar"), placeholder_text="Tamanho (Bytes)")
        self.entry_alloc_size.grid(row=1, column=0, pady=5, sticky="ew")
        self.btn_alloc_manual = ctk.CTkButton(
            self.manual_tab.tab("Alocar"), 
            text="Alocar na RAM", 
            command=self.execute_manual_alloc,
            fg_color=self.success_green,
            hover_color="#207820"
        )
        self.btn_alloc_manual.grid(row=2, column=0, pady=10, sticky="ew")

        # Widgets de Liberação Manual
        self.manual_tab.tab("Liberar").grid_columnconfigure(0, weight=1)
        self.entry_free_id = ctk.CTkEntry(self.manual_tab.tab("Liberar"), placeholder_text="ID do Processo (Ex: P9)")
        self.entry_free_id.grid(row=0, column=0, pady=5, sticky="ew")
        self.btn_free_manual = ctk.CTkButton(
            self.manual_tab.tab("Liberar"), 
            text="Liberar da RAM", 
            command=self.execute_manual_free,
            fg_color=self.fail_red,
            hover_color="#9e1d1d"
        )
        self.btn_free_manual.grid(row=1, column=0, pady=10, sticky="ew")

        # Seção 4: Velocidade da Animação
        self.speed_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.speed_frame.grid(row=6, column=0, padx=20, pady=10, sticky="ew")
        
        self.speed_title = ctk.CTkLabel(
            self.speed_frame, text="Velocidade de Reprodução", 
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.speed_title.pack(anchor="w", pady=2)
        
        self.speed_slider = ctk.CTkSlider(self.speed_frame, from_=0.2, to=3.0, number_of_steps=14)
        self.speed_slider.set(1.0)
        self.speed_slider.pack(fill="x", pady=5)
        
        self.speed_label = ctk.CTkLabel(self.speed_frame, text="Velocidade: 1.0s / passo", font=ctk.CTkFont(size=11), text_color="#888888")
        self.speed_label.pack(anchor="e")
        self.speed_slider.bind("<ButtonRelease-1>", self.on_speed_slider_change)
        self.speed_slider.bind("<B1-Motion>", self.on_speed_slider_change)

    def create_main_panel(self):
        """Cria a tela principal do simulador contendo gráficos, métricas e canvas."""
        self.main_panel = ctk.CTkFrame(self, fg_color=self.bg_color_dark, corner_radius=0)
        self.main_panel.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # Grid no painel principal
        # Linha 0: Cards de Métricas
        # Linha 1: Canvas de Memória Física
        # Linha 2: Controles de Reprodução
        # Linha 3: Abas (Eventos, Gráficos, Log)
        self.main_panel.grid_rowconfigure(3, weight=1)
        self.main_panel.grid_columnconfigure(0, weight=1)

        # ----------------- LINHA 0: Cards de Métricas -----------------
        self.metrics_frame = ctk.CTkFrame(self.main_panel, fg_color="transparent")
        self.metrics_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        for col in range(4):
            self.metrics_frame.grid_columnconfigure(col, weight=1)

        # Card 1: Utilização
        self.card_util = ctk.CTkFrame(self.metrics_frame, fg_color=self.card_color_dark, height=90)
        self.card_util.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        self.card_util.grid_propagate(False)
        self.metric_used_title = ctk.CTkLabel(self.card_util, text="Uso da Memória", text_color="#888888", font=ctk.CTkFont(size=12, weight="bold"))
        self.metric_used_title.pack(anchor="w", padx=15, pady=(8, 2))
        self.metric_used_val = ctk.CTkLabel(self.card_util, text="0.0 %", font=ctk.CTkFont(size=20, weight="bold"))
        self.metric_used_val.pack(anchor="w", padx=15)
        self.metric_used_sub = ctk.CTkLabel(self.card_util, text="0 / 1000 Bytes", text_color="#888888", font=ctk.CTkFont(size=10))
        self.metric_used_sub.pack(anchor="w", padx=15)
        self.metric_used_progress = ctk.CTkProgressBar(self.card_util, height=4, progress_color=self.accent_blue)
        self.metric_used_progress.pack(fill="x", padx=15, pady=(5, 0))
        self.metric_used_progress.set(0)

        # Card 2: Processos Ativos
        self.card_procs = ctk.CTkFrame(self.metrics_frame, fg_color=self.card_color_dark, height=90)
        self.card_procs.grid(row=0, column=1, padx=5, sticky="nsew")
        self.card_procs.grid_propagate(False)
        self.metric_procs_title = ctk.CTkLabel(self.card_procs, text="Processos Ativos", text_color="#888888", font=ctk.CTkFont(size=12, weight="bold"))
        self.metric_procs_title.pack(anchor="w", padx=15, pady=(10, 2))
        self.metric_procs_val = ctk.CTkLabel(self.card_procs, text="0", font=ctk.CTkFont(size=24, weight="bold"), text_color=self.success_green)
        self.metric_procs_val.pack(anchor="w", padx=15)
        self.metric_procs_sub = ctk.CTkLabel(self.card_procs, text="atualmente alocados", text_color="#888888", font=ctk.CTkFont(size=10))
        self.metric_procs_sub.pack(anchor="w", padx=15)

        # Card 3: Brechas (Holes)
        self.card_holes = ctk.CTkFrame(self.metrics_frame, fg_color=self.card_color_dark, height=90)
        self.card_holes.grid(row=0, column=2, padx=5, sticky="nsew")
        self.card_holes.grid_propagate(False)
        self.metric_holes_title = ctk.CTkLabel(self.card_holes, text="Brechas Livres", text_color="#888888", font=ctk.CTkFont(size=12, weight="bold"))
        self.metric_holes_title.pack(anchor="w", padx=15, pady=(10, 2))
        self.metric_holes_val = ctk.CTkLabel(self.card_holes, text="1", font=ctk.CTkFont(size=24, weight="bold"), text_color=self.warn_orange)
        self.metric_holes_val.pack(anchor="w", padx=15)
        self.metric_holes_sub = ctk.CTkLabel(self.card_holes, text="espaços contíguos", text_color="#888888", font=ctk.CTkFont(size=10))
        self.metric_holes_sub.pack(anchor="w", padx=15)

        # Card 4: Falhas de Fragmentação
        self.card_frag = ctk.CTkFrame(self.metrics_frame, fg_color=self.card_color_dark, height=90)
        self.card_frag.grid(row=0, column=3, padx=(10, 0), sticky="nsew")
        self.card_frag.grid_propagate(False)
        self.metric_frag_title = ctk.CTkLabel(self.card_frag, text="Frag. Externa", text_color="#888888", font=ctk.CTkFont(size=12, weight="bold"))
        self.metric_frag_title.pack(anchor="w", padx=15, pady=(10, 2))
        self.metric_frag_val = ctk.CTkLabel(self.card_frag, text="0", font=ctk.CTkFont(size=24, weight="bold"), text_color=self.fail_red)
        self.metric_frag_val.pack(anchor="w", padx=15)
        self.metric_frag_sub = ctk.CTkLabel(self.card_frag, text="falhas de espaço", text_color="#888888", font=ctk.CTkFont(size=10))
        self.metric_frag_sub.pack(anchor="w", padx=15)

        # ----------------- LINHA 1: Canvas da RAM Física -----------------
        self.canvas_frame = ctk.CTkFrame(self.main_panel, fg_color=self.card_color_dark)
        self.canvas_frame.grid(row=1, column=0, sticky="ew", pady=10)
        self.canvas_frame.grid_columnconfigure(0, weight=1)

        self.canvas_header = ctk.CTkLabel(self.canvas_frame, text="Mapa de Alocação de Memória Física", font=ctk.CTkFont(size=14, weight="bold"))
        self.canvas_header.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")

        # Canvas Tkinter para desenho da memória
        self.canvas = tk.Canvas(
            self.canvas_frame, 
            height=160, 
            bg="#111115", 
            highlightthickness=0, 
            bd=0
        )
        self.canvas.grid(row=1, column=0, padx=15, pady=(5, 5), sticky="ew")
        
        # Binds para redimensionamento e hover interativo
        self.canvas.bind("<Configure>", lambda event: self.redraw_memory())
        self.canvas.bind("<Motion>", self.on_canvas_motion)
        self.canvas.bind("<Leave>", self.on_canvas_leave)

        # Barra de Status do Canvas (Hover Details)
        self.hover_info_label = ctk.CTkLabel(
            self.canvas_frame, 
            text="Passe o mouse sobre a memória física para inspecionar os blocos...",
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="#888888",
            anchor="w"
        )
        self.hover_info_label.grid(row=2, column=0, padx=15, pady=(5, 10), sticky="w")

        # ----------------- LINHA 2: Painel de Controle de Playback -----------------
        self.playback_frame = ctk.CTkFrame(self.main_panel, fg_color="transparent")
        self.playback_frame.grid(row=2, column=0, sticky="ew", pady=10)
        self.playback_frame.grid_columnconfigure(0, weight=1)

        self.btn_container = ctk.CTkFrame(self.playback_frame, fg_color="transparent")
        self.btn_container.pack(anchor="center")

        # Botões do Player
        self.btn_reset = ctk.CTkButton(self.btn_container, text="⏮ Reabrir", width=80, command=self.reset_simulation, fg_color="#333336", hover_color="#454549")
        self.btn_reset.pack(side="left", padx=5)

        self.btn_prev = ctk.CTkButton(self.btn_container, text="◀ Anterior", width=90, command=self.step_backward, fg_color="#333336", hover_color="#454549")
        self.btn_prev.pack(side="left", padx=5)

        self.btn_play = ctk.CTkButton(self.btn_container, text="▶ Reproduzir", width=120, command=self.toggle_play, fg_color=self.accent_blue, hover_color="#185c8c")
        self.btn_play.pack(side="left", padx=5)

        self.btn_next = ctk.CTkButton(self.btn_container, text="Próximo ▶", width=90, command=self.step_forward, fg_color="#333336", hover_color="#454549")
        self.btn_next.pack(side="left", padx=5)

        self.btn_end = ctk.CTkButton(self.btn_container, text="⏭ Fim", width=80, command=self.skip_to_end, fg_color="#333336", hover_color="#454549")
        self.btn_end.pack(side="left", padx=5)

        # Label do Passo Atual
        self.step_label = ctk.CTkLabel(self.playback_frame, text="Passo: 0 / 0", font=ctk.CTkFont(size=12, weight="bold"))
        self.step_label.pack(side="right", padx=10)

        # ----------------- LINHA 3: Abas Informativas -----------------
        self.info_tabview = ctk.CTkTabview(self.main_panel)
        self.info_tabview.grid(row=3, column=0, sticky="nsew", pady=(10, 0))
        
        self.info_tabview.add("Logs do Simulador")
        self.info_tabview.add("Fila de Eventos")
        self.info_tabview.add("Estatísticas & Gráficos")
        self.info_tabview.set("Logs do Simulador")

        # Aba 1: Fila de Eventos (Scrollable List)
        self.info_tabview.tab("Fila de Eventos").grid_columnconfigure(0, weight=1)
        self.info_tabview.tab("Fila de Eventos").grid_rowconfigure(0, weight=1)
        
        self.events_scroll_frame = ctk.CTkScrollableFrame(
            self.info_tabview.tab("Fila de Eventos"),
            fg_color="#18181b",
            label_text="Fila ordenada de ações do simulador"
        )
        self.events_scroll_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.event_row_widgets = [] # Armazena referências para destacar a linha ativa

        # Aba 2: Estatísticas & Gráficos (Matplotlib)
        self.info_tabview.tab("Estatísticas & Gráficos").grid_columnconfigure(0, weight=1)
        self.info_tabview.tab("Estatísticas & Gráficos").grid_rowconfigure(0, weight=1)
        
        self.charts_container = ctk.CTkFrame(self.info_tabview.tab("Estatísticas & Gráficos"), fg_color="#242429")
        self.charts_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.charts_container.grid_columnconfigure(0, weight=1)
        self.charts_container.grid_rowconfigure(0, weight=1)

        # Matplotlib Figure
        self.fig = Figure(figsize=(7, 3), facecolor='#242429')
        self.ax_util = self.fig.add_subplot(121)
        self.ax_pie = self.fig.add_subplot(122)
        
        self.fig_canvas = FigureCanvasTkAgg(self.fig, master=self.charts_container)
        self.fig_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Aba 3: Logs do Simulador
        self.info_tabview.tab("Logs do Simulador").grid_columnconfigure(0, weight=1)
        self.info_tabview.tab("Logs do Simulador").grid_rowconfigure(0, weight=1)
        
        self.textbox_log = ctk.CTkTextbox(
            self.info_tabview.tab("Logs do Simulador"), 
            font=ctk.CTkFont(family="Consolas", size=12),
            activate_scrollbars=True
        )
        self.textbox_log.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    # ----------------- Lógica de Simulação & Controle de Fluxo -----------------

    def load_default_simulation(self):
        """Inicializa um cenário clássico por padrão para o simulador não começar vazio."""
        self.total_memory = 1000
        self.events = [
            {"type": "allocate", "process_id": "P1", "size": 200, "raw_line": "Alocação P1 (200)"},
            {"type": "allocate", "process_id": "P2", "size": 350, "raw_line": "Alocação P2 (350)"},
            {"type": "allocate", "process_id": "P3", "size": 150, "raw_line": "Alocação P3 (150)"},
            {"type": "release", "process_id": "P2", "raw_line": "Desalocação P2"},
            {"type": "allocate", "process_id": "P4", "size": 250, "raw_line": "Alocação P4 (250)"},
            {"type": "allocate", "process_id": "P5", "size": 300, "raw_line": "Alocação P5 (300)"},
            {"type": "release", "process_id": "P1", "raw_line": "Desalocação P1"},
            {"type": "allocate", "process_id": "P6", "size": 100, "raw_line": "Alocação P6 (100)"},
            {"type": "allocate", "process_id": "P7", "size": 250, "raw_line": "Alocação P7 (250)"},
        ]
        
        self.sim = MemorySimulator(self.total_memory)
        self.current_step = 0
        self.is_playing = False
        self.update_play_button_text()
        
        self.rebuild_event_list()
        self.update_ui()
        self.log_message("Simulador inicializado com dados padrão. Modifique carregando um arquivo ou usando os comandos manuais.")

    def on_algorithm_change(self, *args):
        """Recalcula toda a simulação até o ponto atual se o usuário alterar o algoritmo no menu."""
        if not self.sim or not self.events:
            return
        
        saved_step = self.current_step
        alg = self.algorithm_var.get()
        
        # Reinicia o motor com o mesmo tamanho físico
        self.sim = MemorySimulator(self.total_memory)
        
        # Re-executa as etapas até o passo atual com o novo algoritmo
        for i in range(saved_step):
            event = self.events[i]
            if event["type"] == "allocate":
                self.sim.allocate(alg, event["process_id"], event["size"])
            elif event["type"] == "release":
                self.sim.release(event["process_id"])
        
        self.current_step = saved_step
        self.update_ui()
        self.log_message(f"--- Algoritmo alterado para: {alg} ---")
        self.log_message(f"Simulação recalculada até o passo {self.current_step} usando {alg}.")

    def rebuild_event_list(self):
        """Reconstrói os widgets visuais da fila de eventos na aba correspondente."""
        # Limpa widgets anteriores
        for widget in self.event_row_widgets:
            widget.destroy()
        self.event_row_widgets = []

        if not self.events:
            empty_lbl = ctk.CTkLabel(self.events_scroll_frame, text="Nenhum evento carregado.", text_color="#888888")
            empty_lbl.pack(pady=10)
            self.event_row_widgets.append(empty_lbl)
            return

        # Popula as linhas
        for idx, event in enumerate(self.events):
            row_frame = ctk.CTkFrame(self.events_scroll_frame, fg_color="#202024", height=38, corner_radius=6)
            row_frame.pack(fill="x", pady=4, padx=5)
            row_frame.pack_propagate(False)
            
            # Número do passo (1-indexed para o usuário)
            step_num = ctk.CTkLabel(row_frame, text=f" {idx + 1:02d} ", font=ctk.CTkFont(weight="bold"), text_color="#888888")
            step_num.pack(side="left", padx=10)

            # Descrição do evento
            if event["type"] == "allocate":
                desc_text = f"Alocar {event['process_id']} (Tamanho: {event['size']} B)"
                icon_color = self.accent_blue
            else:
                desc_text = f"Liberar {event['process_id']}"
                icon_color = self.warn_orange

            desc_lbl = ctk.CTkLabel(row_frame, text=desc_text, anchor="w", font=ctk.CTkFont(size=12))
            desc_lbl.pack(side="left", padx=5, fill="x", expand=True)

            # Badge de Status (será atualizado por update_ui)
            status_badge = ctk.CTkLabel(
                row_frame, 
                text="Pendente", 
                fg_color="#333338", 
                text_color="#aaaaaa",
                font=ctk.CTkFont(size=10, weight="bold"),
                width=110,
                corner_radius=4
            )
            # Truque: salvamos referências a esses widgets para atualizá-los dinamicamente
            row_frame.status_badge = status_badge
            status_badge.pack(side="right", padx=10, pady=6)
            
            self.event_row_widgets.append(row_frame)

    def step_forward(self) -> bool:
        """Avança um passo na simulação."""
        if not self.sim or not self.events:
            return False

        if self.current_step >= len(self.events):
            # Final dos eventos atingido
            self.is_playing = False
            self.update_play_button_text()
            return False

        # Próximo evento
        event = self.events[self.current_step]
        alg = self.algorithm_var.get()

        # Verifica se já está no histórico do simulador
        # O histórico possui tamanho len(history). O passo atual corresponde à história no índice current_step.
        # Ao avançar, queremos o estado no índice current_step + 1.
        if self.current_step + 1 < len(self.sim.history):
            self.sim.restore_step(self.current_step + 1)
        else:
            # Precisa computar um novo passo no simulador
            if event["type"] == "allocate":
                self.sim.allocate(alg, event["process_id"], event["size"])
            elif event["type"] == "release":
                self.sim.release(event["process_id"])

        self.current_step += 1
        
        # Adiciona a mensagem do log mais recente
        newest_log = self.sim.history[self.current_step]["log"]
        self.log_message(f"--- [PASSO {self.current_step}] {self.sim.history[self.current_step]['action']} ---")
        self.log_message(newest_log + "\n")

        self.update_ui()
        return True

    def step_backward(self) -> bool:
        """Retrocede um passo na simulação."""
        if not self.sim or self.current_step <= 0:
            return False

        # Tenta restaurar o passo anterior
        self.current_step -= 1
        self.sim.restore_step(self.current_step)
        
        self.log_message(f"--- Retrocedeu para Passo {self.current_step} ---")
        self.log_message(f"Restaurado estado de memória correspondente.\n")

        # Se estava reproduzindo, pausa
        self.is_playing = False
        self.update_play_button_text()

        self.update_ui()
        return True

    def reset_simulation(self):
        """Reinicia a simulação para o estado inicial (passo 0)."""
        if not self.sim:
            return

        self.current_step = 0
        self.sim.restore_step(0)
        
        # Descarta os passos calculados posteriores à inicialização para evitar caminhos inconsistentes se mudar configs
        self.sim.truncate_history_to(0)
        
        self.is_playing = False
        self.update_play_button_text()

        self.log_message("--- Simulação Reiniciada ---")
        self.log_message("Memória limpa para o estado de inicialização física original.\n")

        self.update_ui()

    def skip_to_end(self):
        """Avança toda a simulação até o final dos eventos carregados."""
        if not self.sim or not self.events:
            return
        
        self.is_playing = False
        self.update_play_button_text()
        
        while self.current_step < len(self.events):
            self.step_forward()

    def toggle_play(self):
        """Alterna entre tocar automaticamente e pausar."""
        if not self.sim or not self.events:
            return
        
        if self.is_playing:
            self.is_playing = False
            self.update_play_button_text()
            if self.after_id:
                self.after_cancel(self.after_id)
                self.after_id = None
        else:
            self.is_playing = True
            self.update_play_button_text()
            self.play_loop()

    def play_loop(self):
        """Loop de reprodução baseado na velocidade do slider."""
        if not self.is_playing:
            return

        if self.step_forward():
            # Programa o próximo passo
            speed_seconds = self.speed_slider.get()
            self.after_id = self.after(int(speed_seconds * 1000), self.play_loop)
        else:
            # Parou (fim da fila)
            self.is_playing = False
            self.update_play_button_text()
            self.after_id = None

    def update_play_button_text(self):
        """Atualiza a parte textual do botão de play."""
        if self.is_playing:
            self.btn_play.configure(text="⏸ Pausar", fg_color=self.warn_orange, hover_color="#c9640a")
        else:
            self.btn_play.configure(text="▶ Reproduzir", fg_color=self.accent_blue, hover_color="#185c8c")

    def on_speed_slider_change(self, event=None):
        """Atualiza a label de velocidade com base no valor do slider."""
        val = self.speed_slider.get()
        self.speed_label.configure(text=f"Velocidade: {val:.1f}s / passo")

    # ----------------- Desenho da Memória no Canvas -----------------

    def redraw_memory(self):
        """Desenha de forma pixel-perfect a representação da RAM e seus blocos livres/ocupados."""
        if not self.sim:
            return

        self.canvas.delete("all")
        
        # Dimensões e escala
        padding_x = 30
        y_top = 25
        y_bottom = 105
        bar_height = y_bottom - y_top
        
        canvas_w = self.canvas.winfo_width()
        # Fallback caso a janela não esteja totalmente mapeada em tela
        if canvas_w < 100:
            canvas_w = 850
            
        eff_width = canvas_w - (2 * padding_x)
        total_mem = self.total_memory

        # Desenha a moldura de fundo da memória física
        self.canvas.create_rectangle(
            padding_x - 4, y_top - 4, 
            padding_x + eff_width + 4, y_bottom + 4, 
            fill="#0b0b0d", outline="#3f3f45", width=2
        )

        # Mapeia as posições físicas dos blocos para o Canvas
        self.canvas_blocks_coords = [] # Lista para tratar o hover: (start_x, end_x, MemoryBlock)

        for idx, block in enumerate(self.sim.blocks):
            # Calcula posições pixel correspondentes
            bx_start = padding_x + (block.start / total_mem) * eff_width
            bx_end = padding_x + (block.end / total_mem) * eff_width
            b_width = bx_end - bx_start

            # Salva para cálculo de hover
            self.canvas_blocks_coords.append((bx_start, bx_end, block))

            if block.is_allocated:
                # Processo ocupado
                color = self.get_process_color(block.process_id)
                # Retângulo do bloco
                self.canvas.create_rectangle(
                    bx_start, y_top, bx_end, y_bottom, 
                    fill=color, outline="#ffffff", width=1.5
                )
                
                # Texto interno (Processo ID + tamanho)
                mid_x = (bx_start + bx_end) / 2
                mid_y = (y_top + y_bottom) / 2
                
                if b_width > 55:
                    self.canvas.create_text(
                        mid_x, mid_y, 
                        text=f"{block.process_id}\n{block.size} B", 
                        fill="#ffffff", 
                        font=ctk.CTkFont(family="Helvetica", size=11, weight="bold"),
                        justify=tk.CENTER
                    )
                elif b_width > 28:
                    self.canvas.create_text(
                        mid_x, mid_y, 
                        text=str(block.process_id), 
                        fill="#ffffff", 
                        font=ctk.CTkFont(family="Helvetica", size=9, weight="bold")
                    )
            else:
                # Bloco livre (brecha)
                # Preenche com textura escura
                self.canvas.create_rectangle(
                    bx_start, y_top, bx_end, y_bottom, 
                    fill="#1b1b22", outline="#5e5e64", width=1, dash=(4, 4)
                )
                
                # Texto interno (Livre)
                mid_x = (bx_start + bx_end) / 2
                mid_y = (y_top + y_bottom) / 2
                
                if b_width > 55:
                    self.canvas.create_text(
                        mid_x, mid_y, 
                        text=f"Livre\n{block.size} B", 
                        fill="#7f7f87", 
                        font=ctk.CTkFont(family="Helvetica", size=10, slant="italic"),
                        justify=tk.CENTER
                    )
                elif b_width > 28:
                    self.canvas.create_text(
                        mid_x, mid_y, 
                        text="L", 
                        fill="#7f7f87", 
                        font=ctk.CTkFont(family="Helvetica", size=8, slant="italic")
                    )

            # Ticks de Endereços (Régua inferior)
            # Desenha a linha marcadora de início do bloco
            self.canvas.create_line(bx_start, y_bottom, bx_start, y_bottom + 8, fill="#5e5e64", width=1)
            # Desenha o endereço numérico rotacionado ou simplesmente deslocado
            self.canvas.create_text(
                bx_start, y_bottom + 16, 
                text=str(block.start), 
                fill="#888890", 
                font=ctk.CTkFont(family="Consolas", size=8)
            )

            # Para o último bloco, imprime também a marca final da RAM
            if idx == len(self.sim.blocks) - 1:
                self.canvas.create_line(bx_end, y_bottom, bx_end, y_bottom + 8, fill="#5e5e64", width=1)
                self.canvas.create_text(
                    bx_end, y_bottom + 16, 
                    text=str(block.end), 
                    fill="#888890", 
                    font=ctk.CTkFont(family="Consolas", size=8)
                )

    def on_canvas_motion(self, event):
        """Detecção de hover do mouse para exibir os dados do bloco sob o ponteiro."""
        if not self.sim or not hasattr(self, 'canvas_blocks_coords'):
            return

        x, y = event.x, event.y
        # Valida se o mouse está na faixa vertical da barra física
        if 25 <= y <= 105:
            # Encontra qual bloco contém a posição horizontal x
            for start_x, end_x, block in self.canvas_blocks_coords:
                if start_x <= x <= end_x:
                    status_desc = f"Ocupado pelo Processo {block.process_id}" if block.is_allocated else "Livre (Brecha de Memória)"
                    # Calcula o endereço físico relativo baseado em x
                    padding_x = 30
                    canvas_w = self.canvas.winfo_width()
                    if canvas_w < 100: canvas_w = 850
                    eff_width = canvas_w - (2 * padding_x)
                    rel_addr = int(((x - padding_x) / eff_width) * self.total_memory)
                    rel_addr = max(0, min(rel_addr, self.total_memory))

                    self.hover_info_label.configure(
                        text=f"Mouse sobre Endereço: {rel_addr} B | Bloco Físico: [{block.start} - {block.end}] (Tamanho: {block.size} B) | Status: {status_desc}",
                        text_color="white"
                    )
                    return
        
        # Se saiu da barra mas ainda está no canvas, volta ao padrão
        self.on_canvas_leave()

    def on_canvas_leave(self, event=None):
        """Restaura o texto explicativo da barra de status ao tirar o mouse do canvas."""
        self.hover_info_label.configure(
            text="Passe o mouse sobre a memória física para inspecionar os blocos...",
            text_color="#888888"
        )

    # ----------------- Atualizações Gerais da UI -----------------

    def update_ui(self):
        """Sincroniza todos os painéis, métricas, abas e gráficos com o estado atual da simulação."""
        if not self.sim:
            return

        # 1. Desenhar Memória Física
        self.redraw_memory()

        # 2. Atualizar Cards de Métricas
        used_bytes = sum(b.size for b in self.sim.blocks if b.is_allocated)
        util_pct = (used_bytes / self.total_memory) * 100.0
        
        self.metric_used_val.configure(text=f"{util_pct:.1f} %")
        self.metric_used_sub.configure(text=f"{used_bytes} / {self.total_memory} Bytes")
        self.metric_used_progress.set(used_bytes / self.total_memory)

        active_procs = len(self.sim.stats["allocated_processes"])
        self.metric_procs_val.configure(text=str(active_procs))

        free_blocks = sum(1 for b in self.sim.blocks if not b.is_allocated)
        self.metric_holes_val.configure(text=str(free_blocks))

        frag_failures = self.sim.stats["external_frag_failures"]
        self.metric_frag_val.configure(text=str(frag_failures))

        # 3. Label de Passos
        self.step_label.configure(text=f"Passo: {self.current_step} / {len(self.events)}")

        # 4. Atualizar Linhas da Aba "Fila de Eventos"
        for idx, row_frame in enumerate(self.event_row_widgets):
            # Checa o status de cada evento em relação ao passo atual
            if idx < self.current_step:
                # O evento já ocorreu
                # Verifica no histórico do passo correspondente (idx + 1) se foi sucesso
                state = self.sim.history[idx + 1]
                if state["success"]:
                    if "Alocação" in state["action"]:
                        row_frame.status_badge.configure(text="Sucesso", fg_color="#1b4d22", text_color="#7ae68c")
                    else:
                        row_frame.status_badge.configure(text="Liberado", fg_color="#3e3e42", text_color="#c5c5c9")
                else:
                    # Falhou: Identifica o motivo
                    log_text = state["log"]
                    if "FRAGMENTAÇÃO EXTERNA" in log_text:
                        row_frame.status_badge.configure(text="Frag. Externa", fg_color="#542e0c", text_color="#ffae59")
                    else:
                        row_frame.status_badge.configure(text="Sem Memória", fg_color="#521414", text_color="#ffa6a6")
                
                # Se foi o último executado, dá destaque
                if idx == self.current_step - 1:
                    row_frame.configure(fg_color="#182c3c", border_width=1, border_color=self.accent_blue)
                else:
                    row_frame.configure(fg_color="#1c1c1f", border_width=0)
            else:
                # Evento pendente
                row_frame.status_badge.configure(text="Pendente", fg_color="#27272a", text_color="#88888b")
                row_frame.configure(fg_color="#131316", border_width=0)

        # 5. Atualizar Gráficos do Matplotlib
        self.update_matplotlib_charts()

    def update_matplotlib_charts(self):
        """Redesenha os gráficos estatísticos do Matplotlib incorporados."""
        if not self.sim:
            return

        self.ax_util.clear()
        self.ax_pie.clear()

        # Gráfico 1: Utilização de Memória ao Longo do Tempo (Passos)
        history = self.sim.stats["utilization_history"]
        steps = list(range(len(history)))
        
        self.ax_util.plot(steps, history, marker='o', markersize=4, color=self.accent_blue, linewidth=2, label="Uso (%)")
        self.ax_util.fill_between(steps, history, color=self.accent_blue, alpha=0.15)
        
        # Destaca o passo atual no gráfico com uma bola amarela/laranja
        if 0 <= self.current_step < len(history):
            self.ax_util.plot(self.current_step, history[self.current_step], marker='o', markersize=8, color=self.warn_orange)

        self.ax_util.set_title("Utilização da Memória por Passo", fontsize=9, color='white', weight="bold")
        self.ax_util.set_xlabel("Número de Eventos Executados", fontsize=8, color='#aaaaaa')
        self.ax_util.set_ylabel("% Ocupação", fontsize=8, color='#aaaaaa')
        self.ax_util.set_ylim(-5, 105)
        self.ax_util.tick_params(colors='#aaaaaa', labelsize=7)
        self.ax_util.grid(True, linestyle=':', alpha=0.3, color='#5e5e64')
        self.ax_util.set_facecolor('#19191e')

        # Gráfico 2: Divisão de Sucesso e Falhas (Somente até o passo atual)
        # Varre o histórico até o passo atual (índice current_step)
        success_alloc = 0
        success_free = 0
        frag_failures = 0
        insuf_failures = 0

        for h in self.sim.history[1:self.current_step + 1]:
            if h["success"]:
                if "Alocação" in h["action"]:
                    success_alloc += 1
                else:
                    success_free += 1
            else:
                if "FRAGMENTAÇÃO EXTERNA" in h["log"]:
                    frag_failures += 1
                else:
                    insuf_failures += 1

        labels = ['Alocado', 'Liberado', 'Frag. Externa', 'Sem Memória']
        counts = [success_alloc, success_free, frag_failures, insuf_failures]
        colors = [self.success_green, '#707078', self.warn_orange, self.fail_red]

        # Filtra os dados de contagem maior que 0
        filtered_data = [(l, c, col) for l, c, col in zip(labels, counts, colors) if c > 0]
        
        if filtered_data:
            f_labels, f_counts, f_colors = zip(*filtered_data)
            self.ax_pie.pie(
                f_counts, 
                labels=f_labels, 
                colors=f_colors, 
                autopct='%1.0f%%', 
                startangle=90,
                textprops={'color': 'white', 'fontsize': 8, 'weight': 'bold'},
                wedgeprops={'edgecolor': '#242429', 'linewidth': 1}
            )
            self.ax_pie.axis('equal')
        else:
            self.ax_pie.text(0.5, 0.5, "Nenhum evento executado\nno passo atual.", 
                             color='#88888b', ha='center', va='center', fontsize=9, style='italic')
            self.ax_pie.axis('off')

        self.ax_pie.set_title("Status das Operações Executadas", fontsize=9, color='white', weight="bold")
        self.ax_pie.set_facecolor('#19191e')

        self.fig.tight_layout()
        self.fig_canvas.draw()

    def log_message(self, message: str):
        """Adiciona uma mensagem à caixa de texto de log de auditoria e rola a tela."""
        self.textbox_log.configure(state="normal")
        self.textbox_log.insert(tk.END, message + "\n")
        self.textbox_log.configure(state="disabled")
        self.textbox_log.see(tk.END)

    # ----------------- Parser de Arquivos de Texto -----------------

    def load_file(self):
        """Abre janela de diálogo do Windows para selecionar o arquivo de teste."""
        filepath = filedialog.askopenfilename(
            title="Selecionar Arquivo de Simulação",
            filetypes=[("Arquivos de Texto", "*.txt"), ("Todos os Arquivos", "*.*")]
        )
        if not filepath:
            return
        self.process_file(filepath)

    def process_file(self, filepath: str):
        """Lê o arquivo, valida a estrutura lógica e inicializa a simulação."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Limpa comentários e linhas em branco
            cleaned_lines = []
            for line in lines:
                line_str = line.strip()
                if not line_str or line_str.startswith("#"):
                    continue
                cleaned_lines.append(line_str)
                
            if not cleaned_lines:
                raise ValueError("O arquivo de simulação está vazio ou contém apenas comentários.")
                
            # Primeira linha: tamanho total de RAM física
            try:
                # Divide por espaços e pega o primeiro número
                total_size = int(cleaned_lines[0].split()[0])
                if total_size <= 0:
                    raise ValueError("O tamanho deve ser um valor inteiro positivo.")
            except Exception:
                raise ValueError("A primeira linha útil deve conter o tamanho total da memória (ex: 1000).")
                
            # Demais linhas: comandos sequenciais
            events = []
            for line_idx, line in enumerate(cleaned_lines[1:]):
                # Split flexível por espaços, vírgulas e ponto-e-vírgula
                tokens = [t.strip() for t in re.split(r'[,\s;]+', line) if t.strip()]
                if not tokens:
                    continue
                    
                command = tokens[0].lower()
                
                # Comando Alocação: A <ID> <Tamanho>
                if command in ["a", "alloc", "allocate", "alocar"]:
                    if len(tokens) < 3:
                        raise ValueError(f"Linha {line_idx+2}: Alocação incompleta. Formato: A <ID_PROCESSO> <TAMANHO>.")
                    proc_id = tokens[1]
                    try:
                        size = int(tokens[2])
                        if size <= 0:
                            raise ValueError()
                    except Exception:
                        raise ValueError(f"Linha {line_idx+2}: O tamanho solicitado '{tokens[2]}' deve ser um inteiro maior que zero.")
                    
                    events.append({
                        "type": "allocate", 
                        "process_id": proc_id, 
                        "size": size, 
                        "raw_line": f"Alocação {proc_id} ({size} B)"
                    })
                
                # Comando Liberação: D/L <ID>
                elif command in ["d", "l", "free", "release", "liberar", "desalocar", "r"]:
                    if len(tokens) < 2:
                        raise ValueError(f"Linha {line_idx+2}: Liberação incompleta. Formato: D/L <ID_PROCESSO>.")
                    proc_id = tokens[1]
                    
                    events.append({
                        "type": "release", 
                        "process_id": proc_id, 
                        "raw_line": f"Liberação {proc_id}"
                    })
                else:
                    raise ValueError(f"Linha {line_idx+2}: Comando '{tokens[0]}' inválido. Use 'A' para alocação ou 'D'/'L' para liberação.")
            
            # Configura o motor com a nova simulação carregada
            self.total_memory = total_size
            self.events = events
            self.sim = MemorySimulator(total_size)
            self.current_step = 0
            
            # Atualiza o arquivo ativo
            self.filepath_label.configure(text=os.path.basename(filepath))
            
            # Pausa a simulação
            self.is_playing = False
            self.update_play_button_text()
            if self.after_id:
                self.after_cancel(self.after_id)
                self.after_id = None
                
            # Atualiza a interface
            self.rebuild_event_list()
            self.update_ui()
            
            # Log inicial
            self.textbox_log.configure(state="normal")
            self.textbox_log.delete("1.0", tk.END)
            self.textbox_log.configure(state="disabled")
            self.log_message(f"=== NOVO ARQUIVO DE EVENTOS CARREGADO ===")
            self.log_message(f"Arquivo: {os.path.basename(filepath)}")
            self.log_message(f"Memória Total: {total_size} Bytes")
            self.log_message(f"Total de Ações: {len(events)}\n")
            
        except Exception as e:
            messagebox.showerror("Erro de Formatação no Arquivo", str(e))
            self.log_message(f"Erro de Parser: {str(e)}")

    def generate_sample_file(self):
        """Gera um arquivo txt estruturado de teste no diretório que o usuário escolher."""
        content = """# Simulador de Alocação de Memória Dinâmica - Exemplo SO
# -----------------------------------------------------------
# Linha 1: Tamanho total da Memória Física (ex: 1000)
1000

# Eventos:
# Alocação: A <ID_Processo> <Tamanho_Bytes>
# Liberação: D <ID_Processo> ou L <ID_Processo>

A P1 150
A P2 300
A P3 200
D P2
A P4 350
A P5 100
D P1
A P6 200
A P7 100
"""
        filepath = filedialog.asksaveasfilename(
            title="Salvar Arquivo de Exemplo",
            defaultextension=".txt",
            filetypes=[("Arquivos de Texto", "*.txt")],
            initialfile="teste_alocacao.txt"
        )
        if not filepath:
            return
            
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("Sucesso", f"Arquivo de exemplo criado e salvo em:\n{filepath}")
            self.process_file(filepath)
        except Exception as e:
            messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o arquivo: {str(e)}")

    # ----------------- Execução das Ações Manuais -----------------

    def ensure_manual_simulator(self):
        """Garante que haja um motor de simulação pronto para receber comandos avulsos."""
        if not self.sim:
            self.total_memory = 1000
            self.sim = MemorySimulator(self.total_memory)
            self.events = []
            self.current_step = 0
            self.filepath_label.configure(text="Controle Manual")
            self.rebuild_event_list()
            self.update_ui()
            self.log_message("Motor de simulação avulso criado com 1000 Bytes por padrão.")

    def execute_manual_alloc(self):
        """Efetua uma alocação manual e anexa na fila histórica de passos."""
        self.ensure_manual_simulator()

        proc_id = self.entry_alloc_id.get().strip()
        size_str = self.entry_alloc_size.get().strip()

        if not proc_id:
            messagebox.showerror("Erro de Input", "Preencha o ID do processo.")
            return
        
        try:
            size = int(size_str)
            if size <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Erro de Input", "Tamanho de alocação deve ser um valor inteiro positivo.")
            return

        # Verifica se o processo já está na memória antes de registrar na fila
        if proc_id in self.sim.stats["allocated_processes"]:
            messagebox.showerror("Erro de Alocação", f"O processo '{proc_id}' já está alocado na RAM.")
            return

        # Para compatibilidade com o sistema histórico passo-a-passo:
        # 1. Se o usuário estiver no meio da fila, descarta o histórico futuro
        if self.current_step < len(self.events):
            self.events = self.events[:self.current_step]
            self.sim.truncate_history_to(self.current_step)
            self.log_message("--- Histórico futuro descartado devido a inserção manual ---")

        # 2. Registra o novo evento no vetor
        event_entry = {
            "type": "allocate", 
            "process_id": proc_id, 
            "size": size, 
            "raw_line": f"Manual: Alocar {proc_id} ({size} B)"
        }
        self.events.append(event_entry)

        # 3. Executa o algoritmo ativo
        alg = self.algorithm_var.get()
        self.sim.allocate(alg, proc_id, size)
        
        # 4. Incrementa o passo atual
        self.current_step += 1

        # Limpa entries e atualiza UI
        self.entry_alloc_id.delete(0, tk.END)
        self.entry_alloc_size.delete(0, tk.END)
        
        self.rebuild_event_list()
        self.update_ui()

        # Loga no console textual
        newest_log = self.sim.history[self.current_step]["log"]
        self.log_message(f"--- [PASSO {self.current_step} - MANUAL] Alocação {proc_id} ---")
        self.log_message(newest_log + "\n")

    def execute_manual_free(self):
        """Efetua uma desalocação manual e anexa na fila histórica de passos."""
        self.ensure_manual_simulator()

        proc_id = self.entry_free_id.get().strip()

        if not proc_id:
            messagebox.showerror("Erro de Input", "Preencha o ID do processo a ser liberado.")
            return

        # Confirma se o processo está alocado
        if proc_id not in self.sim.stats["allocated_processes"]:
            messagebox.showerror("Erro de Liberação", f"O processo '{proc_id}' não está ativo na memória.")
            return

        # Se o usuário estiver no meio da fila, descarta o histórico futuro
        if self.current_step < len(self.events):
            self.events = self.events[:self.current_step]
            self.sim.truncate_history_to(self.current_step)
            self.log_message("--- Histórico futuro descartado devido a inserção manual ---")

        # Registra na fila
        event_entry = {
            "type": "release", 
            "process_id": proc_id, 
            "raw_line": f"Manual: Liberar {proc_id}"
        }
        self.events.append(event_entry)

        # Executa no motor
        self.sim.release(proc_id)
        
        # Incrementa passo
        self.current_step += 1

        self.entry_free_id.delete(0, tk.END)
        self.rebuild_event_list()
        self.update_ui()

        newest_log = self.sim.history[self.current_step]["log"]
        self.log_message(f"--- [PASSO {self.current_step} - MANUAL] Liberação {proc_id} ---")
        self.log_message(newest_log + "\n")


if __name__ == "__main__":
    app = App()
    app.mainloop()
