import tkinter as tk
from tkinter import ttk

import pandas as pd

from core.formatters import formatar_moeda, formatar_numero
from ui.styles import configurar_tags_tabela
from ui.sortable_tree import aplicar_ordenacao_treeview


class FaturadosTab:
    def __init__(self, parent, controller, state):
        self.parent = parent
        self.controller = controller
        self.state = state

        self.busca_var = tk.StringVar()
        self.mapa_pedidos = {}
        self._df_faturados = pd.DataFrame()

        self.criar_interface()

    def criar_interface(self):
        container = ttk.Frame(self.parent, padding=(8, 6))
        container.pack(fill="both", expand=True)

        self.criar_resumo(container)
        self.criar_acoes(container)
        self.criar_tabela(container)

    def criar_resumo(self, parent):
        frame = ttk.LabelFrame(
            parent,
            text="Resumo de faturados",
            padding=(8, 6),
            style="Section.TLabelframe",
        )
        frame.pack(fill="x", pady=(0, 6))

        self.label_pedidos = ttk.Label(frame, text="Pedidos faturados: 0", style="SummaryValue.TLabel")
        self.label_pedidos.grid(row=0, column=0, sticky="w", padx=(0, 24))

        self.label_itens = ttk.Label(frame, text="Itens: 0", style="SummaryValue.TLabel")
        self.label_itens.grid(row=0, column=1, sticky="w", padx=(0, 24))

        self.label_valor_total = ttk.Label(frame, text="Valor total: R$ 0,00", style="SummaryValue.TLabel")
        self.label_valor_total.grid(row=0, column=2, sticky="w", padx=(0, 24))

        self.label_valor_liberado = ttk.Label(frame, text="Valor liberado: R$ 0,00", style="SummaryValue.TLabel")
        self.label_valor_liberado.grid(row=0, column=3, sticky="w", padx=(0, 24))

        frame.columnconfigure(4, weight=1)

    def criar_acoes(self, parent):
        frame = ttk.LabelFrame(
            parent,
            text="Ações",
            padding=(8, 6),
            style="Section.TLabelframe",
        )
        frame.pack(fill="x", pady=(0, 6))

        ttk.Label(frame, text="Buscar", style="Hint.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 6))

        entrada = ttk.Entry(frame, textvariable=self.busca_var, width=42)
        entrada.grid(row=0, column=1, sticky="w", padx=(0, 12))
        entrada.bind("<KeyRelease>", lambda event: self.refresh())

        ttk.Button(
            frame,
            text="Remover do faturamento",
            command=self.remover_selecionado,
            style="Danger.TButton",
        ).grid(row=0, column=2, sticky="w", padx=3)

        ttk.Label(
            frame,
            text="Remover faz o pedido voltar para a carteira, caso ele exista no CSV atual.",
            style="Hint.TLabel",
        ).grid(row=0, column=3, sticky="w", padx=(12, 0))

        frame.columnconfigure(4, weight=1)

    def criar_tabela(self, parent):
        frame = ttk.LabelFrame(
            parent,
            text="Pedidos faturados",
            padding=(8, 6),
            style="Section.TLabelframe",
        )
        frame.pack(fill="both", expand=True)

        barra = ttk.Frame(frame)
        barra.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))

        ttk.Label(
            barra,
            text="Pedidos fechados no PROG 2 ficam salvos localmente e não aparecem mais na carteira de pedidos.",
            style="Subtitle.TLabel",
        ).pack(side="left")

        ttk.Button(barra, text="Expandir todos", command=self.expandir_todos).pack(side="right", padx=(4, 0))
        ttk.Button(barra, text="Recolher todos", command=self.recolher_todos).pack(side="right", padx=4)

        colunas = (
            "Data Faturamento",
            "Cliente",
            "Data Entrega",
            "Qtde Saldo",
            "Valor Pedido",
            "Valor Bloqueado",
            "Valor Liberado",
            "Status",
        )

        self.tabela = ttk.Treeview(frame, columns=colunas, show="tree headings")
        self.tabela.heading("#0", text="Pedido / Item")
        self.tabela.column("#0", width=320, minwidth=220, anchor="w", stretch=True)

        larguras = {
            "Data Faturamento": 140,
            "Cliente": 340,
            "Data Entrega": 105,
            "Qtde Saldo": 90,
            "Valor Pedido": 130,
            "Valor Bloqueado": 130,
            "Valor Liberado": 130,
            "Status": 170,
        }

        textos = {
            "Qtde Saldo": "Qtde",
            "Valor Pedido": "Vlr Pedido",
            "Valor Bloqueado": "Vlr Bloq.",
            "Valor Liberado": "Vlr Lib.",
        }

        for coluna in colunas:
            self.tabela.heading(coluna, text=textos.get(coluna, coluna))
            self.tabela.column(
                coluna,
                width=larguras.get(coluna, 120),
                minwidth=60,
                anchor="w",
                stretch=False,
            )

        configurar_tags_tabela(self.tabela)
        self.tabela.tag_configure("faturado_pedido", background="#dcfce7", foreground="#166534")
        self.tabela.tag_configure("faturado_item", background="#f0fdf4", foreground="#14532d")
        self.aplicar_ordenacao()

        scroll_y = ttk.Scrollbar(frame, orient="vertical", command=self.tabela.yview)
        scroll_x = ttk.Scrollbar(frame, orient="horizontal", command=self.tabela.xview)

        self.tabela.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tabela.grid(row=1, column=0, sticky="nsew")
        scroll_y.grid(row=1, column=1, sticky="ns")
        scroll_x.grid(row=2, column=0, sticky="ew")

        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)

    def aplicar_ordenacao(self):
        aplicar_ordenacao_treeview(self.tabela)

    def pedidos_faturados(self):
        return sorted(str(pedido) for pedido in getattr(self.state, "pedidos_faturados", set()))

    def datas_faturamento(self):
        return getattr(self.state, "datas_faturamento_pedido", {})

    def df_base_faturados(self):
        if not self.state.tem_dados():
            return pd.DataFrame()

        pedidos = set(self.pedidos_faturados())

        if not pedidos:
            return pd.DataFrame()

        df = self.state.df_original.copy()
        coluna_pedido = "Pedido Texto" if "Pedido Texto" in df.columns else "Pedido"
        df = df[df[coluna_pedido].astype(str).isin(pedidos)].copy()

        if df.empty:
            return pd.DataFrame()

        if "Saldo a Faturar" in df.columns:
            df = df[df["Saldo a Faturar"] > 0].copy()

        if hasattr(self.state, "df_com_bloqueios"):
            df = self.state.df_com_bloqueios(df)
        else:
            df["_Bloqueado"] = False
            df["_Tipo Bloqueio"] = ""
            df["_Valor Bloqueado"] = 0
            df["_Valor Liberado"] = df["Valor em Carteira"]

        return df

    def get_current_df(self):
        pedidos = self.pedidos_faturados()
        datas = self.datas_faturamento()
        df = self.df_base_faturados()
        registros = []

        for pedido in pedidos:
            grupo = pd.DataFrame()

            if not df.empty:
                coluna_pedido = "Pedido Texto" if "Pedido Texto" in df.columns else "Pedido"
                grupo = df[df[coluna_pedido].astype(str) == str(pedido)]

            if grupo.empty:
                registros.append({
                    "Pedido": pedido,
                    "Data Faturamento": datas.get(pedido, ""),
                    "Cliente": "Não encontrado no CSV atual",
                    "Data Entrega": "",
                    "Qtd. Itens": 0,
                    "Qtde Saldo": 0,
                    "Valor Pedido": 0,
                    "Valor Bloqueado": 0,
                    "Valor Liberado": 0,
                    "Status": "Faturado salvo",
                })
                continue

            valor_total = grupo["Valor em Carteira"].sum()
            valor_bloqueado = grupo["_Valor Bloqueado"].sum() if "_Valor Bloqueado" in grupo.columns else 0
            valor_liberado = grupo["_Valor Liberado"].sum() if "_Valor Liberado" in grupo.columns else valor_total

            registros.append({
                "Pedido": pedido,
                "Data Faturamento": datas.get(pedido, ""),
                "Cliente": str(grupo["Cliente"].iloc[0]),
                "Data Entrega": str(grupo["Data Entrega"].iloc[0]) if "Data Entrega" in grupo.columns else "",
                "Qtd. Itens": len(grupo),
                "Qtde Saldo": grupo["Saldo a Faturar"].sum() if "Saldo a Faturar" in grupo.columns else 0,
                "Valor Pedido": valor_total,
                "Valor Bloqueado": valor_bloqueado,
                "Valor Liberado": valor_liberado,
                "Status": "Faturado",
            })

        return pd.DataFrame(registros)

    def refresh(self):
        self.tabela.delete(*self.tabela.get_children())
        self.mapa_pedidos.clear()

        pedidos = self.pedidos_faturados()
        datas = self.datas_faturamento()
        df = self.df_base_faturados()
        termo = self.busca_var.get().strip().lower()
        df_resumo = self.get_current_df()

        if termo and not df_resumo.empty:
            df_resumo = df_resumo[
                df_resumo[["Pedido", "Cliente", "Status"]]
                .astype(str)
                .apply(lambda linha: linha.str.lower().str.contains(termo, na=False).any(), axis=1)
            ]
            pedidos = [str(pedido) for pedido in df_resumo["Pedido"].tolist()]

        if df_resumo.empty:
            self._df_faturados = pd.DataFrame()
            self.atualizar_resumo(0, 0, 0, 0)
            return

        self._df_faturados = df_resumo.copy()

        total_pedidos = 0
        total_itens = 0
        valor_total = 0
        valor_liberado = 0

        for indice, pedido in enumerate(pedidos, start=1):
            resumo = df_resumo[df_resumo["Pedido"].astype(str) == str(pedido)]

            if resumo.empty:
                continue

            linha_resumo = resumo.iloc[0]
            iid_pedido = f"faturado_pedido_{indice}"

            self.tabela.insert(
                "",
                "end",
                iid=iid_pedido,
                text=str(pedido),
                values=(
                    linha_resumo["Data Faturamento"],
                    linha_resumo["Cliente"],
                    linha_resumo["Data Entrega"],
                    formatar_numero(linha_resumo["Qtde Saldo"]),
                    formatar_moeda(linha_resumo["Valor Pedido"]),
                    formatar_moeda(linha_resumo["Valor Bloqueado"]),
                    formatar_moeda(linha_resumo["Valor Liberado"]),
                    linha_resumo["Status"],
                ),
                open=True,
                tags=("pedido", "faturado_pedido"),
            )

            self.mapa_pedidos[iid_pedido] = str(pedido)
            total_pedidos += 1
            total_itens += int(linha_resumo["Qtd. Itens"])
            valor_total += float(linha_resumo["Valor Pedido"])
            valor_liberado += float(linha_resumo["Valor Liberado"])

            if not df.empty:
                coluna_pedido = "Pedido Texto" if "Pedido Texto" in df.columns else "Pedido"
                grupo = df[df[coluna_pedido].astype(str) == str(pedido)]

                for _, linha in grupo.iterrows():
                    id_linha = int(linha["ID Linha"]) if "ID Linha" in linha else len(self.mapa_pedidos) + 1
                    iid_item = f"faturado_item_{id_linha}"
                    bloqueado = bool(linha.get("_Bloqueado", False))
                    status_item = f'✕ {linha.get("_Tipo Bloqueio", "Bloqueado")}' if bloqueado else "✓ Liberado"

                    self.tabela.insert(
                        iid_pedido,
                        "end",
                        iid=iid_item,
                        text=f'{linha["Item"]} - {linha["Descrição Item"]}',
                        values=(
                            datas.get(str(pedido), ""),
                            "",
                            "",
                            formatar_numero(linha["Saldo a Faturar"]),
                            formatar_moeda(linha["Valor em Carteira"]),
                            formatar_moeda(linha.get("_Valor Bloqueado", 0)),
                            formatar_moeda(linha.get("_Valor Liberado", linha["Valor em Carteira"])),
                            status_item,
                        ),
                        tags=("faturado_item",),
                    )

        self.atualizar_resumo(total_pedidos, total_itens, valor_total, valor_liberado)
        self.aplicar_ordenacao()

    def atualizar_resumo(self, pedidos, itens, valor_total, valor_liberado):
        self.label_pedidos.config(text=f"Pedidos faturados: {pedidos}")
        self.label_itens.config(text=f"Itens: {itens}")
        self.label_valor_total.config(text=f"Valor total: {formatar_moeda(valor_total)}")
        self.label_valor_liberado.config(text=f"Valor liberado: {formatar_moeda(valor_liberado)}")

    def get_selected_pedido(self):
        selecionado = self.tabela.selection()

        if not selecionado:
            return None

        iid = selecionado[0]

        if iid in self.mapa_pedidos:
            return self.mapa_pedidos[iid]

        parent = self.tabela.parent(iid)

        if parent and parent in self.mapa_pedidos:
            return self.mapa_pedidos[parent]

        return None

    def remover_selecionado(self):
        pedido = self.get_selected_pedido()

        if not pedido:
            self.controller.set_status("Selecione um pedido faturado para remover.")
            return

        self.controller.remover_pedido_faturado(pedido)

    def expandir_todos(self):
        for item in self.tabela.get_children():
            self.tabela.item(item, open=True)

    def recolher_todos(self):
        for item in self.tabela.get_children():
            self.tabela.item(item, open=False)
