from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app_weather_v109 import app

client = app.test_client()

paths = [
    "/",
    "/api/nws?place=Jasper,%20Alabama",
    "/api/copilot/questions",
    "/api/watchman/notifications",
    "/api/watchman/device/status",
    "/api/watchman/web-push/status",
    "/watchman_service_worker.js",
    "/api/watchman/weather-v109/status",
    "/api/watchman/weather-v109/routes",
    "/api/watchman/weather-v109/capabilities",
    "/api/watchman/weather-v109/health",
]

failed = []

for path in paths:
    response = client.get(path)
    print(f"{path} {response.status_code} {response.content_type}")
    if response.status_code != 200:
        failed.append((path, response.status_code))

if failed:
    print("\nFAILED:")
    for path, code in failed:
        print(f"{path} {code}")
    raise SystemExit(1)

print("\nWeather Watchman V109 test passed.")
