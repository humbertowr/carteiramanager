import tkinter as tk
from tkinter import ttk

from core.carteira_processor import obter_consolidacao
from core.formatters import formatar_moeda, formatar_numero


class ConsolidacoesTab:
    def __init__(self, parent, controller, state):
        self.parent = parent
        self.controller = controller
        self.state = state

        self.tipo_var = tk.StringVar(value="Carteira Detalhada")
        self.busca_var = tk.StringVar()
        self.df_visualizacao = None

        self.criar_interface()

    def criar_interface(self):
        container = ttk.Frame(self.parent, padding=8)
        container.pack(fill="both", expand=True)

        frame_filtros = ttk.LabelFrame(
            container,
            text="Filtros da consolidação",
            padding=8,
            style="Section.TLabelframe"
        )
        frame_filtros.pack(fill="x", pady=(0, 6))

        ttk.Label(frame_filtros, text="Consolidação:").grid(row=0, column=0, sticky="w", padx=(0, 5))

        opcoes = [
            "Carteira Detalhada",
            "Por Item",
            "Por Pedido",
            "Por Cliente",
            "Por Grupo de Faturamento",
            "Por Previsão de Faturamento",
        ]

        combo = ttk.Combobox(
            frame_filtros,
            textvariable=self.tipo_var,
            values=opcoes,
            state="readonly",
            width=32
        )
        combo.grid(row=0, column=1, sticky="w", padx=(0, 14))
        combo.bind("<<ComboboxSelected>>", lambda event: self.refresh())

        ttk.Label(frame_filtros, text="Buscar:").grid(row=0, column=2, sticky="w", padx=(0, 5))

        entrada_busca = ttk.Entry(
            frame_filtros,
            textvariable=self.busca_var,
            width=40
        )
        entrada_busca.grid(row=0, column=3, sticky="w", padx=(0, 8))
        entrada_busca.bind("<KeyRelease>", lambda event: self.aplicar_busca())

        ttk.Button(
            frame_filtros,
            text="Limpar busca",
            command=self.limpar_busca
        ).grid(row=0, column=4, sticky="w")

        frame_filtros.columnconfigure(5, weight=1)

        self.criar_tabela(container)

    def criar_tabela(self, parent):
        frame_tabela = ttk.LabelFrame(
            parent,
            text="Resultado",
            padding=8,
            style="Section.TLabelframe"
        )
        frame_tabela.pack(fill="both", expand=True)

        self.tabela = ttk.Treeview(frame_tabela, show="headings")

        scroll_y = ttk.Scrollbar(
            frame_tabela,
            orient="vertical",
            command=self.tabela.yview
        )

        scroll_x = ttk.Scrollbar(
            frame_tabela,
            orient="horizontal",
            command=self.tabela.xview
        )

        self.tabela.configure(
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )

        self.tabela.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        frame_tabela.rowconfigure(0, weight=1)
        frame_tabela.columnconfigure(0, weight=1)

    def refresh(self):
        if not self.state.tem_dados():
            return

        tipo = self.tipo_var.get()
        self.df_visualizacao = obter_consolidacao(self.state.df_original, tipo)

        self.busca_var.set("")
        self.preencher_tabela(self.df_visualizacao)

    def aplicar_busca(self):
        if self.df_visualizacao is None:
            return

        termo = self.busca_var.get().strip().lower()

        if termo == "":
            self.preencher_tabela(self.df_visualizacao)
            return

        df_filtrado = self.df_visualizacao[
            self.df_visualizacao.astype(str)
            .apply(
                lambda linha: linha.str.lower().str.contains(termo, na=False).any(),
                axis=1
            )
        ]

        self.preencher_tabela(df_filtrado)

    def limpar_busca(self):
        self.busca_var.set("")

        if self.df_visualizacao is not None:
            self.preencher_tabela(self.df_visualizacao)

    def preencher_tabela(self, df):
        self.tabela.delete(*self.tabela.get_children())

        colunas = list(df.columns)
        self.tabela["columns"] = colunas

        for coluna in colunas:
            self.tabela.heading(coluna, text=coluna)
            self.tabela.column(coluna, width=160, minwidth=100, anchor="w")

        limite_linhas = 1000
        df_exibicao = df.head(limite_linhas).copy()

        for _, linha in df_exibicao.iterrows():
            valores = []

            for coluna in colunas:
                valor = linha[coluna]

                if isinstance(valor, float):
                    if "Valor" in coluna:
                        valor = formatar_moeda(valor)
                    elif "%" in coluna:
                        valor = f"{valor:.2f}%".replace(".", ",")
                    else:
                        valor = formatar_numero(valor)

                valores.append(valor)

            self.tabela.insert("", "end", values=valores)

    def get_current_df(self):
        if self.df_visualizacao is None:
            return None

        return self.df_visualizacao