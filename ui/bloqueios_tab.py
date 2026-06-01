import tkinter as tk
from tkinter import ttk

from core.formatters import formatar_moeda, formatar_numero
from ui.styles import configurar_tags_tabela
from ui.sortable_tree import aplicar_ordenacao_treeview
from ui.ux_helpers import aplicar_menu_generico_tabela


class BloqueiosTab:
    def __init__(self, parent, controller, state):
        self.parent = parent
        self.controller = controller
        self.state = state

        self.busca_var = tk.StringVar()
        self.tipo_var = tk.StringVar(value="Todos")

        self.mapa_linhas = {}

        self.criar_interface()

    def criar_interface(self):
        container = ttk.Frame(self.parent, padding=(10, 8))
        container.pack(fill="both", expand=True)

        self.criar_topo(container)
        self.criar_tabela(container)

    def criar_topo(self, parent):
        frame_topo = ttk.LabelFrame(
            parent,
            text="Bloqueios aplicados",
            padding=(8, 6),
            style="Section.TLabelframe"
        )
        frame_topo.pack(fill="x", pady=(0, 6))

        ttk.Label(frame_topo, text="Buscar", style="Hint.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 5))

        self.entrada_busca = ttk.Entry(frame_topo, textvariable=self.busca_var, width=34)
        self.entrada_busca.grid(row=0, column=1, sticky="w", padx=(0, 12))
        self.entrada_busca.bind("<KeyRelease>", lambda event: self.refresh())

        ttk.Label(frame_topo, text="Tipo", style="Hint.TLabel").grid(row=0, column=2, sticky="w", padx=(0, 5))

        combo = ttk.Combobox(
            frame_topo,
            textvariable=self.tipo_var,
            values=[
                "Todos",
                "Pedido bloqueado",
                "Item bloqueado",
                "Item bloqueado global",
                "Cliente bloqueado",
                "Observação bloqueada",
            ],
            state="readonly",
            width=24
        )
        combo.grid(row=0, column=3, sticky="w", padx=(0, 12))
        combo.bind("<<ComboboxSelected>>", lambda event: self.refresh())

        ttk.Button(
            frame_topo,
            text="Liberar selecionado",
            command=self.controller.liberar_bloqueio_na_aba,
            style="Success.TButton"
        ).grid(row=0, column=4, sticky="w", padx=3)

        ttk.Button(
            frame_topo,
            text="Limpar todos",
            command=self.controller.limpar_todos_bloqueios,
            style="Danger.TButton"
        ).grid(row=0, column=5, sticky="w", padx=3)

        ttk.Label(
            frame_topo,
            text="Revise bloqueios por pedido, item, cliente ou observação. Clique nos cabeçalhos para ordenar.",
            style="Hint.TLabel"
        ).grid(row=1, column=0, columnspan=6, sticky="w", pady=(6, 0))

        frame_topo.columnconfigure(6, weight=1)

    def criar_tabela(self, parent):
        frame_tabela = ttk.LabelFrame(
            parent,
            text="Lista de bloqueios",
            padding=(8, 6),
            style="Section.TLabelframe"
        )
        frame_tabela.pack(fill="both", expand=True)

        colunas = (
            "Tipo Bloqueio",
            "Pedido",
            "Cliente",
            "Cliente Original",
            "Item",
            "Descrição Item",
            "Observação",
            "Qtde Saldo",
            "Valor Bloqueado",
            "Motivo",
        )

        self.tabela = ttk.Treeview(frame_tabela, columns=colunas, show="headings")

        larguras = {
            "Tipo Bloqueio": 180,
            "Pedido": 110,
            "Cliente": 130,
            "Cliente Original": 260,
            "Item": 100,
            "Descrição Item": 280,
            "Observação": 220,
            "Qtde Saldo": 100,
            "Valor Bloqueado": 130,
            "Motivo": 260,
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
        aplicar_ordenacao_treeview(self.tabela)

        scroll_y = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tabela.yview)
        scroll_x = ttk.Scrollbar(frame_tabela, orient="horizontal", command=self.tabela.xview)

        self.tabela.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tabela.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        frame_tabela.rowconfigure(0, weight=1)
        frame_tabela.columnconfigure(0, weight=1)
        aplicar_menu_generico_tabela(self, "Bloqueios")

    def focar_busca(self):
        if hasattr(self, "entrada_busca"):
            self.entrada_busca.focus_set()
            self.entrada_busca.selection_range(0, "end")

    def refresh(self):
        self.tabela.delete(*self.tabela.get_children())
        self.mapa_linhas.clear()

        if not self.state.tem_dados():
            return

        df = self.state.gerar_df_bloqueios()

        if df.empty:
            return

        termo = self.busca_var.get().strip().lower()
        tipo = self.tipo_var.get()

        if tipo != "Todos":
            df = df[df["Tipo Bloqueio"].astype(str).str.contains(tipo, case=False, na=False)]

        if termo:
            df = df[
                df.astype(str).apply(
                    lambda linha: linha.str.lower().str.contains(termo, na=False).any(),
                    axis=1
                )
            ]

        for indice, (_, linha) in enumerate(df.iterrows(), start=1):
            iid = f"bloqueio_{indice}"
            id_linha = int(linha.get("ID Linha", 0))

            self.tabela.insert(
                "",
                "end",
                iid=iid,
                values=(
                    linha.get("Tipo Bloqueio", ""),
                    linha.get("Pedido", ""),
                    linha.get("Cliente", ""),
                    linha.get("Cliente Original", ""),
                    linha.get("Item", ""),
                    linha.get("Descrição Item", ""),
                    linha.get("Observação", ""),
                    formatar_numero(linha.get("Qtde Saldo", 0)),
                    formatar_moeda(linha.get("Valor Bloqueado", 0)),
                    linha.get("Motivo", ""),
                ),
                tags=("item_bloqueado",),
            )

            self.mapa_linhas[iid] = id_linha

    def get_selected_id_linha(self):
        selecionado = self.tabela.selection()

        if not selecionado:
            return None

        return self.mapa_linhas.get(selecionado[0])