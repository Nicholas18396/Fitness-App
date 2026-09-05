import random


# ============================================================
# EXERCISE CATEGORIES
# ============================================================
#
# Each exercise is tagged with the muscle groups / training
# styles it hits. Used to match a written goal ("arms and
# core") to the exercises that actually train that goal.
#

EXERCISE_CATEGORIES = {
    "PUSHUPS": {"upper", "push", "chest", "arms", "triceps"},
    "SIT-UPS": {"core", "abs"},
    "SQUATS": {"lower", "legs", "quads", "glutes"},
    "LUNGES": {"lower", "legs", "quads", "glutes", "balance"},
    "JUMPING JACKS": {"cardio", "full body", "warmup"},
    "BICEP CURLS": {"upper", "arms", "biceps", "pull"},
    "SHOULDER PRESS": {"upper", "arms", "shoulders", "push"},
    "HIGH KNEES": {"cardio", "legs", "core"},
    "MOUNTAIN CLIMBERS": {"cardio", "core", "full body"},
    "PLANK": {"core", "abs", "hold"},
}


# ============================================================
# KEYWORD -> CATEGORY MAP
# ============================================================
#
# Free-text goal descriptions are scanned for every one of
# these keywords (substring match). Both singular and plural
# forms are listed since a goal like "toned arm" should match
# just as well as "toned arms".
#

KEYWORD_CATEGORIES = [
    ("full body", {"full body"}),
    ("total body", {"full body"}),
    ("everything", {"full body"}),
    ("biceps", {"biceps"}),
    ("bicep", {"biceps"}),
    ("triceps", {"triceps"}),
    ("tricep", {"triceps"}),
    ("chest", {"chest"}),
    ("shoulders", {"shoulders"}),
    ("shoulder", {"shoulders"}),
    ("arms", {"arms"}),
    ("arm", {"arms"}),
    ("push", {"push"}),
    ("pull", {"pull"}),
    ("abs", {"abs", "core"}),
    ("stomach", {"abs", "core"}),
    ("belly", {"abs", "core"}),
    ("waist", {"abs", "core"}),
    ("obliques", {"abs", "core"}),
    ("oblique", {"abs", "core"}),
    ("core", {"core", "abs"}),
    ("glutes", {"glutes"}),
    ("glute", {"glutes"}),
    ("quads", {"quads"}),
    ("quad", {"quads"}),
    ("hamstrings", {"legs"}),
    ("hamstring", {"legs"}),
    ("calves", {"legs"}),
    ("calf", {"legs"}),
    ("legs", {"legs"}),
    ("leg", {"legs"}),
    ("lower body", {"lower"}),
    ("upper body", {"upper"}),
    ("cardio", {"cardio"}),
    ("conditioning", {"cardio"}),
    ("endurance", {"cardio", "hold"}),
    ("warm up", {"warmup", "cardio"}),
    ("warmup", {"warmup", "cardio"}),
    ("lose weight", {"cardio"}),
    ("weight loss", {"cardio"}),
    ("fat loss", {"cardio"}),
    ("burn fat", {"cardio"}),
    ("balance", {"balance"}),
    ("stability", {"core", "hold", "balance"}),
]


# ============================================================
# REP / TIME TARGET RANGES
# ============================================================
#
# (low, high) inclusive. PLANK's range is measured in seconds;
# every other exercise's range is measured in reps.
#

TARGET_RANGES = {
    "PUSHUPS": (8, 20),
    "SIT-UPS": (10, 25),
    "SQUATS": (10, 20),
    "LUNGES": (10, 20),
    "JUMPING JACKS": (15, 30),
    "BICEP CURLS": (8, 15),
    "SHOULDER PRESS": (8, 15),
    "HIGH KNEES": (20, 40),
    "MOUNTAIN CLIMBERS": (20, 40),
    "PLANK": (20, 60),
}

TIMED_EXERCISES = {"PLANK"}


# ============================================================
# TARGET ROUNDING
# ============================================================

def _round_target(name, value):

    if name in TIMED_EXERCISES:

        rounded = int(round(value / 5.0)) * 5

        return max(15, rounded)

    return max(5, int(round(value)))


# ============================================================
# DISPLAY HELPERS
# ============================================================

def format_target(entry):
    """
    "15 reps" for rep-based exercises, "30s hold" for timed
    ones (currently just PLANK).
    """

    if entry["is_timed"]:

        return f"{entry['target']}s hold"

    return f"{entry['target']} reps"


def format_achieved(entry):
    """
    Same idea as format_target(), but for the value the user
    actually reached on their last attempt.
    """

    achieved = entry.get("achieved", 0)

    if entry["is_timed"]:

        return f"{int(achieved)}s"

    return f"{int(achieved)} reps"


# ============================================================
# DAILY RANDOM WORKOUT
# ============================================================

def generate_daily_workout(
    exercise_names,
    count=5,
    rng=None
):
    """
    Picks `count` random exercises from exercise_names and
    assigns each a random target within its normal range.
    Returns a list of dicts: {"name", "target", "is_timed"}.
    """

    rng = rng or random

    count = min(
        count,
        len(exercise_names)
    )

    chosen = rng.sample(
        exercise_names,
        count
    )

    workout = []

    for name in chosen:

        low, high = TARGET_RANGES.get(
            name,
            (10, 15)
        )

        raw_target = rng.uniform(
            low,
            high
        )

        workout.append({
            "name": name,
            "target": _round_target(name, raw_target),
            "is_timed": name in TIMED_EXERCISES
        })

    return workout


# ============================================================
# GOAL MATCHING
# ============================================================

def match_categories(goal_text):
    """
    Scans free text for known keywords and returns the union
    of every matched category.
    """

    text = goal_text.lower()

    matched = set()

    for keyword, categories in KEYWORD_CATEGORIES:

        if keyword in text:

            matched |= categories

    return matched


# ============================================================
# GOAL-BASED WORKOUT
# ============================================================

def generate_workout_from_goal(
    goal_text,
    exercise_names,
    count=5,
    rng=None
):
    """
    Matches a free-text goal to exercise categories, ranks
    every exercise by how many categories it shares with the
    goal, and fills the workout with the best matches first -
    topping up with other exercises if not enough matched.

    Exercises that strongly match the goal get pushed toward
    the tougher end of their normal target range; exercises
    included only to fill out the workout get the easier end.

    Falls back to generate_daily_workout() if no keyword in
    the goal text is recognized at all.
    """

    rng = rng or random

    count = min(
        count,
        len(exercise_names)
    )

    matched_categories = match_categories(goal_text)

    if not matched_categories:

        return generate_daily_workout(
            exercise_names,
            count=count,
            rng=rng
        )

    scored = []

    for name in exercise_names:

        overlap = len(
            EXERCISE_CATEGORIES.get(name, set())
            & matched_categories
        )

        scored.append([overlap, name])

    # Shuffle first so exercises tied on score come out in a
    # different order each time, then do a stable sort by
    # score so the shuffle order survives within each tier.
    rng.shuffle(scored)

    scored.sort(
        key=lambda pair: pair[0],
        reverse=True
    )

    top_picks = scored[:count]

    workout = []

    for overlap, name in top_picks:

        low, high = TARGET_RANGES.get(
            name,
            (10, 15)
        )

        midpoint = low + (high - low) * 0.5

        if overlap >= 2:

            raw_target = rng.uniform(midpoint, high)

        elif overlap == 1:

            raw_target = rng.uniform(low, high)

        else:

            raw_target = rng.uniform(low, midpoint)

        workout.append({
            "name": name,
            "target": _round_target(name, raw_target),
            "is_timed": name in TIMED_EXERCISES
        })

    return workout
