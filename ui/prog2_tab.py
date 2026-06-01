import tkinter as tk
from tkinter import ttk

from core.formatters import converter_valor_digitado, formatar_moeda, formatar_numero
from ui.styles import CORES, FONTE, configurar_tags_tabela
from ui.ux_helpers import abrir_janela_detalhes, copiar_para_clipboard, criar_menu_contexto, obter_texto_linha_treeview


MOTIVOS_PENDENCIA_PROG2 = (
    "Falta processo",
    "Falta usinagem",
    "Falta montagem",
    "Falta terceiro",
)


class Prog2Tab:
    def __init__(self, parent, controller, state):
        self.parent = parent
        self.controller = controller
        self.state = state

        self.busca_var = tk.StringVar()
        self.meta_faturamento_var = tk.StringVar(value=self.carregar_meta_config("meta_faturamento_dia"))
        self.meta_faturamento_mes_var = tk.StringVar(value=self.carregar_meta_config("meta_faturamento_mes"))

        self.mapa_pedidos = {}
        self.mapa_itens = {}
        self.pedidos_marcados = set()
        self.estado_expansao_pedidos = {}

        self.sort_coluna = "Valor Liberado"
        self.sort_ascendente = False

        self.valor_total_atual = 0
        self.valor_liberado_atual = 0

        self.criar_interface()

    def carregar_meta_config(self, chave):
        try:
            config = getattr(self.controller, "config", {})
            settings = config.get("settings", {})
            valor = str(settings.get(chave, "") or "").strip()
            if not valor:
                return ""
            return formatar_moeda(converter_valor_digitado(valor))
        except Exception:
            return ""

    def salvar_meta_config(self):
        try:
            config = getattr(self.controller, "config", None)
            config_manager = getattr(self.controller, "config_manager", None)

            if isinstance(config, dict) and config_manager:
                settings = config.setdefault("settings", {})
                settings["meta_faturamento_dia"] = self.meta_faturamento_var.get().strip()
                settings["meta_faturamento_mes"] = self.meta_faturamento_mes_var.get().strip()
                settings.pop("meta_faturamento_semana", None)
                config_manager.salvar(config)
        except Exception:
            pass

    def criar_interface(self):
        container = ttk.Frame(self.parent, padding=(10, 8))
        container.pack(fill="both", expand=True)

        self.criar_topo(container)
        self.criar_resumo(container)
        self.criar_metas(container)
        self.criar_tabela(container)
        self.criar_menu_contexto()

    def criar_topo(self, parent):
        frame_topo = ttk.LabelFrame(parent, text="Programação PROG 2", padding=(8, 5), style="Section.TLabelframe")
        frame_topo.pack(fill="x", pady=(0, 5))

        linha_1 = ttk.Frame(frame_topo)
        linha_1.pack(fill="x")

        ttk.Label(linha_1, text="Buscar", style="Hint.TLabel").pack(side="left", padx=(0, 6))
        self.entrada_busca = ttk.Entry(linha_1, textvariable=self.busca_var, width=46)
        self.entrada_busca.pack(side="left", padx=(0, 10))
        self.entrada_busca.bind("<KeyRelease>", lambda event: self.refresh())

        ttk.Button(linha_1, text="Desmarcar", command=self.desmarcar_todos_pedidos, style="Subtle.TButton").pack(side="left", padx=3)
        ttk.Button(linha_1, text="Remover marcados", command=self.remover_pedidos_marcados, style="Danger.TButton").pack(side="left", padx=3)
        ttk.Button(linha_1, text="Limpar PROG 2", command=self.controller.limpar_prog2, style="Danger.TButton").pack(side="left", padx=3)
        ttk.Button(linha_1, text="Fechar faturamento", command=self.controller.fechar_faturamento_prog2, style="Primary.TButton").pack(side="right", padx=(12, 0))

        ttk.Label(
            frame_topo,
            text="Botão direito no pedido ou item para ações rápidas. Pendências são aplicadas diretamente no item.",
            style="Hint.TLabel",
        ).pack(anchor="w", pady=(5, 0))

    def criar_menu_exportacao(self, parent, texto, comando_excel, comando_pdf):
        menu_button = ttk.Menubutton(parent, text=f"Exportar {texto} ▾")
        menu = tk.Menu(
            menu_button,
            tearoff=0,
            font=(FONTE, 9),
            background=CORES["card"],
            foreground=CORES["text"],
            activebackground=CORES["primary_soft"],
            relief="solid",
            borderwidth=1,
        )
        menu.add_command(label="Excel (.xlsx)", command=comando_excel)
        menu.add_command(label="Abrir PDF", command=comando_pdf)
        menu_button["menu"] = menu
        menu_button.pack(side="left", padx=(0, 6))

    def criar_resumo(self, parent):
        frame_resumo = ttk.LabelFrame(parent, text="Resumo", padding=(8, 5), style="Section.TLabelframe")
        frame_resumo.pack(fill="x", pady=(0, 5))

        self.label_pedidos = ttk.Label(frame_resumo, text="Pedidos: 0", style="SummaryValue.TLabel")
        self.label_pedidos.grid(row=0, column=0, padx=(0, 14), sticky="w")

        self.label_itens = ttk.Label(frame_resumo, text="Itens: 0", style="SummaryValue.TLabel")
        self.label_itens.grid(row=0, column=1, padx=(0, 14), sticky="w")

        self.label_itens_pendentes = ttk.Label(frame_resumo, text="Pendentes: 0", style="SummaryValue.TLabel")
        self.label_itens_pendentes.grid(row=0, column=2, padx=(0, 14), sticky="w")

        self.label_total = ttk.Label(frame_resumo, text="Total: R$ 0,00", style="SummaryValue.TLabel")
        self.label_total.grid(row=0, column=3, padx=(0, 14), sticky="w")

        self.label_liberado = ttk.Label(frame_resumo, text="Liberado: R$ 0,00", style="SummaryValue.TLabel")
        self.label_liberado.grid(row=0, column=4, padx=(0, 14), sticky="w")

        frame_resumo.columnconfigure(5, weight=1)

    def criar_metas(self, parent):
        frame_meta = ttk.LabelFrame(parent, text="Meta de faturamento", padding=(8, 5), style="Section.TLabelframe")
        frame_meta.pack(fill="x", pady=(0, 5))

        metas = (
            ("Dia", self.meta_faturamento_var),
            ("Mês", self.meta_faturamento_mes_var),
        )

        ttk.Label(frame_meta, text="Dia", style="Card.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 4))
        entrada_dia = ttk.Entry(frame_meta, textvariable=self.meta_faturamento_var, width=14)
        entrada_dia.grid(row=0, column=1, sticky="w", padx=(0, 12))

        ttk.Label(frame_meta, text="Mês", style="Card.TLabel").grid(row=0, column=2, sticky="w", padx=(0, 4))
        entrada_mes = ttk.Entry(frame_meta, textvariable=self.meta_faturamento_mes_var, width=14)
        entrada_mes.grid(row=0, column=3, sticky="w", padx=(0, 14))

        self.label_meta_resumo = ttk.Label(
            frame_meta,
            text="Dia: R$ 0,00 | falta R$ 0,00 | 0,0%    Mês: R$ 0,00 | falta R$ 0,00 | 0,0%",
            style="SummaryValue.TLabel"
        )
        self.label_meta_resumo.grid(row=0, column=4, sticky="w")

        for _, variavel in metas:
            variavel.trace_add("write", lambda *_: self.atualizar_meta_display())

        for entrada, variavel in ((entrada_dia, self.meta_faturamento_var), (entrada_mes, self.meta_faturamento_mes_var)):
            entrada.bind("<FocusOut>", lambda event, var=variavel: self.finalizar_meta_input(var))
            entrada.bind("<Return>", lambda event, var=variavel: self.finalizar_meta_input(var))

        frame_meta.columnconfigure(4, weight=1)

    def finalizar_meta_input(self, variavel):
        valor = converter_valor_digitado(variavel.get())
        variavel.set(formatar_moeda(valor) if valor > 0 else "")
        self.salvar_meta_config()
        self.atualizar_meta_display()
        return "break"

    def criar_tabela(self, parent):
        frame_tabela = ttk.LabelFrame(parent, text="Pedidos e itens selecionados", padding=(8, 5), style="Section.TLabelframe")
        frame_tabela.pack(fill="both", expand=True, pady=(0, 0))

        barra_tabela = ttk.Frame(frame_tabela)
        barra_tabela.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        ttk.Label(
            barra_tabela,
            text="☑ marcado | ✓ liberado | ⚠ parcial/pendente | ✕ bloqueado",
            style="Subtitle.TLabel",
        ).pack(side="left")

        acoes_tabela = ttk.Frame(barra_tabela)
        acoes_tabela.pack(side="right")

        ttk.Button(acoes_tabela, text="Recolher", command=self.recolher_todos, style="Compact.TButton").pack(side="left", padx=(0, 4))
        ttk.Button(acoes_tabela, text="Expandir", command=self.expandir_todos, style="Compact.TButton").pack(side="left", padx=(0, 8))

        self.criar_menu_exportacao(
            acoes_tabela,
            texto="Itens liberados",
            comando_excel=lambda: self.controller.exportar_prog2_itens_liberados("excel"),
            comando_pdf=lambda: self.controller.exportar_prog2_itens_liberados("pdf"),
        )
        self.criar_menu_exportacao(
            acoes_tabela,
            texto="Pedidos liberados",
            comando_excel=lambda: self.controller.exportar_prog2_pedidos_liberados("excel"),
            comando_pdf=lambda: self.controller.exportar_prog2_pedidos_liberados("pdf"),
        )

        colunas = (
            "Sel.",
            "Cliente",
            "Valor Total Pedido",
            "Valor Bloqueado",
            "Valor Liberado",
            "Qtd. Itens",
            "Qtde Item",
            "Pendência",
            "Status",
        )

        self.tabela = ttk.Treeview(frame_tabela, columns=colunas, show="tree headings")
        self.tabela.heading("#0", text="Pedido / Item", command=lambda: self.alternar_ordenacao("Pedido"))
        self.tabela.column("#0", width=455, minwidth=320, anchor="w")

        larguras = {
            "Sel.": 58,
            "Cliente": 320,
            "Valor Total Pedido": 135,
            "Valor Bloqueado": 130,
            "Valor Liberado": 130,
            "Qtd. Itens": 80,
            "Qtde Item": 90,
            "Pendência": 180,
            "Status": 175,
        }

        for coluna in colunas:
            self.tabela.heading(coluna, text=coluna, command=lambda c=coluna: self.alternar_ordenacao(c))
            self.tabela.column(
                coluna,
                width=larguras.get(coluna, 140),
                minwidth=50,
                anchor="center" if coluna == "Sel." else "w",
                stretch=False,
            )

        configurar_tags_tabela(self.tabela)
        self.tabela.bind("<Button-1>", self.on_click_tabela)
        self.tabela.bind("<Button-3>", self.on_right_click_tabela)
        self.tabela.bind("<Double-1>", self.on_double_click_tabela)

        scroll_y = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tabela.yview)
        scroll_x = ttk.Scrollbar(frame_tabela, orient="horizontal", command=self.tabela.xview)
        self.tabela.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tabela.grid(row=1, column=0, sticky="nsew")
        scroll_y.grid(row=1, column=1, sticky="ns")
        scroll_x.grid(row=2, column=0, sticky="ew")

        frame_tabela.rowconfigure(1, weight=1)
        frame_tabela.columnconfigure(0, weight=1)

    def criar_menu_contexto(self):
        self.menu_contexto = criar_menu_contexto(self.tabela)

        self.submenu_pendencias = criar_menu_contexto(self.menu_contexto)
        for motivo in MOTIVOS_PENDENCIA_PROG2:
            self.submenu_pendencias.add_command(label=motivo, command=lambda m=motivo: self.aplicar_pendencia_item_menu(m))

        self.menu_contexto.add_command(label="Ver detalhes", command=self.abrir_detalhes_selecionado)
        self.menu_contexto.add_separator()
        self.menu_contexto.add_cascade(label="Pendência do item", menu=self.submenu_pendencias)
        self.menu_contexto.add_command(label="Limpar pendência do item", command=self.limpar_pendencia_item_menu)
        self.menu_contexto.add_separator()
        self.menu_contexto.add_command(label="Remover pedido do PROG 2", command=self.remover_pedido_menu)
        self.menu_contexto.add_separator()
        self.menu_contexto.add_command(label="Copiar pedido", command=self.copiar_pedido_menu)
        self.menu_contexto.add_command(label="Copiar cliente", command=self.copiar_cliente_menu)
        self.menu_contexto.add_command(label="Copiar código do item", command=self.copiar_item_menu)
        self.menu_contexto.add_command(label="Copiar linha completa", command=self.copiar_linha_menu)
        self.menu_contexto.add_separator()
        self.menu_contexto.add_command(label="Expandir pedido", command=self.expandir_pedido_menu)
        self.menu_contexto.add_command(label="Recolher pedido", command=self.recolher_pedido_menu)

        self.item_menu_contexto = None
        self.pedido_menu_contexto = None
        self.iid_menu_contexto = None

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

    def on_right_click_tabela(self, event):
        iid = self.tabela.identify_row(event.y)
        if not iid:
            return "break"

        self.tabela.selection_set(iid)
        self.tabela.focus(iid)

        is_item = iid.startswith("prog2_item_")
        is_pedido = iid.startswith("prog2_pedido_")

        self.iid_menu_contexto = iid
        self.item_menu_contexto = self.mapa_itens.get(iid) if is_item else None
        self.pedido_menu_contexto = self.mapa_pedidos.get(iid)

        self.menu_contexto.entryconfigure("Ver detalhes", state="normal" if (is_item or is_pedido) else "disabled")
        self.menu_contexto.entryconfigure("Pendência do item", state="normal" if is_item else "disabled")
        self.menu_contexto.entryconfigure("Limpar pendência do item", state="normal" if is_item else "disabled")
        self.menu_contexto.entryconfigure("Remover pedido do PROG 2", state="normal" if self.pedido_menu_contexto else "disabled")
        self.menu_contexto.entryconfigure("Copiar pedido", state="normal" if self.pedido_menu_contexto else "disabled")
        self.menu_contexto.entryconfigure("Copiar cliente", state="normal" if self.pedido_menu_contexto else "disabled")
        self.menu_contexto.entryconfigure("Copiar código do item", state="normal" if is_item else "disabled")
        self.menu_contexto.entryconfigure("Copiar linha completa", state="normal" if (is_item or is_pedido) else "disabled")
        self.menu_contexto.entryconfigure("Expandir pedido", state="normal" if is_pedido else "disabled")
        self.menu_contexto.entryconfigure("Recolher pedido", state="normal" if is_pedido else "disabled")

        try:
            self.menu_contexto.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu_contexto.grab_release()
        return "break"

    def on_double_click_tabela(self, event):
        iid = self.tabela.identify_row(event.y)
        coluna = self.tabela.identify_column(event.x)
        if not iid or coluna == "#1":
            return None
        self.tabela.selection_set(iid)
        self.tabela.focus(iid)
        self.abrir_detalhes_selecionado()
        return "break"

    def focar_busca(self):
        if hasattr(self, "entrada_busca"):
            self.entrada_busca.focus_set()
            self.entrada_busca.selection_range(0, "end")

    def aplicar_pendencia_item_menu(self, motivo):
        if self.item_menu_contexto is None:
            self.controller.set_status("Clique com o botão direito diretamente em um item para aplicar pendência.")
            return
        self.controller.definir_pendencia_prog2_item(self.item_menu_contexto, motivo)

    def limpar_pendencia_item_menu(self):
        if self.item_menu_contexto is None:
            self.controller.set_status("Clique com o botão direito diretamente em um item para limpar pendência.")
            return
        self.controller.limpar_pendencia_prog2_item(self.item_menu_contexto)

    def remover_pedido_menu(self):
        if not self.pedido_menu_contexto:
            self.controller.set_status("Nenhum pedido selecionado no PROG 2.")
            return
        self.controller.remover_pedidos_selecionados_prog2([self.pedido_menu_contexto])

    def copiar_pedido_menu(self):
        if not self.pedido_menu_contexto:
            return
        self.tabela.clipboard_clear()
        self.tabela.clipboard_append(str(self.pedido_menu_contexto))
        self.controller.set_status(f"Pedido {self.pedido_menu_contexto} copiado.")

    def copiar_item_menu(self):
        if self.item_menu_contexto is None:
            return
        linha = self.state.pegar_linha_por_id(self.item_menu_contexto)
        if linha is None:
            return
        codigo = str(linha["Item"])
        self.tabela.clipboard_clear()
        self.tabela.clipboard_append(codigo)
        self.controller.set_status(f"Item {codigo} copiado.")

    def copiar_cliente_menu(self):
        cliente = self.get_selected_cliente()
        if not cliente:
            return
        copiar_para_clipboard(self.tabela, cliente, self.controller, f"Cliente copiado: {cliente}")

    def copiar_linha_menu(self):
        iid = self.iid_menu_contexto or (self.tabela.selection()[0] if self.tabela.selection() else None)
        if not iid:
            return
        copiar_para_clipboard(self.tabela, obter_texto_linha_treeview(self.tabela, iid), self.controller, "Linha copiada.")

    def abrir_detalhes_selecionado(self):
        detalhes = self.get_detalhes_selecionado()
        if not detalhes:
            self.controller.set_status("Nenhuma linha selecionada para detalhes.")
            return
        titulo, resumo, itens = detalhes
        abrir_janela_detalhes(self.parent, titulo, resumo, itens)

    def get_detalhes_selecionado(self):
        selecionado = self.tabela.selection()
        if not selecionado:
            return None

        iid = selecionado[0]
        id_linha = self.mapa_itens.get(iid)

        if id_linha is not None:
            linha = self.state.pegar_linha_por_id(id_linha)
            if linha is None:
                return None
            pendencia = self.state.pendencias_prog2.get(int(id_linha), "")
            return (
                f"Detalhes do item {linha['Item']}",
                [
                    ("Tipo", "Item PROG 2"),
                    ("Pedido", linha.get("Pedido", "")),
                    ("Cliente", linha.get("Cliente", "")),
                    ("Item", linha.get("Item", "")),
                    ("Descrição", linha.get("Descrição Item", "")),
                    ("Qtde saldo", formatar_numero(linha.get("Saldo a Faturar", 0))),
                    ("Valor carteira", formatar_moeda(linha.get("Valor em Carteira", 0))),
                    ("Pendência", pendencia or "-"),
                    ("Data entrega", linha.get("Data Entrega", "")),
                    ("Grupo", linha.get("Grupo Faturamento Abrev", "")),
                ],
                None,
            )

        pedido = self.mapa_pedidos.get(iid)
        if not pedido or not self.state.tem_dados():
            return None

        if hasattr(self.controller, "obter_df_com_bloqueios_cache"):
            df = self.controller.obter_df_com_bloqueios_cache()
        else:
            df = self.state.df_com_bloqueios(self.state.df_aberto())
        grupo = df[df["Pedido Texto"].astype(str) == str(pedido)]
        if grupo.empty:
            return None

        itens = []
        for _, linha in grupo.iterrows():
            id_item = int(linha["ID Linha"])
            itens.append({
                "Item": linha.get("Item", ""),
                "Descrição": linha.get("Descrição Item", ""),
                "Qtde": formatar_numero(linha.get("Saldo a Faturar", 0)),
                "Valor lib.": formatar_moeda(linha.get("_Valor Liberado", 0)),
                "Pendência": self.state.pendencias_prog2.get(id_item, "-"),
                "Status": "Bloqueado" if bool(linha.get("_Bloqueado", False)) else "Liberado",
            })

        pendentes = sum(1 for _, linha in grupo.iterrows() if int(linha["ID Linha"]) in self.state.pendencias_prog2)
        return (
            f"Detalhes do pedido {pedido}",
            [
                ("Tipo", "Pedido PROG 2"),
                ("Pedido", pedido),
                ("Cliente", grupo["Cliente"].iloc[0]),
                ("Itens", len(grupo)),
                ("Itens pendentes", pendentes),
                ("Qtde total", formatar_numero(grupo["Saldo a Faturar"].sum())),
                ("Valor pedido", formatar_moeda(grupo["Valor em Carteira"].sum())),
                ("Valor bloqueado", formatar_moeda(grupo["_Valor Bloqueado"].sum())),
                ("Valor liberado", formatar_moeda(grupo["_Valor Liberado"].sum())),
                ("Data entrega", grupo["Data Entrega"].iloc[0]),
                ("Grupo", grupo["Grupo Faturamento Abrev"].iloc[0]),
            ],
            itens,
        )

    def expandir_pedido_menu(self):
        iid = self.iid_menu_contexto
        if iid and iid.startswith("prog2_pedido_") and self.tabela.exists(iid):
            self.tabela.item(iid, open=True)
            pedido = self.mapa_pedidos.get(iid)
            if pedido is not None:
                self.estado_expansao_pedidos[str(pedido)] = True

    def recolher_pedido_menu(self):
        iid = self.iid_menu_contexto
        if iid and iid.startswith("prog2_pedido_") and self.tabela.exists(iid):
            self.tabela.item(iid, open=False)
            pedido = self.mapa_pedidos.get(iid)
            if pedido is not None:
                self.estado_expansao_pedidos[str(pedido)] = False

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
        if coluna in ("Qtde Item",):
            return
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
        if coluna == "Pendência":
            return item.get("pendencia_resumo", "")
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
            "Pendência": "Pendência",
            "Status": "Status",
        }
        indicador = " ↑" if self.sort_ascendente else " ↓"
        self.tabela.heading("#0", text=textos["Pedido"] + (indicador if self.sort_coluna == "Pedido" else ""), command=lambda: self.alternar_ordenacao("Pedido"))
        for coluna, texto in textos.items():
            if coluna == "Pedido":
                continue
            self.tabela.heading(coluna, text=texto + (indicador if self.sort_coluna == coluna else ""), command=lambda c=coluna: self.alternar_ordenacao(c))

    def status_pedido(self, pedido_str, valor_total, valor_bloqueado, qtd_pendencias=0):
        if pedido_str in self.state.pedidos_bloqueados:
            return "✕ Pedido bloqueado", ("pedido", "pedido_bloqueado")
        if self.state.pedido_bloqueado_por_cliente(pedido_str):
            return "✕ Cliente bloqueado", ("pedido", "pedido_bloqueado")
        if self.state.pedido_bloqueado_por_observacao(pedido_str):
            return "✕ Observação bloqueada", ("pedido", "pedido_bloqueado")
        if valor_total > 0 and valor_bloqueado >= valor_total:
            return "✕ Total bloqueado", ("pedido", "pedido_bloqueado")
        if qtd_pendencias > 0:
            return f"⚠ {qtd_pendencias} item(ns) pendente(s)", ("pedido", "pedido_parcial")
        if valor_bloqueado > 0:
            return "⚠ Parcial", ("pedido", "pedido_parcial")
        return "✓ Liberado", ("pedido", "prog2")

    def resumo_meta(self, valor_meta):
        meta = converter_valor_digitado(valor_meta)
        if meta <= 0:
            return "Falta: R$ 0,00", "0,0% atingido"
        falta = meta - self.valor_liberado_atual
        percentual = 0 if meta <= 0 else min(self.valor_liberado_atual / meta * 100, 999.9)
        if falta > 0:
            return f"Falta: {formatar_moeda(falta)}", f"{percentual:.1f}% atingido"
        return f"Superou: {formatar_moeda(abs(falta))}", f"{percentual:.1f}% atingido"

    def atualizar_meta_display(self):
        if not hasattr(self, "label_meta_resumo"):
            return

        meta_dia = converter_valor_digitado(self.meta_faturamento_var.get())
        meta_mes = converter_valor_digitado(self.meta_faturamento_mes_var.get())

        def resumo(valor_meta):
            falta = valor_meta - self.valor_liberado_atual
            percentual = 0 if valor_meta <= 0 else min(self.valor_liberado_atual / valor_meta * 100, 999.9)
            texto_falta = f"falta {formatar_moeda(falta)}" if falta > 0 else f"superou {formatar_moeda(abs(falta))}"
            return texto_falta, percentual

        falta_dia, percentual_dia = resumo(meta_dia)
        falta_mes, percentual_mes = resumo(meta_mes)

        self.label_meta_resumo.config(
            text=(
                f"Dia: {formatar_moeda(meta_dia)} | {falta_dia} | {percentual_dia:.1f}%    "
                f"Mês: {formatar_moeda(meta_mes)} | {falta_mes} | {percentual_mes:.1f}%"
            )
        )

    def refresh(self):
        estados_expansao = self.capturar_estado_expansao()
        self.tabela.delete(*self.tabela.get_children())
        self.mapa_pedidos.clear()
        self.mapa_itens.clear()
        self.atualizar_cabecalhos()

        if not self.state.tem_dados():
            self.atualizar_labels(0, 0, 0, 0, 0)
            return

        if hasattr(self.controller, "obter_df_com_bloqueios_cache"):
            df = self.controller.obter_df_com_bloqueios_cache()
        else:
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
                    .apply(lambda linha: linha.str.lower().str.contains(termo, na=False).any(), axis=1)
                ]
                if grupo_busca.empty:
                    continue

            valor_total = grupo["Valor em Carteira"].sum()
            valor_bloqueado = grupo["_Valor Bloqueado"].sum()
            valor_liberado = grupo["_Valor Liberado"].sum()
            pedido_str = str(pedido)
            cliente = str(grupo["Cliente"].iloc[0])
            qtd_itens = len(grupo)
            qtd_pendencias = sum(1 for _, linha in grupo.iterrows() if int(linha["ID Linha"]) in self.state.pendencias_prog2)
            pendencia_resumo = "-" if qtd_pendencias == 0 else f"{qtd_pendencias} item(ns)"
            status, tags = self.status_pedido(pedido_str, valor_total, valor_bloqueado, qtd_pendencias)

            pedidos_processados.append({
                "pedido": pedido_str,
                "grupo": grupo,
                "cliente": cliente,
                "qtd_itens": qtd_itens,
                "qtd_pendencias": qtd_pendencias,
                "valor_total": valor_total,
                "valor_bloqueado": valor_bloqueado,
                "valor_liberado": valor_liberado,
                "pendencia_resumo": pendencia_resumo,
                "status": status,
                "tags": tags,
            })

        pedidos_processados.sort(key=self.chave_ordenacao, reverse=not self.sort_ascendente)

        pedidos_exibidos = 0
        itens_exibidos = 0
        itens_pendentes = 0
        valor_total_lista = 0
        valor_liberado_lista = 0
        pedidos_visiveis = set()

        for indice, dados in enumerate(pedidos_processados, start=1):
            pedido_str = dados["pedido"]
            grupo = dados["grupo"]
            pedidos_visiveis.add(pedido_str)

            marcado = pedido_str in self.pedidos_marcados
            iid_pedido = f"prog2_pedido_{indice}"
            tags_pedido = ("pedido_marcado",) if marcado else dados["tags"]

            self.tabela.insert(
                "",
                "end",
                iid=iid_pedido,
                text=pedido_str,
                values=(
                    "☑" if marcado else "☐",
                    dados["cliente"],
                    formatar_moeda(dados["valor_total"]),
                    formatar_moeda(dados["valor_bloqueado"]),
                    formatar_moeda(dados["valor_liberado"]),
                    dados["qtd_itens"],
                    "",
                    dados["pendencia_resumo"],
                    dados["status"],
                ),
                open=estados_expansao.get(pedido_str, True),
                tags=tags_pedido,
            )
            self.mapa_pedidos[iid_pedido] = pedido_str

            for _, linha in grupo.iterrows():
                id_linha = int(linha["ID Linha"])
                bloqueado = bool(linha["_Bloqueado"])
                pendencia = self.state.pendencias_prog2.get(id_linha, "")
                iid_item = f"prog2_item_{id_linha}"

                if marcado:
                    tags_item = ("item_marcado",)
                elif bloqueado:
                    tags_item = ("item_bloqueado",)
                elif pendencia:
                    tags_item = ("pedido_parcial",)
                else:
                    tags_item = ("item_linha",)

                if bloqueado:
                    status_item = f'✕ {linha["_Tipo Bloqueio"]}'
                elif pendencia:
                    status_item = "⚠ Pendente"
                else:
                    status_item = "✓ Liberado"

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
                        pendencia or "-",
                        status_item,
                    ),
                    tags=tags_item,
                )
                self.mapa_pedidos[iid_item] = pedido_str
                self.mapa_itens[iid_item] = id_linha
                itens_exibidos += 1
                if pendencia:
                    itens_pendentes += 1

            pedidos_exibidos += 1
            valor_total_lista += dados["valor_total"]
            valor_liberado_lista += dados["valor_liberado"]

        self.pedidos_marcados = {pedido for pedido in self.pedidos_marcados if pedido in pedidos_visiveis}
        self.atualizar_labels(pedidos_exibidos, itens_exibidos, valor_total_lista, valor_liberado_lista, itens_pendentes)

    def atualizar_labels(self, pedidos, itens, valor_total, valor_liberado, itens_pendentes=0):
        self.valor_total_atual = valor_total
        self.valor_liberado_atual = valor_liberado
        self.label_pedidos.config(text=f"Pedidos: {pedidos}")
        self.label_itens.config(text=f"Itens: {itens}")
        self.label_itens_pendentes.config(text=f"Pendentes: {itens_pendentes}")
        self.label_total.config(text=f"Total: {formatar_moeda(valor_total)}")
        self.label_liberado.config(text=f"Liberado: {formatar_moeda(valor_liberado)}")
        self.atualizar_meta_display()

    def get_selected_pedido(self):
        selecionado = self.tabela.selection()
        if not selecionado:
            return None
        return self.mapa_pedidos.get(selecionado[0])

    def get_selected_cliente(self):
        selecionado = self.tabela.selection()
        if not selecionado:
            return None

        iid = selecionado[0]
        id_linha = self.mapa_itens.get(iid)
        if id_linha is not None:
            linha = self.state.pegar_linha_por_id(id_linha)
            if linha is not None:
                return str(linha.get("Cliente", ""))

        pedido = self.get_selected_pedido()
        if not pedido or not self.state.tem_dados():
            return None

        if hasattr(self.controller, "obter_df_com_bloqueios_cache"):
            df = self.controller.obter_df_com_bloqueios_cache()
        else:
            df = self.state.df_com_bloqueios(self.state.df_aberto())
        grupo = df[df["Pedido Texto"].astype(str) == str(pedido)]
        if grupo.empty:
            return None
        return str(grupo["Cliente"].iloc[0])

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
