from tkinter import ttk

from core.formatters import formatar_moeda, formatar_numero, normalizar_texto


class BloqueiosTab:
    def __init__(self, parent, controller, state):
        self.parent = parent
        self.controller = controller
        self.state = state

        self.mapa_linhas = {}

        self.criar_interface()

    def criar_interface(self):
        container = ttk.Frame(self.parent, padding=8)
        container.pack(fill="both", expand=True)

        frame_botoes = ttk.LabelFrame(
            container,
            text="Ações de bloqueio",
            padding=8,
            style="Section.TLabelframe"
        )
        frame_botoes.pack(fill="x", pady=(0, 6))

        ttk.Button(
            frame_botoes,
            text="Liberar bloqueio selecionado",
            command=self.controller.liberar_bloqueio_na_aba
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            frame_botoes,
            text="Limpar todos os bloqueios",
            command=self.controller.limpar_todos_bloqueios
        ).pack(side="left", padx=5)

        ttk.Label(
            frame_botoes,
            text="Lista bloqueios por item, pedido, cliente, item global ou observação.",
            style="Subtitle.TLabel"
        ).pack(side="left", padx=20)

        self.criar_tabela(container)

    def criar_tabela(self, parent):
        frame_tabela = ttk.LabelFrame(
            parent,
            text="Itens bloqueados",
            padding=8,
            style="Section.TLabelframe"
        )
        frame_tabela.pack(fill="both", expand=True)

        colunas = (
            "Tipo Bloqueio",
            "Pedido",
            "Cliente",
            "Item",
            "Descrição",
            "Observação",
            "Qtde Saldo",
            "Valor Bloqueado",
            "Motivo",
        )

        self.tabela = ttk.Treeview(
            frame_tabela,
            columns=colunas,
            show="headings"
        )

        larguras = {
            "Tipo Bloqueio": 190,
            "Pedido": 100,
            "Cliente": 160,
            "Item": 100,
            "Descrição": 300,
            "Observação": 240,
            "Qtde Saldo": 100,
            "Valor Bloqueado": 140,
            "Motivo": 240,
        }

        for coluna in colunas:
            self.tabela.heading(coluna, text=coluna)
            self.tabela.column(
                coluna,
                width=larguras.get(coluna, 140),
                minwidth=90,
                anchor="w"
            )

        self.tabela.tag_configure(
            "bloqueado",
            background="#f8d7da",
            foreground="#842029"
        )

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
        self.tabela.delete(*self.tabela.get_children())
        self.mapa_linhas.clear()

        if not self.state.tem_dados():
            return

        df = self.state.df_aberto()

        df_bloqueados = df[
            df.apply(
                lambda linha: self.state.linha_bloqueada(linha),
                axis=1
            )
        ].copy()

        if df_bloqueados.empty:
            return

        df_bloqueados.sort_values(["Pedido", "Item"], inplace=True)

        for _, linha in df_bloqueados.iterrows():
            id_linha = int(linha["ID Linha"])
            iid = f"bloqueado_{id_linha}"

            self.tabela.insert(
                "",
                "end",
                iid=iid,
                values=(
                    self.state.tipo_bloqueio_linha(linha),
                    linha["Pedido"],
                    self.state.abreviar_cliente(linha["Cliente"]),
                    linha["Item"],
                    linha["Descrição Item"],
                    normalizar_texto(linha["Observação"]),
                    formatar_numero(linha["Saldo a Faturar"]),
                    formatar_moeda(linha["Valor em Carteira"]),
                    self.state.motivo_bloqueio_linha(linha),
                ),
                tags=("bloqueado",),
            )

            self.mapa_linhas[iid] = id_linha

    def get_selected_id_linha(self):
        selecionado = self.tabela.selection()

        if not selecionado:
            return None

        return self.mapa_linhas.get(selecionado[0])