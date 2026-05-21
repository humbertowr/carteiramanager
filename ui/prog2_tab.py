import tkinter as tk
from tkinter import ttk

from core.formatters import converter_valor_digitado, formatar_moeda, formatar_numero
from ui.styles import configurar_tags_tabela


class Prog2Tab:
    def __init__(self, parent, controller, state):
        self.parent = parent
        self.controller = controller
        self.state = state

        self.busca_var = tk.StringVar()
        self.meta_faturamento_var = tk.StringVar(value=self.carregar_meta_config())

        self.mapa_pedidos = {}
        self.pedidos_marcados = set()
        self.estado_expansao_pedidos = {}

        self.sort_coluna = "Valor Liberado"
        self.sort_ascendente = False

        self.valor_total_atual = 0
        self.valor_liberado_atual = 0

        self.criar_interface()

    def carregar_meta_config(self):
        try:
            config = getattr(self.controller, "config", {})
            settings = config.get("settings", {})
            return str(settings.get("meta_faturamento_dia", "") or "")
        except Exception:
            return ""

    def salvar_meta_config(self):
        try:
            config = getattr(self.controller, "config", None)
            config_manager = getattr(self.controller, "config_manager", None)

            if isinstance(config, dict) and config_manager:
                config.setdefault("settings", {})["meta_faturamento_dia"] = self.meta_faturamento_var.get().strip()
                config_manager.salvar(config)
        except Exception:
            pass

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
            text="Desmarcar todos",
            command=self.desmarcar_todos_pedidos
        ).grid(row=0, column=2, sticky="w", padx=3)

        ttk.Button(
            frame_topo,
            text="Remover marcado(s)",
            command=self.remover_pedidos_marcados,
            style="Danger.TButton"
        ).grid(row=0, column=3, sticky="w", padx=3)

        ttk.Button(
            frame_topo,
            text="Remover selecionado",
            command=self.controller.remover_pedido_selecionado_prog2
        ).grid(row=0, column=4, sticky="w", padx=3)

        ttk.Button(
            frame_topo,
            text="Limpar PROG 2",
            command=self.controller.limpar_prog2,
            style="Danger.TButton"
        ).grid(row=0, column=5, sticky="w", padx=3)

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
            text="Use a coluna Sel. para marcar pedidos. Clique nos cabeçalhos para ordenar.",
            style="Hint.TLabel"
        ).grid(row=1, column=2, columnspan=4, sticky="w", padx=(12, 0), pady=(6, 0))

        frame_topo.columnconfigure(6, weight=1)

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
        self.label_pedidos.grid(row=0, column=0, padx=(0, 18), sticky="w")

        self.label_itens = ttk.Label(frame_resumo, text="Itens: 0", style="SummaryValue.TLabel")
        self.label_itens.grid(row=0, column=1, padx=(0, 18), sticky="w")

        self.label_total = ttk.Label(frame_resumo, text="Valor total: R$ 0,00", style="SummaryValue.TLabel")
        self.label_total.grid(row=0, column=2, padx=(0, 18), sticky="w")

        self.label_liberado = ttk.Label(frame_resumo, text="Valor liberado: R$ 0,00", style="SummaryValue.TLabel")
        self.label_liberado.grid(row=0, column=3, padx=(0, 18), sticky="w")

        frame_meta = ttk.Frame(frame_resumo)
        frame_meta.grid(row=0, column=4, sticky="w", padx=(8, 0))

        linha_meta = ttk.Frame(frame_meta)
        linha_meta.pack(anchor="w")

        ttk.Label(linha_meta, text="Meta do dia:").pack(side="left", padx=(0, 5))

        entrada_meta = ttk.Entry(linha_meta, textvariable=self.meta_faturamento_var, width=15)
        entrada_meta.pack(side="left")

        entrada_meta.bind("<KeyRelease>", lambda event: self.atualizar_meta_display())
        entrada_meta.bind("<FocusOut>", lambda event: self.salvar_meta_config())
        entrada_meta.bind("<Return>", lambda event: self.salvar_meta_config())

        self.label_meta_faltante = ttk.Label(
            frame_meta,
            text="Falta para meta: R$ 0,00",
            style="SummaryValue.TLabel"
        )
        self.label_meta_faltante.pack(anchor="w", pady=(3, 0))

        frame_resumo.columnconfigure(5, weight=1)

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
            text="Indicadores: ☑ marcado | ☐ não marcado | ✓ liberado | ⚠ parcial | ✕ bloqueado",
            style="Subtitle.TLabel"
        ).pack(side="left")

        ttk.Button(barra_tabela, text="Expandir todos", command=self.expandir_todos).pack(side="right", padx=(4, 0))
        ttk.Button(barra_tabela, text="Recolher todos", command=self.recolher_todos).pack(side="right", padx=4)

        colunas = (
            "Sel.",
            "Cliente",
            "Valor Total Pedido",
            "Valor Bloqueado",
            "Valor Liberado",
            "Qtd. Itens",
            "Qtde Item",
            "Status",
        )

        self.tabela = ttk.Treeview(frame_tabela, columns=colunas, show="tree headings")

        self.tabela.heading("#0", text="Pedido / Item", command=lambda: self.alternar_ordenacao("Pedido"))
        self.tabela.column("#0", width=390, minwidth=260, anchor="w")

        larguras = {
            "Sel.": 58,
            "Cliente": 340,
            "Valor Total Pedido": 140,
            "Valor Bloqueado": 130,
            "Valor Liberado": 130,
            "Qtd. Itens": 85,
            "Qtde Item": 90,
            "Status": 185,
        }

        for coluna in colunas:
            self.tabela.heading(coluna, text=coluna, command=lambda c=coluna: self.alternar_ordenacao(c))
            self.tabela.column(
                coluna,
                width=larguras.get(coluna, 140),
                minwidth=50,
                anchor="center" if coluna == "Sel." else "w",
                stretch=False
            )

        configurar_tags_tabela(self.tabela)
        self.tabela.bind("<Button-1>", self.on_click_tabela)

        scroll_y = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tabela.yview)
        scroll_x = ttk.Scrollbar(frame_tabela, orient="horizontal", command=self.tabela.xview)

        self.tabela.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tabela.grid(row=1, column=0, sticky="nsew")
        scroll_y.grid(row=1, column=1, sticky="ns")
        scroll_x.grid(row=2, column=0, sticky="ew")

        frame_tabela.rowconfigure(1, weight=1)
        frame_tabela.columnconfigure(0, weight=1)

    def on_click_tabela(self, event):
        coluna = self.tabela.identify_column(event.x)
        iid = self.tabela.identify_row(event.y)

        if not iid or not iid.startswith("prog2_pedido_") or coluna != "#1":
            return None

        pedido = self.mapa_pedidos.get(iid)

        if not pedido:
            return None

        self.alternar_marcacao_pedido(pedido)
        return "break"

    def alternar_marcacao_pedido(self, pedido):
        pedido = str(pedido)

        if pedido in self.pedidos_marcados:
            self.pedidos_marcados.remove(pedido)
        else:
            self.pedidos_marcados.add(pedido)

        self.refresh()

    def capturar_estado_expansao(self):
        for iid, pedido in list(self.mapa_pedidos.items()):
            if not str(iid).startswith("prog2_pedido_"):
                continue

            try:
                if self.tabela.exists(iid):
                    self.estado_expansao_pedidos[str(pedido)] = bool(self.tabela.item(iid, "open"))
            except tk.TclError:
                pass

        return dict(self.estado_expansao_pedidos)

    def desmarcar_todos_pedidos(self):
        self.pedidos_marcados.clear()
        self.refresh()

    def remover_pedidos_marcados(self):
        if not self.pedidos_marcados:
            self.controller.set_status("Nenhum pedido marcado no PROG 2.")
            return

        self.controller.remover_pedidos_selecionados_prog2(sorted(self.pedidos_marcados))
        self.pedidos_marcados.clear()

    def alternar_ordenacao(self, coluna):
        if self.sort_coluna == coluna:
            self.sort_ascendente = not self.sort_ascendente
        else:
            self.sort_coluna = coluna
            self.sort_ascendente = True

        self.refresh()

    def chave_ordenacao(self, item):
        coluna = self.sort_coluna

        if coluna == "Pedido":
            return str(item["pedido"])
        if coluna == "Sel.":
            return 1 if str(item["pedido"]) in self.pedidos_marcados else 0
        if coluna == "Cliente":
            return item["cliente"].lower()
        if coluna == "Valor Total Pedido":
            return item["valor_total"]
        if coluna == "Valor Bloqueado":
            return item["valor_bloqueado"]
        if coluna == "Valor Liberado":
            return item["valor_liberado"]
        if coluna == "Qtd. Itens":
            return item["qtd_itens"]
        if coluna == "Status":
            return item["status"]

        return str(item["pedido"])

    def atualizar_cabecalhos(self):
        textos = {
            "Pedido": "Pedido / Item",
            "Sel.": "Sel.",
            "Cliente": "Cliente",
            "Valor Total Pedido": "Valor Total Pedido",
            "Valor Bloqueado": "Valor Bloqueado",
            "Valor Liberado": "Valor Liberado",
            "Qtd. Itens": "Qtd. Itens",
            "Qtde Item": "Qtde Item",
            "Status": "Status",
        }

        indicador = " ↑" if self.sort_ascendente else " ↓"

        self.tabela.heading(
            "#0",
            text=textos["Pedido"] + (indicador if self.sort_coluna == "Pedido" else ""),
            command=lambda: self.alternar_ordenacao("Pedido")
        )

        for coluna, texto in textos.items():
            if coluna == "Pedido":
                continue

            self.tabela.heading(
                coluna,
                text=texto + (indicador if self.sort_coluna == coluna else ""),
                command=lambda c=coluna: self.alternar_ordenacao(c)
            )

    def status_pedido(self, pedido_str, valor_total, valor_bloqueado):
        if pedido_str in self.state.pedidos_bloqueados:
            return "✕ Pedido bloqueado", ("pedido", "pedido_bloqueado")

        if self.state.pedido_bloqueado_por_cliente(pedido_str):
            return "✕ Cliente bloqueado", ("pedido", "pedido_bloqueado")

        if self.state.pedido_bloqueado_por_observacao(pedido_str):
            return "✕ Observação bloqueada", ("pedido", "pedido_bloqueado")

        if valor_total > 0 and valor_bloqueado >= valor_total:
            return "✕ Total bloqueado", ("pedido", "pedido_bloqueado")

        if valor_bloqueado > 0:
            return "⚠ Parcial", ("pedido", "pedido_parcial")

        return "✓ Liberado", ("pedido", "prog2")

    def atualizar_meta_display(self):
        meta = converter_valor_digitado(self.meta_faturamento_var.get())
        falta = meta - self.valor_liberado_atual

        if meta <= 0:
            self.label_meta_faltante.config(text="Falta para meta: R$ 0,00")
            return

        if falta > 0:
            self.label_meta_faltante.config(text=f"Falta para meta: {formatar_moeda(falta)}")
        else:
            self.label_meta_faltante.config(text=f"Meta superada em: {formatar_moeda(abs(falta))}")

    def refresh(self):
        estados_expansao = self.capturar_estado_expansao()

        self.tabela.delete(*self.tabela.get_children())
        self.mapa_pedidos.clear()
        self.atualizar_cabecalhos()

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
            pedido_str = str(pedido)
            cliente = str(grupo["Cliente"].iloc[0])
            qtd_itens = len(grupo)
            status, tags = self.status_pedido(pedido_str, valor_total, valor_bloqueado)

            pedidos_processados.append({
                "pedido": pedido_str,
                "grupo": grupo,
                "cliente": cliente,
                "qtd_itens": qtd_itens,
                "valor_total": valor_total,
                "valor_bloqueado": valor_bloqueado,
                "valor_liberado": valor_liberado,
                "status": status,
                "tags": tags,
            })

        pedidos_processados.sort(key=self.chave_ordenacao, reverse=not self.sort_ascendente)

        pedidos_exibidos = 0
        itens_exibidos = 0
        valor_total_lista = 0
        valor_liberado_lista = 0
        pedidos_visiveis = set()

        for indice, dados in enumerate(pedidos_processados, start=1):
            pedido_str = dados["pedido"]
            grupo = dados["grupo"]
            cliente = dados["cliente"]
            qtd_itens = dados["qtd_itens"]
            valor_total = dados["valor_total"]
            valor_bloqueado = dados["valor_bloqueado"]
            valor_liberado = dados["valor_liberado"]
            status = dados["status"]
            tags = dados["tags"]

            pedidos_visiveis.add(pedido_str)

            marcado = pedido_str in self.pedidos_marcados
            iid_pedido = f"prog2_pedido_{indice}"
            tags_pedido = ("pedido_marcado",) if marcado else tags

            self.tabela.insert(
                "",
                "end",
                iid=iid_pedido,
                text=pedido_str,
                values=(
                    "☑" if marcado else "☐",
                    cliente,
                    formatar_moeda(valor_total),
                    formatar_moeda(valor_bloqueado),
                    formatar_moeda(valor_liberado),
                    qtd_itens,
                    "",
                    status,
                ),
                open=estados_expansao.get(pedido_str, True),
                tags=tags_pedido,
            )

            self.mapa_pedidos[iid_pedido] = pedido_str

            for _, linha in grupo.iterrows():
                id_linha = int(linha["ID Linha"])
                bloqueado = bool(linha["_Bloqueado"])
                iid_item = f"prog2_item_{id_linha}"

                if marcado:
                    tags_item = ("item_marcado",)
                else:
                    tags_item = ("item_bloqueado",) if bloqueado else ("item_linha",)

                self.tabela.insert(
                    iid_pedido,
                    "end",
                    iid=iid_item,
                    text=f'{linha["Item"]} - {linha["Descrição Item"]}',
                    values=(
                        "",
                        "",
                        formatar_moeda(linha["Valor em Carteira"]),
                        formatar_moeda(linha["_Valor Bloqueado"]),
                        formatar_moeda(linha["_Valor Liberado"]),
                        "",
                        formatar_numero(linha["Saldo a Faturar"]),
                        f'✕ {linha["_Tipo Bloqueio"]}' if bloqueado else "✓ Liberado",
                    ),
                    tags=tags_item,
                )

                self.mapa_pedidos[iid_item] = pedido_str
                itens_exibidos += 1

            pedidos_exibidos += 1
            valor_total_lista += valor_total
            valor_liberado_lista += valor_liberado

        self.pedidos_marcados = {
            pedido for pedido in self.pedidos_marcados
            if pedido in pedidos_visiveis
        }

        self.atualizar_labels(pedidos_exibidos, itens_exibidos, valor_total_lista, valor_liberado_lista)

    def atualizar_labels(self, pedidos, itens, valor_total, valor_liberado):
        self.valor_total_atual = valor_total
        self.valor_liberado_atual = valor_liberado

        self.label_pedidos.config(text=f"Pedidos: {pedidos}")
        self.label_itens.config(text=f"Itens: {itens}")
        self.label_total.config(text=f"Valor total: {formatar_moeda(valor_total)}")
        self.label_liberado.config(text=f"Valor liberado: {formatar_moeda(valor_liberado)}")

        self.atualizar_meta_display()

    def get_selected_pedido(self):
        selecionado = self.tabela.selection()

        if not selecionado:
            return None

        return self.mapa_pedidos.get(selecionado[0])

    def expandir_todos(self):
        for item in self.tabela.get_children():
            self.tabela.item(item, open=True)
            pedido = self.mapa_pedidos.get(item)
            if pedido is not None:
                self.estado_expansao_pedidos[str(pedido)] = True

    def recolher_todos(self):
        for item in self.tabela.get_children():
            self.tabela.item(item, open=False)
            pedido = self.mapa_pedidos.get(item)
            if pedido is not None:
                self.estado_expansao_pedidos[str(pedido)] = False
