LEVELS = {
    1: "Stabilization",
    2: "Accountability",
    3: "Employment",
    4: "Independence",
    5: "Graduate",
    6: "Mentor"
}

def level_name(level):
    return LEVELS.get(level, "Unknown")
