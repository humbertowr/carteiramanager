from datetime import date, datetime, timedelta
import tkinter as tk

import pandas as pd
from tkinter import ttk, filedialog, messagebox

from core.exporter import exportar_simulacao_faturamento_excel
from core.formatters import converter_valor_digitado, formatar_moeda, formatar_numero
from services.simulacao_faturamento_service import SimulacaoFaturamentoService
from ui.styles import configurar_tags_tabela
from ui.ux_helpers import (
    abrir_janela_detalhes,
    aplicar_estado_vazio_treeview,
    aplicar_tooltip,
    copiar_para_clipboard,
    criar_cabecalho_aba,
    criar_menu_contexto,
    obter_texto_linha_treeview,
)


class SimulacaoSemanalTab:
    def __init__(self, parent, controller, state):
        self.parent = parent
        self.controller = controller
        self.state = state
        self.service = SimulacaoFaturamentoService()
        self.resultado_atual = None
        self.tabelas_dia = []
        self.contexto_tabelas = {}

        hoje = date.today()
        fim_padrao = hoje + timedelta(days=4)

        self.data_inicio_var = tk.StringVar(value=hoje.strftime("%d/%m/%Y"))
        self.data_fim_var = tk.StringVar(value=fim_padrao.strftime("%d/%m/%Y"))
        self.meta_diaria_var = tk.StringVar(value="R$ 100.000,00")
        self.tolerancia_var = tk.StringVar(value="10%")
        self.valor_minimo_pedido_var = tk.StringVar(value="R$ 1.000,00")
        self.somente_dias_uteis_var = tk.BooleanVar(value=True)
        self.priorizar_entrega_var = tk.BooleanVar(value=True)

        self.criar_interface()

    def criar_interface(self):
        container = ttk.Frame(self.parent, padding=(8, 6))
        container.pack(fill="both", expand=True)

        criar_cabecalho_aba(container, "Simulação", "Planejamento de faturamento por período, meta e tolerância.")
        self.criar_topo(container)
        self.criar_resumo(container)
        self.criar_estimativa_por_dia(container)

    def criar_topo(self, parent):
        frame = ttk.LabelFrame(
            parent,
            text="Simulação de faturamento semanal",
            padding=(7, 5),
            style="Section.TLabelframe",
        )
        frame.pack(fill="x", pady=(0, 5))

        ttk.Label(frame, text="Início", style="Card.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 5))
        entrada_inicio = ttk.Entry(frame, textvariable=self.data_inicio_var, width=12)
        entrada_inicio.grid(row=0, column=1, sticky="w", padx=(0, 10))

        ttk.Label(frame, text="Fim", style="Card.TLabel").grid(row=0, column=2, sticky="w", padx=(0, 5))
        entrada_fim = ttk.Entry(frame, textvariable=self.data_fim_var, width=12)
        entrada_fim.grid(row=0, column=3, sticky="w", padx=(0, 10))

        ttk.Label(frame, text="Meta/dia", style="Card.TLabel").grid(row=0, column=4, sticky="w", padx=(0, 5))
        entrada_meta = ttk.Entry(frame, textvariable=self.meta_diaria_var, width=16)
        entrada_meta.grid(row=0, column=5, sticky="w", padx=(0, 10))

        ttk.Label(frame, text="Tolerância", style="Card.TLabel").grid(row=0, column=6, sticky="w", padx=(0, 5))
        entrada_tolerancia = ttk.Entry(frame, textvariable=self.tolerancia_var, width=8)
        entrada_tolerancia.grid(row=0, column=7, sticky="w", padx=(0, 10))

        ttk.Label(frame, text="Mín. pedido", style="Card.TLabel").grid(row=0, column=8, sticky="w", padx=(0, 5))
        entrada_minimo_pedido = ttk.Entry(frame, textvariable=self.valor_minimo_pedido_var, width=13)
        entrada_minimo_pedido.grid(row=0, column=9, sticky="w", padx=(0, 10))

        ttk.Button(
            frame,
            text="Simular",
            command=self.gerar_simulacao,
            style="Primary.TButton",
        ).grid(row=0, column=10, sticky="e", padx=(0, 5))

        ttk.Button(
            frame,
            text="Exportar",
            command=self.exportar_excel,
            style="Compact.TButton",
        ).grid(row=0, column=11, sticky="e")

        ttk.Checkbutton(
            frame,
            text="Dias úteis",
            variable=self.somente_dias_uteis_var,
        ).grid(row=1, column=0, sticky="w", pady=(5, 0))

        ttk.Checkbutton(
            frame,
            text="Priorizar entrega",
            variable=self.priorizar_entrega_var,
        ).grid(row=1, column=1, columnspan=2, sticky="w", pady=(5, 0))

        ttk.Label(
            frame,
            text="Considera somente valor liberado, ignora bloqueios/pendências, respeita a tolerância e descarta pedidos abaixo do mínimo informado.",
            style="CardHint.TLabel",
        ).grid(row=1, column=3, columnspan=9, sticky="w", pady=(5, 0))

        for entrada in (entrada_inicio, entrada_fim):
            entrada.bind("<Return>", lambda event: self.gerar_simulacao())

        entrada_meta.bind("<FocusOut>", self.finalizar_meta)
        entrada_meta.bind("<Return>", self.finalizar_meta)
        entrada_tolerancia.bind("<FocusOut>", self.finalizar_tolerancia)
        entrada_tolerancia.bind("<Return>", self.finalizar_tolerancia)
        entrada_minimo_pedido.bind("<FocusOut>", self.finalizar_valor_minimo_pedido)
        entrada_minimo_pedido.bind("<Return>", self.finalizar_valor_minimo_pedido)

        frame.columnconfigure(11, weight=1)

    def criar_resumo(self, parent):
        frame = ttk.Frame(parent, padding=(5, 4), style="Card.TFrame")
        frame.pack(fill="x", pady=(0, 5))

        campos = [
            ("Dias", "-"),
            ("Meta total", "R$ 0,00"),
            ("Estimado", "R$ 0,00"),
            ("Diferença", "R$ 0,00"),
            ("Tolerância", "10%"),
            ("Pedidos", "0"),
            ("Saldo elegível restante", "R$ 0,00"),
        ]

        self.labels_resumo = {}

        for coluna, (titulo, valor) in enumerate(campos):
            bloco = ttk.Frame(frame, padding=(6, 4), style="KpiCard.TFrame")
            bloco.grid(row=0, column=coluna, sticky="nsew", padx=2)
            ttk.Label(bloco, text=titulo, style="KpiTitle.TLabel").pack(anchor="w")
            label = ttk.Label(bloco, text=valor, style="KpiValue.TLabel")
            label.pack(anchor="w")
            self.labels_resumo[titulo] = label
            frame.columnconfigure(coluna, weight=1)

    def criar_estimativa_por_dia(self, parent):
        frame = ttk.LabelFrame(
            parent,
            text="Estimativa por dia e pedidos selecionados",
            padding=(4, 4),
            style="Section.TLabelframe",
        )
        frame.pack(fill="both", expand=True)

        self.dias_notebook = ttk.Notebook(frame)
        self.dias_notebook.grid(row=0, column=0, sticky="nsew")

        self.aba_vazia = ttk.Frame(self.dias_notebook, padding=(12, 10))
        ttk.Label(
            self.aba_vazia,
            text="Gere uma simulação para visualizar os dias separados em abas.",
            style="Hint.TLabel",
        ).pack(anchor="w")
        self.dias_notebook.add(self.aba_vazia, text="Sem simulação")

        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

    def criar_tabela_dia(self, parent, dia=None):
        colunas = (
            "Cliente / Descrição",
            "Entrega",
            "Qtd",
            "Valor Faturável",
            "Saldo Bloq./Pend.",
            "Status",
        )

        tabela = ttk.Treeview(parent, columns=colunas, show="tree headings")
        tabela.heading("#0", text="Pedido / Item")
        tabela.column("#0", width=210, minwidth=150, anchor="w", stretch=False)

        larguras = {
            "Cliente / Descrição": 460,
            "Entrega": 95,
            "Qtd": 90,
            "Valor Faturável": 130,
            "Saldo Bloq./Pend.": 135,
            "Status": 130,
        }

        for coluna in colunas:
            tabela.heading(coluna, text=coluna)
            tabela.column(
                coluna,
                width=larguras.get(coluna, 100),
                minwidth=70,
                anchor="e" if coluna in ("Qtd", "Valor Faturável", "Saldo Bloq./Pend.") else "w",
                stretch=coluna == "Cliente / Descrição",
            )

        configurar_tags_tabela(tabela)
        tabela.tag_configure("pedido_simulado", font=("Segoe UI", 9, "bold"))
        tabela.tag_configure("item_simulado", background="#ffffff", foreground="#374151")
        tabela.tag_configure("item_desc", background="#f8fafc", foreground="#374151")

        scroll_y = ttk.Scrollbar(parent, orient="vertical", command=tabela.yview)
        scroll_x = ttk.Scrollbar(parent, orient="horizontal", command=tabela.xview)
        tabela.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        tabela.grid(row=1, column=0, sticky="nsew")
        scroll_y.grid(row=1, column=1, sticky="ns")
        scroll_x.grid(row=2, column=0, sticky="ew")

        parent.rowconfigure(1, weight=1)
        parent.columnconfigure(0, weight=1)

        self.contexto_tabelas[tabela] = {"dia": dia, "indice_dia": None, "linhas": {}}
        self.configurar_menu_contexto_tabela_dia(tabela)

        return tabela

    def finalizar_meta(self, event=None):
        valor = converter_valor_digitado(self.meta_diaria_var.get())
        self.meta_diaria_var.set(formatar_moeda(valor) if valor > 0 else "")
        return "break"

    def finalizar_tolerancia(self, event=None):
        try:
            valor = self.parse_percentual(self.tolerancia_var.get())
            self.tolerancia_var.set(self.formatar_percentual(valor))
        except ValueError:
            self.tolerancia_var.set("10%")
        return "break"

    def finalizar_valor_minimo_pedido(self, event=None):
        valor = converter_valor_digitado(self.valor_minimo_pedido_var.get())
        if valor < 0:
            valor = 0
        self.valor_minimo_pedido_var.set(formatar_moeda(valor))
        return "break"

    def parse_percentual(self, texto):
        texto = str(texto).strip().replace("%", "").replace(",", ".")
        if not texto:
            return 10.0
        try:
            valor = float(texto)
        except ValueError as erro:
            raise ValueError("Tolerância inválida. Use exemplo: 10%") from erro
        if valor < 0 or valor > 100:
            raise ValueError("A tolerância deve estar entre 0% e 100%.")
        return valor

    def formatar_percentual(self, valor):
        valor = float(valor or 0)
        if valor.is_integer():
            return f"{int(valor)}%"
        return f"{valor:.1f}%".replace(".", ",")

    def parse_data(self, texto):
        texto = str(texto).strip()
        for formato in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
            try:
                return datetime.strptime(texto, formato).date()
            except ValueError:
                continue
        raise ValueError(f"Data inválida: {texto}. Use dd/mm/aaaa.")

    def gerar_simulacao(self):
        try:
            data_inicio = self.parse_data(self.data_inicio_var.get())
            data_fim = self.parse_data(self.data_fim_var.get())
            meta_diaria = converter_valor_digitado(self.meta_diaria_var.get())
            tolerancia = self.parse_percentual(self.tolerancia_var.get())
            valor_minimo_pedido = converter_valor_digitado(self.valor_minimo_pedido_var.get())
            somente_dias_uteis = bool(self.somente_dias_uteis_var.get())
            priorizar_entrega = bool(self.priorizar_entrega_var.get())

            self.resultado_atual = self.service.calcular(
                self.state,
                data_inicio,
                data_fim,
                meta_diaria,
                somente_dias_uteis=somente_dias_uteis,
                tolerancia_percentual=tolerancia,
                priorizar_data_entrega=priorizar_entrega,
                valor_minimo_pedido=valor_minimo_pedido,
            )

            self.meta_diaria_var.set(formatar_moeda(meta_diaria))
            self.tolerancia_var.set(self.formatar_percentual(tolerancia))
            self.valor_minimo_pedido_var.set(formatar_moeda(valor_minimo_pedido))
            self.renderizar_resultado()
            self.controller.set_status("Simulação semanal gerada.")
        except Exception as erro:
            self.resultado_atual = None
            self.limpar_tabela()
            messagebox.showerror("Erro na simulação", str(erro))
            self.controller.set_status("Erro ao gerar simulação semanal.")

    def renderizar_resultado(self, indice_selecionado=0):
        self.limpar_tabela(manter_resumo=True, mostrar_vazio=False)
        resultado = self.resultado_atual
        if not resultado:
            return

        self.labels_resumo["Dias"].config(text=str(resultado["qtd_dias"]))
        self.labels_resumo["Meta total"].config(text=formatar_moeda(resultado["meta_total"]))
        self.labels_resumo["Estimado"].config(text=formatar_moeda(resultado["valor_estimado_total"]))
        self.labels_resumo["Diferença"].config(
            text=formatar_moeda(resultado["diferenca_total"]),
            style="KpiPositive.TLabel" if resultado["diferenca_total"] >= 0 else "KpiWarning.TLabel",
        )
        self.labels_resumo["Tolerância"].config(text=self.formatar_percentual(resultado.get("tolerancia_percentual", 10)))
        self.labels_resumo["Pedidos"].config(text=str(resultado["qtd_pedidos"]))
        self.labels_resumo["Saldo elegível restante"].config(text=formatar_moeda(resultado["valor_restante"]))

        for indice, dia in enumerate(resultado["dias"], start=1):
            self.renderizar_aba_dia(indice, dia)

        abas = self.dias_notebook.tabs()
        if abas:
            indice_selecionado = max(0, min(int(indice_selecionado or 0), len(abas) - 1))
            self.dias_notebook.select(abas[indice_selecionado])

    def renderizar_aba_dia(self, indice, dia):
        aba = ttk.Frame(self.dias_notebook, padding=(4, 4))
        data_txt = dia["data"].strftime("%d/%m")
        titulo_aba = f"{data_txt} • {formatar_moeda(dia['valor_estimado'])}"
        self.dias_notebook.add(aba, text=titulo_aba)

        barra = ttk.Frame(aba, padding=(4, 3), style="Card.TFrame")
        barra.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        barra.columnconfigure(6, weight=1)

        diferenca = dia["diferenca"]
        tolerancia_txt = self.formatar_percentual(self.resultado_atual.get("tolerancia_percentual", 10) if self.resultado_atual else 10)
        resumo_txt = (
            f"{dia['data'].strftime('%d/%m/%Y')}  |  "
            f"Meta: {formatar_moeda(dia['meta'])}  |  "
            f"Estimado: {formatar_moeda(dia['valor_estimado'])}  |  "
            f"Diferença: {formatar_moeda(diferenca)}  |  "
            f"Tol.: {tolerancia_txt}  |  "
            f"Pedidos: {dia['qtd_pedidos']}  |  {dia['status']}"
        )
        estilo_resumo = "KpiPositive.TLabel" if diferenca >= 0 else "KpiWarning.TLabel"
        ttk.Label(barra, text=resumo_txt, style=estilo_resumo).grid(row=0, column=0, sticky="w")

        ttk.Button(
            barra,
            text="Recalcular dia",
            command=lambda idx=indice - 1: self.recalcular_dia_indice(idx),
            style="Compact.TButton",
        ).grid(row=0, column=7, sticky="e", padx=(8, 0))

        ttk.Button(
            barra,
            text="Adicionar dia ao PROG 2",
            command=lambda d=dia: self.adicionar_dia_prog2(d),
            style="Primary.TButton",
        ).grid(row=0, column=8, sticky="e", padx=(4, 0))

        ttk.Button(
            barra,
            text="Expandir",
            command=lambda: self.expandir_tabela_dia(self.dias_notebook.select()),
            style="Compact.TButton",
        ).grid(row=0, column=9, sticky="e", padx=(4, 0))

        ttk.Button(
            barra,
            text="Recolher",
            command=lambda: self.recolher_tabela_dia(self.dias_notebook.select()),
            style="Compact.TButton",
        ).grid(row=0, column=10, sticky="e", padx=(4, 0))

        tabela = self.criar_tabela_dia(aba, dia=dia)
        self.tabelas_dia.append(tabela)
        contexto_tabela = self.contexto_tabelas.get(tabela, {"dia": dia, "indice_dia": indice - 1, "linhas": {}})
        contexto_tabela["indice_dia"] = indice - 1

        for pedido in dia.get("pedidos", []):
            entrega = pedido["data_entrega"].strftime("%d/%m/%Y") if pedido.get("data_entrega") else ""
            id_pedido = tabela.insert(
                "",
                "end",
                text=f"Pedido {pedido['pedido']}",
                values=(
                    pedido["cliente_original"] or pedido["cliente"],
                    entrega,
                    formatar_numero(pedido.get("quantidade", 0)),
                    formatar_moeda(pedido["valor_liberado"]),
                    formatar_moeda(pedido["valor_bloqueado"]),
                    pedido["status"],
                ),
                tags=("pedido_simulado",),
                open=True,
            )
            contexto_tabela["linhas"][id_pedido] = {
                "tipo": "pedido",
                "dia": dia,
                "pedido": pedido,
                "pedido_numero": str(pedido.get("pedido", "")),
            }

            for item in pedido.get("itens", []):
                entrega_item = item["data_entrega"].strftime("%d/%m/%Y") if item.get("data_entrega") else ""
                id_item = tabela.insert(
                    id_pedido,
                    "end",
                    text=item.get("item") or "Item",
                    values=(
                        item.get("descricao", ""),
                        entrega_item,
                        formatar_numero(item.get("quantidade", 0)),
                        formatar_moeda(item.get("valor", 0)),
                        "",
                        "Faturável",
                    ),
                    tags=("item_simulado",),
                )
                contexto_tabela["linhas"][id_item] = {
                    "tipo": "item",
                    "dia": dia,
                    "pedido": pedido,
                    "pedido_numero": str(pedido.get("pedido", "")),
                    "item": item,
                    "item_codigo": str(item.get("item", "")),
                }

        if not dia.get("pedidos"):
            id_vazio = tabela.insert(
                "",
                "end",
                text="Sem pedidos selecionados",
                values=("", "", "", "", "", "Abaixo da meta"),
                tags=("item_simulado",),
            )
            contexto_tabela["linhas"][id_vazio] = {"tipo": "vazio", "dia": dia}

        aba.rowconfigure(1, weight=1)
        aba.columnconfigure(0, weight=1)

    def obter_pedidos_do_dia(self, dia):
        pedidos = []
        for pedido in dia.get("pedidos", []):
            numero = str(pedido.get("pedido", "")).strip()
            if numero and numero not in pedidos:
                pedidos.append(numero)
        return pedidos

    def adicionar_dia_prog2(self, dia):
        pedidos = self.obter_pedidos_do_dia(dia)
        if not pedidos:
            messagebox.showwarning("Nenhum pedido", "Este dia não possui pedidos selecionados para adicionar ao PROG 2.")
            return

        if hasattr(self.controller, "adicionar_pedidos_selecionados_prog2"):
            self.controller.adicionar_pedidos_selecionados_prog2(pedidos)
            data_txt = dia["data"].strftime("%d/%m/%Y") if dia.get("data") else "dia selecionado"
            self.controller.set_status(f"{len(pedidos)} pedido(s) de {data_txt} adicionados ao PROG 2.")

    def adicionar_pedido_prog2_contexto(self, tabela):
        contexto = self.obter_contexto_linha(tabela)
        if not contexto or not contexto.get("pedido_numero"):
            return

        pedido = contexto["pedido_numero"]
        if hasattr(self.controller, "adicionar_pedidos_selecionados_prog2"):
            self.controller.adicionar_pedidos_selecionados_prog2([pedido])
            self.controller.set_status(f"Pedido {pedido} adicionado ao PROG 2.")

    def obter_indice_dia_tabela(self, tabela):
        contexto_tabela = self.contexto_tabelas.get(tabela, {})
        indice = contexto_tabela.get("indice_dia")
        if indice is not None:
            return int(indice)

        aba_id = self.dias_notebook.select()
        abas = list(self.dias_notebook.tabs())
        return abas.index(aba_id) if aba_id in abas else 0

    def recalcular_dia_indice(self, indice_dia):
        if not self.resultado_atual:
            messagebox.showwarning("Nenhuma simulação", "Gere uma simulação antes de recalcular o dia.")
            return

        try:
            self.resultado_atual = self.service.recalcular_dia(self.resultado_atual, int(indice_dia))
            self.renderizar_resultado(indice_selecionado=indice_dia)
            self.controller.set_status("Dia recalculado na simulação.")
        except Exception as erro:
            messagebox.showerror("Erro ao recalcular dia", str(erro))
            self.controller.set_status("Erro ao recalcular dia da simulação.")

    def recalcular_dia_contexto(self, tabela):
        self.recalcular_dia_indice(self.obter_indice_dia_tabela(tabela))

    def remover_pedido_simulacao_contexto(self, tabela):
        contexto = self.obter_contexto_linha(tabela)
        if not contexto or not contexto.get("pedido_numero"):
            return

        pedido = contexto["pedido_numero"]
        indice_dia = self.obter_indice_dia_tabela(tabela)

        confirmar = messagebox.askyesno(
            "Remover pedido",
            f"Remover o pedido {pedido} desta simulação?\n\nEle não será usado ao recalcular os dias até você gerar uma nova simulação.",
        )
        if not confirmar:
            return

        try:
            self.resultado_atual = self.service.remover_pedido_da_simulacao(self.resultado_atual, indice_dia, pedido)
            self.renderizar_resultado(indice_selecionado=indice_dia)
            self.controller.set_status(f"Pedido {pedido} removido da simulação.")
        except Exception as erro:
            messagebox.showerror("Erro ao remover pedido", str(erro))
            self.controller.set_status("Erro ao remover pedido da simulação.")

    def obter_contexto_linha(self, tabela, iid=None):
        if iid is None:
            iid = tabela.focus() or (tabela.selection()[0] if tabela.selection() else "")
        if not iid:
            return None
        contexto_tabela = self.contexto_tabelas.get(tabela, {})
        return contexto_tabela.get("linhas", {}).get(iid)

    def copiar_pedido_contexto(self, tabela):
        contexto = self.obter_contexto_linha(tabela)
        pedido = contexto.get("pedido_numero") if contexto else ""
        if pedido:
            copiar_para_clipboard(tabela, pedido, self.controller, "Pedido copiado.")

    def copiar_item_contexto(self, tabela):
        contexto = self.obter_contexto_linha(tabela)
        item = contexto.get("item_codigo") if contexto else ""
        if item:
            copiar_para_clipboard(tabela, item, self.controller, "Item copiado.")

    def copiar_linha_contexto(self, tabela):
        iid = tabela.focus() or (tabela.selection()[0] if tabela.selection() else "")
        if iid:
            copiar_para_clipboard(tabela, obter_texto_linha_treeview(tabela, iid), self.controller, "Linha copiada.")

    def abrir_detalhes_contexto(self, tabela):
        contexto = self.obter_contexto_linha(tabela)
        if not contexto:
            return

        if contexto.get("tipo") == "pedido":
            pedido = contexto.get("pedido", {})
            itens = []
            for item in pedido.get("itens", []):
                itens.append({
                    "Item": item.get("item", ""),
                    "Descrição": item.get("descricao", ""),
                    "Qtd": formatar_numero(item.get("quantidade", 0)),
                    "Valor": formatar_moeda(item.get("valor", 0)),
                    "Entrega": item["data_entrega"].strftime("%d/%m/%Y") if item.get("data_entrega") else "",
                })

            dados = [
                ("Pedido", pedido.get("pedido", "")),
                ("Cliente", pedido.get("cliente_original") or pedido.get("cliente", "")),
                ("Entrega", pedido["data_entrega"].strftime("%d/%m/%Y") if pedido.get("data_entrega") else ""),
                ("Quantidade", formatar_numero(pedido.get("quantidade", 0))),
                ("Valor faturável", formatar_moeda(pedido.get("valor_liberado", 0))),
                ("Saldo bloqueado/pendente", formatar_moeda(pedido.get("valor_bloqueado", 0))),
                ("Status", pedido.get("status", "")),
            ]
            abrir_janela_detalhes(self.parent, "Detalhes do pedido simulado", dados, itens=itens)
            return

        if contexto.get("tipo") == "item":
            pedido = contexto.get("pedido", {})
            item = contexto.get("item", {})
            dados = [
                ("Pedido", pedido.get("pedido", "")),
                ("Cliente", pedido.get("cliente_original") or pedido.get("cliente", "")),
                ("Item", item.get("item", "")),
                ("Descrição", item.get("descricao", "")),
                ("Entrega", item["data_entrega"].strftime("%d/%m/%Y") if item.get("data_entrega") else ""),
                ("Quantidade", formatar_numero(item.get("quantidade", 0))),
                ("Valor faturável", formatar_moeda(item.get("valor", 0))),
                ("Status", "Faturável"),
            ]
            abrir_janela_detalhes(self.parent, "Detalhes do item simulado", dados)
            return

        self.copiar_linha_contexto(tabela)

    def configurar_menu_contexto_tabela_dia(self, tabela):
        menu = criar_menu_contexto(tabela)
        menu.add_command(label="Ver detalhes", command=lambda t=tabela: self.abrir_detalhes_contexto(t))
        menu.add_command(label="Copiar linha", command=lambda t=tabela: self.copiar_linha_contexto(t))
        menu.add_command(label="Copiar pedido", command=lambda t=tabela: self.copiar_pedido_contexto(t))
        menu.add_command(label="Copiar item", command=lambda t=tabela: self.copiar_item_contexto(t))
        menu.add_separator()
        menu.add_command(label="Adicionar pedido ao PROG 2", command=lambda t=tabela: self.adicionar_pedido_prog2_contexto(t))
        menu.add_command(
            label="Adicionar dia ao PROG 2",
            command=lambda t=tabela: self.adicionar_dia_prog2(self.contexto_tabelas.get(t, {}).get("dia", {})),
        )
        menu.add_separator()
        menu.add_command(label="Recalcular dia", command=lambda t=tabela: self.recalcular_dia_contexto(t))
        menu.add_command(label="Remover pedido da simulação", command=lambda t=tabela: self.remover_pedido_simulacao_contexto(t))
        menu.add_separator()
        menu.add_command(label="Expandir pedido", command=lambda t=tabela: self.expandir_linha_focada(t))
        menu.add_command(label="Recolher pedido", command=lambda t=tabela: self.recolher_linha_focada(t))
        menu.add_command(label="Expandir todos", command=lambda t=tabela: self.expandir_todos_tabela(t))
        menu.add_command(label="Recolher todos", command=lambda t=tabela: self.recolher_todos_tabela(t))

        def abrir_menu(event):
            iid = tabela.identify_row(event.y)
            if not iid:
                return "break"
            tabela.selection_set(iid)
            tabela.focus(iid)
            contexto = self.obter_contexto_linha(tabela, iid) or {}
            tipo = contexto.get("tipo")
            menu.entryconfig("Copiar item", state="normal" if tipo == "item" else "disabled")
            menu.entryconfig("Adicionar pedido ao PROG 2", state="normal" if tipo in ("pedido", "item") else "disabled")
            menu.entryconfig("Remover pedido da simulação", state="normal" if tipo in ("pedido", "item") else "disabled")
            menu.tk_popup(event.x_root, event.y_root)
            return "break"

        tabela.bind("<Button-3>", abrir_menu)
        tabela.bind("<Double-1>", lambda event, t=tabela: self.abrir_detalhes_contexto(t))
        tabela.bind("<Return>", lambda event, t=tabela: self.abrir_detalhes_contexto(t))
        tabela.menu_contexto_simulacao = menu

    def expandir_linha_focada(self, tabela):
        iid = tabela.focus() or (tabela.selection()[0] if tabela.selection() else "")
        if iid:
            tabela.item(iid, open=True)

    def recolher_linha_focada(self, tabela):
        iid = tabela.focus() or (tabela.selection()[0] if tabela.selection() else "")
        if iid:
            tabela.item(iid, open=False)

    def expandir_todos_tabela(self, tabela):
        for iid in tabela.get_children(""):
            tabela.item(iid, open=True)

    def recolher_todos_tabela(self, tabela):
        for iid in tabela.get_children(""):
            tabela.item(iid, open=False)

    def obter_tabela_por_aba_id(self, aba_id):
        if not aba_id:
            return None
        try:
            aba = self.dias_notebook.nametowidget(aba_id)
        except Exception:
            return None
        for child in aba.winfo_children():
            if isinstance(child, ttk.Treeview):
                return child
            for grandchild in child.winfo_children():
                if isinstance(grandchild, ttk.Treeview):
                    return grandchild
        return None

    def expandir_tabela_dia(self, aba_id):
        tabela = self.obter_tabela_por_aba_id(aba_id)
        if tabela:
            self.expandir_todos_tabela(tabela)

    def recolher_tabela_dia(self, aba_id):
        tabela = self.obter_tabela_por_aba_id(aba_id)
        if tabela:
            self.recolher_todos_tabela(tabela)

    def limpar_tabela(self, manter_resumo=False, mostrar_vazio=True):
        if hasattr(self, "dias_notebook"):
            for aba_id in self.dias_notebook.tabs():
                widget = self.dias_notebook.nametowidget(aba_id)
                self.dias_notebook.forget(aba_id)
                widget.destroy()

            self.tabelas_dia = []
            self.contexto_tabelas = {}
            if mostrar_vazio:
                self.aba_vazia = ttk.Frame(self.dias_notebook, padding=(12, 10))
                ttk.Label(
                    self.aba_vazia,
                    text="Gere uma simulação para visualizar os dias separados em abas.",
                    style="Hint.TLabel",
                ).pack(anchor="w")
                self.dias_notebook.add(self.aba_vazia, text="Sem simulação")

        if not manter_resumo and hasattr(self, "labels_resumo"):
            self.labels_resumo["Dias"].config(text="-")
            self.labels_resumo["Meta total"].config(text="R$ 0,00")
            self.labels_resumo["Estimado"].config(text="R$ 0,00")
            self.labels_resumo["Diferença"].config(text="R$ 0,00", style="KpiValue.TLabel")
            if "Tolerância" in self.labels_resumo:
                self.labels_resumo["Tolerância"].config(text="10%")
            self.labels_resumo["Pedidos"].config(text="0")
            self.labels_resumo["Saldo elegível restante"].config(text="R$ 0,00")

    def refresh(self):
        # A simulação não é recalculada automaticamente para evitar trocar o resultado sem ação do usuário.
        pass

    def focar_busca(self):
        pass

    def get_current_df(self):
        if not self.resultado_atual:
            return None

        linhas = []
        for dia in self.resultado_atual["dias"]:
            for pedido in dia.get("pedidos", []):
                linhas.append({
                    "Data": dia["data"].strftime("%d/%m/%Y"),
                    "Tipo": "Pedido",
                    "Pedido": pedido["pedido"],
                    "Item": "",
                    "Descrição": "",
                    "Cliente": pedido["cliente_original"] or pedido["cliente"],
                    "Entrega": pedido["data_entrega"].strftime("%d/%m/%Y") if pedido.get("data_entrega") else "",
                    "Qtd": pedido.get("quantidade", 0),
                    "Valor Faturável": pedido["valor_liberado"],
                    "Saldo Bloqueado/Pendente": pedido["valor_bloqueado"],
                    "Status": pedido["status"],
                })

                for item in pedido.get("itens", []):
                    linhas.append({
                        "Data": dia["data"].strftime("%d/%m/%Y"),
                        "Tipo": "Item",
                        "Pedido": pedido["pedido"],
                        "Item": item.get("item", ""),
                        "Descrição": item.get("descricao", ""),
                        "Cliente": pedido["cliente_original"] or pedido["cliente"],
                        "Entrega": item["data_entrega"].strftime("%d/%m/%Y") if item.get("data_entrega") else "",
                        "Qtd": item.get("quantidade", 0),
                        "Valor Faturável": item.get("valor", 0),
                        "Saldo Bloqueado/Pendente": "",
                        "Status": "Faturável",
                    })
        return pd.DataFrame(linhas)

    def exportar_excel(self):
        if not self.resultado_atual:
            messagebox.showwarning("Nenhuma simulação", "Gere uma simulação antes de exportar.")
            return

        initialdir = self.controller.obter_pasta_exportacao() if hasattr(self.controller, "obter_pasta_exportacao") else None
        initialfile = self.controller.gerar_nome_exportacao("Simulacao_Faturamento", "xlsx") if hasattr(self.controller, "gerar_nome_exportacao") else f"Simulacao_Faturamento_{datetime.now().strftime('%Y-%m-%d')}.xlsx"

        caminho = filedialog.asksaveasfilename(
            title="Exportar simulação semanal",
            initialdir=initialdir,
            initialfile=initialfile,
            defaultextension=".xlsx",
            filetypes=[("Arquivo Excel", "*.xlsx")],
        )

        if not caminho:
            return

        try:
            exportar_simulacao_faturamento_excel(caminho, self.resultado_atual)
            messagebox.showinfo("Exportação concluída", f"Simulação exportada com sucesso:\n{caminho}")
            self.controller.set_status(f"Simulação semanal exportada: {caminho}")
        except Exception as erro:
            self.controller.registrar_erro("Erro ao exportar simulação semanal", erro)
            messagebox.showerror("Erro ao exportar", f"Não foi possível gerar a planilha de simulação.\n\nDetalhe: {erro}")
