import tkinter as tk
from tkinter import ttk

from core.formatters import formatar_moeda, formatar_numero
from ui.styles import configurar_tags_tabela
from ui.sortable_tree import aplicar_ordenacao_treeview
from ui.ux_helpers import aplicar_menu_generico_tabela


class GargalosTab:
    def __init__(self, parent, controller, state):
        self.parent = parent
        self.controller = controller
        self.state = state
        self.criar_interface()

    def criar_interface(self):
        container = ttk.Frame(self.parent, padding=(10, 8))
        container.pack(fill="both", expand=True)
        self.criar_resumo(container)
        self.criar_tabela(container)

    def criar_resumo(self, parent):
        frame = ttk.LabelFrame(parent, text="Dashboard de gargalos", padding=(10, 8), style="Section.TLabelframe")
        frame.pack(fill="x", pady=(0, 8))

        self.label_total_pendencias = ttk.Label(frame, text="Itens com pendência: 0", style="SummaryValue.TLabel")
        self.label_total_pendencias.grid(row=0, column=0, padx=(0, 18), sticky="w")

        self.label_pedidos_afetados = ttk.Label(frame, text="Pedidos afetados: 0", style="SummaryValue.TLabel")
        self.label_pedidos_afetados.grid(row=0, column=1, padx=(0, 18), sticky="w")

        self.label_valor_pendente = ttk.Label(frame, text="Valor liberado pendente: R$ 0,00", style="SummaryValue.TLabel")
        self.label_valor_pendente.grid(row=0, column=2, padx=(0, 18), sticky="w")

        self.label_maior_gargalo = ttk.Label(frame, text="Maior gargalo: -", style="SummaryValue.TLabel")
        self.label_maior_gargalo.grid(row=0, column=3, padx=(0, 18), sticky="w")

        ttk.Label(
            frame,
            text="Baseado nas pendências por item aplicadas no PROG 2. O maior gargalo considera o valor liberado pendente.",
            style="Hint.TLabel",
        ).grid(row=1, column=0, columnspan=4, sticky="w", pady=(4, 0))

        frame.columnconfigure(4, weight=1)

    def criar_tabela(self, parent):
        frame = ttk.LabelFrame(parent, text="Resumo por motivo", padding=(8, 6), style="Section.TLabelframe")
        frame.pack(fill="both", expand=True)

        barra = ttk.Frame(frame, style="Card.TFrame")
        barra.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        ttk.Label(
            barra,
            text="Abra cada motivo para ver os pedidos e itens afetados.",
            style="CardHint.TLabel",
        ).pack(side="left")
        ttk.Button(barra, text="Atualizar", command=self.refresh, style="Compact.TButton").pack(side="right")

        colunas = ("Pedidos", "Itens", "Qtde", "Valor Total", "Valor Bloqueado", "Valor Liberado", "% Valor")
        self.tabela = ttk.Treeview(frame, columns=colunas, show="tree headings")
        self.tabela.heading("#0", text="Motivo / Pedido / Item")
        self.tabela.column("#0", width=390, minwidth=260, anchor="w")

        larguras = {
            "Pedidos": 80,
            "Itens": 70,
            "Qtde": 90,
            "Valor Total": 130,
            "Valor Bloqueado": 130,
            "Valor Liberado": 130,
            "% Valor": 90,
        }

        for coluna in colunas:
            self.tabela.heading(coluna, text=coluna)
            self.tabela.column(coluna, width=larguras.get(coluna, 120), minwidth=60, anchor="w", stretch=False)

        configurar_tags_tabela(self.tabela)

        scroll_y = ttk.Scrollbar(frame, orient="vertical", command=self.tabela.yview)
        scroll_x = ttk.Scrollbar(frame, orient="horizontal", command=self.tabela.xview)
        self.tabela.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        aplicar_ordenacao_treeview(self.tabela)

        self.tabela.grid(row=1, column=0, sticky="nsew")
        scroll_y.grid(row=1, column=1, sticky="ns")
        scroll_x.grid(row=2, column=0, sticky="ew")

        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)
        aplicar_menu_generico_tabela(self, "Gargalos")

    def refresh(self):
        self.tabela.delete(*self.tabela.get_children())

        if not self.state.tem_dados():
            self.atualizar_labels(0, 0, 0, "-")
            return

        if hasattr(self.controller, "obter_df_com_bloqueios_cache"):
            df = self.controller.obter_df_com_bloqueios_cache()
        else:
            df = self.state.df_com_bloqueios(self.state.df_aberto())

        if df.empty:
            self.atualizar_labels(0, 0, 0, "-")
            return

        pedidos_prog2 = set(str(pedido) for pedido in self.state.pedidos_prog2)
        resumo = {}
        total_liberado_pendente = 0.0
        pedidos_afetados = set()
        total_itens = 0

        for id_linha, motivo in sorted(self.state.pendencias_prog2.items(), key=lambda item: str(item[1])):
            try:
                id_linha_int = int(id_linha)
            except (TypeError, ValueError):
                continue

            linha_df = df[df["ID Linha"] == id_linha_int]
            if linha_df.empty:
                continue

            linha = linha_df.iloc[0]
            pedido = str(linha["Pedido Texto"])
            if pedido not in pedidos_prog2:
                continue

            valor_total = float(linha["Valor em Carteira"])
            valor_bloqueado = float(linha["_Valor Bloqueado"])
            valor_liberado = float(linha["_Valor Liberado"])

            dados = resumo.setdefault(str(motivo), {
                "pedidos": set(),
                "itens": [],
                "qtd": 0.0,
                "valor_total": 0.0,
                "valor_bloqueado": 0.0,
                "valor_liberado": 0.0,
            })
            dados["pedidos"].add(pedido)
            dados["itens"].append({
                "pedido": pedido,
                "cliente": str(linha["Cliente"]),
                "item": str(linha["Item"]),
                "descricao": str(linha["Descrição Item"]),
                "qtd": float(linha["Saldo a Faturar"]),
                "valor_total": valor_total,
                "valor_bloqueado": valor_bloqueado,
                "valor_liberado": valor_liberado,
            })
            dados["qtd"] += float(linha["Saldo a Faturar"])
            dados["valor_total"] += valor_total
            dados["valor_bloqueado"] += valor_bloqueado
            dados["valor_liberado"] += valor_liberado

            pedidos_afetados.add(pedido)
            total_liberado_pendente += valor_liberado
            total_itens += 1

        maior_motivo = "-"
        if resumo:
            maior_motivo = max(resumo.items(), key=lambda item: item[1]["valor_liberado"])[0]

        for indice, (motivo, dados) in enumerate(
            sorted(resumo.items(), key=lambda item: item[1]["valor_liberado"], reverse=True),
            start=1,
        ):
            percentual = 0 if total_liberado_pendente <= 0 else dados["valor_liberado"] / total_liberado_pendente * 100
            iid_motivo = f"gargalo_{indice}"
            self.tabela.insert(
                "",
                "end",
                iid=iid_motivo,
                text=motivo,
                values=(
                    len(dados["pedidos"]),
                    len(dados["itens"]),
                    formatar_numero(dados["qtd"]),
                    formatar_moeda(dados["valor_total"]),
                    formatar_moeda(dados["valor_bloqueado"]),
                    formatar_moeda(dados["valor_liberado"]),
                    f"{percentual:.1f}%",
                ),
                open=True,
                tags=("pedido_parcial",),
            )

            for item in sorted(dados["itens"], key=lambda linha: (linha["pedido"], linha["item"])):
                self.tabela.insert(
                    iid_motivo,
                    "end",
                    text=f'{item["pedido"]} | {item["item"]} - {item["descricao"]}',
                    values=(
                        1,
                        1,
                        formatar_numero(item["qtd"]),
                        formatar_moeda(item["valor_total"]),
                        formatar_moeda(item["valor_bloqueado"]),
                        formatar_moeda(item["valor_liberado"]),
                        "",
                    ),
                    tags=("item_linha",),
                )

        self.atualizar_labels(total_itens, len(pedidos_afetados), total_liberado_pendente, maior_motivo)

    def atualizar_labels(self, itens, pedidos, valor_liberado, maior_gargalo):
        self.label_total_pendencias.config(text=f"Itens com pendência: {itens}")
        self.label_pedidos_afetados.config(text=f"Pedidos afetados: {pedidos}")
        self.label_valor_pendente.config(text=f"Valor liberado pendente: {formatar_moeda(valor_liberado)}")
        self.label_maior_gargalo.config(text=f"Maior gargalo: {maior_gargalo}")
