"""
Weather Watchman V109 route module.

This file holds Weather Watchman routes that are safe to separate from
the original parent Watchman app.
"""

from datetime import datetime, timezone


def register_weather_routes(app):
    @app.get("/api/watchman/weather-v109/status")
    def weather_v109_status():
        return {
            "ok": True,
            "mode": "Weather Watchman V109",
            "branch": "watchman-weather-v109",
            "status": "online",
            "message": "Weather Watchman V109 route module is active.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


    @app.get("/api/watchman/weather-v109/routes")
    def weather_v109_routes():
        routes = sorted(str(rule) for rule in app.url_map.iter_rules())
        weather_routes = [
            r for r in routes
            if "watchman" in r.lower() or "weather" in r.lower() or "api" in r.lower()
        ]
        return {
            "ok": True,
            "mode": "Weather Watchman V109 Route Inventory",
            "totalRoutes": len(routes),
            "weatherRouteCount": len(weather_routes),
            "routes": weather_routes,
        }

    return app
