from .employer_partner_registry import employer_partner_registry
from .hiring_activity import sample_hiring_activity

def employer_scorecard():
    employers = employer_partner_registry()
    activity = sample_hiring_activity()

    scorecards = []

    for employer in employers:
        employer_id = employer["employer_id"]
        related = [a for a in activity if a["employer_id"] == employer_id]

        applications = sum(a["applications_sent"] for a in related)
        interviews = sum(a["interviews_generated"] for a in related)
        offers = sum(a["offers_generated"] for a in related)
        hires = sum(a["hires_generated"] for a in related)

        scorecards.append({
            "employer_id": employer_id,
            "name": employer["name"],
            "industry": employer["industry"],
            "status": employer["status"],
            "open_positions": employer["open_positions"],
            "applications_sent": applications,
            "interviews_generated": interviews,
            "offers_generated": offers,
            "hires_generated": hires,
            "retained_30_days": employer["retained_30_days"]
        })

    return scorecards
