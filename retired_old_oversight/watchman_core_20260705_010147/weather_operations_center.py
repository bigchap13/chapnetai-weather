from .weather_briefings import build_weather_briefing
from .weather_risk_model import WATCHMAN_WEATHER_VERSION


def analyze_weather(payload=None):
    return {
        "watchman_version": WATCHMAN_WEATHER_VERSION,
        "engine": "Watchman Weather Operations Center",
        "status": "operational",
        "weather_intelligence": build_weather_briefing(payload or {}),
    }
