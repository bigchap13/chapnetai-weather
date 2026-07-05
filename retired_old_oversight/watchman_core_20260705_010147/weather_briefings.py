from .weather_alerts import summarize_alerts
from .weather_risk_model import WATCHMAN_WEATHER_VERSION, evaluate_weather_risk


def build_weather_briefing(payload=None):
    payload = payload or {}
    risk = evaluate_weather_risk(payload)
    alerts = summarize_alerts(payload)

    briefing = "\n".join([
        "Watchman V108 Weather Intelligence Briefing",
        "Risk level: " + str(risk["risk_level"]),
        "Risk score: " + str(risk["score"]),
        "Active alerts: " + str(alerts["active_alert_count"]),
        "Severe alerts: " + str(alerts["severe_alert_count"]),
    ])

    return {
        "watchman_version": WATCHMAN_WEATHER_VERSION,
        "briefing": briefing,
        "risk": risk,
        "alerts": alerts,
    }
