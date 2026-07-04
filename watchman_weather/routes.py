"""
Weather Watchman V109 route module.

This file holds Weather Watchman routes that are safe to separate from
the original parent Watchman app.
"""

from datetime import datetime, timezone

from flask import jsonify, request
from watchman_weather.weather_memory_timeline import weather_memory_summary


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


    @app.get("/api/watchman/weather-v109/capabilities")
    def weather_v109_capabilities():
        return {
            "ok": True,
            "mode": "Weather Watchman V109 Capabilities",
            "capabilities": [
                "NOAA / National Weather Service weather data",
                "NWS active alerts",
                "GPS current-device weather monitoring",
                "Weather risk status",
                "GPS risk-change notifications",
                "Browser/Web Push support",
                "Phone push polling bridge",
                "Android Termux notification bridge",
                "Radar intelligence",
                "Radar motion tracking",
                "Radar cell tracking",
                "Multi-cell radar tracking",
                "Storm arrival intelligence",
                "Alert change detection",
                "NWS polygon layer",
                "Lightning intelligence",
                "Impact forecasting",
                "Route weather intelligence",
                "Live weather timeline",
                "Weather memory timeline",
                "Decision engine weather answers",
                "Weather voice copilot",
            ],
            "protectedParentDomains": [
                "Joshua's Journey",
                "Workforce",
                "Employment",
                "Transportation",
                "Grants",
                "Community CRM",
                "Executive oversight",
            ],
        }


    @app.get("/api/watchman/weather-v109/health")
    def weather_v109_health():
        checks = []
        required_routes = [
            "/api/nws",
            "/api/copilot/questions",
            "/api/watchman/notifications",
            "/api/watchman/device/status",
            "/api/watchman/web-push/status",
            "/watchman_service_worker.js",
            "/api/watchman/weather-v109/status",
            "/api/watchman/weather-v109/routes",
            "/api/watchman/weather-v109/capabilities",
        ]

        registered = {str(rule) for rule in app.url_map.iter_rules()}

        for route in required_routes:
            checks.append({
                "route": route,
                "registered": route in registered,
            })

        ok = all(item["registered"] for item in checks)

        return {
            "ok": ok,
            "mode": "Weather Watchman V109 Health",
            "status": "healthy" if ok else "missing_routes",
            "checks": checks,
        }


    @app.get("/api/watchman/weather-memory")
    def api_watchman_weather_memory():
        place = request.args.get("place", "").strip() or None

        return jsonify({
            "app": "CHAPNETAI Weather",
            "mode": "Watchman Weather Memory Timeline V1",
            "summary": weather_memory_summary(place),
        })

    return app
