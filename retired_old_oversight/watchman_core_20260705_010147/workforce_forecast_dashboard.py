from .workforce_forecasting_engine import workforce_forecasting_engine
from .workforce_risk_model import workforce_risk_model

def workforce_forecast_dashboard():
    forecast = workforce_forecasting_engine()
    risk = workforce_risk_model()

    return {
        "dashboard": "Workforce Forecast Dashboard",
        "forecast": forecast,
        "risk": risk
    }

def format_forecast_dashboard(data):
    f = data["forecast"]
    r = data["risk"]

    lines = [
        "WATCHMAN WORKFORCE FORECASTING",
        "",
        f"Projected Hires: {f['projected_hires']}",
        f"Placement Pressure: {f['placement_pressure'].upper()}",
        f"Residents Seeking Work: {f['residents_seeking_work']}",
        f"Job Leads Available: {f['job_leads_available']}",
        f"Employer Partners: {f['employer_partners']}",
        "",
        f"Risk Count: {r['risk_count']}",
        "",
        "RISKS:"
    ]

    if r["risks"]:
        for item in r["risks"]:
            lines.append(f"- {item['level'].upper()}: {item['issue']} | {item['recommendation']}")
    else:
        lines.append("- No major workforce risks detected.")

    return "\n".join(lines)
