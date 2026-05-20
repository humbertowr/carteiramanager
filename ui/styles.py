from tkinter import ttk


def configurar_estilo():
    estilo = ttk.Style()

    try:
        estilo.theme_use("clam")
    except Exception:
        pass

    estilo.configure(
        "TFrame",
        background="#f4f6f8"
    )

    estilo.configure(
        "TLabel",
        font=("Segoe UI", 9),
        background="#f4f6f8"
    )

    estilo.configure(
        "Title.TLabel",
        font=("Segoe UI", 17, "bold"),
        background="#f4f6f8"
    )

    estilo.configure(
        "Subtitle.TLabel",
        font=("Segoe UI", 8),
        foreground="#5f6b7a",
        background="#f4f6f8"
    )

    estilo.configure(
        "Hint.TLabel",
        font=("Segoe UI", 8),
        foreground="#6c757d",
        background="#f4f6f8"
    )

    estilo.configure(
        "Summary.TLabelframe",
        background="#f4f6f8"
    )

    estilo.configure(
        "Summary.TLabelframe.Label",
        font=("Segoe UI", 8, "bold")
    )

    estilo.configure(
        "Section.TLabelframe",
        background="#f4f6f8",
        padding=4
    )

    estilo.configure(
        "Section.TLabelframe.Label",
        font=("Segoe UI", 8, "bold")
    )

    estilo.configure(
        "SummaryTitle.TLabel",
        font=("Segoe UI", 8),
        foreground="#5f6b7a",
        background="#f4f6f8"
    )

    estilo.configure(
        "SummaryValue.TLabel",
        font=("Segoe UI", 10, "bold"),
        background="#f4f6f8"
    )

    estilo.configure(
        "Treeview",
        rowheight=26,
        font=("Segoe UI", 9),
        background="#ffffff",
        fieldbackground="#ffffff",
        borderwidth=0
    )

    estilo.configure(
        "Treeview.Heading",
        font=("Segoe UI", 9, "bold"),
        background="#e9ecef",
        foreground="#212529",
        padding=(5, 4)
    )

    estilo.map(
        "Treeview",
        background=[("selected", "#0d6efd")],
        foreground=[("selected", "#ffffff")]
    )

    estilo.configure(
        "TButton",
        font=("Segoe UI", 8),
        padding=(6, 3)
    )

    estilo.configure(
        "Primary.TButton",
        font=("Segoe UI", 8, "bold"),
        padding=(7, 3)
    )

    estilo.configure(
        "TEntry",
        padding=(3, 2)
    )

    estilo.configure(
        "TCombobox",
        padding=(3, 2)
    )

    estilo.configure(
        "TNotebook",
        background="#f4f6f8",
        borderwidth=0
    )

    estilo.configure(
        "TNotebook.Tab",
        font=("Segoe UI", 9),
        padding=(10, 5)
    )


def configurar_tags_tabela(tabela):
    tabela.tag_configure("pedido", font=("Segoe UI", 9, "bold"))
    tabela.tag_configure("pedido_parcial", background="#fff3cd")
    tabela.tag_configure("pedido_bloqueado", background="#f8d7da")
    tabela.tag_configure("item_bloqueado", background="#f8d7da", foreground="#842029")
    tabela.tag_configure("item_liberado", background="#d1e7dd", foreground="#0f5132")
    tabela.tag_configure("prog2", background="#cff4fc", foreground="#055160")
    tabela.tag_configure("item_linha", foreground="#495057")