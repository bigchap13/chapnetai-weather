def donation_opportunity_score(record):
    score = 50

    if "Dealership" in record.get("organization", ""):
        score += 20

    if record.get("contact_status") == "identified":
        score += 10

    return min(score, 100)
