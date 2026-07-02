def graduation_readiness(resident):
    score = resident.get("readiness_score", 0)
    employed = resident.get("employment_status") == "Employed"
    meetings = resident.get("meetings", 0)
    savings = resident.get("savings", 0)

    ready = score >= 80 and employed and meetings >= 25 and savings >= 500

    return {
        "sol_id": resident.get("sol_id"),
        "graduation_ready": ready,
        "requirements": {
            "readiness_score_80": score >= 80,
            "employed": employed,
            "meetings_25": meetings >= 25,
            "savings_500": savings >= 500
        }
    }
