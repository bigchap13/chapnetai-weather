def score_grant(grant):
    score = 50

    if grant.get("fit") == "high":
        score += 30

    if grant.get("category") in ["Transportation", "Employment"]:
        score += 10

    if grant.get("status") == "prospect":
        score += 5

    return min(score, 100)
