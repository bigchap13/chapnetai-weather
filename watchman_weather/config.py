"""
Weather Watchman V109 configuration.

Central place for weather-only runtime settings.
"""

WEATHER_V109 = {
    "name": "Weather Watchman V109",
    "branch": "watchman-weather-v109",
    "default_place": "Jasper, Alabama",
    "default_port": 5099,
    "noaa_source": "NOAA / National Weather Service",
    "gps_poll_seconds": 15,
    "phone_push_poll_seconds": 15,
    "min_gps_notification_seconds": 300,
    "service_worker_path": "/watchman_service_worker.js",
}
