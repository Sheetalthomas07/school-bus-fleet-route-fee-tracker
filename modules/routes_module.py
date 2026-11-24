
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import time

from database.db_connection import get_connection
from utils import theme
from utils.ui_effects import apply_interactive_effects, prepare_treeview_hover
from utils.rounded_widgets import (
    RoundedButton,
    RoundedEntry,
    RoundedPanel,
    ScrollableFrame
)
from utils.module_ui import (
    bind_preview_updates,
    create_live_preview,
    create_module_header
)


def open_routes_module(parent):

    routes_page = ScrollableFrame(parent, bg=theme.BACKGROUND)
    routes_window = routes_page.content

    route_count_value = tk.StringVar(master=routes_page, value="0")
    total_seats_value = tk.StringVar(master=routes_page, value="0")
    module_header = create_module_header(
        routes_window,
        "Routes & Buses",
        "Manage school bus routes and driver information.",
        (
            (route_count_value, "Routes"),
            (total_seats_value, "Total seats")
        )
    )

    count_animation_after_id = None

    def cancel_count_animation():

        nonlocal count_animation_after_id

        if count_animation_after_id is None:
            return
        routes_page.after_cancel(count_animation_after_id)
        count_animation_after_id = None

    def animate_count_values(route_count, total_seats):

        nonlocal count_animation_after_id

        cancel_count_animation()
        route_count_value.set("0")
        total_seats_value.set("0")

        def begin_animation():

            nonlocal count_animation_after_id

            count_animation_after_id = None
            started_at = time.monotonic()

            def update_counts():

                nonlocal count_animation_after_id

                progress = min((time.monotonic() - started_at) / 1.2, 1)
                eased_progress = 1 - (1 - progress) ** 3
                route_count_value.set(str(round(route_count * eased_progress)))
                total_seats_value.set(str(round(total_seats * eased_progress)))

                if progress >= 1:
                    route_count_value.set(str(route_count))
                    total_seats_value.set(str(total_seats))
                    count_animation_after_id = None
                    return
                count_animation_after_id = routes_page.after(30, update_counts)

            update_counts()

        count_animation_after_id = routes_page.after(300, begin_animation)

    def on_routes_page_destroy(event):

        if event.widget is routes_page:
            cancel_count_animation()

    routes_page.bind("<Destroy>", on_routes_page_destroy, add="+")

    # Form
    editor_row = tk.Frame(routes_window, bg=theme.BACKGROUND)
    editor_row.pack(fill="x", padx=30, pady=(0, 20))
    editor_row.grid_columnconfigure(0, weight=3)
    editor_row.grid_columnconfigure(1, weight=2)

    form = RoundedPanel(
        editor_row,
        bg=theme.CARD_BACKGROUND,
        padx=25,
        pady=20,
        highlightbackground=theme.ACCENT,
        highlightthickness=1
    )
    form.grid(row=0, column=0, sticky="nsew")

    tk.Label(
        form.content,
        text="Add New Bus Route",
        font=("Segoe UI", 14, "bold"),
        bg=theme.CARD_BACKGROUND,
        fg=theme.PRIMARY
    ).pack(anchor="w", pady=(0, 18))

    fields_frame = tk.Frame(form.content, bg=theme.CARD_BACKGROUND)
    fields_frame.pack(fill="x")

    fields = [
        ("Route Name", 0, 0),
        ("Bus Number", 0, 1),
        ("Start Point", 2, 0),
        ("End Point", 2, 1),
        ("Driver Name", 4, 0),
        ("Driver Phone", 4, 1),
        ("Maximum Bus Capacity", 6, 0)
    ]

    entries = {}

    for label, row, column in fields:

        tk.Label(
            fields_frame,
            text=label,
            font=("Segoe UI", 10, "bold"),
            bg=theme.CARD_BACKGROUND,
            fg=theme.TEXT_PRIMARY
        ).grid(
            row=row,
            column=column,
            sticky="w",
            padx=(0, 20),
            pady=(0, 5)
        )

        entry = RoundedEntry(fields_frame, font=("Segoe UI", 10))
        entry.grid(
            row=row + 1,
            column=column,
            sticky="ew",
            padx=(0, 20),
            pady=(0, 16)
        )

        entries[label] = entry

    fields_frame.grid_columnconfigure(0, weight=1)
    fields_frame.grid_columnconfigure(1, weight=1)

    route_entry = entries["Route Name"]
    bus_entry = entries["Bus Number"]
    start_point_entry = entries["Start Point"]
    end_point_entry = entries["End Point"]
    driver_entry = entries["Driver Name"]
    phone_entry = entries["Driver Phone"]
    capacity_entry = entries["Maximum Bus Capacity"]

    preview_title = tk.StringVar(master=routes_page, value="Route name")
    preview_bus = tk.StringVar(master=routes_page, value="BUS NUMBER")
    preview_values = {
        "Start point": tk.StringVar(master=routes_page, value="Not set"),
        "End point": tk.StringVar(master=routes_page, value="Not set"),
        "Driver": tk.StringVar(master=routes_page, value="Driver name"),
        "Phone": tk.StringVar(master=routes_page, value="—"),
        "Seats": tk.StringVar(master=routes_page, value="—")
    }
    create_live_preview(
        editor_row,
        preview_title,
        preview_bus,
        tuple(preview_values.items()),
        icon="▣"
    )

    def sync_route_preview(event=None):

        preview_title.set(route_entry.get().strip() or "Route name")
        preview_bus.set(bus_entry.get().strip().upper() or "BUS NUMBER")
        preview_values["Start point"].set(
            start_point_entry.get().strip() or "Not set"
        )
        preview_values["End point"].set(
            end_point_entry.get().strip() or "Not set"
        )
        preview_values["Driver"].set(
            driver_entry.get().strip() or "Driver name"
        )
        preview_values["Phone"].set(
            phone_entry.get().strip() or "—"
        )
        preview_values["Seats"].set(
            capacity_entry.get().strip() or "—"
        )

    bind_preview_updates(entries.values(), sync_route_preview)

    selected_route_id = None

    # Route Table
    table_frame = RoundedPanel(
        routes_window,
        bg=theme.CARD_BACKGROUND,
        padx=20,
        pady=20
    )
    table_frame.pack(
        fill="both",
        expand=True,
        padx=30,
        pady=(0, 25)
    )

    tk.Label(
        table_frame.content,
        text="Registered Bus Routes",
        font=("Segoe UI", 14, "bold"),
        bg=theme.CARD_BACKGROUND,
        fg=theme.PRIMARY
    ).pack(anchor="w")

    columns = (
        "route_name",
        "start_point",
        "end_point",
        "bus_no",
        "driver_name",
        "driver_phone",
        "capacity",
        "action"
    )

    table_container = tk.Frame(table_frame.content, bg=theme.CARD_BACKGROUND)
    route_table = ttk.Treeview(
        table_container,
        columns=columns,
        show="headings",
        height=8
    )
    prepare_treeview_hover(route_table)
    route_tree_style_name = f"Routes{id(route_table)}.Treeview"
    route_tree_style = ttk.Style(route_table)
    route_tree_style.map(
        route_tree_style_name,
        background=[("selected", theme.ROW_EDITING)],
        foreground=[("selected", theme.TEXT_PRIMARY)]
    )
    route_table.configure(style=route_tree_style_name)
    route_table.tag_configure(
        "_editing",
        background=theme.ROW_EDITING,
        foreground=theme.TEXT_PRIMARY
    )

    headings = {
        "route_name": ("Route Name", 120),
        "start_point": ("Start Point", 130),
        "end_point": ("End Point", 130),
        "bus_no": ("Bus Number", 110),
        "driver_name": ("Driver Name", 130),
        "driver_phone": ("Driver Phone", 110),
        "capacity": ("Capacity", 80),
        "action": ("Action", 80)
    }

    for column, (heading, width) in headings.items():
        route_table.heading(column, text=heading)
        route_table.column(column, width=width, anchor="center")

# Search Routes
    search_frame = tk.Frame(
        table_frame.content,
        bg=theme.CARD_BACKGROUND
    )
    search_frame.pack(fill="x", pady=(15, 5))

    search_entry = RoundedEntry(
        search_frame,
        font=("Segoe UI", 10),
        width=35
    )
    search_entry.pack(side="left", padx=(0, 10))

    search_button = RoundedButton(
        search_frame,
        text="Search",
        font=("Segoe UI", 9, "bold"),
        bg=theme.SECONDARY,
        fg=theme.TEXT_LIGHT,
        relief="flat",
        padx=15,
        pady=6,
        cursor="hand2"
    )
    search_button.pack(side="left")

    update_button = RoundedButton(
        search_frame,
        text="Update Route",
        font=("Segoe UI", 9, "bold"),
        bg=theme.PRIMARY,
        fg=theme.TEXT_LIGHT,
        relief="flat",
        padx=15,
        pady=6,
        cursor="hand2"
    )
    update_button.pack(side="left", padx=(8, 0))

    table_scrollbar_y = ttk.Scrollbar(
        table_container,
        orient="vertical",
        command=route_table.yview
    )
    table_scrollbar_x = ttk.Scrollbar(
        table_container,
        orient="horizontal",
        command=route_table.xview
    )
    route_table.configure(
        yscrollcommand=table_scrollbar_y.set,
        xscrollcommand=table_scrollbar_x.set
    )
    table_container.grid_rowconfigure(0, weight=1)
    table_container.grid_columnconfigure(0, weight=1)
    route_table.grid(row=0, column=0, sticky="nsew", pady=(15, 0))
    table_scrollbar_y.grid(row=0, column=1, sticky="ns", pady=(15, 0))
    table_scrollbar_x.grid(row=1, column=0, sticky="ew")
    table_container.pack(fill="both", expand=True, pady=(15, 0))

    def clear_editing_row():

        for item in route_table.get_children():
            tags = route_table.item(item, "tags")
            if "_editing" in tags:
                route_table.item(
                    item,
                    tags=tuple(tag for tag in tags if tag != "_editing")
                )

    def select_route(event):

        nonlocal selected_route_id

        clear_editing_row()
        selected = route_table.selection()

        if not selected:
            selected_route_id = None
            return

        selected_route_id = int(selected[0])
        tags = route_table.item(selected[0], "tags")
        route_table.item(
            selected[0],
            tags=("_editing",) + tuple(
                tag for tag in tags if tag != "_editing"
            )
        )

        values = route_table.item(selected[0], "values")

        route_entry.delete(0, tk.END)
        route_entry.insert(0, values[0])

        start_point_entry.delete(0, tk.END)
        start_point_entry.insert(0, values[1] or "")

        end_point_entry.delete(0, tk.END)
        end_point_entry.insert(0, values[2] or "")

        bus_entry.delete(0, tk.END)
        bus_entry.insert(0, values[3])

        driver_entry.delete(0, tk.END)
        driver_entry.insert(0, values[4])

        phone_entry.delete(0, tk.END)
        phone_entry.insert(0, values[5])

        capacity_entry.delete(0, tk.END)
        capacity_entry.insert(0, values[6])
        sync_route_preview()

    route_table.bind("<<TreeviewSelect>>", select_route)
    
    def update_route():

        nonlocal selected_route_id

        if selected_route_id is None:
            messagebox.showwarning(
                "Select Route",
                "Please select a route from the table first.",
                parent=routes_window.winfo_toplevel()
            )
            return

        route_name = route_entry.get().strip()
        bus_no = bus_entry.get().strip().upper()
        start_point = start_point_entry.get().strip()
        end_point = end_point_entry.get().strip()
        driver_name = driver_entry.get().strip()
        driver_phone = phone_entry.get().strip()
        capacity_text = capacity_entry.get().strip()

        if not all([
            route_name,
            bus_no,
            start_point,
            end_point,
            driver_name,
            driver_phone,
            capacity_text
        ]):
            messagebox.showwarning(
                "Missing Information",
                "Please fill in all fields.",
                parent=routes_window.winfo_toplevel()
            )
            return

        if not driver_phone.isdigit() or len(driver_phone) != 10:
            messagebox.showwarning(
                "Invalid Phone Number",
                "Enter a valid 10-digit phone number.",
                parent=routes_window.winfo_toplevel()
            )
            return

        try:
            capacity = int(capacity_text)
            if capacity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Invalid Capacity",
                "Enter a positive whole number.",
                parent=routes_window.winfo_toplevel()
            )
            return

        connection = None

        try:
            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute("""
                UPDATE routes
                SET route_name = ?,
                    start_point = ?,
                    end_point = ?,
                    bus_no = ?,
                    driver_name = ?,
                    driver_phone = ?,
                    max_capacity = ?
                WHERE route_id = ?
            """, (
                route_name,
                start_point,
                end_point,
                bus_no,
                driver_name,
                driver_phone,
                capacity,
                selected_route_id
            ))

            connection.commit()

        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Duplicate Route or Bus",
                "This route name or bus number already exists.",
                parent=routes_window.winfo_toplevel()
            )
            return

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Unable to update route:\n{error}",
                parent=routes_window.winfo_toplevel()
            )
            return

        finally:
            if connection:
                connection.close()

        selected_route_id = None
        load_routes()

        clear_route_form()

        messagebox.showinfo(
            "Success",
            "Route updated successfully!",
            parent=routes_window.winfo_toplevel()
        )

    update_button.config(
        command=update_route
    )


    # Load Routes
    def load_routes(animate_counts=False):

        cancel_count_animation()

        for item in route_table.get_children():
            route_table.delete(item)

        connection = None

        try:
            connection = get_connection()
            cursor = connection.cursor()

            search_term = search_entry.get().strip()
            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(max_capacity), 0)
                FROM routes
            """)
            route_count, total_seats = cursor.fetchone()
            if not animate_counts:
                route_count_value.set(str(route_count))
                total_seats_value.set(str(total_seats))

            cursor.execute("""
                SELECT
                    route_id,
                    route_name,
                    start_point,
                    end_point,
                    bus_no,
                    driver_name,
                    driver_phone,
                    max_capacity
                FROM routes
                WHERE route_name LIKE ?
                   OR start_point LIKE ?
                   OR end_point LIKE ?
                   OR bus_no LIKE ?
                   OR driver_name LIKE ?
                ORDER BY route_id DESC
            """, (
                f"%{search_term}%",
                f"%{search_term}%",
                f"%{search_term}%",
                f"%{search_term}%",
                f"%{search_term}%"
            ))

            for route in cursor.fetchall():
                route_table.insert(
                    "",
                    "end",
                    iid=str(route[0]),
                    values=tuple(value or "" for value in route[1:]) + (
                        "Edit",
                    )
                )

            if animate_counts:
                animate_count_values(route_count, total_seats)

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Unable to load routes:\n{error}",
                parent=routes_window.winfo_toplevel()
            )

        finally:
            if connection:
                connection.close()

    search_button.config(
        command=load_routes
    )

    search_entry.bind(
        "<Return>",
        lambda event: load_routes()
    )

    def clear_route_form():

        nonlocal selected_route_id

        selected_route_id = None
        clear_editing_row()
        selected = route_table.selection()
        if selected:
            route_table.selection_remove(*selected)
        for entry in entries.values():
            entry.delete(0, tk.END)
        sync_route_preview()

    # Save Route
    def save_route():

        route_name = route_entry.get().strip()
        bus_no = bus_entry.get().strip().upper()
        start_point = start_point_entry.get().strip()
        end_point = end_point_entry.get().strip()
        driver_name = driver_entry.get().strip()
        driver_phone = phone_entry.get().strip()
        capacity_text = capacity_entry.get().strip()

        if not all([
            route_name,
            bus_no,
            start_point,
            end_point,
            driver_name,
            driver_phone,
            capacity_text
        ]):
            messagebox.showwarning(
                "Missing Information",
                "Please fill in all fields.",
                parent=routes_window.winfo_toplevel()
            )
            return

        if not driver_phone.isdigit() or len(driver_phone) != 10:
            messagebox.showwarning(
                "Invalid Phone Number",
                "Enter a valid 10-digit phone number.",
                parent=routes_window.winfo_toplevel()
            )
            return

        try:
            capacity = int(capacity_text)
            if capacity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Invalid Capacity",
                "Bus capacity must be a positive whole number.",
                parent=routes_window.winfo_toplevel()
            )
            return

        connection = None

        try:
            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute("""
                INSERT INTO routes (
                    route_name,
                    start_point,
                    end_point,
                    bus_no,
                    driver_name,
                    driver_phone,
                    max_capacity
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                route_name,
                start_point,
                end_point,
                bus_no,
                driver_name,
                driver_phone,
                capacity
            ))

            connection.commit()

        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Duplicate Route or Bus",
                "This route name or bus number already exists.",
                parent=routes_window.winfo_toplevel()
            )
            return

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Unable to save route:\n{error}",
                parent=routes_window.winfo_toplevel()
            )
            return

        finally:
            if connection:
                connection.close()

        load_routes()

        messagebox.showinfo(
            "Success",
            "Bus route added successfully!",
            parent=routes_window.winfo_toplevel()
        )

        clear_route_form()

        route_entry.focus_set()

    route_actions = tk.Frame(form.content, bg=theme.CARD_BACKGROUND)
    route_actions.pack(anchor="w", pady=(5, 0))
    RoundedButton(
        route_actions,
        text="Save Route",
        font=("Segoe UI", 10, "bold"),
        bg=theme.PRIMARY,
        fg=theme.TEXT_LIGHT,
        activebackground=theme.SECONDARY,
        activeforeground=theme.TEXT_LIGHT,
        relief="flat",
        padx=25,
        pady=10,
        cursor="hand2",
        command=save_route
    ).pack(side="left")
    RoundedButton(
        route_actions,
        text="Clear form",
        font=("Segoe UI", 9, "bold"),
        bg=theme.GLASS_FIELD,
        fg=theme.TEXT_PRIMARY,
        activebackground=theme.PALE_GREEN,
        activeforeground=theme.TEXT_PRIMARY,
        relief="flat",
        padx=18,
        pady=9,
        cursor="hand2",
        command=clear_route_form
    ).pack(side="left", padx=(8, 0))

    load_routes(animate_counts=True)
    route_entry.focus_set()
    module_header._navigation_heading_meta["rest_widgets"] = tuple(
        widget
        for widget in routes_window.winfo_children()
        if widget is not module_header
    )
    routes_page._navigation_heading_meta = (
        module_header._navigation_heading_meta
    )
    apply_interactive_effects(routes_page, fade=False)
    return routes_page
