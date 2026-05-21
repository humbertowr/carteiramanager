import tkinter as tk
from tkinter import ttk

from core.formatters import converter_valor_digitado, formatar_moeda, formatar_numero
from ui.styles import configurar_tags_tabela
from ui.sortable_tree import aplicar_ordenacao_treeview


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
        self.pedidos_marcados = set()

        self.icone_marcado = "☑"
        self.icone_desmarcado = "☐"

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
            text="Filtros de carteira",
            padding=(10, 8),
            style="Section.TLabelframe"
        )
        frame_filtros.pack(fill="x", pady=(0, 6))

        linha_principal = ttk.Frame(frame_filtros)
        linha_principal.grid(row=0, column=0, sticky="ew")

        ttk.Label(linha_principal, text="Buscar", style="Hint.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 6))
        entrada_busca = ttk.Entry(linha_principal, textvariable=self.busca_var, width=38)
        entrada_busca.grid(row=0, column=1, sticky="w", padx=(0, 16))
        entrada_busca.bind("<KeyRelease>", lambda event: self.refresh())

        ttk.Label(linha_principal, text="Valor mín.", style="Hint.TLabel").grid(row=0, column=2, sticky="w", padx=(0, 6))
        entrada_valor = ttk.Entry(linha_principal, textvariable=self.valor_minimo_var, width=12)
        entrada_valor.grid(row=0, column=3, sticky="w", padx=(0, 16))
        entrada_valor.bind("<KeyRelease>", lambda event: self.controller.refresh_pedidos())

        ttk.Label(linha_principal, text="Status", style="Hint.TLabel").grid(row=0, column=4, sticky="w", padx=(0, 6))
        combo_status = ttk.Combobox(
            linha_principal,
            textvariable=self.filtro_status_var,
            values=["Todos", "Liberados", "Parciais", "Bloqueados"],
            state="readonly",
            width=13,
        )
        combo_status.grid(row=0, column=5, sticky="w", padx=(0, 16))
        combo_status.bind("<<ComboboxSelected>>", lambda event: self.refresh())

        ttk.Label(linha_principal, text="Grupo", style="Hint.TLabel").grid(row=0, column=6, sticky="w", padx=(0, 6))
        combo_grupo = ttk.Combobox(
            linha_principal,
            textvariable=self.filtro_grupo_var,
            values=["Todos", "I", "P"],
            state="readonly",
            width=8,
        )
        combo_grupo.grid(row=0, column=7, sticky="w", padx=(0, 16))
        combo_grupo.bind("<<ComboboxSelected>>", lambda event: self.refresh())

        ttk.Button(
            linha_principal,
            text="Limpar",
            command=self.limpar_filtros,
        ).grid(row=0, column=8, sticky="w")

        ttk.Label(
            frame_filtros,
            text="Clique nos cabeçalhos da tabela para ordenar. Para marcar pedidos, use somente a coluna Sel.",
            style="Hint.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(7, 0))

        frame_filtros.columnconfigure(0, weight=1)
        linha_principal.columnconfigure(9, weight=1)

    def criar_area_acoes(self, parent):
        frame_acoes = ttk.LabelFrame(
            parent,
            text="Ações rápidas",
            padding=(10, 8),
            style="Section.TLabelframe"
        )
        frame_acoes.pack(fill="x")

        grupo_lote = ttk.LabelFrame(
            frame_acoes,
            text="PROG 2 em lote",
            padding=(8, 6),
            style="Action.TLabelframe"
        )
        grupo_lote.grid(row=0, column=0, sticky="nw", padx=(0, 8))

        ttk.Button(
            grupo_lote,
            text="Adicionar PROG2",
            command=self.adicionar_pedidos_marcados_prog2,
            style="Primary.TButton"
        ).grid(row=0, column=0, sticky="we", padx=2, pady=2)

        ttk.Button(
            grupo_lote,
            text="Desmarcar",
            command=self.desmarcar_todos_pedidos
        ).grid(row=0, column=1, sticky="we", padx=2, pady=2)

        grupo_bloqueios = ttk.LabelFrame(
            frame_acoes,
            text="Bloqueios globais",
            padding=(8, 6),
            style="Action.TLabelframe"
        )
        grupo_bloqueios.grid(row=0, column=1, sticky="nw", padx=(0, 8))

        ttk.Button(grupo_bloqueios, text="Itens", command=self.controller.abrir_janela_bloqueio_item).grid(row=0, column=0, sticky="w", padx=2, pady=2)
        ttk.Button(grupo_bloqueios, text="Clientes", command=self.controller.abrir_janela_bloqueio_cliente).grid(row=0, column=1, sticky="w", padx=2, pady=2)
        ttk.Button(grupo_bloqueios, text="Observações", command=self.controller.abrir_janela_bloqueio_observacao).grid(row=0, column=2, sticky="w", padx=2, pady=2)

        grupo_item_global = ttk.LabelFrame(
            frame_acoes,
            text="Item global",
            padding=(8, 6),
            style="Action.TLabelframe"
        )
        grupo_item_global.grid(row=0, column=2, sticky="nw")

        ttk.Label(grupo_item_global, text="Código:", style="Card.TLabel").grid(row=0, column=0, sticky="w", padx=(2, 4), pady=2)
        ttk.Entry(grupo_item_global, textvariable=self.item_global_var, width=14).grid(row=0, column=1, sticky="w", padx=2, pady=2)
        ttk.Button(grupo_item_global, text="Bloquear", command=self.controller.bloquear_item_global).grid(row=0, column=2, sticky="w", padx=2, pady=2)
        ttk.Button(grupo_item_global, text="Liberar", command=self.controller.liberar_item_global).grid(row=0, column=3, sticky="w", padx=2, pady=2)

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
            text="Indicadores: ☑ marcado | ☐ não marcado | ✓ liberado | ⚠ parcial | ✕ bloqueado",
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
            "Sel.",
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
        self.tabela.column("#0", width=390, minwidth=260, anchor="w", stretch=True)

        larguras = {
            "Sel.": 54,
            "Cliente": 320,
            "Qtde Saldo": 85,
            "Valor Pedido": 120,
            "Valor Bloqueado": 120,
            "Valor Liberado": 120,
            "Data Entrega": 100,
            "Grupo": 60,
            "Status": 175,
        }

        textos_cabecalho = {
            "Qtde Saldo": "Qtde",
            "Valor Pedido": "Vlr Pedido",
            "Valor Bloqueado": "Vlr Bloq.",
            "Valor Liberado": "Vlr Lib.",
            "Data Entrega": "Entrega",
        }

        for coluna in colunas:
            if coluna == "Sel.":
                self.tabela.heading(coluna, text="Sel.")
                self.tabela.column(
                    coluna,
                    width=larguras.get(coluna, 54),
                    minwidth=54,
                    anchor="center",
                    stretch=False
                )
                continue

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
                minwidth=50,
                anchor="w",
                stretch=False
            )

        configurar_tags_tabela(self.tabela)
        self.aplicar_ordenacao()
        self.tabela.bind("<Button-1>", self.on_click_tabela)

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

    def aplicar_ordenacao(self):
        aplicar_ordenacao_treeview(self.tabela)

    def on_click_tabela(self, event):
        coluna = self.tabela.identify_column(event.x)
        iid = self.tabela.identify_row(event.y)

        if coluna != "#1":
            return None

        if not iid or iid not in self.mapa_pedidos:
            return None

        if not iid.startswith("pedido_"):
            return None

        pedido = self.mapa_pedidos[iid]
        self.alternar_marcacao_pedido(pedido)
        return "break"

    def alternar_marcacao_pedido(self, pedido):
        pedido = str(pedido)

        if pedido in self.pedidos_marcados:
            self.pedidos_marcados.remove(pedido)
        else:
            self.pedidos_marcados.add(pedido)

        self.refresh()

    def desmarcar_todos_pedidos(self):
        self.pedidos_marcados.clear()
        self.refresh()

    def adicionar_pedidos_marcados_prog2(self):
        if not self.pedidos_marcados:
            self.controller.set_status("Nenhum pedido marcado.")
            return

        pedidos = sorted(self.pedidos_marcados)
        self.controller.adicionar_pedidos_selecionados_prog2(pedidos)
        self.pedidos_marcados.clear()
        self.refresh()

    def atualizar_label_marcados(self):
        pass

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
            self.atualizar_label_marcados()
            return

        termo = self.busca_var.get().strip().lower()
        valor_minimo = converter_valor_digitado(self.valor_minimo_var.get())
        filtro_grupo = self.filtro_grupo_var.get()

        df = self.controller.obter_df_com_bloqueios_cache()

        pedidos_prog2 = set(str(pedido) for pedido in self.state.pedidos_prog2)
        if pedidos_prog2:
            df = df[~df["Pedido Texto"].astype(str).isin(pedidos_prog2)]

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
        pedidos_visiveis = set()

        for indice, dados in enumerate(pedidos_processados, start=1):
            pedido = dados["pedido"]
            grupo = dados["grupo"]
            valor_original = dados["valor_original"]
            valor_bloqueado = dados["valor_bloqueado"]
            valor_liberado = dados["valor_liberado"]
            status_texto = dados["status_texto"]
            tags = dados["tags"]

            pedido_str = str(pedido)
            pedidos_visiveis.add(pedido_str)

            cliente = str(grupo["Cliente"].iloc[0])
            qtde_saldo = grupo["Saldo a Faturar"].sum()
            data_entrega = str(grupo["Data Entrega"].iloc[0])
            grupo_faturamento = str(grupo["Grupo Faturamento Abrev"].iloc[0])
            iid_pedido = f"pedido_{indice}"
            marcado = pedido_str in self.pedidos_marcados
            texto_checkbox = self.icone_marcado if marcado else self.icone_desmarcado
            tags_pedido = ("pedido_marcado",) if marcado else tags

            self.tabela.insert(
                "",
                "end",
                iid=iid_pedido,
                text=pedido_str,
                values=(
                    texto_checkbox,
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
                tags=tags_pedido,
            )

            self.mapa_pedidos[iid_pedido] = pedido_str

            for _, linha in grupo.iterrows():
                id_linha = int(linha["ID Linha"])
                bloqueado = bool(linha["_Bloqueado"])

                iid_item = f"item_{id_linha}"
                texto_item = f'   {linha["Item"]} - {linha["Descrição Item"]}'
                status_item = f'✕ {linha["_Tipo Bloqueio"]}' if bloqueado else "✓ Liberado"

                if marcado:
                    tags_item = ("item_marcado",)
                else:
                    tags_item = ("item_bloqueado",) if bloqueado else ("item_linha",)

                self.tabela.insert(
                    iid_pedido,
                    "end",
                    iid=iid_item,
                    text=texto_item,
                    values=(
                        "",
                        "",
                        formatar_numero(linha["Saldo a Faturar"]),
                        formatar_moeda(float(linha["Valor em Carteira"])),
                        formatar_moeda(float(linha["_Valor Bloqueado"])),
                        formatar_moeda(float(linha["_Valor Liberado"])),
                        "",
                        "",
                        status_item,
                    ),
                    tags=tags_item,
                )

                self.mapa_linhas[iid_item] = id_linha
                itens_exibidos += 1

            pedidos_exibidos += 1

        self.pedidos_marcados = {
            pedido for pedido in self.pedidos_marcados
            if pedido in pedidos_visiveis
        }

        self.atualizar_label_marcados()
        self.aplicar_ordenacao()

        self.controller.set_status(
            f"Pedidos exibidos: {pedidos_exibidos} | Itens exibidos: {itens_exibidos} | Pedidos marcados: {len(self.pedidos_marcados)}"
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
