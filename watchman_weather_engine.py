from watchman_weather.weather_operations_center import analyze_weather as _watchman_analyze_weather

def analyze_weather(alerts=None, forecast=None, observation=None, location_name=None):
    payload = {
        "alerts": alerts or {},
        "forecast": forecast or {},
        "observation": observation or {},
        "location_name": location_name,
    }
    return _watchman_analyze_weather(payload)
