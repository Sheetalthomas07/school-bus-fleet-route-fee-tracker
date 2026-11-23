import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date
import csv
import sqlite3

from utils import theme
from modules.routes_module import open_routes_module
from modules.stops_module import open_stops_module
from modules.student_allocation_module import open_student_allocation_module
from modules.fee_management_module import open_fee_management_module
from modules.bus_passes_module import open_bus_passes_module
from modules.reports_module import open_reports_module
from modules.welcome_screen import create_welcome_screen
from database.db_connection import get_connection
from database.db_setup import create_tables
from utils.ui_effects import (
    apply_interactive_effects,
    bind_sidebar_item,
    prepare_treeview_hover
)
from utils.rounded_widgets import (
    RoundedButton,
    RoundedEntry,
    RoundedPanel,
    ScrollableFrame
)


# ==========================================
# MAIN APPLICATION WINDOWs
# ==========================================

create_tables()

root = tk.Tk()
root.title("School Transit | Transport Management System")
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.geometry(
    f"{min(1440, max(1000, screen_width - 80))}x"
    f"{min(920, max(650, screen_height - 80))}"
)
root.minsize(900, 650)
root.configure(bg=theme.BACKGROUND)
style = ttk.Style(root)
style.theme_use("clam")


# ==========================================
# LEFT NAVIGATION SIDEBAR
# ==========================================

SIDEBAR_WIDTH = 250

sidebar_slot = tk.Frame(
    root,
    bg=theme.BACKGROUND,
    width=SIDEBAR_WIDTH
)

sidebar_slot.pack(side="left", fill="y")
sidebar_slot.pack_propagate(False)

sidebar = tk.Frame(
    sidebar_slot,
    bg=theme.GLASS_SIDEBAR,
    width=SIDEBAR_WIDTH
)

sidebar.place(x=0, y=0, width=SIDEBAR_WIDTH, relheight=1)
sidebar.pack_propagate(False)


# Application branding
brand_frame = tk.Frame(
    sidebar,
    bg=theme.GLASS_SIDEBAR
)
brand_frame.pack(fill="x", padx=14, pady=(20, 28))

brand_icon = tk.Canvas(
    brand_frame,
    width=38,
    height=38,
    bg=theme.GLASS_SIDEBAR,
    bd=0,
    highlightthickness=0
)
brand_icon.pack(side="left", padx=(0, 10))
brand_icon.create_rectangle(2, 2, 36, 36, fill=theme.ACCENT, outline="")
brand_icon.create_rectangle(10, 12, 28, 24, fill=theme.TEXT_PRIMARY, outline="")
brand_icon.create_rectangle(13, 14, 18, 18, fill=theme.ACCENT, outline="")
brand_icon.create_rectangle(20, 14, 25, 18, fill=theme.ACCENT, outline="")
brand_icon.create_oval(12, 22, 17, 27, fill=theme.TEXT_PRIMARY, outline="")
brand_icon.create_oval(22, 22, 27, 27, fill=theme.TEXT_PRIMARY, outline="")

brand_text = tk.Frame(
    brand_frame,
    bg=theme.GLASS_SIDEBAR
)
brand_text.pack(side="left", fill="x", expand=True)

app_name = tk.Label(
    brand_text,
    text="School\nTransit",
    font=("Segoe UI", 11, "bold"),
    bg=theme.GLASS_SIDEBAR,
    fg=theme.TEXT_LIGHT,
    justify="left"
)
app_name.pack(anchor="w")

subtitle = tk.Label(
    brand_text,
    text="TRANSPORT\nMANAGEMENT",
    font=("Segoe UI", 6),
    bg=theme.GLASS_SIDEBAR,
    fg=theme.TEXT_SECONDARY
)
subtitle.pack(anchor="w", pady=(1, 0))


# Navigation heading
nav_heading = tk.Label(
    sidebar,
    text="MAIN MENU",
    font=("Segoe UI", 9, "bold"),
    bg=theme.GLASS_SIDEBAR,
    fg=theme.TEXT_SECONDARY
)

nav_heading.pack(anchor="w", padx=25, pady=(0, 12))


# Currently selected navigation item
active_menu = tk.StringVar(value="Dashboard")

nav_buttons = []
nav_button_names = {}
nav_hover_handlers = {}


def set_active_menu(module_name):

    active_menu.set(module_name)

    for btn in nav_buttons:
        is_active = nav_button_names[btn] == module_name
        button_background = (
            theme.ACCENT if is_active else theme.GLASS_SIDEBAR
        )
        button_foreground = (
            theme.TEXT_PRIMARY if is_active else theme.TEXT_LIGHT
        )
        btn.config(
            bg=button_background,
            fg=button_foreground,
            activebackground=button_background,
            activeforeground=button_foreground,
            font=(
                ("Segoe UI", 11, "bold")
                if is_active
                else ("Segoe UI", 11)
            )
        )
        handler = nav_hover_handlers.get(btn)
        if handler is not None:
            handler(is_active)


# Navigation button action
def open_module(module_name):

    if page_transition["busy"]:
        return

    set_active_menu(module_name)
    module_page = None

    if module_name == "Routes & Buses":
        module_page = open_routes_module(page_container)

    elif module_name == "Bus Stops":
        module_page = open_stops_module(page_container)

    elif module_name == "Student Allocation":
        module_page = open_student_allocation_module(
            page_container,
            refresh_dashboard
        )

    elif module_name == "Fee Management":
        module_page = open_fee_management_module(
            page_container,
            refresh_dashboard
        )

    elif module_name == "Bus Passes":
        module_page = open_bus_passes_module(page_container, refresh_dashboard)

    elif module_name == "Reports":
        module_page = open_reports_module(page_container)

    elif module_name == "Dashboard":
        refresh_dashboard()
        show_page(dashboard_page)
        if sidebar_animation["target_x"] == 0:
            toggle_sidebar()
        return

    else:
        messagebox.showinfo(
            module_name,
            f"{module_name} module will be available soon!"
        )

    if module_page is not None:
        show_page(module_page)


# Navigation menu items
menu_items = [
    ("▦", "Dashboard"),
    ("↗", "Routes & Buses"),
    ("⌖", "Bus Stops"),
    ("♙", "Student Allocation"),
    ("▣", "Fee Management"),
    ("▤", "Bus Passes"),
    ("▥", "Reports")
]


# Create navigation buttons
for icon, item in menu_items:

    button = RoundedButton(
        sidebar,
        text=f"  {icon}   {item}",
        font=(
            ("Segoe UI", 10, "bold")
            if item == "Dashboard"
            else ("Segoe UI", 10)
        ),
        bg=theme.GLASS_SIDEBAR,
        fg=theme.TEXT_LIGHT,
        activebackground=theme.SECONDARY,
        activeforeground=theme.TEXT_LIGHT,
        relief="flat",
        anchor="w",
        padx=20,
        pady=13,
        cursor="hand2",
        command=lambda name=item.strip(): open_module(name)
    )

    button.pack(fill="x", padx=12, pady=2)

    nav_buttons.append(button)
    nav_button_names[button] = item

    nav_hover_handlers[button] = bind_sidebar_item(button)

set_active_menu(active_menu.get())

admin_footer = tk.Frame(
    sidebar,
    bg=theme.PRIMARY,
    padx=9,
    pady=8
)
admin_footer.pack(side="bottom", fill="x", padx=12, pady=14)

admin_avatar = tk.Canvas(
    admin_footer,
    width=26,
    height=26,
    bg=theme.PRIMARY,
    bd=0,
    highlightthickness=0
)
admin_avatar.pack(side="left", padx=(0, 8))
admin_avatar.create_oval(1, 1, 25, 25, fill=theme.ACCENT, outline="")
admin_avatar.create_text(
    13,
    13,
    text="A",
    fill=theme.TEXT_PRIMARY,
    font=("Segoe UI", 9, "bold")
)

admin_footer_text = tk.Frame(admin_footer, bg=theme.PRIMARY)
admin_footer_text.pack(side="left", fill="x", expand=True)
tk.Label(
    admin_footer_text,
    text="Administrator",
    font=("Segoe UI", 9, "bold"),
    bg=theme.PRIMARY,
    fg=theme.TEXT_LIGHT
).pack(anchor="w")
tk.Label(
    admin_footer_text,
    text="Admin",
    font=("Segoe UI", 7),
    bg=theme.PRIMARY,
    fg=theme.TEXT_SECONDARY
).pack(anchor="w")

set_active_menu(active_menu.get())


# ==========================================
# MAIN CONTENT AREA
# ==========================================

content_area = tk.Frame(
    root,
    bg=theme.BACKGROUND
)

content_area.pack(
    side="right",
    fill="both",
    expand=True
)


# ==========================================
# DASHBOARD HEADING
# ==========================================

content_header = tk.Frame(
    content_area,
    bg=theme.BACKGROUND
)
content_header.pack(
    fill="x",
)


SIDEBAR_ANIMATION_STEPS = 16
SIDEBAR_ANIMATION_INTERVAL_MS = 15
sidebar_animation = {
    "after_id": None,
    "target_x": 0
}


def toggle_sidebar():

    pending_after_id = sidebar_animation["after_id"]
    if pending_after_id is not None:
        root.after_cancel(pending_after_id)
        sidebar_animation["after_id"] = None

    target_x = (
        -SIDEBAR_WIDTH
        if sidebar_animation["target_x"] == 0
        else 0
    )

    if target_x == 0 and not sidebar_slot.winfo_manager():
        sidebar_slot.pack(side="left", fill="y", before=content_area)
        sidebar.place_configure(
            x=-SIDEBAR_WIDTH,
            y=0,
            width=SIDEBAR_WIDTH,
            relheight=1
        )
        start_x = -SIDEBAR_WIDTH
    else:
        start_x = sidebar.winfo_x()

    sidebar_animation["target_x"] = target_x
    menu_toggle_button.configure(
        text="☰" if target_x < 0 else "×"
    )

    def animate_sidebar(step):

        progress = step / SIDEBAR_ANIMATION_STEPS
        if progress < 0.5:
            eased_progress = 4 * progress ** 3
        else:
            eased_progress = 1 - ((-2 * progress + 2) ** 3) / 2

        position = round(
            start_x
            + (target_x - start_x) * eased_progress
        )
        sidebar.place_configure(x=position)

        if step < SIDEBAR_ANIMATION_STEPS:
            sidebar_animation["after_id"] = root.after(
                SIDEBAR_ANIMATION_INTERVAL_MS,
                lambda: animate_sidebar(step + 1)
            )
            return

        sidebar_animation["after_id"] = None
        if target_x < 0:
            sidebar_slot.pack_forget()

    animate_sidebar(1)


menu_toggle_button = RoundedButton(
    content_header,
    text="×",
    font=("Segoe UI", 14, "bold"),
    bg=theme.SECONDARY,
    fg=theme.TEXT_LIGHT,
    activebackground=theme.PRIMARY,
    activeforeground=theme.TEXT_LIGHT,
    padx=12,
    pady=5,
    command=toggle_sidebar
)
menu_toggle_button.pack(side="left", padx=35, pady=(10, 6))

page_container = tk.Frame(
    content_area,
    bg=theme.BACKGROUND
)
page_container.pack(fill="both", expand=True)

dashboard_page = ScrollableFrame(
    page_container,
    bg=theme.BACKGROUND
)
dashboard_page.place(x=0, y=0, relwidth=1, relheight=1)
dashboard_content = dashboard_page.content

PAGE_TRANSITION_STEPS = 16
PAGE_TRANSITION_INTERVAL_MS = 12
PAGE_TRANSITION_OFFSET = 34
page_transition = {
    "after_id": None,
    "busy": False,
    "current": dashboard_page
}


def show_page(target_page):

    previous_page = page_transition["current"]
    if page_transition["busy"] or target_page is previous_page:
        return

    page_transition["busy"] = True
    target_page.place(
        x=PAGE_TRANSITION_OFFSET,
        y=0,
        relwidth=1,
        relheight=1
    )
    target_page.lift()

    def animate_page(step):

        progress = step / PAGE_TRANSITION_STEPS
        eased_progress = 1 - (1 - progress) ** 3
        position = round(PAGE_TRANSITION_OFFSET * (1 - eased_progress))
        target_page.place_configure(x=position)

        if step < PAGE_TRANSITION_STEPS:
            page_transition["after_id"] = root.after(
                PAGE_TRANSITION_INTERVAL_MS,
                lambda: animate_page(step + 1)
            )
            return

        target_page.place_configure(x=0)
        previous_page.place_forget()
        if previous_page is not dashboard_page:
            previous_page.destroy()
        page_transition["current"] = target_page
        page_transition["after_id"] = None
        page_transition["busy"] = False

    animate_page(1)


def fetch_route_overview(cursor):

    cursor.execute("""
        SELECT
            r.route_id,
            r.route_name,
            r.start_point,
            r.end_point,
            s.stop_name,
            COALESCE(SUM(
                CASE
                    WHEN st.transport_status = 'Active' THEN 1
                    ELSE 0
                END
            ), 0)
        FROM routes r
        LEFT JOIN stops s
            ON s.route_id = r.route_id
        LEFT JOIN student_transport st
            ON st.stop_id = s.stop_id
        GROUP BY
            r.route_id,
            r.route_name,
            r.start_point,
            r.end_point,
            s.stop_id,
            s.stop_name
        ORDER BY r.route_id, s.stop_id
    """)
    return cursor.fetchall()


connection = get_connection()
cursor = connection.cursor()
cursor.execute("SELECT COUNT(*) FROM routes")
total_routes = cursor.fetchone()[0]
cursor.execute("""
    SELECT COUNT(*)
    FROM student_transport
    WHERE transport_status = 'Active'
""")
total_students = cursor.fetchone()[0]
cursor.execute(
    "SELECT COALESCE(SUM(max_capacity), 0) FROM routes"
)
total_capacity = cursor.fetchone()[0]
cursor.execute(
    "SELECT COALESCE(SUM(dues), 0) FROM student_transport"
)
total_dues = cursor.fetchone()[0]
route_overview_rows = fetch_route_overview(cursor)
connection.close()


# ==========================================
# DASHBOARD HEADER
# ==========================================

dashboard_heading = tk.Frame(
    dashboard_content,
    bg=theme.BACKGROUND
)
dashboard_heading.pack(
    fill="x",
    padx=28,
    pady=(10, 12)
)

heading_text = tk.Frame(dashboard_heading, bg=theme.BACKGROUND)
heading_text.pack(side="left")

admin_label = tk.Label(
    heading_text,
    text="SCHOOL ADMINISTRATION",
    font=("Segoe UI", 8, "bold"),
    bg=theme.BACKGROUND,
    fg=theme.TEXT_SECONDARY
)
admin_label.pack(anchor="w")

dashboard_title = tk.Label(
    heading_text,
    text="Dashboard",
    font=("Segoe UI", 26, "bold"),
    bg=theme.BACKGROUND,
    fg=theme.TEXT_PRIMARY
)
dashboard_title.pack(anchor="w")

profile_panel = RoundedPanel(
    dashboard_heading,
    bg=theme.CARD_BACKGROUND,
    padx=9,
    pady=6,
    radius=16,
    highlightbackground=theme.GLASS_BORDER,
    highlightthickness=1,
    hoverable=False
)
profile_panel.pack(side="right", pady=(5, 0))

profile_avatar = tk.Canvas(
    profile_panel.content,
    width=28,
    height=28,
    bg=theme.CARD_BACKGROUND,
    bd=0,
    highlightthickness=0
)
profile_avatar.pack(side="left", padx=(0, 7))
profile_avatar.create_oval(1, 1, 27, 27, fill=theme.SECONDARY, outline="")
profile_avatar.create_text(
    14,
    14,
    text="A",
    fill=theme.TEXT_LIGHT,
    font=("Segoe UI", 9, "bold")
)

profile_text = tk.Frame(profile_panel.content, bg=theme.CARD_BACKGROUND)
profile_text.pack(side="left")
tk.Label(
    profile_text,
    text="Administrator",
    font=("Segoe UI", 8, "bold"),
    bg=theme.CARD_BACKGROUND,
    fg=theme.TEXT_PRIMARY
).pack(anchor="w")
tk.Label(
    profile_text,
    text="Admin",
    font=("Segoe UI", 7),
    bg=theme.CARD_BACKGROUND,
    fg=theme.TEXT_SECONDARY
).pack(anchor="w")


# ==========================================
# TRANSPORT OVERVIEW BANNER
# ==========================================

hero_frame = RoundedPanel(
    dashboard_content,
    bg=theme.PRIMARY,
    padx=0,
    pady=0,
    radius=12,
    highlightbackground=theme.PRIMARY,
    highlightthickness=1,
    hoverable=False
)
hero_frame.pack(fill="x", padx=28, pady=(0, 12))

hero_body = tk.Frame(hero_frame.content, bg=theme.PRIMARY)
hero_body.grid(row=0, column=0, sticky="nsew", padx=20, pady=14)
hero_frame.content.grid_columnconfigure(0, weight=1)
hero_frame.content.grid_rowconfigure(0, weight=1)

hero_text = tk.Frame(hero_body, bg=theme.PRIMARY)
hero_text.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
hero_body.grid_columnconfigure(0, weight=3)
hero_body.grid_columnconfigure(1, weight=2)

overview_badge = tk.Label(
    hero_text,
    text="TRANSPORT OVERVIEW",
    font=("Segoe UI", 7, "bold"),
    bg=theme.ACCENT,
    fg=theme.TEXT_PRIMARY,
    padx=8,
    pady=4
)
overview_badge.pack(anchor="w", pady=(0, 8))

hero_title = tk.Label(
    hero_text,
    text="Welcome back! Here's your transport overview.",
    font=("Segoe UI", 19, "bold"),
    bg=theme.PRIMARY,
    fg=theme.TEXT_LIGHT,
    justify="left",
    wraplength=410
)
hero_title.pack(anchor="w")

hero_summary_label = tk.Label(
    hero_text,
    text=(
        f"{total_routes} routes, {total_students} active students and "
        f"₹{total_dues:,.2f} in outstanding fees across the fleet today."
    ),
    font=("Segoe UI", 9),
    bg=theme.PRIMARY,
    fg=theme.TEXT_LIGHT,
    justify="left",
    wraplength=410
)
hero_summary_label.pack(anchor="w", pady=(6, 9))

hero_actions = tk.Frame(hero_text, bg=theme.PRIMARY)
hero_actions.pack(anchor="w")

allocation_action = RoundedButton(
    hero_actions,
    text="Student Allocation",
    font=("Segoe UI", 8, "bold"),
    bg=theme.ACCENT,
    fg=theme.TEXT_PRIMARY,
    activebackground=theme.ACCENT,
    activeforeground=theme.TEXT_PRIMARY,
    padx=12,
    pady=6,
    command=lambda: open_module("Student Allocation")
)
allocation_action.configure(
    bg=theme.ACCENT,
    fg=theme.TEXT_PRIMARY,
    activebackground=theme.ACCENT,
    activeforeground=theme.TEXT_PRIMARY
)
allocation_action.pack(side="left", padx=(0, 7))

passes_action = RoundedButton(
    hero_actions,
    text="View Bus Passes",
    font=("Segoe UI", 8, "bold"),
    bg=theme.PRIMARY,
    fg=theme.TEXT_LIGHT,
    activebackground=theme.SECONDARY,
    activeforeground=theme.TEXT_LIGHT,
    padx=12,
    pady=6,
    command=lambda: open_module("Bus Passes")
)
passes_action.pack(side="left")

hero_route_canvas = tk.Canvas(
    hero_body,
    width=300,
    height=138,
    bg=theme.PRIMARY,
    bd=0,
    highlightthickness=0
)
hero_route_canvas.grid(row=0, column=1, sticky="nsew")


def draw_route_overview(event=None):

    width = max(hero_route_canvas.winfo_width(), 240)
    height = max(hero_route_canvas.winfo_height(), 120)
    hero_route_canvas.delete("all")

    start_x = 18
    start_y = height * 0.68
    middle_x = width * 0.42
    middle_y = height * 0.46
    end_x = width - 24
    end_y = height * 0.35

    hero_route_canvas.create_line(
        start_x,
        start_y,
        middle_x,
        middle_y,
        width * 0.65,
        height * 0.69,
        end_x,
        end_y,
        smooth=True,
        splinesteps=20,
        dash=(2, 5),
        fill=theme.MOSS,
        width=2
    )

    for x, y in ((start_x, start_y), (end_x, end_y)):
        hero_route_canvas.create_oval(
            x - 6,
            y - 6,
            x + 6,
            y + 6,
            fill=theme.CARD_BACKGROUND,
            outline=theme.MOSS,
            width=2
        )

    bus_x = width * 0.62
    bus_y = height * 0.37
    hero_route_canvas.create_rectangle(
        bus_x - 17,
        bus_y - 8,
        bus_x + 17,
        bus_y + 7,
        fill=theme.MOSS,
        outline=theme.MOSS
    )
    hero_route_canvas.create_rectangle(
        bus_x - 12,
        bus_y - 5,
        bus_x - 4,
        bus_y,
        fill=theme.PRIMARY,
        outline=""
    )
    hero_route_canvas.create_rectangle(
        bus_x - 2,
        bus_y - 5,
        bus_x + 7,
        bus_y,
        fill=theme.PRIMARY,
        outline=""
    )
    for wheel_x in (bus_x - 10, bus_x + 10):
        hero_route_canvas.create_oval(
            wheel_x - 3,
            bus_y + 4,
            wheel_x + 3,
            bus_y + 10,
            fill=theme.TEXT_PRIMARY,
            outline=""
        )

    first_route = route_overview_rows[0] if route_overview_rows else None
    start_name = (
        first_route[2] or "Start not set"
        if first_route
        else "No route yet"
    )
    end_name = (
        first_route[3] or "End not set"
        if first_route
        else "Add routes to begin"
    )
    hero_route_canvas.create_text(
        start_x,
        start_y + 16,
        text=start_name,
        fill=theme.TEXT_LIGHT,
        font=("Segoe UI", 7, "bold"),
        anchor="n"
    )
    hero_route_canvas.create_text(
        end_x,
        end_y + 16,
        text=end_name,
        fill=theme.TEXT_LIGHT,
        font=("Segoe UI", 7, "bold"),
        anchor="n"
    )


hero_route_canvas.bind("<Configure>", draw_route_overview, add="+")

hero_footer = tk.Canvas(
    hero_frame.content,
    height=7,
    bg=theme.PRIMARY,
    bd=0,
    highlightthickness=0
)
hero_footer.grid(row=1, column=0, sticky="ew")


def draw_hero_stripes(event):

    hero_footer.delete("all")
    for start in range(-7, event.width, 22):
        hero_footer.create_polygon(
            start,
            7,
            start + 8,
            7,
            start + 15,
            0,
            start + 7,
            0,
            fill=theme.ACCENT,
            outline=""
        )


hero_footer.bind("<Configure>", draw_hero_stripes, add="+")


# ==========================================
# DASHBOARD STATISTICS
# ==========================================

stats_frame = tk.Frame(dashboard_content, bg=theme.BACKGROUND)
stats_frame.pack(fill="x", padx=28, pady=(0, 12))

stats = [
    (
        "TOTAL ROUTES",
        str(total_routes),
        theme.CARD_BACKGROUND,
        theme.TEXT_SECONDARY,
        theme.SECONDARY,
        "↗"
    ),
    (
        "ACTIVE STUDENTS",
        str(total_students),
        theme.CARD_BACKGROUND,
        theme.TEXT_SECONDARY,
        theme.SECONDARY,
        "●"
    ),
    (
        "TOTAL BUS CAPACITY",
        str(total_capacity),
        theme.CARD_BACKGROUND,
        theme.TEXT_SECONDARY,
        theme.SECONDARY,
        "▣"
    ),
    (
        "OUTSTANDING FEES",
        f"₹{total_dues:,.2f}",
        theme.PRIMARY,
        theme.TEXT_LIGHT,
        theme.ACCENT,
        "DUE"
    )
]

stat_value_labels = {}

for index, (title, value, surface, title_color, value_color, badge) in enumerate(stats):

    card = RoundedPanel(
        stats_frame,
        bg=surface,
        padx=14,
        pady=11,
        highlightbackground=(
            surface if surface != theme.CARD_BACKGROUND
            else theme.GLASS_BORDER
        ),
        highlightthickness=1,
        hoverable=True
    )
    card.grid(row=0, column=index, padx=5, sticky="nsew")
    stats_frame.grid_columnconfigure(index, weight=1)

    card_header = tk.Frame(card.content, bg=surface)
    card_header.pack(fill="x")
    tk.Label(
        card_header,
        text=title,
        font=("Segoe UI", 7, "bold"),
        bg=surface,
        fg=title_color
    ).pack(side="left", anchor="w")

    badge_background = (
        theme.DANGER if badge == "DUE"
        else theme.PALE_GREEN
    )
    badge_foreground = (
        theme.TEXT_LIGHT if badge == "DUE"
        else theme.SECONDARY
    )
    tk.Label(
        card_header,
        text=badge,
        font=("Segoe UI", 7, "bold"),
        bg=badge_background,
        fg=badge_foreground,
        padx=5,
        pady=2
    ).pack(side="right")

    card_value = tk.Label(
        card.content,
        text=value,
        font=("Segoe UI", 23, "bold"),
        bg=surface,
        fg=value_color
    )
    card_value.pack(anchor="w", pady=(8, 0))
    stat_value_labels[title] = card_value


# ==========================================
# SEAT ALLOCATION AND ROUTE STOPS
# ==========================================

dashboard_summary = tk.Frame(dashboard_content, bg=theme.BACKGROUND)
dashboard_summary.pack(fill="x", padx=28, pady=(0, 12))
dashboard_summary.grid_columnconfigure(0, weight=1)
dashboard_summary.grid_columnconfigure(1, weight=1)

seat_panel = RoundedPanel(
    dashboard_summary,
    bg=theme.CARD_BACKGROUND,
    padx=15,
    pady=12,
    highlightbackground=theme.GLASS_BORDER,
    highlightthickness=1,
    hoverable=True
)
seat_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

seat_header = tk.Frame(seat_panel.content, bg=theme.CARD_BACKGROUND)
seat_header.pack(fill="x")
tk.Label(
    seat_header,
    text="Seat allocation",
    font=("Segoe UI", 11, "bold"),
    bg=theme.CARD_BACKGROUND,
    fg=theme.TEXT_PRIMARY
).pack(side="left")

seat_taken_label = tk.Label(
    seat_header,
    text=f"{total_students} of {total_capacity} seats taken",
    font=("Segoe UI", 7, "bold"),
    bg=theme.CARD_BACKGROUND,
    fg=theme.SECONDARY
)
seat_taken_label.pack(side="right")

seat_progress_values = {
    "active": total_students,
    "capacity": total_capacity
}
seat_progress_canvas = tk.Canvas(
    seat_panel.content,
    height=12,
    bg=theme.CARD_BACKGROUND,
    bd=0,
    highlightthickness=0
)
seat_progress_canvas.pack(fill="x", pady=(7, 9))


def draw_seat_progress(event=None):

    width = max(seat_progress_canvas.winfo_width(), 1)
    height = max(seat_progress_canvas.winfo_height(), 1)
    seat_progress_canvas.delete("all")
    inset = height / 2
    seat_progress_canvas.create_line(
        inset,
        height / 2,
        width - inset,
        height / 2,
        fill=theme.PALE_GREEN,
        width=height,
        capstyle="round"
    )
    capacity = seat_progress_values["capacity"]
    if capacity <= 0:
        return
    progress = min(seat_progress_values["active"] / capacity, 1)
    if progress:
        seat_progress_canvas.create_line(
            inset,
            height / 2,
            inset + (width - 2 * inset) * progress,
            height / 2,
            fill=theme.SECONDARY,
            width=height,
            capstyle="round"
        )


seat_progress_canvas.bind("<Configure>", draw_seat_progress, add="+")

seat_metrics = tk.Frame(seat_panel.content, bg=theme.CARD_BACKGROUND)
seat_metrics.pack(fill="x")
seat_metric_values = {}

for index, (key, title, value) in enumerate((
    ("active", "Active students", total_students),
    ("open", "Seats still open", max(total_capacity - total_students, 0)),
    ("capacity", "Total capacity", total_capacity)
)):
    metric = tk.Frame(seat_metrics, bg=theme.CARD_BACKGROUND)
    metric.grid(row=0, column=index, sticky="w", padx=(0, 18))
    tk.Label(
        metric,
        text=title,
        font=("Segoe UI", 7),
        bg=theme.CARD_BACKGROUND,
        fg=theme.TEXT_SECONDARY
    ).pack(anchor="w")
    value_label = tk.Label(
        metric,
        text=str(value),
        font=("Segoe UI", 11, "bold"),
        bg=theme.CARD_BACKGROUND,
        fg=theme.TEXT_PRIMARY
    )
    value_label.pack(anchor="w", pady=(2, 0))
    seat_metric_values[key] = value_label

route_panel = RoundedPanel(
    dashboard_summary,
    bg=theme.CARD_BACKGROUND,
    padx=15,
    pady=12,
    highlightbackground=theme.GLASS_BORDER,
    highlightthickness=1,
    hoverable=True
)
route_panel.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

route_header = tk.Frame(route_panel.content, bg=theme.CARD_BACKGROUND)
route_header.pack(fill="x", pady=(0, 6))
route_stops_title = tk.Label(
    route_header,
    text="Route stops",
    font=("Segoe UI", 11, "bold"),
    bg=theme.CARD_BACKGROUND,
    fg=theme.TEXT_PRIMARY
)
route_stops_title.pack(side="left")

route_navigation = tk.Frame(route_header, bg=theme.CARD_BACKGROUND)
route_navigation.pack(side="right")
route_count_badge = tk.Label(
    route_navigation,
    text="0 / 0",
    font=("Segoe UI", 7, "bold"),
    bg=theme.PALE_GREEN,
    fg=theme.SECONDARY,
    padx=6,
    pady=2
)
route_previous_button = RoundedButton(
    route_navigation,
    text="‹",
    font=("Segoe UI", 11, "bold"),
    bg=theme.PALE_GREEN,
    fg=theme.TEXT_PRIMARY,
    activebackground=theme.MOSS,
    activeforeground=theme.TEXT_PRIMARY,
    padx=6,
    pady=1
)
route_previous_button.pack(side="left", padx=(0, 4))
route_count_badge.pack(side="left", padx=(0, 4))
route_next_button = RoundedButton(
    route_navigation,
    text="›",
    font=("Segoe UI", 11, "bold"),
    bg=theme.PALE_GREEN,
    fg=theme.TEXT_PRIMARY,
    activebackground=theme.MOSS,
    activeforeground=theme.TEXT_PRIMARY,
    padx=6,
    pady=1
)
route_next_button.pack(side="left")

route_stops_list = tk.Frame(route_panel.content, bg=theme.CARD_BACKGROUND)
route_stops_list.pack(fill="x")
route_slide_state = {"index": 0}


def get_route_groups():
    route_groups = []
    for (
        route_id,
        route_name,
        start_point,
        end_point,
        stop_name,
        student_count
    ) in route_overview_rows:
        if not route_groups or route_groups[-1]["route_id"] != route_id:
            route_groups.append({
                "route_id": route_id,
                "name": route_name,
                "start_point": start_point,
                "end_point": end_point,
                "stops": []
            })
        if stop_name:
            route_groups[-1]["stops"].append((stop_name, student_count))

    return route_groups


def show_route_slide(route_groups):

    for child in route_stops_list.winfo_children():
        child.destroy()

    if not route_groups:
        route_count_badge.config(text="0 / 0")
        route_previous_button.config(state=tk.DISABLED)
        route_next_button.config(state=tk.DISABLED)
        tk.Label(
            route_stops_list,
            text="No routes have been added yet.",
            font=("Segoe UI", 8),
            bg=theme.CARD_BACKGROUND,
            fg=theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(2, 0))
        return

    route_slide_state["index"] %= len(route_groups)
    route_index = route_slide_state["index"]
    route = route_groups[route_index]
    route_count_badge.config(
        text=f"{route_index + 1} / {len(route_groups)}"
    )
    button_state = (
        tk.NORMAL if len(route_groups) > 1 else tk.DISABLED
    )
    route_previous_button.config(state=button_state)
    route_next_button.config(state=button_state)

    route_slide_header = tk.Frame(
        route_stops_list,
        bg=theme.CARD_BACKGROUND
    )
    route_slide_header.pack(fill="x", pady=(2, 3))
    tk.Label(
        route_slide_header,
        text=route["name"],
        font=("Segoe UI", 9, "bold"),
        bg=theme.CARD_BACKGROUND,
        fg=theme.SECONDARY
    ).pack(side="left")
    tk.Label(
        route_slide_header,
        text=f"{len(route['stops'])} stops",
        font=("Segoe UI", 7),
        bg=theme.CARD_BACKGROUND,
        fg=theme.TEXT_SECONDARY
    ).pack(side="right")

    endpoint_row = tk.Frame(
        route_stops_list,
        bg=theme.GLASS_FIELD
    )
    endpoint_row.pack(fill="x", pady=(0, 5))
    endpoint_row.grid_columnconfigure(0, weight=1)
    endpoint_row.grid_columnconfigure(2, weight=1)

    start_block = tk.Frame(endpoint_row, bg=theme.GLASS_FIELD)
    start_block.grid(row=0, column=0, sticky="ew", padx=(8, 2), pady=5)
    tk.Label(
        start_block,
        text="START POINT",
        font=("Segoe UI", 6, "bold"),
        bg=theme.GLASS_FIELD,
        fg=theme.TEXT_SECONDARY
    ).pack(anchor="w")
    tk.Label(
        start_block,
        text=route["start_point"] or "Not set",
        font=("Segoe UI", 8, "bold"),
        bg=theme.GLASS_FIELD,
        fg=theme.TEXT_PRIMARY,
        wraplength=135,
        justify="left"
    ).pack(anchor="w")

    tk.Label(
        endpoint_row,
        text="→",
        font=("Segoe UI", 11, "bold"),
        bg=theme.GLASS_FIELD,
        fg=theme.MOSS
    ).grid(row=0, column=1, padx=4)

    end_block = tk.Frame(endpoint_row, bg=theme.GLASS_FIELD)
    end_block.grid(row=0, column=2, sticky="ew", padx=(2, 8), pady=5)
    tk.Label(
        end_block,
        text="END POINT",
        font=("Segoe UI", 6, "bold"),
        bg=theme.GLASS_FIELD,
        fg=theme.TEXT_SECONDARY
    ).pack(anchor="w")
    tk.Label(
        end_block,
        text=route["end_point"] or "Not set",
        font=("Segoe UI", 8, "bold"),
        bg=theme.GLASS_FIELD,
        fg=theme.TEXT_PRIMARY,
        wraplength=135,
        justify="left"
    ).pack(anchor="w")

    if not route["stops"]:
        tk.Label(
            route_stops_list,
            text="No stops added yet.",
            font=("Segoe UI", 7),
            bg=theme.CARD_BACKGROUND,
            fg=theme.TEXT_SECONDARY
        ).pack(anchor="w", padx=(12, 0), pady=(2, 0))
        return

    for stop_name, student_count in route["stops"]:
        row = tk.Frame(route_stops_list, bg=theme.CARD_BACKGROUND)
        row.pack(fill="x", pady=(2, 0))
        tk.Label(
            row,
            text="●",
            font=("Segoe UI", 8),
            bg=theme.CARD_BACKGROUND,
            fg=theme.MOSS
        ).pack(side="left", padx=(2, 6))
        tk.Label(
            row,
            text=stop_name,
            font=("Segoe UI", 8),
            bg=theme.CARD_BACKGROUND,
            fg=theme.TEXT_PRIMARY
        ).pack(side="left")
        tk.Label(
            row,
            text=f"{student_count} students",
            font=("Segoe UI", 7),
            bg=theme.CARD_BACKGROUND,
            fg=theme.TEXT_SECONDARY
        ).pack(side="right")


def change_route_slide(offset):

    route_groups = get_route_groups()
    if not route_groups:
        return
    route_slide_state["index"] = (
        route_slide_state["index"] + offset
    ) % len(route_groups)
    show_route_slide(route_groups)


def update_route_stops():

    show_route_slide(get_route_groups())


route_previous_button.config(
    command=lambda: change_route_slide(-1)
)
route_next_button.config(
    command=lambda: change_route_slide(1)
)


update_route_stops()


# ==========================================
# RECENT STUDENT ALLOCATIONS
# ==========================================

recent_frame = RoundedPanel(
    dashboard_content,
    bg=theme.CARD_BACKGROUND,
    padx=15,
    pady=13,
    highlightbackground=theme.GLASS_BORDER,
    highlightthickness=1
)

recent_frame.pack(
    fill="both",
    expand=True,
    padx=28,
    pady=(0, 16)
)


recent_title = tk.Label(
    recent_frame.content,
    text="Recent Student Allocations",
    font=("Segoe UI", 13, "bold"),
    bg=theme.CARD_BACKGROUND,
    fg=theme.PRIMARY
)

recent_title.pack(
    anchor="w",
    pady=(0, 8)
)

# ==========================================
# STUDENT SEARCH BAR
# ==========================================

search_frame = tk.Frame(
    recent_frame.content,
    bg=theme.CARD_BACKGROUND
)

search_frame.pack(
    fill="x",
    pady=(0, 9)
)

search_label = tk.Label(
    search_frame,
    text="Search Student:",
    font=("Segoe UI", 8, "bold"),
    bg=theme.CARD_BACKGROUND,
    fg=theme.PRIMARY
)

search_label.pack(side="left", padx=(0, 10))

search_entry = RoundedEntry(
    search_frame,
    font=("Segoe UI", 10),
    width=35
)

search_entry.pack(side="left", padx=(0, 10))
search_placeholder = "Name or registration no."
search_entry.insert(0, search_placeholder)
search_entry["foreground"] = theme.TEXT_SECONDARY


def current_search_term():

    value = search_entry.get().strip()
    return "" if value == search_placeholder else value


def on_search_focus_in(event):

    if search_entry.get() == search_placeholder:
        search_entry.delete(0, tk.END)
        search_entry["foreground"] = theme.TEXT_PRIMARY


def on_search_focus_out(event):

    if not search_entry.get().strip():
        search_entry.insert(0, search_placeholder)
        search_entry["foreground"] = theme.TEXT_SECONDARY


search_entry.bind("<FocusIn>", on_search_focus_in, add="+")
search_entry.bind("<FocusOut>", on_search_focus_out, add="+")



search_button = RoundedButton(
    search_frame,
    text="Search",
    font=("Segoe UI", 8, "bold"),
    bg=theme.SECONDARY,
    fg=theme.TEXT_LIGHT,
    relief="flat",
    padx=15,
    pady=6,
    cursor="hand2"
)
search_button.configure(
    bg=theme.SECONDARY,
    fg=theme.TEXT_LIGHT,
    activebackground=theme.PRIMARY,
    activeforeground=theme.TEXT_LIGHT
)

search_button.pack(side="left")

clear_button = RoundedButton(
    search_frame,
    text="Clear",
    font=("Segoe UI", 8, "bold"),
    bg=theme.GLASS_FIELD,
    fg=theme.PRIMARY,
    relief="flat",
    padx=15,
    pady=6,
    cursor="hand2"
)
clear_button.configure(
    bg=theme.GLASS_FIELD,
    fg=theme.TEXT_PRIMARY,
    activebackground=theme.CARD_BACKGROUND,
    activeforeground=theme.TEXT_PRIMARY
)

clear_button.pack(side="left", padx=(8, 0))

# Export student records button
export_button = RoundedButton(
    search_frame,
    text="Export CSV",
    font=("Segoe UI", 8, "bold"),
    bg=theme.ACCENT,
    fg=theme.TEXT_PRIMARY,
    relief="flat",
    padx=15,
    pady=6,
    cursor="hand2"
)
export_button.configure(
    bg=theme.ACCENT,
    fg=theme.TEXT_PRIMARY,
    activebackground=theme.ACCENT,
    activeforeground=theme.TEXT_PRIMARY
)

export_button.pack(side="left", padx=(8, 0))

# Student record counter
record_count_label = tk.Label(
    search_frame,
    text="Showing 0 student records",
    font=("Segoe UI", 8),
    bg=theme.CARD_BACKGROUND,
    fg=theme.TEXT_SECONDARY
)

record_count_label.pack(side="right", padx=10)

# ==========================================
# STUDENT TABLE STYLING
# ==========================================

style.configure(
    "Treeview",
    background=theme.CARD_BACKGROUND,
    foreground=theme.TEXT_PRIMARY,
    rowheight=30,
    fieldbackground=theme.CARD_BACKGROUND,
    font=("Segoe UI", 10)
)

style.configure(
    "Treeview.Heading",
    background=theme.GLASS_SIDEBAR,
    foreground=theme.TEXT_LIGHT,
    font=("Segoe UI", 10, "bold"),
    padding=7
)

style.configure(
    "Vertical.TScrollbar",
    background=theme.GLASS_SIDEBAR,
    troughcolor=theme.BACKGROUND,
    bordercolor=theme.GLASS_BORDER,
    arrowcolor=theme.TEXT_SECONDARY
)

style.configure(
    "Horizontal.TScrollbar",
    background=theme.GLASS_SIDEBAR,
    troughcolor=theme.BACKGROUND,
    bordercolor=theme.GLASS_BORDER,
    arrowcolor=theme.TEXT_SECONDARY
)

style.map(
    "Treeview",
    background=[("selected", theme.ACCENT)],
    foreground=[("selected", theme.TEXT_PRIMARY)]
)


# ==========================================
# STUDENT TABLE AND SCROLLBAR
# ==========================================

columns = (
    "reg_no",
    "student",
    "route",
    "stop",
    "status",
    "transport_status"
)


# Create container FIRST
table_container = tk.Frame(
    recent_frame.content,
    bg=theme.CARD_BACKGROUND
)

table_container.pack(
    fill="both",
    expand=True
)


# Create student table INSIDE the container
student_table = ttk.Treeview(
    table_container,
    columns=columns,
    show="headings",
    height=3
)
prepare_treeview_hover(student_table)


# Configure table headings
student_table.heading(
    "reg_no",
    text="Registration No.",
    command=lambda: sort_students("reg_no")
)

student_table.heading(
    "student",
    text="Student Name",
    command=lambda: sort_students("student")
)

student_table.heading(
    "route",
    text="Route",
    command=lambda: sort_students("route")
)

student_table.heading(
    "stop",
    text="Bus Stop",
    command=lambda: sort_students("stop")
)

student_table.heading(
    "status",
    text="Pass Status",
    command=lambda: sort_students("status")
)

student_table.heading(
    "transport_status",
    text="Transport Status",
    command=lambda: sort_students("transport_status")
)


# Configure column widths
student_table.column("reg_no", width=120)
student_table.column("student", width=180)
student_table.column("route", width=120)
student_table.column("stop", width=150)
student_table.column("status", width=120)
student_table.column("transport_status", width=140)

# ==========================================
# STUDENT TABLE SORTING
# ==========================================

def sort_students(column, reverse=False):

    records = [
        (student_table.set(item, column), item)
        for item in student_table.get_children("")
    ]

    records.sort(
        key=lambda record: record[0].casefold(),
        reverse=reverse
    )

    for index, (value, item) in enumerate(records):
        student_table.move(item, "", index)

    # Alternate sorting direction on the next click
    student_table.heading(
        column,
        command=lambda: sort_students(column, not reverse)
    )

# Add vertical scrollbar
table_scrollbar = ttk.Scrollbar(
    table_container,
    orient="vertical",
    command=student_table.yview
)
horizontal_scrollbar = ttk.Scrollbar(
    table_container,
    orient="horizontal",
    command=student_table.xview
)

student_table.configure(
    yscrollcommand=table_scrollbar.set,
    xscrollcommand=horizontal_scrollbar.set
)


# Display table and scrollbar
student_table.pack(
    side="left",
    fill="both",
    expand=True
)

table_scrollbar.pack(
    side="right",
    fill="y"
)
horizontal_scrollbar.pack(
    side="bottom",
    fill="x"
)

# ==========================================
# STUDENT PASS STATUS COLOURS
# ==========================================
# Alternating student row colours
student_table.tag_configure(
    "oddrow",
    background=theme.CARD_BACKGROUND
)

student_table.tag_configure(
    "evenrow",
    background=theme.GLASS_FIELD
)

student_table.tag_configure(
    "Active",
    foreground=theme.SUCCESS
)

student_table.tag_configure(
    "Expired",
    foreground=theme.DANGER
)

student_table.tag_configure(
    "Not Issued",
    foreground=theme.TEXT_SECONDARY
)
student_table.tag_configure(
    "Discontinued",
    foreground=theme.DANGER
)


# ==========================================
# FETCH AND SEARCH STUDENT RECORDS
# ==========================================

def load_students(search_term=""):

    # Clear existing table records
    for row in student_table.get_children():
        student_table.delete(row)

    connection = get_connection()
    cursor = connection.cursor()

    search_value = f"%{search_term}%"

    cursor.execute("""
        SELECT
            st.reg_no,
            st.student_name,
            r.route_name,
            s.stop_name,
            st.pass_valid_until,
            st.transport_status
        FROM student_transport st
        INNER JOIN stops s
            ON st.stop_id = s.stop_id
        INNER JOIN routes r
            ON s.route_id = r.route_id
        WHERE
            st.reg_no LIKE ?
            OR st.student_name LIKE ?
            OR r.route_name LIKE ?
        ORDER BY st.alloc_id DESC
    """, (
        search_value,
        search_value,
        search_value
    ))

    students = cursor.fetchall()

    # Update student record counter
    record_count_label.config(
        text=f"Showing {len(students)} student record(s)"
    )

    connection.close()

    today = date.today()

    for index, student in enumerate(students):

        expiry_date = student[4]

        if student[5] == "Discontinued":
            pass_status = "Discontinued"
        elif not expiry_date:
            pass_status = "Not Issued"
        else:
            expiry_date = date.fromisoformat(expiry_date)

            if expiry_date >= today:
                pass_status = "Active"
            else:
                pass_status = "Expired"

        row_tag = "oddrow" if index % 2 == 0 else "evenrow"

        student_table.insert(
            "",
            "end",
            values=(
                student[0],
                student[1],
                student[2],
                student[3],
                pass_status,
                student[5]
            ),
            tags=(row_tag, pass_status)
        )


def refresh_dashboard():

    connection = None

    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM routes")
        total_routes = cursor.fetchone()[0]
        cursor.execute("""
            SELECT COUNT(*)
            FROM student_transport
            WHERE transport_status = 'Active'
        """)
        total_students = cursor.fetchone()[0]
        cursor.execute(
            "SELECT COALESCE(SUM(max_capacity), 0) FROM routes"
        )
        total_capacity = cursor.fetchone()[0]
        cursor.execute(
            "SELECT COALESCE(SUM(dues), 0) FROM student_transport"
        )
        total_dues = cursor.fetchone()[0]
        route_rows = fetch_route_overview(cursor)

    except sqlite3.Error as error:
        messagebox.showerror(
            "Database Error",
            f"Unable to refresh dashboard:\n{error}",
            parent=root
        )
        return

    finally:
        if connection:
            connection.close()

    refreshed_values = {
        "TOTAL ROUTES": str(total_routes),
        "ACTIVE STUDENTS": str(total_students),
        "TOTAL BUS CAPACITY": str(total_capacity),
        "OUTSTANDING FEES": f"₹{total_dues:,.2f}"
    }
    for title, value in refreshed_values.items():
        stat_value_labels[title].config(text=value)

    hero_summary_label.config(
        text=(
            f"{total_routes} routes, {total_students} active students and "
            f"₹{total_dues:,.2f} in outstanding fees across the fleet today."
        )
    )
    seat_taken_label.config(
        text=f"{total_students} of {total_capacity} seats taken"
    )
    seat_metric_values["active"].config(text=str(total_students))
    seat_metric_values["open"].config(
        text=str(max(total_capacity - total_students, 0))
    )
    seat_metric_values["capacity"].config(text=str(total_capacity))
    seat_progress_values["active"] = total_students
    seat_progress_values["capacity"] = total_capacity
    draw_seat_progress()

    route_overview_rows[:] = route_rows
    update_route_stops()
    draw_route_overview()

    load_students(current_search_term())


# ==========================================
# EXPORT STUDENT RECORDS TO CSV
# ==========================================

def export_students():

    records = student_table.get_children()

    if not records:
        messagebox.showwarning(
            "No Records",
            "There are no student records to export."
        )
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv")],
        title="Save Student Records"
    )

    if not file_path:
        return

    with open(file_path, "w", newline="", encoding="utf-8-sig") as file:

        writer = csv.writer(file)

        writer.writerow([
            "Registration Number",
            "Student Name",
            "Route",
            "Bus Stop",
            "Pass Status"
        ])

        for item in records:
            writer.writerow(student_table.item(item, "values"))

    messagebox.showinfo(
        "Export Successful",
        "Student records exported successfully!"
    )

# Load all students when dashboard opens
load_students()

# Connect Search button
search_button.config(
    command=lambda: load_students(current_search_term())
)

# Clear search and display all students
def clear_search():

    search_entry.delete(0, tk.END)
    search_entry.insert(0, search_placeholder)
    search_entry["foreground"] = theme.TEXT_SECONDARY

    load_students()


clear_button.config(
    command=clear_search
)

# Connect Export CSV button
export_button.config(
    command=export_students
)

# Search when Enter key is pressed
search_entry.bind(
    "<Return>",
    lambda event: load_students(current_search_term())
)

# ==========================================
# RUN APPLICATION
# ==========================================

apply_interactive_effects(root, skip_buttons=nav_buttons)

sidebar_slot.pack_forget()
content_area.pack_forget()


def open_dashboard_after_admin_sign_in():

    welcome_screen.destroy()
    root.minsize(1000, 650)
    sidebar_slot.pack(side="left", fill="y")
    content_area.pack(side="right", fill="both", expand=True)
    set_active_menu("Dashboard")
    refresh_dashboard()


welcome_screen = create_welcome_screen(
    root,
    open_dashboard_after_admin_sign_in
)
welcome_screen.pack(fill="both", expand=True)

root.mainloop()
