import json
import os
import re

from datetime import date


# ============================================================
# SAVE LOCATION
# ============================================================
#
# Save files live in a "save_data" folder next to this script,
# not the current working directory, so the app finds its data
# the same way no matter where it's launched from.
#

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(SCRIPT_DIR, "save_data")


# ============================================================
# USERNAME HANDLING
# ============================================================

def sanitize_username(username):
    """
    Turns a typed username into a safe, unique filename: lower
    -cased, spaces collapsed to underscores, anything that
    isn't a letter/digit/underscore/hyphen stripped out.
    """

    cleaned = username.strip().lower()

    cleaned = re.sub(r"\s+", "_", cleaned)

    cleaned = re.sub(r"[^a-z0-9_\-]", "", cleaned)

    return cleaned or "player"


def user_filepath(username):

    safe_name = sanitize_username(username)

    return os.path.join(SAVE_DIR, f"{safe_name}.json")


def list_saved_usernames():
    """
    Returns the display username stored inside every save file
    under SAVE_DIR - used to show a "recent players" quick-pick
    list on the login screen.
    """

    if not os.path.isdir(SAVE_DIR):

        return []

    names = []

    for filename in sorted(os.listdir(SAVE_DIR)):

        if not filename.endswith(".json"):

            continue

        filepath = os.path.join(SAVE_DIR, filename)

        try:

            with open(filepath, "r", encoding="utf-8") as handle:

                data = json.load(handle)

            names.append(
                data.get("username", filename[:-5])
            )

        except (json.JSONDecodeError, OSError):

            continue

    return names


# ============================================================
# DEFAULT DATA
# ============================================================

def default_user_data(display_username):

    return {
        "username": display_username,
        "totals": {},
        "history": [],
        "current_workout": None
    }


# ============================================================
# LOAD / SAVE
# ============================================================

def load_user(display_username):
    """
    Returns (data, filepath) for this user, creating a fresh
    save file if none exists yet. A corrupted save file is
    backed up (renamed with a .corrupt suffix) and replaced
    with a fresh one instead of crashing the app.
    """

    os.makedirs(SAVE_DIR, exist_ok=True)

    filepath = user_filepath(display_username)

    if not os.path.exists(filepath):

        data = default_user_data(
            display_username.strip()
        )

        save_user(data, filepath)

        return data, filepath

    try:

        with open(filepath, "r", encoding="utf-8") as handle:

            data = json.load(handle)

    except (json.JSONDecodeError, OSError):

        backup_path = filepath + ".corrupt"

        try:

            os.replace(filepath, backup_path)

        except OSError:

            pass

        data = default_user_data(
            display_username.strip()
        )

        save_user(data, filepath)

        return data, filepath

    data.setdefault("username", display_username.strip())
    data.setdefault("totals", {})
    data.setdefault("history", [])
    data.setdefault("current_workout", None)

    return data, filepath


def save_user(data, filepath):

    os.makedirs(
        os.path.dirname(filepath),
        exist_ok=True
    )

    with open(filepath, "w", encoding="utf-8") as handle:

        json.dump(data, handle, indent=2)


# ============================================================
# LIFETIME TOTALS
# ============================================================

def record_attempt(data, exercise_name, achieved, is_timed):
    """
    Adds one completed attempt to the user's lifetime totals
    for this exercise - called for EVERY attempt, whether it
    came from free play or an AI-prescribed workout. Attempts
    of 0 (opened the tracker and immediately backed out) are
    not counted, so idle clicks don't inflate the stats.
    """

    if achieved <= 0:

        return

    totals = data.setdefault("totals", {})

    entry = totals.setdefault(
        exercise_name,
        {"sessions": 0, "reps": 0, "seconds": 0, "best": 0}
    )

    entry["sessions"] += 1

    if is_timed:

        entry["seconds"] += achieved

    else:

        entry["reps"] += achieved

    entry["best"] = max(entry["best"], achieved)


# ============================================================
# WORKOUT HISTORY
# ============================================================

def archive_workout(data, record):
    """
    Appends a finished (or abandoned) AI-prescribed workout to
    the user's permanent history log. `record` is expected to
    have: date, type ("daily"/"goal"), goal_text (or None),
    completed (bool), and exercises (a plain, JSON-safe list).
    """

    history = data.setdefault("history", [])

    history.append(record)


def today_string():

    return date.today().isoformat()
