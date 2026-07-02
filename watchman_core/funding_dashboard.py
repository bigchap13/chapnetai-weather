from .grant_registry import grant_registry
from .funding_pipeline import funding_pipeline_records
from .grant_scoring import score_grant
from .grant_calendar import grant_calendar

def funding_dashboard():
    grants = grant_registry()
    pipeline = funding_pipeline_records()
    calendar = grant_calendar()

    scored = [
        {
            **grant,
            "score": score_grant(grant)
        }
        for grant in grants
    ]

    return {
        "dashboard": "Grant & Funding Opportunity Engine",
        "grants": len(grants),
        "pipeline_items": len(pipeline),
        "calendar_items": len(calendar),
        "high_fit": len([g for g in grants if g["fit"] == "high"]),
        "scored_grants": scored,
        "pipeline": pipeline,
        "calendar": calendar,
        "status": "operational"
    }

def format_funding_dashboard(data):
    lines = [
        "WATCHMAN GRANT & FUNDING OPPORTUNITY ENGINE",
        "",
        f"Grant Prospects: {data['grants']}",
        f"Pipeline Items: {data['pipeline_items']}",
        f"Calendar Items: {data['calendar_items']}",
        f"High-Fit Opportunities: {data['high_fit']}",
        "",
        "OPPORTUNITIES:"
    ]

    for grant in data["scored_grants"]:
        lines.append(
            f"- {grant['name']} | {grant['category']} | Fit: {grant['fit']} | Score: {grant['score']}"
        )

    return "\n".join(lines)
