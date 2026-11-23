import csv
import sqlite3
import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox, ttk

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


REPORTS = {
    "Student Transport": {
        "columns": (
            ("reg_no", "Registration No.", 140),
            ("student_name", "Student Name", 180),
            ("route_name", "Route", 140),
            ("bus_no", "Bus Number", 130),
            ("stop_name", "Bus Stop", 160),
            ("transport_status", "Transport Status", 140),
            ("pass_status", "Pass Status", 130),
            ("pass_valid_until", "Valid Until", 130),
            ("term_fee", "Term Fee (₹)", 120),
            ("fee_paid", "Fee Paid (₹)", 120),
            ("dues", "Dues (₹)", 120)
        ),
        "query": """
            SELECT
                st.reg_no,
                st.student_name,
                r.route_name,
                r.bus_no,
                s.stop_name,
                st.transport_status,
                st.pass_valid_until,
                CASE
                    WHEN st.transport_status = 'Discontinued'
                    THEN st.fee_paid + st.dues - st.credit_balance
                    ELSE s.term_fee
                END,
                st.fee_paid,
                st.dues
            FROM student_transport st
            JOIN stops s ON st.stop_id = s.stop_id
            JOIN routes r ON s.route_id = r.route_id
        """,
        "search_fields": (
            "st.reg_no", "st.student_name", "r.route_name",
            "r.bus_no", "s.stop_name", "st.transport_status"
        ),
        "order_by": "ORDER BY st.student_name, st.reg_no",
        "kind": "student_transport"
    },
    "Outstanding Fees": {
        "columns": (
            ("reg_no", "Registration No.", 140),
            ("student_name", "Student Name", 180),
            ("route_name", "Route", 140),
            ("stop_name", "Bus Stop", 160),
            ("transport_status", "Transport Status", 140),
            ("term_fee", "Term Fee (₹)", 120),
            ("fee_paid", "Fee Paid (₹)", 120),
            ("dues", "Dues (₹)", 120)
        ),
        "query": """
            SELECT
                st.reg_no,
                st.student_name,
                r.route_name,
                s.stop_name,
                st.transport_status,
                CASE
                    WHEN st.transport_status = 'Discontinued'
                    THEN st.fee_paid + st.dues - st.credit_balance
                    ELSE s.term_fee
                END,
                st.fee_paid,
                st.dues
            FROM student_transport st
            JOIN stops s ON st.stop_id = s.stop_id
            JOIN routes r ON s.route_id = r.route_id
        """,
        "where": "st.dues > 0",
        "search_fields": (
            "st.reg_no", "st.student_name", "r.route_name",
            "s.stop_name", "st.transport_status"
        ),
        "order_by": "ORDER BY st.dues DESC, st.student_name",
        "kind": "outstanding_fees"
    },
    "Pass Status": {
        "columns": (
            ("reg_no", "Registration No.", 140),
            ("student_name", "Student Name", 180),
            ("route_name", "Route", 140),
            ("bus_no", "Bus Number", 130),
            ("stop_name", "Bus Stop", 160),
            ("transport_status", "Transport Status", 140),
            ("pass_status", "Pass Status", 130),
            ("pass_valid_until", "Valid Until", 130)
        ),
        "query": """
            SELECT
                st.reg_no,
                st.student_name,
                r.route_name,
                r.bus_no,
                s.stop_name,
                st.transport_status,
                st.pass_valid_until
            FROM student_transport st
            JOIN stops s ON st.stop_id = s.stop_id
            JOIN routes r ON s.route_id = r.route_id
        """,
        "search_fields": (
            "st.reg_no", "st.student_name", "r.route_name",
            "r.bus_no", "s.stop_name", "st.transport_status"
        ),
        "order_by": "ORDER BY st.student_name, st.reg_no",
        "kind": "pass_status"
    },
    "Payment History": {
        "columns": (
            ("payment_date", "Date", 130),
            ("reg_no", "Registration No.", 140),
            ("student_name", "Student Name", 180),
            ("amount", "Amount (₹)", 130),
            ("payment_method", "Method", 140),
            ("route_name", "Route", 140),
            ("stop_name", "Bus Stop", 160),
            ("transport_status", "Transport Status", 140)
        ),
        "query": """
            SELECT
                p.payment_date,
                st.reg_no,
                st.student_name,
                p.amount,
                p.payment_method,
                r.route_name,
                s.stop_name,
                st.transport_status
            FROM payments p
            JOIN student_transport st ON p.alloc_id = st.alloc_id
            JOIN stops s ON st.stop_id = s.stop_id
            JOIN routes r ON s.route_id = r.route_id
        """,
        "search_fields": (
            "p.payment_date", "st.reg_no", "st.student_name",
            "p.payment_method", "r.route_name", "s.stop_name",
            "st.transport_status"
        ),
        "order_by": "ORDER BY p.payment_date DESC, p.payment_id DESC",
        "kind": "payment_history"
    },
    "Route Capacity": {
        "columns": (
            ("route_name", "Route", 180),
            ("bus_no", "Bus Number", 150),
            ("driver_name", "Driver", 180),
            ("max_capacity", "Max Capacity", 140),
            ("allocated_count", "Active Students", 150),
            ("seats_remaining", "Seats Remaining", 150)
        ),
        "query": """
            SELECT
                r.route_name,
                r.bus_no,
                r.driver_name,
                r.max_capacity,
                COUNT(DISTINCT st.alloc_id),
                r.max_capacity - COUNT(DISTINCT st.alloc_id)
            FROM routes r
            LEFT JOIN stops s ON s.route_id = r.route_id
            LEFT JOIN student_transport st
                ON st.stop_id = s.stop_id
                AND st.transport_status = 'Active'
        """,
        "search_fields": ("r.route_name", "r.bus_no", "r.driver_name"),
        "group_by": "GROUP BY r.route_id",
        "order_by": "ORDER BY r.route_name",
        "kind": "route_capacity"
    }
}


def get_pass_status(transport_status, expiry_text):

    if transport_status == "Discontinued":
        return "Discontinued"
    if not expiry_text:
        return "Not Issued"

    try:
        expiry_date = date.fromisoformat(expiry_text)
    except ValueError:
        return "Invalid Date"

    return "Active" if expiry_date >= date.today() else "Expired"


def open_reports_module(parent):

    report_page = ScrollableFrame(parent, bg=theme.BACKGROUND)
    report_window = report_page.content

    report_type_count = tk.StringVar(
        master=report_page,
        value=str(len(REPORTS))
    )
    record_count_value = tk.StringVar(master=report_page, value="0")
    create_module_header(
        report_window,
        "Transport Reports",
        "Review student transport, pass, fee, payment and route capacity reports.",
        (
            (report_type_count, "Report types"),
            (record_count_value, "Rows")
        )
    )

    editor_row = tk.Frame(report_window, bg=theme.BACKGROUND)
    editor_row.pack(fill="x", padx=30, pady=(0, 20))
    editor_row.grid_columnconfigure(0, weight=3)
    editor_row.grid_columnconfigure(1, weight=2)

    report_frame = RoundedPanel(
        editor_row,
        bg=theme.CARD_BACKGROUND,
        padx=20,
        pady=20
    )
    report_frame.grid(row=0, column=0, sticky="nsew")

    controls = tk.Frame(report_frame.content, bg=theme.CARD_BACKGROUND)
    controls.pack(fill="x")

    tk.Label(
        controls,
        text="Report",
        font=("Segoe UI", 10, "bold"),
        bg=theme.CARD_BACKGROUND,
        fg=theme.TEXT_PRIMARY
    ).pack(side="left", padx=(0, 8))

    report_combo = RoundedCombobox(
        controls,
        font=("Segoe UI", 10),
        state="readonly",
        values=tuple(REPORTS)
    )
    report_combo.pack(side="left", padx=(0, 12))
    report_combo.set("Student Transport")

    search_entry = RoundedEntry(controls, font=("Segoe UI", 10), width=35)
    search_entry.pack(side="left", padx=(0, 10))

    search_button = RoundedButton(
        controls,
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

    export_button = RoundedButton(
        controls,
        text="Export CSV",
        font=("Segoe UI", 9, "bold"),
        bg=theme.PRIMARY,
        fg=theme.TEXT_LIGHT,
        relief="flat",
        padx=15,
        pady=6,
        cursor="hand2"
    )
    export_button.pack(side="left", padx=(8, 0))

    preview_title = tk.StringVar(
        master=report_page,
        value="Student Transport"
    )
    preview_badge = tk.StringVar(
        master=report_page,
        value="SELECTED REPORT"
    )
    preview_values = {
        "Search filter": tk.StringVar(master=report_page, value="All records"),
        "Result summary": tk.StringVar(
            master=report_page,
            value="Run a report to see its summary."
        )
    }
    create_live_preview(
        editor_row,
        preview_title,
        preview_badge,
        tuple(preview_values.items()),
        icon="▤"
    )

    def sync_report_preview(event=None):

        report = report_combo.get().strip() or "Select a report"
        preview_title.set(report)
        preview_badge.set("REPORT PREVIEW")
        preview_values["Search filter"].set(
            search_entry.get().strip() or "All records"
        )

    bind_preview_updates(
        (report_combo, search_entry),
        sync_report_preview
    )

    results_frame = RoundedPanel(
        report_window,
        bg=theme.CARD_BACKGROUND,
        padx=20,
        pady=20
    )
    results_frame.pack(
        fill="both",
        expand=True,
        padx=30,
        pady=(0, 25)
    )

    summary_label = tk.Label(
        results_frame.content,
        text="",
        font=("Segoe UI", 10, "bold"),
        bg=theme.CARD_BACKGROUND,
        fg=theme.PRIMARY
    )
    summary_label.pack(anchor="w", pady=(15, 5))

    table_frame = tk.Frame(results_frame.content, bg=theme.CARD_BACKGROUND)
    table_frame.pack(fill="both", expand=True)

    report_table = ttk.Treeview(
        table_frame,
        show="headings",
        height=12
    )
    prepare_treeview_hover(report_table)
    scrollbar_y = ttk.Scrollbar(
        table_frame,
        orient="vertical",
        command=report_table.yview
    )
    scrollbar_x = ttk.Scrollbar(
        table_frame,
        orient="horizontal",
        command=report_table.xview
    )
    report_table.configure(
        yscrollcommand=scrollbar_y.set,
        xscrollcommand=scrollbar_x.set
    )
    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)
    report_table.grid(row=0, column=0, sticky="nsew", pady=(10, 0))
    scrollbar_y.grid(row=0, column=1, sticky="ns", pady=(10, 0))
    scrollbar_x.grid(row=1, column=0, sticky="ew")

    for tag, color in (
        ("Active", theme.SUCCESS),
        ("Expired", theme.DANGER),
        ("Due", theme.DANGER),
        ("Not Issued", theme.TEXT_SECONDARY),
        ("Discontinued", theme.DANGER),
        ("Invalid Date", theme.DANGER)
    ):
        report_table.tag_configure(tag, foreground=color)

    current_rows = []
    current_headers = []

    def configure_columns(report):

        definitions = REPORTS[report]["columns"]
        keys = tuple(column[0] for column in definitions)
        current_headers[:] = [column[1] for column in definitions]
        report_table.configure(columns=keys)

        for key, heading, width in definitions:
            report_table.heading(key, text=heading)
            report_table.column(key, width=width, anchor="center")

    def prepare_rows(kind, rows):

        prepared = []
        for row in rows:
            if kind == "student_transport":
                pass_status = get_pass_status(row[5], row[6])
                prepared.append(row[:6] + (pass_status,) + row[6:])
            elif kind == "pass_status":
                pass_status = get_pass_status(row[5], row[6])
                prepared.append(row[:6] + (pass_status, row[6]))
            else:
                prepared.append(row)
        return prepared

    def get_summary(report, rows):

        kind = REPORTS[report]["kind"]
        if kind == "student_transport":
            active_count = sum(1 for row in rows if row[5] == "Active")
            discontinued_count = len(rows) - active_count
            return (
                f"{len(rows)} allocation(s) | {active_count} active | "
                f"{discontinued_count} discontinued"
            )
        if kind == "outstanding_fees":
            total_due = sum(row[7] for row in rows)
            return (
                f"{len(rows)} account(s) with outstanding fees | "
                f"Total due: ₹{total_due:,.2f}"
            )
        if kind == "pass_status":
            statuses = {}
            for row in rows:
                statuses[row[6]] = statuses.get(row[6], 0) + 1
            return " | ".join(
                f"{status}: {count}"
                for status, count in sorted(statuses.items())
            ) or "No pass records"
        if kind == "payment_history":
            total = sum(row[3] for row in rows)
            return (
                f"{len(rows)} payment(s) | "
                f"Total recorded: ₹{total:,.2f}"
            )

        capacity = sum(row[3] for row in rows)
        allocated = sum(row[4] for row in rows)
        return (
            f"{len(rows)} route(s) | {allocated}/{capacity} active seats "
            f"occupied"
        )

    def load_report(event=None):

        report = report_combo.get()
        if report not in REPORTS:
            messagebox.showwarning(
                "Select Report",
                "Select a valid report type.",
                parent=report_window.winfo_toplevel()
            )
            return

        for item in report_table.get_children():
            report_table.delete(item)
        current_rows.clear()
        summary_label.config(text="")
        configure_columns(report)

        definition = REPORTS[report]
        query = definition["query"]
        where_parts = []
        parameters = []

        if definition.get("where"):
            where_parts.append(definition["where"])

        search_term = search_entry.get().strip()
        if search_term:
            search_fields = definition["search_fields"]
            where_parts.append(
                "(" + " OR ".join(
                    f"{field} LIKE ?" for field in search_fields
                ) + ")"
            )
            parameters.extend(
                f"%{search_term}%" for _ in search_fields
            )

        if where_parts:
            query += " WHERE " + " AND ".join(where_parts)
        if definition.get("group_by"):
            query += " " + definition["group_by"]
        query += " " + definition["order_by"]

        connection = None
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute(query, parameters)
            current_rows.extend(
                prepare_rows(definition["kind"], cursor.fetchall())
            )

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Unable to load the selected report:\n{error}",
                parent=report_window.winfo_toplevel()
            )
            return

        finally:
            if connection:
                connection.close()

        for index, row in enumerate(current_rows):
            if "Discontinued" in row:
                tag = "Discontinued"
            elif "Due" in row:
                tag = "Due"
            elif "Expired" in row:
                tag = "Expired"
            elif "Not Issued" in row:
                tag = "Not Issued"
            elif "Invalid Date" in row:
                tag = "Invalid Date"
            elif "Active" in row:
                tag = "Active"
            else:
                tag = "oddrow" if index % 2 == 0 else "evenrow"

            report_table.insert(
                "",
                "end",
                values=row,
                tags=(tag,)
            )

        summary_label.config(text=get_summary(report, current_rows))
        record_count_value.set(str(len(current_rows)))
        preview_values["Result summary"].set(
            get_summary(report, current_rows)
        )

    def export_report():

        if not current_rows:
            messagebox.showwarning(
                "No Records",
                "There are no report records to export.",
                parent=report_window.winfo_toplevel()
            )
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            title=f"Export {report_combo.get()} Report"
        )
        if not file_path:
            return

        try:
            with open(
                file_path,
                "w",
                newline="",
                encoding="utf-8-sig"
            ) as file:
                writer = csv.writer(file)
                writer.writerow(current_headers)
                writer.writerows(current_rows)
        except OSError as error:
            messagebox.showerror(
                "Export Error",
                f"Unable to export the report:\n{error}",
                parent=report_window.winfo_toplevel()
            )
            return

        messagebox.showinfo(
            "Export Successful",
            "The report was exported successfully.",
            parent=report_window.winfo_toplevel()
        )

    report_combo.bind("<<ComboboxSelected>>", load_report)
    search_button.config(command=load_report)
    search_entry.bind("<Return>", load_report)
    export_button.config(command=export_report)

    load_report()
    apply_interactive_effects(report_page, fade=False)
    return report_page
