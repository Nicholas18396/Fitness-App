import tkinter as tk
from tkinter import messagebox

import pushups
import situps
import squats
import lunges
import jumping_jacks
import bicep_curls
import shoulder_press
import high_knees
import mountain_climbers
import plank

import workout_ai
import user_data
import body_diagram


# ============================================================
# GLOBAL VARIABLES
# ============================================================

app_running = True

# ---- Gym color palette ----
BG_DARK      = "#121212"   # near-black background, like a gym floor
BG_PANEL     = "#1c1c1c"   # slightly raised panel color
ACCENT       = "#FF6B00"   # energetic orange accent
STEEL        = "#3a3a3a"   # steel gray for dividers/borders
TEXT_MAIN    = "#F5F5F5"   # bright white-ish text
TEXT_MUTED   = "#9a9a9a"   # muted gray subtitle text

EXIT_COLOR       = "#B71C1C"  # deep red
EXIT_COLOR_HOVER = "#8e1616"

AI_DAILY_COLOR       = "#00C853"  # bright green
AI_DAILY_COLOR_HOVER = "#009624"

AI_GOAL_COLOR       = "#6A1B9A"  # deep violet
AI_GOAL_COLOR_HOVER = "#4a1170"

DONE_COLOR = "#2E7D32"  # muted green for a completed exercise row


# ============================================================
# EXERCISE LIST
# ============================================================
#
# Adding a new exercise means adding one entry here - the menu
# buttons, launch logic, AI workout dashboard, and stats screen
# are all generated from this list.
#

EXERCISES = [
    {
        "name": "PUSHUPS", "emoji": "\U0001F4AA", "module": pushups,
        "color": "#2E8B57", "hover": "#256e46", "is_timed": False
    },
    {
        "name": "SIT-UPS", "emoji": "\U0001F525", "module": situps,
        "color": "#1E88E5", "hover": "#1665a8", "is_timed": False
    },
    {
        "name": "SQUATS", "emoji": "\U0001F3CB", "module": squats,
        "color": "#E65100", "hover": "#b84300", "is_timed": False
    },
    {
        "name": "LUNGES", "emoji": "\U0001F9B5", "module": lunges,
        "color": "#00897B", "hover": "#00695C", "is_timed": False
    },
    {
        "name": "JUMPING JACKS", "emoji": "\u2B50", "module": jumping_jacks,
        "color": "#B8860B", "hover": "#8c6809", "is_timed": False
    },
    {
        "name": "BICEP CURLS", "emoji": "\U0001F4AA", "module": bicep_curls,
        "color": "#7B1FA2", "hover": "#5e1680", "is_timed": False
    },
    {
        "name": "SHOULDER PRESS", "emoji": "\U0001F64C", "module": shoulder_press,
        "color": "#3949AB", "hover": "#283593", "is_timed": False
    },
    {
        "name": "HIGH KNEES", "emoji": "\U0001F3C3", "module": high_knees,
        "color": "#C2185B", "hover": "#93123f", "is_timed": False
    },
    {
        "name": "MOUNTAIN CLIMBERS", "emoji": "\U0001F3D4", "module": mountain_climbers,
        "color": "#6D4C41", "hover": "#4E342E", "is_timed": False
    },
    {
        "name": "PLANK", "emoji": "\u23F1", "module": plank,
        "color": "#455A64", "hover": "#2f3f47", "is_timed": True
    },
]

EXERCISES_BY_NAME = {
    exercise["name"]: exercise
    for exercise in EXERCISES
}

EXERCISE_NAMES = list(EXERCISES_BY_NAME.keys())


# ============================================================
# SESSION / USER STATE
# ============================================================

current_username = None
current_user_data = None
current_user_filepath = None

current_workout = []
current_workout_heading = "TODAY'S AI WORKOUT"
current_workout_type = None
current_workout_goal_text = None


# ============================================================
# BUTTON HOVER HELPER
# ============================================================

def add_hover(widget, normal_color, hover_color):
    """
    Give a button a simple hover effect so it feels more alive,
    like a piece of gym equipment lighting up when you grab it.
    """

    def on_enter(event):
        widget.configure(bg=hover_color)

    def on_leave(event):
        widget.configure(bg=normal_color)

    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)


# ============================================================
# FULLSCREEN HELPER
# ============================================================

def force_fullscreen():
    """
    Re-apply the fullscreen attribute. Called on startup and
    again every time we return from an exercise tracker, since
    hiding/showing the window can otherwise drop back to a
    normal windowed size.
    """

    root.attributes("-fullscreen", True)


# ============================================================
# VIEW SWITCHING
# ============================================================
#
# Every screen lives inside the same fullscreen window. Only
# one is packed (visible) at a time - switching views never
# spawns a new window, so there's nothing to re-apply
# fullscreen to.
#

def show_view(view):

    for candidate in (
        login_view, menu_view, goal_view,
        workout_view, hooray_view, muscle_view, stats_view
    ):

        candidate.pack_forget()

    view.pack(expand=True)


# ============================================================
# WORKOUT ENTRY HELPERS
# ============================================================

def strip_entry(entry):
    """
    Drops the non-JSON-safe fields (module/color/hover/emoji)
    before an in-progress workout entry gets saved to disk.
    """

    return {
        "name": entry["name"],
        "target": entry["target"],
        "is_timed": entry["is_timed"],
        "achieved": entry["achieved"],
        "done": entry["done"]
    }


def persist_current_workout():

    if current_user_data is None:

        return

    if not current_workout:

        current_user_data["current_workout"] = None

    else:

        current_user_data["current_workout"] = {
            "date": user_data.today_string(),
            "type": current_workout_type,
            "goal_text": current_workout_goal_text,
            "heading": current_workout_heading,
            "exercises": [strip_entry(e) for e in current_workout]
        }

    user_data.save_user(current_user_data, current_user_filepath)


def archive_incomplete_current_workout():
    """
    If there's an unfinished AI workout in progress, logs it to
    history as incomplete before it gets replaced or discarded.
    """

    global current_workout

    if current_workout and not all(e["done"] for e in current_workout):

        user_data.archive_workout(current_user_data, {
            "date": user_data.today_string(),
            "type": current_workout_type,
            "goal_text": current_workout_goal_text,
            "completed": False,
            "exercises": [strip_entry(e) for e in current_workout]
        })

        user_data.save_user(current_user_data, current_user_filepath)

    current_workout = []


# ============================================================
# LOGIN
# ============================================================

def build_login_recent_users():

    for child in login_recent_frame.winfo_children():

        child.destroy()

    names = user_data.list_saved_usernames()

    if not names:

        return

    label = tk.Label(
        login_recent_frame,
        text="RECENT PLAYERS",
        font=("Arial", 10, "bold"),
        fg=TEXT_MUTED,
        bg=BG_DARK
    )

    label.pack(pady=(0, 6))

    row = tk.Frame(login_recent_frame, bg=BG_DARK)
    row.pack()

    for name in names[:8]:

        button = tk.Button(
            row,
            text=name,
            command=lambda n=name: quick_login(n),
            font=("Arial", 10, "bold"),
            bg=BG_PANEL,
            fg=TEXT_MAIN,
            activebackground=STEEL,
            width=14,
            height=1,
            border=0,
            relief="flat",
            cursor="hand2"
        )

        button.pack(side="left", padx=4, pady=4)

        add_hover(button, BG_PANEL, STEEL)


def quick_login(name):

    login_username_var.set(name)

    handle_login()


def handle_login():

    global current_username
    global current_user_data
    global current_user_filepath

    typed = login_username_var.get().strip()

    if not typed:

        login_error_label.config(
            text="Please enter a name."
        )

        return

    data, filepath = user_data.load_user(typed)

    current_username = data["username"]
    current_user_data = data
    current_user_filepath = filepath

    root.title(f"Iron Tracker - {current_username}")

    subtitle.config(
        text=f"WELCOME, {current_username.upper()}  \u2022  NO EXCUSES"
    )

    login_username_var.set("")
    login_error_label.config(text="")

    resume_or_reset_workout()


def confirm_switch_user():

    if messagebox.askyesno(
        "Switch User",
        "Log out and switch to a different player?"
    ):

        handle_logout()


def handle_logout():

    global current_username
    global current_user_data
    global current_user_filepath
    global current_workout

    current_username = None
    current_user_data = None
    current_user_filepath = None
    current_workout = []

    root.title("Iron Tracker")

    build_login_recent_users()

    show_view(login_view)


# ============================================================
# RESUME TODAY'S WORKOUT (IF ANY)
# ============================================================

def resume_or_reset_workout():

    global current_workout
    global current_workout_heading
    global current_workout_type
    global current_workout_goal_text

    saved = current_user_data.get("current_workout")

    today = user_data.today_string()

    current_workout = []
    current_workout_heading = "TODAY'S AI WORKOUT"
    current_workout_type = None
    current_workout_goal_text = None

    if not saved:

        show_view(menu_view)

        return

    if saved.get("date") != today:

        # Leftover from a previous day - log it (likely
        # incomplete) and start clean rather than resuming
        # something from yesterday.
        saved_exercises = saved.get("exercises", [])

        completed = bool(saved_exercises) and all(
            e["done"] for e in saved_exercises
        )

        user_data.archive_workout(current_user_data, {
            "date": saved.get("date"),
            "type": saved.get("type"),
            "goal_text": saved.get("goal_text"),
            "completed": completed,
            "exercises": saved_exercises
        })

        current_user_data["current_workout"] = None

        user_data.save_user(current_user_data, current_user_filepath)

        show_view(menu_view)

        return

    # Same-day save - rehydrate it with today's module/color/
    # emoji info and pick back up where it was left off.
    rehydrated = []

    for item in saved.get("exercises", []):

        config = EXERCISES_BY_NAME.get(item["name"])

        if config is None:

            continue

        rehydrated.append({
            "name": item["name"],
            "target": item["target"],
            "is_timed": item["is_timed"],
            "achieved": item["achieved"],
            "done": item["done"],
            "module": config["module"],
            "emoji": config["emoji"],
            "color": config["color"],
            "hover": config["hover"]
        })

    if rehydrated and all(entry["done"] for entry in rehydrated):

        # Already finished earlier today - nothing to resume.
        show_view(menu_view)

        return

    current_workout = rehydrated
    current_workout_heading = saved.get("heading", "TODAY'S AI WORKOUT")
    current_workout_type = saved.get("type")
    current_workout_goal_text = saved.get("goal_text")

    render_workout_view()

    show_view(workout_view)


# ============================================================
# START EXERCISE (FREE PLAY, FROM THE MAIN GRID)
# ============================================================

def start_exercise(module, exercise_name, is_timed):
    """
    Hide the main menu, launch the given exercise tracker
    module, log the attempt to lifetime totals, then restore
    the fullscreen menu when it closes.
    """

    root.withdraw()

    module.run()

    achieved = module.elapsed_seconds if is_timed else module.counter

    if current_user_data is not None:

        user_data.record_attempt(
            current_user_data,
            exercise_name,
            achieved,
            is_timed
        )

        user_data.save_user(current_user_data, current_user_filepath)

    if app_running:

        root.deiconify()

        force_fullscreen()


# ============================================================
# EXIT APPLICATION
# ============================================================

def exit_application():
    global app_running

    app_running = False

    root.destroy()


# ============================================================
# BUILD A NEW AI WORKOUT
# ============================================================

def start_new_workout(prescribed, heading, workout_type, goal_text=None):

    global current_workout
    global current_workout_heading
    global current_workout_type
    global current_workout_goal_text

    archive_incomplete_current_workout()

    current_workout = []

    for item in prescribed:

        config = EXERCISES_BY_NAME[item["name"]]

        current_workout.append({
            "name": item["name"],
            "target": item["target"],
            "is_timed": item["is_timed"],
            "module": config["module"],
            "emoji": config["emoji"],
            "color": config["color"],
            "hover": config["hover"],
            "achieved": 0,
            "done": False
        })

    current_workout_heading = heading
    current_workout_type = workout_type
    current_workout_goal_text = goal_text

    persist_current_workout()

    render_workout_view()

    show_view(workout_view)


def start_daily_ai_workout():

    prescribed = workout_ai.generate_daily_workout(EXERCISE_NAMES)

    start_new_workout(
        prescribed,
        "TODAY'S AI WORKOUT",
        "daily"
    )


def handle_goal_submit():

    text = goal_entry_var.get().strip()

    if not text:

        text = "full body"

    prescribed = workout_ai.generate_workout_from_goal(
        text,
        EXERCISE_NAMES
    )

    goal_entry_var.set("")

    start_new_workout(
        prescribed,
        f"YOUR WORKOUT: \u201C{text.upper()}\u201D",
        "goal",
        goal_text=text
    )


# ============================================================
# RUN ONE EXERCISE FROM THE AI DASHBOARD
# ============================================================

def start_workout_exercise(index):
    """
    Same as start_exercise(), but afterward reads the tracker
    module's final counter (or elapsed_seconds for plank) to
    check whether today's target was hit, logs the attempt to
    lifetime totals, and saves the workout's progress. If this
    was the last exercise needed to finish the workout, it gets
    archived to history and the HOORAY screen is shown instead
    of the dashboard.
    """

    entry = current_workout[index]

    root.withdraw()

    entry["module"].run()

    if entry["is_timed"]:

        achieved = entry["module"].elapsed_seconds

    else:

        achieved = entry["module"].counter

    entry["achieved"] = achieved

    if achieved >= entry["target"]:

        entry["done"] = True

    if current_user_data is not None:

        user_data.record_attempt(
            current_user_data,
            entry["name"],
            achieved,
            entry["is_timed"]
        )

    all_done = bool(current_workout) and all(
        e["done"] for e in current_workout
    )

    if current_user_data is not None:

        if all_done:

            user_data.archive_workout(current_user_data, {
                "date": user_data.today_string(),
                "type": current_workout_type,
                "goal_text": current_workout_goal_text,
                "completed": True,
                "exercises": [strip_entry(e) for e in current_workout]
            })

            current_user_data["current_workout"] = None

            user_data.save_user(current_user_data, current_user_filepath)

        else:

            persist_current_workout()

    if app_running:

        root.deiconify()

        force_fullscreen()

        if all_done:

            render_hooray_view()

            show_view(hooray_view)

        else:

            render_workout_view()

            show_view(workout_view)


# ============================================================
# WORKOUT DASHBOARD DISPLAY HELPERS
# ============================================================

def status_text_for(entry):

    if entry["done"]:

        return f"\u2705 {workout_ai.format_achieved(entry)}"

    if entry["achieved"]:

        return f"Last try: {workout_ai.format_achieved(entry)}"

    return "\u23F3 Not started"


def status_color_for(entry):

    if entry["done"]:

        return "#00E676"

    if entry["achieved"]:

        return "#FFB300"

    return TEXT_MUTED


def completion_text():

    if current_workout and all(
        entry["done"] for entry in current_workout
    ):

        return "\U0001F389 WORKOUT COMPLETE - GREAT JOB! \U0001F389"

    return ""


# ============================================================
# RENDER THE AI WORKOUT DASHBOARD
# ============================================================

def render_workout_view():
    """
    Rebuilds workout_view from scratch based on the current
    contents of current_workout. Called every time a workout is
    generated, resumed, or updated, so the dashboard always
    reflects the latest saved progress.
    """

    for child in workout_view.winfo_children():

        child.destroy()

    heading_label = tk.Label(
        workout_view,
        text=current_workout_heading,
        font=("Arial Black", 22, "bold"),
        fg=TEXT_MAIN,
        bg=BG_DARK,
        wraplength=800,
        justify="center"
    )

    heading_label.pack(pady=(0, 4))

    sub_label = tk.Label(
        workout_view,
        text="Hit every target below to finish today's workout",
        font=("Arial", 11),
        fg=TEXT_MUTED,
        bg=BG_DARK
    )

    sub_label.pack(pady=(0, 20))

    rows_frame = tk.Frame(workout_view, bg=BG_DARK)
    rows_frame.pack()

    for index, entry in enumerate(current_workout):

        row = tk.Frame(rows_frame, bg=BG_PANEL)

        row.grid(row=index, column=0, sticky="ew", pady=5)

        name_text = (
            f"{entry['emoji']}  {entry['name']}  \u2014  "
            f"{workout_ai.format_target(entry)}"
        )

        name_label = tk.Label(
            row,
            text=name_text,
            font=("Arial", 13, "bold"),
            fg=TEXT_MAIN,
            bg=BG_PANEL,
            width=38,
            anchor="w"
        )

        name_label.pack(side="left", padx=(15, 10), pady=12)

        status_label = tk.Label(
            row,
            text=status_text_for(entry),
            font=("Arial", 12, "bold"),
            fg=status_color_for(entry),
            bg=BG_PANEL,
            width=20,
            anchor="w"
        )

        status_label.pack(side="left", padx=10)

        button_text = "DONE" if entry["done"] else "START"
        button_color = DONE_COLOR if entry["done"] else entry["color"]
        button_hover = DONE_COLOR if entry["done"] else entry["hover"]

        start_button = tk.Button(
            row,
            text=button_text,
            command=lambda idx=index: start_workout_exercise(idx),
            font=("Arial", 11, "bold"),
            bg=button_color,
            fg=TEXT_MAIN,
            activebackground=button_hover,
            width=12,
            height=1,
            border=0,
            relief="flat",
            cursor="hand2",
            state=("disabled" if entry["done"] else "normal")
        )

        start_button.pack(side="right", padx=15, pady=12)

        if not entry["done"]:

            add_hover(start_button, button_color, button_hover)

    completion_banner = tk.Label(
        workout_view,
        text=completion_text(),
        font=("Arial", 16, "bold"),
        fg="#00E676",
        bg=BG_DARK
    )

    completion_banner.pack(pady=(20, 0))

    bottom_row = tk.Frame(workout_view, bg=BG_DARK)
    bottom_row.pack(pady=(20, 0))

    new_workout_button = tk.Button(
        bottom_row,
        text="NEW RANDOM WORKOUT",
        command=start_daily_ai_workout,
        font=("Arial", 12, "bold"),
        bg=AI_DAILY_COLOR,
        fg=TEXT_MAIN,
        activebackground=AI_DAILY_COLOR_HOVER,
        width=22,
        height=2,
        border=0,
        relief="flat",
        cursor="hand2"
    )

    new_workout_button.pack(side="left", padx=8)

    add_hover(new_workout_button, AI_DAILY_COLOR, AI_DAILY_COLOR_HOVER)

    back_button = tk.Button(
        bottom_row,
        text="BACK TO MENU",
        command=lambda: show_view(menu_view),
        font=("Arial", 12, "bold"),
        bg=STEEL,
        fg=TEXT_MAIN,
        activebackground="#2a2a2a",
        width=16,
        height=2,
        border=0,
        relief="flat",
        cursor="hand2"
    )

    back_button.pack(side="left", padx=8)

    add_hover(back_button, STEEL, "#2a2a2a")


# ============================================================
# RENDER THE HOORAY (WORKOUT COMPLETE) SCREEN
# ============================================================

def render_hooray_view():

    for child in hooray_view.winfo_children():

        child.destroy()

    banner = tk.Label(
        hooray_view,
        text="\U0001F389 HOORAY! \U0001F389",
        font=("Arial Black", 40, "bold"),
        fg="#00E676",
        bg=BG_DARK
    )

    banner.pack(pady=(0, 10))

    message = tk.Label(
        hooray_view,
        text="You completed today's workout!",
        font=("Arial", 16, "bold"),
        fg=TEXT_MAIN,
        bg=BG_DARK
    )

    message.pack(pady=(0, 25))

    summary_frame = tk.Frame(hooray_view, bg=BG_DARK)
    summary_frame.pack(pady=(0, 30))

    for entry in current_workout:

        line = tk.Label(
            summary_frame,
            text=(
                f"{entry['emoji']}  {entry['name']}  \u2014  "
                f"{workout_ai.format_achieved(entry)} / "
                f"{workout_ai.format_target(entry)}"
            ),
            font=("Arial", 12, "bold"),
            fg=TEXT_MAIN,
            bg=BG_DARK
        )

        line.pack(pady=2)

    back_button = tk.Button(
        hooray_view,
        text="BACK TO MENU",
        command=lambda: show_view(menu_view),
        font=("Arial", 13, "bold"),
        bg=ACCENT,
        fg=TEXT_MAIN,
        activebackground="#CC5500",
        width=22,
        height=2,
        border=0,
        relief="flat",
        cursor="hand2"
    )

    back_button.pack()

    add_hover(back_button, ACCENT, "#CC5500")


# ============================================================
# MUSCLE MAP
# ============================================================

def select_muscle_exercise(name):

    info = body_diagram.MUSCLE_INFO[name]

    body_diagram.highlight_regions(
        muscle_canvas,
        muscle_region_items,
        info["regions"]
    )

    muscle_info_label.config(
        text=f"{name}: {info['muscles']}"
    )


# ============================================================
# STATS SCREEN
# ============================================================

def render_stats_view():

    for child in stats_view.winfo_children():

        child.destroy()

    title_label = tk.Label(
        stats_view,
        text=f"{current_username}'S STATS" if current_username else "STATS",
        font=("Arial Black", 22, "bold"),
        fg=TEXT_MAIN,
        bg=BG_DARK
    )

    title_label.pack(pady=(0, 15))

    totals = current_user_data.get("totals", {}) if current_user_data else {}

    totals_frame = tk.Frame(stats_view, bg=BG_DARK)
    totals_frame.pack(pady=(0, 20))

    headers = ["EXERCISE", "SESSIONS", "TOTAL", "BEST"]

    for col, text in enumerate(headers):

        tk.Label(
            totals_frame,
            text=text,
            font=("Arial", 10, "bold"),
            fg=ACCENT,
            bg=BG_DARK,
            width=18
        ).grid(row=0, column=col, padx=4, pady=4)

    for row_index, exercise in enumerate(EXERCISES, start=1):

        name = exercise["name"]
        entry = totals.get(name)

        if not entry:

            sessions_display = "0"
            total_display = "-"
            best_display = "-"

        else:

            sessions_display = str(entry["sessions"])

            if exercise["is_timed"]:

                total_display = f"{int(entry['seconds'])}s"
                best_display = f"{int(entry['best'])}s"

            else:

                total_display = f"{entry['reps']} reps"
                best_display = f"{entry['best']} reps"

        tk.Label(
            totals_frame,
            text=f"{exercise['emoji']} {name}",
            font=("Arial", 10),
            fg=TEXT_MAIN,
            bg=BG_DARK,
            width=22,
            anchor="w"
        ).grid(row=row_index, column=0, padx=4, pady=2, sticky="w")

        tk.Label(
            totals_frame, text=sessions_display, font=("Arial", 10),
            fg=TEXT_MAIN, bg=BG_DARK, width=12
        ).grid(row=row_index, column=1, padx=4, pady=2)

        tk.Label(
            totals_frame, text=total_display, font=("Arial", 10),
            fg=TEXT_MAIN, bg=BG_DARK, width=14
        ).grid(row=row_index, column=2, padx=4, pady=2)

        tk.Label(
            totals_frame, text=best_display, font=("Arial", 10),
            fg=TEXT_MAIN, bg=BG_DARK, width=14
        ).grid(row=row_index, column=3, padx=4, pady=2)

    history_label = tk.Label(
        stats_view,
        text="RECENT WORKOUT HISTORY",
        font=("Arial", 13, "bold"),
        fg=ACCENT,
        bg=BG_DARK
    )

    history_label.pack(pady=(10, 5))

    history_list = tk.Listbox(
        stats_view,
        width=64,
        height=8,
        bg=BG_PANEL,
        fg=TEXT_MAIN,
        font=("Consolas", 10),
        relief="flat",
        highlightthickness=0,
        justify="center"
    )

    history_list.pack(pady=(0, 15))

    history = current_user_data.get("history", []) if current_user_data else []

    if not history:

        history_list.insert("end", "No workouts recorded yet - go crush one!")

    else:

        for record in reversed(history[-15:]):

            completed_mark = "\u2705" if record.get("completed") else "\u274C"

            if record.get("type") == "goal" and record.get("goal_text"):

                type_label = f'Goal: "{record["goal_text"]}"'

            elif record.get("type") == "daily":

                type_label = "Daily AI workout"

            else:

                type_label = "Workout"

            history_list.insert(
                "end",
                f"{record.get('date', '?')}  |  {type_label:<28}  |  {completed_mark}"
            )

    back_button = tk.Button(
        stats_view,
        text="BACK TO MENU",
        command=lambda: show_view(menu_view),
        font=("Arial", 13, "bold"),
        bg=STEEL,
        fg=TEXT_MAIN,
        activebackground="#2a2a2a",
        width=22,
        height=2,
        border=0,
        relief="flat",
        cursor="hand2"
    )

    back_button.pack(pady=(5, 0))

    add_hover(back_button, STEEL, "#2a2a2a")


# ============================================================
# MAIN WINDOW
# ============================================================

root = tk.Tk()

root.title("Iron Tracker")

root.configure(bg=BG_DARK)

# Fullscreen, borderless, and locked - stays fullscreen for the
# whole session instead of reverting to a normal window.
force_fullscreen()

root.resizable(False, False)

# Escape is bound as a safety valve so the app can still be
# closed cleanly without a mouse/window controls.
root.bind("<Escape>", lambda event: exit_application())


# ============================================================
# TOP / BOTTOM ACCENT BARS
# ============================================================

top_bar = tk.Frame(root, bg=ACCENT, height=8)
top_bar.pack(side="top", fill="x")

bottom_bar = tk.Frame(root, bg=ACCENT, height=8)
bottom_bar.pack(side="bottom", fill="x")


# ============================================================
# CENTERED CONTENT FRAME
# ============================================================
#
# Packed with expand=True so everything stays vertically
# centered no matter the screen resolution. Every screen is a
# child of this frame; show_view() swaps which one is visible.
#

content = tk.Frame(root, bg=BG_DARK)
content.pack(expand=True)

login_view = tk.Frame(content, bg=BG_DARK)
menu_view = tk.Frame(content, bg=BG_DARK)
goal_view = tk.Frame(content, bg=BG_DARK)
workout_view = tk.Frame(content, bg=BG_DARK)
hooray_view = tk.Frame(content, bg=BG_DARK)
muscle_view = tk.Frame(content, bg=BG_DARK)
stats_view = tk.Frame(content, bg=BG_DARK)


# ============================================================
# LOGIN VIEW
# ============================================================

login_kicker = tk.Label(
    login_view,
    text="\u25c6  T R A I N I N G   L O G  \u25c6",
    font=("Arial", 10, "bold"),
    fg=ACCENT,
    bg=BG_DARK
)

login_kicker.pack(pady=(0, 6))

login_title = tk.Label(
    login_view,
    text="IRON TRACKER",
    font=("Arial Black", 32, "bold"),
    fg=TEXT_MAIN,
    bg=BG_DARK
)

login_title.pack(pady=(0, 6))

login_subtitle = tk.Label(
    login_view,
    text="ENTER YOUR NAME TO BEGIN",
    font=("Arial", 12, "bold"),
    fg=TEXT_MUTED,
    bg=BG_DARK
)

login_subtitle.pack(pady=(0, 25))

login_username_var = tk.StringVar()

login_entry = tk.Entry(
    login_view,
    textvariable=login_username_var,
    font=("Arial", 14),
    width=30,
    bg=BG_PANEL,
    fg=TEXT_MAIN,
    insertbackground=TEXT_MAIN,
    relief="flat",
    justify="center"
)

login_entry.pack(ipady=8, pady=(0, 10))

login_entry.bind("<Return>", lambda event: handle_login())

login_error_label = tk.Label(
    login_view,
    text="",
    font=("Arial", 10, "bold"),
    fg="#FF5252",
    bg=BG_DARK
)

login_error_label.pack(pady=(0, 15))

login_button = tk.Button(
    login_view,
    text="LET'S GO",
    command=handle_login,
    font=("Arial", 14, "bold"),
    bg=ACCENT,
    fg=TEXT_MAIN,
    activebackground="#CC5500",
    width=22,
    height=2,
    border=0,
    relief="flat",
    cursor="hand2"
)

login_button.pack(pady=(0, 25))
add_hover(login_button, ACCENT, "#CC5500")

login_recent_frame = tk.Frame(login_view, bg=BG_DARK)
login_recent_frame.pack()


# ============================================================
# MENU VIEW - KICKER / TITLE / SUBTITLE
# ============================================================

kicker = tk.Label(
    menu_view,
    text="\u25c6  T R A I N I N G   L O G  \u25c6",
    font=("Arial", 10, "bold"),
    fg=ACCENT,
    bg=BG_DARK
)

kicker.pack(pady=(0, 6))

title = tk.Label(
    menu_view,
    text="IRON TRACKER",
    font=("Arial Black", 32, "bold"),
    fg=TEXT_MAIN,
    bg=BG_DARK
)

title.pack(pady=(0, 6))

subtitle = tk.Label(
    menu_view,
    text="CHOOSE YOUR WORKOUT  \u2022  NO EXCUSES",
    font=("Arial", 12, "bold"),
    fg=TEXT_MUTED,
    bg=BG_DARK
)

subtitle.pack(pady=(0, 20))


# ============================================================
# MENU VIEW - AI BUTTONS
# ============================================================

ai_row = tk.Frame(menu_view, bg=BG_DARK)
ai_row.pack(pady=(0, 15))

daily_ai_button = tk.Button(
    ai_row,
    text="\U0001F916  AI DAILY WORKOUT",
    command=start_daily_ai_workout,
    font=("Arial", 13, "bold"),
    bg=AI_DAILY_COLOR,
    fg=TEXT_MAIN,
    activebackground=AI_DAILY_COLOR_HOVER,
    width=22,
    height=2,
    border=0,
    relief="flat",
    cursor="hand2"
)

daily_ai_button.pack(side="left", padx=8)
add_hover(daily_ai_button, AI_DAILY_COLOR, AI_DAILY_COLOR_HOVER)

goal_ai_button = tk.Button(
    ai_row,
    text="\U0001F9E0  DESCRIBE A GOAL",
    command=lambda: show_view(goal_view),
    font=("Arial", 13, "bold"),
    bg=AI_GOAL_COLOR,
    fg=TEXT_MAIN,
    activebackground=AI_GOAL_COLOR_HOVER,
    width=22,
    height=2,
    border=0,
    relief="flat",
    cursor="hand2"
)

goal_ai_button.pack(side="left", padx=8)
add_hover(goal_ai_button, AI_GOAL_COLOR, AI_GOAL_COLOR_HOVER)


# ============================================================
# MENU VIEW - TOOLS ROW (MUSCLE MAP / STATS)
# ============================================================

tools_row = tk.Frame(menu_view, bg=BG_DARK)
tools_row.pack(pady=(0, 20))

muscle_map_button = tk.Button(
    tools_row,
    text="\U0001F9CD  MUSCLE MAP",
    command=lambda: show_view(muscle_view),
    font=("Arial", 13, "bold"),
    bg=STEEL,
    fg=TEXT_MAIN,
    activebackground="#2a2a2a",
    width=22,
    height=2,
    border=0,
    relief="flat",
    cursor="hand2"
)

muscle_map_button.pack(side="left", padx=8)
add_hover(muscle_map_button, STEEL, "#2a2a2a")

stats_button = tk.Button(
    tools_row,
    text="\U0001F4CA  MY STATS",
    command=lambda: (render_stats_view(), show_view(stats_view)),
    font=("Arial", 13, "bold"),
    bg=STEEL,
    fg=TEXT_MAIN,
    activebackground="#2a2a2a",
    width=22,
    height=2,
    border=0,
    relief="flat",
    cursor="hand2"
)

stats_button.pack(side="left", padx=8)
add_hover(stats_button, STEEL, "#2a2a2a")


# ============================================================
# MENU VIEW - DIVIDER
# ============================================================

divider = tk.Frame(menu_view, bg=STEEL, height=2, width=460)
divider.pack(pady=(0, 25))


# ============================================================
# MENU VIEW - FREE-PLAY BUTTON GRID (TWO COLUMNS)
# ============================================================

button_panel = tk.Frame(menu_view, bg=BG_DARK)
button_panel.pack()

for index, exercise in enumerate(EXERCISES):

    row = index // 2
    column = index % 2

    button = tk.Button(
        button_panel,
        text=f"{exercise['emoji']}  {exercise['name']}",
        # Default-argument trick avoids every button sharing the
        # LAST loop value - a classic closure-in-a-loop bug.
        command=lambda module=exercise["module"],
        name=exercise["name"],
        timed=exercise["is_timed"]: start_exercise(module, name, timed),
        font=("Arial", 14, "bold"),
        bg=exercise["color"],
        fg=TEXT_MAIN,
        activebackground=exercise["hover"],
        activeforeground=TEXT_MAIN,
        width=20,
        height=2,
        border=0,
        relief="flat",
        cursor="hand2"
    )

    button.grid(row=row, column=column, padx=10, pady=8)

    add_hover(button, exercise["color"], exercise["hover"])


# ============================================================
# MENU VIEW - SWITCH USER / EXIT ROW
# ============================================================

bottom_button_row = (len(EXERCISES) + 1) // 2

switch_user_button = tk.Button(
    button_panel,
    text="SWITCH USER",
    command=confirm_switch_user,
    font=("Arial", 13, "bold"),
    bg=STEEL,
    fg=TEXT_MAIN,
    activebackground="#2a2a2a",
    width=20,
    height=1,
    border=0,
    relief="flat",
    cursor="hand2"
)

switch_user_button.grid(row=bottom_button_row, column=0, padx=6, pady=(20, 0))
add_hover(switch_user_button, STEEL, "#2a2a2a")

exit_button = tk.Button(
    button_panel,
    text="EXIT",
    command=exit_application,
    font=("Arial", 13, "bold"),
    bg=EXIT_COLOR,
    fg=TEXT_MAIN,
    activebackground=EXIT_COLOR_HOVER,
    activeforeground=TEXT_MAIN,
    width=20,
    height=1,
    border=0,
    relief="flat",
    cursor="hand2"
)

exit_button.grid(row=bottom_button_row, column=1, padx=6, pady=(20, 0))
add_hover(exit_button, EXIT_COLOR, EXIT_COLOR_HOVER)


# ============================================================
# MENU VIEW - FOOTER
# ============================================================

footer = tk.Label(
    menu_view,
    text="STAY CONSISTENT  \u2022  STAY STRONG",
    font=("Arial", 9, "bold"),
    fg=STEEL,
    bg=BG_DARK
)

footer.pack(pady=(25, 0))


# ============================================================
# GOAL VIEW - "DESCRIBE A GOAL" SCREEN
# ============================================================

goal_title = tk.Label(
    goal_view,
    text="DESCRIBE YOUR GOAL",
    font=("Arial Black", 26, "bold"),
    fg=TEXT_MAIN,
    bg=BG_DARK
)

goal_title.pack(pady=(0, 10))

goal_hint = tk.Label(
    goal_view,
    text='e.g. "arms and core", "cardio", "leg day", "full body"',
    font=("Arial", 11),
    fg=TEXT_MUTED,
    bg=BG_DARK
)

goal_hint.pack(pady=(0, 20))

goal_entry_var = tk.StringVar()

goal_entry = tk.Entry(
    goal_view,
    textvariable=goal_entry_var,
    font=("Arial", 14),
    width=36,
    bg=BG_PANEL,
    fg=TEXT_MAIN,
    insertbackground=TEXT_MAIN,
    relief="flat",
    justify="center"
)

goal_entry.pack(ipady=8, pady=(0, 25))

goal_entry.bind("<Return>", lambda event: handle_goal_submit())

goal_buttons_row = tk.Frame(goal_view, bg=BG_DARK)
goal_buttons_row.pack()

generate_button = tk.Button(
    goal_buttons_row,
    text="GENERATE WORKOUT",
    command=handle_goal_submit,
    font=("Arial", 13, "bold"),
    bg=ACCENT,
    fg=TEXT_MAIN,
    activebackground="#CC5500",
    width=22,
    height=2,
    border=0,
    relief="flat",
    cursor="hand2"
)

generate_button.pack(side="left", padx=8)
add_hover(generate_button, ACCENT, "#CC5500")

back_from_goal_button = tk.Button(
    goal_buttons_row,
    text="BACK",
    command=lambda: show_view(menu_view),
    font=("Arial", 13, "bold"),
    bg=STEEL,
    fg=TEXT_MAIN,
    activebackground="#2a2a2a",
    width=16,
    height=2,
    border=0,
    relief="flat",
    cursor="hand2"
)

back_from_goal_button.pack(side="left", padx=8)
add_hover(back_from_goal_button, STEEL, "#2a2a2a")


# ============================================================
# MUSCLE VIEW - MUSCLE MAP SCREEN
# ============================================================

muscle_title = tk.Label(
    muscle_view,
    text="MUSCLE MAP",
    font=("Arial Black", 24, "bold"),
    fg=TEXT_MAIN,
    bg=BG_DARK
)

muscle_title.pack(pady=(0, 15))

muscle_body_frame = tk.Frame(muscle_view, bg=BG_DARK)
muscle_body_frame.pack()

muscle_list_frame = tk.Frame(muscle_body_frame, bg=BG_DARK)
muscle_list_frame.pack(side="left", padx=(0, 30), anchor="n")

muscle_canvas = tk.Canvas(
    muscle_body_frame,
    width=300,
    height=350,
    bg=BG_DARK,
    highlightthickness=0
)

muscle_canvas.pack(side="left")

muscle_region_items = body_diagram.draw_body(muscle_canvas)

for exercise in EXERCISES:

    muscle_button = tk.Button(
        muscle_list_frame,
        text=f"{exercise['emoji']} {exercise['name']}",
        command=lambda n=exercise["name"]: select_muscle_exercise(n),
        font=("Arial", 11, "bold"),
        bg=exercise["color"],
        fg=TEXT_MAIN,
        activebackground=exercise["hover"],
        width=20,
        height=1,
        border=0,
        relief="flat",
        cursor="hand2"
    )

    muscle_button.pack(pady=3)

    add_hover(muscle_button, exercise["color"], exercise["hover"])

muscle_info_label = tk.Label(
    muscle_view,
    text="Select an exercise to see the muscles it targets",
    font=("Arial", 12, "bold"),
    fg=TEXT_MUTED,
    bg=BG_DARK,
    wraplength=550,
    justify="center"
)

muscle_info_label.pack(pady=(15, 15))

muscle_back_button = tk.Button(
    muscle_view,
    text="BACK TO MENU",
    command=lambda: show_view(menu_view),
    font=("Arial", 13, "bold"),
    bg=STEEL,
    fg=TEXT_MAIN,
    activebackground="#2a2a2a",
    width=22,
    height=2,
    border=0,
    relief="flat",
    cursor="hand2"
)

muscle_back_button.pack()
add_hover(muscle_back_button, STEEL, "#2a2a2a")


# ============================================================
# START APPLICATION
# ============================================================

build_login_recent_users()

show_view(login_view)

root.mainloop()
