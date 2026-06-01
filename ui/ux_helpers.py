import tkinter as tk
from tkinter import ttk

from ui.styles import CORES, FONTE


def criar_menu_contexto(parent):
    return tk.Menu(
        parent,
        tearoff=0,
        font=(FONTE, 9),
        background=CORES["card"],
        foreground=CORES["text"],
        activebackground=CORES["primary_soft"],
        activeforeground=CORES["text"],
        relief="solid",
        borderwidth=1,
    )


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


def abrir_janela_detalhes(parent, titulo, dados, itens=None):
    janela = tk.Toplevel(parent)
    janela.title(titulo)
    janela.geometry("820x560")
    janela.minsize(680, 420)
    janela.configure(background=CORES["bg"])
    janela.transient(parent.winfo_toplevel())

    container = ttk.Frame(janela, padding=(12, 10))
    container.pack(fill="both", expand=True)

    topo = ttk.Frame(container)
    topo.pack(fill="x", pady=(0, 8))

    ttk.Label(topo, text=titulo, style="TopBarTitle.TLabel").pack(side="left")

    corpo = ttk.Frame(container)
    corpo.pack(fill="both", expand=True)

    texto = tk.Text(
        corpo,
        wrap="word",
        height=18,
        font=(FONTE, 10),
        bg=CORES["card"],
        fg=CORES["text"],
        insertbackground=CORES["text"],
        relief="solid",
        borderwidth=1,
        padx=10,
        pady=8,
    )
    scroll = ttk.Scrollbar(corpo, orient="vertical", command=texto.yview)
    texto.configure(yscrollcommand=scroll.set)

    texto.grid(row=0, column=0, sticky="nsew")
    scroll.grid(row=0, column=1, sticky="ns")
    corpo.rowconfigure(0, weight=1)
    corpo.columnconfigure(0, weight=1)

    linhas = []
    for chave, valor in dados:
        if valor is None:
            valor = ""
        linhas.append(f"{chave}: {valor}")

    if itens:
        linhas.append("")
        linhas.append("Itens")
        linhas.append("-" * 80)
        for item in itens:
            if isinstance(item, dict):
                linha = " | ".join(f"{chave}: {valor}" for chave, valor in item.items())
            else:
                linha = str(item)
            linhas.append(linha)

    conteudo = "\n".join(linhas)
    texto.insert("1.0", conteudo)
    texto.config(state="disabled")

    botoes = ttk.Frame(container)
    botoes.pack(fill="x", pady=(8, 0))

    ttk.Button(
        botoes,
        text="Copiar detalhes",
        command=lambda: copiar_para_clipboard(janela, conteudo),
        style="Compact.TButton",
    ).pack(side="left")

    ttk.Button(
        botoes,
        text="Fechar",
        command=janela.destroy,
        style="Compact.TButton",
    ).pack(side="right")

    janela.focus_set()
    return janela


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
    tabela.bind("<Double-1>", lambda event: ver_detalhes())
    tab.menu_contexto_generico = menu
    tab.abrir_detalhes_selecionado = ver_detalhes
    tab.copiar_linha_selecionada = copiar_linha
