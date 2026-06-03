import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from ui.styles import CORES, FONTE


class ToolTip:
    def __init__(self, widget, text, delay=600):
        self.widget = widget
        self.text = str(text or "").strip()
        self.delay = delay
        self._after_id = None
        self._window = None
        if self.text:
            widget.bind("<Enter>", self._schedule, add="+")
            widget.bind("<Leave>", self._hide, add="+")
            widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event=None):
        self._hide()
        self._after_id = self.widget.after(self.delay, self._show)

    def _show(self):
        if self._window or not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + 18
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        except Exception:
            return
        self._window = tk.Toplevel(self.widget)
        self._window.wm_overrideredirect(True)
        self._window.wm_geometry(f"+{x}+{y}")
        frame = tk.Frame(
            self._window,
            background=CORES["text"],
            borderwidth=1,
            relief="solid",
        )
        frame.pack(fill="both", expand=True)
        label = tk.Label(
            frame,
            text=self.text,
            justify="left",
            wraplength=360,
            font=(FONTE, 8),
            background=CORES["text"],
            foreground="#ffffff",
            padx=8,
            pady=5,
        )
        label.pack()

    def _hide(self, _event=None):
        if self._after_id:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        if self._window:
            try:
                self._window.destroy()
            except Exception:
                pass
            self._window = None


def aplicar_tooltip(widget, texto):
    return ToolTip(widget, texto)


def criar_menu_contexto(parent):
    return tk.Menu(
        parent,
        tearoff=0,
        font=(FONTE, 9),
        background=CORES["card"],
        foreground=CORES["text"],
        activebackground=CORES["primary_soft"],
        activeforeground=CORES["text"],
        disabledforeground=CORES["muted"],
        relief="solid",
        borderwidth=1,
    )


def criar_cabecalho_aba(parent, titulo, subtitulo=""):
    frame = ttk.Frame(parent, padding=(2, 0, 2, 6), style="PageHeader.TFrame")
    frame.pack(fill="x")
    ttk.Label(frame, text=titulo, style="PageTitle.TLabel").pack(anchor="w")
    if subtitulo:
        ttk.Label(frame, text=subtitulo, style="PageSubtitle.TLabel").pack(anchor="w", pady=(1, 0))
    return frame


def criar_barra_acoes(parent):
    frame = ttk.Frame(parent, padding=(6, 5), style="ActionBar.TFrame")
    frame.pack(fill="x", pady=(0, 6))
    return frame


def botao(parent, texto, comando, tipo="secondary", tooltip="", **pack_kwargs):
    estilos = {
        "primary": "Primary.TButton",
        "secondary": "Secondary.TButton",
        "danger": "Danger.TButton",
        "success": "Success.TButton",
        "subtle": "Subtle.TButton",
        "compact": "Compact.TButton",
    }
    b = ttk.Button(parent, text=texto, command=comando, style=estilos.get(tipo, "Secondary.TButton"))
    if pack_kwargs:
        b.pack(**pack_kwargs)
    if tooltip:
        aplicar_tooltip(b, tooltip)
    return b


def copiar_para_clipboard(widget, texto, controller=None, mensagem="Conteúdo copiado."):
    texto = "" if texto is None else str(texto)
    widget.clipboard_clear()
    widget.clipboard_append(texto)

    if controller and hasattr(controller, "set_status"):
        controller.set_status(mensagem)


def obter_texto_linha_treeview(tabela, iid=None):
    if iid is None:
        selecionado = tabela.selection()
        if not selecionado:
            return ""
        iid = selecionado[0]

    if not tabela.exists(iid):
        return ""

    partes = []
    texto_arvore = str(tabela.item(iid, "text") or "").strip()
    if texto_arvore:
        titulo_arvore = tabela.heading("#0", "text") or "Linha"
        partes.append(f"{titulo_arvore}: {texto_arvore}")

    valores = list(tabela.item(iid, "values") or [])
    for indice, coluna in enumerate(tabela["columns"]):
        valor = valores[indice] if indice < len(valores) else ""
        if str(valor).strip():
            partes.append(f"{tabela.heading(coluna, 'text') or coluna}: {valor}")

    return "\n".join(partes)


def _valor_formatado(valor):
    if valor is None:
        return ""
    texto = str(valor)
    return "-" if texto.strip() == "" else texto


def abrir_janela_detalhes(parent, titulo, dados, itens=None):
    janela = tk.Toplevel(parent)
    janela.title(titulo)
    janela.geometry("860x600")
    janela.minsize(720, 460)
    janela.configure(background=CORES["bg"])
    janela.transient(parent.winfo_toplevel())
    janela.bind("<Escape>", lambda _event: janela.destroy())

    container = ttk.Frame(janela, padding=(14, 12))
    container.pack(fill="both", expand=True)

    topo = ttk.Frame(container, style="PageHeader.TFrame")
    topo.pack(fill="x", pady=(0, 8))
    ttk.Label(topo, text=titulo, style="DetailTitle.TLabel").pack(anchor="w")
    ttk.Label(topo, text="Detalhes da linha selecionada.", style="PageSubtitle.TLabel").pack(anchor="w", pady=(1, 0))

    corpo = ttk.Frame(container)
    corpo.pack(fill="both", expand=True)
    corpo.rowconfigure(0, weight=1)
    corpo.columnconfigure(0, weight=1)

    canvas = tk.Canvas(corpo, background=CORES["card"], highlightthickness=1, highlightbackground=CORES["border"])
    scroll = ttk.Scrollbar(corpo, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scroll.set)
    canvas.grid(row=0, column=0, sticky="nsew")
    scroll.grid(row=0, column=1, sticky="ns")

    inner = ttk.Frame(canvas, padding=(12, 10), style="Card.TFrame")
    canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")

    def _on_configure(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfigure(canvas_window, width=canvas.winfo_width())

    inner.bind("<Configure>", _on_configure)
    canvas.bind("<Configure>", _on_configure)

    conteudo_linhas = []
    for idx, (chave, valor) in enumerate(dados or []):
        ttk.Label(inner, text=str(chave), style="DetailKey.TLabel").grid(row=idx, column=0, sticky="nw", padx=(0, 12), pady=3)
        ttk.Label(inner, text=_valor_formatado(valor), style="DetailValue.TLabel", wraplength=560).grid(row=idx, column=1, sticky="nw", pady=3)
        conteudo_linhas.append(f"{chave}: {_valor_formatado(valor)}")

    linha_atual = len(dados or []) + 1
    if itens:
        ttk.Separator(inner).grid(row=linha_atual, column=0, columnspan=2, sticky="ew", pady=(10, 8))
        linha_atual += 1
        ttk.Label(inner, text="Itens", style="DetailSection.TLabel").grid(row=linha_atual, column=0, columnspan=2, sticky="w", pady=(0, 6))
        conteudo_linhas.append("")
        conteudo_linhas.append("Itens")
        linha_atual += 1
        for item in itens:
            if isinstance(item, dict):
                texto = " | ".join(f"{chave}: {valor}" for chave, valor in item.items())
            else:
                texto = str(item)
            ttk.Label(inner, text=texto, style="DetailValue.TLabel", wraplength=760).grid(
                row=linha_atual, column=0, columnspan=2, sticky="w", pady=2
            )
            conteudo_linhas.append(texto)
            linha_atual += 1

    inner.columnconfigure(1, weight=1)
    conteudo = "\n".join(conteudo_linhas)

    botoes = ttk.Frame(container)
    botoes.pack(fill="x", pady=(10, 0))

    ttk.Button(
        botoes,
        text="Copiar",
        command=lambda: copiar_para_clipboard(janela, conteudo),
        style="Secondary.TButton",
    ).pack(side="left")

    ttk.Button(
        botoes,
        text="Fechar",
        command=janela.destroy,
        style="Secondary.TButton",
    ).pack(side="right")

    janela.focus_set()
    return janela


def aplicar_estado_vazio_treeview(tabela, mensagem, tag="estado_vazio"):
    try:
        tabela.delete(*tabela.get_children())
        if not str(mensagem or "").strip():
            return
        tabela.tag_configure(tag, foreground=CORES["muted"], font=(FONTE, 9, "italic"))
        tabela.insert("", "end", text=mensagem, values=tuple("" for _ in tabela["columns"]), tags=(tag,))
    except Exception:
        pass


def confirmar_acao(titulo, mensagem, detalhe="", parent=None):
    texto = str(mensagem or "").strip()
    if detalhe:
        texto += f"\n\n{detalhe}"
    return messagebox.askyesno(titulo or "Confirmar ação", texto, parent=parent)


def mostrar_erro_operacional(titulo, erro, contexto=""):
    detalhe = str(erro)
    if contexto:
        detalhe = f"{contexto}\n\nDetalhe: {erro}"
    messagebox.showerror(titulo or "Erro", detalhe)


def aplicar_menu_generico_tabela(tab, nome_contexto="Linha"):
    tabela = getattr(tab, "tabela", None)
    if tabela is None:
        return

    menu = criar_menu_contexto(tabela)

    def selecionar_evento(event):
        iid = tabela.identify_row(event.y)
        if not iid:
            return "break"
        tabela.selection_set(iid)
        tabela.focus(iid)
        menu.tk_popup(event.x_root, event.y_root)
        return "break"

    def ver_detalhes():
        iid = tabela.focus() or (tabela.selection()[0] if tabela.selection() else "")
        if not iid:
            return
        conteudo = obter_texto_linha_treeview(tabela, iid)
        dados = [("Origem", nome_contexto)]
        for linha in conteudo.splitlines():
            if ":" in linha:
                chave, valor = linha.split(":", 1)
                dados.append((chave.strip(), valor.strip()))
        abrir_janela_detalhes(tab.parent, f"Detalhes - {nome_contexto}", dados)

    def copiar_linha():
        iid = tabela.focus() or (tabela.selection()[0] if tabela.selection() else "")
        if iid:
            copiar_para_clipboard(tabela, obter_texto_linha_treeview(tabela, iid), getattr(tab, "controller", None), "Linha copiada.")

    menu.add_command(label="Ver detalhes", command=ver_detalhes)
    menu.add_command(label="Copiar linha", command=copiar_linha)

    tabela.bind("<Button-3>", selecionar_evento)
    tabela.bind("<Double-1>", lambda _event: ver_detalhes())
    tab.menu_contexto_generico = menu
    tab.abrir_detalhes_selecionado = ver_detalhes
    tab.copiar_linha_selecionada = copiar_linha
