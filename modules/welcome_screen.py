import ctypes
import math
import os
import sqlite3
import sys
import time
import tkinter as tk
import tkinter.font as tkfont
import warnings
from pathlib import Path
from tkinter import messagebox

from database.admin_auth import (
    create_admin_account,
    has_admin_account,
    verify_admin_credentials
)
from utils import theme


_ROUTES = (
    (
        (-20, 700), (260, 700), (360, 600), (700, 600),
        (800, 500), (1100, 500), (1200, 400), (1460, 400)
    ),
    (
        (-20, 250), (200, 250), (300, 350), (560, 350),
        (660, 250), (980, 250), (1080, 150), (1460, 150)
    ),
    (
        (300, 940), (300, 760), (420, 640), (420, 420),
        (560, 280), (560, -40)
    )
)
_REGULAR_STOPS = (
    ((260, 700), (360, 600), (800, 500), (1100, 500), (1200, 400)),
    ((200, 250), (300, 350), (560, 350), (980, 250), (1080, 150)),
    ((300, 760), (420, 640), (420, 420), (560, 280))
)
_KEY_STOPS = (
    (700, 600, "CITY CENTRE"),
    (660, 250, "MEJESTIC")
)


def _register_welcome_fonts():

    if sys.platform != "win32":
        return []

    font_directory = Path(__file__).resolve().parent.parent / "assets" / "fonts"
    register_font = ctypes.windll.gdi32.AddFontResourceExW
    register_font.argtypes = (ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_void_p)
    register_font.restype = ctypes.c_int
    loaded_paths = []
    for filename in (
        "BricolageGrotesque-Regular.ttf",
        "BricolageGrotesque-Bold.ttf",
        "Manrope-Regular.ttf",
        "Manrope-Bold.ttf"
    ):
        font_path = font_directory / filename
        if not font_path.is_file():
            warnings.warn(
                f"Bundled Welcome font is missing: {font_path}",
                RuntimeWarning
            )
            continue
        if register_font(str(font_path), 0x10, None):
            loaded_paths.append(str(font_path))
        else:
            warnings.warn(
                f"Unable to register bundled Welcome font: {font_path}",
                RuntimeWarning
            )
    return loaded_paths


def _rounded_points(x1, y1, x2, y2, radius):

    radius = min(radius, (x2 - x1) / 2, (y2 - y1) / 2)
    return (
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1
    )


def _blend(first, second, amount):

    start = tuple(int(first[index:index + 2], 16) for index in (1, 3, 5))
    end = tuple(int(second[index:index + 2], 16) for index in (1, 3, 5))
    channels = tuple(
        round(start[index] * (1 - amount) + end[index] * amount)
        for index in range(3)
    )
    return "#{:02X}{:02X}{:02X}".format(*channels)


def _oriented_rectangle(center_x, center_y, tangent_x, tangent_y, half_length, half_width):

    normal_x = -tangent_y
    normal_y = tangent_x
    return (
        center_x - tangent_x * half_length - normal_x * half_width,
        center_y - tangent_y * half_length - normal_y * half_width,
        center_x + tangent_x * half_length - normal_x * half_width,
        center_y + tangent_y * half_length - normal_y * half_width,
        center_x + tangent_x * half_length + normal_x * half_width,
        center_y + tangent_y * half_length + normal_y * half_width,
        center_x - tangent_x * half_length + normal_x * half_width,
        center_y - tangent_y * half_length + normal_y * half_width
    )


def _reduced_motion_enabled():

    if sys.platform != "win32":
        return os.environ.get("SCHOOL_TRANSIT_REDUCED_MOTION") == "1"

    enabled = ctypes.c_int()
    try:
        result = ctypes.windll.user32.SystemParametersInfoW(
            0x1042,
            0,
            ctypes.byref(enabled),
            0
        )
    except (AttributeError, OSError):
        return False
    return bool(result) and not bool(enabled.value)


class WelcomeScreen(tk.Canvas):

    def __init__(self, master, on_admin_success):

        super().__init__(
            master,
            bg=theme.WELCOME_FOREST_OLIVE,
            bd=0,
            highlightthickness=0,
            takefocus=False
        )
        self.root = master
        self.on_admin_success = on_admin_success
        self.reduced_motion = _reduced_motion_enabled()
        self.mode = "choose"
        self._entry_fields = []
        self._entry_windows = []
        self._login_error = ""
        self._login_error_type = ""
        self._active_hover = None
        self._hover_animations = {}
        self._canvas_lifts = {}
        self._hover_idle_after_ids = set()
        self._button_shadow_colors = {}
        self._pressed_button = None
        self._ticker_after = None
        self._motion_after = None
        self._entrance_after = None
        self._ticker_x = 0.0
        self._ticker_group_width = 1
        self._started_at = time.monotonic()
        self._last_size = (0, 0)
        self._animate_next_draw = True
        self._map_bus_items = []
        self._pulse_items = []
        self._map_paths = []
        self._entrance_step = 0
        self._ticker_font = None
        self._registered_font_paths = _register_welcome_fonts()
        self._ticker_text = (
            "ROUTE 01   |   CITY CENTRE   |   MEJESTIC   |   "
            "ROUTE 02   |   ROUTE 03   |   ALL ABOARD   |   "
        )
        self._font_families = set(tkfont.families(master))
        self.bind("<Configure>", self._on_configure, add="+")
        self.bind("<Motion>", self._on_motion, add="+")
        self.bind("<Leave>", self._on_canvas_leave, add="+")
        self.bind("<Button-1>", self._on_click, add="+")
        self.bind("<ButtonRelease-1>", self._on_release, add="+")
        self.bind("<Destroy>", self._cancel_hover_work, add="+")
        self.bind("<MouseWheel>", self._on_mousewheel, add="+")
        self.bind("<Button-4>", self._on_mousewheel, add="+")
        self.bind("<Button-5>", self._on_mousewheel, add="+")
        self._ticker_font = tkfont.Font(
            root=master,
            family=self._font_family(theme.WELCOME_BODY_FONT),
            size=theme.WELCOME_TICKER_SIZE,
            weight="bold"
        )
        if not self.reduced_motion:
            self._ticker_after = self.after(33, self._animate_ticker)
            self._motion_after = self.after(33, self._animate_motion)

    def _font_family(self, family):

        if family in self._font_families:
            return family
        return theme.WELCOME_FONT_FALLBACK

    def _font(self, family, size, weight=None):

        resolved = self._font_family(family)
        return (resolved, size, weight) if weight else (resolved, size)

    def _on_configure(self, event):

        if event.widget is not self:
            return
        size = (event.width, event.height)
        if size == self._last_size or event.width < 2 or event.height < 2:
            return
        self._last_size = size
        self._draw()

    def _draw(self):

        focused_entry = self.focus_get()
        self._cancel_hover_work()
        self._button_shadow_colors.clear()
        self._pressed_button = None
        self._active_hover = None
        for entry in self._entry_fields:
            entry["window"] = None
        self.delete("all")
        self._map_bus_items.clear()
        self._pulse_items.clear()
        width = max(self.winfo_width(), 1)
        height = max(self.winfo_height(), 1)
        ticker_top = height - 46
        page_width = min(width, 1440)
        page_x = (width - page_width) / 2

        self._draw_map(width, ticker_top)
        self._draw_header(page_x, page_width)

        compact = page_width < 1000
        if compact:
            self._draw_compact_hero_copy(24, 96, min(width - 48, 560))
            self._draw_active_panel(
                24,
                204,
                width - 48,
                max(394, ticker_top - 220)
            )
        else:
            left_x = page_x + 36
            left_width = min(560, max(400, int(page_width * 0.41)))
            right_x = page_x + max(
                36 + left_width + 48,
                int(page_width * 0.51)
            )
            right_width = min(
                600,
                max(340, page_width - (right_x - page_x) - 36)
            )
            self._draw_hero_copy(left_x, 142, left_width)
            self._draw_active_panel(
                right_x,
                132,
                right_width,
                ticker_top - 148
            )

        self._draw_ticker(width, height)
        if focused_entry in [field["entry"] for field in self._entry_fields]:
            focused_entry.focus_set()
        if self._animate_next_draw and not self.reduced_motion:
            self._animate_next_draw = False
            self._entrance_step = 0
            self.move("content", 0, 26)
            self._entrance_after = self.after(1, self._animate_entrance)

    def _cancel_hover_work(self, event=None):

        if event is not None and event.widget is not self:
            return
        for animation in self._hover_animations.values():
            if animation["after_id"] is not None:
                self.after_cancel(animation["after_id"])
        for after_id in self._hover_idle_after_ids:
            self.after_cancel(after_id)
        self._hover_animations.clear()
        self._hover_idle_after_ids.clear()
        self._canvas_lifts.clear()

    def _draw_compact_hero_copy(self, x, y, max_width):

        self._round_rect(
            x,
            y,
            x + 122,
            y + 30,
            15,
            theme.WELCOME_MARIGOLD,
            tags=("content",)
        )
        self.create_text(
            x + 61,
            y + 15,
            text="ALL ABOARD",
            fill=theme.WELCOME_INK,
            font=self._font(theme.WELCOME_BODY_FONT, 8, "bold"),
            tags=("content",)
        )
        self.create_text(
            x,
            y + 40,
            text="Every stop. Every student. On time.",
            fill=theme.WELCOME_CREAM,
            font=self._font(theme.WELCOME_DISPLAY_FONT, 22, "bold"),
            width=max_width,
            anchor="nw",
            tags=("content",)
        )

    def _draw_map(self, width, usable_height):

        map_height = usable_height
        scale = max(width / 1440, map_height / 900)
        offset_x = (width - 1440 * scale) / 2
        offset_y = (map_height - 900 * scale) / 2

        def point(position):
            return (
                offset_x + position[0] * scale,
                offset_y + position[1] * scale
            )

        for route in _ROUTES:
            coordinates = [
                value
                for position in route
                for value in point(position)
            ]
            self.create_line(
                *coordinates,
                fill=theme.WELCOME_ROAD_OLIVE,
                width=max(16, 22 * scale),
                capstyle=tk.BUTT,
                joinstyle="miter",
                tags=("map",)
            )
            self.create_line(
                *coordinates,
                fill=theme.WELCOME_OLIVE,
                width=max(2, 3 * scale),
                dash=(
                    max(1, round(4 * scale)),
                    max(1, round(10 * scale))
                ),
                capstyle=tk.BUTT,
                joinstyle="miter",
                tags=("map",)
            )

        for route_stops in _REGULAR_STOPS:
            for position in route_stops:
                x, y = point(position)
                self.create_oval(
                    x - 8 * scale, y - 8 * scale,
                    x + 8 * scale, y + 8 * scale,
                    fill=theme.WELCOME_FOREST_OLIVE,
                    outline=theme.WELCOME_MOSS,
                    width=max(2, 3 * scale),
                    tags=("map",)
                )

        for x, y, label in _KEY_STOPS:
            cx, cy = point((x, y))
            ring = self.create_oval(
                cx - 11 * scale, cy - 11 * scale,
                cx + 11 * scale, cy + 11 * scale,
                fill="",
                outline=theme.WELCOME_MARIGOLD,
                width=max(2, 2 * scale),
                tags=("map", "pulse")
            )
            self._pulse_items.append((ring, cx, cy, scale))
            self.create_oval(
                cx - 8 * scale, cy - 8 * scale,
                cx + 8 * scale, cy + 8 * scale,
                fill=theme.WELCOME_FOREST_OLIVE,
                outline=theme.WELCOME_MARIGOLD,
                width=max(2, 3 * scale),
                tags=("map",)
            )

        paths = []
        for route in _ROUTES:
            lengths = [
                math.hypot(
                    end[0] - start[0],
                    end[1] - start[1]
                )
                for start, end in zip(route, route[1:])
            ]
            paths.append((route, lengths, sum(lengths)))
        self._map_paths = paths
        for _ in _ROUTES:
            body = self.create_polygon(
                0, 0, 0, 0, 0, 0, 0, 0,
                fill=theme.WELCOME_MARIGOLD,
                outline=theme.WELCOME_INK,
                width=max(1, round(scale)),
                tags=("map",)
            )
            windows = self.create_polygon(
                0, 0, 0, 0, 0, 0, 0, 0,
                fill=theme.WELCOME_INK,
                outline="",
                tags=("map",)
            )
            wheels = tuple(
                self.create_oval(
                    0, 0, 0, 0,
                    fill=theme.WELCOME_INK,
                    outline="",
                    tags=("map",)
                )
                for _ in range(4)
            )
            self._map_bus_items.append((body, windows, *wheels))

        for width_factor, height_factor, stipple in (
            (0.94, 0.96, "gray25"),
            (0.76, 0.82, "gray50"),
            (0.56, 0.66, "gray75")
        ):
            scrim_width = width * width_factor
            scrim_height = map_height * height_factor
            center_x = width * 0.25
            center_y = map_height * 0.48
            self.create_oval(
                center_x - scrim_width / 2,
                center_y - scrim_height / 2,
                center_x + scrim_width / 2,
                center_y + scrim_height / 2,
                fill=theme.WELCOME_FOREST_OLIVE,
                outline="",
                stipple=stipple,
                tags=("map",)
            )
        for label, position in (
            ("ROUTE 01", (40, 738)),
            ("ROUTE 02", (570, 300)),
            ("ROUTE 03", (324, 820)),
            ("CITY CENTRE", (600, 640)),
            ("MEJESTIC", (645, 200))
        ):
            x, y = point(position)
            self.create_text(
                x, y,
                text=label,
                fill=theme.WELCOME_SAGE,
                font=self._font(theme.WELCOME_BODY_FONT, 10, "bold"),
                anchor="nw",
                tags=("map",)
            )
        self.tag_lower("map")

    def _draw_header(self, x, width):

        self.create_polygon(
            *_rounded_points(x + 36, 24, x + 88, 76, 16),
            fill=theme.WELCOME_MARIGOLD,
            outline="",
            smooth=True,
            splinesteps=16,
            tags=("content",)
        )
        self.create_rectangle(
            x + 49, 44, x + 75, 58,
            fill=theme.WELCOME_INK,
            outline="",
            tags=("content",)
        )
        self.create_rectangle(
            x + 53, 46, x + 61, 52,
            fill=theme.WELCOME_MARIGOLD,
            outline="",
            tags=("content",)
        )
        self.create_rectangle(
            x + 63, 46, x + 71, 52,
            fill=theme.WELCOME_MARIGOLD,
            outline="",
            tags=("content",)
        )
        self.create_oval(
            x + 53, 56, x + 59, 62,
            fill=theme.WELCOME_INK,
            outline="",
            tags=("content",)
        )
        self.create_oval(
            x + 66, 56, x + 72, 62,
            fill=theme.WELCOME_INK,
            outline="",
            tags=("content",)
        )
        self.create_text(
            x + 100, 38,
            text="School Transit",
            fill=theme.WELCOME_CREAM,
            font=self._font(theme.WELCOME_DISPLAY_FONT, 18, "bold"),
            anchor="w",
            tags=("content",)
        )
        self.create_text(
            x + 101, 61,
            text="TRANSPORT MANAGEMENT",
            fill=theme.WELCOME_SOFT_SAGE,
            font=self._font(theme.WELCOME_BODY_FONT, 7, "bold"),
            anchor="w",
            tags=("content",)
        )
        chip_width = 236
        chip_x = x + width - 36 - chip_width
        self._round_rect(
            chip_x,
            31,
            x + width - 36,
            68,
            18,
            theme.WELCOME_DARK_OLIVE,
            outline=theme.WELCOME_OLIVE,
            tags=("content",)
        )
        self.create_text(
            chip_x + chip_width / 2,
            49,
            text="Students don't need to log in",
            fill=theme.WELCOME_SAGE,
            font=self._font(theme.WELCOME_BODY_FONT, 8, "bold"),
            tags=("content",)
        )

    def _draw_hero_copy(self, x, y, max_width):

        headline_size = min(
            theme.WELCOME_HEADLINE_SIZE,
            max(42, int(max_width / 9.3))
        )
        self._round_rect(
            x,
            y,
            x + 122,
            y + 30,
            15,
            theme.WELCOME_MARIGOLD,
            tags=("content",)
        )
        self.create_text(
            x + 61,
            y + 15,
            text="ALL ABOARD",
            fill=theme.WELCOME_INK,
            font=self._font(theme.WELCOME_BODY_FONT, 8, "bold"),
            tags=("content",)
        )

        headline_font = tkfont.Font(
            root=self,
            family=self._font_family(theme.WELCOME_DISPLAY_FONT),
            size=headline_size,
            weight="bold"
        )
        headline_y = y + 48
        line_height = headline_font.metrics("linespace") + 12
        last_line_id = None
        for index, (text, color) in enumerate((
            ("Every stop.", theme.WELCOME_CREAM),
            ("Every student.", theme.WELCOME_MARIGOLD),
            ("On time.", theme.WELCOME_CREAM)
        )):
            last_line_id = self.create_text(
                x,
                headline_y + index * line_height,
                text=text,
                fill=color,
                font=headline_font,
                anchor="nw",
                tags=("content",)
            )

        intro = (
            "Find your route, your stop and your bus in seconds. "
            "Pick where you're headed and we'll take you there."
        )
        last_line_box = self.bbox(last_line_id)
        intro_y = last_line_box[3] + 22 if last_line_box else (
            headline_y + 3 * line_height + 22
        )
        intro_id = self.create_text(
            x,
            intro_y,
            text=intro,
            fill=theme.WELCOME_SAGE,
            font=self._font(theme.WELCOME_BODY_FONT, 11),
            width=max_width - 12,
            justify="left",
            anchor="nw",
            tags=("content",)
        )
        intro_box = self.bbox(intro_id)
        pills_y = intro_box[3] + 20 if intro_box else intro_y + 60
        self._draw_pill(x, pills_y, "route", "Routes", 104)
        self._draw_pill(x + 112, pills_y, "pin", "Bus stops", 125)
        self._draw_pill(x + 245, pills_y, "bus", "Available buses", 164)

    def _draw_pill(self, x, y, icon, text, width):

        tag = f"feature-{text.replace(' ', '-')}"
        self._round_rect(
            x, y, x + width, y + 38, 19,
            theme.WELCOME_DARK_OLIVE,
            outline=theme.WELCOME_OLIVE,
            tags=("content", tag, f"{tag}-surface")
        )
        self._draw_pill_icon(icon, x + 18, y + 19, ("content", tag))
        self.create_text(
            x + 38, y + 19,
            text=text,
            fill=theme.WELCOME_CREAM,
            font=self._font(theme.WELCOME_BODY_FONT, 8, "bold"),
            anchor="w",
            tags=("content", tag)
        )

    def _draw_active_panel(self, x, y, panel_width, panel_height):

        if self.mode == "choose":
            gap = 14
            ticket_height = min(
                238,
                max(188, (panel_height - gap) // 2)
            )
            self._draw_ticket(
                "student",
                x,
                y,
                panel_width,
                ticket_height,
                fill=theme.WELCOME_CREAM,
                stub=theme.WELCOME_MARIGOLD,
                eyebrow="STUDENT PASS  |  VIEW ONLY",
                title="I'm a student",
                description=(
                    "See routes, bus stops and the buses available for you. "
                    "No login needed."
                ),
                button="Find my bus",
                stub_text="NO LOGIN NEEDED",
                dark=False
            )
            self._draw_ticket(
                "admin",
                x,
                y + ticket_height + gap,
                panel_width,
                ticket_height,
                fill=theme.WELCOME_DARK_OLIVE,
                stub=theme.WELCOME_OLIVE,
                eyebrow="ADMIN ACCESS  |  STAFF ONLY",
                title="I'm an admin",
                description=(
                    "Manage routes, stops, student allocation, fees "
                    "and bus passes."
                ),
                button="Admin sign in",
                stub_text="STAFF ONLY",
                dark=True
            )
        elif self.mode == "admin":
            self._draw_login(x, y, panel_width, panel_height)
        else:
            self._draw_student_placeholder(x, y, panel_width)

    def _draw_ticket(
        self,
        tag,
        x,
        y,
        width,
        height,
        *,
        fill,
        stub,
        eyebrow,
        title,
        description,
        button,
        stub_text,
        dark
    ):

        stub_x = x + width - theme.WELCOME_TICKET_STUB_WIDTH
        foreground = theme.WELCOME_CREAM if dark else theme.WELCOME_INK
        muted = theme.WELCOME_SOFT_SAGE if dark else theme.WELCOME_OLIVE_GREY
        shadow_tag = f"{tag}-shadow"
        card_tag = f"{tag}-card"
        button_tag = f"{tag}-button"
        self._round_rect(
            x + 2, y + 7, x + width - 2, y + height - 1,
            theme.WELCOME_TICKET_RADIUS,
            theme.WELCOME_ROAD_OLIVE,
            tags=(shadow_tag, card_tag, "content")
        )
        self._round_rect(
            x, y, x + width, y + height - 8,
            theme.WELCOME_TICKET_RADIUS,
            fill,
            outline=theme.WELCOME_OLIVE if dark else fill,
            tags=(card_tag, "content")
        )
        self.create_rectangle(
            stub_x,
            y + 1,
            x + width - 1,
            y + height - 8,
            fill=stub,
            outline="",
            tags=(card_tag, "content")
        )
        self.create_line(
            stub_x,
            y + 15,
            stub_x,
            y + height - 24,
            fill=theme.WELCOME_FOREST_OLIVE,
            width=2,
            dash=(1, 3),
            tags=(card_tag, "content")
        )
        for notch_y in (y, y + height - 8):
            self.create_oval(
                stub_x - 14,
                notch_y - 14,
                stub_x + 14,
                notch_y + 14,
                fill=theme.WELCOME_FOREST_OLIVE,
                outline="",
                tags=(card_tag, "content")
            )
        icon_x = stub_x + theme.WELCOME_TICKET_STUB_WIDTH / 2
        icon_y = y + height * 0.32
        if dark:
            self._draw_padlock_icon(
                icon_x,
                icon_y,
                40,
                theme.WELCOME_CREAM,
                theme.WELCOME_DARK_OLIVE,
                (card_tag, "content")
            )
        else:
            self._draw_bus_icon(
                icon_x,
                icon_y,
                46,
                30,
                fill=theme.WELCOME_INK,
                outline=theme.WELCOME_INK,
                window=stub,
                tags=(card_tag, "content")
            )
        self.create_text(
            icon_x,
            y + height * 0.7,
            text=stub_text,
            angle=90,
            fill=theme.WELCOME_CREAM if dark else theme.WELCOME_INK,
            font=self._font(theme.WELCOME_BODY_FONT, 7, "bold"),
            tags=(card_tag, "content")
        )
        content_x = x + 25
        self.create_text(
            content_x,
            y + 27,
            text=eyebrow,
            fill=muted,
            font=self._font(theme.WELCOME_BODY_FONT, 7, "bold"),
            anchor="nw",
            tags=(card_tag, "content")
        )
        title_id = self.create_text(
            content_x,
            y + 53,
            text=title,
            fill=foreground,
            font=self._font(
                theme.WELCOME_DISPLAY_FONT,
                min(26, max(20, int(width / 24))),
                "bold"
            ),
            anchor="nw",
            tags=(card_tag, "content")
        )
        title_box = self.bbox(title_id)
        description_y = title_box[3] + 12 if title_box else y + 101
        description_id = self.create_text(
            content_x,
            description_y,
            text=description,
            fill=muted,
            font=self._font(theme.WELCOME_BODY_FONT, 9),
            width=max(160, stub_x - content_x - 16),
            justify="left",
            anchor="nw",
            tags=(card_tag, "content")
        )
        description_box = self.bbox(description_id)
        preferred_button_y = (
            description_box[3] + 18
            if description_box
            else description_y + 36
        )
        button_y = min(preferred_button_y, y + height - 58)
        button_fill = (
            theme.WELCOME_DARK_OLIVE if dark else theme.WELCOME_MARIGOLD
        )
        button_text_color = (
            theme.WELCOME_CREAM if dark else theme.WELCOME_INK
        )
        button_right = min(stub_x - 15, content_x + 210)
        button_shadow = theme.glass_tint(
            theme.WELCOME_FOREST_OLIVE,
            theme.WELCOME_DARK_OLIVE if dark else theme.WELCOME_SAND,
            0.45
        )
        self._button_shadow_colors[button_tag] = button_shadow
        self._round_rect(
            content_x,
            button_y + 3,
            button_right,
            button_y + 45,
            21,
            button_shadow,
            tags=(f"{button_tag}-shadow", card_tag, "content")
        )
        self._round_rect(
            content_x,
            button_y,
            button_right,
            button_y + 42,
            21,
            button_fill,
            outline=theme.WELCOME_MOSS if dark else "",
            tags=(button_tag, f"{button_tag}-surface", card_tag, "content")
        )
        self.create_text(
            (content_x + button_right) / 2 - 7,
            button_y + 21,
            text=button,
            fill=button_text_color,
            font=self._font(theme.WELCOME_BODY_FONT, 9, "bold"),
            tags=(button_tag, f"{button_tag}-label", card_tag, "content")
        )
        self.create_line(
            button_right - 31,
            button_y + 21,
            button_right - 19,
            button_y + 21,
            fill=button_text_color,
            width=2,
            arrow=tk.LAST,
            tags=(button_tag, f"{button_tag}-label", card_tag, "content")
        )
        self.tag_bind(
            card_tag,
            "<Enter>",
            lambda event, name=card_tag: self._set_card_hover(name, True)
        )
        self.tag_bind(
            card_tag,
            "<Leave>",
            lambda event, name=card_tag: self._schedule_card_leave(name)
        )
        self.tag_bind(
            button_tag,
            "<Enter>",
            lambda event, name=button_tag: self._schedule_button_hover(name)
        )
        self.tag_bind(
            button_tag,
            "<Leave>",
            lambda event, name=button_tag: self._schedule_button_hover(name)
        )

    def _draw_bus_icon(
        self,
        center_x,
        center_y,
        width,
        height,
        *,
        fill,
        outline,
        window,
        tags
    ):

        left = center_x - width / 2
        top = center_y - height / 2
        right = center_x + width / 2
        bottom = center_y + height / 2
        self._round_rect(
            left,
            top,
            right,
            bottom,
            height * 0.2,
            fill,
            outline=outline,
            width=1,
            tags=tags
        )
        window_y1 = top + height * 0.18
        window_y2 = top + height * 0.58
        self.create_rectangle(
            left + width * 0.15,
            window_y1,
            center_x - width * 0.06,
            window_y2,
            fill=window,
            outline="",
            tags=tags
        )
        self.create_rectangle(
            center_x + width * 0.05,
            window_y1,
            right - width * 0.12,
            window_y2,
            fill=window,
            outline="",
            tags=tags
        )
        wheel_radius = max(1.5, height * 0.12)
        for wheel_x in (
            left + width * 0.27,
            right - width * 0.27
        ):
            self.create_oval(
                wheel_x - wheel_radius,
                bottom - wheel_radius,
                wheel_x + wheel_radius,
                bottom + wheel_radius,
                fill=outline,
                outline="",
                tags=tags
            )

    def _draw_padlock_icon(
        self,
        center_x,
        center_y,
        size,
        fill,
        keyhole,
        tags
    ):

        self.create_arc(
            center_x - size * 0.24,
            center_y - size * 0.42,
            center_x + size * 0.24,
            center_y + size * 0.12,
            start=0,
            extent=180,
            style=tk.ARC,
            outline=fill,
            width=max(2, size * 0.09),
            tags=tags
        )
        self._round_rect(
            center_x - size * 0.34,
            center_y - size * 0.08,
            center_x + size * 0.34,
            center_y + size * 0.42,
            size * 0.08,
            fill,
            tags=tags
        )
        self.create_oval(
            center_x - size * 0.06,
            center_y + size * 0.06,
            center_x + size * 0.06,
            center_y + size * 0.18,
            fill=keyhole,
            outline="",
            tags=tags
        )

    def _draw_pill_icon(self, icon, center_x, center_y, tags):

        color = theme.WELCOME_MARIGOLD
        if icon == "route":
            self.create_line(
                center_x - 7, center_y + 5,
                center_x - 1, center_y - 4,
                center_x + 7, center_y + 2,
                fill=color,
                width=2,
                capstyle=tk.ROUND,
                joinstyle="round",
                tags=tags
            )
            for dx, dy in ((-7, 5), (7, 2)):
                self.create_oval(
                    center_x + dx - 2,
                    center_y + dy - 2,
                    center_x + dx + 2,
                    center_y + dy + 2,
                    fill=theme.WELCOME_DARK_OLIVE,
                    outline=color,
                    width=2,
                    tags=tags
                )
        elif icon == "pin":
            self.create_polygon(
                center_x,
                center_y + 9,
                center_x - 7,
                center_y - 1,
                center_x - 6,
                center_y - 6,
                center_x,
                center_y - 9,
                center_x + 6,
                center_y - 6,
                center_x + 7,
                center_y - 1,
                fill=color,
                outline=color,
                smooth=True,
                tags=tags
            )
            self.create_oval(
                center_x - 2.5,
                center_y - 5.5,
                center_x + 2.5,
                center_y - 0.5,
                fill=theme.WELCOME_DARK_OLIVE,
                outline="",
                tags=tags
            )
        else:
            self._draw_bus_icon(
                center_x,
                center_y,
                19,
                13,
                fill=color,
                outline=color,
                window=theme.WELCOME_DARK_OLIVE,
                tags=tags
            )
    def _draw_student_placeholder(self, x, y, width):

        panel_height = 260
        self._round_rect(
            x, y, x + width, y + panel_height,
            20,
            theme.WELCOME_CREAM,
            outline=theme.WELCOME_SAND,
            tags=("content",)
        )
        self.create_text(
            x + 24, y + 24,
            text="STUDENT ROUTE FINDER",
            fill=theme.WELCOME_OLIVE_GREY,
            font=self._font(theme.WELCOME_BODY_FONT, 8, "bold"),
            anchor="nw",
            tags=("content",)
        )
        self.create_text(
            x + 24, y + 56,
            text="Find my bus",
            fill=theme.WELCOME_INK,
            font=self._font(theme.WELCOME_DISPLAY_FONT, 26, "bold"),
            anchor="nw",
            tags=("content",)
        )
        self.create_text(
            x + 24, y + 100,
            text=(
                "The student route finder is not available yet. Routes, "
                "stops and bus availability will appear here."
            ),
            fill=theme.WELCOME_OLIVE_GREY,
            font=self._font(theme.WELCOME_BODY_FONT, 10),
            width=width - 48,
            anchor="nw",
            justify="left",
            tags=("content",)
        )
        self._draw_button(
            "student-back",
            x + 24,
            y + panel_height - 65,
            min(210, width - 48),
            46,
            "Back to welcome",
            bg=theme.WELCOME_MARIGOLD,
            fg=theme.WELCOME_INK
        )

    def _draw_login(self, x, y, width, available_height):

        try:
            setup_required = not has_admin_account()
        except sqlite3.Error as error:
            setup_required = False
            self._login_error = f"Unable to check administrator account: {error}"
            self._login_error_type = "error"

        field_specs = [
            ("Username", "Admin username", ""),
            ("Password", "Password", "*")
        ]
        if setup_required:
            field_specs.append(("Confirm password", "Confirm password", "*"))
        self._ensure_login_fields(field_specs)

        compact = self.winfo_width() < 1000
        card_height = (
            max(394, available_height)
            if compact
            else min(
                552 if setup_required else 486,
                max(410, available_height)
            )
        )
        card_width = min(width, 590)
        card_x = x + (width - card_width) / 2
        card_y = y + max(0, (available_height - card_height) / 2)
        body_left = card_x + 26
        body_right = card_x + card_width - 26
        body_width = body_right - body_left

        self._round_rect(
            card_x + 3, card_y + 6, card_x + card_width - 3,
            card_y + card_height,
            22,
            theme.WELCOME_ROAD_OLIVE,
            tags=("content",)
        )
        self._round_rect(
            card_x, card_y, card_x + card_width,
            card_y + card_height - 8,
            22,
            theme.WELCOME_CREAM,
            outline=theme.WELCOME_SAND,
            tags=("content",)
        )
        self.create_rectangle(
            card_x + 1, card_y + 1,
            card_x + card_width - 1, card_y + 49,
            fill=theme.WELCOME_DARK_OLIVE,
            outline="",
            tags=("content",)
        )
        self.create_text(
            body_left,
            card_y + 25,
            text="BOARDING PASS  /  ADMIN",
            fill=theme.WELCOME_CREAM,
            font=self._font(theme.WELCOME_BODY_FONT, 8, "bold"),
            anchor="w",
            tags=("content",)
        )
        self._round_rect(
            card_x + card_width - 93,
            card_y + 11,
            card_x + card_width - 24,
            card_y + 39,
            14,
            theme.WELCOME_MARIGOLD,
            tags=("content",)
        )
        self.create_text(
            card_x + card_width - 58,
            card_y + 25,
            text="GATE A",
            fill=theme.WELCOME_INK,
            font=self._font(theme.WELCOME_BODY_FONT, 7, "bold"),
            tags=("content",)
        )

        title = "Create admin account" if setup_required else "Welcome back"
        intro = (
            "Set up the first administrator account to continue."
            if setup_required
            else "Sign in to manage the transport system."
        )
        self.create_text(
            body_left,
            card_y + (58 if compact else 67),
            text=title,
            fill=theme.WELCOME_INK,
            font=self._font(
                theme.WELCOME_DISPLAY_FONT,
                20 if compact else 24,
                "bold"
            ),
            anchor="nw",
            tags=("content",)
        )
        self.create_text(
            body_left,
            card_y + (86 if compact else 99),
            text=intro,
            fill=theme.WELCOME_OLIVE_GREY,
            font=self._font(theme.WELCOME_BODY_FONT, 8 if compact else 9),
            anchor="nw",
            tags=("content",)
        )

        first_field_y = card_y + (112 if compact else 125)
        row_gap = 56 if compact else 68
        for index, (label, _, _) in enumerate(field_specs):
            field_y = first_field_y + index * row_gap
            self.create_text(
                body_left,
                field_y,
                text=label,
                fill=theme.WELCOME_INK,
                font=self._font(theme.WELCOME_BODY_FONT, 8, "bold"),
                anchor="nw",
                tags=("content",)
            )
            field = self._entry_fields[index]
            input_y = field_y + (16 if compact else 18)
            input_height = 38 if compact else theme.WELCOME_INPUT_HEIGHT
            focused = field["entry"] is self.focus_get()
            ring = self._round_rect(
                body_left,
                input_y,
                body_right,
                input_y + input_height,
                theme.WELCOME_INPUT_RADIUS,
                theme.WELCOME_MARIGOLD if focused else theme.WELCOME_LINEN,
                tags=("content", f"input-outline-{index}")
            )
            border = self._round_rect(
                body_left + 4,
                input_y + 4,
                body_right - 4,
                input_y + input_height - 4,
                theme.WELCOME_INPUT_RADIUS - 3,
                theme.WELCOME_LINEN,
                outline=(
                    theme.WELCOME_OLIVE
                    if focused
                    else theme.WELCOME_SAND
                ),
                width=1 if focused else 2,
                tags=("content", f"input-border-{index}")
            )
            field["outline"] = ring
            field["border"] = border
            window_id = self.create_window(
                body_left + 16,
                input_y + 8,
                anchor="nw",
                window=field["entry"],
                width=body_width - 32,
                height=input_height - (14 if compact else 16),
                tags=("content",)
            )
            field["window"] = window_id

        fields_bottom = first_field_y + len(field_specs) * row_gap - 4
        error_y = fields_bottom + 2
        if self._login_error:
            error_height = 30 if compact else 38
            error_fill = (
                "#F6DDD5"
                if self._login_error_type == "error"
                else theme.WELCOME_CREAM
            )
            self._round_rect(
                body_left,
                error_y,
                body_right,
                error_y + error_height,
                14,
                error_fill,
                tags=("content",)
            )
            self.create_text(
                body_left + 10,
                error_y + error_height / 2,
                text=self._login_error,
                fill=(
                    "#8A2F1B"
                    if self._login_error_type == "error"
                    else theme.WELCOME_OLIVE_GREY
                ),
                font=self._font(theme.WELCOME_BODY_FONT, 8, "bold"),
                width=body_width - 20,
                anchor="w",
                tags=("content",)
            )
            buttons_y = error_y + error_height + 7
        else:
            buttons_y = error_y + 4

        action_label = "Create & continue" if setup_required else "Sign in"
        self._draw_button(
            "admin-submit",
            body_left,
            buttons_y,
            body_width,
            38 if compact else 48,
            action_label,
            bg=theme.WELCOME_MARIGOLD,
            fg=theme.WELCOME_INK
        )
        self._draw_button(
            "admin-back",
            body_left,
            buttons_y + (44 if compact else 56),
            body_width,
            34 if compact else 44,
            "Back",
            bg=theme.WELCOME_CREAM,
            fg=theme.WELCOME_OLIVE_GREY,
            outline=theme.WELCOME_DIVIDER
        )

        if compact:
            return

        footer_y = card_y + card_height - 71
        self.create_line(
            card_x + 20,
            footer_y,
            card_x + card_width - 20,
            footer_y,
            fill=theme.WELCOME_DIVIDER,
            width=2,
            dash=(1, 3),
            tags=("content",)
        )
        self._draw_barcode(card_x + 24, footer_y + 13, 165, 36)
        self.create_text(
            card_x + card_width - 22,
            footer_y + 31,
            text="AUTHORIZED STAFF ONLY",
            fill=theme.WELCOME_OLIVE_GREY,
            font=self._font(theme.WELCOME_BODY_FONT, 7, "bold"),
            anchor="e",
            tags=("content",)
        )

    def _ensure_login_fields(self, specs):

        if len(self._entry_fields) == len(specs):
            return
        self._destroy_login_fields()
        for index, (label, placeholder, mask) in enumerate(specs):
            entry = tk.Entry(
                self,
                bd=0,
                relief="flat",
                highlightthickness=0,
                bg=theme.WELCOME_LINEN,
                fg=theme.WELCOME_PLACEHOLDER,
                insertbackground=theme.WELCOME_INK,
                font=self._font(theme.WELCOME_BODY_FONT, 10),
                show=""
            )
            entry.insert(0, placeholder)
            field = {
                "label": label,
                "placeholder": placeholder,
                "mask": mask,
                "placeholder_visible": True,
                "entry": entry,
                "outline": None,
                "window": None
            }
            entry.bind(
                "<FocusIn>",
                lambda event, item=field: self._entry_focus_in(item),
                add="+"
            )
            entry.bind(
                "<FocusOut>",
                lambda event, item=field: self._entry_focus_out(item),
                add="+"
            )
            entry.bind(
                "<KeyRelease>",
                lambda event: self._clear_login_error(),
                add="+"
            )
            entry.bind(
                "<Return>",
                lambda event: self._submit_admin(),
                add="+"
            )
            self._entry_fields.append(field)

    def _entry_focus_in(self, field):

        entry = field["entry"]
        if field["placeholder_visible"]:
            entry.delete(0, tk.END)
            entry.configure(
                fg=theme.WELCOME_INK,
                show=field["mask"]
            )
            field["placeholder_visible"] = False
        self._set_input_outline(field, focused=True)

    def _entry_focus_out(self, field):

        entry = field["entry"]
        if not entry.get():
            entry.configure(show="")
            entry.insert(0, field["placeholder"])
            entry.configure(fg=theme.WELCOME_PLACEHOLDER)
            field["placeholder_visible"] = True
        self._set_input_outline(field, focused=False)

    def _set_input_outline(self, field, focused):

        outline = field.get("outline")
        border = field.get("border")
        if outline is None or border is None:
            return
        try:
            self.itemconfigure(
                outline,
                fill=(
                    theme.WELCOME_MARIGOLD
                    if focused
                    else theme.WELCOME_LINEN
                )
            )
            self.itemconfigure(
                border,
                outline=(
                    theme.WELCOME_OLIVE
                    if focused
                    else theme.WELCOME_SAND
                ),
                width=1 if focused else 2
            )
        except tk.TclError:
            return

    def _destroy_login_fields(self):

        for field in self._entry_fields:
            field["entry"].destroy()
        self._entry_fields.clear()

    def _draw_barcode(self, x, y, max_width, height):

        cursor = x
        widths = (2, 1, 3, 1, 2, 1, 4)
        gaps = (3, 4, 3, 4, 2, 4, 3)
        while cursor < x + max_width:
            for bar_width, gap in zip(widths, gaps):
                if cursor + bar_width > x + max_width:
                    return
                self.create_rectangle(
                    cursor, y, cursor + bar_width, y + height,
                    fill=theme.WELCOME_INK,
                    outline="",
                    tags=("content",)
                )
                cursor += bar_width + gap

    def _draw_button(
        self,
        tag,
        x,
        y,
        width,
        height,
        text,
        *,
        bg,
        fg,
        outline=""
    ):

        shadow_color = theme.glass_tint(
            theme.WELCOME_FOREST_OLIVE,
            theme.WELCOME_SAND,
            0.45
        )
        self._button_shadow_colors[tag] = shadow_color
        self._round_rect(
            x,
            y + 3,
            x + width,
            y + height + 3,
            height / 2,
            shadow_color,
            tags=("content", f"{tag}-shadow")
        )
        self._round_rect(
            x, y, x + width, y + height,
            height / 2,
            bg,
            outline=outline,
            width=2 if outline else 1,
            tags=("content", tag, f"{tag}-surface")
        )
        self.create_text(
            x + width / 2 - (8 if tag == "admin-submit" else 0),
            y + height / 2,
            text=text,
            fill=fg,
            font=self._font(
                theme.WELCOME_BODY_FONT,
                theme.WELCOME_LOGIN_BUTTON_SIZE
                if tag == "admin-submit"
                else theme.WELCOME_BUTTON_SIZE,
                "bold"
            ),
            tags=("content", tag, f"{tag}-label")
        )
        if tag == "admin-submit":
            self.create_line(
                x + width - 34,
                y + height / 2,
                x + width - 21,
                y + height / 2,
                fill=fg,
                width=2,
                arrow=tk.LAST,
                tags=("content", tag, f"{tag}-label")
            )
        self.tag_bind(
            tag,
            "<Enter>",
            lambda event, item=tag: self._schedule_button_hover(item)
        )
        self.tag_bind(
            tag,
            "<Leave>",
            lambda event, item=tag: self._schedule_button_hover(item)
        )

    def _round_rect(
        self,
        x1,
        y1,
        x2,
        y2,
        radius,
        fill,
        outline="",
        width=1,
        tags=()
    ):

        return self.create_polygon(
            *_rounded_points(x1, y1, x2, y2, radius),
            smooth=True,
            splinesteps=16,
            fill=fill,
            outline=outline,
            width=width,
            tags=tags
        )

    def _set_button_hover(self, tag, hovered):

        color = (
            _blend(self._button_idle_color(tag), "#FFFFFF", 0.08)
            if hovered
            else self._button_idle_color(tag)
        )
        pressed = self._pressed_button == tag
        shadow_color = self._button_shadow_colors.get(
            tag,
            theme.WELCOME_ROAD_OLIVE
        )
        try:
            self.itemconfigure(f"{tag}-surface", fill=color)
            self.itemconfigure(
                f"{tag}-shadow",
                fill=(
                    theme.WELCOME_ROAD_OLIVE
                    if hovered and not pressed
                    else shadow_color
                )
            )
            self.itemconfigure(
                f"{tag}-label",
                fill=(
                    theme.WELCOME_CREAM
                    if tag == "admin-button"
                    else theme.WELCOME_OLIVE_GREY
                    if tag in ("admin-back", "student-back")
                    else theme.WELCOME_INK
                )
            )
        except tk.TclError:
            return
        self._animate_canvas_lift(
            tag,
            -2 if hovered and not pressed else 0,
            200
        )

    def _button_idle_color(self, tag):

        if tag in ("admin-back", "student-back"):
            return theme.WELCOME_CREAM
        if tag == "admin-submit":
            return theme.WELCOME_MARIGOLD
        if tag == "student-button":
            return theme.WELCOME_MARIGOLD
        if tag == "admin-button":
            return theme.WELCOME_DARK_OLIVE
        return theme.WELCOME_MARIGOLD

    def _schedule_button_hover(self, tag):

        self._schedule_hover_check(lambda: self._check_button_hover(tag))

    def _schedule_hover_check(self, callback):

        after_id = None

        def run_callback():

            self._hover_idle_after_ids.discard(after_id)
            if self.winfo_exists():
                callback()

        after_id = self.after_idle(run_callback)
        self._hover_idle_after_ids.add(after_id)

    def _check_button_hover(self, tag):

        if self._pressed_button == tag:
            return
        current = self.find_withtag("current")
        hovered = bool(current and tag in self.gettags(current[0]))
        self._set_button_hover(tag, hovered)

    def _animate_canvas_lift(self, tag, target, duration_ms):

        animation = self._hover_animations.get(tag)
        if animation is None:
            animation = {"after_id": None}
            self._hover_animations[tag] = animation
        if animation["after_id"] is not None:
            self.after_cancel(animation["after_id"])
            animation["after_id"] = None

        start = self._canvas_lifts.get(tag, 0)
        if self.reduced_motion:
            self.move(tag, 0, target - start)
            self._canvas_lifts[tag] = target
            return

        steps = 6
        interval = round(duration_ms / steps)

        def animate_step(step):

            animation["after_id"] = None
            if not self.winfo_exists():
                return

            offset = round(start + (target - start) * step / steps)
            previous = self._canvas_lifts.get(tag, 0)
            self.move(tag, 0, offset - previous)
            self._canvas_lifts[tag] = offset

            if step < steps:
                animation["after_id"] = self.after(
                    interval,
                    lambda: animate_step(step + 1)
                )

        animate_step(1)

    def _set_card_hover(self, tag, hovered):

        if hovered:
            if self._active_hover == tag:
                return
            if self._active_hover:
                self._set_card_hover(self._active_hover, False)
            self._active_hover = tag
            self._animate_canvas_lift(tag, -6, 250)
            self.itemconfigure(
                f"{tag}-shadow",
                fill=theme.glass_tint(
                    theme.WELCOME_FOREST_OLIVE,
                    theme.WELCOME_DARK_OLIVE,
                    0.45
                )
            )
        elif self._active_hover == tag:
            self._animate_canvas_lift(tag, 0, 250)
            self.itemconfigure(
                f"{tag}-shadow",
                fill=theme.WELCOME_ROAD_OLIVE
            )
            self._active_hover = None

    def _schedule_card_leave(self, tag):

        self._schedule_hover_check(lambda: self._check_card_leave(tag))

    def _check_card_leave(self, tag):

        current = self.find_withtag("current")
        if current and tag in self.gettags(current[0]):
            return
        self._set_card_hover(tag, False)

    def _on_motion(self, event):

        current = self.find_withtag("current")
        if not current:
            self.configure(cursor="")
            return
        tags = set(self.gettags(current[0]))
        clickable_tags = {
            "student-button",
            "admin-button",
            "admin-submit",
            "admin-back",
            "student-back"
        }
        self.configure(cursor="hand2" if tags & clickable_tags else "")
        for tag in ("student-card", "admin-card"):
            if tag in tags:
                self._set_card_hover(tag, True)
                return

    def _on_canvas_leave(self, event):

        self.configure(cursor="")
        if self._active_hover:
            self._set_card_hover(self._active_hover, False)

    def _on_click(self, event):

        current = self.find_withtag("current")
        if current:
            tags = set(self.gettags(current[0]))
            for tag in (
                "admin-submit",
                "admin-back",
                "student-button",
                "admin-button",
                "student-back"
            ):
                if tag in tags:
                    self._pressed_button = tag
                    self._set_button_hover(tag, True)
                    break
            if "admin-submit" in tags:
                self._submit_admin()
            elif "admin-back" in tags:
                self._show_choose()
            elif "student-button" in tags:
                self._show_student()
            elif "admin-button" in tags:
                self._show_admin()
            elif "student-back" in tags:
                self._show_choose()

    def _on_release(self, event):

        tag = self._pressed_button
        if tag is None:
            return
        self._pressed_button = None
        current = self.find_withtag("current")
        hovered = bool(current and tag in self.gettags(current[0]))
        self._set_button_hover(tag, hovered)

    def _show_admin(self):

        self.mode = "admin"
        self._login_error = ""
        self._login_error_type = ""
        self._active_hover = None
        self._animate_next_draw = True
        self._draw()
        if self._entry_fields:
            self._entry_fields[0]["entry"].focus_set()

    def _show_choose(self):

        self.mode = "choose"
        self._login_error = ""
        self._login_error_type = ""
        self._active_hover = None
        self._destroy_login_fields()
        self._animate_next_draw = True
        self._draw()

    def _show_student(self):

        self.mode = "student"
        self._destroy_login_fields()
        self._animate_next_draw = True
        self._draw()

    def _clear_login_error(self):

        if self._login_error:
            self._login_error = ""
            self._login_error_type = ""
            self._draw()

    def _submit_admin(self):

        if not self._entry_fields:
            return
        username = (
            ""
            if self._entry_fields[0]["placeholder_visible"]
            else self._entry_fields[0]["entry"].get().strip()
        )
        password = (
            ""
            if self._entry_fields[1]["placeholder_visible"]
            else self._entry_fields[1]["entry"].get()
        )
        if not username or not password:
            self._login_error = "Enter your username and password."
            self._login_error_type = "warning"
            self._draw()
            return

        try:
            setup_required = not has_admin_account()
            if setup_required:
                if len(self._entry_fields) < 3:
                    self._login_error = "Reload the admin setup screen and try again."
                    self._login_error_type = "error"
                    self._draw()
                    return
                confirmation_field = self._entry_fields[2]
                confirmation = (
                    ""
                    if confirmation_field["placeholder_visible"]
                    else confirmation_field["entry"].get()
                )
                if password != confirmation:
                    self._login_error = "The passwords do not match."
                    self._login_error_type = "error"
                    self._draw()
                    return
                create_admin_account(username, password)
            elif not verify_admin_credentials(username, password):
                self._login_error = "The username or password is incorrect."
                self._login_error_type = "error"
                self._draw()
                return
        except ValueError as error:
            self._login_error = str(error)
            self._login_error_type = "error"
            self._draw()
            return
        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Unable to authenticate administrator:\n{error}",
                parent=self.root
            )
            return

        self._destroy_login_fields()
        self.on_admin_success()

    def _draw_ticker(self, width, height):

        ticker_top = height - 46
        self.create_rectangle(
            0, ticker_top, width, height,
            fill=theme.WELCOME_MARIGOLD,
            outline="",
            tags=("ticker",)
        )
        self._ticker_group_width = self._ticker_font.measure(
            self._ticker_text
        ) + 44
        start = self._ticker_x % self._ticker_group_width
        for index in range(3):
            self.create_text(
                start + index * self._ticker_group_width,
                ticker_top + 23,
                text=self._ticker_text,
                font=self._ticker_font,
                fill=theme.WELCOME_INK,
                anchor="w",
                tags=("ticker",)
            )

    def _animate_ticker(self):

        if not self.winfo_exists() or self.reduced_motion:
            return
        self._ticker_x -= max(0.5, self._ticker_group_width / 960)
        if self._ticker_x <= -self._ticker_group_width:
            self._ticker_x = 0
        self.delete("ticker")
        self._draw_ticker(max(self.winfo_width(), 1), max(self.winfo_height(), 1))
        self._ticker_after = self.after(33, self._animate_ticker)

    def _animate_motion(self):

        if not self.winfo_exists() or self.reduced_motion:
            return
        if not self._map_paths:
            self._motion_after = self.after(33, self._animate_motion)
            return
        now = time.monotonic() - self._started_at
        width = max(self.winfo_width(), 1)
        height = max(self.winfo_height() - 46, 1)
        scale = max(width / 1440, height / 900)
        offset_x = (width - 1440 * scale) / 2
        offset_y = (height - 900 * scale) / 2
        for index, items in enumerate(self._map_bus_items):
            body, windows, *wheels = items
            path, lengths, total = self._map_paths[index]
            period = (24, 30, 26)[index]
            start_delay = (0, 8, 14)[index]
            remaining = ((now + start_delay) % period) / period * total
            point = path[-1]
            tangent = (1.0, 0.0)
            for segment_index, segment_length in enumerate(lengths):
                if remaining <= segment_length or segment_index == len(lengths) - 1:
                    fraction = (
                        remaining / segment_length
                        if segment_length
                        else 0
                    )
                    start, end = path[segment_index:segment_index + 2]
                    tangent = (
                        (end[0] - start[0]) / segment_length,
                        (end[1] - start[1]) / segment_length
                    ) if segment_length else (1.0, 0.0)
                    point = (
                        start[0] + (end[0] - start[0]) * fraction,
                        start[1] + (end[1] - start[1]) * fraction
                    )
                    break
                remaining -= segment_length
            x = offset_x + point[0] * scale
            y = offset_y + point[1] * scale
            tangent_x, tangent_y = tangent
            normal_x, normal_y = -tangent_y, tangent_x
            bus_scale = max(0.8, scale)
            self.coords(
                body,
                *_oriented_rectangle(
                    x,
                    y,
                    tangent_x,
                    tangent_y,
                    13 * bus_scale,
                    7 * bus_scale
                )
            )
            self.coords(
                windows,
                *_oriented_rectangle(
                    x,
                    y,
                    tangent_x,
                    tangent_y,
                    6 * bus_scale,
                    4 * bus_scale
                )
            )
            wheel_radius = 1.8 * bus_scale
            for wheel, along, across in zip(
                wheels,
                (-8, 8, -8, 8),
                (-6, -6, 6, 6)
            ):
                wheel_x = (
                    x
                    + tangent_x * along * bus_scale
                    + normal_x * across * bus_scale
                )
                wheel_y = (
                    y
                    + tangent_y * along * bus_scale
                    + normal_y * across * bus_scale
                )
                self.coords(
                    wheel,
                    wheel_x - wheel_radius,
                    wheel_y - wheel_radius,
                    wheel_x + wheel_radius,
                    wheel_y + wheel_radius
                )

        for index, (ring, cx, cy, scale) in enumerate(self._pulse_items):
            phase = ((now - index * 1.2) % 2.6) / 2.6
            radius = (11 + 19 * phase) * scale
            self.coords(
                ring,
                cx - radius, cy - radius,
                cx + radius, cy + radius
            )
            self.itemconfigure(
                ring,
                outline=_blend(
                    theme.WELCOME_MARIGOLD,
                    theme.WELCOME_FOREST_OLIVE,
                    phase
                )
            )
        self._motion_after = self.after(33, self._animate_motion)

    def _animate_entrance(self):

        if not self.winfo_exists() or self.reduced_motion:
            return
        self._entrance_step += 1
        self.move("content", 0, -26 / 22)
        if self._entrance_step < 22:
            self._entrance_after = self.after(34, self._animate_entrance)
        else:
            self._entrance_after = None

    def _on_mousewheel(self, event):

        return "break"

    def destroy(self):

        self._cancel_hover_work()
        for after_id in (
            self._ticker_after,
            self._motion_after,
            self._entrance_after
        ):
            if after_id is not None:
                try:
                    self.after_cancel(after_id)
                except tk.TclError:
                    pass
        self._destroy_login_fields()
        super().destroy()


def create_welcome_screen(master, on_admin_success):

    return WelcomeScreen(master, on_admin_success)
