import math
import os
import tkinter as tk

from utils import theme


class NavigationAnimator:

    def __init__(self, root, sidebar, nav_buttons, menu_order):
        self.root = root
        self.sidebar = sidebar
        self.nav_buttons = nav_buttons
        self.menu_order = menu_order
        self.active_name = "Dashboard"
        self._busy = False
        self._pending = None
        self._after_ids = set()
        self._active_buses = {}
        self._travel_canvas = None
        self._road_canvas = None
        self._reduced_motion = (
            os.environ.get("SCHOOL_TRANSIT_REDUCED_MOTION") == "1"
        )

        self._create_travel_canvas()
        self._create_road_canvas()
        self._attach_menu_buses()
        self.set_active("Dashboard")
        self.root.bind("<Destroy>", self._on_root_destroy, add="+")

    def _schedule(self, delay, callback):
        after_id = self.root.after(delay, callback)
        self._after_ids.add(after_id)

        def wrapped():
            self._after_ids.discard(after_id)
            callback()

        self.root.after_cancel(after_id)
        after_id = self.root.after(delay, wrapped)
        self._after_ids.add(after_id)
        return after_id

    def _cancel_scheduled(self):
        for after_id in tuple(self._after_ids):
            try:
                self.root.after_cancel(after_id)
            except tk.TclError:
                pass
        self._after_ids.clear()

    def _on_root_destroy(self, event):
        if event.widget is self.root:
            self._cancel_scheduled()

    def _raise_widget(self, widget):
        try:
            widget.tk.call("raise", widget._w)
        except tk.TclError:
            pass

    def _create_travel_canvas(self):
        canvas = tk.Canvas(
            self.root,
            width=44,
            height=28,
            bg=theme.BACKGROUND,
            bd=0,
            highlightthickness=0
        )
        canvas.place_forget()
        self._travel_canvas = canvas

    def _create_road_canvas(self):
        canvas = tk.Canvas(
            self.sidebar,
            width=12,
            height=1,
            bg=theme.GLASS_SIDEBAR,
            bd=0,
            highlightthickness=0
        )
        canvas.place_forget()
        self._road_canvas = canvas

    def _draw_side_bus(self, canvas, width=44, height=28, scale=1.0):
        canvas.delete("all")
        sx = scale
        sy = scale

        def point(values):
            return tuple(round(value * sx if index % 2 == 0 else value * sy)
                         for index, value in enumerate(values))

        canvas.create_rounded_rectangle = lambda *args, **kwargs: None
        body = (
            round(4 * sx), round(6 * sy),
            round(38 * sx), round(22 * sy)
        )
        canvas.create_rectangle(*body, fill=theme.ACCENT, outline=theme.TEXT_PRIMARY,
                                width=max(1, round(2 * sx)))
        canvas.create_rectangle(
            round(9 * sx), round(9 * sy),
            round(17 * sx), round(16 * sy),
            fill=theme.TEXT_PRIMARY, outline=theme.TEXT_PRIMARY
        )
        canvas.create_rectangle(
            round(20 * sx), round(9 * sy),
            round(28 * sx), round(16 * sy),
            fill=theme.TEXT_PRIMARY, outline=theme.TEXT_PRIMARY
        )
        canvas.create_rectangle(
            round(31 * sx), round(9 * sy),
            round(36 * sx), round(16 * sy),
            fill=theme.TEXT_PRIMARY, outline=theme.TEXT_PRIMARY
        )
        canvas.create_oval(
            round(9 * sx), round(20 * sy),
            round(17 * sx), round(28 * sy),
            fill=theme.TEXT_PRIMARY, outline=theme.TEXT_PRIMARY
        )
        canvas.create_oval(
            round(31 * sx), round(20 * sy),
            round(39 * sx), round(28 * sy),
            fill=theme.TEXT_PRIMARY, outline=theme.TEXT_PRIMARY
        )

    def _draw_vertical_bus(self, direction):
        canvas = self._travel_canvas
        canvas.configure(width=28, height=44)
        canvas.delete("all")
        canvas.create_rectangle(
            5, 4, 23, 40,
            fill=theme.ACCENT,
            outline=theme.TEXT_PRIMARY,
            width=2
        )
        canvas.create_rectangle(9, 8, 19, 16,
                                fill=theme.TEXT_PRIMARY,
                                outline=theme.TEXT_PRIMARY)
        canvas.create_rectangle(9, 20, 19, 28,
                                fill=theme.TEXT_PRIMARY,
                                outline=theme.TEXT_PRIMARY)
        canvas.create_oval(7, 34, 13, 40,
                           fill=theme.TEXT_PRIMARY,
                           outline=theme.TEXT_PRIMARY)
        canvas.create_oval(15, 34, 21, 40,
                           fill=theme.TEXT_PRIMARY,
                           outline=theme.TEXT_PRIMARY)
        if direction < 0:
            canvas.create_polygon(14, 3, 9, 8, 19, 8,
                                  fill=theme.TEXT_PRIMARY,
                                  outline=theme.TEXT_PRIMARY)
        else:
            canvas.create_polygon(14, 41, 9, 36, 19, 36,
                                  fill=theme.TEXT_PRIMARY,
                                  outline=theme.TEXT_PRIMARY)

    def _attach_menu_buses(self):
        for name, button in self.nav_buttons.items():
            bus = tk.Canvas(
                button,
                width=44,
                height=28,
                bg=theme.ACCENT,
                bd=0,
                highlightthickness=0
            )
            bus.place_forget()
            self._draw_side_bus(bus)
            self._active_buses[name] = bus

    def _button_center(self, name):
        button = self.nav_buttons[name]
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        x = button.winfo_rootx() - root_x + button.winfo_width() - 54
        y = button.winfo_rooty() - root_y + (button.winfo_height() - 28) // 2
        return x, y

    def set_active(self, name, pop=False):
        self.active_name = name
        for item_name, bus in self._active_buses.items():
            bus.place_forget()

        bus = self._active_buses.get(name)
        if bus is not None:
            button = self.nav_buttons[name]
            bus.configure(width=44, height=28)
            bus.place(
                in_=button,
                relx=1.0,
                x=-54,
                y=max(4, (button.winfo_height() - 28) // 2)
            )
            self._raise_widget(bus)
            if pop:
                self._pop_active_bus(name)

    def _pop_active_bus(self, name):
        bus = self._active_buses[name]
        button = self.nav_buttons[name]
        sizes = (0, 53, 44)
        heights = (0, 34, 28)

        def step(index):
            if not bus.winfo_exists():
                return
            width = sizes[index]
            height = heights[index]
            bus.configure(width=max(1, width), height=max(1, height))
            if width > 1:
                self._draw_side_bus(bus, width=44, height=28)
            bus.place(
                in_=button,
                relx=1.0,
                x=-54 - max(0, width - 44),
                y=max(2, (button.winfo_height() - height) // 2)
            )
            self._raise_widget(bus)
            if index < len(sizes) - 1:
                self.root.after(85, lambda: step(index + 1))

        step(0)

    def _show_road(self):
        height = max(100, self.sidebar.winfo_height() - 24)
        canvas = self._road_canvas
        canvas.configure(height=height)
        canvas.delete("all")
        canvas.create_line(
            6, 0, 6, height,
            fill=theme.MOSS,
            width=2,
            dash=(5, 7)
        )
        canvas.place(
            in_=self.sidebar,
            relx=1.0,
            x=-10,
            y=12
        )
        self._raise_widget(canvas)

    def _hide_road(self):
        self._road_canvas.place_forget()

    def _hide_travel_bus(self):
        self._travel_canvas.place_forget()

    def _ease_in_out(self, value):
        if value < 0.5:
            return 4 * value * value * value
        return 1 - ((-2 * value + 2) ** 3) / 2

    def _fade_current_page(self, page):
        if page is None:
            return
        try:
            page.place_configure(x=-14)
            self.root.after(150, lambda: page.place_configure(x=0))
        except tk.TclError:
            pass

    def request_navigation(self, target_name, switch_action, current_page=None):
        if self._reduced_motion:
            self._hide_travel_bus()
            page = switch_action()
            self.set_active(target_name)
            self._reveal_reduced_motion_page(page)
            return

        if self._busy:
            self._pending = (target_name, switch_action)
            return

        if target_name == self.active_name:
            return

        self._busy = True
        self._hide_travel_bus()
        source_name = self.active_name
        source_index = self.menu_order.index(source_name)
        target_index = self.menu_order.index(target_name)
        distance = abs(target_index - source_index)
        duration = 280 + 130 * distance

        for bus in self._active_buses.values():
            bus.place_forget()

        self._fade_current_page(current_page)
        self._show_road()

        start_x, start_y = self._button_center(source_name)
        end_x, end_y = self._button_center(target_name)
        canvas = self._travel_canvas
        canvas.configure(width=28, height=44)
        canvas.place(in_=self.root, x=start_x + 8, y=start_y - 8)

        direction = 1 if target_index >= source_index else -1
        self._draw_vertical_bus(direction)
        started = [False]

        def animate_trip(step, steps=18):
            if step == 0:
                started[0] = True
            progress = step / steps
            eased = self._ease_in_out(progress)
            y = round(start_y + (end_y - start_y) * eased)
            bounce = round(3 * math.sin(progress * math.pi * 4)) if progress < 1 else 0
            canvas.place(in_=self.root, x=start_x + 8, y=y - 8 - bounce)
            if step < steps:
                delay = max(10, round(duration / steps))
                self.root.after(delay, lambda: animate_trip(step + 1, steps))
            else:
                self._hide_road()
                self._hide_travel_bus()
                self.set_active(target_name)
                page = switch_action()
                self._run_heading(page, target_name, heading_complete)

        def heading_complete():
            self._busy = False
            self.set_active(target_name, pop=True)
            if self._pending is not None:
                pending = self._pending
                self._pending = None
                pending_target, pending_action = pending
                self.root.after_idle(
                    lambda: self.request_navigation(
                        pending_target,
                        pending_action,
                        current_page
                    )
                )

        animate_trip(0)

    def _reveal_reduced_motion_page(self, page):
        meta = getattr(page, "_navigation_heading_meta", None)
        if meta is None:
            return
        title_clip = meta.get("title_clip")
        title_label = meta.get("title_label")
        if title_clip is not None and title_label is not None:
            title_clip.configure(
                width=max(title_label.winfo_reqwidth() + 12, 72)
            )

    def run_initial_heading(self, page, name="Dashboard"):
        if self._reduced_motion:
            self.set_active(name)
            self._reveal_reduced_motion_page(page)
            return

        self._busy = True
        self._hide_travel_bus()
        self.set_active(name)

        def complete():
            self._busy = False
            self.set_active(name, pop=True)

        self._run_heading(page, name, complete)

    def _hide_heading_meta(self, meta):
        if meta is None:
            return
        meta["_hidden"] = {}
        for key in ("admin_label", "subtitle_label", "metric_widgets"):
            widgets = meta.get(key, ())
            if not isinstance(widgets, (list, tuple)):
                widgets = (widgets,)
            for widget in widgets:
                if widget is None or not widget.winfo_exists():
                    continue
                pack_info = widget.pack_info() if widget.winfo_manager() == "pack" else None
                if pack_info:
                    meta["_hidden"][id(widget)] = (widget, pack_info)
                    widget.pack_forget()

        rest_widgets = meta.get("rest_widgets", ())
        for widget in rest_widgets:
            if widget is None or not widget.winfo_exists():
                continue
            pack_info = widget.pack_info() if widget.winfo_manager() == "pack" else None
            if pack_info:
                meta["_hidden"][id(widget)] = (widget, pack_info)
                widget.pack_forget()

        clip = meta.get("title_clip")
        if clip is not None and clip.winfo_exists():
            clip.configure(width=1)

    def _run_heading(self, page, name, complete_callback):
        meta = getattr(page, "_navigation_heading_meta", None)
        if meta is None:
            complete_callback()
            return

        title_clip = meta.get("title_clip")
        title_label = meta.get("title_label")
        if title_clip is None or title_label is None:
            complete_callback()
            return

        self._hide_heading_meta(meta)
        self.root.update_idletasks()

        start_x, start_y = self._button_center(name)
        title_x = title_label.winfo_rootx() - self.root.winfo_rootx()
        title_y = title_label.winfo_rooty() - self.root.winfo_rooty()

        canvas = self._travel_canvas
        canvas.configure(width=66, height=42, bg=theme.BACKGROUND)
        canvas.place(in_=self.root, x=start_x - 10, y=start_y - 7)

        def draw_big_bus():
            canvas.delete("all")
            canvas.configure(width=66, height=42)
            canvas.create_rectangle(
                6, 9, 57, 33,
                fill=theme.ACCENT,
                outline=theme.TEXT_PRIMARY,
                width=3
            )
            for x1, x2 in ((13, 25), (30, 42), (46, 54)):
                canvas.create_rectangle(
                    x1, 14, x2, 24,
                    fill=theme.TEXT_PRIMARY,
                    outline=theme.TEXT_PRIMARY
                )
            canvas.create_oval(13, 30, 25, 42,
                               fill=theme.TEXT_PRIMARY,
                               outline=theme.TEXT_PRIMARY)
            canvas.create_oval(46, 30, 58, 42,
                               fill=theme.TEXT_PRIMARY,
                               outline=theme.TEXT_PRIMARY)

        draw_big_bus()
        title_width = max(title_label.winfo_reqwidth() + 12, 72)

        def animate_diagonal(step, steps=21):
            progress = step / steps
            eased = self._ease_in_out(progress)
            bounce = round(4 * math.sin(progress * math.pi * 3))
            x = round(start_x + (title_x - start_x - 10) * eased)
            y = round(start_y + (title_y - start_y - 7) * eased - bounce)
            canvas.place(in_=self.root, x=x, y=y)
            self._raise_widget(canvas)
            if step < steps:
                self.root.after(33, lambda: animate_diagonal(step + 1, steps))
            else:
                canvas.configure(width=66, height=42)
                canvas.place(in_=self.root, x=title_x - 33, y=title_y - 5)
                canvas.delete("all")
                draw_big_bus()
                self._raise_widget(canvas)
                animate_wipe(0)

        def animate_wipe(step, steps=24):
            progress = step / steps
            eased = self._ease_in_out(progress)
            reveal_width = max(1, round(title_width * eased))
            title_clip.configure(width=reveal_width)
            canvas.place(
                in_=self.root,
                x=title_x + reveal_width - 57,
                y=title_y - 5
            )
            self._raise_widget(canvas)
            if step < steps:
                self.root.after(29, lambda: animate_wipe(step + 1, steps))
            else:
                title_clip.configure(width=title_width)
                canvas.configure(width=44, height=28)
                canvas.delete("all")
                self._draw_side_bus(canvas)
                canvas.place(
                    in_=self.root,
                    x=title_x + title_width + 8,
                    y=title_y + max(0, (title_label.winfo_reqheight() - 28) // 2)
                )
                self._raise_widget(canvas)
                self.root.after(120, finish_heading)

        def finish_heading():
            reveal_items = []
            hidden = meta.get("_hidden", {})
            for widget, pack_info in hidden.values():
                reveal_items.append((widget, pack_info))

            def reveal_step(index):
                if index >= len(reveal_items):
                    complete_callback()
                    return
                widget, pack_info = reveal_items[index]
                if widget.winfo_exists():
                    pack_info = dict(pack_info)
                    widget.pack(**pack_info)
                self.root.after(70, lambda: reveal_step(index + 1))

            reveal_step(0)

        animate_diagonal(0)
