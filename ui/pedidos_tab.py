import tkinter as tk
from tkinter import ttk

from core.formatters import converter_valor_digitado, formatar_moeda, formatar_numero
from ui.styles import configurar_tags_tabela


class PedidosTab:
    def __init__(self, parent, controller, state):
        self.parent = parent
        self.controller = controller
        self.state = state

        self.busca_var = tk.StringVar()
        self.valor_minimo_var = tk.StringVar(value="1000")
        self.item_global_var = tk.StringVar()

        self.mapa_linhas = {}
        self.mapa_pedidos = {}

        self.ordenar_por_valor_liberado = False
        self.valor_liberado_desc = True

        self.criar_interface()

    def criar_interface(self):
        container = ttk.Frame(self.parent, padding=(6, 5))
        container.pack(fill="both", expand=True)

        self.criar_painel_acoes(container)
        self.criar_tabela(container)

    def criar_painel_acoes(self, parent):
        painel = ttk.Frame(parent)
        painel.pack(fill="x", pady=(0, 5))

        frame_filtros = ttk.LabelFrame(
            painel,
            text="Filtros da carteira",
            padding=(6, 4),
            style="Section.TLabelframe"
        )
        frame_filtros.pack(fill="x", pady=(0, 4))

        ttk.Label(frame_filtros, text="Buscar:").grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 4)
        )

        entrada_busca = ttk.Entry(
            frame_filtros,
            textvariable=self.busca_var,
            width=36
        )
        entrada_busca.grid(
            row=0,
            column=1,
            sticky="w",
            padx=(0, 10)
        )
        entrada_busca.bind("<KeyRelease>", lambda event: self.refresh())

        ttk.Label(frame_filtros, text="Valor mínimo liberado:").grid(
            row=0,
            column=2,
            sticky="w",
            padx=(0, 4)
        )

        entrada_valor = ttk.Entry(
            frame_filtros,
            textvariable=self.valor_minimo_var,
            width=13
        )
        entrada_valor.grid(
            row=0,
            column=3,
            sticky="w",
            padx=(0, 10)
        )
        entrada_valor.bind("<KeyRelease>", lambda event: self.controller.refresh_pedidos())

        ttk.Button(
            frame_filtros,
            text="Limpar filtros",
            command=self.limpar_filtros
        ).grid(
            row=0,
            column=4,
            sticky="w"
        )

        ttk.Label(
            frame_filtros,
            text="Clique no cabeçalho Valor Liberado para ordenar.",
            style="Hint.TLabel"
        ).grid(
            row=0,
            column=5,
            sticky="w",
            padx=(14, 0)
        )

        frame_filtros.columnconfigure(6, weight=1)

        frame_acoes = ttk.LabelFrame(
            painel,
            text="Ações rápidas",
            padding=(6, 4),
            style="Section.TLabelframe"
        )
        frame_acoes.pack(fill="x")

        bloco_bloqueios = ttk.Frame(frame_acoes)
        bloco_bloqueios.grid(row=0, column=0, sticky="w")

        ttk.Button(
            bloco_bloqueios,
            text="Bloquear item",
            command=self.controller.bloquear_item_selecionado
        ).pack(side="left", padx=(0, 4))

        ttk.Button(
            bloco_bloqueios,
            text="Bloquear pedido",
            command=self.controller.bloquear_pedido_selecionado
        ).pack(side="left", padx=4)

        ttk.Button(
            bloco_bloqueios,
            text="Itens",
            command=self.controller.abrir_janela_bloqueio_item
        ).pack(side="left", padx=4)

        ttk.Button(
            bloco_bloqueios,
            text="Clientes",
            command=self.controller.abrir_janela_bloqueio_cliente
        ).pack(side="left", padx=4)

        ttk.Button(
            bloco_bloqueios,
            text="Observação",
            command=self.controller.abrir_janela_bloqueio_observacao
        ).pack(side="left", padx=4)

        ttk.Button(
            bloco_bloqueios,
            text="Liberar seleção",
            command=self.controller.liberar_selecao_pedidos
        ).pack(side="left", padx=(4, 12))

        bloco_prog2 = ttk.Frame(frame_acoes)
        bloco_prog2.grid(row=0, column=1, sticky="w")

        ttk.Button(
            bloco_prog2,
            text="Adicionar ao PROG 2",
            command=self.controller.adicionar_pedido_selecionado_prog2,
            style="Primary.TButton"
        ).pack(side="left", padx=(0, 10))

        ttk.Label(bloco_prog2, text="Item global:").pack(side="left", padx=(0, 4))

        ttk.Entry(
            bloco_prog2,
            textvariable=self.item_global_var,
            width=12
        ).pack(side="left", padx=(0, 4))

        ttk.Button(
            bloco_prog2,
            text="Bloq. global",
            command=self.controller.bloquear_item_global
        ).pack(side="left", padx=4)

        ttk.Button(
            bloco_prog2,
            text="Lib. global",
            command=self.controller.liberar_item_global
        ).pack(side="left", padx=4)

        frame_acoes.columnconfigure(2, weight=1)

    def criar_tabela(self, parent):
        frame_tabela = ttk.LabelFrame(
            parent,
            text="Carteira de pedidos",
            padding=(6, 5),
            style="Section.TLabelframe"
        )
        frame_tabela.pack(fill="both", expand=True)

        barra_tabela = ttk.Frame(frame_tabela)
        barra_tabela.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        ttk.Label(
            barra_tabela,
            text="Pedidos e itens em aberto",
            style="Subtitle.TLabel"
        ).pack(side="left")

        ttk.Button(
            barra_tabela,
            text="Expandir todos",
            command=self.expandir_todos
        ).pack(side="right", padx=(4, 0))

        ttk.Button(
            barra_tabela,
            text="Recolher todos",
            command=self.recolher_todos
        ).pack(side="right", padx=4)

        colunas = (
            "Cliente",
            "Qtde Saldo",
            "Valor Pedido",
            "Valor Bloqueado",
            "Valor Liberado",
            "Data Entrega",
            "Grupo",
            "Status",
        )

        self.tabela = ttk.Treeview(
            frame_tabela,
            columns=colunas,
            show="tree headings"
        )

        self.tabela.heading("#0", text="Pedido / Item")
        self.tabela.column("#0", width=430, minwidth=260, anchor="w", stretch=True)

        larguras = {
            "Cliente": 150,
            "Qtde Saldo": 90,
            "Valor Pedido": 125,
            "Valor Bloqueado": 125,
            "Valor Liberado": 125,
            "Data Entrega": 105,
            "Grupo": 62,
            "Status": 185,
        }

        textos_cabecalho = {
            "Qtde Saldo": "Qtde",
            "Valor Pedido": "Vlr Pedido",
            "Valor Bloqueado": "Vlr Bloq.",
            "Valor Liberado": "Vlr Lib.",
            "Data Entrega": "Entrega",
            "Grupo": "Grupo",
            "Status": "Status",
            "Cliente": "Cliente",
        }

        for coluna in colunas:
            if coluna == "Valor Liberado":
                self.tabela.heading(
                    coluna,
                    text=textos_cabecalho[coluna],
                    command=self.alternar_ordenacao_valor_liberado
                )
            else:
                self.tabela.heading(coluna, text=textos_cabecalho.get(coluna, coluna))

            self.tabela.column(
                coluna,
                width=larguras.get(coluna, 120),
                minwidth=60,
                anchor="w",
                stretch=False
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

        self.tabela.grid(row=1, column=0, sticky="nsew")
        scroll_y.grid(row=1, column=1, sticky="ns")
        scroll_x.grid(row=2, column=0, sticky="ew")

        frame_tabela.rowconfigure(1, weight=1)
        frame_tabela.columnconfigure(0, weight=1)

    def alternar_ordenacao_valor_liberado(self):
        if not self.ordenar_por_valor_liberado:
            self.ordenar_por_valor_liberado = True
            self.valor_liberado_desc = True
        else:
            self.valor_liberado_desc = not self.valor_liberado_desc

        self.refresh()

    def atualizar_cabecalho_valor_liberado(self):
        if not self.ordenar_por_valor_liberado:
            texto = "Vlr Lib."
        elif self.valor_liberado_desc:
            texto = "Vlr Lib. ↓"
        else:
            texto = "Vlr Lib. ↑"

        self.tabela.heading(
            "Valor Liberado",
            text=texto,
            command=self.alternar_ordenacao_valor_liberado
        )

    def refresh(self):
        self.tabela.delete(*self.tabela.get_children())
        self.mapa_linhas.clear()
        self.mapa_pedidos.clear()
        self.atualizar_cabecalho_valor_liberado()

        if not self.state.tem_dados():
            return

        df = self.state.df_aberto()
        termo = self.busca_var.get().strip().lower()
        valor_minimo = converter_valor_digitado(self.valor_minimo_var.get())

        if termo:
            df = df[
                df[["Pedido", "Cliente", "Item", "Descrição Item"]]
                .astype(str)
                .apply(
                    lambda linha: linha.str.lower().str.contains(termo, na=False).any(),
                    axis=1
                )
            ]

        df = self.state.df_com_bloqueios(df)

        pedidos_processados = []

        for pedido, grupo in df.groupby("Pedido", sort=False):
            valor_original = grupo["Valor em Carteira"].sum()
            valor_bloqueado = grupo["_Valor Bloqueado"].sum()
            valor_liberado = grupo["_Valor Liberado"].sum()

            if valor_liberado < valor_minimo:
                continue

            pedidos_processados.append(
                {
                    "pedido": pedido,
                    "grupo": grupo,
                    "valor_original": valor_original,
                    "valor_bloqueado": valor_bloqueado,
                    "valor_liberado": valor_liberado,
                }
            )

        if self.ordenar_por_valor_liberado:
            pedidos_processados.sort(
                key=lambda item: item["valor_liberado"],
                reverse=self.valor_liberado_desc
            )

        pedidos_exibidos = 0
        itens_exibidos = 0

        for indice, dados in enumerate(pedidos_processados, start=1):
            pedido = dados["pedido"]
            grupo = dados["grupo"]
            valor_original = dados["valor_original"]
            valor_bloqueado = dados["valor_bloqueado"]
            valor_liberado = dados["valor_liberado"]

            pedido_str = str(pedido)
            cliente = self.state.abreviar_cliente(grupo["Cliente"].iloc[0])
            qtde_saldo = grupo["Saldo a Faturar"].sum()
            data_entrega = str(grupo["Data Entrega"].iloc[0])
            grupo_faturamento = str(grupo["Grupo Faturamento Abrev"].iloc[0])

            if pedido_str in self.state.pedidos_bloqueados:
                status = "Pedido bloqueado"
                tags = ("pedido", "pedido_bloqueado")
            elif self.state.pedido_bloqueado_por_cliente(pedido_str):
                status = "Bloqueado por cliente"
                tags = ("pedido", "pedido_bloqueado")
            elif self.state.pedido_bloqueado_por_observacao(pedido_str):
                status = "Bloqueado por observação"
                tags = ("pedido", "pedido_bloqueado")
            elif valor_original > 0 and valor_bloqueado >= valor_original:
                status = "Totalmente bloqueado"
                tags = ("pedido", "pedido_bloqueado")
            elif valor_bloqueado > 0:
                status = "Parcialmente bloqueado"
                tags = ("pedido", "pedido_parcial")
            else:
                status = "Liberado"
                tags = ("pedido",)

            iid_pedido = f"pedido_{indice}"

            self.tabela.insert(
                "",
                "end",
                iid=iid_pedido,
                text=pedido_str,
                values=(
                    cliente,
                    formatar_numero(qtde_saldo),
                    formatar_moeda(valor_original),
                    formatar_moeda(valor_bloqueado),
                    formatar_moeda(valor_liberado),
                    data_entrega,
                    grupo_faturamento,
                    status,
                ),
                open=True,
                tags=tags,
            )

            self.mapa_pedidos[iid_pedido] = pedido_str

            for _, linha in grupo.iterrows():
                id_linha = int(linha["ID Linha"])
                bloqueado = bool(linha["_Bloqueado"])
                valor_item = float(linha["Valor em Carteira"])
                valor_item_bloqueado = float(linha["_Valor Bloqueado"])
                valor_item_liberado = float(linha["_Valor Liberado"])

                iid_item = f"item_{id_linha}"
                texto_item = f'   {linha["Item"]} - {linha["Descrição Item"]}'
                status_item = linha["_Tipo Bloqueio"] if bloqueado else "Liberado"

                self.tabela.insert(
                    iid_pedido,
                    "end",
                    iid=iid_item,
                    text=texto_item,
                    values=(
                        "",
                        formatar_numero(linha["Saldo a Faturar"]),
                        formatar_moeda(valor_item),
                        formatar_moeda(valor_item_bloqueado),
                        formatar_moeda(valor_item_liberado),
                        "",
                        "",
                        status_item,
                    ),
                    tags=("item_bloqueado",) if bloqueado else ("item_linha",),
                )

                self.mapa_linhas[iid_item] = id_linha
                itens_exibidos += 1

            pedidos_exibidos += 1

        self.controller.set_status(
            f"Pedidos exibidos: {pedidos_exibidos} | Itens exibidos: {itens_exibidos}"
        )

    def get_motivo(self):
        return ""

    def get_codigo_item_global(self):
        codigo = self.item_global_var.get().strip()

        if codigo:
            return codigo

        return self.get_selected_item_codigo()

    def set_codigo_item_global(self, codigo):
        self.item_global_var.set(str(codigo))

    def get_selected_id_linha(self):
        selecionado = self.tabela.selection()

        if not selecionado:
            return None

        iid = selecionado[0]

        return self.mapa_linhas.get(iid)

    def get_selected_pedido(self):
        selecionado = self.tabela.selection()

        if not selecionado:
            return None

        iid = selecionado[0]

        if iid in self.mapa_pedidos:
            return self.mapa_pedidos[iid]

        id_linha = self.mapa_linhas.get(iid)

        if id_linha is None:
            return None

        linha = self.state.pegar_linha_por_id(id_linha)

        if linha is None:
            return None

        return str(linha["Pedido"])

    def get_selected_item_codigo(self):
        id_linha = self.get_selected_id_linha()

        if id_linha is None:
            return None

        linha = self.state.pegar_linha_por_id(id_linha)

        if linha is None:
            return None

        return str(linha["Item"])

    def limpar_filtros(self):
        self.busca_var.set("")
        self.valor_minimo_var.set("1000")
        self.controller.refresh_pedidos()

    def expandir_todos(self):
        for item in self.tabela.get_children():
            self.tabela.item(item, open=True)

    def recolher_todos(self):
        for item in self.tabela.get_children():
            self.tabela.item(item, open=False)