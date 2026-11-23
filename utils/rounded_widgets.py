import math
import tkinter as tk
from tkinter import ttk

from utils import theme


def _rounded_points(x1, y1, x2, y2, radius):

    radius = min(radius, (x2 - x1) / 2, (y2 - y1) / 2)
    points = []
    corners = (
        (x2 - radius, y1 + radius, -90),
        (x2 - radius, y2 - radius, 0),
        (x1 + radius, y2 - radius, 90),
        (x1 + radius, y1 + radius, 180)
    )
    for center_x, center_y, start_angle in corners:
        for step in range(5):
            angle = math.radians(start_angle + step * 22.5)
            points.extend((
                center_x + radius * math.cos(angle),
                center_y + radius * math.sin(angle)
            ))
    return tuple(points)


def _button_text_color(widget, background, requested_color):

    if requested_color != theme.TEXT_LIGHT:
        return requested_color

    try:
        channels = [value / 65535 for value in widget.winfo_rgb(background)]
    except tk.TclError:
        return requested_color

    linear_channels = [
        channel / 12.92
        if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    luminance = (
        0.2126 * linear_channels[0]
        + 0.7152 * linear_channels[1]
        + 0.0722 * linear_channels[2]
    )
    return theme.TEXT_PRIMARY if luminance > 0.20 else theme.TEXT_LIGHT


class ScrollableFrame(tk.Frame):

    def __init__(self, master, bg=theme.BACKGROUND):

        super().__init__(master, bg=bg)
        self.canvas = tk.Canvas(
            self,
            bg=bg,
            bd=0,
            highlightthickness=0,
            yscrollincrement=30
        )
        self.scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview
        )
        self.content = tk.Frame(self.canvas, bg=bg)
        self._content_id = self.canvas.create_window(
            0,
            0,
            anchor="nw",
            window=self.content
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self._scrollbar_sync_pending = False
        self.content.bind("<Configure>", self._update_scroll_region, add="+")
        self.canvas.bind("<Configure>", self._resize_content, add="+")
        self.canvas.pack(side="left", fill="both", expand=True)

    def _resize_content(self, event):

        self.canvas.itemconfigure(self._content_id, width=event.width)
        self._schedule_scrollbar_sync()

    def _update_scroll_region(self, event=None):

        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self._schedule_scrollbar_sync()

    def _schedule_scrollbar_sync(self):

        if self._scrollbar_sync_pending:
            return

        self._scrollbar_sync_pending = True
        self.after_idle(self._sync_scrollbar)

    def _sync_scrollbar(self):

        self._scrollbar_sync_pending = False
        bounds = self.canvas.bbox(self._content_id)
        if bounds is None or self.canvas.winfo_height() <= 1:
            return

        content_height = bounds[3] - bounds[1]
        needs_scrollbar = content_height > self.canvas.winfo_height() + 1
        is_visible = self.scrollbar.winfo_manager() == "pack"

        if needs_scrollbar and not is_visible:
            self.scrollbar.pack(side="right", fill="y")
        elif not needs_scrollbar and is_visible:
            self.scrollbar.pack_forget()


class RoundedPanel(tk.Canvas):

    def __init__(
        self,
        master,
        bg=theme.CARD_BACKGROUND,
        padx=18,
        pady=18,
        radius=8,
        highlightbackground=None,
        highlightthickness=1,
        hoverable=False
    ):
        try:
            outer_bg = master.cget("bg")
        except tk.TclError:
            outer_bg = theme.BACKGROUND

        super().__init__(
            master,
            bg=outer_bg,
            bd=0,
            highlightthickness=0,
            width=200,
            height=120
        )
        self.surface = bg
        self.hoverable = hoverable
        self._outer_background = outer_bg
        self.radius = radius
        self.inset = max(8, radius + 1)
        self._lift_reserve = 6 if hoverable else 0
        self._lift = 0
        self._hover_after_id = None
        self.outline = highlightbackground or theme.GLASS_BORDER
        self.outline_width = max(1, highlightthickness)
        self._hovered = False
        self.content = tk.Frame(
            self,
            bg=self.surface,
            padx=padx,
            pady=pady
        )
        self._shadow_idle_color = theme.GLASS_SHADOW
        self._shadow_hover_color = theme.glass_tint(
            theme.GLASS_SIDEBAR,
            self._outer_background,
            0.45
        )
        self._shadow_id = self.create_polygon(
            0,
            0,
            0,
            0,
            smooth=True,
            splinesteps=16,
            fill=theme.GLASS_SHADOW,
            outline=""
        )
        self._surface_id = self.create_polygon(
            0,
            0,
            0,
            0,
            smooth=True,
            splinesteps=16,
            fill=self.surface,
            outline=self.outline,
            width=self.outline_width
        )
        self._highlight_id = self.create_line(
            0,
            0,
            0,
            0,
            fill=theme.GLASS_HIGHLIGHT,
            width=1
        )
        self._content_id = self.create_window(
            self.inset,
            self.inset,
            anchor="nw",
            window=self.content
        )
        self.bind("<Configure>", self._resize_content, add="+")
        self.content.bind("<Configure>", self._schedule_size, add="+")
        self._size_after_id = None
        self.after_idle(self._update_requested_size)
        self.bind("<Destroy>", self._cancel_hover_animation, add="+")

    def _cancel_hover_animation(self, event):

        if event.widget is not self or self._hover_after_id is None:
            return
        self.after_cancel(self._hover_after_id)
        self._hover_after_id = None

    def _resize_content(self, event):

        self._layout_items(event.width, event.height)

    def _layout_items(self, width, height):

        content_width = max(1, width - 2 * self.inset)
        content_height = max(
            1,
            height - 2 * self.inset - self._lift_reserve
        )
        lift = self._lift
        self.coords(
            self._shadow_id,
            *_rounded_points(
                1,
                3 + self._lift_reserve,
                max(2, width - 1),
                max(4, height - 1),
                self.radius
            )
        )
        self.coords(
            self._surface_id,
            *_rounded_points(
                1,
                1 + self._lift_reserve - lift,
                max(2, width - 1),
                max(2, height - 3 - lift),
                self.radius
            )
        )
        self.coords(
            self._highlight_id,
            self.radius + 2,
            2 + self._lift_reserve - lift,
            max(self.radius + 2, width - self.radius - 2),
            2 + self._lift_reserve - lift
        )
        self.coords(
            self._content_id,
            self.inset,
            self.inset + self._lift_reserve - lift
        )
        self.itemconfigure(
            self._content_id,
            width=content_width,
            height=content_height
        )

    def _schedule_size(self, event=None):

        if self._size_after_id is None:
            self._size_after_id = self.after_idle(
                self._update_requested_size
            )

    def _update_requested_size(self):

        self._size_after_id = None
        width = self.content.winfo_reqwidth() + 2 * self.inset
        height = (
            self.content.winfo_reqheight()
            + 2 * self.inset
            + self._lift_reserve
        )
        self.configure(width=max(120, width), height=max(80, height))

    def set_hovered(self, hovered):

        if not self.hoverable or self._hovered == hovered:
            return

        self._hovered = hovered
        if self._hover_after_id is not None:
            self.after_cancel(self._hover_after_id)
            self._hover_after_id = None

        start_lift = self._lift
        target_lift = self._lift_reserve if hovered else 0
        steps = 6

        def animate_step(step):

            self._hover_after_id = None
            if not self.winfo_exists():
                return

            self._lift = round(
                start_lift
                + (target_lift - start_lift) * step / steps
            )
            shadow_amount = self._lift / self._lift_reserve
            self.itemconfigure(
                self._shadow_id,
                fill=theme.glass_tint(
                    self._shadow_hover_color,
                    self._shadow_idle_color,
                    shadow_amount
                )
            )
            self._layout_items(self.winfo_width(), self.winfo_height())

            if step < steps:
                self._hover_after_id = self.after(
                    42,
                    lambda: animate_step(step + 1)
                )

        animate_step(1)


class RoundedButton(tk.Canvas):

    def __init__(
        self,
        master,
        text="",
        font=("Segoe UI", 10),
        bg=theme.PRIMARY,
        fg=theme.TEXT_LIGHT,
        activebackground=theme.SECONDARY,
        activeforeground=theme.TEXT_LIGHT,
        command=None,
        padx=18,
        pady=9,
        cursor="hand2",
        anchor="center",
        relief="flat",
        **kwargs
    ):
        try:
            outer_bg = master.cget("bg")
        except tk.TclError:
            outer_bg = theme.BACKGROUND

        super().__init__(
            master,
            bg=outer_bg,
            bd=0,
            highlightthickness=0,
            cursor=cursor,
            width=160,
            height=40
        )
        self._fill = theme.glass_tint(bg, outer_bg)
        self._active_fill = theme.glass_tint(
            activebackground,
            outer_bg,
            opacity=0.32
        )
        self._outer_background = outer_bg
        button_foreground = _button_text_color(self, self._fill, fg)
        button_active_foreground = _button_text_color(
            self,
            self._active_fill,
            activeforeground
        )
        self._relief = relief
        self._radius = 6
        self._inset_x = 7
        self._inset_y = 4
        self._lift_reserve = 2
        self._lift = 0
        self._shadow_color = theme.GLASS_SHADOW
        self._shadow_id = self.create_polygon(
            0,
            0,
            0,
            0,
            smooth=True,
            splinesteps=16,
            fill=self._shadow_color,
            outline=""
        )
        self._shape_id = self.create_polygon(
            0,
            0,
            0,
            0,
            smooth=True,
            splinesteps=16,
            fill=self._fill,
            outline=theme.GLASS_BORDER,
            width=1
        )
        self._button = tk.Button(
            self,
            text=text,
            font=font,
            bg=self._fill,
            fg=button_foreground,
            activebackground=self._active_fill,
            activeforeground=button_active_foreground,
            command=command,
            padx=padx,
            pady=pady,
            cursor=cursor,
            anchor=anchor,
            relief="flat",
            bd=0,
            highlightthickness=0,
            takefocus=True
        )
        self._window_id = self.create_window(
            self._inset_x,
            self._inset_y,
            anchor="nw",
            window=self._button
        )
        self.bind("<Configure>", self._resize_button, add="+")
        self._button.bind(
            "<Enter>",
            lambda event: self.event_generate("<Enter>"),
            add="+"
        )
        self._button.bind(
            "<Leave>",
            lambda event: self.event_generate("<Leave>"),
            add="+"
        )
        self._update_requested_size()

    def _resize_button(self, event):

        width = event.width if event is not None else self.winfo_width()
        height = event.height if event is not None else self.winfo_height()
        lift = self._lift
        self.coords(
            self._shadow_id,
            *_rounded_points(
                1,
                3 + self._lift_reserve,
                max(2, width - 1),
                max(4, height - 1),
                self._radius
            )
        )
        self.coords(
            self._shape_id,
            *_rounded_points(
                1,
                1 + self._lift_reserve - lift,
                max(2, width - 1),
                max(2, height - 3 - lift),
                self._radius
            )
        )
        self.coords(
            self._window_id,
            self._inset_x,
            self._inset_y + self._lift_reserve - lift
        )
        self.itemconfigure(
            self._window_id,
            width=max(1, width - 2 * self._inset_x),
            height=max(
                1,
                height - 2 * self._inset_y - self._lift_reserve
            )
        )

    def _update_requested_size(self):

        self._button.update_idletasks()
        width = self._button.winfo_reqwidth() + 2 * self._inset_x
        height = (
            self._button.winfo_reqheight()
            + 2 * self._inset_y
            + self._lift_reserve
        )
        self.configure(width=width, height=height)

    def set_lift(self, amount, shadow_color=None):

        self._lift = max(0, min(self._lift_reserve, amount))
        if shadow_color is not None:
            self._shadow_color = shadow_color
        self.itemconfigure(self._shadow_id, fill=self._shadow_color)
        self._resize_button(None)

    def configure(self, cnf=None, **kwargs):

        if isinstance(cnf, str):
            return self.cget(cnf)
        if cnf:
            kwargs.update(cnf)

        canvas_options = {}
        button_options = {}
        for key, value in kwargs.items():
            option = {
                "bg": "background",
                "fg": "foreground"
            }.get(key, key)

            if option == "background":
                self._fill = value
                button_options["background"] = value
            elif option == "activebackground":
                self._active_fill = value
                button_options[option] = value
            elif option == "relief":
                self._relief = value
            elif option in {
                "text",
                "foreground",
                "activeforeground",
                "command",
                "font",
                "padx",
                "pady",
                "cursor",
                "anchor",
                "state"
            }:
                button_options[option] = value
                if option == "cursor":
                    canvas_options[option] = value
            else:
                canvas_options[key] = value

        if button_options:
            if (
                "state" in button_options
                and "cursor" not in button_options
            ):
                cursor = (
                    "arrow"
                    if button_options["state"] == tk.DISABLED
                    else "hand2"
                )
                button_options["cursor"] = cursor
                canvas_options["cursor"] = cursor
            self._button.configure(**button_options)
        result = super().configure(**canvas_options) if canvas_options else None
        self.itemconfigure(self._shape_id, fill=self._fill)
        if "text" in button_options or "font" in button_options:
            self._update_requested_size()
        return result

    config = configure

    def cget(self, key):

        option = {
            "bg": "background",
            "fg": "foreground"
        }.get(key, key)
        if option == "background":
            return self._fill
        if option == "activebackground":
            return self._active_fill
        if option == "relief":
            return self._relief
        if option in {
            "text",
            "foreground",
            "activeforeground",
            "command",
            "font",
            "padx",
            "pady",
            "cursor",
            "anchor",
            "state"
        }:
            return self._button.cget(option)
        return super().cget(key)


class RoundedField(tk.Canvas):

    def __init__(self, master, widget_class, **kwargs):

        try:
            outer_bg = master.cget("bg")
        except tk.TclError:
            outer_bg = theme.BACKGROUND

        super().__init__(
            master,
            bg=outer_bg,
            bd=0,
            highlightthickness=0,
            highlightbackground=theme.ACCENT,
            highlightcolor=theme.ACCENT,
            width=200,
            height=34
        )
        self._field_background = theme.GLASS_FIELD
        self._outline = theme.GLASS_BORDER
        self._radius = 5
        self._inset_x = 8
        self._inset_y = 4
        self._widget_class = widget_class
        self._focused = False
        self._style_name = (
            f"Rounded{id(self)}.TEntry"
            if widget_class is ttk.Entry
            else f"Rounded{id(self)}.TCombobox"
        )
        self._style = ttk.Style(self)
        if widget_class is ttk.Entry:
            self._style.configure(
                self._style_name,
                borderwidth=0,
                relief="flat",
                padding=(7, 4),
                fieldbackground=self._field_background,
                foreground=theme.TEXT_PRIMARY,
                lightcolor=self._field_background,
                darkcolor=self._field_background
            )
        else:
            self._style.configure(
                self._style_name,
                borderwidth=0,
                relief="flat",
                padding=(7, 3),
                fieldbackground=self._field_background,
                background=self._field_background,
                foreground=theme.TEXT_PRIMARY,
                arrowcolor=theme.PRIMARY
            )
            self._style.map(
                self._style_name,
                fieldbackground=[
                    ("readonly", self._field_background),
                    ("focus", self._field_background)
                ],
                foreground=[
                    ("readonly", theme.TEXT_PRIMARY),
                    ("focus", theme.TEXT_PRIMARY)
                ]
            )

        kwargs["style"] = self._style_name
        if widget_class is ttk.Combobox:
            kwargs.setdefault("cursor", "hand2")
        self._field = widget_class(self, **kwargs)
        self._shape_id = self.create_polygon(
            0,
            0,
            0,
            0,
            smooth=True,
            splinesteps=16,
            fill=self._field_background,
            outline=self._outline,
            width=1
        )
        self._window_id = self.create_window(
            self._inset_x,
            self._inset_y,
            anchor="nw",
            window=self._field
        )
        tk.Canvas.bind(self, "<Configure>", self._resize_field, add="+")
        self._field.bind(
            "<FocusIn>",
            lambda event: self._set_focused(True),
            add="+"
        )
        self._field.bind(
            "<FocusOut>",
            lambda event: self._set_focused(False),
            add="+"
        )
        self._update_requested_size()

    def _resize_field(self, event):

        self.coords(
            self._shape_id,
            *_rounded_points(
                1,
                1,
                max(2, event.width - 1),
                max(2, event.height - 1),
                self._radius
            )
        )
        self.coords(self._window_id, self._inset_x, self._inset_y)
        self.itemconfigure(
            self._window_id,
            width=max(1, event.width - 2 * self._inset_x),
            height=max(1, event.height - 2 * self._inset_y)
        )

    def _update_requested_size(self):

        self._field.update_idletasks()
        width = self._field.winfo_reqwidth() + 2 * self._inset_x
        height = self._field.winfo_reqheight() + 2 * self._inset_y
        self.configure(width=width, height=height)

    def _set_focused(self, focused):

        if self._focused == focused:
            return

        self._focused = focused
        self.itemconfigure(
            self._shape_id,
            fill=self._field_background,
            outline=theme.SECONDARY if focused else self._outline
        )
        self.configure(highlightthickness=4 if focused else 0)

    def bind(self, sequence=None, func=None, add=None):

        return self._field.bind(sequence, func, add)

    def cget(self, key):

        return self._field.cget(key)

    def __getitem__(self, key):

        return self._field[key]

    def __setitem__(self, key, value):

        self._field[key] = value

    def delete(self, *args):

        return self._field.delete(*args)

    def insert(self, *args):

        return self._field.insert(*args)

    def get(self):

        return self._field.get()

    def set(self, value):

        return self._field.set(value)

    def focus_set(self):

        return self._field.focus_set()


class RoundedEntry(RoundedField):

    def __init__(self, master, **kwargs):
        super().__init__(master, ttk.Entry, **kwargs)


class RoundedCombobox(RoundedField):

    def __init__(self, master, **kwargs):
        super().__init__(master, ttk.Combobox, **kwargs)
