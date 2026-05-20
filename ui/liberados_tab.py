import tkinter as tk
from tkinter import ttk

from core.formatters import converter_valor_digitado, formatar_moeda, formatar_numero
from ui.styles import configurar_tags_tabela


class LiberadosTab:
    def __init__(self, parent, controller, state, pedidos_tab):
        self.parent = parent
        self.controller = controller
        self.state = state
        self.pedidos_tab = pedidos_tab

        self.busca_var = tk.StringVar()

        self.criar_interface()

    def criar_interface(self):
        container = ttk.Frame(self.parent, padding=8)
        container.pack(fill="both", expand=True)

        frame_filtros = ttk.LabelFrame(
            container,
            text="Filtros",
            padding=8,
            style="Section.TLabelframe"
        )
        frame_filtros.pack(fill="x", pady=(0, 6))

        ttk.Label(frame_filtros, text="Buscar:").grid(row=0, column=0, sticky="w", padx=(0, 5))

        entrada = ttk.Entry(
            frame_filtros,
            textvariable=self.busca_var,
            width=42
        )
        entrada.grid(row=0, column=1, sticky="w", padx=(0, 14))
        entrada.bind("<KeyRelease>", lambda event: self.refresh())

        ttk.Label(
            frame_filtros,
            text="Mostra somente pedidos com saldo aberto e itens liberados para faturar.",
            style="Subtitle.TLabel"
        ).grid(row=0, column=2, sticky="w")

        frame_filtros.columnconfigure(3, weight=1)

        self.criar_tabela(container)

    def criar_tabela(self, parent):
        frame_tabela = ttk.LabelFrame(
            parent,
            text="Pedidos liberados para faturamento",
            padding=8,
            style="Section.TLabelframe"
        )
        frame_tabela.pack(fill="both", expand=True)

        colunas = (
            "Cliente",
            "Qtde Saldo",
            "Valor Liberado",
            "Status",
        )

        self.tabela = ttk.Treeview(
            frame_tabela,
            columns=colunas,
            show="tree headings"
        )

        self.tabela.heading("#0", text="Pedido / Item")
        self.tabela.column("#0", width=430, minwidth=260, anchor="w")

        larguras = {
            "Cliente": 340,
            "Qtde Saldo": 110,
            "Valor Liberado": 150,
            "Status": 180,
        }

        for coluna in colunas:
            self.tabela.heading(coluna, text=coluna)
            self.tabela.column(
                coluna,
                width=larguras.get(coluna, 140),
                minwidth=90,
                anchor="w"
            )

        configurar_tags_tabela(self.tabela)

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

        frame_botoes = ttk.Frame(parent)
        frame_botoes.pack(fill="x", pady=(6, 0))

        ttk.Button(
            frame_botoes,
            text="Expandir todos",
            command=self.expandir_todos
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            frame_botoes,
            text="Recolher todos",
            command=self.recolher_todos
        ).pack(side="left", padx=5)

    def refresh(self):
        self.tabela.delete(*self.tabela.get_children())

        if not self.state.tem_dados():
            return

        df = self.state.df_aberto()
        termo = self.busca_var.get().strip().lower()
        valor_minimo = converter_valor_digitado(self.pedidos_tab.valor_minimo_var.get())

        df = df[
            ~df.apply(
                lambda linha: self.state.linha_bloqueada(linha),
                axis=1
            )
        ].copy()

        if termo:
            df = df[
                df[["Pedido", "Cliente", "Item", "Descrição Item"]]
                .astype(str)
                .apply(
                    lambda linha: linha.str.lower().str.contains(termo, na=False).any(),
                    axis=1
                )
            ]

        for indice, (pedido, grupo) in enumerate(df.groupby("Pedido", sort=False), start=1):
            valor_liberado = grupo["Valor em Carteira"].sum()

            if valor_liberado < valor_minimo:
                continue

            cliente = self.state.abreviar_cliente(grupo["Cliente"].iloc[0])
            qtde_saldo = grupo["Saldo a Faturar"].sum()
            iid_pedido = f"pedido_liberado_{indice}"

            self.tabela.insert(
                "",
                "end",
                iid=iid_pedido,
                text=str(pedido),
                values=(
                    cliente,
                    formatar_numero(qtde_saldo),
                    formatar_moeda(valor_liberado),
                    "Liberado para faturar",
                ),
                open=False,
                tags=("pedido", "item_liberado"),
            )

            for _, linha in grupo.iterrows():
                id_linha = int(linha["ID Linha"])

                self.tabela.insert(
                    iid_pedido,
                    "end",
                    iid=f"item_liberado_{id_linha}",
                    text=f'{linha["Item"]} - {linha["Descrição Item"]}',
                    values=(
                        "",
                        formatar_numero(linha["Saldo a Faturar"]),
                        formatar_moeda(linha["Valor em Carteira"]),
                        "Liberado",
                    ),
                )

    def expandir_todos(self):
        for item in self.tabela.get_children():
            self.tabela.item(item, open=True)

    def recolher_todos(self):
        for item in self.tabela.get_children():
            self.tabela.item(item, open=False)