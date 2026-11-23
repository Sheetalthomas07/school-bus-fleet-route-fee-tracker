import math
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

from database.db_connection import get_connection
from utils import theme
from utils.ui_effects import apply_interactive_effects, prepare_treeview_hover
from utils.rounded_widgets import (
    RoundedButton,
    RoundedCombobox,
    RoundedEntry,
    RoundedPanel,
    ScrollableFrame
)
from utils.module_ui import (
    bind_preview_updates,
    create_live_preview,
    create_module_header
)

def open_stops_module(parent):

    stops_page = ScrollableFrame(parent, bg=theme.BACKGROUND)
    stops_window = stops_page.content

    stop_count_value = tk.StringVar(master=stops_page, value="0")
    route_count_value = tk.StringVar(master=stops_page, value="0")
    create_module_header(
        stops_window,
        "Bus Stops Management",
        "Manage bus stops, route distances and student transport fees.",
        (
            (stop_count_value, "Stops"),
            (route_count_value, "Routes")
        )
    )

        # Add Bus Stop Form
    editor_row = tk.Frame(stops_window, bg=theme.BACKGROUND)
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
        text="Add New Bus Stop",
        font=("Segoe UI", 14, "bold"),
        bg=theme.CARD_BACKGROUND,
        fg=theme.PRIMARY
    ).pack(anchor="w", pady=(0, 18))

        # Bus Stop Input Fields
    fields_frame = tk.Frame(form.content, bg=theme.CARD_BACKGROUND)
    fields_frame.pack(fill="x")

    # Field Labels
    field_labels = [
        ("Select Route", 0, 0),
        ("Stop Name", 0, 1),
        ("Distance (KM)", 2, 0),
        ("Term Fee (₹)", 2, 1)
    ]

    for label, row, column in field_labels:
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

            # Route Dropdown
    route_combo = RoundedCombobox(
        fields_frame,
        font=("Segoe UI", 10),
        state="readonly"
    )
    route_combo.grid(
        row=1,
        column=0,
        sticky="ew",
        padx=(0, 20),
        pady=(0, 16)
    )

        # Stop Name Entry
    stop_name_entry = RoundedEntry(
        fields_frame,
        font=("Segoe UI", 10)
    )
    stop_name_entry.grid(
        row=1,
        column=1,
        sticky="ew",
        padx=(0, 20),
        pady=(0, 16)
    )

        # Distance Entry
    distance_entry = RoundedEntry(
        fields_frame,
        font=("Segoe UI", 10)
    )
    distance_entry.grid(
        row=3,
        column=0,
        sticky="ew",
        padx=(0, 20),
        pady=(0, 16)
    )

        # Term Fee Entry
    fee_entry = RoundedEntry(
        fields_frame,
        font=("Segoe UI", 10)
    )
    fee_entry.grid(
        row=3,
        column=1,
        sticky="ew",
        padx=(0, 20),
        pady=(0, 16)
    )

    preview_title = tk.StringVar(master=stops_page, value="Stop name")
    preview_badge = tk.StringVar(master=stops_page, value="SELECT ROUTE")
    preview_values = {
        "Route": tk.StringVar(master=stops_page, value="—"),
        "Distance": tk.StringVar(master=stops_page, value="—"),
        "Term fee": tk.StringVar(master=stops_page, value="—")
    }
    create_live_preview(
        editor_row,
        preview_title,
        preview_badge,
        tuple(preview_values.items()),
        icon="⌖"
    )

    def sync_stop_preview(event=None):

        preview_title.set(stop_name_entry.get().strip() or "Stop name")
        preview_badge.set(route_combo.get().strip() or "SELECT ROUTE")
        preview_values["Route"].set(
            route_combo.get().strip() or "Not selected"
        )
        distance = distance_entry.get().strip()
        preview_values["Distance"].set(
            f"{distance} km" if distance else "—"
        )
        fee = fee_entry.get().strip()
        preview_values["Term fee"].set(
            f"₹{fee}" if fee else "—"
        )

    bind_preview_updates(
        (route_combo, stop_name_entry, distance_entry, fee_entry),
        sync_stop_preview
    )

        # Bus Stops Table
    table_frame = RoundedPanel(
        stops_window,
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
        text="Registered Bus Stops",
        font=("Segoe UI", 14, "bold"),
        bg=theme.CARD_BACKGROUND,
        fg=theme.PRIMARY
    ).pack(anchor="w")

        # Search Bus Stops
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
        text="Update Stop",
        font=("Segoe UI", 9, "bold"),
        bg=theme.PRIMARY,
        fg=theme.TEXT_LIGHT,
        relief="flat",
        padx=15,
        pady=6,
        cursor="hand2"
    )
    update_button.pack(side="left", padx=(8, 0))

    delete_button = RoundedButton(
        search_frame,
        text="Delete Stop",
        font=("Segoe UI", 9, "bold"),
        bg=theme.DANGER,
        fg=theme.TEXT_LIGHT,
        relief="flat",
        padx=15,
        pady=6,
        cursor="hand2"
    )
    delete_button.pack(side="left", padx=(8, 0))

    # Table Columns
    columns = (
        "route_name",
        "bus_no",
        "stop_name",
        "distance",
        "term_fee"
    )

    table_container = tk.Frame(table_frame.content, bg=theme.CARD_BACKGROUND)
    stop_table = ttk.Treeview(
        table_container,
        columns=columns,
        show="headings",
        height=8
    )
    prepare_treeview_hover(stop_table)

    headings = {
        "route_name": ("Route Name", 150),
        "bus_no": ("Bus Number", 150),
        "stop_name": ("Stop Name", 180),
        "distance": ("Distance (KM)", 120),
        "term_fee": ("Term Fee (₹)", 120)
    }

    for column, (heading, width) in headings.items():
        stop_table.heading(column, text=heading)
        stop_table.column(column, width=width, anchor="center")

            # Table Scrollbar
    scrollbar_y = ttk.Scrollbar(
        table_container,
        orient="vertical",
        command=stop_table.yview
    )
    scrollbar_x = ttk.Scrollbar(
        table_container,
        orient="horizontal",
        command=stop_table.xview
    )
    stop_table.configure(
        yscrollcommand=scrollbar_y.set,
        xscrollcommand=scrollbar_x.set
    )

    table_container.grid_rowconfigure(0, weight=1)
    table_container.grid_columnconfigure(0, weight=1)
    stop_table.grid(row=0, column=0, sticky="nsew", pady=(15, 0))
    scrollbar_y.grid(row=0, column=1, sticky="ns", pady=(15, 0))
    scrollbar_x.grid(row=1, column=0, sticky="ew")
    table_container.pack(fill="both", expand=True)

    # Load Routes into Dropdown
    route_options = {}

    # Selected Bus Stop
    selected_stop_id = None

    # Select Bus Stop from Table
    def select_stop(event):

        nonlocal selected_stop_id

        selected = stop_table.selection()

        if not selected:
            return

        selected_stop_id = int(selected[0])

        values = stop_table.item(selected[0], "values")

        route_name = values[0]
        bus_no = values[1]

        route_combo.set(f"{route_name} - {bus_no}")

        stop_name_entry.delete(0, tk.END)
        stop_name_entry.insert(0, values[2])

        distance_entry.delete(0, tk.END)
        distance_entry.insert(0, values[3])

        fee_entry.delete(0, tk.END)
        fee_entry.insert(0, values[4])
        sync_stop_preview()

    stop_table.bind("<<TreeviewSelect>>", select_stop)

    def load_routes_dropdown():

        connection = None

        try:
            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute("""
                SELECT route_id, route_name, bus_no
                FROM routes
                ORDER BY route_name
            """)

            routes = cursor.fetchall()

            route_options.clear()

            route_values = []

            for route_id, route_name, bus_no in routes:

                display_name = f"{route_name} - {bus_no}"

                route_options[display_name] = route_id
                route_values.append(display_name)

            route_combo["values"] = route_values

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Unable to load routes:\n{error}",
                parent=stops_window.winfo_toplevel()
            )

        finally:
            if connection:
                connection.close()

    def clear_stop_form():

        nonlocal selected_stop_id

        selected_stop_id = None
        selected = stop_table.selection()
        if selected:
            stop_table.selection_remove(*selected)

        route_combo.set("")
        stop_name_entry.delete(0, tk.END)
        distance_entry.delete(0, tk.END)
        fee_entry.delete(0, tk.END)
        sync_stop_preview()

    # Load Registered Bus Stops
    def load_stops():

        clear_stop_form()

        for item in stop_table.get_children():
            stop_table.delete(item)

        connection = None

        try:
            connection = get_connection()
            cursor = connection.cursor()

            search_term = search_entry.get().strip()
            cursor.execute("SELECT COUNT(*) FROM stops")
            stop_count_value.set(str(cursor.fetchone()[0]))
            cursor.execute("SELECT COUNT(*) FROM routes")
            route_count_value.set(str(cursor.fetchone()[0]))

            cursor.execute("""
                SELECT
                    stops.stop_id,
                    routes.route_name,
                    routes.bus_no,
                    stops.stop_name,
                    stops.distance_km,
                    stops.term_fee
                FROM stops
                JOIN routes
                    ON stops.route_id = routes.route_id
                WHERE routes.route_name LIKE ?
                   OR routes.bus_no LIKE ?
                   OR stops.stop_name LIKE ?
                ORDER BY routes.route_name, stops.distance_km, stops.stop_id
            """, (
                f"%{search_term}%",
                f"%{search_term}%",
                f"%{search_term}%"
            ))

            for stop in cursor.fetchall():
                stop_table.insert(
                    "",
                    "end",
                    iid=str(stop[0]),
                    values=stop[1:]
                )

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Unable to load bus stops:\n{error}",
                parent=stops_window.winfo_toplevel()
            )

        finally:
            if connection:
                connection.close()

    # Connect Search Button
    search_button.config(command=load_stops)

    search_entry.bind(
        "<Return>",
        lambda event: load_stops()
    )

    # Save Bus Stop
    def save_stop():

        selected_route = route_combo.get().strip()
        stop_name = stop_name_entry.get().strip()
        distance_text = distance_entry.get().strip()
        fee_text = fee_entry.get().strip()

        if not all([
            selected_route,
            stop_name,
            distance_text,
            fee_text
        ]):
            messagebox.showwarning(
                "Missing Information",
                "Please fill in all fields.",
                parent=stops_window.winfo_toplevel()
            )
            return

        # Validate Distance and Term Fee
        try:
            distance = float(distance_text)
            term_fee = float(fee_text)

            if (
                not math.isfinite(distance)
                or not math.isfinite(term_fee)
                or distance < 0
                or term_fee < 0
            ):
                raise ValueError

        except ValueError:
            messagebox.showwarning(
                "Invalid Input",
                "Distance and term fee must be valid non-negative numbers.",
                parent=stops_window.winfo_toplevel()
            )
            return

        # Get Selected Route ID
        route_id = route_options.get(selected_route)

        if route_id is None:
            messagebox.showwarning(
                "Invalid Route",
                "Please select a valid registered route.",
                parent=stops_window.winfo_toplevel()
            )
            return

        # Save Stop to Database
        connection = None

        try:
            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute("""
                INSERT INTO stops (
                    route_id,
                    stop_name,
                    distance_km,
                    term_fee
                )
                VALUES (?, ?, ?, ?)
            """, (
                route_id,
                stop_name,
                distance,
                term_fee
            ))

            connection.commit()

        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Duplicate Bus Stop",
                "This stop already exists under the selected route.",
                parent=stops_window.winfo_toplevel()
            )
            return

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Unable to save bus stop:\n{error}",
                parent=stops_window.winfo_toplevel()
            )
            return

        finally:
            if connection:
                connection.close()

        # Refresh Table and Clear Form
        load_stops()

        messagebox.showinfo(
            "Success",
            "Bus stop added successfully!",
            parent=stops_window.winfo_toplevel()
        )

    # Update Bus Stop
    def update_stop():

        nonlocal selected_stop_id

        if selected_stop_id is None:
            messagebox.showwarning(
                "Select Bus Stop",
                "Please select a bus stop from the table first.",
                parent=stops_window.winfo_toplevel()
            )
            return

        selected_route = route_combo.get().strip()
        stop_name = stop_name_entry.get().strip()
        distance_text = distance_entry.get().strip()
        fee_text = fee_entry.get().strip()

        if not all([
            selected_route,
            stop_name,
            distance_text,
            fee_text
        ]):
            messagebox.showwarning(
                "Missing Information",
                "Please fill in all fields.",
                parent=stops_window.winfo_toplevel()
            )
            return

        try:
            distance = float(distance_text)
            term_fee = float(fee_text)
            if (
                not math.isfinite(distance)
                or not math.isfinite(term_fee)
                or distance < 0
                or term_fee < 0
            ):
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Invalid Input",
                "Distance and term fee must be valid non-negative numbers.",
                parent=stops_window.winfo_toplevel()
            )
            return

        route_id = route_options.get(selected_route)
        if route_id is None:
            messagebox.showwarning(
                "Invalid Route",
                "Please select a valid registered route.",
                parent=stops_window.winfo_toplevel()
            )
            return

        connection = None
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("BEGIN IMMEDIATE")
            cursor.execute(
                "SELECT route_id FROM stops WHERE stop_id = ?",
                (selected_stop_id,)
            )
            existing_stop = cursor.fetchone()

            if existing_stop is None:
                messagebox.showerror(
                    "Bus Stop Not Found",
                    "The selected bus stop no longer exists. Refresh the list and try again.",
                    parent=stops_window.winfo_toplevel()
                )
                return

            if existing_stop[0] != route_id:
                cursor.execute(
                    "SELECT 1 FROM student_transport WHERE stop_id = ? LIMIT 1",
                    (selected_stop_id,)
                )
                if cursor.fetchone() is not None:
                    messagebox.showwarning(
                        "Stop Has Allocated Students",
                        "Reassign the students using this stop before changing its route.",
                        parent=stops_window.winfo_toplevel()
                    )
                    return

            cursor.execute("""
                UPDATE stops
                SET route_id = ?,
                    stop_name = ?,
                    distance_km = ?,
                    term_fee = ?
                WHERE stop_id = ?
            """, (
                route_id,
                stop_name,
                distance,
                term_fee,
                selected_stop_id
            ))

            if cursor.rowcount == 0:
                messagebox.showerror(
                    "Bus Stop Not Found",
                    "The selected bus stop no longer exists. Refresh the list and try again.",
                    parent=stops_window.winfo_toplevel()
                )
                return

            cursor.execute("""
                UPDATE student_transport
                SET dues = MAX(0, ? - fee_paid),
                    credit_balance = MAX(0, fee_paid - ?)
                WHERE stop_id = ?
                  AND transport_status = 'Active'
            """, (
                term_fee,
                term_fee,
                selected_stop_id
            ))

            connection.commit()

        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Duplicate Bus Stop",
                "This stop already exists under the selected route.",
                parent=stops_window.winfo_toplevel()
            )
            return

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Unable to update bus stop:\n{error}",
                parent=stops_window.winfo_toplevel()
            )
            return

        finally:
            if connection:
                connection.close()

        load_stops()
        messagebox.showinfo(
            "Success",
            "Bus stop updated successfully!",
            parent=stops_window.winfo_toplevel()
        )

    def delete_stop():

        nonlocal selected_stop_id

        if selected_stop_id is None:
            messagebox.showwarning(
                "Select Bus Stop",
                "Please select a bus stop from the table first.",
                parent=stops_window.winfo_toplevel()
            )
            return

        stop_name = stop_name_entry.get().strip()
        if not messagebox.askyesno(
            "Delete Bus Stop",
            f"Are you sure you want to delete '{stop_name}'?",
            parent=stops_window.winfo_toplevel()
        ):
            return

        connection = None
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute(
                "DELETE FROM stops WHERE stop_id = ?",
                (selected_stop_id,)
            )

            if cursor.rowcount == 0:
                messagebox.showerror(
                    "Bus Stop Not Found",
                    "The selected bus stop no longer exists. Refresh the list and try again.",
                    parent=stops_window.winfo_toplevel()
                )
                return

            connection.commit()

        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Bus Stop In Use",
                "This bus stop is assigned to one or more students and cannot be deleted.",
                parent=stops_window.winfo_toplevel()
            )
            return

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Unable to delete bus stop:\n{error}",
                parent=stops_window.winfo_toplevel()
            )
            return

        finally:
            if connection:
                connection.close()

        load_stops()
        messagebox.showinfo(
            "Success",
            "Bus stop deleted successfully.",
            parent=stops_window.winfo_toplevel()
        )

    update_button.config(command=update_stop)
    delete_button.config(command=delete_stop)

    # Save Bus Stop Button
    RoundedButton(
        form.content,
        text="Save Bus Stop",
        font=("Segoe UI", 10, "bold"),
        bg=theme.PRIMARY,
        fg=theme.TEXT_LIGHT,
        activebackground=theme.SECONDARY,
        activeforeground=theme.TEXT_LIGHT,
        relief="flat",
        padx=25,
        pady=10,
        cursor="hand2",
        command=save_stop
    ).pack(anchor="w", pady=(5, 0))

    # Initial Data Loading
    load_routes_dropdown()
    load_stops()

    stop_name_entry.focus_set()        

    fields_frame.grid_columnconfigure(0, weight=1)
    fields_frame.grid_columnconfigure(1, weight=1)
    apply_interactive_effects(stops_page, fade=False)
    return stops_page