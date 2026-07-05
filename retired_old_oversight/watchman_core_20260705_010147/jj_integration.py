def sample_residents():
    return [
        {
            "sol_id": "JJ-0001",
            "track": "Six-Month",
            "stage": "Accountability Plan",
            "readiness_score": 72,
            "meetings": 18,
            "savings": 125,
            "employment_status": "Seeking Work",
            "transportation_requests": 1,
            "wellness": "stable"
        },
        {
            "sol_id": "JJ-0002",
            "track": "One-Year",
            "stage": "Employment",
            "readiness_score": 84,
            "meetings": 42,
            "savings": 525,
            "employment_status": "Employed",
            "transportation_requests": 0,
            "wellness": "excellent"
        }
    ]

def jj_summary(residents):
    return {
        "residents_active": len(residents),
        "average_readiness": round(sum(r["readiness_score"] for r in residents) / len(residents)) if residents else 0,
        "employment_ready": len([r for r in residents if r["employment_status"] in ["Seeking Work", "Employed"]]),
        "transportation_requests": sum(r["transportation_requests"] for r in residents),
        "wellness_alerts": len([r for r in residents if r["wellness"] in ["struggling", "needs_support", "urgent"]])
    }
