from tkinter import ttk


CORES = {
    "bg": "#f3f4f6",
    "card": "#ffffff",
    "border": "#d8dee9",
    "text": "#111827",
    "muted": "#6b7280",
    "header": "#e5e7eb",
    "primary": "#2563eb",
    "primary_hover": "#1d4ed8",
    "success_bg": "#dcfce7",
    "success_fg": "#166534",
    "warning_bg": "#fef3c7",
    "warning_fg": "#92400e",
    "danger_bg": "#fee2e2",
    "danger_fg": "#991b1b",
    "info_bg": "#dbeafe",
    "info_fg": "#1e40af",
    "row_alt": "#f9fafb",
}


FONTE = "Segoe UI"


def configurar_estilo():
    estilo = ttk.Style()

    try:
        estilo.theme_use("clam")
    except Exception:
        pass

    estilo.configure(
        ".",
        font=(FONTE, 9),
        background=CORES["bg"],
        foreground=CORES["text"],
    )

    estilo.configure(
        "TFrame",
        background=CORES["bg"],
    )

    estilo.configure(
        "Card.TFrame",
        background=CORES["card"],
        relief="solid",
        borderwidth=1,
    )

    estilo.configure(
        "Toolbar.TFrame",
        background=CORES["card"],
    )

    estilo.configure(
        "TLabel",
        font=(FONTE, 9),
        background=CORES["bg"],
        foreground=CORES["text"],
    )

    estilo.configure(
        "Card.TLabel",
        font=(FONTE, 9),
        background=CORES["card"],
        foreground=CORES["text"],
    )

    estilo.configure(
        "Title.TLabel",
        font=(FONTE, 17, "bold"),
        background=CORES["bg"],
        foreground=CORES["text"],
    )

    estilo.configure(
        "Subtitle.TLabel",
        font=(FONTE, 8),
        foreground=CORES["muted"],
        background=CORES["bg"],
    )

    estilo.configure(
        "Hint.TLabel",
        font=(FONTE, 8),
        foreground=CORES["muted"],
        background=CORES["bg"],
    )

    estilo.configure(
        "CardHint.TLabel",
        font=(FONTE, 8),
        foreground=CORES["muted"],
        background=CORES["card"],
    )

    estilo.configure(
        "TopBar.TFrame",
        background=CORES["card"],
    )

    estilo.configure(
        "TopBarTitle.TLabel",
        font=(FONTE, 15, "bold"),
        background=CORES["card"],
        foreground=CORES["text"],
    )

    estilo.configure(
        "TopBarSubtitle.TLabel",
        font=(FONTE, 8),
        background=CORES["card"],
        foreground=CORES["muted"],
    )

    estilo.configure(
        "Section.TLabelframe",
        background=CORES["bg"],
        borderwidth=1,
        relief="solid",
        padding=6,
    )

    estilo.configure(
        "Section.TLabelframe.Label",
        font=(FONTE, 9, "bold"),
        foreground=CORES["text"],
        background=CORES["bg"],
    )

    estilo.configure(
        "Action.TLabelframe",
        background=CORES["card"],
        borderwidth=1,
        relief="solid",
        padding=6,
    )

    estilo.configure(
        "Action.TLabelframe.Label",
        font=(FONTE, 8, "bold"),
        foreground=CORES["text"],
        background=CORES["card"],
    )

    estilo.configure(
        "Kpi.TLabelframe",
        background=CORES["bg"],
        borderwidth=1,
        relief="solid",
        padding=5,
    )

    estilo.configure(
        "Kpi.TLabelframe.Label",
        font=(FONTE, 8, "bold"),
        foreground=CORES["text"],
        background=CORES["bg"],
    )

    estilo.configure(
        "KpiTitle.TLabel",
        font=(FONTE, 8),
        foreground=CORES["muted"],
        background=CORES["bg"],
    )

    estilo.configure(
        "KpiValue.TLabel",
        font=(FONTE, 10, "bold"),
        foreground=CORES["text"],
        background=CORES["bg"],
    )

    estilo.configure(
        "KpiPositive.TLabel",
        font=(FONTE, 10, "bold"),
        foreground=CORES["success_fg"],
        background=CORES["bg"],
    )

    estilo.configure(
        "KpiWarning.TLabel",
        font=(FONTE, 10, "bold"),
        foreground=CORES["warning_fg"],
        background=CORES["bg"],
    )

    estilo.configure(
        "KpiDanger.TLabel",
        font=(FONTE, 10, "bold"),
        foreground=CORES["danger_fg"],
        background=CORES["bg"],
    )

    estilo.configure(
        "Summary.TLabelframe",
        background=CORES["bg"],
        borderwidth=1,
        relief="solid",
    )

    estilo.configure(
        "Summary.TLabelframe.Label",
        font=(FONTE, 8, "bold"),
        foreground=CORES["text"],
        background=CORES["bg"],
    )

    estilo.configure(
        "SummaryTitle.TLabel",
        font=(FONTE, 8),
        foreground=CORES["muted"],
        background=CORES["bg"],
    )

    estilo.configure(
        "SummaryValue.TLabel",
        font=(FONTE, 10, "bold"),
        foreground=CORES["text"],
        background=CORES["bg"],
    )

    estilo.configure(
        "Treeview",
        rowheight=27,
        font=(FONTE, 9),
        background=CORES["card"],
        fieldbackground=CORES["card"],
        foreground=CORES["text"],
        borderwidth=0,
    )

    estilo.configure(
        "Treeview.Heading",
        font=(FONTE, 9, "bold"),
        background=CORES["header"],
        foreground=CORES["text"],
        padding=(6, 5),
        relief="flat",
    )

    estilo.map(
        "Treeview",
        background=[("selected", CORES["primary"])],
        foreground=[("selected", "#ffffff")],
    )

    estilo.configure(
        "TButton",
        font=(FONTE, 8),
        padding=(7, 4),
        background=CORES["header"],
        foreground=CORES["text"],
    )

    estilo.configure(
        "Primary.TButton",
        font=(FONTE, 8, "bold"),
        padding=(8, 4),
        background=CORES["primary"],
        foreground="#ffffff",
    )

    estilo.map(
        "Primary.TButton",
        background=[("active", CORES["primary_hover"])],
        foreground=[("active", "#ffffff")],
    )

    estilo.configure(
        "Danger.TButton",
        font=(FONTE, 8, "bold"),
        padding=(8, 4),
        foreground=CORES["danger_fg"],
    )

    estilo.configure(
        "TMenubutton",
        font=(FONTE, 8),
        padding=(8, 4),
        background=CORES["header"],
        foreground=CORES["text"],
    )

    estilo.configure(
        "TEntry",
        padding=(4, 3),
        fieldbackground="#ffffff",
    )

    estilo.configure(
        "TCombobox",
        padding=(4, 3),
        fieldbackground="#ffffff",
    )

    estilo.configure(
        "TNotebook",
        background=CORES["bg"],
        borderwidth=0,
    )

    estilo.configure(
        "TNotebook.Tab",
        font=(FONTE, 9),
        padding=(12, 6),
        background=CORES["header"],
        foreground=CORES["text"],
    )

    estilo.map(
        "TNotebook.Tab",
        background=[("selected", CORES["card"])],
        foreground=[("selected", CORES["text"])],
    )


def configurar_tags_tabela(tabela):
    tabela.tag_configure("pedido", font=(FONTE, 9, "bold"))
    tabela.tag_configure("pedido_liberado", background=CORES["success_bg"], foreground=CORES["success_fg"])
    tabela.tag_configure("pedido_parcial", background=CORES["warning_bg"], foreground=CORES["warning_fg"])
    tabela.tag_configure("pedido_bloqueado", background=CORES["danger_bg"], foreground=CORES["danger_fg"])

    tabela.tag_configure("item_linha", background=CORES["card"], foreground="#374151")
    tabela.tag_configure("item_liberado", background=CORES["success_bg"], foreground=CORES["success_fg"])
    tabela.tag_configure("item_bloqueado", background=CORES["danger_bg"], foreground=CORES["danger_fg"])

    tabela.tag_configure("prog2", background=CORES["info_bg"], foreground=CORES["info_fg"])
    tabela.tag_configure("linha_alt", background=CORES["row_alt"])