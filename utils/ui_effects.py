import tkinter as tk
from tkinter import ttk

from utils import theme
from utils.rounded_widgets import (
    RoundedButton,
    RoundedField,
    RoundedPanel,
    ScrollableFrame
)


def _blend_color(widget, first_color, second_color, amount):

    try:
        first = widget.winfo_rgb(first_color)
        second = widget.winfo_rgb(second_color)
    except tk.TclError:
        return second_color

    channels = [
        round((first[index] * (1 - amount) + second[index] * amount) / 257)
        for index in range(3)
    ]
    return "#{:02x}{:02x}{:02x}".format(*channels)


def bind_button_hover(
    button,
    idle_color=None,
    idle_foreground=None,
    hover_color=None,
    hover_foreground=None
):

    initial_color = button.cget("background")
    initial_foreground = button.cget("foreground")
    outer_background = (
        button._outer_background
        if isinstance(button, RoundedButton)
        else theme.BACKGROUND
    )
    idle_shadow = theme.GLASS_SHADOW
    hover_shadow = theme.glass_tint(
        theme.GLASS_SIDEBAR,
        outer_background,
        0.45
    )
    animation = {"after_id": None}

    def get_idle_color():
        if callable(idle_color):
            return idle_color()
        return idle_color or initial_color

    def get_idle_foreground():
        if callable(idle_foreground):
            return idle_foreground()
        return idle_foreground or initial_foreground

    def is_disabled():

        return button.cget("state") == tk.DISABLED

    def animate_to(hovered, pressed=False):

        if not button.winfo_exists():
            return
        after_id = animation["after_id"]
        if after_id is not None:
            button.after_cancel(after_id)
        animation["after_id"] = None
        start_color = button.cget("background")
        start_foreground = button.cget("foreground")
        base_color = get_idle_color()
        target_color = (
            hover_color
            if hover_color is not None
            else theme.glass_tint("#FFFFFF", base_color, 0.08)
        ) if hovered else base_color
        base_foreground = get_idle_foreground()
        target_foreground = (
            hover_foreground
            if hover_foreground is not None
            else base_foreground
        )
        start_lift = button._lift if isinstance(button, RoundedButton) else 0
        target_lift = 2 if hovered and not pressed else 0
        steps = 6

        def animate_step(step):

            animation["after_id"] = None
            if not button.winfo_exists():
                return

            fraction = step / steps
            color = _blend_color(button, start_color, target_color, fraction)
            foreground = _blend_color(
                button,
                start_foreground,
                target_foreground,
                fraction
            )
            button.configure(
                background=color,
                foreground=foreground,
                activebackground=target_color,
                activeforeground=target_foreground
            )

            if isinstance(button, RoundedButton):
                lift = start_lift + (target_lift - start_lift) * fraction
                shadow_fraction = lift / button._lift_reserve
                shadow = theme.glass_tint(
                    hover_shadow,
                    idle_shadow,
                    shadow_fraction
                )
                button.set_lift(lift, shadow)

            if step < steps:
                animation["after_id"] = button.after(
                    33,
                    lambda: animate_step(step + 1)
                )

        animate_step(1)

    def on_enter(event):

        if is_disabled():
            return

        animate_to(True)

    def on_leave(event):

        animate_to(False)

    def on_press(event):

        if not is_disabled():
            animate_to(True, pressed=True)

    def on_release(event):

        if is_disabled() or not button.winfo_exists():
            return

        def restore_hover_state():

            if not button.winfo_exists() or is_disabled():
                return
            hovered_widget = button.winfo_containing(
                event.x_root,
                event.y_root
            )
            while hovered_widget is not None:
                if hovered_widget is button:
                    animate_to(True)
                    return
                hovered_widget = hovered_widget.master
            animate_to(False)

        button.winfo_toplevel().after_idle(restore_hover_state)

    def on_destroy(event):

        if event.widget is button and animation["after_id"] is not None:
            button.after_cancel(animation["after_id"])
            animation["after_id"] = None

    button.configure(cursor="hand2" if not is_disabled() else "arrow")
    button.bind("<Enter>", on_enter, add="+")
    button.bind("<Leave>", on_leave, add="+")
    button.bind("<Destroy>", on_destroy, add="+")
    press_target = button._button if isinstance(button, RoundedButton) else button
    press_target.bind("<ButtonPress-1>", on_press, add="+")
    press_target.bind("<ButtonRelease-1>", on_release, add="+")


def bind_sidebar_item(button, base_padding=12):

    bar_id = button.create_rectangle(
        1,
        0,
        5,
        0,
        fill=theme.ACCENT,
        outline=""
    )
    state = {
        "active": False,
        "hovered": False,
        "after_id": None,
        "offset": 0,
        "bar_height": 0
    }

    def animate(hovered):

        after_id = state["after_id"]
        if after_id is not None:
            button.after_cancel(after_id)
            state["after_id"] = None

        start_color = button.cget("background")
        target_color = theme.PRIMARY if hovered else theme.GLASS_SIDEBAR
        start_offset = state["offset"]
        target_offset = 5 if hovered else 0
        start_height = state["bar_height"]
        target_height = button.winfo_height() if hovered else 0
        steps = 6

        def animate_step(step):

            state["after_id"] = None
            if not button.winfo_exists():
                return

            fraction = step / steps
            state["offset"] = round(
                start_offset + (target_offset - start_offset) * fraction
            )
            state["bar_height"] = round(
                start_height + (target_height - start_height) * fraction
            )
            color = _blend_color(button, start_color, target_color, fraction)
            button.configure(
                bg=color,
                fg=theme.TEXT_LIGHT,
                activebackground=target_color,
                activeforeground=theme.TEXT_LIGHT
            )
            button.pack_configure(
                padx=(
                    base_padding + state["offset"],
                    base_padding - state["offset"]
                )
            )
            middle = button.winfo_height() / 2
            half_height = state["bar_height"] / 2
            button.coords(
                bar_id,
                1,
                middle - half_height,
                5,
                middle + half_height
            )

            if step < steps:
                state["after_id"] = button.after(
                    33,
                    lambda: animate_step(step + 1)
                )

        animate_step(1)

    def on_enter(event):

        state["hovered"] = True
        if not state["active"]:
            animate(True)

    def on_leave(event):

        state["hovered"] = False
        if not state["active"]:
            animate(False)

    def set_active(active):

        state["active"] = active
        if active:
            if state["after_id"] is not None:
                button.after_cancel(state["after_id"])
                state["after_id"] = None
            state["offset"] = 0
            state["bar_height"] = 0
            button.pack_configure(padx=base_padding)
            middle = button.winfo_height() / 2
            button.coords(bar_id, 1, middle, 5, middle)
        else:
            if state["hovered"]:
                animate(True)
            elif state["offset"] or state["bar_height"]:
                animate(False)

    def on_destroy(event):

        if event.widget is button and state["after_id"] is not None:
            button.after_cancel(state["after_id"])
            state["after_id"] = None

    button.configure(cursor="hand2")
    button.bind("<Enter>", on_enter, add="+")
    button.bind("<Leave>", on_leave, add="+")
    button.bind("<Destroy>", on_destroy, add="+")
    return set_active


def prepare_treeview_hover(tree):
    """Create hover styling before row tags so it can override their colors."""

    tree.tag_configure(
        "_pointer_hover",
        background=theme.ROW_HOVER,
        foreground=theme.TEXT_PRIMARY
    )
    tree.configure(cursor="hand2")


def _bind_treeview_hover(tree):

    prepare_treeview_hover(tree)
    hovered_item = {"iid": None, "tags": None}
    leave_state = {"after_id": None}
    action_state = {}
    overlay_parent = tree.master
    action_shadow = tk.Label(
        overlay_parent,
        bg=theme.glass_tint(theme.GLASS_SIDEBAR, theme.ROW_HOVER, 0.45),
        bd=0
    )
    action_button = tk.Label(
        overlay_parent,
        bg=theme.SECONDARY,
        fg=theme.TEXT_LIGHT,
        font=("Segoe UI", 8, "bold"),
        cursor="hand2",
        bd=0
    )
    action_shadow.place_forget()
    action_button.place_forget()

    def restore_previous():

        iid = hovered_item["iid"]
        if iid and tree.exists(iid):
            tree.item(iid, tags=hovered_item["tags"])

        hovered_item["iid"] = None
        hovered_item["tags"] = None

    def hide_action():

        action_shadow.place_forget()
        action_button.place_forget()
        action_state.clear()

    def update_action(event):

        iid = tree.identify_row(event.y)
        column = tree.identify_column(event.x)
        if not iid or not column.startswith("#"):
            hide_action()
            return

        try:
            column_index = int(column[1:]) - 1
            action = tree.item(iid, "values")[column_index]
        except (ValueError, IndexError):
            hide_action()
            return

        action = str(action).strip()
        if action.lower() not in ("edit", "delete", "view"):
            hide_action()
            return

        cell = tree.bbox(iid, column)
        if not cell:
            hide_action()
            return

        x, y, width, height = cell
        button_width = min(width - 6, max(44, len(action) * 7 + 18))
        button_height = min(22, max(1, height - 4))
        if button_width < 1:
            hide_action()
            return

        button_x = x + (width - button_width) // 2
        button_y = y + (height - button_height) // 2 - 1
        overlay_y = tree.winfo_y() + button_y
        action_state.update({
            "iid": iid,
            "column": column,
            "x": button_x + button_width // 2,
            "y": button_y + button_height // 2,
            "button_y": overlay_y
        })
        action_button.configure(text=action)
        action_shadow.place(
            x=tree.winfo_x() + button_x,
            y=overlay_y + 3,
            width=button_width,
            height=button_height
        )
        action_button.place(
            x=tree.winfo_x() + button_x,
            y=overlay_y,
            width=button_width,
            height=button_height
        )
        action_button.lift()

    def on_action_press(event):

        action_button.configure(bg=theme.PRIMARY)
        action_shadow.place_forget()
        action_button.place_configure(y=action_state["button_y"] + 1)

    def on_action_release(event):

        if not action_state:
            return
        action_button.configure(bg=theme.SECONDARY)
        action_button.place_configure(y=action_state["button_y"])
        action_shadow.place_configure(
            y=action_state["button_y"] + 3
        )
        tree.event_generate(
            "<Button-1>",
            x=action_state["x"],
            y=action_state["y"],
            state=event.state
        )

    def finish_leave():

        leave_state["after_id"] = None
        under_pointer = tree.winfo_containing(
            tree.winfo_pointerx(),
            tree.winfo_pointery()
        )
        if under_pointer in (action_button, action_shadow):
            return
        restore_previous()
        hide_action()

    def on_leave(event):

        if leave_state["after_id"] is not None:
            tree.after_cancel(leave_state["after_id"])
        leave_state["after_id"] = tree.after_idle(finish_leave)

    def on_destroy(event):

        if (
            event.widget is tree
            and leave_state["after_id"] is not None
        ):
            tree.after_cancel(leave_state["after_id"])
            leave_state["after_id"] = None
        if event.widget is tree:
            action_shadow.place_forget()
            action_button.place_forget()
            action_shadow.destroy()
            action_button.destroy()

    def on_motion(event):

        update_action(event)
        iid = tree.identify_row(event.y)
        if iid and iid in tree.selection():
            restore_previous()
            return
        if iid == hovered_item["iid"]:
            return

        restore_previous()
        if not iid:
            return

        tags = tree.item(iid, "tags")
        if isinstance(tags, str):
            tags = (tags,) if tags else ()
        else:
            tags = tuple(tags)
        hovered_item["iid"] = iid
        hovered_item["tags"] = tags
        tree.item(iid, tags=("_pointer_hover",) + tags)

    action_button.bind("<ButtonPress-1>", on_action_press, add="+")
    action_button.bind("<ButtonRelease-1>", on_action_release, add="+")
    for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
        action_button.bind(sequence, lambda event: hide_action(), add="+")
        action_shadow.bind(sequence, lambda event: hide_action(), add="+")
    tree.bind("<Motion>", on_motion, add="+")
    tree.bind("<Leave>", on_leave, add="+")
    tree.bind("<Destroy>", on_destroy, add="+")


def _bind_panel_hover(panel):

    if not panel.hoverable:
        return

    descendants = []

    def collect(widget):

        descendants.append(widget)
        if isinstance(widget, (RoundedButton, RoundedField, ttk.Treeview)):
            return

        for child in widget.winfo_children():
            collect(child)

    collect(panel.content)
    state = {"after_id": None}

    def update_hover():

        state["after_id"] = None
        if not panel.winfo_exists():
            return

        window = panel.winfo_toplevel()
        hovered_widget = window.winfo_containing(
            window.winfo_pointerx(),
            window.winfo_pointery()
        )
        while hovered_widget is not None:
            if hovered_widget is panel:
                panel.set_hovered(True)
                return
            hovered_widget = hovered_widget.master

        panel.set_hovered(False)

    def schedule_update(event):

        after_id = state["after_id"]
        if after_id is not None:
            panel.after_cancel(after_id)
        state["after_id"] = panel.after_idle(update_hover)

    def on_destroy(event):

        if event.widget is panel and state["after_id"] is not None:
            panel.after_cancel(state["after_id"])
            state["after_id"] = None

    for widget in [panel] + descendants:
        widget.bind("<Enter>", schedule_update, add="+")
        widget.bind("<Leave>", schedule_update, add="+")
    panel.bind("<Destroy>", on_destroy, add="+")


def _fade_in(window):

    steps = 8
    try:
        window.attributes("-alpha", 0.0)
    except tk.TclError:
        return

    def show_step(step):

        if not window.winfo_exists():
            return

        try:
            window.attributes("-alpha", step / steps)
        except tk.TclError:
            return

        if step < steps:
            window.after(18, lambda: show_step(step + 1))

    window.after(10, lambda: show_step(1))


def _bind_page_mousewheel(page):

    def scroll_units(event):

        if getattr(event, "num", None) == 4:
            direction = -1
            notches = 1
        elif getattr(event, "num", None) == 5:
            direction = 1
            notches = 1
        else:
            delta = getattr(event, "delta", 0)
            if not delta:
                return 0
            direction = -1 if delta > 0 else 1
            notches = max(1, int(abs(delta) / 120))

        return direction * notches * 3

    def on_mousewheel(event):

        units = scroll_units(event)
        if not units:
            return "break"

        widget = event.widget
        tree = None
        while widget is not None:
            if isinstance(widget, ttk.Treeview):
                tree = widget
                break
            if widget is page:
                break
            widget = getattr(widget, "master", None)

        if tree is not None:
            first, last = tree.yview()
            can_scroll = (
                (units < 0 and first > 0)
                or (units > 0 and last < 1)
            )
            if can_scroll:
                tree.yview_scroll(units, "units")
                return "break"
        elif widget is not page:
            return

        page.canvas.yview_scroll(units, "units")
        return "break"

    def bind_descendants(widget):

        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            widget.bind(sequence, on_mousewheel, add="+")
        for child in widget.winfo_children():
            bind_descendants(child)

    bind_descendants(page)


def apply_interactive_effects(window, skip_buttons=(), fade=True):

    skipped = {id(button) for button in skip_buttons}

    def visit(widget):

        if isinstance(widget, ScrollableFrame):
            _bind_page_mousewheel(widget)
        if isinstance(widget, RoundedPanel):
            _bind_panel_hover(widget)
        if isinstance(widget, RoundedButton):
            if id(widget) not in skipped:
                bind_button_hover(widget)
            return
        if isinstance(widget, RoundedField):
            return
        if isinstance(widget, tk.Button) and id(widget) not in skipped:
            bind_button_hover(widget)
        elif isinstance(widget, ttk.Treeview):
            _bind_treeview_hover(widget)

        for child in widget.winfo_children():
            visit(child)

    visit(window)
    if fade:
        _fade_in(window)
