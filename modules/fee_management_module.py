import math
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
    create_module_header
)


def open_fee_management_module(parent, on_change=None):

    fee_page = ScrollableFrame(parent, bg=theme.BACKGROUND)
    fee_window = fee_page.content

    payment_count_value = tk.StringVar(master=fee_page, value="0")
    outstanding_value = tk.StringVar(master=fee_page, value="₹0")
    create_module_header(
        fee_window,
        "Fee Management",
        "Record student payments and review payment history.",
        (
            (payment_count_value, "Payments"),
            (outstanding_value, "Outstanding")
        )
    )

    editor_row = tk.Frame(fee_window, bg=theme.BACKGROUND)
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
        text="Record a Payment",
        font=("Segoe UI", 14, "bold"),
        bg=theme.CARD_BACKGROUND,
        fg=theme.PRIMARY
    ).pack(anchor="w", pady=(0, 18))

    fields_frame = tk.Frame(form.content, bg=theme.CARD_BACKGROUND)
    fields_frame.pack(fill="x")

    field_labels = [
        ("Student Allocation", 0, 0),
        ("Payment Amount (₹)", 0, 1),
        ("Payment Method", 2, 0),
        ("Payment Date (YYYY-MM-DD)", 2, 1)
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

    student_combo = RoundedCombobox(
        fields_frame,
        font=("Segoe UI", 10),
        state="readonly"
    )
    student_combo.grid(
        row=1, column=0, sticky="ew", padx=(0, 20), pady=(0, 12)
    )

    amount_entry = RoundedEntry(fields_frame, font=("Segoe UI", 10))
    amount_entry.grid(
        row=1, column=1, sticky="ew", padx=(0, 20), pady=(0, 12)
    )

    method_combo = RoundedCombobox(
        fields_frame,
        font=("Segoe UI", 10),
        values=("UPI", "Cash", "Card", "Bank Transfer", "Cheque")
    )
    method_combo.grid(
        row=3, column=0, sticky="ew", padx=(0, 20), pady=(0, 12)
    )

    payment_date_entry = RoundedEntry(fields_frame, font=("Segoe UI", 10))
    payment_date_entry.grid(
        row=3, column=1, sticky="ew", padx=(0, 20), pady=(0, 12)
    )
    payment_date_entry.insert(0, date.today().isoformat())

    fields_frame.grid_columnconfigure(0, weight=1)
    fields_frame.grid_columnconfigure(1, weight=1)

    balance_label = tk.Label(
        fields_frame,
        text="Select a student allocation to view fee status.",
        font=("Segoe UI", 9),
        bg=theme.CARD_BACKGROUND,
        fg=theme.TEXT_SECONDARY
    )
    balance_label.grid(
        row=4,
        column=0,
        columnspan=2,
        sticky="w",
        pady=(0, 12)
    )

    payment_actions = tk.Frame(form.content, bg=theme.CARD_BACKGROUND)
    payment_actions.pack(anchor="w", pady=(5, 0))

    RoundedButton(
        payment_actions,
        text="Record Payment",
        font=("Segoe UI", 10, "bold"),
        bg=theme.PRIMARY,
        fg=theme.TEXT_LIGHT,
        activebackground=theme.SECONDARY,
        activeforeground=theme.TEXT_LIGHT,
        relief="flat",
        padx=25,
        pady=10,
        cursor="hand2",
        command=lambda: record_payment()
    ).pack(side="left")

    RoundedButton(
        payment_actions,
        text="Pay Remaining Due",
        font=("Segoe UI", 10, "bold"),
        bg=theme.SECONDARY,
        fg=theme.TEXT_LIGHT,
        activebackground=theme.PRIMARY,
        activeforeground=theme.TEXT_LIGHT,
        relief="flat",
        padx=25,
        pady=10,
        cursor="hand2",
        command=lambda: record_remaining_due()
    ).pack(side="left", padx=(10, 0))

    history_frame = RoundedPanel(
        fee_window,
        bg=theme.CARD_BACKGROUND,
        padx=20,
        pady=20
    )
    history_frame.pack(
        fill="both",
        expand=True,
        padx=30,
        pady=(0, 25)
    )

    tk.Label(
        history_frame.content,
        text="Payment History",
        font=("Segoe UI", 14, "bold"),
        bg=theme.CARD_BACKGROUND,
        fg=theme.PRIMARY
    ).pack(anchor="w")

    tk.Label(
        history_frame.content,
        text=(
            "Select a payment row to edit it. Click Current Fee Status "
            "to view the student's remaining balance."
        ),
        font=("Segoe UI", 9),
        bg=theme.CARD_BACKGROUND,
        fg=theme.TEXT_SECONDARY
    ).pack(anchor="w", pady=(5, 0))

    search_frame = tk.Frame(history_frame.content, bg=theme.CARD_BACKGROUND)
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
        text="Update Payment",
        font=("Segoe UI", 9, "bold"),
        bg=theme.PRIMARY,
        fg=theme.TEXT_LIGHT,
        relief="flat",
        padx=15,
        pady=6,
        cursor="hand2"
    )
    update_button.pack(side="left", padx=(8, 0))

    columns = (
        "payment_date",
        "reg_no",
        "student_name",
        "amount",
        "fee_status",
        "payment_method",
        "route_name",
        "stop_name",
        "transport_status"
    )

    table_container = tk.Frame(history_frame.content, bg=theme.CARD_BACKGROUND)
    payment_table = ttk.Treeview(
        table_container,
        columns=columns,
        show="headings",
        height=8
    )
    prepare_treeview_hover(payment_table)

    headings = {
        "payment_date": ("Date", 120),
        "reg_no": ("Registration No.", 140),
        "student_name": ("Student Name", 180),
        "amount": ("Amount (₹)", 120),
        "fee_status": ("Current Fee Status", 150),
        "payment_method": ("Method", 130),
        "route_name": ("Route", 140),
        "stop_name": ("Bus Stop", 160),
        "transport_status": ("Transport Status", 140)
    }

    for column, (heading, width) in headings.items():
        payment_table.heading(column, text=heading)
        payment_table.column(column, width=width, anchor="center")

    payment_table.tag_configure("Due", foreground=theme.DANGER)
    payment_table.tag_configure("Fully Paid", foreground=theme.SUCCESS)
    payment_table.tag_configure("Advance Credit", foreground=theme.SECONDARY)

    scrollbar_y = ttk.Scrollbar(
        table_container,
        orient="vertical",
        command=payment_table.yview
    )
    scrollbar_x = ttk.Scrollbar(
        table_container,
        orient="horizontal",
        command=payment_table.xview
    )
    payment_table.configure(
        yscrollcommand=scrollbar_y.set,
        xscrollcommand=scrollbar_x.set
    )

    table_container.grid_rowconfigure(0, weight=1)
    table_container.grid_columnconfigure(0, weight=1)
    payment_table.grid(row=0, column=0, sticky="nsew", pady=(15, 0))
    scrollbar_y.grid(row=0, column=1, sticky="ns", pady=(15, 0))
    scrollbar_x.grid(row=1, column=0, sticky="ew")
    table_container.pack(fill="both", expand=True)

    student_options = {}
    student_display_by_alloc = {}
    student_balances = {}
    student_transport_status = {}
    payment_records = {}
    payment_balances = {}
    selected_payment_id = None

    preview_title = tk.StringVar(
        master=fee_page,
        value="Select a student"
    )
    preview_badge = tk.StringVar(
        master=fee_page,
        value="PAYMENT AMOUNT"
    )
    preview_values = {
        "Payment method": tk.StringVar(master=fee_page, value="—"),
        "Payment date": tk.StringVar(master=fee_page, value="—"),
        "Fee status": tk.StringVar(
            master=fee_page,
            value="Select an allocation"
        ),
        "Outstanding": tk.StringVar(master=fee_page, value="—")
    }
    create_live_preview(
        editor_row,
        preview_title,
        preview_badge,
        tuple(preview_values.items()),
        icon="₹"
    )

    def sync_payment_preview(event=None):

        selected_student = student_combo.get().strip()
        preview_title.set(
            selected_student.split(" (")[0]
            if selected_student
            else "Select a student"
        )
        amount = amount_entry.get().strip()
        preview_badge.set(
            f"₹{amount}" if amount else "PAYMENT AMOUNT"
        )
        preview_values["Payment method"].set(
            method_combo.get().strip() or "—"
        )
        preview_values["Payment date"].set(
            payment_date_entry.get().strip() or "—"
        )
        balances = student_balances.get(selected_student)
        if balances is None:
            preview_values["Fee status"].set("Select an allocation")
            preview_values["Outstanding"].set("—")
            return
        dues, credit_balance = balances
        preview_values["Fee status"].set(
            get_fee_status(dues, credit_balance)
        )
        preview_values["Outstanding"].set(f"₹{dues:,.2f}")

    bind_preview_updates(
        (student_combo, amount_entry, method_combo, payment_date_entry),
        sync_payment_preview
    )

    def load_students():

        connection = None

        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("""
                SELECT
                    st.alloc_id,
                    st.reg_no,
                    st.student_name,
                    r.route_name,
                    s.stop_name,
                    st.dues,
                    st.credit_balance,
                    st.transport_status
                FROM student_transport st
                JOIN stops s ON st.stop_id = s.stop_id
                JOIN routes r ON s.route_id = r.route_id
                ORDER BY st.student_name, st.reg_no
            """)
            students = cursor.fetchall()

            student_options.clear()
            student_display_by_alloc.clear()
            student_balances.clear()
            student_transport_status.clear()
            student_values = []

            for student in students:
                alloc_id = student[0]
                transport_status = student[7]
                display = (
                    f"{student[1]} - {student[2]} "
                    f"({student[3]} / {student[4]})"
                )
                if transport_status == "Discontinued":
                    display += " [Discontinued]"
                student_options[display] = alloc_id
                student_display_by_alloc[alloc_id] = display
                student_balances[display] = (student[5], student[6])
                student_transport_status[display] = transport_status
                student_values.append(display)

            student_combo["values"] = student_values

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Unable to load student allocations:\n{error}",
                parent=fee_window.winfo_toplevel()
            )

        finally:
            if connection:
                connection.close()

    def update_balance_label(event=None):

        balances = student_balances.get(student_combo.get())
        if balances is None:
            balance_label.config(
                text="Select a student allocation to view fee status."
            )
            sync_payment_preview()
            return

        dues, credit_balance = balances
        status = get_fee_status(dues, credit_balance)
        transport_status = student_transport_status.get(
            student_combo.get(),
            "Active"
        )
        if status == "Due":
            status_color = theme.DANGER
        elif status == "Advance Credit":
            status_color = theme.SECONDARY
        else:
            status_color = theme.SUCCESS

        balance_label.config(
            text=(
                f"Status: {status}    "
                f"Transport: {transport_status}    "
                f"Outstanding dues: ₹{dues:,.2f}    "
                f"Advance credit: ₹{credit_balance:,.2f}"
            ),
            fg=status_color
        )
        sync_payment_preview()

    def on_student_selected(event=None):

        nonlocal selected_payment_id

        selected_payment_id = None
        update_balance_label()

    student_combo.bind("<<ComboboxSelected>>", on_student_selected)

    def get_payment_form_values(require_amount=True):

        selected_student = student_combo.get().strip()
        alloc_id = student_options.get(selected_student)
        amount_text = amount_entry.get().strip()
        payment_method = method_combo.get().strip()
        payment_date = payment_date_entry.get().strip()

        if (
            alloc_id is None
            or (require_amount and not amount_text)
            or not payment_method
            or not payment_date
        ):
            messagebox.showwarning(
                "Missing Information",
                "Select a student and enter the required payment details.",
                parent=fee_window.winfo_toplevel()
            )
            return None

        amount = None
        if require_amount:
            try:
                amount = float(amount_text)
                if not math.isfinite(amount) or amount <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning(
                    "Invalid Amount",
                    "Enter a positive finite payment amount.",
                    parent=fee_window.winfo_toplevel()
                )
                return None

        try:
            parsed_date = date.fromisoformat(payment_date)
            if parsed_date.isoformat() != payment_date:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Invalid Payment Date",
                "Enter the payment date in YYYY-MM-DD format.",
                parent=fee_window.winfo_toplevel()
            )
            return None

        return alloc_id, amount, payment_method, payment_date

    def load_payment_history():

        nonlocal selected_payment_id

        selected_payment_id = None
        payment_records.clear()
        payment_balances.clear()

        for item in payment_table.get_children():
            payment_table.delete(item)

        connection = None

        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM payments")
            payment_count_value.set(str(cursor.fetchone()[0]))
            cursor.execute("""
                SELECT COALESCE(SUM(dues), 0)
                FROM student_transport
                WHERE transport_status = 'Active'
            """)
            outstanding_value.set(
                f"₹{cursor.fetchone()[0]:,.0f}"
            )
            search_term = f"%{search_entry.get().strip()}%"
            cursor.execute("""
                SELECT
                    p.payment_id,
                    p.payment_date,
                    st.reg_no,
                    st.student_name,
                    p.amount,
                    st.dues,
                    st.credit_balance,
                    p.payment_method,
                    r.route_name,
                    s.stop_name,
                    p.alloc_id,
                    st.transport_status
                FROM payments p
                JOIN student_transport st ON p.alloc_id = st.alloc_id
                JOIN stops s ON st.stop_id = s.stop_id
                JOIN routes r ON s.route_id = r.route_id
                WHERE st.reg_no LIKE ?
                   OR st.student_name LIKE ?
                   OR p.payment_method LIKE ?
                   OR p.payment_date LIKE ?
                ORDER BY p.payment_date DESC, p.payment_id DESC
            """, (
                search_term,
                search_term,
                search_term,
                search_term
            ))

            for payment in cursor.fetchall():
                payment_records[payment[0]] = (
                    payment[10],
                    payment[4],
                    payment[1],
                    payment[7]
                )
                payment_balances[payment[0]] = (
                    payment[5],
                    payment[6]
                )
                fee_status = get_fee_status(payment[5], payment[6])
                payment_table.insert(
                    "",
                    "end",
                    iid=str(payment[0]),
                    values=(
                        payment[1],
                        payment[2],
                        payment[3],
                        f"{payment[4]:,.2f}",
                        fee_status,
                        payment[7],
                        payment[8],
                        payment[9],
                        payment[11]
                    ),
                    tags=(fee_status,)
                )

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Unable to load payment history:\n{error}",
                parent=fee_window.winfo_toplevel()
            )

        finally:
            if connection:
                connection.close()

    def show_fee_status(payment_id):

        balances = payment_balances.get(payment_id)
        if balances is None:
            return

        dues, credit_balance = balances
        status = get_fee_status(dues, credit_balance)
        if dues > 0:
            detail = f"Amount remaining to pay: ₹{dues:,.2f}"
        elif credit_balance > 0:
            detail = f"Advance credit available: ₹{credit_balance:,.2f}"
        else:
            detail = "There is no outstanding amount."

        messagebox.showinfo(
            status,
            f"Current fee status: {status}\n{detail}",
            parent=fee_window.winfo_toplevel()
        )

    def on_payment_cell_click(event):

        if payment_table.identify_column(event.x) != "#5":
            return

        item = payment_table.identify_row(event.y)
        if item:
            payment_table.after_idle(
                lambda: show_fee_status(int(item))
            )

    payment_table.bind("<Button-1>", on_payment_cell_click)

    def select_payment(event=None):

        nonlocal selected_payment_id

        selected = payment_table.selection()
        if not selected:
            return

        payment_id = int(selected[0])
        payment = payment_records.get(payment_id)
        if payment is None:
            messagebox.showerror(
                "Payment Not Found",
                "The selected payment is no longer available. Refresh the history and try again.",
                parent=fee_window.winfo_toplevel()
            )
            return

        alloc_id, amount, payment_date, payment_method = payment
        student_display = student_display_by_alloc.get(alloc_id)
        if student_display is None:
            messagebox.showerror(
                "Allocation Not Found",
                "The student allocation for this payment is no longer available.",
                parent=fee_window.winfo_toplevel()
            )
            return

        selected_payment_id = payment_id
        student_combo.set(student_display)
        amount_entry.delete(0, tk.END)
        amount_entry.insert(0, str(amount))
        method_combo.set(payment_method)
        payment_date_entry.delete(0, tk.END)
        payment_date_entry.insert(0, payment_date)
        update_balance_label()

    payment_table.bind("<<TreeviewSelect>>", select_payment)

    def record_payment(amount_override=None):

        values = get_payment_form_values(
            require_amount=amount_override is None
        )
        if values is None:
            return

        alloc_id, amount, payment_method, payment_date = values
        connection = None
        try:
            connection = get_connection()
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.cursor()
            cursor.execute("""
                SELECT
                    st.fee_paid,
                    s.term_fee,
                    st.dues,
                    st.transport_status,
                    st.credit_balance
                FROM student_transport st
                JOIN stops s ON st.stop_id = s.stop_id
                WHERE st.alloc_id = ?
            """, (alloc_id,))
            allocation = cursor.fetchone()

            if allocation is None:
                messagebox.showerror(
                    "Allocation Not Found",
                    "This student allocation no longer exists. Refresh and try again.",
                    parent=fee_window.winfo_toplevel()
                )
                return

            if amount_override is not None:
                if allocation[2] <= 0:
                    messagebox.showinfo(
                        "No Outstanding Due",
                        "This student has no outstanding fee to pay.",
                        parent=fee_window.winfo_toplevel()
                    )
                    return

                if allocation[2] != amount_override:
                    messagebox.showwarning(
                        "Balance Changed",
                        f"The current outstanding due is ₹{allocation[2]:,.2f}. "
                        "Review the updated balance and try again.",
                        parent=fee_window.winfo_toplevel()
                    )
                    return

                amount = allocation[2]

            if allocation[3] == "Discontinued" and (
                allocation[2] <= 0 or amount > allocation[2]
            ):
                messagebox.showwarning(
                    "Payment Exceeds Outstanding Due",
                    (
                        "For discontinued transport, only the existing "
                        f"outstanding due of ₹{allocation[2]:,.2f} can be paid."
                    ),
                    parent=fee_window.winfo_toplevel()
                )
                return

            new_fee_paid = allocation[0] + amount
            term_fee = allocation[1]
            if allocation[3] == "Discontinued":
                term_fee = allocation[0] + allocation[2] - allocation[4]
            if not math.isfinite(new_fee_paid) or not math.isfinite(term_fee):
                messagebox.showerror(
                    "Invalid Fee Balance",
                    "The payment or stop fee exceeds the supported numeric range.",
                    parent=fee_window.winfo_toplevel()
                )
                return

            new_dues = max(0, term_fee - new_fee_paid)
            new_credit = max(0, new_fee_paid - term_fee)

            cursor.execute("""
                INSERT INTO payments (
                    alloc_id,
                    amount,
                    payment_date,
                    payment_method
                )
                VALUES (?, ?, ?, ?)
            """, (
                alloc_id,
                amount,
                payment_date,
                payment_method
            ))
            cursor.execute("""
                UPDATE student_transport
                SET fee_paid = ?,
                    dues = ?,
                    credit_balance = ?
                WHERE alloc_id = ?
            """, (
                new_fee_paid,
                new_dues,
                new_credit,
                alloc_id
            ))
            connection.commit()

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Unable to record payment:\n{error}",
                parent=fee_window.winfo_toplevel()
            )
            return

        finally:
            if connection:
                connection.close()

        selected_student = student_combo.get()
        load_students()
        if selected_student in student_options:
            student_combo.set(selected_student)
        update_balance_label()
        load_payment_history()
        amount_entry.delete(0, tk.END)
        sync_payment_preview()
        if on_change:
            on_change()

        payment_status = get_fee_status(new_dues, new_credit)
        messagebox.showinfo(
            "Payment Recorded",
            (
                f"Payment recorded successfully.\n"
                f"Status: {payment_status}\n"
                f"Outstanding dues: ₹{new_dues:,.2f}\n"
                f"Advance credit: ₹{new_credit:,.2f}"
            ),
            parent=fee_window.winfo_toplevel()
        )

    def record_remaining_due():

        values = get_payment_form_values(require_amount=False)
        if values is None:
            return

        _, _, payment_method, payment_date = values
        dues, _ = student_balances.get(
            student_combo.get().strip(),
            (None, None)
        )

        if dues is None:
            messagebox.showerror(
                "Balance Not Available",
                "Refresh the student list and select the student again.",
                parent=fee_window.winfo_toplevel()
            )
            return

        if dues <= 0:
            messagebox.showinfo(
                "No Outstanding Due",
                "This student has no outstanding fee to pay.",
                parent=fee_window.winfo_toplevel()
            )
            return

        if not messagebox.askyesno(
            "Pay Remaining Due",
            (
                f"Record ₹{dues:,.2f} as the final payment for "
                f"{student_combo.get()}?\n\n"
                f"Method: {payment_method}\nDate: {payment_date}"
            ),
            parent=fee_window.winfo_toplevel()
        ):
            return

        record_payment(amount_override=dues)

    def update_payment():

        if selected_payment_id is None:
            messagebox.showwarning(
                "Select Payment",
                "Select a payment from the history table first.",
                parent=fee_window.winfo_toplevel()
            )
            return

        values = get_payment_form_values()
        if values is None:
            return

        selected_alloc_id, amount, payment_method, payment_date = values
        connection = None

        try:
            connection = get_connection()
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.cursor()
            cursor.execute("""
                SELECT alloc_id, amount
                FROM payments
                WHERE payment_id = ?
            """, (selected_payment_id,))
            existing_payment = cursor.fetchone()

            if existing_payment is None:
                messagebox.showerror(
                    "Payment Not Found",
                    "This payment no longer exists. Refresh the history and try again.",
                    parent=fee_window.winfo_toplevel()
                )
                return

            if selected_alloc_id != existing_payment[0]:
                messagebox.showwarning(
                    "Student Cannot Be Changed",
                    "A payment can only be updated for its original student allocation.",
                    parent=fee_window.winfo_toplevel()
                )
                return

            cursor.execute("""
                SELECT
                    st.fee_paid,
                    s.term_fee,
                    st.transport_status,
                    st.dues,
                    st.credit_balance
                FROM student_transport st
                JOIN stops s ON st.stop_id = s.stop_id
                WHERE st.alloc_id = ?
            """, (selected_alloc_id,))
            allocation = cursor.fetchone()

            if allocation is None:
                messagebox.showerror(
                    "Allocation Not Found",
                    "The student allocation for this payment no longer exists.",
                    parent=fee_window.winfo_toplevel()
                )
                return

            new_fee_paid = allocation[0] - existing_payment[1] + amount
            term_fee = allocation[1]
            if allocation[2] == "Discontinued":
                term_fee = allocation[0] + allocation[3] - allocation[4]
            if (
                not math.isfinite(new_fee_paid)
                or not math.isfinite(term_fee)
                or new_fee_paid < 0
            ):
                messagebox.showerror(
                    "Invalid Fee Balance",
                    "The updated payment would create an invalid fee balance.",
                    parent=fee_window.winfo_toplevel()
                )
                return

            if (
                allocation[2] == "Discontinued"
                and new_fee_paid > max(allocation[0], term_fee)
            ):
                messagebox.showwarning(
                    "Payment Exceeds Discontinued Balance",
                    (
                        "Updating this payment cannot increase the "
                        "discontinued student's total paid amount beyond "
                        "its existing paid balance or term fee."
                    ),
                    parent=fee_window.winfo_toplevel()
                )
                return

            new_dues = max(0, term_fee - new_fee_paid)
            new_credit = max(0, new_fee_paid - term_fee)
            cursor.execute("""
                UPDATE payments
                SET amount = ?,
                    payment_date = ?,
                    payment_method = ?
                WHERE payment_id = ?
            """, (
                amount,
                payment_date,
                payment_method,
                selected_payment_id
            ))
            cursor.execute("""
                UPDATE student_transport
                SET fee_paid = ?,
                    dues = ?,
                    credit_balance = ?
                WHERE alloc_id = ?
            """, (
                new_fee_paid,
                new_dues,
                new_credit,
                selected_alloc_id
            ))
            connection.commit()

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Unable to update payment:\n{error}",
                parent=fee_window.winfo_toplevel()
            )
            return

        finally:
            if connection:
                connection.close()

        selected_student = student_combo.get()
        load_students()
        if selected_student in student_options:
            student_combo.set(selected_student)
        update_balance_label()
        load_payment_history()
        amount_entry.delete(0, tk.END)
        if on_change:
            on_change()

        payment_status = get_fee_status(new_dues, new_credit)
        messagebox.showinfo(
            "Payment Updated",
            (
                f"Payment updated successfully.\n"
                f"Status: {payment_status}\n"
                f"Outstanding dues: ₹{new_dues:,.2f}\n"
                f"Advance credit: ₹{new_credit:,.2f}"
            ),
            parent=fee_window.winfo_toplevel()
        )

    search_button.config(command=load_payment_history)
    search_entry.bind("<Return>", lambda event: load_payment_history())
    update_button.config(command=update_payment)

    load_students()
    load_payment_history()
    student_combo.focus_set()
    apply_interactive_effects(fee_page, fade=False)
    return fee_page
