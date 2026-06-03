from tkinter import ttk


FONTE = "Segoe UI"

CORES = {
    "bg": "#eef2f7",
    "card": "#ffffff",
    "card_soft": "#f8fafc",
    "border": "#d7dee8",
    "border_soft": "#e5eaf1",
    "text": "#111827",
    "muted": "#64748b",
    "header": "#e8edf5",
    "topbar": "#0f172a",
    "topbar_2": "#111827",
    "topbar_button": "#1e293b",
    "topbar_button_hover": "#334155",
    "topbar_button_pressed": "#2563eb",
    "topbar_text": "#f8fafc",
    "primary": "#2563eb",
    "primary_hover": "#1d4ed8",
    "primary_soft": "#dbeafe",
    "success_bg": "#dcfce7",
    "success_fg": "#166534",
    "warning_bg": "#fef3c7",
    "warning_fg": "#92400e",
    "danger_bg": "#fee2e2",
    "danger_fg": "#991b1b",
    "info_bg": "#dbeafe",
    "info_fg": "#1e40af",
    "row_alt": "#f8fafc",
    "selected_batch_bg": "#bfdbfe",
    "selected_batch_item_bg": "#eff6ff",
    "selected_batch_fg": "#1e3a8a",
}


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

    estilo.configure("TFrame", background=CORES["bg"])
    estilo.configure("Card.TFrame", background=CORES["card"])
    estilo.configure("Toolbar.TFrame", background=CORES["card"])
    estilo.configure("Soft.TFrame", background=CORES["card_soft"])

    estilo.configure(
        "TopBar.TFrame",
        background=CORES["topbar"],
    )

    estilo.configure(
        "TopBarTitle.TLabel",
        font=(FONTE, 16, "bold"),
        background=CORES["topbar"],
        foreground=CORES["topbar_text"],
        padding=(0, 1),
    )

    estilo.configure(
        "TopBarSubtitle.TLabel",
        font=(FONTE, 8),
        background=CORES["topbar"],
        foreground="#cbd5e1",
    )

    estilo.configure(
        "TopMenu.TMenubutton",
        font=(FONTE, 9, "bold"),
        padding=(13, 7),
        background=CORES["topbar_button"],
        foreground=CORES["topbar_text"],
        borderwidth=0,
        relief="flat",
        arrowcolor=CORES["topbar_text"],
    )

    estilo.map(
        "TopMenu.TMenubutton",
        background=[
            ("pressed", CORES["topbar_button_pressed"]),
            ("active", CORES["topbar_button_hover"]),
        ],
        foreground=[
            ("pressed", "#ffffff"),
            ("active", "#ffffff"),
        ],
        relief=[
            ("pressed", "flat"),
            ("active", "flat"),
        ],
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
        "CardTitle.TLabel",
        font=(FONTE, 10, "bold"),
        background=CORES["card"],
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
        "Section.TLabelframe",
        background=CORES["card"],
        borderwidth=1,
        relief="solid",
        padding=5,
    )

    estilo.configure(
        "Section.TLabelframe.Label",
        font=(FONTE, 9, "bold"),
        foreground=CORES["text"],
        background=CORES["card"],
    )

    estilo.configure(
        "Action.TLabelframe",
        background=CORES["card_soft"],
        borderwidth=1,
        relief="solid",
        padding=5,
    )

    estilo.configure(
        "Action.TLabelframe.Label",
        font=(FONTE, 8, "bold"),
        foreground=CORES["text"],
        background=CORES["card_soft"],
    )

    estilo.configure(
        "Kpi.TLabelframe",
        background=CORES["card"],
        borderwidth=1,
        relief="solid",
        padding=6,
    )

    estilo.configure(
        "Kpi.TLabelframe.Label",
        font=(FONTE, 8, "bold"),
        foreground=CORES["text"],
        background=CORES["card"],
    )

    estilo.configure(
        "KpiCard.TFrame",
        background=CORES["card_soft"],
        borderwidth=1,
        relief="solid",
    )

    estilo.configure(
        "KpiTitle.TLabel",
        font=(FONTE, 8),
        foreground=CORES["muted"],
        background=CORES["card_soft"],
    )

    estilo.configure(
        "KpiValue.TLabel",
        font=(FONTE, 10, "bold"),
        foreground=CORES["text"],
        background=CORES["card_soft"],
    )

    estilo.configure(
        "KpiPositive.TLabel",
        font=(FONTE, 10, "bold"),
        foreground=CORES["success_fg"],
        background=CORES["card_soft"],
    )

    estilo.configure(
        "KpiWarning.TLabel",
        font=(FONTE, 10, "bold"),
        foreground=CORES["warning_fg"],
        background=CORES["card_soft"],
    )

    estilo.configure(
        "KpiDanger.TLabel",
        font=(FONTE, 10, "bold"),
        foreground=CORES["danger_fg"],
        background=CORES["card_soft"],
    )

    estilo.configure(
        "SummaryValue.TLabel",
        font=(FONTE, 9, "bold"),
        foreground=CORES["text"],
        background=CORES["card"],
    )

    estilo.configure(
        "SummaryMuted.TLabel",
        font=(FONTE, 8),
        foreground=CORES["muted"],
        background=CORES["card"],
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
        padding=(7, 3),
        background=CORES["header"],
        foreground=CORES["text"],
        borderwidth=1,
    )

    estilo.map(
        "TButton",
        background=[("active", CORES["border_soft"])],
    )

    estilo.configure(
        "Compact.TButton",
        font=(FONTE, 8),
        padding=(6, 3),
    )

    estilo.configure(
        "Primary.TButton",
        font=(FONTE, 8, "bold"),
        padding=(9, 4),
        background=CORES["primary"],
        foreground="#ffffff",
    )

    estilo.map(
        "Primary.TButton",
        background=[("active", CORES["primary_hover"]), ("pressed", CORES["primary_hover"])],
        foreground=[("active", "#ffffff"), ("pressed", "#ffffff")],
    )

    estilo.configure(
        "Success.TButton",
        font=(FONTE, 8, "bold"),
        padding=(9, 4),
        foreground=CORES["success_fg"],
    )

    estilo.configure(
        "Danger.TButton",
        font=(FONTE, 8, "bold"),
        padding=(9, 4),
        foreground=CORES["danger_fg"],
    )

    estilo.configure(
        "Subtle.TButton",
        font=(FONTE, 8),
        padding=(7, 3),
        foreground=CORES["muted"],
    )

    estilo.configure(
        "TMenubutton",
        font=(FONTE, 8, "bold"),
        padding=(7, 3),
        background=CORES["header"],
        foreground=CORES["text"],
        arrowcolor=CORES["muted"],
    )

    estilo.configure(
        "TEntry",
        padding=(5, 4),
        fieldbackground="#ffffff",
        bordercolor=CORES["border"],
        lightcolor=CORES["border"],
        darkcolor=CORES["border"],
    )

    estilo.configure(
        "TCombobox",
        padding=(5, 4),
        fieldbackground="#ffffff",
        bordercolor=CORES["border"],
        arrowcolor=CORES["muted"],
    )

    estilo.configure(
        "TNotebook",
        background=CORES["bg"],
        borderwidth=0,
        tabmargins=(0, 4, 0, 0),
    )

    estilo.configure(
        "TNotebook.Tab",
        font=(FONTE, 9, "bold"),
        padding=(12, 6),
        background=CORES["header"],
        foreground=CORES["muted"],
    )

    estilo.map(
        "TNotebook.Tab",
        background=[("selected", CORES["card"]), ("active", CORES["primary_soft"])],
        foreground=[("selected", CORES["primary"]), ("active", CORES["text"])],
    )


def configurar_tags_tabela(tabela):
    tabela.tag_configure("pedido", font=(FONTE, 9, "bold"))
    tabela.tag_configure("pedido_liberado", background=CORES["success_bg"], foreground=CORES["success_fg"], font=(FONTE, 9, "bold"))
    tabela.tag_configure("pedido_parcial", background=CORES["warning_bg"], foreground=CORES["warning_fg"], font=(FONTE, 9, "bold"))
    tabela.tag_configure("pedido_bloqueado", background=CORES["danger_bg"], foreground=CORES["danger_fg"], font=(FONTE, 9, "bold"))
    tabela.tag_configure("pedido_marcado", background=CORES["selected_batch_bg"], foreground=CORES["selected_batch_fg"], font=(FONTE, 9, "bold"))
    tabela.tag_configure("item_linha", background=CORES["card"], foreground="#374151")
    tabela.tag_configure("item_liberado", background=CORES["success_bg"], foreground=CORES["success_fg"])
    tabela.tag_configure("item_bloqueado", background=CORES["danger_bg"], foreground=CORES["danger_fg"])
    tabela.tag_configure("item_marcado", background=CORES["selected_batch_item_bg"], foreground=CORES["selected_batch_fg"])
    tabela.tag_configure("prog2", background=CORES["info_bg"], foreground=CORES["info_fg"], font=(FONTE, 9, "bold"))
    tabela.tag_configure("linha_alt", background=CORES["row_alt"])
