def earned_badges(resident):
    badges = []

    if resident.get("stage"):
        badges.append("🥉 Intake")

    if resident.get("stage") in ["Assessment", "Accountability Plan", "Employment", "Stability", "Independence", "Graduate"]:
        badges.append("📋 Assessment")

    if resident.get("stage") in ["Accountability Plan", "Employment", "Stability", "Independence", "Graduate"]:
        badges.append("🛡 Accountability")

    if resident.get("employment_status") == "Employed":
        badges.append("💼 Employment")

    meetings = resident.get("meetings", 0)

    if meetings >= 10:
        badges.append("🎯 10 Meetings")
    if meetings >= 25:
        badges.append("🎯 25 Meetings")
    if meetings >= 50:
        badges.append("🎯 50 Meetings")
    if meetings >= 100:
        badges.append("🎯 100 Meetings")

    savings = resident.get("savings", 0)

    if savings >= 100:
        badges.append("💵 $100 Saved")
    if savings >= 500:
        badges.append("💵 $500 Saved")
    if savings >= 1000:
        badges.append("💵 $1000 Saved")

    if resident.get("stage") == "Graduate":
        badges.append("🎓 Graduate")

    return badges

def next_badge(resident):
    meetings = resident.get("meetings", 0)

    if meetings < 10:
        return f"🎯 10 Meetings ({meetings}/10)"
    if meetings < 25:
        return f"🎯 25 Meetings ({meetings}/25)"
    if resident.get("employment_status") != "Employed":
        return "💼 Employment"
    if resident.get("savings", 0) < 500:
        return f"💵 $500 Saved (${resident.get('savings',0)}/500)"
    return "🎓 Graduation"
