import tkinter as tk

from utils import theme
from utils.rounded_widgets import RoundedPanel


def create_module_header(parent, title, subtitle, metrics=()):

    header = tk.Frame(parent, bg=theme.BACKGROUND)
    header.pack(fill="x", padx=30, pady=(20, 15))

    title_area = tk.Frame(header, bg=theme.BACKGROUND)
    title_area.pack(side="left", fill="x", expand=True)
    admin_label = tk.Label(
        title_area,
        text="SCHOOL ADMINISTRATION",
        font=("Segoe UI", 7, "bold"),
        bg=theme.BACKGROUND,
        fg=theme.TEXT_SECONDARY
    )
    admin_label.pack(anchor="w")
    title_clip = tk.Frame(
        title_area,
        width=1,
        height=32,
        bg=theme.BACKGROUND
    )
    title_clip.pack_propagate(False)
    title_clip.pack(anchor="w")
    title_label = tk.Label(
        title_clip,
        text=title,
        font=("Segoe UI", 25, "bold"),
        bg=theme.BACKGROUND,
        fg=theme.TEXT_PRIMARY
    )
    title_label.place(x=0, y=0)
    subtitle_label = tk.Label(
        title_area,
        text=subtitle,
        font=("Segoe UI", 9),
        bg=theme.BACKGROUND,
        fg=theme.TEXT_SECONDARY
    )
    subtitle_label.pack(anchor="w", pady=(2, 0))

    metric_area = tk.Frame(header, bg=theme.BACKGROUND)
    metric_area.pack(side="right", padx=(12, 0))
    metric_widgets = []
    for index, (value, label) in enumerate(metrics):
        background = theme.ACCENT if index == 0 else theme.PRIMARY
        foreground = (
            theme.TEXT_PRIMARY if index == 0 else theme.TEXT_LIGHT
        )
        chip = tk.Frame(
            metric_area,
            bg=background,
            padx=11,
            pady=6
        )
        chip.pack(side="left", padx=(6, 0))
        value_variable = (
            value if isinstance(value, tk.Variable)
            else tk.StringVar(master=chip, value=value)
        )
        tk.Label(
            chip,
            textvariable=value_variable,
            font=("Segoe UI", 10, "bold"),
            bg=background,
            fg=foreground
        ).pack(side="left", padx=(0, 5))
        tk.Label(
            chip,
            text=label.upper(),
            font=("Segoe UI", 6, "bold"),
            bg=background,
            fg=foreground
        ).pack(side="left")
        metric_widgets.append(chip)

    header._navigation_heading_meta = {
        "title_clip": title_clip,
        "title_label": title_label,
        "admin_label": admin_label,
        "subtitle_label": subtitle_label,
        "metric_widgets": tuple(metric_widgets),
        "rest_widgets": ()
    }

    return header


def create_live_preview(parent, title, badge, details, icon="•"):

    panel = RoundedPanel(
        parent,
        bg=theme.PRIMARY,
        padx=18,
        pady=14,
        radius=12,
        highlightbackground=theme.PRIMARY,
        highlightthickness=1,
        hoverable=True
    )
    panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

    content = panel.content
    content.configure(bg=theme.PRIMARY)

    top_row = tk.Frame(content, bg=theme.PRIMARY)
    top_row.pack(fill="x")
    tk.Label(
        top_row,
        text="LIVE PREVIEW",
        font=("Segoe UI", 7, "bold"),
        bg=theme.PRIMARY,
        fg=theme.PALE_GREEN
    ).pack(side="left")
    tk.Label(
        top_row,
        text=icon,
        font=("Segoe UI", 10, "bold"),
        bg=theme.ACCENT,
        fg=theme.TEXT_PRIMARY,
        width=3,
        pady=3
    ).pack(side="right")

    title_variable = (
        title if isinstance(title, tk.Variable)
        else tk.StringVar(master=content, value=title)
    )
    tk.Label(
        content,
        textvariable=title_variable,
        font=("Segoe UI", 18, "bold"),
        bg=theme.PRIMARY,
        fg=theme.TEXT_LIGHT,
        anchor="w",
        wraplength=250,
        justify="left"
    ).pack(fill="x", pady=(12, 8))

    badge_variable = (
        badge if isinstance(badge, tk.Variable)
        else tk.StringVar(master=content, value=badge)
    )
    tk.Label(
        content,
        textvariable=badge_variable,
        font=("Segoe UI", 8, "bold"),
        bg=theme.ACCENT,
        fg=theme.TEXT_PRIMARY,
        padx=10,
        pady=5,
        anchor="w"
    ).pack(anchor="w", pady=(0, 10))

    tk.Frame(content, height=1, bg=theme.MOSS).pack(fill="x", pady=(0, 8))

    for label, value in details:
        value_variable = (
            value if isinstance(value, tk.Variable)
            else tk.StringVar(master=content, value=value)
        )
        row = tk.Frame(content, bg=theme.PRIMARY)
        row.pack(fill="x", pady=2)
        tk.Label(
            row,
            text=label.upper(),
            font=("Segoe UI", 6, "bold"),
            bg=theme.PRIMARY,
            fg=theme.PALE_GREEN
        ).pack(side="left")
        tk.Label(
            row,
            textvariable=value_variable,
            font=("Segoe UI", 8, "bold"),
            bg=theme.PRIMARY,
            fg=theme.TEXT_LIGHT
        ).pack(side="right")

    stripe = tk.Canvas(
        content,
        height=7,
        bg=theme.PRIMARY,
        bd=0,
        highlightthickness=0
    )
    stripe.pack(fill="x", side="bottom", pady=(10, 0))

    def draw_stripe(event):
        stripe.delete("all")
        for start in range(-8, event.width, 22):
            stripe.create_polygon(
                start,
                7,
                start + 8,
                7,
                start + 16,
                0,
                start + 8,
                0,
                fill=theme.ACCENT,
                outline=""
            )

    stripe.bind("<Configure>", draw_stripe, add="+")
    return panel


def bind_preview_updates(widgets, callback):

    for widget in widgets:
        widget.bind("<KeyRelease>", callback, add="+")
        widget.bind("<<ComboboxSelected>>", callback, add="+")
        widget.bind("<FocusOut>", callback, add="+")
