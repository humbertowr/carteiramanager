import tkinter as tk
from tkinter import ttk

import pandas as pd

from core.carteira_processor import obter_consolidacao
from core.formatters import formatar_moeda, formatar_numero
from ui.styles import configurar_tags_tabela
from ui.sortable_tree import aplicar_ordenacao_treeview
from ui.ux_helpers import aplicar_menu_generico_tabela


class ConsolidacoesTab:
    def __init__(self, parent, controller, state):
        self.parent = parent
        self.controller = controller
        self.state = state

        self.tipo_var = tk.StringVar(value="Por Item")
        self.busca_var = tk.StringVar()

        self.df_atual = pd.DataFrame()

        self.criar_interface()

    def criar_interface(self):
        container = ttk.Frame(self.parent, padding=(7, 5))
        container.pack(fill="both", expand=True)

        self.criar_topo(container)
        self.criar_tabela(container)

    def criar_topo(self, parent):
        frame_topo = ttk.LabelFrame(
            parent,
            text="Consolidações",
            padding=(7, 5),
            style="Section.TLabelframe"
        )
        frame_topo.pack(fill="x", pady=(0, 5))

        ttk.Label(frame_topo, text="Tipo", style="Hint.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 5))

        combo = ttk.Combobox(
            frame_topo,
            textvariable=self.tipo_var,
            values=[
                "Por Item",
                "Por Pedido",
                "Por Cliente",
                "Por Grupo de Faturamento",
                "Por Previsão de Faturamento",
            ],
            state="readonly",
            width=30
        )
        combo.grid(row=0, column=1, sticky="w", padx=(0, 12))
        combo.bind("<<ComboboxSelected>>", lambda event: self.refresh())

        ttk.Label(frame_topo, text="Buscar", style="Hint.TLabel").grid(row=0, column=2, sticky="w", padx=(0, 5))

        self.entrada_busca = ttk.Entry(frame_topo, textvariable=self.busca_var, width=34)
        self.entrada_busca.grid(row=0, column=3, sticky="w", padx=(0, 12))
        self.entrada_busca.bind("<KeyRelease>", lambda event: self.refresh())

        ttk.Button(
            frame_topo,
            text="Atualizar",
            command=self.refresh,
            style="Compact.TButton"
        ).grid(row=0, column=4, sticky="w", padx=3)

        ttk.Label(
            frame_topo,
            text="A exportação em CSV usa exatamente a visualização filtrada nesta aba. Clique nos cabeçalhos para ordenar.",
            style="Hint.TLabel"
        ).grid(row=1, column=0, columnspan=5, sticky="w", pady=(6, 0))

        frame_topo.columnconfigure(5, weight=1)

    def criar_tabela(self, parent):
        frame_tabela = ttk.LabelFrame(
            parent,
            text="Resultado consolidado",
            padding=(7, 5),
            style="Section.TLabelframe"
        )
        frame_tabela.pack(fill="both", expand=True)

        self.tabela = ttk.Treeview(frame_tabela, show="headings")

        configurar_tags_tabela(self.tabela)
        aplicar_ordenacao_treeview(self.tabela)

        self.scroll_y = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tabela.yview)
        self.scroll_x = ttk.Scrollbar(frame_tabela, orient="horizontal", command=self.tabela.xview)

        self.tabela.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)

        self.tabela.grid(row=0, column=0, sticky="nsew")
        self.scroll_y.grid(row=0, column=1, sticky="ns")
        self.scroll_x.grid(row=1, column=0, sticky="ew")

        frame_tabela.rowconfigure(0, weight=1)
        frame_tabela.columnconfigure(0, weight=1)
        aplicar_menu_generico_tabela(self, "Consolidações")

    def configurar_colunas(self, df):
        colunas = list(df.columns)

        self.tabela["columns"] = colunas

        larguras_padrao = {
            "Item": 110,
            "Descrição Item": 330,
            "Pedido": 120,
            "Cliente": 320,
            "Grupo Faturamento": 180,
            "Data Entrega": 130,
            "Qtd. Pedidos": 110,
            "Qtd. Clientes": 110,
            "Qtd. Itens": 110,
            "Qtde": 110,
            "Valor": 140,
        }

        for coluna in colunas:
            self.tabela.heading(coluna, text=coluna)
            self.tabela.column(
                coluna,
                width=larguras_padrao.get(coluna, 150),
                minwidth=90,
                anchor="w"
            )

    def focar_busca(self):
        if hasattr(self, "entrada_busca"):
            self.entrada_busca.focus_set()
            self.entrada_busca.selection_range(0, "end")

    def refresh(self):
        self.tabela.delete(*self.tabela.get_children())

        if not self.state.tem_dados():
            self.df_atual = pd.DataFrame()
            self.tabela["columns"] = []
            return

        df = obter_consolidacao(
            self.state.df_aberto(),
            self.tipo_var.get()
        )

        termo = self.busca_var.get().strip().lower()

        if termo and not df.empty:
            df = df[
                df.astype(str).apply(
                    lambda linha: linha.str.lower().str.contains(termo, na=False).any(),
                    axis=1
                )
            ]

        self.df_atual = df.copy()

        if df.empty:
            self.tabela["columns"] = []
            return

        self.configurar_colunas(df)
        aplicar_ordenacao_treeview(self.tabela)

        for indice, (_, linha) in enumerate(df.iterrows(), start=1):
            valores = []

            for coluna in df.columns:
                valor = linha[coluna]

                if "Valor" in coluna:
                    valores.append(formatar_moeda(valor))
                elif coluna in {"Qtde", "Qtd. Pedidos", "Qtd. Clientes", "Qtd. Itens"}:
                    valores.append(formatar_numero(valor))
                else:
                    valores.append(valor)

            tags = ("linha_alt",) if indice % 2 == 0 else ()

            self.tabela.insert(
                "",
                "end",
                values=valores,
                tags=tags,
            )

    def get_current_df(self):
        return self.df_atual