from datetime import date
import tkinter as tk
from tkinter import ttk

import pandas as pd

from core.formatters import formatar_moeda, formatar_numero
from ui.styles import configurar_tags_tabela
from ui.sortable_tree import aplicar_ordenacao_treeview


class AtrasadosTab:
    def __init__(self, parent, controller, state):
        self.parent = parent
        self.controller = controller
        self.state = state

        self.busca_var = tk.StringVar()
        self.mapa_linhas = {}
        self._df_atrasados = pd.DataFrame()

        self.criar_interface()

    def criar_interface(self):
        container = ttk.Frame(self.parent, padding=(8, 6))
        container.pack(fill="both", expand=True)

        self.criar_resumo(container)
        self.criar_filtros(container)
        self.criar_tabela(container)

    def criar_resumo(self, parent):
        frame = ttk.LabelFrame(
            parent,
            text="Resumo de atrasados",
            padding=(8, 6),
            style="Section.TLabelframe"
        )
        frame.pack(fill="x", pady=(0, 6))

        self.label_pedidos = ttk.Label(frame, text="Pedidos atrasados: 0", style="SummaryValue.TLabel")
        self.label_pedidos.grid(row=0, column=0, sticky="w", padx=(0, 24))

        self.label_itens = ttk.Label(frame, text="Itens atrasados: 0", style="SummaryValue.TLabel")
        self.label_itens.grid(row=0, column=1, sticky="w", padx=(0, 24))

        self.label_maior_atraso = ttk.Label(frame, text="Maior atraso: 0 dias", style="SummaryValue.TLabel")
        self.label_maior_atraso.grid(row=0, column=2, sticky="w", padx=(0, 24))

        self.label_valor_total = ttk.Label(frame, text="Valor total em atraso: R$ 0,00", style="SummaryValue.TLabel")
        self.label_valor_total.grid(row=0, column=3, sticky="w", padx=(0, 24))

        self.label_valor_liberado = ttk.Label(frame, text="Valor liberado em atraso: R$ 0,00", style="SummaryValue.TLabel")
        self.label_valor_liberado.grid(row=0, column=4, sticky="w", padx=(0, 24))

        frame.columnconfigure(5, weight=1)

    def criar_filtros(self, parent):
        frame = ttk.LabelFrame(
            parent,
            text="Filtros de atrasados",
            padding=(8, 6),
            style="Section.TLabelframe"
        )
        frame.pack(fill="x", pady=(0, 6))

        ttk.Label(frame, text="Busca geral").grid(row=0, column=0, sticky="w", padx=(0, 5))

        entrada = ttk.Entry(frame, textvariable=self.busca_var, width=42)
        entrada.grid(row=0, column=1, sticky="w", padx=(0, 12))
        entrada.bind("<KeyRelease>", lambda event: self.refresh())

        ttk.Label(
            frame,
            text="Considera pedidos com Data Entrega menor que hoje.",
            style="Hint.TLabel"
        ).grid(row=0, column=2, sticky="w")

        frame.columnconfigure(3, weight=1)

    def criar_tabela(self, parent):
        frame = ttk.LabelFrame(
            parent,
            text="Pedidos em atraso",
            padding=(8, 6),
            style="Section.TLabelframe"
        )
        frame.pack(fill="both", expand=True)

        barra = ttk.Frame(frame)
        barra.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))

        ttk.Label(
            barra,
            text="Pedidos atrasados ficam agrupados; abra o pedido para ver os itens.",
            style="Subtitle.TLabel"
        ).pack(side="left")

        ttk.Button(barra, text="Expandir todos", command=self.expandir_todos).pack(side="right", padx=(4, 0))
        ttk.Button(barra, text="Recolher todos", command=self.recolher_todos).pack(side="right", padx=4)

        colunas = (
            "Cliente",
            "Data Entrega",
            "Dias Atraso",
            "Qtde Saldo",
            "Valor Total Atraso",
            "Valor Liberado",
            "Status",
        )

        self.tabela = ttk.Treeview(frame, columns=colunas, show="tree headings")
        self.tabela.heading("#0", text="Pedido / Item")
        self.tabela.column("#0", width=380, minwidth=260, anchor="w", stretch=True)

        larguras = {
            "Cliente": 360,
            "Data Entrega": 105,
            "Dias Atraso": 95,
            "Qtde Saldo": 90,
            "Valor Total Atraso": 150,
            "Valor Liberado": 135,
            "Status": 175,
        }

        textos = {
            "Dias Atraso": "Dias atraso",
            "Qtde Saldo": "Qtde",
            "Valor Total Atraso": "Valor atraso",
            "Valor Liberado": "Valor liberado",
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
        self.tabela.tag_configure("atraso_pedido", background="#fee2e2", foreground="#991b1b")
        self.tabela.tag_configure("atraso_item", background="#fff7ed", foreground="#7c2d12")
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

    def calcular_df_atrasados(self):
        if not self.state.tem_dados():
            return pd.DataFrame()

        df = self.controller.obter_df_com_bloqueios_cache().copy()

        if df.empty or "Data Entrega" not in df.columns:
            return pd.DataFrame()

        df["_Data Entrega Calc"] = pd.to_datetime(
            df["Data Entrega"],
            errors="coerce",
            dayfirst=True,
        )

        hoje = pd.Timestamp(date.today())
        df["_Dias Atraso"] = (hoje - df["_Data Entrega Calc"]).dt.days
        df = df[df["_Dias Atraso"] > 0].copy()

        if df.empty:
            return pd.DataFrame()

        termo = self.busca_var.get().strip().lower()

        if termo:
            colunas_busca = ["Pedido", "Cliente", "Item", "Descrição Item"]
            df = df[
                df[colunas_busca]
                .astype(str)
                .apply(
                    lambda linha: linha.str.lower().str.contains(termo, na=False).any(),
                    axis=1,
                )
            ]

        return df

    def definir_status_pedido(self, pedido_str, valor_total, valor_bloqueado):
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

        return "✓ Liberado", ("pedido", "pedido_liberado")

    def refresh(self):
        self.tabela.delete(*self.tabela.get_children())
        self.mapa_linhas.clear()

        df = self.calcular_df_atrasados()
        self._df_atrasados = df.copy()

        if df.empty:
            self.atualizar_resumo(0, 0, 0, 0, 0)
            return

        agrupados = []

        for pedido, grupo in df.groupby("Pedido", sort=False):
            valor_total = grupo["Valor em Carteira"].sum()
            valor_bloqueado = grupo["_Valor Bloqueado"].sum()
            valor_liberado = grupo["_Valor Liberado"].sum()
            dias_atraso = int(grupo["_Dias Atraso"].max())

            agrupados.append({
                "pedido": pedido,
                "grupo": grupo,
                "valor_total": valor_total,
                "valor_bloqueado": valor_bloqueado,
                "valor_liberado": valor_liberado,
                "dias_atraso": dias_atraso,
            })

        agrupados.sort(
            key=lambda item: (item["dias_atraso"], item["valor_total"]),
            reverse=True,
        )

        total_pedidos = 0
        total_itens = 0
        maior_atraso = 0
        valor_total_atraso = 0
        valor_liberado_atraso = 0

        for indice, dados in enumerate(agrupados, start=1):
            pedido = dados["pedido"]
            grupo = dados["grupo"]
            valor_total = dados["valor_total"]
            valor_bloqueado = dados["valor_bloqueado"]
            valor_liberado = dados["valor_liberado"]
            dias_atraso = dados["dias_atraso"]
            pedido_str = str(pedido)

            cliente = str(grupo["Cliente"].iloc[0])
            data_entrega = str(grupo["Data Entrega"].iloc[0])
            qtde_saldo = grupo["Saldo a Faturar"].sum()
            status, tags = self.definir_status_pedido(pedido_str, valor_total, valor_bloqueado)

            iid_pedido = f"atraso_pedido_{indice}"

            self.tabela.insert(
                "",
                "end",
                iid=iid_pedido,
                text=pedido_str,
                values=(
                    cliente,
                    data_entrega,
                    dias_atraso,
                    formatar_numero(qtde_saldo),
                    formatar_moeda(valor_total),
                    formatar_moeda(valor_liberado),
                    status,
                ),
                open=True,
                tags=("atraso_pedido",),
            )

            for _, linha in grupo.iterrows():
                id_linha = int(linha["ID Linha"])
                bloqueado = bool(linha["_Bloqueado"])
                status_item = f'✕ {linha["_Tipo Bloqueio"]}' if bloqueado else "✓ Liberado"

                self.tabela.insert(
                    iid_pedido,
                    "end",
                    iid=f"atraso_item_{id_linha}",
                    text=f'{linha["Item"]} - {linha["Descrição Item"]}',
                    values=(
                        "",
                        "",
                        int(linha["_Dias Atraso"]),
                        formatar_numero(linha["Saldo a Faturar"]),
                        formatar_moeda(float(linha["Valor em Carteira"])),
                        formatar_moeda(float(linha["_Valor Liberado"])),
                        status_item,
                    ),
                    tags=("item_bloqueado",) if bloqueado else ("atraso_item",),
                )

                self.mapa_linhas[f"atraso_item_{id_linha}"] = id_linha
                total_itens += 1

            total_pedidos += 1
            maior_atraso = max(maior_atraso, dias_atraso)
            valor_total_atraso += valor_total
            valor_liberado_atraso += valor_liberado

        self.atualizar_resumo(
            total_pedidos,
            total_itens,
            maior_atraso,
            valor_total_atraso,
            valor_liberado_atraso,
        )
        self.aplicar_ordenacao()

        self.controller.set_status(
            f"Pedidos atrasados: {total_pedidos} | Itens atrasados: {total_itens} | Valor em atraso: {formatar_moeda(valor_total_atraso)}"
        )

    def atualizar_resumo(self, pedidos, itens, maior_atraso, valor_total, valor_liberado):
        self.label_pedidos.config(text=f"Pedidos atrasados: {pedidos}")
        self.label_itens.config(text=f"Itens atrasados: {itens}")
        self.label_maior_atraso.config(text=f"Maior atraso: {maior_atraso} dias")
        self.label_valor_total.config(text=f"Valor total em atraso: {formatar_moeda(valor_total)}")
        self.label_valor_liberado.config(text=f"Valor liberado em atraso: {formatar_moeda(valor_liberado)}")

    def get_current_df(self):
        if self._df_atrasados is None or self._df_atrasados.empty:
            return pd.DataFrame()

        colunas = [
            "Pedido",
            "Cliente",
            "Data Entrega",
            "_Dias Atraso",
            "Item",
            "Descrição Item",
            "Saldo a Faturar",
            "Valor em Carteira",
            "_Valor Bloqueado",
            "_Valor Liberado",
            "_Tipo Bloqueio",
        ]

        existentes = [coluna for coluna in colunas if coluna in self._df_atrasados.columns]
        df_saida = self._df_atrasados[existentes].copy()

        df_saida.rename(
            columns={
                "_Dias Atraso": "Dias em Atraso",
                "Saldo a Faturar": "Qtde Saldo",
                "Valor em Carteira": "Valor Total em Atraso",
                "_Valor Bloqueado": "Valor Bloqueado",
                "_Valor Liberado": "Valor Liberado",
                "_Tipo Bloqueio": "Tipo Bloqueio",
            },
            inplace=True,
        )

        return df_saida

    def expandir_todos(self):
        for item in self.tabela.get_children():
            self.tabela.item(item, open=True)

    def recolher_todos(self):
        for item in self.tabela.get_children():
            self.tabela.item(item, open=False)
