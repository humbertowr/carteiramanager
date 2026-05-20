import tkinter as tk
from tkinter import ttk

from core.formatters import formatar_moeda, formatar_numero
from ui.styles import configurar_tags_tabela


class Prog2Tab:
    def __init__(self, parent, controller, state):
        self.parent = parent
        self.controller = controller
        self.state = state

        self.busca_var = tk.StringVar()
        self.mapa_pedidos = {}

        self.ordenar_por_valor_liberado = False
        self.valor_liberado_desc = True

        self.criar_interface()

    def criar_interface(self):
        container = ttk.Frame(self.parent, padding=(8, 6))
        container.pack(fill="both", expand=True)

        self.criar_topo(container)
        self.criar_resumo(container)
        self.criar_tabela(container)

    def criar_topo(self, parent):
        frame_topo = ttk.LabelFrame(
            parent,
            text="PROG 2",
            padding=(8, 6),
            style="Section.TLabelframe"
        )
        frame_topo.pack(fill="x", pady=(0, 6))

        ttk.Label(frame_topo, text="Busca geral").grid(row=0, column=0, sticky="w", padx=(0, 5))

        entrada = ttk.Entry(frame_topo, textvariable=self.busca_var, width=34)
        entrada.grid(row=0, column=1, sticky="w", padx=(0, 12))
        entrada.bind("<KeyRelease>", lambda event: self.refresh())

        ttk.Button(
            frame_topo,
            text="Remover selecionado",
            command=self.controller.remover_pedido_selecionado_prog2
        ).grid(row=0, column=2, sticky="w", padx=3)

        ttk.Button(
            frame_topo,
            text="Limpar PROG 2",
            command=self.controller.limpar_prog2,
            style="Danger.TButton"
        ).grid(row=0, column=3, sticky="w", padx=3)

        self.criar_menu_exportacao(
            frame_topo,
            texto="Itens liberados",
            comando_excel=lambda: self.controller.exportar_prog2_itens_liberados("excel"),
            comando_pdf=lambda: self.controller.exportar_prog2_itens_liberados("pdf"),
            row=1,
            column=0,
        )

        self.criar_menu_exportacao(
            frame_topo,
            texto="Pedidos liberados",
            comando_excel=lambda: self.controller.exportar_prog2_pedidos_liberados("excel"),
            comando_pdf=lambda: self.controller.exportar_prog2_pedidos_liberados("pdf"),
            row=1,
            column=1,
        )

        ttk.Label(
            frame_topo,
            text="Exportações consideram somente itens/pedidos liberados.",
            style="Hint.TLabel"
        ).grid(row=1, column=2, columnspan=3, sticky="w", padx=(12, 0), pady=(6, 0))

        frame_topo.columnconfigure(5, weight=1)

    def criar_menu_exportacao(self, parent, texto, comando_excel, comando_pdf, row, column):
        menu_button = ttk.Menubutton(parent, text=f"Exportar {texto} ▾")
        menu = tk.Menu(menu_button, tearoff=0)

        menu.add_command(label="Excel (.xlsx)", command=comando_excel)
        menu.add_command(label="Abrir PDF", command=comando_pdf)

        menu_button["menu"] = menu
        menu_button.grid(row=row, column=column, sticky="w", padx=3, pady=(6, 0))

    def criar_resumo(self, parent):
        frame_resumo = ttk.LabelFrame(
            parent,
            text="Resumo da programação",
            padding=(8, 6),
            style="Section.TLabelframe"
        )
        frame_resumo.pack(fill="x", pady=(0, 6))

        self.label_pedidos = ttk.Label(frame_resumo, text="Pedidos: 0", style="SummaryValue.TLabel")
        self.label_pedidos.grid(row=0, column=0, padx=(0, 22), sticky="w")

        self.label_itens = ttk.Label(frame_resumo, text="Itens: 0", style="SummaryValue.TLabel")
        self.label_itens.grid(row=0, column=1, padx=(0, 22), sticky="w")

        self.label_total = ttk.Label(frame_resumo, text="Valor total: R$ 0,00", style="SummaryValue.TLabel")
        self.label_total.grid(row=0, column=2, padx=(0, 22), sticky="w")

        self.label_liberado = ttk.Label(frame_resumo, text="Valor liberado: R$ 0,00", style="SummaryValue.TLabel")
        self.label_liberado.grid(row=0, column=3, padx=(0, 22), sticky="w")

        frame_resumo.columnconfigure(4, weight=1)

    def criar_tabela(self, parent):
        frame_tabela = ttk.LabelFrame(
            parent,
            text="Pedidos selecionados",
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

        ttk.Button(barra_tabela, text="Expandir todos", command=self.expandir_todos).pack(side="right", padx=(4, 0))
        ttk.Button(barra_tabela, text="Recolher todos", command=self.recolher_todos).pack(side="right", padx=4)

        colunas = (
            "Cliente",
            "Valor Total Pedido",
            "Valor Bloqueado",
            "Valor Liberado",
            "Qtd. Itens",
            "Qtde Item",
            "Status",
        )

        self.tabela = ttk.Treeview(frame_tabela, columns=colunas, show="tree headings")
        self.tabela.heading("#0", text="Pedido / Item")
        self.tabela.column("#0", width=430, minwidth=260, anchor="w")

        larguras = {
            "Cliente": 150,
            "Valor Total Pedido": 145,
            "Valor Bloqueado": 135,
            "Valor Liberado": 135,
            "Qtd. Itens": 85,
            "Qtde Item": 90,
            "Status": 190,
        }

        for coluna in colunas:
            if coluna == "Valor Liberado":
                self.tabela.heading(
                    coluna,
                    text="Valor Liberado",
                    command=self.alternar_ordenacao_valor_liberado
                )
            else:
                self.tabela.heading(coluna, text=coluna)

            self.tabela.column(
                coluna,
                width=larguras.get(coluna, 140),
                minwidth=80,
                anchor="w"
            )

        configurar_tags_tabela(self.tabela)

        scroll_y = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tabela.yview)
        scroll_x = ttk.Scrollbar(frame_tabela, orient="horizontal", command=self.tabela.xview)

        self.tabela.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

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
            texto = "Valor Liberado"
        elif self.valor_liberado_desc:
            texto = "Valor Liberado ↓"
        else:
            texto = "Valor Liberado ↑"

        self.tabela.heading(
            "Valor Liberado",
            text=texto,
            command=self.alternar_ordenacao_valor_liberado
        )

    def refresh(self):
        self.tabela.delete(*self.tabela.get_children())
        self.mapa_pedidos.clear()
        self.atualizar_cabecalho_valor_liberado()

        if not self.state.tem_dados():
            self.atualizar_labels(0, 0, 0, 0)
            return

        df = self.state.df_com_bloqueios(self.state.df_aberto())
        termo = self.busca_var.get().strip().lower()

        pedidos_processados = []

        for pedido in self.state.pedidos_prog2:
            grupo = df[df["Pedido Texto"] == str(pedido)]

            if grupo.empty:
                continue

            if termo:
                grupo_busca = grupo[
                    grupo[["Pedido", "Cliente", "Item", "Descrição Item"]]
                    .astype(str)
                    .apply(
                        lambda linha: linha.str.lower().str.contains(termo, na=False).any(),
                        axis=1
                    )
                ]

                if grupo_busca.empty:
                    continue

            valor_total = grupo["Valor em Carteira"].sum()
            valor_bloqueado = grupo["_Valor Bloqueado"].sum()
            valor_liberado = grupo["_Valor Liberado"].sum()

            pedidos_processados.append({
                "pedido": pedido,
                "grupo": grupo,
                "valor_total": valor_total,
                "valor_bloqueado": valor_bloqueado,
                "valor_liberado": valor_liberado,
            })

        if self.ordenar_por_valor_liberado:
            pedidos_processados.sort(
                key=lambda item: item["valor_liberado"],
                reverse=self.valor_liberado_desc
            )

        pedidos_exibidos = 0
        itens_exibidos = 0
        valor_total_lista = 0
        valor_liberado_lista = 0

        for indice, dados in enumerate(pedidos_processados, start=1):
            pedido = dados["pedido"]
            grupo = dados["grupo"]
            valor_total = dados["valor_total"]
            valor_bloqueado = dados["valor_bloqueado"]
            valor_liberado = dados["valor_liberado"]

            pedido_str = str(pedido)
            cliente = self.state.abreviar_cliente(grupo["Cliente"].iloc[0])
            qtd_itens = len(grupo)

            if pedido_str in self.state.pedidos_bloqueados:
                status = "✕ Pedido bloqueado"
                tags = ("pedido", "pedido_bloqueado")
            elif self.state.pedido_bloqueado_por_cliente(pedido_str):
                status = "✕ Cliente bloqueado"
                tags = ("pedido", "pedido_bloqueado")
            elif self.state.pedido_bloqueado_por_observacao(pedido_str):
                status = "✕ Observação bloqueada"
                tags = ("pedido", "pedido_bloqueado")
            elif valor_total > 0 and valor_bloqueado >= valor_total:
                status = "✕ Total bloqueado"
                tags = ("pedido", "pedido_bloqueado")
            elif valor_bloqueado > 0:
                status = "⚠ Parcial"
                tags = ("pedido", "pedido_parcial")
            else:
                status = "✓ Liberado"
                tags = ("pedido", "prog2")

            iid_pedido = f"prog2_pedido_{indice}"

            self.tabela.insert(
                "",
                "end",
                iid=iid_pedido,
                text=pedido_str,
                values=(
                    cliente,
                    formatar_moeda(valor_total),
                    formatar_moeda(valor_bloqueado),
                    formatar_moeda(valor_liberado),
                    qtd_itens,
                    "",
                    status,
                ),
                open=True,
                tags=tags,
            )

            self.mapa_pedidos[iid_pedido] = pedido_str

            for _, linha in grupo.iterrows():
                id_linha = int(linha["ID Linha"])
                bloqueado = bool(linha["_Bloqueado"])
                iid_item = f"prog2_item_{id_linha}"

                self.tabela.insert(
                    iid_pedido,
                    "end",
                    iid=iid_item,
                    text=f'{linha["Item"]} - {linha["Descrição Item"]}',
                    values=(
                        "",
                        formatar_moeda(linha["Valor em Carteira"]),
                        formatar_moeda(linha["_Valor Bloqueado"]),
                        formatar_moeda(linha["_Valor Liberado"]),
                        "",
                        formatar_numero(linha["Saldo a Faturar"]),
                        f'✕ {linha["_Tipo Bloqueio"]}' if bloqueado else "✓ Liberado",
                    ),
                    tags=("item_bloqueado",) if bloqueado else ("item_linha",),
                )

                self.mapa_pedidos[iid_item] = pedido_str
                itens_exibidos += 1

            pedidos_exibidos += 1
            valor_total_lista += valor_total
            valor_liberado_lista += valor_liberado

        self.atualizar_labels(
            pedidos_exibidos,
            itens_exibidos,
            valor_total_lista,
            valor_liberado_lista
        )

    def atualizar_labels(self, pedidos, itens, valor_total, valor_liberado):
        self.label_pedidos.config(text=f"Pedidos: {pedidos}")
        self.label_itens.config(text=f"Itens: {itens}")
        self.label_total.config(text=f"Valor total: {formatar_moeda(valor_total)}")
        self.label_liberado.config(text=f"Valor liberado: {formatar_moeda(valor_liberado)}")

    def get_selected_pedido(self):
        selecionado = self.tabela.selection()

        if not selecionado:
            return None

        return self.mapa_pedidos.get(selecionado[0])

    def expandir_todos(self):
        for item in self.tabela.get_children():
            self.tabela.item(item, open=True)

    def recolher_todos(self):
        for item in self.tabela.get_children():
            self.tabela.item(item, open=False)