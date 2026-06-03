import tkinter as tk
from tkinter import ttk, messagebox

from services.historico_service import HistoricoService
from ui.sortable_tree import aplicar_ordenacao_treeview
from ui.ux_helpers import aplicar_estado_vazio_treeview, aplicar_menu_generico_tabela, copiar_para_clipboard, criar_cabecalho_aba


class HistoricoTab:
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.service = HistoricoService()
        self.busca_var = tk.StringVar()
        self.acao_var = tk.StringVar(value="Todos")
        self._df_atual = self.service.para_dataframe([])

        self.criar_interface()

    def criar_interface(self):
        container = ttk.Frame(self.parent, padding=(8, 6))
        container.pack(fill="both", expand=True)

        criar_cabecalho_aba(container, "Histórico", "Auditoria das alterações operacionais do sistema.")
        self.criar_topo(container)
        self.criar_tabela(container)

    def criar_topo(self, parent):
        frame = ttk.LabelFrame(
            parent,
            text="Histórico de alterações",
            padding=(7, 5),
            style="Section.TLabelframe",
        )
        frame.pack(fill="x", pady=(0, 5))

        self.label_total = ttk.Label(frame, text="Registros: 0", style="SummaryValue.TLabel")
        self.label_total.grid(row=0, column=0, sticky="w", padx=(0, 20))

        self.label_usuarios = ttk.Label(frame, text="Usuários: 0", style="SummaryValue.TLabel")
        self.label_usuarios.grid(row=0, column=1, sticky="w", padx=(0, 20))

        self.label_ultimo = ttk.Label(frame, text="Último evento: -", style="SummaryValue.TLabel")
        self.label_ultimo.grid(row=0, column=2, sticky="w", padx=(0, 20))

        self.label_acao = ttk.Label(frame, text="Última ação: -", style="SummaryValue.TLabel")
        self.label_acao.grid(row=0, column=3, sticky="w", padx=(0, 20))

        frame.columnconfigure(4, weight=1)

        filtros = ttk.Frame(frame, style="Card.TFrame")
        filtros.grid(row=1, column=0, columnspan=5, sticky="ew", pady=(6, 0))

        ttk.Label(filtros, text="Buscar", style="Hint.TLabel").pack(side="left", padx=(0, 5))
        self.entrada_busca = ttk.Entry(filtros, textvariable=self.busca_var, width=36)
        self.entrada_busca.pack(side="left", padx=(0, 10))
        self.entrada_busca.bind("<KeyRelease>", lambda event: self.refresh())

        ttk.Label(filtros, text="Ação", style="Hint.TLabel").pack(side="left", padx=(0, 5))
        self.combo_acoes = ttk.Combobox(
            filtros,
            textvariable=self.acao_var,
            values=["Todos"],
            state="readonly",
            width=26,
        )
        self.combo_acoes.pack(side="left", padx=(0, 10))
        self.combo_acoes.bind("<<ComboboxSelected>>", lambda event: self.refresh())

        ttk.Button(
            filtros,
            text="Atualizar",
            command=self.refresh,
            style="Compact.TButton",
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            filtros,
            text="Limpar histórico",
            command=self.limpar_historico,
            style="Danger.TButton",
        ).pack(side="right")

    def criar_tabela(self, parent):
        frame = ttk.LabelFrame(
            parent,
            text="Eventos registrados",
            padding=(7, 5),
            style="Section.TLabelframe",
        )
        frame.pack(fill="both", expand=True)

        colunas = ("Usuário", "Ação", "Pedido", "Item", "Detalhe")
        self.tabela = ttk.Treeview(frame, columns=colunas, show="tree headings")
        self.tabela.heading("#0", text="Data/Hora")
        self.tabela.column("#0", width=145, minwidth=130, anchor="w", stretch=False)

        larguras = {
            "Usuário": 130,
            "Ação": 210,
            "Pedido": 105,
            "Item": 95,
            "Detalhe": 720,
        }

        for coluna in colunas:
            self.tabela.heading(coluna, text=coluna)
            self.tabela.column(
                coluna,
                width=larguras.get(coluna, 120),
                minwidth=70,
                anchor="w",
                stretch=coluna == "Detalhe",
            )

        self.tabela.tag_configure("linha_alt", background="#f8fafc")
        self.tabela.tag_configure("linha_recente", background="#eef6ff")
        aplicar_ordenacao_treeview(self.tabela)

        scroll_y = ttk.Scrollbar(frame, orient="vertical", command=self.tabela.yview)
        scroll_x = ttk.Scrollbar(frame, orient="horizontal", command=self.tabela.xview)
        self.tabela.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tabela.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        aplicar_menu_generico_tabela(self, "Histórico")
        self.adicionar_menu_extra()

    def adicionar_menu_extra(self):
        menu = getattr(self, "menu_contexto_generico", None)
        if not menu:
            return
        menu.add_separator()
        menu.add_command(label="Copiar detalhe", command=self.copiar_detalhe)

    def obter_historico(self):
        return self.controller.config.get("historico", []) if isinstance(self.controller.config, dict) else []

    def focar_busca(self):
        self.entrada_busca.focus_set()
        self.entrada_busca.selection_range(0, "end")

    def limpar_historico(self):
        confirmar = messagebox.askyesno(
            "Limpar histórico",
            "Deseja apagar o histórico de alterações?\n\nEssa ação não altera pedidos, PROG 2, pendências ou faturados.",
            parent=self.parent,
        )
        if not confirmar:
            return

        self.controller.config["historico"] = []
        self.controller.config_manager.salvar(self.controller.config)
        self.refresh()
        self.controller.set_status("Histórico de alterações limpo.")

    def copiar_detalhe(self):
        iid = self.tabela.focus() or (self.tabela.selection()[0] if self.tabela.selection() else "")
        if not iid:
            return
        valores = list(self.tabela.item(iid, "values") or [])
        detalhe = valores[4] if len(valores) >= 5 else ""
        copiar_para_clipboard(self.tabela, detalhe, self.controller, "Detalhe copiado.")

    def get_current_df(self):
        return self._df_atual.copy()

    def refresh(self):
        historico = self.obter_historico()
        acoes = self.service.acoes_disponiveis(historico)
        valor_atual = self.acao_var.get() or "Todos"
        self.combo_acoes["values"] = acoes
        if valor_atual not in acoes:
            self.acao_var.set("Todos")

        registros = self.service.filtrar(
            historico,
            termo=self.busca_var.get(),
            acao=self.acao_var.get(),
        )
        self._df_atual = self.service.para_dataframe(
            historico,
            termo=self.busca_var.get(),
            acao=self.acao_var.get(),
        )

        self.tabela.delete(*self.tabela.get_children())
        if not registros:
            aplicar_estado_vazio_treeview(self.tabela, "Nenhum evento encontrado no histórico.")
        for indice, registro in enumerate(registros):
            tags = ("linha_recente",) if indice < 3 else (("linha_alt",) if indice % 2 else ())
            self.tabela.insert(
                "",
                "end",
                text=registro.get("Data/Hora", ""),
                values=(
                    registro.get("Usuário", ""),
                    registro.get("Ação", ""),
                    registro.get("Pedido", ""),
                    registro.get("Item", ""),
                    registro.get("Detalhe", ""),
                ),
                tags=tags,
            )

        resumo = self.service.resumo(self.service.normalizar(historico))
        self.label_total.config(text=f"Registros: {resumo['total']}")
        self.label_usuarios.config(text=f"Usuários: {resumo['usuarios']}")
        self.label_ultimo.config(text=f"Último evento: {resumo['ultimo_evento']}")
        self.label_acao.config(text=f"Última ação: {resumo['acao_mais_recente']}")
