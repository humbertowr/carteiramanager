from datetime import datetime
import tkinter as tk
from tkinter import ttk

import pandas as pd

from core.formatters import formatar_moeda, formatar_numero
from ui.styles import configurar_tags_tabela
from ui.sortable_tree import aplicar_ordenacao_treeview
from ui.ux_helpers import aplicar_menu_generico_tabela


class FaturadosTab:
    def __init__(self, parent, controller, state):
        self.parent = parent
        self.controller = controller
        self.state = state

        self.busca_var = tk.StringVar()
        self.mapa_pedidos = {}
        self._df_faturados = pd.DataFrame()
        self._df_itens_dia = pd.DataFrame()

        self.criar_interface()

    def criar_interface(self):
        container = ttk.Frame(self.parent, padding=(10, 8))
        container.pack(fill="both", expand=True)

        self.criar_resumo(container)
        self.criar_acoes(container)
        self.criar_tabela(container)

    def criar_resumo(self, parent):
        frame = ttk.LabelFrame(
            parent,
            text="Faturados do dia",
            padding=(8, 6),
            style="Section.TLabelframe",
        )
        frame.pack(fill="x", pady=(0, 6))

        self.label_data = ttk.Label(frame, text=f"Data: {self.data_hoje()}", style="SummaryValue.TLabel")
        self.label_data.grid(row=0, column=0, sticky="w", padx=(0, 24))

        self.label_pedidos = ttk.Label(frame, text="Pedidos: 0", style="SummaryValue.TLabel")
        self.label_pedidos.grid(row=0, column=1, sticky="w", padx=(0, 24))

        self.label_itens = ttk.Label(frame, text="Itens: 0", style="SummaryValue.TLabel")
        self.label_itens.grid(row=0, column=2, sticky="w", padx=(0, 24))

        self.label_qtde = ttk.Label(frame, text="Qtde: 0,00", style="SummaryValue.TLabel")
        self.label_qtde.grid(row=0, column=3, sticky="w", padx=(0, 24))

        self.label_valor_total = ttk.Label(frame, text="Total faturado: R$ 0,00", style="SummaryValue.TLabel")
        self.label_valor_total.grid(row=0, column=4, sticky="w", padx=(0, 24))

        frame.columnconfigure(5, weight=1)

    def criar_acoes(self, parent):
        frame = ttk.LabelFrame(
            parent,
            text="Ações",
            padding=(8, 6),
            style="Section.TLabelframe",
        )
        frame.pack(fill="x", pady=(0, 6))

        ttk.Label(frame, text="Buscar", style="Hint.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 6))

        self.entrada_busca = ttk.Entry(frame, textvariable=self.busca_var, width=42)
        self.entrada_busca.grid(row=0, column=1, sticky="w", padx=(0, 12))
        self.entrada_busca.bind("<KeyRelease>", lambda event: self.refresh())

        ttk.Button(
            frame,
            text="Exportar faturados do dia",
            command=self.controller.exportar_faturados_dia,
            style="Primary.TButton",
        ).grid(row=0, column=2, sticky="w", padx=3)

        ttk.Button(
            frame,
            text="Remover do faturamento",
            command=self.remover_selecionado,
            style="Danger.TButton",
        ).grid(row=0, column=3, sticky="w", padx=3)

        ttk.Label(
            frame,
            text="Mostra somente pedidos fechados hoje via PROG 2.",
            style="Hint.TLabel",
        ).grid(row=0, column=4, sticky="w", padx=(12, 0))

        frame.columnconfigure(5, weight=1)

    def criar_tabela(self, parent):
        frame = ttk.LabelFrame(
            parent,
            text="Pedidos e itens faturados hoje",
            padding=(8, 6),
            style="Section.TLabelframe",
        )
        frame.pack(fill="both", expand=True)

        barra = ttk.Frame(frame)
        barra.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))

        ttk.Label(
            barra,
            text="Cada fechamento de faturamento registra os itens liberados do PROG 2 no dia atual.",
            style="Subtitle.TLabel",
        ).pack(side="left")

        ttk.Button(barra, text="Expandir", command=self.expandir_todos, style="Compact.TButton").pack(side="right", padx=(4, 0))
        ttk.Button(barra, text="Recolher", command=self.recolher_todos, style="Compact.TButton").pack(side="right", padx=4)

        colunas = (
            "Cliente",
            "Qtde",
            "Valor Faturamento",
            "Data/Hora",
            "Status/OBS",
        )

        self.tabela = ttk.Treeview(frame, columns=colunas, show="tree headings")
        self.tabela.heading("#0", text="Pedido / Item")
        self.tabela.column("#0", width=360, minwidth=240, anchor="w", stretch=True)

        larguras = {
            "Cliente": 340,
            "Qtde": 90,
            "Valor Faturamento": 150,
            "Data/Hora": 140,
            "Status/OBS": 240,
        }

        for coluna in colunas:
            self.tabela.heading(coluna, text=coluna)
            self.tabela.column(
                coluna,
                width=larguras.get(coluna, 120),
                minwidth=70,
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
        aplicar_menu_generico_tabela(self, "Faturados do dia")

    def aplicar_ordenacao(self):
        aplicar_ordenacao_treeview(self.tabela)

    def data_hoje(self):
        return datetime.now().strftime("%d/%m/%Y")

    def normalizar_data_faturamento(self, valor):
        texto = str(valor or "").strip()
        if not texto:
            return ""
        return texto.split()[0]

    def _valor_total_pedido_original(self, pedido):
        if not self.state.tem_dados():
            return 0.0

        df = self.state.df_original
        coluna_pedido = "Pedido Texto" if "Pedido Texto" in df.columns else "Pedido"
        if coluna_pedido not in df.columns or "Valor em Carteira" not in df.columns:
            return 0.0

        filtro = df[coluna_pedido].astype(str) == str(pedido)
        if not filtro.any():
            return 0.0

        return float(pd.to_numeric(df.loc[filtro, "Valor em Carteira"], errors="coerce").fillna(0).sum())

    def _aplicar_valor_saldo_pedido(self, df):
        if df is None or df.empty:
            return pd.DataFrame() if df is None else df

        resultado = df.copy()

        if "Valor Saldo Pedido" not in resultado.columns:
            resultado["Valor Saldo Pedido"] = 0.0

        resultado["Valor Saldo Pedido"] = pd.to_numeric(
            resultado["Valor Saldo Pedido"],
            errors="coerce"
        ).fillna(0)

        if "Pedido" not in resultado.columns or "Valor Total Faturamento" not in resultado.columns:
            return resultado

        for pedido, grupo in resultado.groupby("Pedido", sort=False):
            pedido = str(pedido)
            valor_atual = float(grupo["Valor Saldo Pedido"].max())
            if valor_atual > 0:
                continue

            valor_total_pedido = self._valor_total_pedido_original(pedido)
            if valor_total_pedido <= 0:
                continue

            valor_faturado = float(
                pd.to_numeric(grupo["Valor Total Faturamento"], errors="coerce").fillna(0).sum()
            )
            saldo = max(valor_total_pedido - valor_faturado, 0)
            resultado.loc[grupo.index, "Valor Saldo Pedido"] = saldo

        return resultado

    def pedidos_faturados(self):
        hoje = self.data_hoje()
        datas = getattr(self.state, "datas_faturamento_pedido", {})
        pedidos = {
            str(pedido)
            for pedido in getattr(self.state, "pedidos_faturados", set())
            if self.normalizar_data_faturamento(datas.get(str(pedido), "")) == hoje
        }

        for registro in getattr(self.state, "registros_faturamento", []):
            data_ref = self.normalizar_data_faturamento(
                registro.get("Data Referência", registro.get("Data Faturamento", ""))
            )
            if data_ref == hoje and registro.get("Pedido"):
                pedidos.add(str(registro.get("Pedido")))

        return sorted(pedidos)

    def df_registros_faturamento_dia(self):
        registros = [
            dict(registro)
            for registro in getattr(self.state, "registros_faturamento", [])
            if isinstance(registro, dict)
        ]

        if not registros:
            return pd.DataFrame()

        df = pd.DataFrame(registros)
        if df.empty:
            return pd.DataFrame()

        if "Data Referência" not in df.columns:
            df["Data Referência"] = df.get("Data Faturamento", "").astype(str).str.split().str[0]

        hoje = self.data_hoje()
        df = df[df["Data Referência"].astype(str).apply(self.normalizar_data_faturamento) == hoje].copy()

        if df.empty:
            return pd.DataFrame()

        colunas_padrao = {
            "Data Referência": hoje,
            "Data Faturamento": "",
            "Pedido": "",
            "Cliente": "",
            "Item": "",
            "Descrição Item": "",
            "Qtde": 0,
            "Valor Total Faturamento": 0,
            "Valor Saldo Pedido": 0,
            "Data Entrega": "",
            "Grupo": "",
            "OBS": "",
            "ID Linha": "",
        }

        for coluna, padrao in colunas_padrao.items():
            if coluna not in df.columns:
                df[coluna] = padrao

        df["Qtde"] = pd.to_numeric(df["Qtde"], errors="coerce").fillna(0)
        df["Valor Total Faturamento"] = pd.to_numeric(df["Valor Total Faturamento"], errors="coerce").fillna(0)
        df["Valor Saldo Pedido"] = pd.to_numeric(df["Valor Saldo Pedido"], errors="coerce").fillna(0)
        df = self._aplicar_valor_saldo_pedido(df)

        return df[list(colunas_padrao.keys())].copy()

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
            if "_Bloqueado" in df.columns:
                df = df[~df["_Bloqueado"]].copy()

        return df

    def df_itens_faturados_dia(self):
        df_registros = self.df_registros_faturamento_dia()
        if not df_registros.empty:
            return df_registros

        df = self.df_base_faturados()
        if df.empty:
            return pd.DataFrame()

        datas = getattr(self.state, "datas_faturamento_pedido", {})
        registros = []

        for _, linha in df.iterrows():
            pedido = str(linha.get("Pedido Texto", linha.get("Pedido", "")))
            id_linha = linha.get("ID Linha", "")
            try:
                id_pendencia = int(id_linha)
            except (TypeError, ValueError):
                id_pendencia = None

            obs = ""
            if id_pendencia is not None:
                obs = str(getattr(self.state, "pendencias_prog2", {}).get(id_pendencia, "") or "").strip()

            registros.append({
                "Data Referência": self.data_hoje(),
                "Data Faturamento": datas.get(pedido, ""),
                "Pedido": pedido,
                "Cliente": str(linha.get("Cliente", "")),
                "Item": str(linha.get("Item", "")),
                "Descrição Item": str(linha.get("Descrição Item", "")),
                "Qtde": float(linha.get("Saldo a Faturar", 0) or 0),
                "Valor Total Faturamento": float(linha.get("Valor em Carteira", 0) or 0),
                "Valor Saldo Pedido": 0.0,
                "Data Entrega": str(linha.get("Data Entrega", "")),
                "Grupo": str(linha.get("Grupo Faturamento Abrev", linha.get("Grupo Faturamento", ""))),
                "OBS": obs,
                "ID Linha": str(id_linha),
            })

        return self._aplicar_valor_saldo_pedido(pd.DataFrame(registros))

    def get_export_df(self, incluir_total=True):
        df = self.df_itens_faturados_dia()
        if df.empty:
            return pd.DataFrame()

        colunas = [
            "Pedido",
            "Cliente",
            "Item",
            "Descrição Item",
            "Qtde",
            "Valor Total Faturamento",
            "Valor Saldo Pedido",
            "Previsão de Embarque",
            "OBS",
        ]

        for coluna in colunas:
            if coluna not in df.columns:
                df[coluna] = "" if coluna not in ("Qtde", "Valor Total Faturamento", "Valor Saldo Pedido") else 0

        resultado = df[colunas].copy()
        resultado.sort_values(["Pedido", "Item"], inplace=True, kind="stable")

        if incluir_total:
            total = {coluna: "" for coluna in colunas}
            total["Pedido"] = "TOTAL DO DIA"
            total["Qtde"] = resultado["Qtde"].sum()
            total["Valor Total Faturamento"] = resultado["Valor Total Faturamento"].sum()
            total["Valor Saldo Pedido"] = resultado.drop_duplicates("Pedido")["Valor Saldo Pedido"].sum()
            resultado = pd.concat([resultado, pd.DataFrame([total])], ignore_index=True)

        return resultado

    def get_current_df(self):
        return self.get_export_df(incluir_total=False)

    def focar_busca(self):
        if hasattr(self, "entrada_busca"):
            self.entrada_busca.focus_set()
            self.entrada_busca.selection_range(0, "end")

    def refresh(self):
        self.tabela.delete(*self.tabela.get_children())
        self.mapa_pedidos.clear()

        df_itens = self.df_itens_faturados_dia()
        termo = self.busca_var.get().strip().lower()

        if termo and not df_itens.empty:
            colunas_busca = ["Pedido", "Cliente", "Item", "Descrição Item", "OBS"]
            colunas_existentes = [coluna for coluna in colunas_busca if coluna in df_itens.columns]
            df_itens = df_itens[
                df_itens[colunas_existentes]
                .astype(str)
                .apply(lambda linha: linha.str.lower().str.contains(termo, na=False).any(), axis=1)
            ].copy()

        if df_itens.empty:
            self._df_faturados = pd.DataFrame()
            self._df_itens_dia = pd.DataFrame()
            self.atualizar_resumo(0, 0, 0, 0)
            return

        self._df_itens_dia = df_itens.copy()
        self._df_faturados = self.get_current_df()

        total_pedidos = 0
        total_itens = len(df_itens)
        total_qtde = float(df_itens["Qtde"].sum())
        valor_total = float(df_itens["Valor Total Faturamento"].sum())

        for indice, (pedido, grupo) in enumerate(df_itens.groupby("Pedido", sort=False), start=1):
            if str(pedido).strip() == "":
                continue

            cliente = str(grupo["Cliente"].iloc[0]) if "Cliente" in grupo.columns else ""
            data_faturamento = str(grupo["Data Faturamento"].iloc[0]) if "Data Faturamento" in grupo.columns else ""
            qtde_pedido = float(grupo["Qtde"].sum())
            valor_pedido = float(grupo["Valor Total Faturamento"].sum())
            iid_pedido = f"faturado_pedido_{indice}"

            self.tabela.insert(
                "",
                "end",
                iid=iid_pedido,
                text=str(pedido),
                values=(
                    cliente,
                    formatar_numero(qtde_pedido),
                    formatar_moeda(valor_pedido),
                    data_faturamento,
                    "Faturado hoje",
                ),
                open=True,
                tags=("pedido", "faturado_pedido"),
            )

            self.mapa_pedidos[iid_pedido] = str(pedido)
            total_pedidos += 1

            for item_indice, (_, linha) in enumerate(grupo.iterrows(), start=1):
                item = str(linha.get("Item", ""))
                descricao = str(linha.get("Descrição Item", ""))
                obs = str(linha.get("OBS", "") or "").strip()
                status_item = obs if obs else "Faturado"
                iid_item = f"faturado_item_{indice}_{item_indice}"

                self.tabela.insert(
                    iid_pedido,
                    "end",
                    iid=iid_item,
                    text=f"{item} - {descricao}" if descricao else item,
                    values=(
                        "",
                        formatar_numero(linha.get("Qtde", 0)),
                        formatar_moeda(linha.get("Valor Total Faturamento", 0)),
                        "",
                        status_item,
                    ),
                    tags=("faturado_item",),
                )

        self.atualizar_resumo(total_pedidos, total_itens, total_qtde, valor_total)
        self.aplicar_ordenacao()

    def atualizar_resumo(self, pedidos, itens, qtde_total, valor_total):
        self.label_data.config(text=f"Data: {self.data_hoje()}")
        self.label_pedidos.config(text=f"Pedidos: {pedidos}")
        self.label_itens.config(text=f"Itens: {itens}")
        self.label_qtde.config(text=f"Qtde: {formatar_numero(qtde_total)}")
        self.label_valor_total.config(text=f"Total faturado: {formatar_moeda(valor_total)}")

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
