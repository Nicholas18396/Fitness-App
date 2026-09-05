# ============================================================
# MUSCLE INFO
# ============================================================
#
# Each exercise maps to:
#   - "regions": which zones of the body diagram light up
#     (a subset of "head", "shoulders", "chest", "arms",
#     "core", "legs")
#   - "muscles": a human-readable list of the actual muscles
#     it trains, shown as text under the diagram
#
# Names match the "name" field used throughout main.py and
# workout_ai.py exactly.
#

MUSCLE_INFO = {
    "PUSHUPS": {
        "regions": {"chest", "shoulders", "arms"},
        "muscles": "Chest, Shoulders, Triceps"
    },
    "SIT-UPS": {
        "regions": {"core"},
        "muscles": "Abdominals"
    },
    "SQUATS": {
        "regions": {"legs"},
        "muscles": "Quadriceps, Glutes, Hamstrings"
    },
    "LUNGES": {
        "regions": {"legs"},
        "muscles": "Quadriceps, Glutes, Hamstrings"
    },
    "JUMPING JACKS": {
        "regions": {"shoulders", "arms", "legs"},
        "muscles": "Full Body, Shoulders, Calves"
    },
    "BICEP CURLS": {
        "regions": {"arms"},
        "muscles": "Biceps"
    },
    "SHOULDER PRESS": {
        "regions": {"shoulders", "arms"},
        "muscles": "Shoulders, Triceps"
    },
    "HIGH KNEES": {
        "regions": {"legs", "core"},
        "muscles": "Hip Flexors, Core, Calves"
    },
    "MOUNTAIN CLIMBERS": {
        "regions": {"core", "shoulders", "legs"},
        "muscles": "Core, Shoulders, Hip Flexors"
    },
    "PLANK": {
        "regions": {"core", "shoulders"},
        "muscles": "Core, Shoulders (stabilizers)"
    },
}


# ============================================================
# DIAGRAM COLORS
# ============================================================

INACTIVE_COLOR = "#3a3a3a"
ACTIVE_COLOR = "#FF6B00"
OUTLINE_COLOR = "#F5F5F5"


# ============================================================
# DRAW BODY
# ============================================================
#
# Draws a simple front-facing humanoid figure on the given
# canvas and returns a dict mapping region name -> list of
# canvas item ids, so highlight_regions() can recolor regions
# later without redrawing the whole figure.
#
# No tkinter import here on purpose - this only calls methods
# (create_oval, create_rectangle, itemconfig) on whatever
# canvas-like object it's given, so the drawing logic itself
# can be unit tested with a plain mock object.
#

def draw_body(canvas):

    canvas.delete("all")

    regions = {
        "head": [],
        "shoulders": [],
        "chest": [],
        "arms": [],
        "core": [],
        "legs": [],
    }

    # ------------------------------------------------
    # HEAD
    # ------------------------------------------------

    head = canvas.create_oval(
        110, 10, 190, 80,
        fill=INACTIVE_COLOR,
        outline=OUTLINE_COLOR,
        width=2
    )

    regions["head"].append(head)

    # ------------------------------------------------
    # SHOULDERS
    # ------------------------------------------------

    left_shoulder = canvas.create_oval(
        60, 78, 108, 116,
        fill=INACTIVE_COLOR,
        outline=OUTLINE_COLOR,
        width=2
    )

    right_shoulder = canvas.create_oval(
        192, 78, 240, 116,
        fill=INACTIVE_COLOR,
        outline=OUTLINE_COLOR,
        width=2
    )

    regions["shoulders"] += [left_shoulder, right_shoulder]

    # ------------------------------------------------
    # CHEST (upper torso)
    # ------------------------------------------------

    chest = canvas.create_rectangle(
        102, 85, 198, 155,
        fill=INACTIVE_COLOR,
        outline=OUTLINE_COLOR,
        width=2
    )

    regions["chest"].append(chest)

    # ------------------------------------------------
    # CORE (lower torso)
    # ------------------------------------------------

    core = canvas.create_rectangle(
        107, 155, 193, 222,
        fill=INACTIVE_COLOR,
        outline=OUTLINE_COLOR,
        width=2
    )

    regions["core"].append(core)

    # ------------------------------------------------
    # ARMS
    # ------------------------------------------------

    left_arm = canvas.create_rectangle(
        58, 116, 96, 232,
        fill=INACTIVE_COLOR,
        outline=OUTLINE_COLOR,
        width=2
    )

    right_arm = canvas.create_rectangle(
        204, 116, 242, 232,
        fill=INACTIVE_COLOR,
        outline=OUTLINE_COLOR,
        width=2
    )

    regions["arms"] += [left_arm, right_arm]

    # ------------------------------------------------
    # LEGS
    # ------------------------------------------------

    left_leg = canvas.create_rectangle(
        109, 222, 146, 350,
        fill=INACTIVE_COLOR,
        outline=OUTLINE_COLOR,
        width=2
    )

    right_leg = canvas.create_rectangle(
        154, 222, 191, 350,
        fill=INACTIVE_COLOR,
        outline=OUTLINE_COLOR,
        width=2
    )

    regions["legs"] += [left_leg, right_leg]

    return regions


# ============================================================
# HIGHLIGHT REGIONS
# ============================================================
#
# Recolors every body part according to whether its region is
# in active_regions. The head is never highlighted - none of
# these exercises target it, so it always stays neutral.
#

def highlight_regions(canvas, region_items, active_regions):

    for region_name, item_ids in region_items.items():

        if region_name == "head":

            color = INACTIVE_COLOR

        elif region_name in active_regions:

            color = ACTIVE_COLOR

        else:

            color = INACTIVE_COLOR

        for item_id in item_ids:

            canvas.itemconfig(item_id, fill=color)
