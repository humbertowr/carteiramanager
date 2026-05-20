import os
import tempfile
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import pandas as pd

from core.app_state import AppState, CLIENTES_BLOQUEIO_PADRAO
from core.carteira_processor import carregar_carteira
from core.exporter import (
    exportar_csv,
    exportar_excel_completo,
    exportar_dataframe_excel,
    exportar_dataframe_pdf,
)
from core.formatters import formatar_moeda
from ui.styles import configurar_estilo
from ui.pedidos_tab import PedidosTab
from ui.prog2_tab import Prog2Tab
from ui.liberados_tab import LiberadosTab
from ui.bloqueios_tab import BloqueiosTab
from ui.consolidacoes_tab import ConsolidacoesTab


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Consolidador de Carteira de Pedidos")
        self.root.geometry("1500x860")
        self.root.minsize(1180, 700)

        configurar_estilo()

        self.state = AppState()
        self.labels_resumo = {}

        self.criar_interface()

    def criar_interface(self):
        self.criar_topo()
        self.criar_resumo()
        self.criar_abas()
        self.criar_barra_status()

    def criar_topo(self):
        frame = ttk.Frame(self.root, padding=(8, 6))
        frame.pack(fill="x")

        bloco_titulo = ttk.Frame(frame)
        bloco_titulo.pack(side="left", fill="x", expand=True)

        titulo = ttk.Label(
            bloco_titulo,
            text="Consolidador de Carteira de Pedidos",
            style="Title.TLabel"
        )
        titulo.pack(anchor="w")

        subtitulo = ttk.Label(
            bloco_titulo,
            text="Importe a carteira, bloqueie pedidos/itens/clientes e monte a programação PROG 2.",
            style="Subtitle.TLabel"
        )
        subtitulo.pack(anchor="w", pady=(1, 0))

        bloco_botoes = ttk.Frame(frame)
        bloco_botoes.pack(side="right")

        ttk.Button(
            bloco_botoes,
            text="Importar CSV",
            command=self.importar_csv,
            style="Primary.TButton"
        ).pack(side="left", padx=3)

        ttk.Button(
            bloco_botoes,
            text="Exportar Excel",
            command=self.exportar_excel
        ).pack(side="left", padx=3)

        ttk.Button(
            bloco_botoes,
            text="Exportar CSV",
            command=self.exportar_csv_atual
        ).pack(side="left", padx=3)

    def criar_resumo(self):
        frame = ttk.LabelFrame(
            self.root,
            text="Resumo geral",
            padding=(6, 3),
            style="Summary.TLabelframe"
        )
        frame.pack(fill="x", padx=8, pady=(0, 5))

        campos = [
            "Pedidos Abertos",
            "Pedidos Bloqueados",
            "Clientes Bloq.",
            "Pedidos PROG 2",
            "Obs. Bloqueadas",
            "Valor Carteira",
            "Valor Bloqueado",
            "Valor Liberado",
            "Valor liberado PROG 2",
        ]

        for indice, campo in enumerate(campos):
            bloco = ttk.Frame(frame, padding=(4, 2))
            bloco.grid(row=0, column=indice, sticky="nsew", padx=2)

            ttk.Label(
                bloco,
                text=campo,
                style="SummaryTitle.TLabel"
            ).pack(anchor="center")

            label_valor = ttk.Label(
                bloco,
                text="-",
                style="SummaryValue.TLabel"
            )
            label_valor.pack(anchor="center", pady=(1, 0))

            self.labels_resumo[campo] = label_valor

        for i in range(len(campos)):
            frame.columnconfigure(i, weight=1)

    def criar_abas(self):
        self.abas = ttk.Notebook(self.root)
        self.abas.pack(fill="both", expand=True, padx=8, pady=(0, 5))

        aba_pedidos = ttk.Frame(self.abas)
        aba_prog2 = ttk.Frame(self.abas)
        aba_liberados = ttk.Frame(self.abas)
        aba_bloqueios = ttk.Frame(self.abas)
        aba_consolidacoes = ttk.Frame(self.abas)

        self.abas.add(aba_pedidos, text="Pedidos")
        self.abas.add(aba_prog2, text="PROG 2")
        self.abas.add(aba_liberados, text="Liberados")
        self.abas.add(aba_bloqueios, text="Bloqueios")
        self.abas.add(aba_consolidacoes, text="Consolidações")

        self.pedidos_tab = PedidosTab(aba_pedidos, self, self.state)
        self.prog2_tab = Prog2Tab(aba_prog2, self, self.state)
        self.liberados_tab = LiberadosTab(aba_liberados, self, self.state, self.pedidos_tab)
        self.bloqueios_tab = BloqueiosTab(aba_bloqueios, self, self.state)
        self.consolidacoes_tab = ConsolidacoesTab(aba_consolidacoes, self, self.state)

    def criar_barra_status(self):
        self.status = ttk.Label(
            self.root,
            text="Importe um arquivo CSV para começar.",
            relief="sunken",
            anchor="w",
            padding=(6, 4)
        )
        self.status.pack(fill="x", side="bottom")

    def set_status(self, texto):
        self.status.config(text=texto)

    def importar_csv(self):
        caminho = filedialog.askopenfilename(
            title="Selecione o arquivo CSV da carteira",
            filetypes=[
                ("Arquivos CSV/TXT", "*.csv *.txt"),
                ("Todos os arquivos", "*.*")
            ]
        )

        if not caminho:
            return

        try:
            self.set_status("Importando arquivo...")
            self.root.update_idletasks()

            df = carregar_carteira(caminho)
            self.state.carregar_dataframe(df)

            self.refresh_all()

            self.set_status(f"Arquivo importado com sucesso: {caminho}")

        except Exception as erro:
            messagebox.showerror(
                "Erro ao importar arquivo",
                str(erro)
            )
            self.set_status("Erro ao importar arquivo.")

    def refresh_all(self):
        self.atualizar_resumo()
        self.pedidos_tab.refresh()
        self.prog2_tab.refresh()
        self.liberados_tab.refresh()
        self.bloqueios_tab.refresh()
        self.consolidacoes_tab.refresh()

    def refresh_pedidos(self):
        self.pedidos_tab.refresh()
        self.prog2_tab.refresh()
        self.liberados_tab.refresh()
        self.atualizar_resumo()

    def atualizar_resumo(self):
        if not self.state.tem_dados():
            return

        df_aberto = self.state.df_aberto()
        df_bloqueios = self.state.df_com_bloqueios(df_aberto)

        valor_total = df_bloqueios["Valor em Carteira"].sum() if not df_bloqueios.empty else 0
        valor_bloqueado = df_bloqueios["_Valor Bloqueado"].sum() if not df_bloqueios.empty else 0
        valor_liberado = df_bloqueios["_Valor Liberado"].sum() if not df_bloqueios.empty else 0
        totais_prog2 = self.state.calcular_totais_prog2()

        pedidos_bloqueados_total = set(self.state.pedidos_bloqueados)
        pedidos_bloqueados_total.update(self.state.pedidos_bloqueados_por_observacao_set())
        pedidos_bloqueados_total.update(self.state.pedidos_bloqueados_por_cliente_set())

        valores = {
            "Pedidos Abertos": df_aberto["Pedido"].nunique(),
            "Pedidos Bloqueados": len(pedidos_bloqueados_total),
            "Clientes Bloq.": len(self.state.clientes_bloqueados),
            "Pedidos PROG 2": totais_prog2["pedidos"],
            "Obs. Bloqueadas": len(self.state.observacoes_bloqueadas),
            "Valor Carteira": formatar_moeda(valor_total),
            "Valor Bloqueado": formatar_moeda(valor_bloqueado),
            "Valor Liberado": formatar_moeda(valor_liberado),
            "Valor liberado PROG 2": formatar_moeda(totais_prog2["valor_liberado"]),
        }

        for campo, label in self.labels_resumo.items():
            label.config(text=str(valores.get(campo, "-")))

    def abrir_janela_checkbox(
        self,
        titulo,
        subtitulo,
        registros,
        chave_coluna,
        texto_funcao,
        texto_busca_funcao,
        selecionados_atuais,
        ao_bloquear,
        ao_liberar,
        preset=None,
    ):
        janela = tk.Toplevel(self.root)
        janela.title(titulo)
        janela.geometry("980x580")
        janela.minsize(760, 440)
        janela.transient(self.root)
        janela.grab_set()

        busca_var = tk.StringVar()

        variaveis = {
            registro[chave_coluna]: tk.BooleanVar(
                value=registro[chave_coluna] in selecionados_atuais
            )
            for registro in registros
        }

        frame_topo = ttk.Frame(janela, padding=8)
        frame_topo.pack(fill="x")

        ttk.Label(
            frame_topo,
            text=titulo,
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w")

        ttk.Label(
            frame_topo,
            text=subtitulo,
            style="Subtitle.TLabel"
        ).pack(anchor="w", pady=(1, 0))

        frame_pesquisa = ttk.Frame(janela, padding=(8, 0, 8, 6))
        frame_pesquisa.pack(fill="x")

        ttk.Label(frame_pesquisa, text="Pesquisar:").pack(side="left", padx=(0, 5))

        entrada_busca = ttk.Entry(
            frame_pesquisa,
            textvariable=busca_var,
            width=52
        )
        entrada_busca.pack(side="left", padx=(0, 10))

        frame_preset = ttk.Frame(janela, padding=(8, 0, 8, 4))
        frame_preset.pack(fill="x")

        if preset:
            preset_nome = preset["nome"]
            preset_chaves = set(preset["chaves"])
            preset_chaves_presentes = [
                chave
                for chave in preset_chaves
                if chave in variaveis
            ]

            preset_var = tk.BooleanVar(
                value=bool(preset_chaves_presentes)
                and all(chave in selecionados_atuais for chave in preset_chaves_presentes)
            )

            def alternar_preset():
                if preset_var.get():
                    ao_bloquear(preset_chaves_presentes)

                    for chave in preset_chaves_presentes:
                        variaveis[chave].set(True)

                    self.refresh_all()
                    self.set_status(f"{preset_nome} aplicado.")
                else:
                    ao_liberar(preset_chaves_presentes)

                    for chave in preset_chaves_presentes:
                        variaveis[chave].set(False)

                    self.refresh_all()
                    self.set_status(f"{preset_nome} removido.")

            ttk.Checkbutton(
                frame_preset,
                text=preset_nome,
                variable=preset_var,
                command=alternar_preset
            ).pack(anchor="w")

        frame_acoes = ttk.Frame(janela, padding=(8, 0, 8, 6))
        frame_acoes.pack(fill="x")

        frame_lista = ttk.Frame(janela, padding=(8, 0, 8, 8))
        frame_lista.pack(fill="both", expand=True)

        canvas = tk.Canvas(frame_lista, borderwidth=0, highlightthickness=0)
        scroll_y = ttk.Scrollbar(frame_lista, orient="vertical", command=canvas.yview)
        frame_checks = ttk.Frame(canvas)

        frame_checks.bind(
            "<Configure>",
            lambda event: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=frame_checks, anchor="nw")
        canvas.configure(yscrollcommand=scroll_y.set)

        canvas.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")

        frame_lista.rowconfigure(0, weight=1)
        frame_lista.columnconfigure(0, weight=1)

        registros_visiveis = []

        def obter_filtrados():
            termo = busca_var.get().strip().lower()

            if not termo:
                return registros

            filtrados = []

            for registro in registros:
                texto_busca = texto_busca_funcao(registro).lower()

                if termo in texto_busca:
                    filtrados.append(registro)

            return filtrados

        def renderizar():
            nonlocal registros_visiveis

            for widget in frame_checks.winfo_children():
                widget.destroy()

            registros_visiveis = obter_filtrados()

            if not registros_visiveis:
                ttk.Label(
                    frame_checks,
                    text="Nenhum resultado encontrado.",
                    style="Subtitle.TLabel"
                ).grid(row=0, column=0, sticky="w", padx=4, pady=4)
                return

            for indice, registro in enumerate(registros_visiveis):
                chave = registro[chave_coluna]

                check = ttk.Checkbutton(
                    frame_checks,
                    text=texto_funcao(registro),
                    variable=variaveis[chave]
                )
                check.grid(row=indice, column=0, sticky="w", padx=4, pady=2)

            canvas.yview_moveto(0)

        def marcar_todos():
            for registro in registros_visiveis:
                variaveis[registro[chave_coluna]].set(True)

        def desmarcar_todos():
            for registro in registros_visiveis:
                variaveis[registro[chave_coluna]].set(False)

        ttk.Button(
            frame_acoes,
            text="Marcar todos",
            command=marcar_todos
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            frame_acoes,
            text="Desmarcar todos",
            command=desmarcar_todos
        ).pack(side="left", padx=5)

        ttk.Label(
            frame_acoes,
            text="Os botões acima afetam somente os itens visíveis na pesquisa.",
            style="Subtitle.TLabel"
        ).pack(side="left", padx=16)

        busca_var.trace_add("write", lambda *args: renderizar())

        frame_botoes = ttk.Frame(janela, padding=8)
        frame_botoes.pack(fill="x")

        def confirmar_bloqueio():
            selecionados = [
                chave
                for chave, var in variaveis.items()
                if var.get()
            ]

            if not selecionados:
                messagebox.showwarning(
                    "Nenhum item selecionado",
                    "Selecione pelo menos uma opção."
                )
                return

            ao_bloquear(selecionados)
            self.refresh_all()
            janela.destroy()
            self.set_status("Bloqueios atualizados.")

        def confirmar_liberacao():
            selecionados = [
                chave
                for chave, var in variaveis.items()
                if var.get()
            ]

            if not selecionados:
                messagebox.showwarning(
                    "Nenhum item selecionado",
                    "Selecione pelo menos uma opção."
                )
                return

            ao_liberar(selecionados)
            self.refresh_all()
            janela.destroy()
            self.set_status("Bloqueios atualizados.")

        ttk.Button(
            frame_botoes,
            text="Bloquear selecionados",
            command=confirmar_bloqueio,
            style="Primary.TButton"
        ).pack(side="left", padx=5)

        ttk.Button(
            frame_botoes,
            text="Liberar selecionados",
            command=confirmar_liberacao
        ).pack(side="left", padx=5)

        ttk.Button(
            frame_botoes,
            text="Fechar",
            command=janela.destroy
        ).pack(side="right", padx=5)

        entrada_busca.focus_set()
        renderizar()

    def bloquear_item_selecionado(self):
        if not self.state.tem_dados():
            messagebox.showwarning("Nenhum arquivo", "Importe um CSV primeiro.")
            return

        id_linha = self.pedidos_tab.get_selected_id_linha()

        if id_linha is None:
            messagebox.showwarning(
                "Seleção inválida",
                "Selecione um item dentro de um pedido."
            )
            return

        self.state.bloquear_linha(id_linha, "")
        self.refresh_all()
        self.set_status("Item selecionado bloqueado para faturamento.")

    def bloquear_pedido_selecionado(self):
        if not self.state.tem_dados():
            messagebox.showwarning("Nenhum arquivo", "Importe um CSV primeiro.")
            return

        pedido = self.pedidos_tab.get_selected_pedido()

        if not pedido:
            messagebox.showwarning(
                "Nenhum pedido selecionado",
                "Selecione a linha principal do pedido ou um item dentro do pedido."
            )
            return

        self.state.bloquear_pedido(pedido, "")
        self.refresh_all()
        self.set_status(f"Pedido {pedido} bloqueado para faturamento.")

    def bloquear_item_global(self):
        if not self.state.tem_dados():
            messagebox.showwarning("Nenhum arquivo", "Importe um CSV primeiro.")
            return

        codigo = self.pedidos_tab.get_codigo_item_global()

        if not codigo:
            messagebox.showwarning(
                "Nenhum item informado",
                "Digite o código do item ou selecione um item na aba Pedidos."
            )
            return

        self.state.bloquear_item_global(codigo, "")
        self.pedidos_tab.set_codigo_item_global(codigo)

        self.refresh_all()
        self.set_status(f"Item {codigo} bloqueado na carteira inteira.")

    def liberar_item_global(self):
        if not self.state.tem_dados():
            return

        codigo = self.pedidos_tab.get_codigo_item_global()

        if not codigo:
            messagebox.showwarning(
                "Nenhum item informado",
                "Digite o código do item ou selecione um item."
            )
            return

        self.state.liberar_item_global(codigo)

        self.refresh_all()
        self.set_status(f"Item {codigo} liberado na carteira inteira.")

    def adicionar_pedido_selecionado_prog2(self):
        if not self.state.tem_dados():
            messagebox.showwarning("Nenhum arquivo", "Importe um CSV primeiro.")
            return

        pedido = self.pedidos_tab.get_selected_pedido()

        if not pedido:
            messagebox.showwarning(
                "Nenhum pedido selecionado",
                "Selecione a linha do pedido ou qualquer item dentro dele."
            )
            return

        self.state.adicionar_pedido_prog2(pedido)
        self.refresh_all()
        self.set_status(f"Pedido {pedido} adicionado ao PROG 2.")

    def remover_pedido_selecionado_prog2(self):
        pedido = self.prog2_tab.get_selected_pedido()

        if not pedido:
            messagebox.showwarning(
                "Nenhum pedido selecionado",
                "Selecione um pedido ou item no PROG 2."
            )
            return

        self.state.remover_pedido_prog2(pedido)
        self.refresh_all()
        self.set_status(f"Pedido {pedido} removido do PROG 2.")

    def limpar_prog2(self):
        if not self.state.pedidos_prog2:
            return

        confirmar = messagebox.askyesno(
            "Limpar PROG 2",
            "Deseja remover todos os pedidos do PROG 2?"
        )

        if not confirmar:
            return

        self.state.limpar_prog2()
        self.refresh_all()
        self.set_status("PROG 2 limpo.")

    def abrir_janela_bloqueio_observacao(self):
        if not self.state.tem_dados():
            messagebox.showwarning("Nenhum arquivo", "Importe um CSV primeiro.")
            return

        observacoes = self.state.obter_observacoes_disponiveis()

        if not observacoes:
            messagebox.showinfo(
                "Sem observações",
                "Não foram encontradas observações nos pedidos em aberto."
            )
            return

        self.abrir_janela_checkbox(
            titulo="Bloquear pedidos por observação",
            subtitulo="Pesquise, marque as observações e bloqueie todos os pedidos relacionados.",
            registros=observacoes,
            chave_coluna="observacao",
            texto_funcao=lambda r: (
                f'{r["observacao"]} | '
                f'Pedidos: {r["pedidos"]} | '
                f'Itens: {r["itens"]} | '
                f'Valor: {formatar_moeda(r["valor"])}'
            ),
            texto_busca_funcao=lambda r: r["observacao"],
            selecionados_atuais=self.state.observacoes_bloqueadas,
            ao_bloquear=lambda selecionados: self.state.bloquear_observacoes(selecionados, ""),
            ao_liberar=lambda selecionados: [self.state.liberar_observacao(item) for item in selecionados],
        )

    def abrir_janela_bloqueio_cliente(self):
        if not self.state.tem_dados():
            messagebox.showwarning("Nenhum arquivo", "Importe um CSV primeiro.")
            return

        clientes = self.state.obter_clientes_bloqueio_disponiveis()

        if not clientes:
            messagebox.showinfo(
                "Clientes não encontrados",
                "Nenhum cliente foi encontrado nos pedidos em aberto."
            )
            return

        self.abrir_janela_checkbox(
            titulo="Bloquear pedidos por cliente",
            subtitulo="Todos os clientes presentes na carteira aparecem abaixo. O preset aplica os clientes fixos configurados.",
            registros=clientes,
            chave_coluna="cliente_chave",
            texto_funcao=lambda r: (
                f'{"[PRESET] " if r["preset_1"] else ""}'
                f'{r["cliente_curto"]} | '
                f'Pedidos: {r["pedidos"]} | '
                f'Itens: {r["itens"]} | '
                f'Valor: {formatar_moeda(r["valor"])} | '
                f'{r["cliente_original"]}'
            ),
            texto_busca_funcao=lambda r: (
                f'{r["cliente_curto"]} {r["cliente_original"]} {r["cliente_chave"]}'
            ),
            selecionados_atuais=self.state.clientes_bloqueados,
            ao_bloquear=lambda selecionados: self.state.bloquear_clientes(selecionados, ""),
            ao_liberar=lambda selecionados: [self.state.liberar_cliente(item) for item in selecionados],
            preset={
                "nome": "CLIENTES BLOQUEADOS 1",
                "chaves": self.state.clientes_preset_bloqueados_1(),
            },
        )

    def abrir_janela_bloqueio_item(self):
        if not self.state.tem_dados():
            messagebox.showwarning("Nenhum arquivo", "Importe um CSV primeiro.")
            return

        itens = self.state.obter_itens_bloqueio_disponiveis()

        if not itens:
            messagebox.showinfo(
                "Itens não encontrados",
                "Nenhum item foi encontrado nos pedidos em aberto."
            )
            return

        self.abrir_janela_checkbox(
            titulo="Bloquear itens na carteira inteira",
            subtitulo="Pesquise por código ou descrição. O bloqueio vale para o item em todos os pedidos.",
            registros=itens,
            chave_coluna="item",
            texto_funcao=lambda r: (
                f'{r["item"]} - {r["descricao"]} | '
                f'Pedidos: {r["pedidos"]} | '
                f'Clientes: {r["clientes"]} | '
                f'Linhas: {r["linhas"]} | '
                f'Valor: {formatar_moeda(r["valor"])}'
            ),
            texto_busca_funcao=lambda r: (
                f'{r["item"]} {r["descricao"]}'
            ),
            selecionados_atuais=self.state.codigos_itens_bloqueados,
            ao_bloquear=lambda selecionados: self.state.bloquear_itens_globais(selecionados, ""),
            ao_liberar=lambda selecionados: self.state.liberar_itens_globais(selecionados),
        )

    def gerar_df_prog2_itens_liberados(self):
        if not self.state.tem_dados() or not self.state.pedidos_prog2:
            return pd.DataFrame()

        df = self.state.df_com_bloqueios(self.state.df_aberto())

        pedidos_prog2 = set(str(pedido) for pedido in self.state.pedidos_prog2)
        df = df[df["Pedido Texto"].isin(pedidos_prog2)]

        if df.empty:
            return pd.DataFrame()

        df = df[~df["_Bloqueado"]].copy()

        if df.empty:
            return pd.DataFrame()

        resultado = df.groupby(
            ["Item", "Descrição Item"],
            as_index=False
        ).agg({
            "Pedido": "nunique",
            "Cliente": "nunique",
            "Saldo a Faturar": "sum",
            "Valor em Carteira": "sum",
        })

        resultado.rename(
            columns={
                "Pedido": "Qtd. Pedidos",
                "Cliente": "Qtd. Clientes",
                "Saldo a Faturar": "Qtde Liberada",
                "Valor em Carteira": "Valor Liberado",
            },
            inplace=True
        )

        resultado.sort_values(
            "Valor Liberado",
            ascending=False,
            inplace=True
        )

        return resultado

    def gerar_df_prog2_pedidos_liberados(self):
        if not self.state.tem_dados() or not self.state.pedidos_prog2:
            return pd.DataFrame()

        df = self.state.df_com_bloqueios(self.state.df_aberto())

        pedidos_prog2 = set(str(pedido) for pedido in self.state.pedidos_prog2)
        df = df[df["Pedido Texto"].isin(pedidos_prog2)]

        if df.empty:
            return pd.DataFrame()

        df = df[~df["_Bloqueado"]].copy()

        if df.empty:
            return pd.DataFrame()

        registros = []

        for pedido, grupo in df.groupby("Pedido", sort=False):
            cliente_original = str(grupo["Cliente"].iloc[0])
            cliente_abrev = self.state.abreviar_cliente(cliente_original)

            registros.append({
                "Pedido": pedido,
                "Cliente": cliente_abrev,
                "Cliente Original": cliente_original,
                "Data Entrega": str(grupo["Data Entrega"].iloc[0]),
                "Grupo": str(grupo["Grupo Faturamento Abrev"].iloc[0]),
                "Qtd. Itens Liberados": grupo["Item"].nunique(),
                "Qtde Liberada": grupo["Saldo a Faturar"].sum(),
                "Valor Total Liberado": grupo["Valor em Carteira"].sum(),
            })

        resultado = pd.DataFrame(registros)

        if not resultado.empty:
            resultado.sort_values(
                "Valor Total Liberado",
                ascending=False,
                inplace=True
            )

        return resultado

    def abrir_arquivo_pdf(self, caminho):
        try:
            os.startfile(caminho)
        except Exception:
            caminho_url = caminho.replace(os.sep, "/")
            webbrowser.open(f"file:///{caminho_url}")

    def exportar_dataframe_escolhido(self, df_exportar, titulo, nome_padrao, formato):
        if df_exportar.empty:
            messagebox.showwarning(
                "Sem dados para exportar",
                "Não há dados liberados para exportar."
            )
            return

        if formato == "pdf":
            try:
                arquivo_temporario = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".pdf",
                    prefix=f"{nome_padrao}_"
                )
                caminho = arquivo_temporario.name
                arquivo_temporario.close()

                exportar_dataframe_pdf(
                    caminho,
                    df_exportar,
                    titulo=titulo
                )

                self.abrir_arquivo_pdf(caminho)
                self.set_status(f"PDF temporário aberto: {caminho}")

            except Exception as erro:
                messagebox.showerror(
                    "Erro ao gerar PDF",
                    str(erro)
                )

            return

        caminho = filedialog.asksaveasfilename(
            title=titulo,
            initialfile=nome_padrao + ".xlsx",
            defaultextension=".xlsx",
            filetypes=[("Arquivo Excel", "*.xlsx")]
        )

        if not caminho:
            return

        try:
            exportar_dataframe_excel(
                caminho,
                df_exportar,
                sheet_name=nome_padrao[:31]
            )

            messagebox.showinfo(
                "Exportação concluída",
                f"Arquivo exportado com sucesso:\n{caminho}"
            )

            self.set_status(f"Arquivo exportado: {caminho}")

        except Exception as erro:
            messagebox.showerror(
                "Erro ao exportar",
                str(erro)
            )

    def exportar_prog2_itens_liberados(self, formato="excel"):
        df_exportar = self.gerar_df_prog2_itens_liberados()

        self.exportar_dataframe_escolhido(
            df_exportar=df_exportar,
            titulo="Itens liberados do PROG 2",
            nome_padrao="prog2_itens_liberados",
            formato=formato
        )

    def exportar_prog2_pedidos_liberados(self, formato="excel"):
        df_exportar = self.gerar_df_prog2_pedidos_liberados()

        self.exportar_dataframe_escolhido(
            df_exportar=df_exportar,
            titulo="Pedidos liberados do PROG 2",
            nome_padrao="prog2_pedidos_liberados",
            formato=formato
        )

    def liberar_selecao_pedidos(self):
        if not self.state.tem_dados():
            return

        pedido = self.pedidos_tab.get_selected_pedido()
        id_linha = self.pedidos_tab.get_selected_id_linha()

        if not pedido and id_linha is None:
            messagebox.showwarning("Nenhuma seleção", "Selecione um item ou pedido.")
            return

        if pedido and id_linha is None:
            self.state.liberar_pedido(pedido)

            cliente = self.state.cliente_bloqueado_do_pedido(pedido)
            if cliente:
                nome_curto = CLIENTES_BLOQUEIO_PADRAO.get(cliente, cliente)
                confirmar = messagebox.askyesno(
                    "Liberar cliente",
                    f"O pedido também está bloqueado pelo cliente:\n\n{nome_curto}\n\nDeseja liberar esse cliente?"
                )

                if confirmar:
                    self.state.liberar_cliente(cliente)

            observacao = self.state.observacao_bloqueada_do_pedido(pedido)
            if observacao:
                confirmar = messagebox.askyesno(
                    "Liberar observação",
                    f"O pedido também está bloqueado pela observação:\n\n{observacao}\n\nDeseja liberar essa observação?"
                )

                if confirmar:
                    self.state.liberar_observacao(observacao)

            self.refresh_all()
            self.set_status(f"Pedido {pedido} liberado.")
            return

        linha = self.state.pegar_linha_por_id(id_linha)

        if linha is None:
            return

        pedido_linha = str(linha["Pedido"])
        item = str(linha["Item"])

        if pedido_linha in self.state.pedidos_bloqueados:
            confirmar = messagebox.askyesno(
                "Liberar pedido",
                f"Este item está bloqueado porque o pedido {pedido_linha} está bloqueado.\n\nDeseja liberar o pedido inteiro?"
            )

            if confirmar:
                self.state.liberar_pedido(pedido_linha)

        elif self.state.cliente_bloqueado_da_linha(linha):
            cliente = self.state.cliente_bloqueado_da_linha(linha)
            nome_curto = CLIENTES_BLOQUEIO_PADRAO.get(cliente, cliente)

            confirmar = messagebox.askyesno(
                "Liberar cliente",
                f"Este pedido está bloqueado pelo cliente:\n\n{nome_curto}\n\nDeseja liberar esse cliente?"
            )

            if confirmar:
                self.state.liberar_cliente(cliente)

        elif self.state.pedido_bloqueado_por_observacao(pedido_linha):
            observacao = self.state.observacao_bloqueada_do_pedido(pedido_linha)

            confirmar = messagebox.askyesno(
                "Liberar observação",
                f"Este pedido está bloqueado pela observação:\n\n{observacao}\n\nDeseja liberar essa observação?"
            )

            if confirmar:
                self.state.liberar_observacao(observacao)

        elif item in self.state.codigos_itens_bloqueados:
            confirmar = messagebox.askyesno(
                "Liberar item na carteira inteira",
                f"Este item está bloqueado na carteira inteira.\n\nDeseja liberar o item {item} em todos os pedidos?"
            )

            if confirmar:
                self.state.liberar_item_global(item)

        else:
            self.state.liberar_linha(id_linha)

        self.refresh_all()
        self.set_status("Seleção liberada.")

    def liberar_bloqueio_na_aba(self):
        id_linha = self.bloqueios_tab.get_selected_id_linha()

        if id_linha is None:
            messagebox.showwarning(
                "Nenhum bloqueio selecionado",
                "Selecione uma linha bloqueada."
            )
            return

        linha = self.state.pegar_linha_por_id(id_linha)

        if linha is None:
            return

        pedido = str(linha["Pedido"])
        item = str(linha["Item"])

        if pedido in self.state.pedidos_bloqueados:
            confirmar = messagebox.askyesno(
                "Liberar pedido",
                f"Deseja liberar o pedido {pedido} inteiro?"
            )

            if confirmar:
                self.state.liberar_pedido(pedido)

        elif self.state.cliente_bloqueado_da_linha(linha):
            cliente = self.state.cliente_bloqueado_da_linha(linha)
            nome_curto = CLIENTES_BLOQUEIO_PADRAO.get(cliente, cliente)

            confirmar = messagebox.askyesno(
                "Liberar cliente",
                f"Deseja liberar todos os pedidos bloqueados pelo cliente?\n\n{nome_curto}"
            )

            if confirmar:
                self.state.liberar_cliente(cliente)

        elif self.state.pedido_bloqueado_por_observacao(pedido):
            observacao = self.state.observacao_bloqueada_do_pedido(pedido)

            confirmar = messagebox.askyesno(
                "Liberar observação",
                f"Deseja liberar todos os pedidos bloqueados por esta observação?\n\n{observacao}"
            )

            if confirmar:
                self.state.liberar_observacao(observacao)

        elif item in self.state.codigos_itens_bloqueados:
            confirmar = messagebox.askyesno(
                "Liberar item global",
                f"Deseja liberar o item {item} na carteira inteira?"
            )

            if confirmar:
                self.state.liberar_item_global(item)

        else:
            self.state.liberar_linha(id_linha)

        self.refresh_all()
        self.set_status("Bloqueio removido.")

    def limpar_todos_bloqueios(self):
        existe_bloqueio = (
            self.state.linhas_bloqueadas
            or self.state.codigos_itens_bloqueados
            or self.state.pedidos_bloqueados
            or self.state.observacoes_bloqueadas
            or self.state.clientes_bloqueados
        )

        if not existe_bloqueio:
            return

        confirmar = messagebox.askyesno(
            "Limpar bloqueios",
            "Deseja remover todos os bloqueios de itens, códigos, pedidos, observações e clientes?"
        )

        if not confirmar:
            return

        self.state.limpar_bloqueios()
        self.refresh_all()
        self.set_status("Todos os bloqueios foram removidos.")

    def exportar_excel(self):
        if not self.state.tem_dados():
            messagebox.showwarning(
                "Nenhum arquivo importado",
                "Importe um CSV antes de exportar."
            )
            return

        caminho = filedialog.asksaveasfilename(
            title="Salvar relatório Excel",
            defaultextension=".xlsx",
            filetypes=[("Arquivo Excel", "*.xlsx")]
        )

        if not caminho:
            return

        try:
            exportar_excel_completo(caminho, self.state)

            messagebox.showinfo(
                "Exportação concluída",
                f"Relatório exportado com sucesso:\n{caminho}"
            )

            self.set_status(f"Excel exportado: {caminho}")

        except Exception as erro:
            messagebox.showerror(
                "Erro ao exportar Excel",
                str(erro)
            )

    def exportar_csv_atual(self):
        if not self.state.tem_dados():
            messagebox.showwarning(
                "Nenhum arquivo importado",
                "Importe um CSV antes de exportar."
            )
            return

        aba_atual = self.abas.tab(self.abas.select(), "text")

        if aba_atual == "Pedidos":
            df_exportar = self.state.gerar_df_pedidos_ajustados()
        elif aba_atual == "PROG 2":
            df_exportar = self.state.gerar_df_prog2()
        elif aba_atual == "Liberados":
            df_exportar = self.state.gerar_df_pedidos_liberados()
        elif aba_atual == "Bloqueios":
            df_exportar = self.state.gerar_df_bloqueios()
        else:
            df_exportar = self.consolidacoes_tab.get_current_df()

        if df_exportar is None:
            messagebox.showwarning(
                "Nenhuma visualização",
                "Nenhum dado disponível para exportar."
            )
            return

        caminho = filedialog.asksaveasfilename(
            title="Salvar CSV atual",
            defaultextension=".csv",
            filetypes=[("Arquivo CSV", "*.csv")]
        )

        if not caminho:
            return

        try:
            exportar_csv(caminho, df_exportar)

            messagebox.showinfo(
                "Exportação concluída",
                f"CSV exportado com sucesso:\n{caminho}"
            )

            self.set_status(f"CSV exportado: {caminho}")

        except Exception as erro:
            messagebox.showerror(
                "Erro ao exportar CSV",
                str(erro)
            )