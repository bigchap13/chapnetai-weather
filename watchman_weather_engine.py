from watchman_core.weather_operations_center import analyze_weather as _watchman_analyze_weather


def analyze_weather(*args, **kwargs):
    payload = {
        "args": args,
        "kwargs": kwargs,
    }
    return _watchman_analyze_weather(payload)


def run_watchman_weather(payload=None):
    return _watchman_analyze_weather(payload or {})
