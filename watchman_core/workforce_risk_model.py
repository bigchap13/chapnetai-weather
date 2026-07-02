from .workforce_forecasting_engine import workforce_forecasting_engine

def workforce_risk_model():
    forecast = workforce_forecasting_engine()
    risks = []

    if forecast["placement_pressure"] == "critical":
        risks.append({
            "level": "critical",
            "issue": "No job leads available",
            "recommendation": "Add job leads or employer partners immediately."
        })

    if forecast["placement_pressure"] == "high":
        risks.append({
            "level": "high",
            "issue": "More residents seeking work than job leads available",
            "recommendation": "Expand employer outreach."
        })

    if forecast["projected_hires"] == 0:
        risks.append({
            "level": "medium",
            "issue": "No projected hires",
            "recommendation": "Review applications, interviews, and employer activity."
        })

    return {
        "forecast": forecast,
        "risks": risks,
        "risk_count": len(risks)
    }
