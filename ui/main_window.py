import os
import subprocess
import tempfile
import traceback
import webbrowser
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog


from core.app_state import AppState, CLIENTES_BLOQUEIO_PADRAO
from core.config_manager import ConfigManager
from core.exporter import (
    exportar_csv,
    exportar_excel_completo,
    exportar_dataframe_excel,
    exportar_dataframe_pdf,
)
from core.formatters import formatar_moeda, formatar_numero
from ui.styles import CORES, configurar_estilo
from ui.pedidos_tab import PedidosTab
from ui.prog2_tab import Prog2Tab
from ui.faturados_tab import FaturadosTab
from ui.atrasados_tab import AtrasadosTab
from ui.bloqueios_tab import BloqueiosTab
from ui.consolidacoes_tab import ConsolidacoesTab
from ui.gargalos_tab import GargalosTab
from ui.sortable_tree import aplicar_ordenacao_treeview
from services.cache_service import CarteiraCacheService
from services.estado_service import EstadoService
from services.exportacao_service import ExportacaoService
from services.faturamento_service import FaturamentoService
from services.importacao_service import ImportacaoService


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Carteira Manager")
        self.root.geometry("1500x860")
        self.root.minsize(1180, 700)

        configurar_estilo()
        try:
            self.root.configure(background=CORES["bg"])
        except Exception:
            pass

        self.state = AppState()
        self.labels_resumo = {}

        self.cache_service = CarteiraCacheService(self.state)
        self.estado_service = EstadoService()
        self.exportacao_service = ExportacaoService()
        self.faturamento_service = FaturamentoService(self.state)
        self.importacao_service = ImportacaoService(self.state)

        self.config_manager = ConfigManager()
        self.config = self.config_manager.carregar()

        self.ultimo_arquivo_importado = self.config.get("ultimo_csv", "")
        self.observacoes_internas = self.config.setdefault("observacoes_internas", {})

        self.garantir_preset_padrao_clientes()

        self.log_dir = Path.home() / ".carteira_ops" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.log_dir / "app.log"

        self.criar_interface()

    def criar_interface(self):
        self.criar_topo()
        self.criar_resumo()
        self.criar_abas()
        self.criar_barra_status()
        self.registrar_atalhos()

    def registrar_atalhos(self):
        self.root.bind_all("<Control-f>", self.atalho_buscar)
        self.root.bind_all("<Control-F>", self.atalho_buscar)
        self.root.bind_all("<Control-e>", self.atalho_exportar)
        self.root.bind_all("<Control-E>", self.atalho_exportar)
        self.root.bind_all("<Control-r>", self.atalho_recarregar)
        self.root.bind_all("<Control-R>", self.atalho_recarregar)
        self.root.bind_all("<Delete>", self.atalho_delete)
        self.root.bind_all("<Return>", self.atalho_enter)

    def obter_aba_ativa(self):
        if not hasattr(self, "abas"):
            return None, None

        texto = self.abas.tab(self.abas.select(), "text")
        mapa = {
            "Pedidos": getattr(self, "pedidos_tab", None),
            "PROG 2": getattr(self, "prog2_tab", None),
            "Faturados": getattr(self, "faturados_tab", None),
            "Atrasados": getattr(self, "atrasados_tab", None),
            "Bloqueios": getattr(self, "bloqueios_tab", None),
            "Gargalos": getattr(self, "gargalos_tab", None),
            "Consolidações": getattr(self, "consolidacoes_tab", None),
        }
        return texto, mapa.get(texto)

    def atalho_buscar(self, event=None):
        _, aba = self.obter_aba_ativa()
        if aba and hasattr(aba, "focar_busca"):
            aba.focar_busca()
            return "break"

        entrada = getattr(aba, "entrada_busca", None) if aba else None
        if entrada is not None:
            entrada.focus_set()
            entrada.selection_range(0, "end")
            return "break"
        return None

    def atalho_exportar(self, event=None):
        self.exportar_csv_atual()
        return "break"

    def atalho_recarregar(self, event=None):
        if self.ultimo_arquivo_importado:
            self.recarregar_ultimo_csv()
        else:
            self.refresh_all()
            self.set_status("Tela atualizada.")
        return "break"

    def atalho_delete(self, event=None):
        nome_aba, aba = self.obter_aba_ativa()
        if nome_aba == "PROG 2":
            self.remover_pedido_selecionado_prog2()
            return "break"
        if nome_aba == "Bloqueios":
            self.liberar_bloqueio_na_aba()
            return "break"
        if nome_aba == "Faturados" and hasattr(aba, "remover_selecionado"):
            aba.remover_selecionado()
            return "break"
        return None

    def atalho_enter(self, event=None):
        _, aba = self.obter_aba_ativa()
        widget_focado = self.root.focus_get()
        if isinstance(widget_focado, (tk.Entry, ttk.Entry, ttk.Combobox)):
            return None
        if aba and hasattr(aba, "abrir_detalhes_selecionado"):
            aba.abrir_detalhes_selecionado()
            return "break"
        return None

    def criar_topo(self):
        frame = ttk.Frame(self.root, padding=(12, 8), style="TopBar.TFrame")
        frame.pack(fill="x")

        bloco_titulo = ttk.Frame(frame, style="TopBar.TFrame")
        bloco_titulo.pack(side="left", fill="x", expand=True)

        ttk.Label(
            bloco_titulo,
            text="Carteira Manager",
            style="TopBarTitle.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            bloco_titulo,
            text="Carteira, bloqueios, PROG 2, faturamento e gargalos em uma visão única.",
            style="TopBarSubtitle.TLabel",
        ).pack(anchor="w", pady=(1, 0))

        bloco_menus = ttk.Frame(frame, style="TopBar.TFrame")
        bloco_menus.pack(side="right", padx=(12, 0))

        self.criar_menu_arquivo(bloco_menus)
        self.criar_menu_presets(bloco_menus)
        self.criar_menu_exportacao(bloco_menus)
        self.criar_menu_suporte(bloco_menus)

    def criar_menu_popup(self, parent):
        menu = tk.Menu(
            parent,
            tearoff=0,
            font=("Segoe UI", 9),
            background=CORES["card"],
            foreground=CORES["text"],
            activebackground=CORES["primary_soft"],
            activeforeground=CORES["text"],
            relief="solid",
            borderwidth=1,
        )
        return menu

    def criar_menu_arquivo(self, parent):
        botao = ttk.Menubutton(parent, text="Arquivo  ▾", style="TopMenu.TMenubutton")
        menu = self.criar_menu_popup(botao)

        menu.add_command(label="Importar CSV", command=self.importar_csv)
        menu.add_command(label="Recarregar último CSV", command=self.recarregar_ultimo_csv)
        menu.add_separator()
        menu.add_command(label="Salvar estado agora", command=self.salvar_estado_manual)
        menu.add_separator()
        menu.add_command(label="Sair", command=self.root.destroy)

        botao["menu"] = menu
        botao.pack(side="left", padx=(6, 0), ipady=1)

    def criar_menu_presets(self, parent):
        botao = ttk.Menubutton(parent, text="Presets  ▾", style="TopMenu.TMenubutton")
        menu = self.criar_menu_popup(botao)

        menu.add_command(
            label="Criar preset com itens bloqueados atuais",
            command=self.criar_preset_itens
        )
        menu.add_command(
            label="Aplicar preset de itens",
            command=lambda: self.abrir_janela_presets("itens")
        )

        menu.add_separator()

        menu.add_command(
            label="Criar preset com clientes bloqueados atuais",
            command=self.criar_preset_clientes
        )
        menu.add_command(
            label="Aplicar preset de clientes",
            command=lambda: self.abrir_janela_presets("clientes")
        )

        botao["menu"] = menu
        botao.pack(side="left", padx=(6, 0), ipady=1)

    def criar_menu_exportacao(self, parent):
        botao = ttk.Menubutton(parent, text="Exportar  ▾", style="TopMenu.TMenubutton")
        menu = self.criar_menu_popup(botao)

        menu.add_command(label="Relatório completo em Excel", command=self.exportar_excel)
        menu.add_command(label="Aba atual em CSV", command=self.exportar_csv_atual)

        botao["menu"] = menu
        botao.pack(side="left", padx=(6, 0), ipady=1)

    def criar_menu_suporte(self, parent):
        botao = ttk.Menubutton(parent, text="Ajuda  ▾", style="TopMenu.TMenubutton")
        menu = self.criar_menu_popup(botao)

        menu.add_command(label="Abrir arquivo de log", command=self.abrir_log)
        menu.add_command(label="Sobre", command=self.mostrar_sobre)

        botao["menu"] = menu
        botao.pack(side="left", padx=(6, 0), ipady=1)

    def criar_resumo(self):
        frame = ttk.LabelFrame(
            self.root,
            text="Resumo geral",
            padding=(6, 4),
            style="Kpi.TLabelframe"
        )
        frame.pack(fill="x", padx=8, pady=(4, 4))

        campos = [
            ("Pedidos Abertos", "Abertos"),
            ("Pedidos Bloqueados", "Bloqueados"),
            ("Clientes Bloq.", "Clientes bloq."),
            ("Pedidos PROG 2", "PROG 2"),
            ("Valor Carteira", "Carteira"),
            ("Valor Bloqueado", "Valor bloq."),
            ("Valor Liberado", "Valor lib."),
            ("Valor liberado PROG 2", "PROG 2 lib."),
        ]

        for indice, (campo, titulo) in enumerate(campos):
            bloco = ttk.Frame(frame, padding=(6, 4), style="KpiCard.TFrame")
            bloco.grid(row=0, column=indice, sticky="nsew", padx=2, pady=2)

            ttk.Label(
                bloco,
                text=titulo,
                style="KpiTitle.TLabel"
            ).pack(anchor="w")

            label_valor = ttk.Label(
                bloco,
                text="-",
                style="KpiValue.TLabel"
            )
            label_valor.pack(anchor="w", pady=(1, 0))

            self.labels_resumo[campo] = label_valor

        for indice in range(len(campos)):
            frame.columnconfigure(indice, weight=1)

    def criar_abas(self):
        self.abas = ttk.Notebook(self.root)
        self.abas.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        aba_pedidos = ttk.Frame(self.abas)
        aba_prog2 = ttk.Frame(self.abas)
        aba_faturados = ttk.Frame(self.abas)
        aba_atrasados = ttk.Frame(self.abas)
        aba_bloqueios = ttk.Frame(self.abas)
        aba_gargalos = ttk.Frame(self.abas)
        aba_consolidacoes = ttk.Frame(self.abas)

        self.abas.add(aba_pedidos, text="Pedidos")
        self.abas.add(aba_prog2, text="PROG 2")
        self.abas.add(aba_faturados, text="Faturados")
        self.abas.add(aba_atrasados, text="Atrasados")
        self.abas.add(aba_bloqueios, text="Bloqueios")
        self.abas.add(aba_gargalos, text="Gargalos")
        self.abas.add(aba_consolidacoes, text="Consolidações")

        self.pedidos_tab = PedidosTab(aba_pedidos, self, self.state)
        self.prog2_tab = Prog2Tab(aba_prog2, self, self.state)
        self.faturados_tab = FaturadosTab(aba_faturados, self, self.state)
        self.atrasados_tab = AtrasadosTab(aba_atrasados, self, self.state)
        self.bloqueios_tab = BloqueiosTab(aba_bloqueios, self, self.state)
        self.gargalos_tab = GargalosTab(aba_gargalos, self, self.state)
        self.consolidacoes_tab = ConsolidacoesTab(aba_consolidacoes, self, self.state)

        self.aplicar_ordenacao_tabelas()

    def aplicar_ordenacao_tabelas(self):
        abas = [
            getattr(self, "pedidos_tab", None),
            getattr(self, "prog2_tab", None),
            getattr(self, "faturados_tab", None),
            getattr(self, "atrasados_tab", None),
            getattr(self, "bloqueios_tab", None),
            getattr(self, "gargalos_tab", None),
            getattr(self, "consolidacoes_tab", None),
        ]

        for aba in abas:
            tabela = getattr(aba, "tabela", None)

            if tabela is not None:
                try:
                    aplicar_ordenacao_treeview(tabela)
                except Exception:
                    pass

    def criar_barra_status(self):
        texto = "Importe um arquivo CSV para começar."

        if self.ultimo_arquivo_importado:
            texto = f"Último CSV salvo: {self.ultimo_arquivo_importado}"

        self.status = ttk.Label(
            self.root,
            text=texto,
            relief="flat",
            anchor="w",
            padding=(10, 5),
            style="Hint.TLabel"
        )
        self.status.pack(fill="x", side="bottom")

    def set_status(self, texto):
        self.status.config(text=texto)

    def invalidar_cache(self):
        self.cache_service.invalidar()

    def obter_df_aberto_cache(self):
        return self.cache_service.obter_df_aberto()

    def obter_df_com_bloqueios_cache(self):
        return self.cache_service.obter_df_com_bloqueios()

    def garantir_preset_padrao_clientes(self):
        presets_clientes = self.config.setdefault("presets", {}).setdefault("clientes", {})

        if "CLIENTES BLOQUEADOS 1" not in presets_clientes:
            presets_clientes["CLIENTES BLOQUEADOS 1"] = sorted(CLIENTES_BLOQUEIO_PADRAO.keys())
            self.config_manager.salvar(self.config)

    def gerar_estado_para_salvar(self):
        return self.estado_service.gerar_estado_para_salvar(self.state)

    def salvar_estado_atual(self):
        self.config["ultimo_csv"] = self.ultimo_arquivo_importado or ""
        self.config["estado"] = self.gerar_estado_para_salvar()
        self.config["observacoes_internas"] = self.observacoes_internas
        self.config_manager.salvar(self.config)

    def salvar_estado_manual(self):
        self.salvar_estado_atual()

        messagebox.showinfo(
            "Estado salvo",
            f"Estado salvo localmente em:\n{self.config_manager.config_path}"
        )

        self.set_status("Estado salvo localmente.")

    def restaurar_estado_salvo(self):
        self.observacoes_internas = self.config.setdefault("observacoes_internas", {})
        self.observacoes_internas = self.estado_service.restaurar_estado_salvo(
            self.state,
            self.config,
            self.observacoes_internas,
        )

    def observacao_interna_pedido(self, pedido):
        return self.observacoes_internas.get(str(pedido), "")

    def editar_observacao_interna(self, pedido):
        pedido = str(pedido)
        atual = self.observacoes_internas.get(pedido, "")

        texto = simpledialog.askstring(
            "Observação interna",
            f"Observação interna do pedido {pedido}:",
            initialvalue=atual,
            parent=self.root
        )

        if texto is None:
            return

        texto = texto.strip()

        if texto:
            self.observacoes_internas[pedido] = texto
        else:
            self.observacoes_internas.pop(pedido, None)

        self.salvar_estado_atual()
        self.refresh_all()
        self.set_status(f"Observação interna atualizada para o pedido {pedido}.")

    def limpar_observacao_interna(self, pedido):
        pedido = str(pedido)

        if pedido in self.observacoes_internas:
            self.observacoes_internas.pop(pedido, None)
            self.salvar_estado_atual()
            self.refresh_all()
            self.set_status(f"Observação interna removida do pedido {pedido}.")
        else:
            self.set_status(f"O pedido {pedido} não possui observação interna.")

    def obter_linha_por_id(self, id_linha):
        try:
            id_linha = int(id_linha)
        except (TypeError, ValueError):
            return None

        if not self.state.tem_dados():
            return None

        linha = self.state.df_original[self.state.df_original["ID Linha"] == id_linha]
        if linha.empty:
            return None

        return linha.iloc[0]

    def definir_pendencia_prog2_item(self, id_linha, motivo):
        linha = self.obter_linha_por_id(id_linha)
        motivo = str(motivo).strip()

        if linha is None:
            self.set_status("Item inválido para aplicar pendência.")
            return

        if not motivo:
            self.set_status("Motivo de pendência inválido.")
            return

        pedido = str(linha["Pedido Texto"])
        if pedido not in self.state.pedidos_prog2:
            self.set_status(f"Pedido {pedido} não está no PROG 2.")
            return

        if not self.state.definir_pendencia_item_prog2(id_linha, motivo):
            self.set_status("Não foi possível aplicar a pendência no item.")
            return

        self.invalidar_cache()
        self.refresh_all()
        self.salvar_estado_atual()
        self.set_status(f"Pendência '{motivo}' aplicada ao item {linha['Item']} do pedido {pedido}.")

    def limpar_pendencia_prog2_item(self, id_linha):
        linha = self.obter_linha_por_id(id_linha)
        if linha is None:
            self.set_status("Item inválido para limpar pendência.")
            return

        pedido = str(linha["Pedido Texto"])
        if self.state.limpar_pendencia_item_prog2(id_linha):
            self.invalidar_cache()
            self.refresh_all()
            self.salvar_estado_atual()
            self.set_status(f"Pendência removida do item {linha['Item']} do pedido {pedido}.")
            return

        self.set_status(f"O item {linha['Item']} do pedido {pedido} não possui pendência.")

    def definir_pendencia_prog2(self, pedido, motivo):
        self.set_status("Pendências agora são aplicadas por item. Clique com o botão direito em um item do PROG 2.")

    def limpar_pendencia_prog2(self, pedido):
        self.set_status("Pendências agora são removidas por item. Clique com o botão direito em um item do PROG 2.")

    def registrar_erro(self, contexto, erro):
        data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        with open(self.log_path, "a", encoding="utf-8") as arquivo:
            arquivo.write("\n" + "=" * 80 + "\n")
            arquivo.write(f"{data} | {contexto}\n")
            arquivo.write("-" * 80 + "\n")
            arquivo.write(str(erro) + "\n")
            arquivo.write(traceback.format_exc())
            arquivo.write("\n")

    def abrir_log(self):
        if not self.log_path.exists():
            self.log_path.write_text("Nenhum erro registrado até o momento.\n", encoding="utf-8")

        self.abrir_arquivo(str(self.log_path))

    def mostrar_sobre(self):
        messagebox.showinfo(
            "Sobre",
            "Carteira Manager\n\n"
            "Aplicativo desktop para consolidação, bloqueio e programação de carteira de pedidos.\n\n"
            f"Log local:\n{self.log_path}"
        )

    def abrir_arquivo(self, caminho):
        try:
            if os.name == "nt":
                os.startfile(caminho)
            else:
                subprocess.Popen(["xdg-open", caminho])
        except Exception:
            caminho_url = os.path.abspath(caminho).replace(os.sep, "/")
            webbrowser.open(f"file:///{caminho_url}")

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

        self.carregar_arquivo_csv(caminho)

    def recarregar_ultimo_csv(self):
        if not self.ultimo_arquivo_importado:
            messagebox.showwarning(
                "Nenhum arquivo anterior",
                "Ainda não existe um CSV salvo no estado local."
            )
            return

        if not os.path.exists(self.ultimo_arquivo_importado):
            messagebox.showerror(
                "Arquivo não encontrado",
                f"O último arquivo importado não existe mais:\n{self.ultimo_arquivo_importado}"
            )
            return

        self.carregar_arquivo_csv(self.ultimo_arquivo_importado)

    def carregar_arquivo_csv(self, caminho):
        try:
            self.set_status("Importando e validando arquivo...")
            self.root.update_idletasks()

            df = self.importacao_service.carregar_csv(caminho)
            self.ultimo_arquivo_importado = caminho

            self.invalidar_cache()
            self.restaurar_estado_salvo()
            self.invalidar_cache()
            self.refresh_all()
            self.salvar_estado_atual()

            self.set_status(
                f"Arquivo importado com sucesso: {caminho} | "
                f"Linhas: {len(df)} | "
                f"Pedidos: {df['Pedido'].nunique()} | "
                f"Estado local restaurado."
            )

        except Exception as erro:
            self.registrar_erro("Erro ao importar CSV", erro)

            messagebox.showerror(
                "Erro ao importar arquivo",
                str(erro)
            )

            self.set_status("Erro ao importar arquivo. Veja o log em Suporte > Abrir arquivo de log.")

    def refresh_all(self):
        self.atualizar_resumo()
        self.pedidos_tab.refresh()
        self.prog2_tab.refresh()
        self.faturados_tab.refresh()
        self.atrasados_tab.refresh()
        self.bloqueios_tab.refresh()
        self.gargalos_tab.refresh()
        self.consolidacoes_tab.refresh()
        self.aplicar_ordenacao_tabelas()

    def refresh_pedidos(self):
        self.pedidos_tab.refresh()
        self.prog2_tab.refresh()
        self.faturados_tab.refresh()
        self.atrasados_tab.refresh()
        self.gargalos_tab.refresh()
        self.atualizar_resumo()
        self.aplicar_ordenacao_tabelas()

    def atualizar_resumo(self):
        if not self.state.tem_dados():
            return

        df_aberto = self.obter_df_aberto_cache()
        df_bloqueios = self.obter_df_com_bloqueios_cache()

        valor_total = df_bloqueios["Valor em Carteira"].sum() if not df_bloqueios.empty else 0
        valor_bloqueado = df_bloqueios["_Valor Bloqueado"].sum() if not df_bloqueios.empty else 0
        valor_liberado = df_bloqueios["_Valor Liberado"].sum() if not df_bloqueios.empty else 0
        totais_prog2 = self.state.calcular_totais_prog2(df_bloqueios)

        pedidos_bloqueados_total = set(self.state.pedidos_bloqueados)
        pedidos_bloqueados_total.update(self.state.pedidos_bloqueados_por_observacao_set())
        pedidos_bloqueados_total.update(self.state.pedidos_bloqueados_por_cliente_set())

        valores = {
            "Pedidos Abertos": df_aberto["Pedido"].nunique(),
            "Pedidos Bloqueados": len(pedidos_bloqueados_total),
            "Clientes Bloq.": len(self.state.clientes_bloqueados),
            "Pedidos PROG 2": totais_prog2["pedidos"],
            "Valor Carteira": formatar_moeda(valor_total),
            "Valor Bloqueado": formatar_moeda(valor_bloqueado),
            "Valor Liberado": formatar_moeda(valor_liberado),
            "Valor liberado PROG 2": formatar_moeda(totais_prog2["valor_liberado"]),
        }

        estilos = {
            "Pedidos Bloqueados": "KpiDanger.TLabel" if len(pedidos_bloqueados_total) > 0 else "KpiValue.TLabel",
            "Clientes Bloq.": "KpiDanger.TLabel" if len(self.state.clientes_bloqueados) > 0 else "KpiValue.TLabel",
            "Valor Bloqueado": "KpiDanger.TLabel" if valor_bloqueado > 0 else "KpiValue.TLabel",
            "Valor Liberado": "KpiPositive.TLabel" if valor_liberado > 0 else "KpiValue.TLabel",
            "Valor liberado PROG 2": "KpiPositive.TLabel" if totais_prog2["valor_liberado"] > 0 else "KpiValue.TLabel",
        }

        for campo, label in self.labels_resumo.items():
            label.config(
                text=str(valores.get(campo, "-")),
                style=estilos.get(campo, "KpiValue.TLabel")
            )

    def obter_presets(self, tipo):
        return self.config.setdefault("presets", {}).setdefault(tipo, {})

    def pedir_nome_preset(self, titulo):
        nome = simpledialog.askstring(
            titulo,
            "Digite o nome do preset:",
            parent=self.root
        )

        if not nome:
            return None

        nome = nome.strip()

        if not nome:
            return None

        return nome

    def criar_preset_itens(self):
        if not self.state.codigos_itens_bloqueados:
            messagebox.showwarning(
                "Nenhum item bloqueado",
                "Bloqueie os itens desejados antes de criar um preset."
            )
            return

        nome = self.pedir_nome_preset("Criar preset de itens")

        if not nome:
            return

        presets = self.obter_presets("itens")
        presets[nome] = sorted(str(item) for item in self.state.codigos_itens_bloqueados)

        self.config_manager.salvar(self.config)

        messagebox.showinfo(
            "Preset salvo",
            f"Preset de itens salvo:\n{nome}"
        )

        self.set_status(f"Preset de itens salvo: {nome}")

    def criar_preset_clientes(self):
        if not self.state.clientes_bloqueados:
            messagebox.showwarning(
                "Nenhum cliente bloqueado",
                "Bloqueie os clientes desejados antes de criar um preset."
            )
            return

        nome = self.pedir_nome_preset("Criar preset de clientes")

        if not nome:
            return

        presets = self.obter_presets("clientes")
        presets[nome] = sorted(str(item) for item in self.state.clientes_bloqueados)

        self.config_manager.salvar(self.config)

        messagebox.showinfo(
            "Preset salvo",
            f"Preset de clientes salvo:\n{nome}"
        )

        self.set_status(f"Preset de clientes salvo: {nome}")

    def abrir_janela_presets(self, tipo):
        presets = self.obter_presets(tipo)

        if not presets:
            messagebox.showwarning(
                "Nenhum preset salvo",
                f"Não existe preset de {tipo} salvo."
            )
            return

        janela = tk.Toplevel(self.root)
        janela.title(f"Presets de {tipo}")
        janela.geometry("760x460")
        janela.minsize(620, 380)
        janela.transient(self.root)
        janela.grab_set()

        frame = ttk.Frame(janela, padding=10)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text=f"Presets de {tipo}",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w")

        ttk.Label(
            frame,
            text="Selecione um preset para aplicar ou excluir.",
            style="Subtitle.TLabel"
        ).pack(anchor="w", pady=(2, 8))

        corpo = ttk.Frame(frame)
        corpo.pack(fill="both", expand=True)

        lista = tk.Listbox(corpo, height=12)
        lista.pack(side="left", fill="both", expand=False, padx=(0, 8))

        preview = tk.Text(corpo, height=12, wrap="word")
        preview.pack(side="left", fill="both", expand=True)

        nomes = sorted(presets.keys())

        for nome in nomes:
            lista.insert("end", nome)

        def preset_selecionado():
            selecao = lista.curselection()

            if not selecao:
                return None

            return lista.get(selecao[0])

        def atualizar_preview(event=None):
            nome = preset_selecionado()

            preview.delete("1.0", "end")

            if not nome:
                return

            valores = presets.get(nome, [])

            linhas = [
                f"Preset: {nome}",
                f"Tipo: {tipo}",
                f"Quantidade: {len(valores)}",
                "",
                "Itens/clientes salvos:",
                "",
            ]

            for valor in valores:
                if tipo == "clientes":
                    linhas.append(f"- {self.state.abreviar_cliente(valor)} | {valor}")
                else:
                    linhas.append(f"- {valor}")

            preview.insert("1.0", "\n".join(linhas))

        def aplicar_preset():
            if not self.state.tem_dados():
                messagebox.showwarning(
                    "Nenhum CSV importado",
                    "Importe a carteira antes de aplicar um preset."
                )
                return

            nome = preset_selecionado()

            if not nome:
                messagebox.showwarning(
                    "Nenhum preset selecionado",
                    "Selecione um preset."
                )
                return

            valores = presets.get(nome, [])

            if tipo == "itens":
                self.state.bloquear_itens_globais(valores, "")
            else:
                self.state.bloquear_clientes(valores, "")

            self.invalidar_cache()
            self.refresh_all()
            self.salvar_estado_atual()

            self.set_status(f"Preset aplicado: {nome}")
            janela.destroy()

        def excluir_preset():
            nome = preset_selecionado()

            if not nome:
                messagebox.showwarning(
                    "Nenhum preset selecionado",
                    "Selecione um preset."
                )
                return

            confirmar = messagebox.askyesno(
                "Excluir preset",
                f"Deseja excluir o preset?\n\n{nome}"
            )

            if not confirmar:
                return

            presets.pop(nome, None)
            self.config_manager.salvar(self.config)

            lista.delete(0, "end")

            for nome_preset in sorted(presets.keys()):
                lista.insert("end", nome_preset)

            preview.delete("1.0", "end")
            self.set_status(f"Preset excluído: {nome}")

        lista.bind("<<ListboxSelect>>", atualizar_preview)

        frame_botoes = ttk.Frame(frame)
        frame_botoes.pack(fill="x", pady=(10, 0))

        ttk.Button(
            frame_botoes,
            text="Aplicar preset",
            command=aplicar_preset,
            style="Primary.TButton"
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            frame_botoes,
            text="Excluir preset",
            command=excluir_preset,
            style="Danger.TButton"
        ).pack(side="left", padx=5)

        ttk.Button(
            frame_botoes,
            text="Fechar",
            command=janela.destroy
        ).pack(side="right")

        if nomes:
            lista.selection_set(0)
            atualizar_preview()

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
        janela.geometry("980x620")
        janela.minsize(780, 460)
        janela.transient(self.root)
        janela.grab_set()

        busca_var = tk.StringVar()

        variaveis = {
            registro[chave_coluna]: tk.BooleanVar(
                value=registro[chave_coluna] in selecionados_atuais
            )
            for registro in registros
        }

        frame_topo = ttk.Frame(janela, padding=(10, 8))
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
        ).pack(anchor="w", pady=(2, 0))

        frame_pesquisa = ttk.Frame(janela, padding=(10, 0, 10, 6))
        frame_pesquisa.pack(fill="x")

        ttk.Label(frame_pesquisa, text="Pesquisar:").pack(side="left", padx=(0, 5))

        entrada_busca = ttk.Entry(
            frame_pesquisa,
            textvariable=busca_var,
            width=55
        )
        entrada_busca.pack(side="left", padx=(0, 10))

        frame_preset = ttk.Frame(janela, padding=(10, 0, 10, 4))
        frame_preset.pack(fill="x")

        if preset:
            preset_nome = preset["nome"]
            preset_chaves = set(preset["chaves"])
            preset_chaves_presentes = [
                chave for chave in preset_chaves
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

                    self.invalidar_cache()
                    self.refresh_all()
                    self.salvar_estado_atual()
                    self.set_status(f"{preset_nome} aplicado.")
                else:
                    ao_liberar(preset_chaves_presentes)

                    for chave in preset_chaves_presentes:
                        variaveis[chave].set(False)

                    self.invalidar_cache()
                    self.refresh_all()
                    self.salvar_estado_atual()
                    self.set_status(f"{preset_nome} removido.")

            ttk.Checkbutton(
                frame_preset,
                text=preset_nome,
                variable=preset_var,
                command=alternar_preset
            ).pack(anchor="w")

        frame_acoes = ttk.Frame(janela, padding=(10, 0, 10, 6))
        frame_acoes.pack(fill="x")

        frame_lista = ttk.Frame(janela, padding=(10, 0, 10, 8))
        frame_lista.pack(fill="both", expand=True)

        canvas = tk.Canvas(
            frame_lista,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground="#cfd4da",
            background="#f4f6f8",
        )

        scroll_y = ttk.Scrollbar(
            frame_lista,
            orient="vertical",
            command=canvas.yview
        )

        frame_checks = ttk.Frame(canvas)
        canvas_window = canvas.create_window(
            (0, 0),
            window=frame_checks,
            anchor="nw"
        )

        def atualizar_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def ajustar_largura_canvas(event):
            canvas.itemconfigure(canvas_window, width=event.width)

        frame_checks.bind("<Configure>", atualizar_scroll_region)
        canvas.bind("<Configure>", ajustar_largura_canvas)

        canvas.configure(yscrollcommand=scroll_y.set)

        canvas.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")

        frame_lista.rowconfigure(0, weight=1)
        frame_lista.columnconfigure(0, weight=1)
        frame_checks.columnconfigure(0, weight=1)

        def rolar_mouse(event):
            if getattr(event, "num", None) == 4:
                canvas.yview_scroll(-3, "units")
            elif getattr(event, "num", None) == 5:
                canvas.yview_scroll(3, "units")
            else:
                delta = int(-1 * (event.delta / 120))
                canvas.yview_scroll(delta, "units")

            return "break"

        def ativar_scroll_mouse(event=None):
            canvas.bind_all("<MouseWheel>", rolar_mouse)
            canvas.bind_all("<Button-4>", rolar_mouse)
            canvas.bind_all("<Button-5>", rolar_mouse)

        def desativar_scroll_mouse(event=None):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        canvas.bind("<Enter>", ativar_scroll_mouse)
        canvas.bind("<Leave>", desativar_scroll_mouse)
        frame_checks.bind("<Enter>", ativar_scroll_mouse)
        frame_checks.bind("<Leave>", desativar_scroll_mouse)
        janela.bind("<Destroy>", lambda event: desativar_scroll_mouse() if event.widget == janela else None)

        registros_visiveis = []

        def obter_filtrados():
            termo = busca_var.get().strip().lower()

            if not termo:
                return registros

            return [
                registro for registro in registros
                if termo in texto_busca_funcao(registro).lower()
            ]

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
                ).grid(row=0, column=0, sticky="w", padx=6, pady=6)

                frame_checks.update_idletasks()
                atualizar_scroll_region()
                canvas.yview_moveto(0)
                return

            for indice, registro in enumerate(registros_visiveis):
                chave = registro[chave_coluna]

                check = ttk.Checkbutton(
                    frame_checks,
                    text=texto_funcao(registro),
                    variable=variaveis[chave]
                )
                check.grid(
                    row=indice,
                    column=0,
                    sticky="ew",
                    padx=6,
                    pady=2
                )

                check.bind("<Enter>", ativar_scroll_mouse)

            frame_checks.update_idletasks()
            atualizar_scroll_region()
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

        frame_botoes = ttk.Frame(janela, padding=(10, 8))
        frame_botoes.pack(fill="x")

        def confirmar_bloqueio():
            selecionados = [
                chave for chave, var in variaveis.items()
                if var.get()
            ]

            if not selecionados:
                messagebox.showwarning(
                    "Nenhum item selecionado",
                    "Selecione pelo menos uma opção."
                )
                return

            ao_bloquear(selecionados)
            self.invalidar_cache()
            self.refresh_all()
            self.salvar_estado_atual()
            janela.destroy()
            self.set_status("Bloqueios atualizados.")

        def confirmar_liberacao():
            selecionados = [
                chave for chave, var in variaveis.items()
                if var.get()
            ]

            if not selecionados:
                messagebox.showwarning(
                    "Nenhum item selecionado",
                    "Selecione pelo menos uma opção."
                )
                return

            ao_liberar(selecionados)
            self.invalidar_cache()
            self.refresh_all()
            self.salvar_estado_atual()
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
            messagebox.showwarning("Seleção inválida", "Selecione um item dentro de um pedido.")
            return

        self.state.bloquear_linha(id_linha, "")
        self.invalidar_cache()
        self.refresh_all()
        self.salvar_estado_atual()
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
        self.invalidar_cache()
        self.refresh_all()
        self.salvar_estado_atual()
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

        self.invalidar_cache()
        self.refresh_all()
        self.salvar_estado_atual()
        self.set_status(f"Item {codigo} bloqueado na carteira inteira.")

    def liberar_item_global(self):
        if not self.state.tem_dados():
            return

        codigo = self.pedidos_tab.get_codigo_item_global()

        if not codigo:
            messagebox.showwarning("Nenhum item informado", "Digite o código do item ou selecione um item.")
            return

        self.state.liberar_item_global(codigo)

        self.invalidar_cache()
        self.refresh_all()
        self.salvar_estado_atual()
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
        self.salvar_estado_atual()
        self.set_status(f"Pedido {pedido} adicionado ao PROG 2.")

    def adicionar_pedidos_selecionados_prog2(self, pedidos):
        if not self.state.tem_dados():
            return

        adicionados = 0

        for pedido in pedidos:
            antes = len(self.state.pedidos_prog2)
            self.state.adicionar_pedido_prog2(pedido)

            if len(self.state.pedidos_prog2) > antes:
                adicionados += 1

        self.refresh_all()
        self.salvar_estado_atual()
        self.set_status(f"{adicionados} pedido(s) adicionados ao PROG 2.")

    def remover_pedido_selecionado_prog2(self):
        pedido = self.prog2_tab.get_selected_pedido()

        if not pedido:
            messagebox.showwarning("Nenhum pedido selecionado", "Selecione um pedido ou item no PROG 2.")
            return

        self.state.remover_pedido_prog2(pedido)
        self.refresh_all()
        self.salvar_estado_atual()
        self.set_status(f"Pedido {pedido} removido do PROG 2.")

    def remover_pedidos_selecionados_prog2(self, pedidos):
        if not pedidos:
            return

        for pedido in pedidos:
            self.state.remover_pedido_prog2(pedido)

        self.refresh_all()
        self.salvar_estado_atual()
        self.set_status(f"{len(pedidos)} pedido(s) removidos do PROG 2.")

    def limpar_prog2(self):
        if not self.state.pedidos_prog2:
            return

        confirmar = messagebox.askyesno("Limpar PROG 2", "Deseja remover todos os pedidos do PROG 2?")

        if not confirmar:
            return

        self.state.limpar_prog2()
        self.refresh_all()
        self.salvar_estado_atual()
        self.set_status("PROG 2 limpo.")

    def fechar_faturamento_prog2(self):
        if not self.state.tem_dados():
            messagebox.showwarning("Nenhum arquivo", "Importe um CSV primeiro.")
            return

        pedidos_prog2 = [str(pedido) for pedido in self.state.pedidos_prog2]

        if not pedidos_prog2:
            messagebox.showwarning("PROG 2 vazio", "Não há pedidos no PROG 2 para fechar faturamento.")
            return

        df_prog2 = self.gerar_df_prog2_pedidos_liberados()
        valor_liberado = 0

        if df_prog2 is not None and not df_prog2.empty and "Valor Total Liberado" in df_prog2.columns:
            valor_liberado = df_prog2["Valor Total Liberado"].sum()

        confirmar = messagebox.askyesno(
            "Fechar faturamento",
            "Deseja marcar todos os pedidos do PROG 2 como faturados?\n\n"
            f"Pedidos: {len(pedidos_prog2)}\n"
            f"Valor liberado: {formatar_moeda(valor_liberado)}\n\n"
            "Após confirmar, eles sairão do PROG 2 e não aparecerão mais na carteira de pedidos nas próximas importações."
        )

        if not confirmar:
            return

        self.faturamento_service.fechar_prog2()
        self.invalidar_cache()
        self.refresh_all()
        self.salvar_estado_atual()

        self.set_status(f"Faturamento fechado: {len(pedidos_prog2)} pedido(s) marcados como faturados.")

    def remover_pedido_faturado(self, pedido):
        pedido = str(pedido)

        if pedido not in self.state.pedidos_faturados:
            self.set_status("Pedido não está marcado como faturado.")
            return

        confirmar = messagebox.askyesno(
            "Remover do faturamento",
            f"Deseja remover o pedido {pedido} da lista de faturados?\n\n"
            "Se ele ainda existir na carteira CSV atual, voltará a aparecer na aba Pedidos."
        )

        if not confirmar:
            return

        self.faturamento_service.remover_pedido_faturado(pedido)
        self.invalidar_cache()
        self.refresh_all()
        self.salvar_estado_atual()

        self.set_status(f"Pedido {pedido} removido da lista de faturados.")

    def abrir_janela_bloqueio_observacao(self):
        if not self.state.tem_dados():
            messagebox.showwarning("Nenhum arquivo", "Importe um CSV primeiro.")
            return

        observacoes = self.state.obter_observacoes_disponiveis()

        if not observacoes:
            messagebox.showinfo("Sem observações", "Não foram encontradas observações nos pedidos em aberto.")
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
            messagebox.showinfo("Clientes não encontrados", "Nenhum cliente foi encontrado nos pedidos em aberto.")
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
            texto_busca_funcao=lambda r: f'{r["cliente_curto"]} {r["cliente_original"]} {r["cliente_chave"]}',
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
            messagebox.showinfo("Itens não encontrados", "Nenhum item foi encontrado nos pedidos em aberto.")
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
                f'Qtd Total: {formatar_numero(r["qtde_total"])} | '
                f'Valor: {formatar_moeda(r["valor"])}'
            ),
            texto_busca_funcao=lambda r: f'{r["item"]} {r["descricao"]}',
            selecionados_atuais=self.state.codigos_itens_bloqueados,
            ao_bloquear=lambda selecionados: self.state.bloquear_itens_globais(selecionados, ""),
            ao_liberar=lambda selecionados: self.state.liberar_itens_globais(selecionados),
        )

    def gerar_df_prog2_itens_liberados(self):
        return self.exportacao_service.gerar_df_prog2_itens_liberados(
            self.state,
            self.obter_df_com_bloqueios_cache(),
        )

    def gerar_df_prog2_pedidos_liberados(self):
        return self.exportacao_service.gerar_df_prog2_pedidos_liberados(
            self.state,
            self.obter_df_com_bloqueios_cache(),
        )

    def abrir_arquivo_pdf(self, caminho):
        self.abrir_arquivo(caminho)

    def abrir_janela_revisao_exportacao(self, df_exportar, titulo, formato):
        if df_exportar is None or df_exportar.empty:
            return False

        qtd_linhas = len(df_exportar)

        qtd_pedidos = 0
        if "Pedido" in df_exportar.columns:
            qtd_pedidos = df_exportar["Pedido"].nunique()

        qtd_itens = 0
        if "Item" in df_exportar.columns:
            qtd_itens = df_exportar["Item"].nunique()
        elif "Qtd. Itens Liberados" in df_exportar.columns:
            qtd_itens = df_exportar["Qtd. Itens Liberados"].sum()

        qtd_clientes = 0
        if "Cliente Original" in df_exportar.columns:
            qtd_clientes = df_exportar["Cliente Original"].nunique()
        elif "Cliente" in df_exportar.columns:
            qtd_clientes = df_exportar["Cliente"].nunique()

        qtde_total = 0
        for coluna in ["Qtde Liberada", "Qtde Saldo Liberada", "Qtde"]:
            if coluna in df_exportar.columns:
                qtde_total = df_exportar[coluna].sum()
                break

        valor_total = 0
        for coluna in ["Valor Liberado", "Valor Total Liberado", "Valor"]:
            if coluna in df_exportar.columns:
                valor_total = df_exportar[coluna].sum()
                break

        mensagem = (
            f"{titulo}\n\n"
            f"Formato: {formato.upper()}\n"
            f"Linhas: {qtd_linhas}\n"
            f"Pedidos: {qtd_pedidos}\n"
            f"Itens: {formatar_numero(qtd_itens)}\n"
            f"Clientes: {qtd_clientes}\n"
            f"Qtde total: {formatar_numero(qtde_total)}\n"
            f"Valor liberado: {formatar_moeda(valor_total)}\n\n"
            "Deseja continuar?"
        )

        return messagebox.askyesno("Revisar exportação", mensagem)

    def exportar_dataframe_escolhido(self, df_exportar, titulo, nome_padrao, formato):
        if df_exportar.empty:
            messagebox.showwarning("Sem dados para exportar", "Não há dados liberados para exportar.")
            return

        if not self.abrir_janela_revisao_exportacao(df_exportar, titulo, formato):
            self.set_status("Exportação cancelada.")
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

                exportar_dataframe_pdf(caminho, df_exportar, titulo=titulo)

                self.abrir_arquivo_pdf(caminho)
                self.set_status(f"PDF temporário aberto: {caminho}")

            except Exception as erro:
                self.registrar_erro("Erro ao gerar PDF", erro)
                messagebox.showerror("Erro ao gerar PDF", str(erro))

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
            exportar_dataframe_excel(caminho, df_exportar, sheet_name=nome_padrao[:31])

            messagebox.showinfo("Exportação concluída", f"Arquivo exportado com sucesso:\n{caminho}")
            self.set_status(f"Arquivo exportado: {caminho}")

        except Exception as erro:
            self.registrar_erro("Erro ao exportar Excel", erro)
            messagebox.showerror("Erro ao exportar", str(erro))

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

            self.invalidar_cache()
            self.refresh_all()
            self.salvar_estado_atual()
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

        self.invalidar_cache()
        self.refresh_all()
        self.salvar_estado_atual()
        self.set_status("Seleção liberada.")

    def liberar_bloqueio_na_aba(self):
        id_linha = self.bloqueios_tab.get_selected_id_linha()

        if id_linha is None:
            messagebox.showwarning("Nenhum bloqueio selecionado", "Selecione uma linha bloqueada.")
            return

        linha = self.state.pegar_linha_por_id(id_linha)

        if linha is None:
            return

        pedido = str(linha["Pedido"])
        item = str(linha["Item"])

        if pedido in self.state.pedidos_bloqueados:
            confirmar = messagebox.askyesno("Liberar pedido", f"Deseja liberar o pedido {pedido} inteiro?")

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
            confirmar = messagebox.askyesno("Liberar item global", f"Deseja liberar o item {item} na carteira inteira?")

            if confirmar:
                self.state.liberar_item_global(item)

        else:
            self.state.liberar_linha(id_linha)

        self.invalidar_cache()
        self.refresh_all()
        self.salvar_estado_atual()
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
        self.invalidar_cache()
        self.refresh_all()
        self.salvar_estado_atual()
        self.set_status("Todos os bloqueios foram removidos.")

    def exportar_excel(self):
        if not self.state.tem_dados():
            messagebox.showwarning("Nenhum arquivo importado", "Importe um CSV antes de exportar.")
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

            messagebox.showinfo("Exportação concluída", f"Relatório exportado com sucesso:\n{caminho}")
            self.set_status(f"Excel exportado: {caminho}")

        except Exception as erro:
            self.registrar_erro("Erro ao exportar Excel completo", erro)
            messagebox.showerror("Erro ao exportar Excel", str(erro))

    def exportar_csv_atual(self):
        if not self.state.tem_dados():
            messagebox.showwarning("Nenhum arquivo importado", "Importe um CSV antes de exportar.")
            return

        aba_atual = self.abas.tab(self.abas.select(), "text")

        if aba_atual == "Pedidos":
            df_exportar = self.state.gerar_df_pedidos_ajustados()
        elif aba_atual == "PROG 2":
            df_exportar = self.state.gerar_df_prog2()
        elif aba_atual == "Faturados":
            df_exportar = self.faturados_tab.get_current_df()
        elif aba_atual == "Atrasados":
            df_exportar = self.atrasados_tab.get_current_df()
        elif aba_atual == "Bloqueios":
            df_exportar = self.state.gerar_df_bloqueios()
        else:
            df_exportar = self.consolidacoes_tab.get_current_df()

        if df_exportar is None:
            messagebox.showwarning("Nenhuma visualização", "Nenhum dado disponível para exportar.")
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

            messagebox.showinfo("Exportação concluída", f"CSV exportado com sucesso:\n{caminho}")
            self.set_status(f"CSV exportado: {caminho}")

        except Exception as erro:
            self.registrar_erro("Erro ao exportar CSV", erro)
            messagebox.showerror("Erro ao exportar CSV", str(erro))
