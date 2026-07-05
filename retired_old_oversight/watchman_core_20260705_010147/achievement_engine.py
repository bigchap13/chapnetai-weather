from .jj_badges import earned_badges

def achievement_summary(resident):
    badges = earned_badges(resident)

    return {
        "sol_id": resident.get("sol_id"),
        "badges_earned": len(badges),
        "badges": badges
    }
