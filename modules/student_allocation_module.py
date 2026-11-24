import sqlite3
import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

from database.db_connection import get_connection
from utils import theme
from utils.fee_status import get_fee_status
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
    create_module_header,
    bind_module_navigation
)


def open_student_allocation_module(parent, on_change=None):

    allocation_page = ScrollableFrame(parent, bg=theme.BACKGROUND)
    allocation_window = allocation_page.content

    allocation_count_value = tk.StringVar(master=allocation_page, value="0")
    active_count_value = tk.StringVar(master=allocation_page, value="0")
    create_module_header(
        allocation_window,
        "Student Transport Allocations",
        "Assign students to bus stops and manage their transport passes.",
        (
            (allocation_count_value, "Allocations"),
            (active_count_value, "Active")
        )
    )

    editor_row = tk.Frame(allocation_window, bg=theme.BACKGROUND)
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
        text="Student Allocation Details",
        font=("Segoe UI", 14, "bold"),
        bg=theme.CARD_BACKGROUND,
        fg=theme.PRIMARY
    ).pack(anchor="w", pady=(0, 18))

    fields_frame = tk.Frame(form.content, bg=theme.CARD_BACKGROUND)
    fields_frame.pack(fill="x")

    field_specs = [
        ("Registration Number", 0, 0),
        ("Student Name", 0, 1),
        ("Route", 2, 0),
        ("Bus Stop", 2, 1),
        ("Pass Valid Until (YYYY-MM-DD, optional)", 4, 0)
    ]

    for label, row, column in field_specs:
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

    reg_no_entry = RoundedEntry(fields_frame, font=("Segoe UI", 10))
    reg_no_entry.grid(
        row=1, column=0, sticky="ew", padx=(0, 20), pady=(0, 16)
    )

    student_name_entry = RoundedEntry(fields_frame, font=("Segoe UI", 10))
    student_name_entry.grid(
        row=1, column=1, sticky="ew", padx=(0, 20), pady=(0, 16)
    )

    route_combo = RoundedCombobox(
        fields_frame,
        font=("Segoe UI", 10),
        state="readonly"
    )
    route_combo.grid(
        row=3, column=0, sticky="ew", padx=(0, 20), pady=(0, 16)
    )

    stop_combo = RoundedCombobox(
        fields_frame,
        font=("Segoe UI", 10),
        state="readonly"
    )
    stop_combo.grid(
        row=3, column=1, sticky="ew", padx=(0, 20), pady=(0, 16)
    )

    pass_valid_entry = RoundedEntry(fields_frame, font=("Segoe UI", 10))
    pass_valid_entry.grid(
        row=5, column=0, sticky="ew", padx=(0, 20), pady=(0, 16)
    )

    fields_frame.grid_columnconfigure(0, weight=1)
    fields_frame.grid_columnconfigure(1, weight=1)

    preview_title = tk.StringVar(
        master=allocation_page,
        value="Student name"
    )
    preview_badge = tk.StringVar(
        master=allocation_page,
        value="REGISTRATION NO."
    )
    preview_values = {
        "Route": tk.StringVar(master=allocation_page, value="—"),
        "Bus stop": tk.StringVar(master=allocation_page, value="—"),
        "Pass valid until": tk.StringVar(master=allocation_page, value="—")
    }
    create_live_preview(
        editor_row,
        preview_title,
        preview_badge,
        tuple(preview_values.items()),
        icon="♙"
    )

    def sync_allocation_preview(event=None):

        preview_title.set(
            student_name_entry.get().strip() or "Student name"
        )
        preview_badge.set(
            reg_no_entry.get().strip().upper() or "REGISTRATION NO."
        )
        preview_values["Route"].set(
            route_combo.get().strip() or "Not selected"
        )
        preview_values["Bus stop"].set(
            stop_combo.get().strip() or "Not selected"
        )
        preview_values["Pass valid until"].set(
            pass_valid_entry.get().strip() or "Not set"
        )

    bind_preview_updates(
        (
            reg_no_entry,
            student_name_entry,
            route_combo,
            stop_combo,
            pass_valid_entry
        ),
        sync_allocation_preview
    )

    table_frame = RoundedPanel(
        allocation_window,
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
        text="Registered Student Allocations",
        font=("Segoe UI", 14, "bold"),
        bg=theme.CARD_BACKGROUND,
        fg=theme.PRIMARY
    ).pack(anchor="w")

    search_frame = tk.Frame(table_frame.content, bg=theme.CARD_BACKGROUND)
    search_frame.pack(fill="x", pady=(15, 5))

    search_entry = RoundedEntry(search_frame, font=("Segoe UI", 10), width=35)
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
        text="Update Allocation",
        font=("Segoe UI", 9, "bold"),
        bg=theme.PRIMARY,
        fg=theme.TEXT_LIGHT,
        relief="flat",
        padx=15,
        pady=6,
        cursor="hand2"
    )
    update_button.pack(side="left", padx=(8, 0))

    discontinue_button = RoundedButton(
        search_frame,
        text="Discontinue Transport",
        font=("Segoe UI", 9, "bold"),
        bg=theme.DANGER,
        fg=theme.TEXT_LIGHT,
        relief="flat",
        padx=15,
        pady=6,
        cursor="hand2"
    )
    discontinue_button.pack(side="left", padx=(8, 0))

    reactivate_button = RoundedButton(
        search_frame,
        text="Reactivate Transport",
        font=("Segoe UI", 9, "bold"),
        bg=theme.SUCCESS,
        fg=theme.TEXT_LIGHT,
        relief="flat",
        padx=15,
        pady=6,
        cursor="hand2"
    )
    reactivate_button.pack(side="left", padx=(8, 0))

    delete_button = RoundedButton(
        search_frame,
        text="Delete Allocation",
        font=("Segoe UI", 9, "bold"),
        bg=theme.DANGER,
        fg=theme.TEXT_LIGHT,
        relief="flat",
        padx=15,
        pady=6,
        cursor="hand2"
    )
    delete_button.pack(side="left", padx=(8, 0))

    columns = (
        "reg_no",
        "student_name",
        "route_name",
        "bus_no",
        "stop_name",
        "term_fee",
        "fee_paid",
        "credit_balance",
        "dues",
        "fee_status",
        "pass_valid_until",
        "transport_status"
    )

    table_container = tk.Frame(table_frame.content, bg=theme.CARD_BACKGROUND)
    allocation_table = ttk.Treeview(
        table_container,
        columns=columns,
        show="headings",
        height=8
    )
    prepare_treeview_hover(allocation_table)

    headings = {
        "reg_no": ("Registration No.", 140),
        "student_name": ("Student Name", 180),
        "route_name": ("Route", 130),
        "bus_no": ("Bus Number", 130),
        "stop_name": ("Bus Stop", 160),
        "term_fee": ("Term Fee (₹)", 120),
        "fee_paid": ("Fee Paid (₹)", 120),
        "credit_balance": ("Credit (₹)", 120),
        "dues": ("Dues (₹)", 120),
        "fee_status": ("Fee Status", 140),
        "pass_valid_until": ("Pass Valid Until", 140),
        "transport_status": ("Transport Status", 140)
    }

    for column, (heading, width) in headings.items():
        allocation_table.heading(column, text=heading)
        allocation_table.column(column, width=width, anchor="center")

    scrollbar_y = ttk.Scrollbar(
        table_container,
        orient="vertical",
        command=allocation_table.yview
    )
    scrollbar_x = ttk.Scrollbar(
        table_container,
        orient="horizontal",
        command=allocation_table.xview
    )
    allocation_table.configure(
        yscrollcommand=scrollbar_y.set,
        xscrollcommand=scrollbar_x.set
    )

    table_container.grid_rowconfigure(0, weight=1)
    table_container.grid_columnconfigure(0, weight=1)
    allocation_table.grid(row=0, column=0, sticky="nsew", pady=(15, 0))
    scrollbar_y.grid(row=0, column=1, sticky="ns", pady=(15, 0))
    scrollbar_x.grid(row=1, column=0, sticky="ew")
    table_container.pack(fill="both", expand=True)

    route_options = {}
    stop_options = {}
    stop_display_by_id = {}
    allocation_stop_ids = {}
    selected_alloc_id = None

    def clear_form():

        nonlocal selected_alloc_id

        selected_alloc_id = None
        selected = allocation_table.selection()
        if selected:
            allocation_table.selection_remove(*selected)

        reg_no_entry.delete(0, tk.END)
        student_name_entry.delete(0, tk.END)
        route_combo.set("")
        stop_combo.set("")
        stop_combo["values"] = ()
        stop_options.clear()
        stop_display_by_id.clear()
        pass_valid_entry.delete(0, tk.END)
        sync_allocation_preview()

    def load_routes():

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
                display = f"{route_name} - {bus_no}"
                route_options[display] = route_id
                route_values.append(display)

            route_combo["values"] = route_values

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Unable to load routes:\n{error}",
                parent=allocation_window.winfo_toplevel()
            )

        finally:
            if connection:
                connection.close()

    def load_stops_for_route(route_id):

        connection = None

        stop_options.clear()
        stop_display_by_id.clear()
        stop_combo.set("")
        stop_combo["values"] = ()

        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("""
                SELECT stop_id, stop_name, distance_km, term_fee
                FROM stops
                WHERE route_id = ?
                ORDER BY distance_km, stop_name
            """, (route_id,))
            stops = cursor.fetchall()

            stop_values = []
            for stop_id, stop_name, distance_km, term_fee in stops:
                display = (
                    f"{stop_name} ({distance_km:g} km, "
                    f"₹{term_fee:,.2f})"
                )
                stop_options[display] = (stop_id, term_fee)
                stop_display_by_id[stop_id] = display
                stop_values.append(display)

            stop_combo["values"] = stop_values

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Unable to load stops for this route:\n{error}",
                parent=allocation_window.winfo_toplevel()
            )

        finally:
            if connection:
                connection.close()

    def get_route_capacity(cursor, route_id):

        cursor.execute(
            "SELECT max_capacity FROM routes WHERE route_id = ?",
            (route_id,)
        )
        route = cursor.fetchone()
        if route is None:
            return None

        cursor.execute("""
            SELECT COUNT(*)
            FROM student_transport st
            JOIN stops s ON st.stop_id = s.stop_id
            WHERE s.route_id = ?
              AND st.transport_status = 'Active'
        """, (route_id,))
        return route[0], cursor.fetchone()[0]

    def on_route_selected(event=None):

        route_id = route_options.get(route_combo.get())
        if route_id is None:
            stop_combo.set("")
            stop_combo["values"] = ()
            stop_options.clear()
            stop_display_by_id.clear()
            sync_allocation_preview()
            return

        load_stops_for_route(route_id)
        sync_allocation_preview()

    route_combo.bind("<<ComboboxSelected>>", on_route_selected)

    def load_allocations():

        clear_form()

        for item in allocation_table.get_children():
            allocation_table.delete(item)
        allocation_stop_ids.clear()

        connection = None

        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("""
                SELECT
                    COUNT(*),
                    COALESCE(SUM(
                        CASE WHEN transport_status = 'Active' THEN 1 ELSE 0 END
                    ), 0)
                FROM student_transport
            """)
            allocation_count, active_count = cursor.fetchone()
            allocation_count_value.set(str(allocation_count))
            active_count_value.set(str(active_count))
            search_term = f"%{search_entry.get().strip()}%"
            cursor.execute("""
                SELECT
                    st.alloc_id,
                    st.reg_no,
                    st.student_name,
                    r.route_name,
                    r.bus_no,
                    s.stop_name,
                    s.distance_km,
                    CASE
                        WHEN st.transport_status = 'Discontinued'
                        THEN st.fee_paid + st.dues - st.credit_balance
                        ELSE s.term_fee
                    END,
                    st.fee_paid,
                    st.credit_balance,
                    st.dues,
                    st.pass_valid_until,
                    st.stop_id,
                    st.transport_status
                FROM student_transport st
                JOIN stops s ON st.stop_id = s.stop_id
                JOIN routes r ON s.route_id = r.route_id
                WHERE st.reg_no LIKE ?
                   OR st.student_name LIKE ?
                   OR r.route_name LIKE ?
                   OR s.stop_name LIKE ?
                ORDER BY st.alloc_id DESC
            """, (
                search_term,
                search_term,
                search_term,
                search_term
            ))

            for allocation in cursor.fetchall():
                allocation_id = allocation[0]
                allocation_stop_ids[allocation_id] = allocation[12]
                fee_status = get_fee_status(
                    allocation[10],
                    allocation[9]
                )

                allocation_table.insert(
                    "",
                    "end",
                    iid=str(allocation_id),
                    values=(
                        allocation[1],
                        allocation[2],
                        allocation[3],
                        allocation[4],
                        allocation[5],
                        f"{allocation[7]:,.2f}",
                        f"{allocation[8]:,.2f}",
                        f"{allocation[9]:,.2f}",
                        f"{allocation[10]:,.2f}",
                        fee_status,
                        allocation[11] or "",
                        allocation[13]
                    )
                )

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Unable to load student allocations:\n{error}",
                parent=allocation_window.winfo_toplevel()
            )

        finally:
            if connection:
                connection.close()

    def select_allocation(event):

        nonlocal selected_alloc_id

        selected = allocation_table.selection()
        if not selected:
            return

        selected_alloc_id = int(selected[0])
        values = allocation_table.item(selected[0], "values")
        stop_id = allocation_stop_ids.get(selected_alloc_id)

        reg_no_entry.delete(0, tk.END)
        reg_no_entry.insert(0, values[0])
        student_name_entry.delete(0, tk.END)
        student_name_entry.insert(0, values[1])
        pass_valid_entry.delete(0, tk.END)
        pass_valid_entry.insert(0, values[10])

        route_display = f"{values[2]} - {values[3]}"
        route_combo.set(route_display)
        route_id = route_options.get(route_display)
        if route_id is not None:
            load_stops_for_route(route_id)
            stop_display = stop_display_by_id.get(stop_id)
            if stop_display is not None:
                stop_combo.set(stop_display)
        sync_allocation_preview()

    allocation_table.bind("<<TreeviewSelect>>", select_allocation)

    def get_form_values():

        reg_no = reg_no_entry.get().strip()
        student_name = student_name_entry.get().strip()
        selected_route = route_combo.get().strip()
        selected_stop = stop_combo.get().strip()
        pass_valid_until = pass_valid_entry.get().strip()

        if not all([reg_no, student_name, selected_route, selected_stop]):
            messagebox.showwarning(
                "Missing Information",
                "Enter the registration number and student name, then select a route and stop.",
                parent=allocation_window.winfo_toplevel()
            )
            return None

        stop = stop_options.get(selected_stop)
        if stop is None:
            messagebox.showwarning(
                "Invalid Stop",
                "Select a valid bus stop for the selected route.",
                parent=allocation_window.winfo_toplevel()
            )
            return None

        if pass_valid_until:
            try:
                parsed_date = date.fromisoformat(pass_valid_until)
                if parsed_date.isoformat() != pass_valid_until:
                    raise ValueError
            except ValueError:
                messagebox.showwarning(
                    "Invalid Pass Date",
                    "Enter the pass validity date in YYYY-MM-DD format.",
                    parent=allocation_window.winfo_toplevel()
                )
                return None

        route_id = route_options.get(selected_route)
        if route_id is None:
            messagebox.showwarning(
                "Invalid Route",
                "Select a valid registered route.",
                parent=allocation_window.winfo_toplevel()
            )
            return None

        stop_id, term_fee = stop
        return (
            reg_no,
            student_name,
            route_id,
            stop_id,
            term_fee,
            pass_valid_until or None
        )

    def save_allocation():

        values = get_form_values()
        if values is None:
            return

        (
            reg_no,
            student_name,
            route_id,
            stop_id,
            term_fee,
            pass_valid_until
        ) = values
        connection = None

        try:
            connection = get_connection()
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.cursor()

            cursor.execute(
                "SELECT route_id, term_fee FROM stops WHERE stop_id = ?",
                (stop_id,)
            )
            stop = cursor.fetchone()
            if stop is None or stop[0] != route_id:
                messagebox.showerror(
                    "Stop or Route Changed",
                    "The selected stop is no longer available on this route. Refresh and try again.",
                    parent=allocation_window.winfo_toplevel()
                )
                return

            capacity = get_route_capacity(cursor, route_id)
            if capacity is None:
                messagebox.showerror(
                    "Route Not Found",
                    "The selected route no longer exists. Refresh and try again.",
                    parent=allocation_window.winfo_toplevel()
                )
                return

            max_capacity, allocated_count = capacity
            if allocated_count >= max_capacity:
                messagebox.showwarning(
                    "Route At Capacity",
                    f"This route is full ({allocated_count}/{max_capacity}). "
                    "Choose another route or increase its capacity.",
                    parent=allocation_window.winfo_toplevel()
                )
                return

            term_fee = stop[1]
            cursor.execute("""
                INSERT INTO student_transport (
                    reg_no,
                    student_name,
                    stop_id,
                    fee_paid,
                    dues,
                    pass_valid_until
                )
                VALUES (?, ?, ?, 0, ?, ?)
            """, (
                reg_no,
                student_name,
                stop_id,
                term_fee,
                pass_valid_until
            ))
            connection.commit()

        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Duplicate Registration Number",
                "A student allocation already uses this registration number.",
                parent=allocation_window.winfo_toplevel()
            )
            return

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Unable to save student allocation:\n{error}",
                parent=allocation_window.winfo_toplevel()
            )
            return

        finally:
            if connection:
                connection.close()

        load_allocations()
        if on_change:
            on_change()
        messagebox.showinfo(
            "Success",
            "Student allocation created successfully.",
            parent=allocation_window.winfo_toplevel()
        )

    def update_allocation():

        if selected_alloc_id is None:
            messagebox.showwarning(
                "Select Allocation",
                "Select a student allocation from the table first.",
                parent=allocation_window.winfo_toplevel()
            )
            return

        values = get_form_values()
        if values is None:
            return

        (
            reg_no,
            student_name,
            route_id,
            stop_id,
            term_fee,
            pass_valid_until
        ) = values
        connection = None

        try:
            connection = get_connection()
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT
                    st.fee_paid,
                    s.route_id,
                    st.transport_status,
                    st.stop_id,
                    st.dues,
                    st.credit_balance
                FROM student_transport st
                JOIN stops s ON st.stop_id = s.stop_id
                WHERE st.alloc_id = ?
                """,
                (selected_alloc_id,)
            )
            allocation = cursor.fetchone()

            if allocation is None:
                messagebox.showerror(
                    "Allocation Not Found",
                    "This allocation no longer exists. Refresh the list and try again.",
                    parent=allocation_window.winfo_toplevel()
                )
                return

            if (
                allocation[2] == "Discontinued"
                and stop_id != allocation[3]
            ):
                messagebox.showwarning(
                    "Transport Discontinued",
                    "Reactivate transport before changing the student's route or stop.",
                    parent=allocation_window.winfo_toplevel()
                )
                return

            cursor.execute(
                "SELECT route_id, term_fee FROM stops WHERE stop_id = ?",
                (stop_id,)
            )
            stop = cursor.fetchone()
            if stop is None or stop[0] != route_id:
                messagebox.showerror(
                    "Stop or Route Changed",
                    "The selected stop is no longer available on this route. Refresh and try again.",
                    parent=allocation_window.winfo_toplevel()
                )
                return

            if (
                route_id != allocation[1]
                and allocation[2] == "Active"
            ):
                capacity = get_route_capacity(cursor, route_id)
                if capacity is None:
                    messagebox.showerror(
                        "Route Not Found",
                        "The selected route no longer exists. Refresh and try again.",
                        parent=allocation_window.winfo_toplevel()
                    )
                    return

                max_capacity, allocated_count = capacity
                if allocated_count >= max_capacity:
                    messagebox.showwarning(
                        "Route At Capacity",
                        f"This route is full ({allocated_count}/{max_capacity}). "
                        "Choose another route or increase its capacity.",
                        parent=allocation_window.winfo_toplevel()
                    )
                    return

            if allocation[2] == "Discontinued":
                dues = allocation[4]
                credit_balance = allocation[5]
                pass_valid_until = None
            else:
                term_fee = stop[1]
                dues = max(0, term_fee - allocation[0])
                credit_balance = max(0, allocation[0] - term_fee)
            cursor.execute("""
                UPDATE student_transport
                SET reg_no = ?,
                    student_name = ?,
                    stop_id = ?,
                    dues = ?,
                    credit_balance = ?,
                    pass_valid_until = ?
                WHERE alloc_id = ?
            """, (
                reg_no,
                student_name,
                stop_id,
                dues,
                credit_balance,
                pass_valid_until,
                selected_alloc_id
            ))
            connection.commit()

        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Duplicate Registration Number",
                "Another student allocation already uses this registration number.",
                parent=allocation_window.winfo_toplevel()
            )
            return

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Unable to update student allocation:\n{error}",
                parent=allocation_window.winfo_toplevel()
            )
            return

        finally:
            if connection:
                connection.close()

        load_allocations()
        if on_change:
            on_change()
        messagebox.showinfo(
            "Success",
            "Student allocation updated successfully. Dues were recalculated.",
            parent=allocation_window.winfo_toplevel()
        )

    def delete_allocation():

        if selected_alloc_id is None:
            messagebox.showwarning(
                "Select Allocation",
                "Select a student allocation from the table first.",
                parent=allocation_window.winfo_toplevel()
            )
            return

        reg_no = reg_no_entry.get().strip()
        if not messagebox.askyesno(
            "Delete Allocation",
            f"Delete the transport allocation for {reg_no}?",
            parent=allocation_window.winfo_toplevel()
        ):
            return

        connection = None
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute(
                "DELETE FROM student_transport WHERE alloc_id = ?",
                (selected_alloc_id,)
            )

            if cursor.rowcount == 0:
                messagebox.showerror(
                    "Allocation Not Found",
                    "This allocation no longer exists. Refresh the list and try again.",
                    parent=allocation_window.winfo_toplevel()
                )
                return

            connection.commit()

        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Allocation Has Payments",
                "This allocation has payment records and cannot be deleted.",
                parent=allocation_window.winfo_toplevel()
            )
            return

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Unable to delete student allocation:\n{error}",
                parent=allocation_window.winfo_toplevel()
            )
            return

        finally:
            if connection:
                connection.close()

        load_allocations()
        if on_change:
            on_change()
        messagebox.showinfo(
            "Success",
            "Student allocation deleted successfully.",
            parent=allocation_window.winfo_toplevel()
        )

    def change_transport_status(new_status):

        if selected_alloc_id is None:
            messagebox.showwarning(
                "Select Allocation",
                "Select a student allocation from the table first.",
                parent=allocation_window.winfo_toplevel()
            )
            return

        if new_status == "Discontinued" and not messagebox.askyesno(
            "Discontinue Transport",
            (
                "Discontinue this student's bus transport?\n\n"
                "The allocation and payment history will be kept. "
                "The pass will be marked discontinued, and route capacity "
                "will be released."
            ),
            parent=allocation_window.winfo_toplevel()
        ):
            return

        connection = None
        try:
            connection = get_connection()
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.cursor()
            cursor.execute("""
                SELECT
                    st.transport_status,
                    s.route_id,
                    st.student_name,
                    s.term_fee
                FROM student_transport st
                JOIN stops s ON st.stop_id = s.stop_id
                WHERE st.alloc_id = ?
            """, (selected_alloc_id,))
            allocation = cursor.fetchone()

            if allocation is None:
                messagebox.showerror(
                    "Allocation Not Found",
                    "This allocation no longer exists. Refresh the list and try again.",
                    parent=allocation_window.winfo_toplevel()
                )
                return

            if allocation[0] == new_status:
                messagebox.showinfo(
                    "Transport Status Unchanged",
                    f"This allocation is already {new_status.lower()}.",
                    parent=allocation_window.winfo_toplevel()
                )
                return

            if new_status == "Active":
                capacity = get_route_capacity(cursor, allocation[1])
                if capacity is None:
                    messagebox.showerror(
                        "Route Not Found",
                        "The assigned route no longer exists.",
                        parent=allocation_window.winfo_toplevel()
                    )
                    return

                max_capacity, allocated_count = capacity
                if allocated_count >= max_capacity:
                    messagebox.showwarning(
                        "Route At Capacity",
                        (
                            f"The assigned route is full "
                            f"({allocated_count}/{max_capacity}). "
                            "Increase its capacity or free a place before "
                            "reactivating this allocation."
                        ),
                        parent=allocation_window.winfo_toplevel()
                    )
                    return

            if new_status == "Discontinued":
                cursor.execute("""
                    UPDATE student_transport
                    SET transport_status = ?,
                        pass_valid_until = NULL
                    WHERE alloc_id = ?
                """, (new_status, selected_alloc_id))
            else:
                cursor.execute("""
                    UPDATE student_transport
                    SET transport_status = ?,
                        pass_valid_until = NULL,
                        dues = MAX(0, ? - fee_paid),
                        credit_balance = MAX(0, fee_paid - ?)
                    WHERE alloc_id = ?
                """, (
                    new_status,
                    allocation[3],
                    allocation[3],
                    selected_alloc_id
                ))
            connection.commit()

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Unable to change transport status:\n{error}",
                parent=allocation_window.winfo_toplevel()
            )
            return

        finally:
            if connection:
                connection.close()

        load_allocations()
        if on_change:
            on_change()
        messagebox.showinfo(
            "Transport Status Updated",
            f"{allocation[2]}'s transport is now {new_status.lower()}.",
            parent=allocation_window.winfo_toplevel()
        )

    search_button.config(command=load_allocations)
    search_entry.bind("<Return>", lambda event: load_allocations())
    update_button.config(command=update_allocation)
    delete_button.config(command=delete_allocation)
    discontinue_button.config(
        command=lambda: change_transport_status("Discontinued")
    )
    reactivate_button.config(
        command=lambda: change_transport_status("Active")
    )

    RoundedButton(
        form.content,
        text="Save Allocation",
        font=("Segoe UI", 10, "bold"),
        bg=theme.PRIMARY,
        fg=theme.TEXT_LIGHT,
        activebackground=theme.SECONDARY,
        activeforeground=theme.TEXT_LIGHT,
        relief="flat",
        padx=25,
        pady=10,
        cursor="hand2",
        command=save_allocation
    ).pack(anchor="w", pady=(5, 0))

    load_routes()
    load_allocations()
    reg_no_entry.focus_set()
    bind_module_navigation(allocation_page, allocation_window)
    apply_interactive_effects(allocation_page, fade=False)
    return allocation_page
