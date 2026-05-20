import tkinter as tk
from tkinter import ttk, messagebox

from core.formatters import converter_valor_digitado, formatar_moeda, formatar_numero
from ui.styles import configurar_tags_tabela


class LiberadosTab:
    def __init__(self, parent, controller, state, pedidos_tab=None):
        self.parent = parent
        self.controller = controller
        self.state = state
        self.pedidos_tab = pedidos_tab

        self.busca_var = tk.StringVar()
        self.valor_minimo_var = tk.StringVar(value="0")

        self.mapa_pedidos = {}

        self.criar_interface()

    def criar_interface(self):
        container = ttk.Frame(self.parent, padding=(8, 6))
        container.pack(fill="both", expand=True)

        self.criar_topo(container)
        self.criar_tabela(container)

    def criar_topo(self, parent):
        frame_topo = ttk.LabelFrame(
            parent,
            text="Pedidos liberados",
            padding=(8, 6),
            style="Section.TLabelframe"
        )
        frame_topo.pack(fill="x", pady=(0, 6))

        ttk.Label(frame_topo, text="Busca geral").grid(row=0, column=0, sticky="w", padx=(0, 5))

        entrada = ttk.Entry(frame_topo, textvariable=self.busca_var, width=34)
        entrada.grid(row=0, column=1, sticky="w", padx=(0, 12))
        entrada.bind("<KeyRelease>", lambda event: self.refresh())

        ttk.Label(frame_topo, text="Valor mín. liberado").grid(row=0, column=2, sticky="w", padx=(0, 5))

        entrada_valor = ttk.Entry(frame_topo, textvariable=self.valor_minimo_var, width=12)
        entrada_valor.grid(row=0, column=3, sticky="w", padx=(0, 12))
        entrada_valor.bind("<KeyRelease>", lambda event: self.refresh())

        ttk.Button(
            frame_topo,
            text="Adicionar ao PROG 2",
            command=self.adicionar_selecionado_prog2,
            style="Primary.TButton"
        ).grid(row=0, column=4, sticky="w", padx=3)

        ttk.Button(
            frame_topo,
            text="Limpar filtros",
            command=self.limpar_filtros
        ).grid(row=0, column=5, sticky="w", padx=3)

        ttk.Label(
            frame_topo,
            text="Mostra somente pedidos sem itens bloqueados.",
            style="Hint.TLabel"
        ).grid(row=1, column=0, columnspan=6, sticky="w", pady=(6, 0))

        frame_topo.columnconfigure(6, weight=1)

    def criar_tabela(self, parent):
        frame_tabela = ttk.LabelFrame(
            parent,
            text="Carteira liberada para faturamento",
            padding=(8, 6),
            style="Section.TLabelframe"
        )
        frame_tabela.pack(fill="both", expand=True)

        colunas = (
            "Cliente",
            "Cliente Original",
            "Qtd. Itens Liberados",
            "Qtde Saldo Liberada",
            "Valor Liberado",
            "Status",
        )

        self.tabela = ttk.Treeview(frame_tabela, columns=colunas, show="tree headings")
        self.tabela.heading("#0", text="Pedido")
        self.tabela.column("#0", width=130, minwidth=100, anchor="w")

        larguras = {
            "Cliente": 130,
            "Cliente Original": 310,
            "Qtd. Itens Liberados": 130,
            "Qtde Saldo Liberada": 130,
            "Valor Liberado": 140,
            "Status": 160,
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

        scroll_y = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tabela.yview)
        scroll_x = ttk.Scrollbar(frame_tabela, orient="horizontal", command=self.tabela.xview)

        self.tabela.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tabela.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        frame_tabela.rowconfigure(0, weight=1)
        frame_tabela.columnconfigure(0, weight=1)

    def refresh(self):
        self.tabela.delete(*self.tabela.get_children())
        self.mapa_pedidos.clear()

        if not self.state.tem_dados():
            return

        df = self.state.gerar_df_pedidos_liberados()

        if df.empty:
            return

        termo = self.busca_var.get().strip().lower()
        valor_minimo = converter_valor_digitado(self.valor_minimo_var.get())

        if termo:
            df = df[
                df.astype(str).apply(
                    lambda linha: linha.str.lower().str.contains(termo, na=False).any(),
                    axis=1
                )
            ]

        if "Valor Liberado" in df.columns:
            df = df[df["Valor Liberado"] >= valor_minimo]

        for indice, (_, linha) in enumerate(df.iterrows(), start=1):
            pedido = str(linha["Pedido"])
            iid = f"liberado_{indice}"

            self.tabela.insert(
                "",
                "end",
                iid=iid,
                text=pedido,
                values=(
                    linha.get("Cliente", ""),
                    linha.get("Cliente Original", ""),
                    linha.get("Qtd. Itens Liberados", ""),
                    formatar_numero(linha.get("Qtde Saldo Liberada", 0)),
                    formatar_moeda(linha.get("Valor Liberado", 0)),
                    "✓ Liberado",
                ),
                tags=("pedido_liberado",),
            )

            self.mapa_pedidos[iid] = pedido

    def get_selected_pedido(self):
        selecionado = self.tabela.selection()

        if not selecionado:
            return None

        return self.mapa_pedidos.get(selecionado[0])

    def adicionar_selecionado_prog2(self):
        pedido = self.get_selected_pedido()

        if not pedido:
            messagebox.showwarning(
                "Nenhum pedido selecionado",
                "Selecione um pedido liberado para adicionar ao PROG 2."
            )
            return

        self.state.adicionar_pedido_prog2(pedido)
        self.controller.refresh_all()
        self.controller.set_status(f"Pedido {pedido} adicionado ao PROG 2.")

    def limpar_filtros(self):
        self.busca_var.set("")
        self.valor_minimo_var.set("0")
        self.refresh()