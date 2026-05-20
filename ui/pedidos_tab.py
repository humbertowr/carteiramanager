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
        self.filtro_status_var = tk.StringVar(value="Todos")
        self.filtro_grupo_var = tk.StringVar(value="Todos")
        self.item_global_var = tk.StringVar()

        self.mapa_linhas = {}
        self.mapa_pedidos = {}

        self.ordenar_por_valor_liberado = False
        self.valor_liberado_desc = True

        self.criar_interface()

    def criar_interface(self):
        container = ttk.Frame(self.parent, padding=(8, 6))
        container.pack(fill="both", expand=True)

        self.criar_painel_acoes(container)
        self.criar_tabela(container)

    def criar_painel_acoes(self, parent):
        painel = ttk.Frame(parent)
        painel.pack(fill="x", pady=(0, 6))

        self.criar_area_filtros(painel)
        self.criar_area_acoes(painel)

    def criar_area_filtros(self, parent):
        frame_filtros = ttk.LabelFrame(
            parent,
            text="Filtros da carteira",
            padding=(8, 6),
            style="Section.TLabelframe"
        )
        frame_filtros.pack(fill="x", pady=(0, 5))

        ttk.Label(frame_filtros, text="Busca geral").grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 5)
        )

        entrada_busca = ttk.Entry(
            frame_filtros,
            textvariable=self.busca_var,
            width=34
        )
        entrada_busca.grid(
            row=0,
            column=1,
            sticky="w",
            padx=(0, 14)
        )
        entrada_busca.bind("<KeyRelease>", lambda event: self.refresh())

        ttk.Label(frame_filtros, text="Valor mín. liberado").grid(
            row=0,
            column=2,
            sticky="w",
            padx=(0, 5)
        )

        entrada_valor = ttk.Entry(
            frame_filtros,
            textvariable=self.valor_minimo_var,
            width=12
        )
        entrada_valor.grid(
            row=0,
            column=3,
            sticky="w",
            padx=(0, 14)
        )
        entrada_valor.bind("<KeyRelease>", lambda event: self.controller.refresh_pedidos())

        ttk.Label(frame_filtros, text="Status").grid(
            row=0,
            column=4,
            sticky="w",
            padx=(0, 5)
        )

        combo_status = ttk.Combobox(
            frame_filtros,
            textvariable=self.filtro_status_var,
            values=["Todos", "Liberados", "Parciais", "Bloqueados"],
            state="readonly",
            width=13
        )
        combo_status.grid(
            row=0,
            column=5,
            sticky="w",
            padx=(0, 14)
        )
        combo_status.bind("<<ComboboxSelected>>", lambda event: self.refresh())

        ttk.Label(frame_filtros, text="Grupo").grid(
            row=0,
            column=6,
            sticky="w",
            padx=(0, 5)
        )

        combo_grupo = ttk.Combobox(
            frame_filtros,
            textvariable=self.filtro_grupo_var,
            values=["Todos", "I", "P"],
            state="readonly",
            width=8
        )
        combo_grupo.grid(
            row=0,
            column=7,
            sticky="w",
            padx=(0, 14)
        )
        combo_grupo.bind("<<ComboboxSelected>>", lambda event: self.refresh())

        ttk.Button(
            frame_filtros,
            text="Limpar filtros",
            command=self.limpar_filtros
        ).grid(
            row=0,
            column=8,
            sticky="w",
            padx=(0, 10)
        )

        ttk.Label(
            frame_filtros,
            text="Dica: clique no cabeçalho Vlr Lib. para alternar entre maior e menor valor.",
            style="Hint.TLabel"
        ).grid(
            row=1,
            column=0,
            columnspan=9,
            sticky="w",
            pady=(6, 0)
        )

        frame_filtros.columnconfigure(9, weight=1)

    def criar_area_acoes(self, parent):
        frame_acoes = ttk.LabelFrame(
            parent,
            text="Ações rápidas",
            padding=(8, 6),
            style="Section.TLabelframe"
        )
        frame_acoes.pack(fill="x")

        grupo_bloqueios = ttk.LabelFrame(
            frame_acoes,
            text="Bloqueios",
            padding=(6, 5),
            style="Action.TLabelframe"
        )
        grupo_bloqueios.grid(row=0, column=0, sticky="nw", padx=(0, 8))

        ttk.Button(
            grupo_bloqueios,
            text="Bloquear item",
            command=self.controller.bloquear_item_selecionado
        ).grid(row=0, column=0, sticky="w", padx=2, pady=2)

        ttk.Button(
            grupo_bloqueios,
            text="Bloquear pedido",
            command=self.controller.bloquear_pedido_selecionado
        ).grid(row=0, column=1, sticky="w", padx=2, pady=2)

        ttk.Button(
            grupo_bloqueios,
            text="Liberar seleção",
            command=self.controller.liberar_selecao_pedidos
        ).grid(row=0, column=2, sticky="w", padx=2, pady=2)

        ttk.Button(
            grupo_bloqueios,
            text="Por item",
            command=self.controller.abrir_janela_bloqueio_item
        ).grid(row=1, column=0, sticky="w", padx=2, pady=2)

        ttk.Button(
            grupo_bloqueios,
            text="Por cliente",
            command=self.controller.abrir_janela_bloqueio_cliente
        ).grid(row=1, column=1, sticky="w", padx=2, pady=2)

        ttk.Button(
            grupo_bloqueios,
            text="Por observação",
            command=self.controller.abrir_janela_bloqueio_observacao
        ).grid(row=1, column=2, sticky="w", padx=2, pady=2)

        grupo_programacao = ttk.LabelFrame(
            frame_acoes,
            text="Programação",
            padding=(6, 5),
            style="Action.TLabelframe"
        )
        grupo_programacao.grid(row=0, column=1, sticky="nw", padx=(0, 8))

        ttk.Button(
            grupo_programacao,
            text="Adicionar ao PROG 2",
            command=self.controller.adicionar_pedido_selecionado_prog2,
            style="Primary.TButton"
        ).grid(row=0, column=0, sticky="w", padx=2, pady=2)

        ttk.Label(
            grupo_programacao,
            text="Selecione um pedido ou item na carteira.",
            style="CardHint.TLabel"
        ).grid(row=1, column=0, sticky="w", padx=2, pady=(4, 2))

        grupo_item_global = ttk.LabelFrame(
            frame_acoes,
            text="Item global",
            padding=(6, 5),
            style="Action.TLabelframe"
        )
        grupo_item_global.grid(row=0, column=2, sticky="nw")

        ttk.Label(
            grupo_item_global,
            text="Código:",
            style="Card.TLabel"
        ).grid(row=0, column=0, sticky="w", padx=(2, 4), pady=2)

        ttk.Entry(
            grupo_item_global,
            textvariable=self.item_global_var,
            width=14
        ).grid(row=0, column=1, sticky="w", padx=2, pady=2)

        ttk.Button(
            grupo_item_global,
            text="Bloquear",
            command=self.controller.bloquear_item_global
        ).grid(row=0, column=2, sticky="w", padx=2, pady=2)

        ttk.Button(
            grupo_item_global,
            text="Liberar",
            command=self.controller.liberar_item_global
        ).grid(row=0, column=3, sticky="w", padx=2, pady=2)

        ttk.Label(
            grupo_item_global,
            text="Aplica o código em toda a carteira.",
            style="CardHint.TLabel"
        ).grid(row=1, column=0, columnspan=4, sticky="w", padx=2, pady=(4, 2))

        frame_acoes.columnconfigure(3, weight=1)

    def criar_tabela(self, parent):
        frame_tabela = ttk.LabelFrame(
            parent,
            text="Carteira de pedidos",
            padding=(8, 6),
            style="Section.TLabelframe"
        )
        frame_tabela.pack(fill="both", expand=True)

        barra_tabela = ttk.Frame(frame_tabela)
        barra_tabela.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))

        ttk.Label(
            barra_tabela,
            text="Indicadores: ✓ liberado | ⚠ parcial | ✕ bloqueado",
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

    def status_pedido(self, pedido_str, valor_original, valor_bloqueado):
        if pedido_str in self.state.pedidos_bloqueados:
            return "bloqueado", "✕ Pedido bloqueado", ("pedido", "pedido_bloqueado")

        if self.state.pedido_bloqueado_por_cliente(pedido_str):
            return "bloqueado", "✕ Cliente bloqueado", ("pedido", "pedido_bloqueado")

        if self.state.pedido_bloqueado_por_observacao(pedido_str):
            return "bloqueado", "✕ Observação bloqueada", ("pedido", "pedido_bloqueado")

        if valor_original > 0 and valor_bloqueado >= valor_original:
            return "bloqueado", "✕ Total bloqueado", ("pedido", "pedido_bloqueado")

        if valor_bloqueado > 0:
            return "parcial", "⚠ Parcial", ("pedido", "pedido_parcial")

        return "liberado", "✓ Liberado", ("pedido", "pedido_liberado")

    def pedido_passa_filtro_status(self, status_chave):
        filtro = self.filtro_status_var.get()

        if filtro == "Todos":
            return True

        if filtro == "Liberados":
            return status_chave == "liberado"

        if filtro == "Parciais":
            return status_chave == "parcial"

        if filtro == "Bloqueados":
            return status_chave == "bloqueado"

        return True

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
        filtro_grupo = self.filtro_grupo_var.get()

        if termo:
            df = df[
                df[["Pedido", "Cliente", "Item", "Descrição Item"]]
                .astype(str)
                .apply(
                    lambda linha: linha.str.lower().str.contains(termo, na=False).any(),
                    axis=1
                )
            ]

        if filtro_grupo in {"I", "P"}:
            df = df[df["Grupo Faturamento Abrev"].astype(str) == filtro_grupo]

        df = self.state.df_com_bloqueios(df)

        pedidos_processados = []

        for pedido, grupo in df.groupby("Pedido", sort=False):
            valor_original = grupo["Valor em Carteira"].sum()
            valor_bloqueado = grupo["_Valor Bloqueado"].sum()
            valor_liberado = grupo["_Valor Liberado"].sum()
            pedido_str = str(pedido)

            if valor_liberado < valor_minimo:
                continue

            status_chave, status_texto, tags = self.status_pedido(
                pedido_str,
                valor_original,
                valor_bloqueado
            )

            if not self.pedido_passa_filtro_status(status_chave):
                continue

            pedidos_processados.append({
                "pedido": pedido,
                "grupo": grupo,
                "valor_original": valor_original,
                "valor_bloqueado": valor_bloqueado,
                "valor_liberado": valor_liberado,
                "status_texto": status_texto,
                "tags": tags,
            })

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
            status_texto = dados["status_texto"]
            tags = dados["tags"]

            pedido_str = str(pedido)
            cliente = self.state.abreviar_cliente(grupo["Cliente"].iloc[0])
            qtde_saldo = grupo["Saldo a Faturar"].sum()
            data_entrega = str(grupo["Data Entrega"].iloc[0])
            grupo_faturamento = str(grupo["Grupo Faturamento Abrev"].iloc[0])

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
                    status_texto,
                ),
                open=True,
                tags=tags,
            )

            self.mapa_pedidos[iid_pedido] = pedido_str

            for _, linha in grupo.iterrows():
                id_linha = int(linha["ID Linha"])
                bloqueado = bool(linha["_Bloqueado"])

                iid_item = f"item_{id_linha}"
                texto_item = f'   {linha["Item"]} - {linha["Descrição Item"]}'
                status_item = f'✕ {linha["_Tipo Bloqueio"]}' if bloqueado else "✓ Liberado"

                self.tabela.insert(
                    iid_pedido,
                    "end",
                    iid=iid_item,
                    text=texto_item,
                    values=(
                        "",
                        formatar_numero(linha["Saldo a Faturar"]),
                        formatar_moeda(float(linha["Valor em Carteira"])),
                        formatar_moeda(float(linha["_Valor Bloqueado"])),
                        formatar_moeda(float(linha["_Valor Liberado"])),
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
        self.filtro_status_var.set("Todos")
        self.filtro_grupo_var.set("Todos")
        self.controller.refresh_pedidos()

    def expandir_todos(self):
        for item in self.tabela.get_children():
            self.tabela.item(item, open=True)

    def recolher_todos(self):
        for item in self.tabela.get_children():
            self.tabela.item(item, open=False)