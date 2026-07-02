from .community_partner_registry import community_partner_registry

def partner_scorecard():
    partners = community_partner_registry()

    scorecards = []

    for p in partners:
        score = 50

        if p.get("priority") == "high":
            score += 25

        if p.get("status") == "active":
            score += 25

        scorecards.append({
            "partner_id": p["partner_id"],
            "name": p["name"],
            "category": p["category"],
            "status": p["status"],
            "priority": p["priority"],
            "score": min(score, 100)
        })

    return scorecards
