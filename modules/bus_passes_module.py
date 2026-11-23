import sqlite3
import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

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


def open_bus_passes_module(parent, on_change=None):

    pass_page = ScrollableFrame(parent, bg=theme.BACKGROUND)
    pass_window = pass_page.content

    allocation_count_value = tk.StringVar(master=pass_page, value="0")
    active_pass_value = tk.StringVar(master=pass_page, value="0")
    create_module_header(
        pass_window,
        "Bus Pass Management",
        "Issue and renew student bus passes, and review their current status.",
        (
            (allocation_count_value, "Records"),
            (active_pass_value, "Active passes")
        )
    )

    editor_row = tk.Frame(pass_window, bg=theme.BACKGROUND)
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
        text="Issue or Renew a Pass",
        font=("Segoe UI", 14, "bold"),
        bg=theme.CARD_BACKGROUND,
        fg=theme.PRIMARY
    ).pack(anchor="w", pady=(0, 18))

    fields_frame = tk.Frame(form.content, bg=theme.CARD_BACKGROUND)
    fields_frame.pack(fill="x")

    tk.Label(
        fields_frame,
        text="Student Allocation",
        font=("Segoe UI", 10, "bold"),
        bg=theme.CARD_BACKGROUND,
        fg=theme.TEXT_PRIMARY
    ).grid(row=0, column=0, sticky="w", padx=(0, 20), pady=(0, 5))

    tk.Label(
        fields_frame,
        text="Pass Valid Until (YYYY-MM-DD)",
        font=("Segoe UI", 10, "bold"),
        bg=theme.CARD_BACKGROUND,
        fg=theme.TEXT_PRIMARY
    ).grid(row=0, column=1, sticky="w", padx=(0, 20), pady=(0, 5))

    student_combo = RoundedCombobox(
        fields_frame,
        font=("Segoe UI", 10),
        state="readonly"
    )
    student_combo.grid(
        row=1, column=0, sticky="ew", padx=(0, 20), pady=(0, 16)
    )

    expiry_entry = RoundedEntry(fields_frame, font=("Segoe UI", 10))
    expiry_entry.grid(
        row=1, column=1, sticky="ew", padx=(0, 20), pady=(0, 16)
    )

    fields_frame.grid_columnconfigure(0, weight=1)
    fields_frame.grid_columnconfigure(1, weight=1)

    preview_title = tk.StringVar(master=pass_page, value="Student name")
    preview_badge = tk.StringVar(master=pass_page, value="PASS STATUS")
    preview_values = {
        "Student allocation": tk.StringVar(
            master=pass_page,
            value="Select a student"
        ),
        "Valid until": tk.StringVar(master=pass_page, value="Not set")
    }
    create_live_preview(
        editor_row,
        preview_title,
        preview_badge,
        tuple(preview_values.items()),
        icon="▣"
    )

    def sync_pass_preview(event=None):

        selected_student = student_combo.get().strip()
        preview_title.set(
            selected_student.split(" (")[0]
            if selected_student
            else "Student name"
        )
        expiry_text = expiry_entry.get().strip()
        preview_values["Student allocation"].set(
            selected_student or "Select a student"
        )
        preview_values["Valid until"].set(expiry_text or "Not set")
        if not expiry_text:
            preview_badge.set("NOT ISSUED")
        else:
            try:
                expiry_date = date.fromisoformat(expiry_text)
                preview_badge.set(
                    "ACTIVE" if expiry_date >= date.today() else "EXPIRED"
                )
            except ValueError:
                preview_badge.set("INVALID DATE")

    bind_preview_updates(
        (student_combo, expiry_entry),
        sync_pass_preview
    )

    table_frame = RoundedPanel(
        pass_window,
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
        text="Student Bus Passes",
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

    columns = (
        "reg_no",
        "student_name",
        "route_name",
        "bus_no",
        "stop_name",
        "pass_valid_until",
        "pass_status"
    )

    table_container = tk.Frame(table_frame.content, bg=theme.CARD_BACKGROUND)
    pass_table = ttk.Treeview(
        table_container,
        columns=columns,
        show="headings",
        height=8
    )
    prepare_treeview_hover(pass_table)

    headings = {
        "reg_no": ("Registration No.", 150),
        "student_name": ("Student Name", 190),
        "route_name": ("Route", 150),
        "bus_no": ("Bus Number", 140),
        "stop_name": ("Bus Stop", 180),
        "pass_valid_until": ("Valid Until", 150),
        "pass_status": ("Pass Status", 140)
    }

    for column, (heading, width) in headings.items():
        pass_table.heading(column, text=heading)
        pass_table.column(column, width=width, anchor="center")

    pass_table.tag_configure("Active", foreground=theme.SUCCESS)
    pass_table.tag_configure("Expired", foreground=theme.DANGER)
    pass_table.tag_configure("Not Issued", foreground=theme.TEXT_SECONDARY)
    pass_table.tag_configure("Discontinued", foreground=theme.DANGER)

    scrollbar_y = ttk.Scrollbar(
        table_container,
        orient="vertical",
        command=pass_table.yview
    )
    scrollbar_x = ttk.Scrollbar(
        table_container,
        orient="horizontal",
        command=pass_table.xview
    )
    pass_table.configure(
        yscrollcommand=scrollbar_y.set,
        xscrollcommand=scrollbar_x.set
    )
    table_container.grid_rowconfigure(0, weight=1)
    table_container.grid_columnconfigure(0, weight=1)
    pass_table.grid(row=0, column=0, sticky="nsew", pady=(15, 0))
    scrollbar_y.grid(row=0, column=1, sticky="ns", pady=(15, 0))
    scrollbar_x.grid(row=1, column=0, sticky="ew")
    table_container.pack(fill="both", expand=True)

    student_options = {}
    selected_alloc_id = None

    def clear_form():

        nonlocal selected_alloc_id

        selected_alloc_id = None
        selected = pass_table.selection()
        if selected:
            pass_table.selection_remove(*selected)
        student_combo.set("")
        expiry_entry.delete(0, tk.END)
        sync_pass_preview()

    def get_pass_status(expiry_date, transport_status):

        if transport_status == "Discontinued":
            return "Discontinued"
        if not expiry_date:
            return "Not Issued"

        return "Active" if date.fromisoformat(expiry_date) >= date.today() else "Expired"

    def load_passes():

        clear_form()

        for item in pass_table.get_children():
            pass_table.delete(item)
        student_options.clear()

        connection = None

        try:
            connection = get_connection()
            cursor = connection.cursor()
            search_term = f"%{search_entry.get().strip()}%"
            cursor.execute("""
                SELECT
                    st.alloc_id,
                    st.reg_no,
                    st.student_name,
                    r.route_name,
                    r.bus_no,
                    s.stop_name,
                    st.pass_valid_until,
                    st.transport_status
                FROM student_transport st
                JOIN stops s ON st.stop_id = s.stop_id
                JOIN routes r ON s.route_id = r.route_id
                WHERE st.reg_no LIKE ?
                   OR st.student_name LIKE ?
                   OR r.route_name LIKE ?
                   OR s.stop_name LIKE ?
                ORDER BY st.student_name, st.reg_no
            """, (
                search_term,
                search_term,
                search_term,
                search_term
            ))

            active_count = 0
            allocations = cursor.fetchall()
            for allocation in allocations:
                allocation_id = allocation[0]
                expiry_date = allocation[6]
                transport_status = allocation[7]
                pass_status = get_pass_status(
                    expiry_date,
                    transport_status
                )
                if pass_status == "Active":
                    active_count += 1
                student_display = (
                    f"{allocation[1]} - {allocation[2]} "
                    f"({allocation[3]} / {allocation[5]})"
                )
                student_options[student_display] = allocation_id
                pass_table.insert(
                    "",
                    "end",
                    iid=str(allocation_id),
                    values=(
                        allocation[1],
                        allocation[2],
                        allocation[3],
                        allocation[4],
                        allocation[5],
                        expiry_date or "",
                        pass_status
                    ),
                    tags=(pass_status,)
                )

            student_combo["values"] = list(student_options)
            allocation_count_value.set(str(len(allocations)))
            active_pass_value.set(str(active_count))

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Unable to load bus passes:\n{error}",
                parent=pass_window.winfo_toplevel()
            )

        finally:
            if connection:
                connection.close()

    def select_pass(event):

        nonlocal selected_alloc_id

        selected = pass_table.selection()
        if not selected:
            return

        selected_alloc_id = int(selected[0])
        values = pass_table.item(selected[0], "values")
        student_combo.set(
            f"{values[0]} - {values[1]} ({values[2]} / {values[4]})"
        )
        expiry_entry.delete(0, tk.END)
        expiry_entry.insert(0, values[5])
        sync_pass_preview()

    pass_table.bind("<<TreeviewSelect>>", select_pass)

    def on_student_selected(event=None):

        nonlocal selected_alloc_id

        selected_alloc_id = student_options.get(student_combo.get())
        if selected_alloc_id is None:
            sync_pass_preview()
            return

        item = str(selected_alloc_id)
        if pass_table.exists(item):
            pass_table.selection_set(item)
            pass_table.focus(item)
            pass_table.see(item)
            select_pass()

    student_combo.bind("<<ComboboxSelected>>", on_student_selected)

    def save_pass():

        if selected_alloc_id is None:
            messagebox.showwarning(
                "Select Student",
                "Select a student allocation from the table first.",
                parent=pass_window.winfo_toplevel()
            )
            return

        student_display = student_combo.get().strip()
        if student_options.get(student_display) != selected_alloc_id:
            messagebox.showwarning(
                "Invalid Student",
                "Select a valid student allocation from the list.",
                parent=pass_window.winfo_toplevel()
            )
            return

        expiry_text = expiry_entry.get().strip()
        try:
            expiry_date = date.fromisoformat(expiry_text)
            if expiry_date.isoformat() != expiry_text or expiry_date < date.today():
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Invalid Expiry Date",
                "Enter a valid date in YYYY-MM-DD format that is today or later.",
                parent=pass_window.winfo_toplevel()
            )
            return

        connection = None

        try:
            connection = get_connection()
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.cursor()
            cursor.execute(
                "SELECT transport_status FROM student_transport WHERE alloc_id = ?",
                (selected_alloc_id,)
            )
            allocation = cursor.fetchone()

            if allocation is None:
                messagebox.showerror(
                    "Student Not Found",
                    "This student allocation no longer exists. Refresh and try again.",
                    parent=pass_window.winfo_toplevel()
                )
                return

            if allocation[0] == "Discontinued":
                messagebox.showwarning(
                    "Transport Discontinued",
                    "Reactivate this student's transport before issuing or renewing a pass.",
                    parent=pass_window.winfo_toplevel()
                )
                return

            cursor.execute("""
                UPDATE student_transport
                SET pass_valid_until = ?
                WHERE alloc_id = ?
            """, (expiry_text, selected_alloc_id))

            if cursor.rowcount == 0:
                messagebox.showerror(
                    "Student Not Found",
                    "This student allocation no longer exists. Refresh and try again.",
                    parent=pass_window.winfo_toplevel()
                )
                return

            connection.commit()

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Unable to save bus pass:\n{error}",
                parent=pass_window.winfo_toplevel()
            )
            return

        finally:
            if connection:
                connection.close()

        load_passes()
        if on_change:
            on_change()
        messagebox.showinfo(
            "Success",
            "Bus pass issued or renewed successfully.",
            parent=pass_window.winfo_toplevel()
        )

    search_button.config(command=load_passes)
    search_entry.bind("<Return>", lambda event: load_passes())

    RoundedButton(
        form.content,
        text="Issue / Renew Pass",
        font=("Segoe UI", 10, "bold"),
        bg=theme.PRIMARY,
        fg=theme.TEXT_LIGHT,
        activebackground=theme.SECONDARY,
        activeforeground=theme.TEXT_LIGHT,
        relief="flat",
        padx=25,
        pady=10,
        cursor="hand2",
        command=save_pass
    ).pack(anchor="w", pady=(5, 0))

    load_passes()
    student_combo.focus_set()
    apply_interactive_effects(pass_page, fade=False)
    return pass_page
