from watchman_knowledge.live_timeline import build_live_timeline
from watchman_knowledge.mission_time_machine import mission_time_machine
from watchman_knowledge.weather_memory_timeline import record_weather_memory, weather_memory_summary
from watchman_knowledge.decision_explainer import explain_watchman_decision
from watchman_knowledge.mission_planner import mission_planner, MISSIONS
from watchman_knowledge.gps_risk_notifier import gps_risk_change_notifier, gps_risk_notifier_summary
from watchman_knowledge.gps_watch import update_gps_watch, stop_gps_watch, gps_watch_summary
from watchman_knowledge.weather_service import normalize_place, weather_lookup_for_place, weather_lookup_for_gps
from watchman_knowledge.gps_impact import gps_impact_forecast
from watchman_knowledge.decision_engine_v1 import watchman_decision_engine
from watchman_knowledge.impact_forecast import impact_forecast
from watchman_knowledge.radar_multi_cell_tracker import radar_multi_cell_tracker
from watchman_knowledge.nws_polygon_layer import build_advanced_nws_polygon_layer
from watchman_knowledge.lightning_map import lightning_intelligence
from watchman_knowledge.radar_cell_tracker import radar_cell_tracker
from watchman_knowledge.radar_motion_engine import radar_motion_engine
from watchman_knowledge.map_intelligence import build_map_intelligence
from watchman_knowledge.alert_change_notifier import alert_change_notifier, alert_change_summary
from watchman_knowledge.change_detection_engine import detect_weather_changes, change_detection_summary
from watchman_knowledge.storm_arrival_engine import storm_arrival_engine
from watchman_knowledge.alert_tracking import track_alerts, alert_tracking_summary
from watchman_knowledge.background_watch_loop import load_persisted_watches
from watchman_knowledge.background_watch_loop import register_watch, unregister_watch, list_watches, run_watch_once, start_background_watch_loop, stop_background_watch_loop, background_watch_summary, set_flask_app
from watchman_knowledge.android_notification_bridge import send_pending_android_notifications, android_bridge_summary
from watchman_knowledge.phone_push_bridge import pending_phone_pushes, acknowledge_phone_push, phone_push_summary
from watchman_knowledge.notification_delivery import queue_deliveries, list_delivery_outbox, delivery_summary
from watchman_knowledge.notification_engine import evaluate_notifications, list_notifications, mark_all_read, notification_summary
from watchman_knowledge.national_scope import national_scope_answer
from watchman_knowledge.conversation_memory import remember_conversation
from watchman_knowledge.national_alerts import answer_national_alert_question
from flask import Flask, request, jsonify
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import json
import math
from datetime import datetime, timezone
from watchman_weather_engine import analyze_weather
from watchman_voice_copilot import answer_watchman_question, top_questions_flat, extract_place_from_question
from watchman_knowledge.memory_engine import remember_scan, memory_summary
from watchman_knowledge.briefing_mode import build_watchman_briefing
from watchman_knowledge.mission_planner import build_mission_plan
from watchman_knowledge.current_device_gps_notifications import register_device, update_location, pending_pushes, ack_push, status as current_device_status
from watchman_knowledge.watchman_web_push import get_vapid_public_key, save_subscription, get_subscription, send_web_push, status as web_push_status

app = Flask(__name__)

APP_NAME = "CHAPNETAI Weather"
TAGLINE = "ChapNetAI Watchman"
CREDIT = "Your AI Weather and Navigation Companion"
USER_AGENT = "(chapnetai-weather.local, chapnetai@example.com)"

DEFAULT_LOCATION = {
    "name": "Jasper",
    "admin1": "Alabama",
    "country": "United States",
    "latitude": 33.8312,
    "longitude": -87.2775,
    "timezone": "America/Chicago",
}

def fetch_json(url):
    req = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/geo+json, application/json",
        },
    )
    with urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))

def geocode(place):
    normalized = (place or "").strip().lower()
    if normalized in {"", "jasper", "jasper alabama", "jasper, alabama", "jasper al"}:
        return DEFAULT_LOCATION

    q = urlencode({"name": place, "count": 10, "language": "en", "format": "json"})
    data = fetch_json(f"https://geocoding-api.open-meteo.com/v1/search?{q}")
    results = data.get("results") or []

    for item in results:
        if str(item.get("country_code", "")).upper() == "US":
            return {
                "name": item.get("name"),
                "admin1": item.get("admin1"),
                "country": item.get("country"),
                "latitude": item.get("latitude"),
                "longitude": item.get("longitude"),
                "timezone": item.get("timezone") or "America/Chicago",
            }

    if results:
        item = results[0]
        return {
            "name": item.get("name"),
            "admin1": item.get("admin1"),
            "country": item.get("country"),
            "latitude": item.get("latitude"),
            "longitude": item.get("longitude"),
            "timezone": item.get("timezone") or "America/Chicago",
        }

    return None

def c_to_f(value):
    if value is None:
        return None
    return round((float(value) * 9 / 5) + 32)

def mps_to_mph(value):
    if value is None:
        return None
    return round(float(value) * 2.23694)

def kmh_to_mph(value):
    if value is None:
        return None
    return round(float(value) * 0.621371)

def get_nested(data, *keys, default=None):
    cur = data
    for key in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
    return cur if cur is not None else default

def nws_points(lat, lon):
    return fetch_json(f"https://api.weather.gov/points/{lat:.4f},{lon:.4f}")

def active_alerts(lat, lon):
    url = f"https://api.weather.gov/alerts/active?point={lat:.4f},{lon:.4f}"
    data = fetch_json(url)
    alerts = []
    for feature in data.get("features", []):
        p = feature.get("properties", {})
        alerts.append({
            "event": p.get("event"),
            "headline": p.get("headline"),
            "severity": p.get("severity"),
            "urgency": p.get("urgency"),
            "certainty": p.get("certainty"),
            "instruction": p.get("instruction"),
            "description": p.get("description"),
            "effective": p.get("effective"),
            "expires": p.get("expires"),
            "sender": p.get("senderName"),
        })
    return alerts

def nearest_observation(stations_url):
    stations = fetch_json(stations_url)
    features = stations.get("features") or []
    if not features:
        return None

    station_id = features[0].get("properties", {}).get("stationIdentifier")
    if not station_id:
        return None

    obs = fetch_json(f"https://api.weather.gov/stations/{station_id}/observations/latest")
    p = obs.get("properties", {})

    return {
        "station": station_id,
        "name": features[0].get("properties", {}).get("name"),
        "temperatureF": c_to_f(get_nested(p, "temperature", "value")),
        "dewpointF": c_to_f(get_nested(p, "dewpoint", "value")),
        "windMph": mps_to_mph(get_nested(p, "windSpeed", "value")),
        "gustMph": mps_to_mph(get_nested(p, "windGust", "value")),
        "text": p.get("textDescription"),
        "timestamp": p.get("timestamp"),
    }





def _is_watchman_decision_question(q):
    q = (q or "").lower()
    triggers = [
        "what should i do",
        "what do i do",
        "right now",
        "safe to drive",
        "safe to go",
        "should i drive",
        "should i go outside",
        "go outside",
        "need to shelter",
        "do i need to shelter",
        "should i shelter",
        "shelter now",
        "safe outside",
        "delay travel",
        "should i delay",
        "is it safe",
    ]
    return any(t in q for t in triggers)


def _watchman_direct_alert_answer(place, weather):
    alerts = weather.get("alerts") or []

    if not alerts:
        return f"No active NWS alerts for {place}."

    lines = [f"{len(alerts)} active alert(s) for {place}:"]

    for alert in alerts[:5]:
        event = alert.get("event") or "Weather Alert"
        headline = alert.get("headline") or ""
        area = alert.get("areaDesc") or ""
        expires = alert.get("expires") or ""

        text = f"- {event}"
        if headline:
            text += f": {headline}"
        if area:
            text += f" | Areas: {area}"
        if expires:
            text += f" | Expires: {expires}"

        lines.append(text)

    return "\n".join(lines)


def _fetch_weather_direct(place):
    place = normalize_place(place)

    raw = place.replace(" ", "")
    geo = None

    if "," in raw:
        try:
            a, b = raw.split(",", 1)
            lat = float(a)
            lon = float(b)
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                geo = {
                    "name": "Route Point",
                    "admin1": "",
                    "country": "",
                    "lat": lat,
                    "lon": lon,
                    "latitude": lat,
                    "longitude": lon,
                    "timezone": "America/Chicago",
                }
        except Exception:
            geo = None

    if geo is None:
        geo = geocode(place)

    if not geo:
        return {"error": "geocode_failed", "place": place}

    lat = geo.get("lat") or geo.get("latitude")
    lon = geo.get("lon") or geo.get("lng") or geo.get("longitude")

    if lat is None or lon is None:
        return {
            "error": "geocode_coordinates_missing",
            "place": place,
            "geocode": geo,
        }

    try:
        points = nws_points(float(lat), float(lon))
    except Exception as exc:
        return {
            "error": "nws_point_lookup_failed",
            "place": place,
            "lat": float(lat),
            "lon": float(lon),
            "details": str(exc)[:200],
        }

    forecast_url = get_nested(points, "properties", "forecast")
    hourly_url = get_nested(points, "properties", "forecastHourly")
    stations_url = get_nested(points, "properties", "observationStations")

    forecast = fetch_json(forecast_url).get("properties", {}).get("periods", []) if forecast_url else []
    hourly = fetch_json(hourly_url).get("properties", {}).get("periods", []) if hourly_url else []
    observation = nearest_observation(stations_url) if stations_url else {}
    alerts = active_alerts(float(lat), float(lon))

    location_name = f"{geo.get('name')}, {geo.get('admin1') or geo.get('country')}"
    watchman = analyze_weather(alerts, forecast, observation, location_name)

    return {
        "app": "CHAPNETAI Weather",
        "location": {
            "name": geo.get("name"),
            "region": geo.get("admin1"),
            "country": geo.get("country"),
            "lat": float(lat),
            "lon": float(lon),
            "timezone": geo.get("timezone") or "America/Chicago",
        },
        "alerts": alerts,
        "forecast": forecast,
        "hourly": hourly[:24],
        "observation": observation,
        "watchman": watchman,
    }


def _watchman_safe_error_answer(question, place, status_code=502):
    return jsonify({
        "app": "CHAPNETAI Weather",
        "watchman_version": "Watchman V108",
        "mode": "Watchman AI Copilot",
        "place": place,
        "requestedPlace": place,
        "question": question,
        "answer": (
            "Watchman could not complete the live weather lookup for this location. "
            "This is a weather/location data fetch failure, not a Watchman Intelligence Core V2 reasoning failure. "
            "Try the same question again or use a nearby city."
        ),
        "error": "weather_lookup_failed",
        "status": "degraded",
    }), status_code

@app.route("/health")
def health():
    return {
        "service": APP_NAME,
        "tagline": TAGLINE,
        "status": "online",
        "source": "NOAA / National Weather Service",
    }

@app.route("/api/nws")
def api_nws():
    place = request.args.get("place", "Jasper, Alabama").strip() or "Jasper, Alabama"
    place = place.replace(",", ", ")
    while "  " in place:
        place = place.replace("  ", " ")
    geo = geocode(place)
    if not geo:
        return jsonify({"error": "Location not found"}), 404

    lat = float(geo["latitude"])
    lon = float(geo["longitude"])

    try:
        point = nws_points(lat, lon)
        props = point.get("properties", {})

        forecast = fetch_json(props["forecast"])
        hourly = fetch_json(props["forecastHourly"])
        alerts = active_alerts(lat, lon)

        observation = None
        try:
            observation = nearest_observation(props["observationStations"])
        except Exception:
            observation = None

        forecast_periods = forecast.get("properties", {}).get("periods", [])
        hourly_periods = hourly.get("properties", {}).get("periods", [])[:24]

        # NOAA station observations sometimes return null temperature.
        # Use the first NOAA hourly forecast temperature as the display fallback.
        if observation is not None and observation.get("temperatureF") is None and hourly_periods:
            fallback_temp = hourly_periods[0].get("temperature")
            if fallback_temp is not None:
                observation["temperatureF"] = fallback_temp
                observation["temperatureSource"] = "NOAA hourly forecast fallback"

        watchman = analyze_weather(alerts, forecast_periods, observation, f"{geo.get('name')}, {geo.get('admin1') or geo.get('country')}")

        return jsonify({
            "app": APP_NAME,
            "tagline": TAGLINE,
            "credit": CREDIT,
            "location": geo,
            "nws": {
                "office": props.get("cwa"),
                "gridId": props.get("gridId"),
                "gridX": props.get("gridX"),
                "gridY": props.get("gridY"),
                "forecastOffice": props.get("forecastOffice"),
                "timeZone": props.get("timeZone"),
            },
            "observation": observation,
            "alerts": alerts,
            "forecast": forecast_periods,
            "hourly": hourly_periods,
            "watchman": watchman,
            "generatedAt": datetime.now(timezone.utc).isoformat(),
        })

    except HTTPError as e:
        return jsonify({"error": f"NWS request failed: {e.code}"}), 502
    except URLError as e:
        return jsonify({"error": f"Network error: {e}"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/copilot/questions")
def api_copilot_questions():
    return jsonify({
        "count": len(top_questions_flat()),
        "questions": top_questions_flat(),
    })

@app.route("/api/copilot/ask")
def api_copilot_ask():
    requested_place = request.args.get("place", "Jasper, Alabama").strip() or "Jasper, Alabama"
    requested_place = requested_place.replace(",", ", ")
    while "  " in requested_place:
        requested_place = requested_place.replace("  ", " ")
    question = request.args.get("q", "").strip()

    scope_ai = national_scope_answer(question)
    if scope_ai:
        return jsonify({
            "app": "CHAPNETAI Weather",
            "mode": "Watchman AI Copilot",
            "question": question,
            "answer": scope_ai["answer"],
            "scope": scope_ai,
            "watchman_version": "Watchman V108",
        })

    if not question:
        return jsonify({"error": "Missing q question parameter"}), 400

    q_low = question.lower()
    county_alert_question = (
        ("alert" in q_low or "warning" in q_low or "watch" in q_low or "advisory" in q_low)
        and "county" in q_low
    )

    if county_alert_question:
        place = requested_place
    else:
        place = extract_place_from_question(question, requested_place)

    weather = weather_lookup_for_place(place, geocode, _fetch_weather_direct)

    if "error" in weather:
        return _watchman_safe_error_answer(question, place, weather)

    q_lower = question.lower()

    if _is_watchman_decision_question(q_lower):
        geo = geocode(place)
        lat = geo.get("lat") or geo.get("latitude") if geo else None
        lon = geo.get("lon") or geo.get("lng") or geo.get("longitude") if geo else None

        if lat is not None and lon is not None:
            multi_cell = radar_multi_cell_tracker(place, lat, lon)
            impact = impact_forecast(place, lat, lon, weather, multi_cell)
            radar_motion = radar_motion_engine(place, lat, lon, weather, storm_arrival_engine("copilot decision", weather))
            radar_cell = radar_cell_tracker(place, lat, lon)
            lightning = lightning_intelligence(place, lat, lon, weather, radar_motion, radar_cell)
            decision = watchman_decision_engine(place, weather, impact, lightning, multi_cell)

            recs = " ".join(decision.get("recommendations") or [])
            reasons = " ".join(decision.get("reasons") or [])
            answer = (
                f"{decision.get('decision')}. "
                f"Severity: {decision.get('severity')}. "
                f"Score: {decision.get('decisionScore')}/100. "
                f"Primary threat: {decision.get('primaryThreat')}. "
                f"Action: {recs} "
                f"Reason: {reasons}"
            )
        else:
            answer = answer_watchman_question(question, weather)

    elif any(x in q_lower for x in [
        "active alert",
        "active alerts",
        "weather alert",
        "weather alerts",
        "nws alert",
        "nws alerts",
        "warning",
        "warnings",
        "watch",
        "watches",
        "advisory",
        "advisories"
    ]):
        answer = _watchman_direct_alert_answer(place, weather)
    elif any(x in q_lower for x in [
        "when will the storm",
        "storm arrival",
        "storm get here",
        "storms get here",
        "approaching",
        "coming toward",
        "coming from the east",
        "from the east",
        "storm timing"
    ]):
        answer = storm_arrival_engine(question, weather)["answer"]
    elif any(x in q_lower for x in [
        "what changed",
        "anything changed",
        "has it changed",
        "changed since",
        "since earlier",
        "since last scan"
    ]):
        arrival = storm_arrival_engine(question, weather)
        answer = detect_weather_changes(place, weather, arrival)["answer"]
    else:
        answer = answer_watchman_question(question, weather)
    remember_conversation(place, question, answer, weather)
    try:
        from watchman_knowledge.radar_intelligence_v2 import radar_intelligence_v2
        from watchman_knowledge.emergency_mode import emergency_mode
        radar_result = radar_intelligence_v2(question, weather)
        storm_arrival = storm_arrival_engine(question, weather)
        change_result = detect_weather_changes(place, weather, storm_arrival)
        alert_change = alert_change_notifier(place, weather, storm_arrival)
        emergency_result = emergency_mode(question, weather, radar_result)
        alert_track = track_alerts(place, weather)
        notify_result = evaluate_notifications(place, weather, emergency_result, radar_result, alert_change)
        created_deliveries = queue_deliveries((notify_result or {}).get("created", []))
        send_pending_android_notifications(created_deliveries)
    except Exception:
        pass
    remember_scan(place, question, answer, weather)

    return jsonify({
        "app": APP_NAME,
        "mode": "Watchman AI Copilot",
        "place": place,
        "requestedPlace": requested_place,
        "question": question,
        "answer": answer,
        "memory": memory_summary(place),
        "watchman_version": (weather.get("watchman") or {}).get("watchman_version", "Watchman V108"),
    })


@app.route("/api/briefing")
def api_briefing():
    place = request.args.get("place", "Jasper, Alabama").strip() or "Jasper, Alabama"

    weather = weather_lookup_for_place(place, geocode, _fetch_weather_direct)

    if "error" in weather:
        return jsonify(weather), 502

    return jsonify(build_watchman_briefing(weather))


@app.route("/api/mission")
def api_mission():
    place = request.args.get("place", "Jasper, Alabama").strip() or "Jasper, Alabama"
    question = request.args.get("q", "").strip() or "general weather mission"

    weather = weather_lookup_for_place(place, geocode, _fetch_weather_direct)

    if "error" in weather:
        return jsonify(weather), 502

    return jsonify(build_mission_plan(question, weather))


@app.route("/api/national-alerts")
def api_national_alerts():
    question = request.args.get("q", "Are there active severe weather alerts anywhere?").strip()
    try:
        return jsonify(answer_national_alert_question(question))
    except Exception as e:
        return jsonify({"error": str(e)}), 502

@app.route("/")
def home():
    return """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CHAPNETAI Weather</title>
<style>
:root{--bg:#071019;--panel:#101d2a;--panel2:#0b1622;--line:#22384c;--text:#eef7ff;--muted:#9fb3c8;--gold:#d4af37;--red:#ff5c5c;--orange:#ffae42;--green:#6dff9e;--blue:#4fc3ff}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(circle at top,#173a56,#071019 58%);color:var(--text);font-family:system-ui,Arial,sans-serif}
.wrap{max-width:1180px;margin:auto;padding:1rem}
.hero{border:1px solid var(--line);border-radius:1.5rem;background:linear-gradient(135deg,rgba(16,29,42,.96),rgba(8,18,28,.92));padding:1.25rem;box-shadow:0 24px 80px rgba(0,0,0,.38)}
.kicker{color:var(--gold);font-weight:1000;letter-spacing:.1em;text-transform:uppercase;font-size:.76rem}
h1{font-size:clamp(2.2rem,8vw,4.8rem);line-height:.95;margin:.45rem 0}
h2{margin:.1rem 0 .75rem}
p{color:var(--muted)}
.search{display:flex;gap:.55rem;margin-top:1rem}
.copilotBox{margin-top:1rem;border:1px solid var(--line);border-radius:1.25rem;background:rgba(255,255,255,.045);padding:1rem}
.copilotControls{display:flex;gap:.55rem;flex-wrap:wrap;margin-top:.75rem}
.copilotAnswer{margin-top:.75rem;color:var(--text);font-weight:800;line-height:1.45}
.micBtn{background:#4fc3ff;color:#06101d}
.speakBtn{background:#6dff9e;color:#06101d}
input,button{border-radius:999px;border:1px solid var(--line);padding:.9rem 1rem;font:inherit}
input{flex:1;background:#08131d;color:var(--text)}
button{background:var(--gold);color:#111;font-weight:1000}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-top:1rem}
.card{border:1px solid var(--line);border-radius:1.25rem;background:rgba(16,29,42,.88);padding:1rem}
.big{font-size:3.8rem;font-weight:1000}
.threat{display:inline-flex;padding:.4rem .75rem;border-radius:999px;font-weight:1000}
.LOW{background:rgba(109,255,158,.16);color:var(--green);border:1px solid rgba(109,255,158,.45)}
.ELEVATED{background:rgba(255,174,66,.16);color:var(--orange);border:1px solid rgba(255,174,66,.45)}
.HIGH,.EXTREME{background:rgba(255,92,92,.18);color:var(--red);border:1px solid rgba(255,92,92,.5)}
.row{display:flex;justify-content:space-between;gap:1rem;border-top:1px solid var(--line);padding:.72rem 0;color:var(--muted)}
.row strong{color:var(--text)}
.alert{border-left:5px solid var(--red);background:rgba(255,92,92,.08)}
.days{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.75rem}
.day{border:1px solid var(--line);border-radius:1rem;background:rgba(255,255,255,.04);padding:.8rem}
.hourly{max-height:460px;overflow:auto}
#radarMap{width:100%;height:430px;border-radius:18px;border:1px solid rgba(255,255,255,.16);background:#06101d;overflow:hidden}
.radarNote{font-size:.9rem;color:var(--muted);margin-top:.6rem}
.mapLegend{display:flex;flex-wrap:wrap;gap:.5rem;margin-top:.7rem}

.nwsFlash{animation:nwsPulse 1.15s infinite}
@keyframes nwsPulse{0%{filter:brightness(1)}50%{filter:brightness(1.8)}100%{filter:brightness(1)}}
.layerControls{display:flex;flex-wrap:wrap;gap:.45rem;margin-top:.8rem}
.layerControls label{font-size:.82rem;padding:.32rem .55rem;border:1px solid rgba(255,255,255,.16);border-radius:999px;background:rgba(255,255,255,.06)}
.legendPill{font-size:.8rem;padding:.35rem .55rem;border-radius:999px;border:1px solid rgba(255,255,255,.16);background:rgba(255,255,255,.07)}
.footer{text-align:center;color:var(--muted);padding:2rem 0}
@media(max-width:780px){.grid{grid-template-columns:1fr}.search{flex-direction:column}.big{font-size:3rem}}

.hero{text-align:center}
.hero .kicker{text-align:center}
.hero h1{text-align:center}
.hero p{text-align:center}
.hero input{display:block;margin-left:auto;margin-right:auto;text-align:center}
.hero button{display:block;margin:1rem auto 0 auto;min-width:min(100%,320px)}
.sourcePill{display:inline-block;margin-top:.8rem;padding:.75rem 1rem;border-radius:16px;background:rgba(255,255,255,.06);color:var(--muted)}
.card:first-of-type .kicker{text-align:center}
.card:first-of-type h2{text-align:center}
.card:first-of-type p{text-align:center}
.voiceButtons{justify-content:center}
#voiceStatus{text-align:center}


/* ChapNetAI Watchman centered branding lock */
.hero,
.hero .kicker,
.hero h1,
.hero p{
  text-align:center;
}
.hero h1{
  margin:.4rem auto .8rem auto;
}
.heroTagline{
  color:#d8b94f;
  font-size:1.18rem;
}
.watchmanPower{
  margin-top:1.1rem;
  font-size:1.05rem;
}
.sourcePill{
  display:inline-block;
  margin:1rem auto 0 auto;
  padding:.8rem 1rem;
  border-radius:16px;
  background:rgba(255,255,255,.06);
  color:var(--muted);
}
.hero input{
  display:block;
  margin:1.35rem auto 0 auto;
  text-align:center;
}
.hero button{
  display:block;
  margin:1rem auto 0 auto;
  min-width:min(100%,320px);
}
.hero + .card,
.hero + .card .kicker,
.hero + .card h2,
.hero + .card p,
#voiceStatus{
  text-align:center;
}
.hero + .card input{
  text-align:center;
}
.hero + .card .voiceButtons{
  display:flex;
  justify-content:center;
  align-items:center;
  gap:1rem;
  flex-wrap:wrap;
}


/* Watchman Copilot mobile polish */
.voiceButtons{
  display:flex;
  justify-content:center;
  align-items:center;
  gap:1rem;
  flex-wrap:wrap;
}
.voiceButtons button{
  min-width:190px;
}
#voiceQuestion{
  display:block;
  margin-left:auto;
  margin-right:auto;
  text-align:center;
}
#copilotAnswer{
  text-align:left;
  line-height:1.45;
  max-width:100%;
  overflow-wrap:anywhere;
}
@media (max-width: 520px){
  .voiceButtons{
    flex-direction:column;
  }
  .voiceButtons button{
    width:100%;
    max-width:320px;
  }
}


.missionGrid{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(135px,1fr));
  gap:.65rem;
  margin:1rem 0;
}
.missionGrid button{
  width:100%;
}


/* Watchman Mission Center polish */
.missionGrid button{
  border-radius:16px;
  padding:.85rem .7rem;
  font-weight:900;
}
#missionCenterBox,
#weatherMemoryBox{
  margin-top:1rem;
}
#missionCenterBox h3,
#weatherMemoryBox h3{
  text-align:center;
  margin-top:1.1rem;
}
.verdictBadge{
  display:inline-block;
  padding:.45rem .8rem;
  border-radius:999px;
  font-weight:900;
  letter-spacing:.08rem;
}
.verdict-go{background:rgba(58,214,122,.18);color:#5cff99}
.verdict-caution{background:rgba(255,210,77,.18);color:#ffd24d}
.verdict-wait{background:rgba(255,91,91,.18);color:#ff7b7b}


/* Watchman V2 Phase 1 UI cleanup */
.watchmanPhase1Hidden{display:none!important}



</style>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
</head>
<body>
<div class="wrap">
<section class="hero">

<div class="kicker">CHAPNETAI WATCHMAN</div>

<h1>ChapNetAI Watchman</h1>

<p class="heroTagline"><strong>Your AI Weather and Navigation Companion</strong></p>

<p class="watchmanPower">
  <strong>Powered by ChapNetAI Watchman™</strong><br>
  AI Weather • Navigation • Travel Intelligence
</p>

<p>
  <span class="sourcePill">Official weather data from NOAA • National Weather Service</span>
</p>

<input id="place" value="Jasper, Alabama" placeholder="City, state">
<button onclick="loadWeather()">Start Watchman</button>

</div>

<div class="copilotBox">
  <div class="kicker" style="text-align:center;">CHAPNETAI WATCHMAN AI</div>
  <h2 style="text-align:center;">Ask Watchman</h2>
  <p style="text-align:center;">Type a question about weather, navigation, travel, or almost anything. Watchman will answer right here.</p>
  <div class="copilotControls">
    <input id="copilotQuestion" placeholder="Ask: Should I mow today? Is lightning nearby? When will rain start?">
    <button class="micBtn" onclick="startWatchmanVoice()">🎙 Ask</button>
    <button class="speakBtn" onclick="speakLastWatchmanAnswer()">Read Again</button>
  </div>
  <div id="copilotAnswer" class="copilotAnswer">Ready.</div>
</div>
</section>


<div id="app"></div>
<div class="footer">Independent ChapNetAI platform. Official warnings remain NOAA / National Weather Service products.</div>
</div>

<script>

function publicText(v){
  return safe(v)
    .replace(/\\bWatchman\\s+V\\d+\\b/g, 'Watchman')
    .replace(/\\bV\\d+\\b/g, '')
    .replace(new RegExp('\\\\bver'+'sion\\\\s*[:#]?\\\\s*\\\\d+(\\\\.\\\\d+)*\\\\b','ig'), '')
    .replace(/\\s{2,}/g, ' ')
    .trim();
}

function safe(v,fallback='—'){return v===null||v===undefined||v===''?fallback:v}
function timeLabel(t){return String(t||'').replace('T',' ').replace('-05:00','').replace('-06:00','')}

let lastWatchmanAnswer='';

function speakWatchman(text){
  lastWatchmanAnswer=text || '';
  if(!lastWatchmanAnswer) return;
  if(!('speechSynthesis' in window)){
    document.getElementById('copilotAnswer').innerText=lastWatchmanAnswer + ' Speech is not supported in this browser.';
    return;
  }
  window.speechSynthesis.cancel();
  const utterance=new SpeechSynthesisUtterance(lastWatchmanAnswer);
  utterance.rate=.92;
  utterance.pitch=.95;
  utterance.volume=1;
  window.speechSynthesis.speak(utterance);
}

function speakLastWatchmanAnswer(){
  speakWatchman(lastWatchmanAnswer || document.getElementById('copilotAnswer').innerText);
}

async function askWatchman(question){
  const place=document.getElementById('place').value || 'Jasper, Alabama';
  const box=document.getElementById('copilotAnswer');
  box.innerText='Watchman is thinking...';
  const url='/api/copilot/ask?place='+encodeURIComponent(place)+'&q='+encodeURIComponent(question);
  const r=await fetch(url);
  const data=await r.json();
  if(!r.ok){
    const msg=data.error || 'Watchman copilot request failed.';
    box.innerText=msg;
    speakWatchman(msg);
    return;
  }
  box.innerText=data.answer;
  speakWatchman(data.answer);
}

function startWatchmanVoice(){
  const input=document.getElementById('copilotQuestion');
  const SpeechRecognition=window.SpeechRecognition || window.webkitSpeechRecognition;

  if(!SpeechRecognition){
    const typed=input.value.trim();
    if(typed){
      askWatchman(typed);
      return;
    }
    const msg='Speech recognition is not supported in this browser. Type your question and press Ask.';
    document.getElementById('copilotAnswer').innerText=msg;
    speakWatchman(msg);
    return;
  }

  const rec=new SpeechRecognition();
  rec.lang='en-US';
  rec.interimResults=false;
  rec.maxAlternatives=1;

  document.getElementById('copilotAnswer').innerText='Listening...';

  rec.onresult=(event)=>{
    const question=event.results[0][0].transcript;
    input.value=question;
    askWatchman(question);
  };

  rec.onerror=()=>{
    const typed=input.value.trim();
    if(typed){
      askWatchman(typed);
    }else{
      const msg='I could not hear the question. Try again or type it.';
      document.getElementById('copilotAnswer').innerText=msg;
      speakWatchman(msg);
    }
  };

  rec.start();
}


let watchmanRadarMap=null;
window.watchmanRadarMap=null;
let watchmanRadarLayers=[];
window.watchmanRadarLayers=watchmanRadarLayers;

function polygonStyle(feature){
  const p=(feature && feature.properties) || {};
  return {
    color: p.color || '#ffd600',
    weight: p.kind === 'watchman_storm_cell_proxy' ? 3 : (p.kind === 'watchman_storm_projection' ? 2 : 2),
    dashArray: p.kind === 'watchman_storm_projection' ? '7,7' : null,
    fillColor: p.color || '#ffd600',
    fillOpacity: p.kind === 'watchman_storm_projection' ? 0.08 : (p.kind === 'watchman_storm_cell_proxy' ? 0.16 : 0.22)
  };
}

function polygonPopup(feature){
  const p=(feature && feature.properties) || {};
  if(p.kind === 'watchman_storm_cell_proxy' || p.kind === 'watchman_storm_projection'){
    return `
      <strong>${safe(p.title || 'Watchman Storm Cell')}</strong><br>
      Threat: ${safe(p.threatScore)}<br>
      Precip: ${safe(p.precipChance)}%<br>
      Arrival: ${safe(p.arrivalEstimate)}<br>
      Movement: ${safe(p.movement)}<br>
      Projection: +${safe(p.projectionMinutes,0)} min<br>
      Bearing: ${safe(p.bearingDegrees)}°<br>
      Speed: ${safe(p.speedMph)} mph<br>
      Confidence: ${safe(p.confidence)}%<br>
      ${safe(p.note)}
    `;
  }

  return `
    <strong>${safe(p.event || 'NWS Alert')}</strong><br>
    ${safe(p.headline || '')}<br>
    Severity: ${safe(p.severity)}<br>
    Urgency: ${safe(p.urgency)}<br>
    Areas: ${safe(p.areaDesc)}<br>
    Expires: ${safe(p.expires)}
  `;
}

let watchmanRouteLayer=null;
let watchmanRouteMarkers=[];
let watchmanNavigationData=null;
let watchmanNavigationWatchId=null;
let watchmanSpokenSteps={};
let watchmanSpokenWeather={};
let watchmanDrivePanelTimer=null;
let watchmanSafetyMarkers=[];
let watchmanLastSpeedLimit={raw:'',mph:null,source:'unavailable',updatedAt:0};

function watchmanSpeak(text){
  if(!text || !('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const u=new SpeechSynthesisUtterance(text);
  u.rate=1;
  window.speechSynthesis.speak(u);
}

function milesBetween(a,b,c,d){
  const R=3958.8;
  const toRad=x=>x*Math.PI/180;
  const dLat=toRad(c-a), dLon=toRad(d-b);
  const aa=Math.sin(dLat/2)**2 + Math.cos(toRad(a))*Math.cos(toRad(c))*Math.sin(dLon/2)**2;
  return R*2*Math.atan2(Math.sqrt(aa),Math.sqrt(1-aa));
}

function clearWatchmanRouteLayers(){
  if(!watchmanRadarMap) return;
  if(watchmanRouteLayer){try{watchmanRadarMap.removeLayer(watchmanRouteLayer)}catch(e){}}
  watchmanRouteLayer=null;
  for(const m of watchmanRouteMarkers){try{watchmanRadarMap.removeLayer(m)}catch(e){}}
  watchmanRouteMarkers=[];
}


function formatRouteMinutes(mins){
  mins=parseInt(mins||0,10);
  if(!mins) return 'time unavailable';
  const h=Math.floor(mins/60);
  const m=mins%60;
  if(h<=0) return m+' min';
  if(m===0) return h+' hr';
  return h+' hr '+m+' min';
}

function routeStatusLabel(verdict){
  const v=(verdict||'').toLowerCase();
  if(v==='dangerous') return '⛔ Avoid Travel';
  if(v==='caution') return '⚠️ Use Caution';
  if(v==='clear') return '✅ Clear';
  return 'ℹ️ Weather Check';
}

function routeConcernText(point){
  const r=(point&&point.risk)||{};
  const explanation=(point&&point.explanation)||'No major weather concern detected.';
  const mile=(point&&point.mile!==undefined)?point.mile:0;
  if(Number(mile)===0) return explanation+' near departure.';
  return explanation+' near mile '+safe(mile)+'.';
}

async function planWatchmanNavigationRoute(){
  const destEl=document.getElementById('watchmanNavDestination');
  const box=document.getElementById('watchmanNavBox');
  const dest=(destEl&&destEl.value||'').trim();
  if(!dest){box.innerText='Enter a destination first.';return;}
  if(!navigator.geolocation){box.innerText='GPS is required.';return;}

  box.innerText='Getting current GPS location...';
  navigator.geolocation.getCurrentPosition(async function(pos){
    try{
      box.innerText='Building road route and scanning weather along the drive...';
      const res=await fetch('/api/watchman/navigation-route',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({
          originLat:pos.coords.latitude,
          originLon:pos.coords.longitude,
          destination:dest,
          samples:6
        })
      });
      const data=await res.json();
      if(!data.ok){box.innerText='Route failed: '+(data.error||'unknown');return;}
      watchmanNavigationData=data;
      watchmanSpokenSteps={};
      watchmanSpokenWeather={};
      clearWatchmanRouteLayers();

      const geometry=(data.route&&data.route.geometry||[]).map(p=>[p.lat,p.lon]);
      watchmanRouteLayer=L.polyline(geometry,{weight:8,opacity:1,color:'#1f7aff'}).addTo(watchmanRadarMap);
      watchmanRadarMap.fitBounds(watchmanRouteLayer.getBounds(),{padding:[24,24]});

      const visibleHazards=visibleRouteHazardPoints(data.weatherPoints||[], data.summary||{});
      for(const p of visibleHazards){
        const r=p.risk||{};
        const marker=L.marker([p.lat,p.lon],{icon:routeHazardIcon(p)}).addTo(watchmanRadarMap);
        marker.bindPopup('<strong>'+safe(p._markerReason||'Route concern')+' · Mile '+safe(p.mile)+'</strong><br>'+routeStatusLabel(r.verdict)+'<br>'+safe(p.explanation)+'<br>'+safe(r.condition));
        watchmanRouteMarkers.push(marker);
      }

      const s=data.summary||{};
      const w=s.worstPoint||{};
      const wr=w.risk||{};
      const steps=(data.route.steps||[]).slice(0,8).map((st,i)=>'<div class="row"><span>'+(i+1)+'. '+safe(st.instruction)+'</span><strong>'+Math.round((st.distanceMeters||0)*0.000621371*10)/10+' mi</strong></div>').join('');

      const statusText=routeStatusLabel(s.verdict);
      const concernText=routeConcernText(w);

      box.innerHTML=
        '<strong>'+statusText+'</strong><br>'+
        safe(s.recommendation)+'<br>'+
        'Trip: '+safe(data.route.distanceMiles)+' mi · '+formatRouteMinutes(data.route.durationMinutes)+'<br>'+
        '<strong>Main weather concern</strong><br>'+safe(concernText)+'<br>'+
        steps;

      loadWatchmanSafetyAlongRoute();
      watchmanSpeak('Route planned. Watchman route verdict is '+(s.verdict||'unknown')+'. '+(s.recommendation||''));
    }catch(e){
      box.innerText='Route planner error: '+e.message;
    }
  }, function(){
    box.innerText='GPS permission is required.';
  }, {enableHighAccuracy:false,maximumAge:60000,timeout:15000});
}



function gpsSpeedMph(pos){
  const s=pos && pos.coords ? pos.coords.speed : null;
  if(s===null || s===undefined || isNaN(s)) return null;
  return Math.round(s*2.23694);
}

async function refreshWatchmanSpeedLimit(lat,lon){
  const now=Date.now();
  if(watchmanLastSpeedLimit.updatedAt && (now-watchmanLastSpeedLimit.updatedAt)<30000) return watchmanLastSpeedLimit;
  try{
    const data=await fetch('/api/watchman/road-speed-limit?lat='+encodeURIComponent(lat)+'&lon='+encodeURIComponent(lon),{cache:'no-store'}).then(r=>r.json());
    watchmanLastSpeedLimit={
      raw:data.speedLimitRaw||'',
      mph:data.speedLimitMph,
      source:data.source||'unavailable',
      road:data.road||'',
      updatedAt:now
    };
  }catch(e){
    watchmanLastSpeedLimit={raw:'',mph:null,source:'unavailable',updatedAt:now};
  }
  return watchmanLastSpeedLimit;
}

function clearWatchmanSafetyLayer(){
  if(!watchmanRadarMap) return;
  for(const m of watchmanSafetyMarkers){try{watchmanRadarMap.removeLayer(m)}catch(e){}}
  watchmanSafetyMarkers=[];
}



function routeHazardKey(point){
  const r=(point&&point.risk)||{};
  const text=((point&&point.explanation)||''+' '+(r.condition||'')+' '+(r.reasons||[]).join(' ')).toLowerCase();
  if(text.includes('lightning') || text.includes('thunder')) return 'storm';
  if(text.includes('tornado')) return 'tornado';
  if(text.includes('flood')) return 'flood';
  if(text.includes('rain') || text.includes('shower')) return 'rain';
  if(text.includes('snow') || text.includes('ice') || text.includes('sleet')) return 'ice';
  if(text.includes('wind') || text.includes('gust')) return 'wind';
  if(text.includes('heat') || text.includes('hot')) return 'heat';
  if(text.includes('fog') || text.includes('visibility')) return 'fog';
  if(text.includes('smoke') || text.includes('fire')) return 'fire';
  return 'general';
}

function visibleRouteHazardPoints(points, summary){
  points=points||[];
  if(!points.length) return [];

  const selected=[];
  const add=(p, reason)=>{
    if(!p) return;
    const key=(p.index||'')+'|'+p.lat+'|'+p.lon;
    if(selected.some(x=>x._key===key)) return;
    selected.push({...p,_key:key,_markerReason:reason});
  };

  add(points[0], 'Departure');
  add(summary&&summary.worstPoint, 'Highest concern');
  add(points[points.length-1], 'Destination');

  const seenTypes={};
  for(const p of points){
    const r=(p&&p.risk)||{};
    if((r.score||0)<40) continue;
    const type=routeHazardKey(p);
    if(seenTypes[type]) continue;
    seenTypes[type]=true;
    add(p, 'Route concern');
  }

  return selected.slice(0,6);
}

function routeHazardIcon(point){
  const r=(point&&point.risk)||{};
  const text=((point&&point.explanation)||''+' '+(r.condition||'')+' '+(r.reasons||[]).join(' ')).toLowerCase();

  let icon='⚠️';
  if(text.includes('lightning') || text.includes('thunder')) icon='⚡';
  else if(text.includes('tornado')) icon='🌪';
  else if(text.includes('flood')) icon='🌊';
  else if(text.includes('rain') || text.includes('shower')) icon='🌧';
  else if(text.includes('snow') || text.includes('ice') || text.includes('sleet')) icon='🧊';
  else if(text.includes('wind') || text.includes('gust')) icon='💨';
  else if(text.includes('heat') || text.includes('hot')) icon='🌡️';
  else if(text.includes('fog') || text.includes('visibility')) icon='🌫️';
  else if(text.includes('smoke') || text.includes('fire')) icon='🔥';

  return L.divIcon({
    className:'watchmanRouteHazardIcon',
    html:'<div style="background:#111827;color:#fff;border:3px solid #d9b82f;border-radius:999px;width:38px;height:38px;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:20px;box-shadow:0 3px 12px rgba(0,0,0,.45)">'+icon+'</div>',
    iconSize:[38,38],
    iconAnchor:[19,19],
    popupAnchor:[0,-19]
  });
}

function safetyIcon(place){
  const kind=(place.kind||'').toLowerCase();
  let label='S';
  if(kind.includes('police')) label='🛡';
  else if(kind.includes('hospital')) label='🏥';
  

  return L.divIcon({
    className:'watchmanSafetyIcon',
    html:'<div style="background:#111827;color:#fff;border:3px solid #d9b82f;border-radius:999px;width:34px;height:34px;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:17px;box-shadow:0 2px 10px rgba(0,0,0,.45)">'+label+'</div>',
    iconSize:[34,34],
    iconAnchor:[17,17],
    popupAnchor:[0,-17]
  });
}

async function loadWatchmanSafetyAlongRoute(){
  if(!watchmanRadarMap || !watchmanNavigationData) return;

  clearWatchmanSafetyLayer();

  const pts=(watchmanNavigationData.weatherPoints||[]);
  const sample=pts.filter((p,i)=>i===0 || i===pts.length-1 || i%2===0);

  const seen={};

  for(const p of sample){
    try{
      const data=await fetch('/api/watchman/safety-layer?lat='+encodeURIComponent(p.lat)+'&lon='+encodeURIComponent(p.lon)+'&radius=12000',{cache:'no-store'}).then(r=>r.json());
      if(!data.ok) continue;

      for(const place of data.places||[]){
        if(!(place.kind||'').includes('police') && !(place.kind||'').includes('hospital')) continue;
        const key=(place.kind||'')+'|'+(place.name||'')+'|'+Math.round(place.lat*10000)+'|'+Math.round(place.lon*10000);
        if(seen[key]) continue;
        seen[key]=true;

        const marker=L.marker([place.lat,place.lon],{icon:safetyIcon(place)}).addTo(watchmanRadarMap);
        marker.bindPopup(
          '<strong>'+safe(place.label)+'</strong><br>'+
          safe(place.name)+'<br>'+
          '<small>Public safety location along or near the route. Not police tracking.</small>'
        );
        watchmanSafetyMarkers.push(marker);
      }
    }catch(e){}
  }
}


function nearestUpcomingStep(lat,lon){
  const steps=(watchmanNavigationData&&watchmanNavigationData.route&&watchmanNavigationData.route.steps)||[];
  let best=null;
  for(let i=0;i<steps.length;i++){
    const st=steps[i];
    if(st.lat==null||st.lon==null||watchmanSpokenSteps[i]) continue;
    const mi=milesBetween(lat,lon,st.lat,st.lon);
    if(!best || mi<best.mi) best={index:i,step:st,mi:mi};
  }
  return best;
}

function nearestWeatherAhead(lat,lon){
  const pts=(watchmanNavigationData&&watchmanNavigationData.weatherPoints)||[];
  let best=null;
  for(let i=0;i<pts.length;i++){
    const p=pts[i], r=p.risk||{};
    const mi=milesBetween(lat,lon,p.lat,p.lon);
    if((r.score||0)<40) continue;
    if(!best || mi<best.mi) best={index:i,point:p,mi:mi};
  }
  return best;
}

function updateWatchmanDrivePanel(lat,lon,speedMph=null,speedLimit=null){
  const box=document.getElementById('watchmanNavBox');
  if(!box || !watchmanNavigationData) return;

  const next=nearestUpcomingStep(lat,lon);
  const wx=nearestWeatherAhead(lat,lon);
  const summary=watchmanNavigationData.summary||{};
  const route=watchmanNavigationData.route||{};

  const nextText=next
    ? safe(next.step.instruction)+' · '+Math.round(next.mi*10)/10+' mi'
    : 'No upcoming turn found';

  const wxText=wx
    ? 'Mile '+safe(wx.point.mile)+' · '+safe((wx.point.risk||{}).verdict)+' '+safe((wx.point.risk||{}).score)+' · '+safe(wx.point.explanation)
    : 'No elevated weather risk ahead on sampled route points.';

  const speedText=(speedMph===null||speedMph===undefined) ? 'Speed unavailable' : (speedMph+' mph');
  const limitText=(speedLimit&&speedLimit.mph!==null&&speedLimit.mph!==undefined) ? (speedLimit.mph+' mph') : 'Speed limit unavailable';
  const roadText=(speedLimit&&speedLimit.road) ? (' · '+safe(speedLimit.road)) : '';

  box.innerHTML=
    '<strong>LIVE WATCHMAN DRIVE MODE</strong><br>'+
    '<strong>'+routeStatusLabel(summary.verdict)+'</strong><br>'+
    'Trip: '+safe(route.distanceMiles)+' mi · ETA '+formatRouteMinutes(route.durationMinutes)+'<br>'+
    '<strong>Speed</strong><br>'+speedText+' / '+limitText+roadText+'<br>'+
    '<hr>'+
    '<strong>Next turn</strong><br>'+nextText+'<br>'+
    '<strong>Weather ahead</strong><br>'+wxText;
}


function startWatchmanVoiceNavigation(){
  const box=document.getElementById('watchmanNavBox');
  if(!watchmanNavigationData){box.innerText='Plan a route first.';return;}
  if(watchmanNavigationWatchId){navigator.geolocation.clearWatch(watchmanNavigationWatchId);}
  watchmanSpeak('Watchman navigation started. I will call out turns and weather risk ahead.');
  if(watchmanDrivePanelTimer){clearInterval(watchmanDrivePanelTimer);watchmanDrivePanelTimer=null;}
  watchmanNavigationWatchId=navigator.geolocation.watchPosition(function(pos){
    const lat=pos.coords.latitude, lon=pos.coords.longitude;
    const speedMph=gpsSpeedMph(pos);
    updateWatchmanDrivePanel(lat,lon,speedMph,watchmanLastSpeedLimit);
    refreshWatchmanSpeedLimit(lat,lon).then(limit=>updateWatchmanDrivePanel(lat,lon,speedMph,limit));
    const steps=(watchmanNavigationData.route&&watchmanNavigationData.route.steps)||[];
    const weather=watchmanNavigationData.weatherPoints||[];

    for(let i=0;i<steps.length;i++){
      const st=steps[i];
      if(st.lat==null||st.lon==null||watchmanSpokenSteps[i]) continue;
      const mi=milesBetween(lat,lon,st.lat,st.lon);
      if(mi<=0.25){
        watchmanSpokenSteps[i]=true;
        watchmanSpeak('In about a quarter mile, '+st.instruction);
        break;
      }
      if(mi<=0.75 && !watchmanSpokenSteps['soon'+i]){
        watchmanSpokenSteps['soon'+i]=true;
        watchmanSpeak('Coming up, '+st.instruction);
        break;
      }
    }

    for(let i=0;i<weather.length;i++){
      const p=weather[i], r=p.risk||{};
      if(watchmanSpokenWeather[i]) continue;
      const mi=milesBetween(lat,lon,p.lat,p.lon);
      if(mi<=5 && (r.score||0)>=40){
        watchmanSpokenWeather[i]=true;
        watchmanSpeak('Watchman weather ahead. In about '+Math.round(mi)+' miles, route risk is '+r.verdict+'. '+(p.explanation||'Use caution.'));
        break;
      }
    }
  }, function(){
    box.innerText='Navigation GPS tracking failed.';
  }, {enableHighAccuracy:true,maximumAge:10000,timeout:15000});
}

function stopWatchmanVoiceNavigation(){
  if(watchmanNavigationWatchId){
    navigator.geolocation.clearWatch(watchmanNavigationWatchId);
    watchmanNavigationWatchId=null;
  }
  if(watchmanDrivePanelTimer){
    clearInterval(watchmanDrivePanelTimer);
    watchmanDrivePanelTimer=null;
  }
  watchmanSpeak('Watchman navigation stopped.');
}

async function initWatchmanRadarMap(place, lat, lon){
  const node=document.getElementById('radarMap');
  const note=document.getElementById('radarMapNote');
  if(!node || !window.L) return;

  if(!watchmanRadarMap){
    watchmanRadarMap=L.map('radarMap').setView([lat, lon], 8);
    window.watchmanRadarMap=watchmanRadarMap;

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 12,
      attribution: '&copy; OpenStreetMap'
    }).addTo(watchmanRadarMap);

    try{
      const rv=await fetch('https://api.rainviewer.com/public/weather-maps.json', {cache:'no-store'}).then(r=>r.json());
      const latest=(rv.radar && rv.radar.past && rv.radar.past.length) ? rv.radar.past[rv.radar.past.length-1] : null;
      if(latest && latest.path){
        L.tileLayer('https://tilecache.rainviewer.com'+latest.path+'/256/{z}/{x}/{y}/2/1_1.png', {
          opacity: .65,
          attribution: 'RainViewer'
        }).addTo(watchmanRadarMap);
      }
    }catch(e){}
  } else {
    watchmanRadarMap.setView([lat, lon], 8);
  }

  for(const layer of watchmanRadarLayers){
    try{ watchmanRadarMap.removeLayer(layer); }catch(e){}
  }
  watchmanRadarLayers=[];

  L.marker([lat, lon]).addTo(watchmanRadarMap).bindPopup(`<strong>${safe(place)}</strong><br>Watched location`);

  try{
    const url='/api/watchman/radar-map/intelligence?place=' + encodeURIComponent(place);
    const payload=await fetch(url, {cache:'no-store'}).then(r=>r.json());
    const intel=payload.intelligence || {};
    const features=intel.features || [];

    for(const f of features){
      const layer=L.geoJSON(f, {
        style: polygonStyle,
        onEachFeature: function(feature, layer){
          layer.bindPopup(polygonPopup(feature));
        }
      }).addTo(watchmanRadarMap);
      watchmanRadarLayers.push(layer);
    }

    if(note){
      const c=intel.counts || {};
      note.innerText=`Watchman map intelligence: ${safe(c.nwsAlertPolygons,0)} official NWS polygon(s), ${safe(c.nwsAlertFallbackPolygons,0)} NWS fallback polygon(s), ${safe(c.stormCellProxyPolygons,0)} storm proxy polygon(s), ${safe(c.stormProjectionPolygons,0)} projection polygon(s).`;
    }
  }catch(e){
    if(note) note.innerText='Radar map loaded. Watchman polygon intelligence failed to load.';
  }
}





async function loadAdvancedNwsPolygons(place){
  try{
    const payload=await fetch('/api/watchman/nws-polygons/advanced?place=' + encodeURIComponent(place), {cache:'no-store'}).then(r=>r.json());
    const r=payload.result || {};
    const node=document.getElementById('advancedNwsBox');
    if(node){
      const c=r.counts || {};
      node.innerHTML=`
        <div class="row"><span>Total</span><strong>${safe(c.total,0)}</strong></div>
        <div class="row"><span>Official</span><strong>${safe(c.official,0)}</strong></div>
        <div class="row"><span>Fallback</span><strong>${safe(c.fallback,0)}</strong></div>
        <div class="row"><span>Warnings</span><strong>${safe(c.warnings,0)}</strong></div>
        <div class="row"><span>Watches</span><strong>${safe(c.watches,0)}</strong></div>
        <div class="row"><span>Advisories</span><strong>${safe(c.advisories,0)}</strong></div>
        <div class="row"><span>Flood</span><strong>${safe(c.flood,0)}</strong></div>
        <p>${safe(r.note)}</p>
      `;
    }

    if(window.watchmanRadarMap && window.L && r.features){
      for(const f of r.features){
        const p=(f && f.properties) || {};
        const layer=L.geoJSON(f, {
          style: function(feature){
            const p=(feature && feature.properties) || {};
            return {
              color: p.color || '#ffd600',
              weight: p.layerGroup === 'warning' ? 4 : 2,
              dashArray: p.fallback ? '8,6' : null,
              fillColor: p.color || '#ffd600',
              fillOpacity: p.fillOpacity || .15
            };
          },
          onEachFeature: function(feature, layer){
            const p=(feature && feature.properties) || {};
            layer.bindPopup(`
              <strong>${safe(p.event || 'NWS Alert')}</strong><br>
              Group: ${safe(p.layerGroup)}<br>
              Severity: ${safe(p.severity)}<br>
              Urgency: ${safe(p.urgency)}<br>
              Certainty: ${safe(p.certainty)}<br>
              Sender: ${safe(p.sender)}<br>
              Areas: ${safe(p.areaDesc)}<br>
              Effective: ${safe(p.effective)}<br>
              Expires: ${safe(p.expires)}<br>
              Fallback polygon: ${safe(p.fallback)}
            `);
          }
        }).addTo(window.watchmanRadarMap);

        layer.watchmanLayerGroup=p.layerGroup || 'other';
        layer.watchmanAdvancedNws=true;

        if(p.flashing){
          try{
            layer.eachLayer(function(l){
              if(l._path) l._path.classList.add('nwsFlash');
            });
          }catch(e){}
        }

        if(window.watchmanRadarLayers) window.watchmanRadarLayers.push(layer);
      }
    }
  }catch(e){}
}

function toggleWatchmanLayerGroup(group, checked){
  if(!window.watchmanRadarLayers) return;
  for(const layer of window.watchmanRadarLayers){
    if(layer && layer.watchmanAdvancedNws && layer.watchmanLayerGroup === group){
      try{
        if(checked){
          if(window.watchmanRadarMap && !window.watchmanRadarMap.hasLayer(layer)) layer.addTo(window.watchmanRadarMap);
        }else{
          if(window.watchmanRadarMap && window.watchmanRadarMap.hasLayer(layer)) window.watchmanRadarMap.removeLayer(layer);
        }
      }catch(e){}
    }
  }
}

async function loadLightningLayer(place){
  try{
    const payload=await fetch('/api/watchman/lightning?place=' + encodeURIComponent(place), {cache:'no-store'}).then(r=>r.json());
    const r=payload.result || {};
    const node=document.getElementById('lightningBox');
    if(!node) return;

    node.innerHTML=`
      <div class="row"><span>Risk</span><strong>${safe(r.risk)}</strong></div>
      <div class="row"><span>Score</span><strong>${safe(r.score)}/100</strong></div>
      <div class="row"><span>Thunder Signal</span><strong>${safe(r.thunderSignal)}</strong></div>
      <div class="row"><span>Bearing</span><strong>${safe(r.bearingDegrees)}°</strong></div>
      <div class="row"><span>Speed</span><strong>${safe(r.speedMph)} mph</strong></div>
      <div class="row"><span>Map Features</span><strong>${safe(r.featureCount)}</strong></div>
      <p>${safe(r.note)}</p>
    `;

    if(window.watchmanRadarMap && window.L && r.features){
      for(const f of r.features){
        const layer=L.geoJSON(f, {
          style: function(feature){
            const p=(feature && feature.properties) || {};
            return {
              color: p.color || '#ffd600',
              weight: 2,
              dashArray: p.kind === 'watchman_lightning_projection_zone' ? '5,8' : '2,4',
              fillColor: p.color || '#ffd600',
              fillOpacity: p.kind === 'watchman_lightning_projection_zone' ? 0.07 : 0.13
            };
          },
          onEachFeature: function(feature, layer){
            const p=(feature && feature.properties) || {};
            layer.bindPopup(`
              <strong>${safe(p.title || 'Lightning Risk')}</strong><br>
              Risk: ${safe(p.risk)}<br>
              Score: ${safe(p.score)}/100<br>
              Projection: +${safe(p.projectionMinutes,0)} min<br>
              Bearing: ${safe(p.bearingDegrees)}°<br>
              Speed: ${safe(p.speedMph)} mph<br>
              ${safe(p.note)}
            `);
          }
        }).addTo(window.watchmanRadarMap);

        if(window.watchmanRadarLayers) window.watchmanRadarLayers.push(layer);
      }
    }
  }catch(e){}
}






let gpsWatchId=null;
let gpsWatchLastLat=null;
let gpsWatchLastLon=null;
let gpsWatchLastUpdate=0;

function gpsDistanceFeet(lat1, lon1, lat2, lon2){
  if(lat1 === null || lon1 === null || lat2 === null || lon2 === null) return 999999;
  const R=20902231;
  const p1=lat1*Math.PI/180;
  const p2=lat2*Math.PI/180;
  const dp=(lat2-lat1)*Math.PI/180;
  const dl=(lon2-lon1)*Math.PI/180;
  const a=Math.sin(dp/2)*Math.sin(dp/2)+Math.cos(p1)*Math.cos(p2)*Math.sin(dl/2)*Math.sin(dl/2);
  return R*2*Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
}

async function sendGpsWatchUpdate(lat, lon, reason){
  const box=document.getElementById('continuousGpsWatchBox');
  if(!box) return;

  const payload=await fetch(
    '/api/watchman/gps-watch/update?lat=' +
    encodeURIComponent(lat) +
    '&lon=' +
    encodeURIComponent(lon) +
    '&label=' +
    encodeURIComponent('Phone GPS'),
    {cache:'no-store'}
  ).then(r=>r.json());

  const s=payload.summary || {};
  const r=s.lastResult || {};
  const d=r.decision || {};
  const i=r.impact || {};

  box.innerHTML=`
    <div class="row"><span>Status</span><strong>${safe(s.enabled)}</strong></div>
    <div class="row"><span>Mode</span><strong>Event-driven GPS</strong></div>
    <div class="row"><span>Reason</span><strong>${safe(reason || 'gps update')}</strong></div>
    <div class="row"><span>Updates</span><strong>${safe(s.updates,0)}</strong></div>
    <div class="row"><span>GPS</span><strong>${safe(lat.toFixed(5))}, ${safe(lon.toFixed(5))}</strong></div>
    <div class="row"><span>Decision</span><strong>${safe(d.decision)}</strong></div>
    <div class="row"><span>Severity</span><strong>${safe(d.severity)}</strong></div>
    <div class="row"><span>Score</span><strong>${safe(d.score)}/100</strong></div>
    <div class="row"><span>Impact</span><strong>${safe(i.highestImpact)}</strong></div>
    ${(d.recommendations || []).map(x=>`<div class="row"><span>Action</span><strong>${safe(x)}</strong></div>`).join('')}
    <p>${safe(s.note)}</p>
  `;
}

function startContinuousGpsWatch(){
  const box=document.getElementById('continuousGpsWatchBox');
  if(!box) return;

  if(!navigator.geolocation){
    box.innerHTML='<p>Browser GPS is not available.</p>';
    return;
  }

  if(gpsWatchId !== null){
    navigator.geolocation.clearWatch(gpsWatchId);
    gpsWatchId=null;
  }

  box.innerHTML='<p>Starting event-driven GPS watch...</p>';

  gpsWatchId=navigator.geolocation.watchPosition(async function(pos){
    const lat=pos.coords.latitude;
    const lon=pos.coords.longitude;
    const now=Date.now();

    const movedFeet=gpsDistanceFeet(gpsWatchLastLat, gpsWatchLastLon, lat, lon);
    const elapsedMs=now-gpsWatchLastUpdate;

    if(gpsWatchLastUpdate && movedFeet < 300 && elapsedMs < 120000){
      box.innerHTML=`
        <div class="row"><span>Status</span><strong>true</strong></div>
        <div class="row"><span>Mode</span><strong>Event-driven GPS</strong></div>
        <div class="row"><span>GPS</span><strong>${safe(lat.toFixed(5))}, ${safe(lon.toFixed(5))}</strong></div>
        <div class="row"><span>Moved</span><strong>${safe(Math.round(movedFeet))} ft</strong></div>
        <p>GPS watch is active. No new Watchman scan needed until movement exceeds 300 ft or 2 minutes pass.</p>
      `;
      return;
    }

    gpsWatchLastLat=lat;
    gpsWatchLastLon=lon;
    gpsWatchLastUpdate=now;

    await sendGpsWatchUpdate(lat, lon, movedFeet >= 300 ? 'location changed' : 'timed refresh');
  }, function(err){
    box.innerHTML='<p>GPS permission failed or was denied.</p>';
  }, {
    enableHighAccuracy:true,
    maximumAge:5000,
    timeout:15000
  });
}

async function stopContinuousGpsWatch(){
  if(gpsWatchId !== null){
    navigator.geolocation.clearWatch(gpsWatchId);
    gpsWatchId=null;
  }

  gpsWatchLastLat=null;
  gpsWatchLastLon=null;
  gpsWatchLastUpdate=0;

  const box=document.getElementById('continuousGpsWatchBox');
  const payload=await fetch('/api/watchman/gps-watch/stop', {cache:'no-store'}).then(r=>r.json());
  const s=payload.summary || {};

  if(box){
    box.innerHTML=`
      <div class="row"><span>Status</span><strong>${safe(s.enabled)}</strong></div>
      <div class="row"><span>Updates</span><strong>${safe(s.updates,0)}</strong></div>
      <p>Event-driven GPS watch stopped.</p>
    `;
  }
}

async function loadGpsImpactFromBrowser(){
  const box=document.getElementById('gpsImpactBox');
  if(!box) return;

  if(!navigator.geolocation){
    box.innerHTML='<p>Browser GPS is not available.</p>';
    return;
  }

  box.innerHTML='<p>Requesting GPS location...</p>';

  navigator.geolocation.getCurrentPosition(async function(pos){
    const lat=pos.coords.latitude;
    const lon=pos.coords.longitude;

    const payload=await fetch('/api/watchman/gps-impact?lat=' + encodeURIComponent(lat) + '&lon=' + encodeURIComponent(lon) + '&label=' + encodeURIComponent('Phone GPS'), {cache:'no-store'}).then(r=>r.json());
    const r=payload.result || {};
    const d=r.decision || {};
    const i=r.impact || {};

    box.innerHTML=`
      <div class="row"><span>GPS</span><strong>${safe(lat.toFixed(5))}, ${safe(lon.toFixed(5))}</strong></div>
      <div class="row"><span>Decision</span><strong>${safe(d.decision)}</strong></div>
      <div class="row"><span>Severity</span><strong>${safe(d.severity)}</strong></div>
      <div class="row"><span>Score</span><strong>${safe(d.score)}/100</strong></div>
      <div class="row"><span>Impact</span><strong>${safe(i.highestImpact)}</strong></div>
      ${(d.recommendations || []).map(x=>`<div class="row"><span>Action</span><strong>${safe(x)}</strong></div>`).join('')}
      <p>${safe(r.note)}</p>
    `;
  }, function(err){
    box.innerHTML='<p>GPS permission failed or was denied.</p>';
  }, {enableHighAccuracy:true, timeout:10000, maximumAge:60000});
}

async function loadWatchmanDecision(place){
  try{
    const payload=await fetch('/api/watchman/decision?place=' + encodeURIComponent(place), {cache:'no-store'}).then(r=>r.json());
    const r=payload.result || {};
    const node=document.getElementById('decisionBox');
    if(!node) return;

    node.innerHTML=`
      <div class="row"><span>Decision</span><strong>${safe(r.decision)}</strong></div>
      <div class="row"><span>Severity</span><strong>${safe(r.severity)}</strong></div>
      <div class="row"><span>Score</span><strong>${safe(r.decisionScore)}/100</strong></div>
      <div class="row"><span>Confidence</span><strong>${safe(r.confidence)}%</strong></div>
      <div class="row"><span>Primary Threat</span><strong>${safe(r.primaryThreat)}</strong></div>
      ${(r.recommendations || []).map(x=>`<div class="row"><span>Action</span><strong>${safe(x)}</strong></div>`).join('')}
      ${(r.reasons || []).map(x=>`<div class="row"><span>Reason</span><strong>${safe(x)}</strong></div>`).join('')}
    `;
  }catch(e){}
}

async function loadImpactForecast(place){
  try{
    const payload=await fetch('/api/watchman/impact-forecast?place=' + encodeURIComponent(place), {cache:'no-store'}).then(r=>r.json());
    const r=payload.result || {};
    const node=document.getElementById('impactForecastBox');
    if(!node) return;

    node.innerHTML=`
      <div class="row"><span>Highest Impact</span><strong>${safe(r.highestImpact)}</strong></div>
      <div class="row"><span>Tracked Cells</span><strong>${safe(r.trackedCells,0)}</strong></div>
      <div class="row"><span>Impact Zones</span><strong>${safe(r.featureCount,0)}</strong></div>
      ${(r.impacts || []).slice(0,6).map(i=>`
        <div class="row"><span>${safe(i.cellId)} +${safe(i.minutes)} min</span><strong>${safe(i.impactLevel)} ${safe(i.distanceFromPlaceMiles)} mi</strong></div>
      `).join('')}
      <p>${safe(r.note)}</p>
    `;

    if(window.watchmanRadarMap && window.L && r.features){
      for(const f of r.features){
        const layer=L.geoJSON(f, {
          style: function(feature){
            const p=(feature && feature.properties) || {};
            return {
              color: p.color || '#ff9800',
              weight: p.impactLevel === 'high' ? 4 : 2,
              dashArray: '3,7',
              fillColor: p.color || '#ff9800',
              fillOpacity: p.impactLevel === 'high' ? .18 : .10
            };
          },
          onEachFeature: function(feature, layer){
            const p=(feature && feature.properties) || {};
            layer.bindPopup(`
              <strong>${safe(p.title || 'Impact Forecast')}</strong><br>
              Impact: ${safe(p.impactLevel)}<br>
              Projection: +${safe(p.projectionMinutes)} min<br>
              Distance: ${safe(p.distanceFromPlaceMiles)} mi<br>
              Confidence: ${safe(p.confidence)}%<br>
              Speed: ${safe(p.speedMph)} mph<br>
              Bearing: ${safe(p.bearingDegrees)}°<br>
              Trend: ${safe(p.strengthTrend)}<br>
              ${safe(p.recommendation)}
            `);
          }
        }).addTo(window.watchmanRadarMap);

        if(window.watchmanRadarLayers) window.watchmanRadarLayers.push(layer);
      }
    }
  }catch(e){}
}

async function loadRadarMultiCell(place){
  try{
    const payload=await fetch('/api/watchman/radar-multi-cell?place=' + encodeURIComponent(place), {cache:'no-store'}).then(r=>r.json());
    const r=payload.result || {};
    const node=document.getElementById('radarMultiCellBox');
    if(!node) return;

    node.innerHTML=`
      <div class="row"><span>Cells Found</span><strong>${safe(r.cellCount,0)}</strong></div>
      <div class="row"><span>Tracked</span><strong>${safe(r.trackedCount,0)}</strong></div>
      ${(r.tracks || []).slice(0,5).map(t=>`
        <div class="row"><span>${safe(t.cellId)}</span><strong>${safe(t.status)} ${safe(t.speedMph || '')} mph ${safe(t.strengthTrend || '')}</strong></div>
      `).join('')}
      <p>${safe(r.note)}</p>
    `;
  }catch(e){}
}

async function loadRadarCellTracker(place){
  try{
    const payload=await fetch('/api/watchman/radar-cell-tracker?place=' + encodeURIComponent(place), {cache:'no-store'}).then(r=>r.json());
    const r=payload.result || {};
    const c=r.cell || {};
    const node=document.getElementById('radarCellTrackerBox');
    if(!node) return;

    if(!r.detected){
      node.innerHTML=`
        <div class="row"><span>Detected</span><strong>false</strong></div>
        <div class="row"><span>Reason</span><strong>${safe(r.reason || r.error || 'No radar cell centroid detected')}</strong></div>
        <p>${safe(r.note || '')}</p>
      `;
      return;
    }

    node.innerHTML=`
      <div class="row"><span>Detected</span><strong>true</strong></div>
      <div class="row"><span>Bearing</span><strong>${safe(c.bearingDegrees)}°</strong></div>
      <div class="row"><span>Measured Speed</span><strong>${safe(c.speedMph)} mph</strong></div>
      <div class="row"><span>Moved</span><strong>${safe(c.distanceMovedMiles)} mi</strong></div>
      <div class="row"><span>Frame Gap</span><strong>${safe(c.minutesBetweenFrames)} min</strong></div>
      <div class="row"><span>Confidence</span><strong>${safe(c.confidence)}%</strong></div>
      <div class="row"><span>Current Cell</span><strong>${safe(c.current?.lat)}, ${safe(c.current?.lon)}</strong></div>
      <p>${safe(r.note)}</p>
    `;
  }catch(e){}
}

async function loadRadarMotion(place){
  try{
    const payload=await fetch('/api/watchman/radar-motion?place=' + encodeURIComponent(place), {cache:'no-store'}).then(r=>r.json());
    const r=payload.result || {};
    const node=document.getElementById('radarMotionBox');
    if(!node) return;

    node.innerHTML=`
      <div class="row"><span>Bearing</span><strong>${safe(r.bearingDegrees)}°</strong></div>
      <div class="row"><span>Speed</span><strong>${safe(r.speedMph)} mph</strong></div>
      <div class="row"><span>Storm Signal</span><strong>${safe(r.stormSignal)}</strong></div>
      <div class="row"><span>Confidence</span><strong>${safe(r.confidence)}%</strong></div>
      <div class="row"><span>RainViewer Frames</span><strong>${safe((r.rainviewer?.frames || []).length,0)}</strong></div>
      ${(r.projections || []).map(p=>`<div class="row"><span>+${safe(p.minutes)} min</span><strong>${safe(p.lat)}, ${safe(p.lon)}</strong></div>`).join('')}
      <p>${safe(r.note)}</p>
    `;
  }catch(e){}
}


async function loadFlagshipStatus(){
  const node=document.getElementById('flagshipStatusBox');
  if(!node) return;

  const gps=await fetch('/api/watchman/gps-watch/status', {cache:'no-store'}).then(r=>r.json());
  const risk=await fetch('/api/watchman/gps-risk/status', {cache:'no-store'}).then(r=>r.json());
  const notes=await fetch('/api/watchman/notifications?unread=1', {cache:'no-store'}).then(r=>r.json());

  const gs=(gps.summary || {});
  const gr=(gs.riskChange || {});
  const ns=(notes.summary || {});

  node.innerHTML=`
    <div class="row"><span>GPS Watch</span><strong>${safe(gs.enabled)}</strong></div>
    <div class="row"><span>GPS Updates</span><strong>${safe(gs.updates,0)}</strong></div>
    <div class="row"><span>Risk Change</span><strong>${safe(gr.changed)}</strong></div>
    <div class="row"><span>Escalated</span><strong>${safe(gr.escalated)}</strong></div>
    <div class="row"><span>Unread Notifications</span><strong>${safe(ns.unread,0)}</strong></div>
    <p>Flagship UI Run: GPS watch, risk-change notifications, decision engine, radar intelligence, and alert pipeline are connected.</p>
  `;
}




async function loadWatchmanLiveTimeline(){
  const place=document.getElementById('place').value || 'Jasper, Alabama';
  const node=document.getElementById('watchmanLiveTimelineBox');
  if(!node) return;

  node.innerHTML='<p>Building Watchman live timeline...</p>';

  const payload=await fetch('/api/watchman/live-timeline?place=' + encodeURIComponent(place), {cache:'no-store'}).then(r=>r.json());
  const r=payload.result || {};
  const events=r.events || [];
  const hours=r.hours || [];

  node.innerHTML=`
    <h3>Live events</h3>
    ${events.map(e=>`
      <div class="day">
        <strong>${publicText(e.title)} · ${publicText(e.time)}</strong>
        <p>${publicText(e.detail)}</p>
      </div>
    `).join('')}
    <h3>Next hours</h3>
    ${hours.slice(0,8).map(h=>`
      <div class="row">
        <span>${publicText(h.time)}</span>
        <strong>${safe(h.risk)}/100 · ${publicText(h.forecast)} · ${safe(h.rainChance)}%</strong>
      </div>
    `).join('')}
  `;
}

async function runNotificationDiagnostic(){
  const place=document.getElementById('place').value || 'Jasper, Alabama';
  const node=document.getElementById('watchmanNotificationDiagnosticBox');
  if(!node) return;

  node.innerHTML='<p>Checking notification path...</p>';

  const payload=await fetch('/api/watchman/notification-diagnostic?place=' + encodeURIComponent(place), {cache:'no-store'}).then(r=>r.json());

  node.innerHTML=`
    <div class="row"><span>Active Alerts</span><strong>${safe(payload.activeAlerts)}</strong></div>
    <div class="row"><span>Threat</span><strong>${publicText(payload.threatLevel)} · ${safe(payload.threatScore)}/100</strong></div>
    ${(payload.likelyReasons || []).map(x=>`<div class="row"><span>Reason</span><strong>${publicText(x)}</strong></div>`).join('')}
  `;
}

async function runMissionTimeMachine(mission){
  const place=document.getElementById('place').value || 'Jasper, Alabama';
  const node=document.getElementById('missionTimeMachineBox');
  if(!node) return;

  node.innerHTML='<p>Finding best mission window...</p>';

  const payload=await fetch('/api/watchman/mission-time-machine?place=' + encodeURIComponent(place) + '&mission=' + encodeURIComponent(mission), {cache:'no-store'}).then(r=>r.json());
  const r=payload.result || {};

  node.innerHTML=`
    <div class="row"><span>Mission</span><strong>${safe(r.missionLabel)}</strong></div>
    <div class="row"><span>Verdict</span><strong>${safe(r.verdict)}</strong></div>
    <div class="row"><span>Best Window</span><strong>${safe(r.bestWindow)}</strong></div>
    <h3>Best Hours</h3>
    ${(r.bestHours || []).map(h=>`
      <div class="day">
        <strong>${safe(h.time)} · ${safe(h.score)}/100</strong>
        <div class="row"><span>Temp</span><strong>${safe(h.temperature)}°</strong></div>
        <div class="row"><span>Rain</span><strong>${safe(h.precipChance)}%</strong></div>
        <div class="row"><span>Forecast</span><strong>${safe(h.forecast)}</strong></div>
        <div class="row"><span>Wind</span><strong>${safe(h.wind)}</strong></div>
        ${(h.reasons || []).map(x=>`<div class="row"><span>Reason</span><strong>${safe(x)}</strong></div>`).join('')}
      </div>
    `).join('')}
  `;
}

async function runWatchmanMission(mission){
  const place=document.getElementById('place').value || 'Jasper, Alabama';
  const node=document.getElementById('missionCenterBox');
  if(!node) return;

  node.innerHTML='<p>Running mission planner...</p>';

  const payload=await fetch('/api/watchman/mission?place=' + encodeURIComponent(place) + '&mission=' + encodeURIComponent(mission), {cache:'no-store'}).then(r=>r.json());
  const m=payload.mission || {};
  const e=payload.explanation || {};
  const factors=e.factors || [];

  node.innerHTML=`
    <div class="row"><span>Mission</span><strong>${safe(m.missionLabel)}</strong></div>
    <div class="row"><span>Verdict</span><strong><span class="verdictBadge verdict-${String(m.verdict || '').toLowerCase()}">${safe(m.verdict)}</span></strong></div>
    <div class="row"><span>Mission Score</span><strong>${safe(m.score)}/100</strong></div>
    <p>${safe(m.recommendation)}</p>
    ${(m.reasons || []).map(x=>`<div class="row"><span>Reason</span><strong>${safe(x)}</strong></div>`).join('')}
    <h3>Why Watchman thinks this</h3>
    <div class="row"><span>Risk Level</span><strong>${safe(e.riskLevel)}</strong></div>
    <div class="row"><span>Explanation Score</span><strong>${safe(e.explanationScore)}/100</strong></div>
    ${factors.map(f=>`<div class="row"><span>${safe(f.label)}</span><strong>+${safe(f.points)} · ${safe(f.reason)}</strong></div>`).join('')}
    <h3>What would change this?</h3>
    ${(e.whatWouldChange || []).map(x=>`<div class="row"><span>Change</span><strong>${safe(x)}</strong></div>`).join('')}
  `;
}

async function loadWeatherMemory(){
  const place=document.getElementById('place').value || 'Jasper, Alabama';
  const node=document.getElementById('weatherMemoryBox');
  if(!node) return;

  const payload=await fetch('/api/watchman/weather-memory?place=' + encodeURIComponent(place), {cache:'no-store'}).then(r=>r.json());
  const s=payload.summary || {};
  const rows=s.timeline || [];

  node.innerHTML=`
    <div class="row"><span>Memory Records</span><strong>${safe(s.count,0)}</strong></div>
    ${(s.changes || []).map(x=>`<div class="row"><span>Change</span><strong>${safe(x)}</strong></div>`).join('')}
    ${rows.slice(-6).reverse().map(r=>`
      <div class="day">
        <strong>${safe(r.time)}</strong>
        <div class="row"><span>Threat</span><strong>${safe(r.threatLevel)} · ${safe(r.threatScore)}/100</strong></div>
        <div class="row"><span>Rain</span><strong>${safe(r.precipChance)}%</strong></div>
        <div class="row"><span>Alerts</span><strong>${safe(r.alertCount)}</strong></div>
      </div>
    `).join('')}
  `;
}


function getWatchmanProfile(){
  try{
    const raw=localStorage.getItem('watchmanProfile');
    if(raw) return JSON.parse(raw);
  }catch(e){}
  return {name:'Chap'};
}

function saveWatchmanProfile(){
  const name=(document.getElementById('watchmanProfileName')?.value || 'Chap').trim() || 'Chap';
  const profile={name:name};
  localStorage.setItem('watchmanProfile', JSON.stringify(profile));
  renderWatchmanProfile();
}

function renderWatchmanProfile(){
  const profile=getWatchmanProfile();
  const input=document.getElementById('watchmanProfileName');
  const label=document.getElementById('watchmanProfileGreeting');
  if(input) input.value=profile.name || 'Chap';
  if(label) label.innerText='Watchman will call you ' + (profile.name || 'Chap') + '.';
}

async function loadWeather(){
  const place=document.getElementById('place').value || 'Jasper, Alabama';
  const root=document.getElementById('app');
  root.innerHTML='<div class="card" style="margin-top:1rem">Running Watchman weather scan...</div>';

  try{
    const r=await fetch('/api/nws?place='+encodeURIComponent(place));
    const data=await r.json();
    if(!r.ok) throw new Error(data.error || 'NWS request failed');

    const w=data.watchman;
    const obs=data.observation || {};
    const first=data.forecast[0] || {};
    const alerts=data.alerts || [];

    root.innerHTML=`
      <div class="grid">
        <section class="card">
          <h2>${data.location.name}, ${data.location.admin1 || data.location.country}</h2>
          <div class="big">${safe(obs.temperatureF,'--')}°F</div>
          <h3>${safe(obs.text, first.shortForecast || 'Current conditions')}</h3>
          <div class="row"><span>Station</span><strong>${safe(obs.station)}</strong></div>
          <div class="row"><span>Dewpoint</span><strong>${safe(obs.dewpointF)}°F</strong></div>
          <div class="row"><span>Wind</span><strong>${safe(obs.windMph)} mph</strong></div>
          <div class="row"><span>Gust</span><strong>${safe(obs.gustMph)} mph</strong></div>
          <div class="row"><span>NWS Office</span><strong>${safe(data.nws.office)}</strong></div>
          <div class="row"><span>Grid</span><strong>${safe(data.nws.gridId)} ${safe(data.nws.gridX)},${safe(data.nws.gridY)}</strong></div>
        </section>

        <section class="card">
          <h2>Watchman Intelligence</h2>
          <span class="threat ${w.threatLevel}">${w.threatLevel} · ${w.threatScore}/100</span>
          <p>${w.briefing}</p>

          <div class="day" style="margin-top:.8rem">
            <strong>Watchman Briefing</strong>
            <p>${publicText(w.aiBriefing)}</p>
          </div>

          <div class="day" style="margin-top:.8rem">
            <strong>Biggest Risk</strong>
            <p>${publicText(w.aiWeatherNarrative) || safe(w.briefing) || 'No major risk detected.'}</p>
          </div>

          <div class="day" style="margin-top:.8rem">
            <strong>Storm / Arrival</strong>
            <p>${safe(w.streetLevelArrival?.rainEta) || safe(w.stormTracker?.estimatedArrival) || 'No clear arrival signal detected.'}</p>
            <p>${safe(w.streetLevelArrival?.lightningEta)}</p>
          </div>

          <div class="day" style="margin-top:.8rem">
            <strong>What Changed</strong>
            <p>${safe(w.whatChanged?.summary) || 'No previous scan comparison available.'}</p>
          </div>

          <details class="day" style="margin-top:.8rem">
            <summary><strong>Technical Details</strong></summary>
            <p><strong>Scanner:</strong> ${publicText(w.liveScanner?.refreshNote)}</p>
            <p><strong>Storm Signal:</strong> ${safe(w.liveStormIntelligence?.stormSignal)}</p>
            <p><strong>Heat Signal:</strong> ${safe(w.liveStormIntelligence?.heatSignal)}</p>
            <p><strong>Flood Signal:</strong> ${safe(w.liveStormIntelligence?.floodSignal)}</p>
            <p><strong>Storm Tracker:</strong> ${safe(w.stormTracker?.estimatedArrival)} · ${safe(w.stormTracker?.confidence)}%</p>
            <p><strong>Reasons:</strong> ${w.reasons.join(', ')}</p>
          </details>

          <div class="row"><span>Outdoor Index</span><strong>${w.outdoorIndex}/100</strong></div>
          <div class="row"><span>Travel Index</span><strong>${w.travelIndex}/100</strong></div>
          <div class="row"><span>Active Alerts</span><strong>${alerts.length}</strong></div>

        </section>
      </div>

      <section class="card ${alerts.length?'alert':''}" style="margin-top:1rem">
        <h2>Active NWS Alerts</h2>
        ${alerts.length ? alerts.map(a=>`
          <div class="day">
            <strong>${safe(a.event)}</strong>
            <p>${safe(a.headline)}</p>
            <div>Severity: ${safe(a.severity)} · Urgency: ${safe(a.urgency)} · Certainty: ${safe(a.certainty)}</div>
          </div>
        `).join('') : '<p>No active NWS alerts for this location.</p>'}
      </section>

      <section class="card" style="margin-top:1rem">
        <h2>Watchman Live Radar + Intelligence Polygons</h2>
        <div id="radarMap"></div>
        <div style="display:flex;gap:.5rem;flex-wrap:wrap;margin-top:.75rem">
          <input id="watchmanNavDestination" placeholder="Destination" style="flex:1;min-width:190px;text-align:center">
          <button onclick="planWatchmanNavigationRoute()">Plan Route</button>
          <button onclick="startWatchmanVoiceNavigation()">Start</button>
          <button onclick="stopWatchmanVoiceNavigation()">Stop</button>
        </div>
        <div id="watchmanNavBox" class="radarNote">Live radar stays on. Enter a destination to overlay a weather-aware driving route.</div>
        <div class="radarNote" id="radarMapNote">Live radar map with Watchman intelligence polygons.</div>
      </section>

      <section class="card" style="margin-top:1rem">
        <h2>NWS Forecast</h2>
        <div class="days">
          ${data.forecast.slice(0,7).map(d=>`
            <div class="day">
              <strong>${safe(d.name)}</strong>
              <p>${safe(d.shortForecast)}</p>
              <div>${safe(d.temperature)}°${safe(d.temperatureUnit)}</div>
              <small>${safe(d.detailedForecast)}</small>
            </div>
          `).join('')}
        </div>
      </section>

      <section class="card hourly" style="margin-top:1rem">
        <h2>Next 24 Hours</h2>
        ${data.hourly.map(h=>`
          <div class="row">
            <span>${timeLabel(h.startTime)}</span>
            <strong>${safe(h.temperature)}°${safe(h.temperatureUnit)} · ${safe(h.shortForecast)} · ${safe(h.windSpeed)}</strong>
          </div>
        `).join('')}
      </section>
    `;
      initWatchmanRadarMap(
        data.location.name || data.location.place || 'Current Location',
        data.location.latitude,
        data.location.longitude
      );
  }catch(e){
    root.innerHTML='<div class="card" style="margin-top:1rem;color:#ff9b9b;font-weight:900">'+e.message+'</div>';
  }
}
loadWeather();
</script>
<script src="/static/watchman_phone_push.js"></script>

<section class="watchman-card" id="watchman-gps-notifications-card">
  <h2>Watchman GPS Notifications</h2>
  <p>Enable current-location alerts so Watchman can warn your phone about meaningful weather risk near you, with your permission.</p>
  <button id="watchman-enable-gps-notifications" type="button">Enable current-location alerts</button>
  <p id="watchman-gps-notification-status">Location not enabled · notifications not enabled · last scan pending · last risk pending</p>
</section>
<script src="/static/watchman_current_device_gps.js"></script>




<script>
async function runWatchmanRoutePlanner(){
  const box=document.getElementById('watchmanRoutePlannerBox');
  const dest=(document.getElementById('watchmanRouteDestination')||{}).value || '';
  if(!dest.trim()){
    box.innerHTML='<p>Enter a destination first.</p>';
    return;
  }
  if(!navigator.geolocation){
    box.innerHTML='<p>GPS is not supported in this browser.</p>';
    return;
  }
  box.innerHTML='<p>Getting current GPS location...</p>';
  navigator.geolocation.getCurrentPosition(async function(pos){
    try{
      box.innerHTML='<p>Watchman is scanning weather along the route...</p>';
      const res=await fetch('/api/watchman/route-planner',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({
          originLat:pos.coords.latitude,
          originLon:pos.coords.longitude,
          destination:dest,
          samples:5
        })
      });
      const data=await res.json();
      if(!data.ok){
        box.innerHTML='<p>Route planner failed: '+(data.error||'unknown')+'</p>';
        return;
      }
      const s=data.summary||{};
      const worst=s.worstPoint||{};
      const risk=worst.risk||{};
      let rows=(data.points||[]).map(p=>{
        const r=p.risk||{};
        return '<div class="row"><span>Mile '+(p.mile||0)+' · '+(r.condition||'Weather checked')+'</span><strong>'+((r.verdict||'unknown')+' '+(r.score||0))+'</strong></div>';
      }).join('');
      box.innerHTML=
        '<div class="resultBox">'+
        '<h3>Route verdict: '+(s.verdict||'unknown')+'</h3>'+
        '<p>'+((s.recommendation)||'Route scan complete.')+'</p>'+
        '<div class="row"><span>Distance</span><strong>'+(s.distanceMiles||0)+' mi</strong></div>'+
        '<div class="row"><span>Worst point</span><strong>Mile '+(worst.mile||0)+' · '+(risk.score||0)+'</strong></div>'+
        rows+
        '</div>';
    }catch(e){
      box.innerHTML='<p>Route planner error: '+e.message+'</p>';
    }
  }, function(err){
    box.innerHTML='<p>GPS permission is required for route planning.</p>';
  }, {enableHighAccuracy:false, maximumAge:60000, timeout:15000});
}
</script>












<script>
(function(){
  function ready(fn){
    if(document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  ready(function(){
    const input =
      document.querySelector('#watchmanQuestionInput') ||
      document.querySelector('#watchmanAskInput') ||
      document.querySelector('input[placeholder*="Should I mow"]') ||
      document.querySelector('input[placeholder*="Ask:"]');

    const askBtn =
      document.querySelector('#watchmanAskButton') ||
      document.querySelector('#watchmanVoiceAsk') ||
      Array.from(document.querySelectorAll('button')).find(b => (b.textContent || '').trim().includes('Ask'));

    const out =
      document.querySelector('#watchmanAnswer') ||
      document.querySelector('#watchmanAskAnswer') ||
      document.querySelector('#watchmanVoiceOutput') ||
      Array.from(document.querySelectorAll('div,p')).find(x => (x.textContent || '').trim() === 'Ready.');

    if(!input || !askBtn || !out) return;

    input.removeAttribute('readonly');
    input.placeholder = 'Ask Watchman anything...';

    function esc(x){
      return String(x == null ? '' : x).replace(/[&<>"']/g, function(c){
        return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
      });
    }

    async function askTypedWatchman(e){
      if(e) e.preventDefault();

      const q = (input.value || '').trim();
      if(!q){
        out.textContent = 'Type a question first.';
        return;
      }

      out.textContent = 'Watchman is thinking...';

      try{
        const res = await fetch('/api/watchman/brain/ask', {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify({question:q, context:{}})
        });

        const data = await res.json();
        const answer = data.answer || data.response || 'Watchman did not return an answer.';
        const decision = data.synthesis && data.synthesis.overallDecision ? data.synthesis.overallDecision : '';

        out.innerHTML = (decision ? '<strong>' + esc(decision) + '</strong><br>' : '') + esc(answer);
      }catch(err){
        out.textContent = 'Watchman typed question failed: ' + err;
      }
    }

    askBtn.onclick = askTypedWatchman;
    input.addEventListener('keydown', function(e){
      if(e.key === 'Enter') askTypedWatchman(e);
    });
  });
})();
</script>

</body>
</html>
"""


@app.route("/api/watchman/notifications")
def api_watchman_notifications():
    unread = request.args.get("unread", "").lower() in ["1", "true", "yes"]
    rows = list_notifications(unread_only=unread, limit=50)
    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman Notification Engine",
        "summary": notification_summary(),
        "notifications": rows,
    })


@app.route("/api/watchman/notifications/read", methods=["POST", "GET"])
def api_watchman_notifications_read():
    count = mark_all_read()
    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman Notification Engine",
        "markedRead": count,
        "summary": notification_summary(),
    })




@app.route("/api/watchman/delivery/outbox")
def api_watchman_delivery_outbox():
    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman Notification Delivery",
        "summary": delivery_summary(),
        "outbox": list_delivery_outbox(50),
    })



@app.route("/api/watchman/phone/push/pending")
def api_watchman_phone_push_pending():
    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman Phone Push Bridge",
        "summary": phone_push_summary(),
        "pushes": pending_phone_pushes(20),
    })


@app.route("/api/watchman/phone/push/ack", methods=["POST", "GET"])
def api_watchman_phone_push_ack():
    push_id = request.args.get("id", "all")
    count = acknowledge_phone_push(push_id)
    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman Phone Push Bridge",
        "acknowledged": count,
        "summary": phone_push_summary(),
    })



@app.route("/api/watchman/android/notifications/status")
def api_watchman_android_notifications_status():
    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman Android Notification Bridge",
        "summary": android_bridge_summary(),
    })


@app.route("/api/watchman/android/notifications/send-pending")
def api_watchman_android_notifications_send_pending():
    from watchman_knowledge.notification_delivery import list_delivery_outbox
    rows = list_delivery_outbox(100)
    result = send_pending_android_notifications(rows)
    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman Android Notification Bridge",
        "result": result,
        "summary": android_bridge_summary(),
    })



@app.route("/api/watchman/watch/register")
def api_watchman_watch_register():
    place = request.args.get("place") or request.args.get("location") or request.args.get("q") or "default"
    interval = request.args.get("interval", "300")
    watch = register_watch(place, interval_seconds=interval)
    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman Background Watch Loop",
        "watch": watch,
        "summary": background_watch_summary(),
    })


@app.route("/api/watchman/watch/unregister")
def api_watchman_watch_unregister():
    place = request.args.get("place") or request.args.get("location") or request.args.get("q") or "default"
    removed = unregister_watch(place)
    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman Background Watch Loop",
        "removed": removed,
        "summary": background_watch_summary(),
    })


@app.route("/api/watchman/watch/list")
def api_watchman_watch_list():
    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman Background Watch Loop",
        "summary": background_watch_summary(),
        "watches": list_watches(),
    })


@app.route("/api/watchman/watch/run-once")
def api_watchman_watch_run_once():
    result = run_watch_once()
    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman Background Watch Loop",
        "result": result,
    })


@app.route("/api/watchman/watch/start")
def api_watchman_watch_start():
    interval = request.args.get("interval", "300")
    summary = start_background_watch_loop(interval)
    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman Background Watch Loop",
        "summary": summary,
    })


@app.route("/api/watchman/watch/stop")
def api_watchman_watch_stop():
    summary = stop_background_watch_loop()
    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman Background Watch Loop",
        "summary": summary,
    })

set_flask_app(app)
load_persisted_watches()
try:
    if list_watches():
        start_background_watch_loop(300)
except Exception:
    pass


@app.route("/api/watchman/alerts/tracking")
def api_watchman_alert_tracking():
    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman Alert Tracking",
        "summary": alert_tracking_summary(),
    })


@app.route("/api/watchman/change-detection")
def api_watchman_change_detection():
    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman Change Detection Engine V1",
        "summary": change_detection_summary(),
    })


@app.route("/api/watchman/alert-changes")
def api_watchman_alert_changes():
    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman Alert Change Notifier V1",
        "summary": alert_change_summary(),
    })


@app.route("/api/watchman/radar-map/intelligence")
def api_watchman_radar_map_intelligence():
    place = request.args.get("place", "Jasper, Alabama").strip() or "Jasper, Alabama"
    place = place.replace(",", ", ")
    while "  " in place:
        place = place.replace("  ", " ")

    geo = geocode(place)
    if not geo:
        return jsonify({"error": "geocode_failed", "place": place}), 502

    lat = geo.get("lat") or geo.get("latitude")
    lon = geo.get("lon") or geo.get("lng") or geo.get("longitude")

    if lat is None or lon is None:
        return jsonify({
            "error": "geocode_coordinates_missing",
            "place": place,
            "geocode": geo,
        }), 502

    weather = weather_lookup_for_place(place, geocode, _fetch_weather_direct)

    if "error" in weather:
        return jsonify(weather), 502

    storm_arrival = storm_arrival_engine("radar map intelligence", weather)
    result = build_map_intelligence(place, lat, lon, weather, storm_arrival)

    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman Radar Map Intelligence V1",
        "intelligence": result,
    })


@app.route("/api/watchman/radar-motion")
def api_watchman_radar_motion():
    place = request.args.get("place", "Jasper, Alabama").strip() or "Jasper, Alabama"
    place = place.replace(",", ", ")
    while "  " in place:
        place = place.replace("  ", " ")

    geo = geocode(place)
    if not geo:
        return jsonify({"error": "geocode_failed", "place": place}), 502

    lat = geo.get("lat") or geo.get("latitude")
    lon = geo.get("lon") or geo.get("lng") or geo.get("longitude")

    if lat is None or lon is None:
        return jsonify({
            "error": "geocode_coordinates_missing",
            "place": place,
            "geocode": geo,
        }), 502

    weather = weather_lookup_for_place(place, geocode, _fetch_weather_direct)

    if "error" in weather:
        return jsonify(weather), 502

    storm_arrival = storm_arrival_engine("radar motion", weather)
    result = radar_motion_engine(place, lat, lon, weather, storm_arrival)

    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman Radar Motion Engine V1",
        "result": result,
    })


@app.route("/api/watchman/radar-cell-tracker")
def api_watchman_radar_cell_tracker():
    place = request.args.get("place", "Jasper, Alabama").strip() or "Jasper, Alabama"
    place = place.replace(",", ", ")
    while "  " in place:
        place = place.replace("  ", " ")

    geo = geocode(place)
    if not geo:
        return jsonify({"error": "geocode_failed", "place": place}), 502

    lat = geo.get("lat") or geo.get("latitude")
    lon = geo.get("lon") or geo.get("lng") or geo.get("longitude")

    if lat is None or lon is None:
        return jsonify({
            "error": "geocode_coordinates_missing",
            "place": place,
            "geocode": geo,
        }), 502

    result = radar_cell_tracker(place, lat, lon)

    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman Radar Cell Tracker V1",
        "result": result,
    })


@app.route("/api/watchman/lightning")
def api_watchman_lightning():
    place = request.args.get("place", "Jasper, Alabama").strip() or "Jasper, Alabama"
    place = place.replace(",", ", ")
    while "  " in place:
        place = place.replace("  ", " ")

    geo = geocode(place)
    if not geo:
        return jsonify({"error": "geocode_failed", "place": place}), 502

    lat = geo.get("lat") or geo.get("latitude")
    lon = geo.get("lon") or geo.get("lng") or geo.get("longitude")

    if lat is None or lon is None:
        return jsonify({
            "error": "geocode_coordinates_missing",
            "place": place,
            "geocode": geo,
        }), 502

    weather = weather_lookup_for_place(place, geocode, _fetch_weather_direct)

    if "error" in weather:
        return jsonify(weather), 502

    radar_motion = radar_motion_engine(place, lat, lon, weather, storm_arrival_engine("lightning", weather))
    radar_cell = radar_cell_tracker(place, lat, lon)

    result = lightning_intelligence(place, lat, lon, weather, radar_motion, radar_cell)

    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman Lightning Intelligence Layer V1",
        "result": result,
    })


@app.route("/api/watchman/nws-polygons/advanced")
def api_watchman_nws_polygons_advanced():
    place = request.args.get("place", "Jasper, Alabama").strip() or "Jasper, Alabama"
    place = place.replace(",", ", ")
    while "  " in place:
        place = place.replace("  ", " ")

    geo = geocode(place)
    if not geo:
        return jsonify({"error": "geocode_failed", "place": place}), 502

    lat = geo.get("lat") or geo.get("latitude")
    lon = geo.get("lon") or geo.get("lng") or geo.get("longitude")

    if lat is None or lon is None:
        return jsonify({
            "error": "geocode_coordinates_missing",
            "place": place,
            "geocode": geo,
        }), 502

    result = build_advanced_nws_polygon_layer(place, lat, lon)

    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman Advanced NWS Polygon Layer V1",
        "result": result,
    })


@app.route("/api/watchman/radar-multi-cell")
def api_watchman_radar_multi_cell():
    place = request.args.get("place", "Jasper, Alabama").strip() or "Jasper, Alabama"
    place = place.replace(",", ", ")
    while "  " in place:
        place = place.replace("  ", " ")

    geo = geocode(place)
    if not geo:
        return jsonify({"error": "geocode_failed", "place": place}), 502

    lat = geo.get("lat") or geo.get("latitude")
    lon = geo.get("lon") or geo.get("lng") or geo.get("longitude")

    if lat is None or lon is None:
        return jsonify({
            "error": "geocode_coordinates_missing",
            "place": place,
            "geocode": geo,
        }), 502

    result = radar_multi_cell_tracker(place, lat, lon)

    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman Multi-Cell Storm Tracker V1",
        "result": result,
    })


@app.route("/api/watchman/impact-forecast")
def api_watchman_impact_forecast():
    place = request.args.get("place", "Jasper, Alabama").strip() or "Jasper, Alabama"
    place = place.replace(",", ", ")
    while "  " in place:
        place = place.replace("  ", " ")

    geo = geocode(place)
    if not geo:
        return jsonify({"error": "geocode_failed", "place": place}), 502

    lat = geo.get("lat") or geo.get("latitude")
    lon = geo.get("lon") or geo.get("lng") or geo.get("longitude")

    if lat is None or lon is None:
        return jsonify({
            "error": "geocode_coordinates_missing",
            "place": place,
            "geocode": geo,
        }), 502

    weather = weather_lookup_for_place(place, geocode, _fetch_weather_direct)

    if "error" in weather:
        return jsonify(weather), 502

    multi_cell = radar_multi_cell_tracker(place, lat, lon)
    result = impact_forecast(place, lat, lon, weather, multi_cell)

    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman Impact Forecast V1",
        "result": result,
    })


@app.route("/api/watchman/decision")
def api_watchman_decision():
    place = request.args.get("place", "Jasper, Alabama").strip() or "Jasper, Alabama"
    place = place.replace(",", ", ")
    while "  " in place:
        place = place.replace("  ", " ")

    geo = geocode(place)
    if not geo:
        return jsonify({"error": "geocode_failed", "place": place}), 502

    lat = geo.get("lat") or geo.get("latitude")
    lon = geo.get("lon") or geo.get("lng") or geo.get("longitude")

    if lat is None or lon is None:
        return jsonify({
            "error": "geocode_coordinates_missing",
            "place": place,
            "geocode": geo,
        }), 502

    weather = weather_lookup_for_place(place, geocode, _fetch_weather_direct)

    if "error" in weather:
        return jsonify(weather), 502

    multi_cell = radar_multi_cell_tracker(place, lat, lon)
    impact = impact_forecast(place, lat, lon, weather, multi_cell)
    radar_motion = radar_motion_engine(place, lat, lon, weather, storm_arrival_engine("decision", weather))
    radar_cell = radar_cell_tracker(place, lat, lon)
    lightning = lightning_intelligence(place, lat, lon, weather, radar_motion, radar_cell)

    result = watchman_decision_engine(place, weather, impact, lightning, multi_cell)

    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman Decision Engine V1",
        "result": result,
    })


@app.route("/api/watchman/gps-impact")
def api_watchman_gps_impact():
    label = request.args.get("label", "GPS Location").strip() or "GPS Location"

    try:
        lat = float(request.args.get("lat", ""))
        lon = float(request.args.get("lon", ""))
    except Exception:
        return jsonify({
            "error": "missing_or_invalid_gps",
            "required": "lat and lon query parameters",
            "example": "/api/watchman/gps-impact?lat=33.8312&lon=-87.2775",
        }), 400

    weather = weather_lookup_for_gps(label, lat, lon, _fetch_weather_direct)

    if "error" in weather:
        return jsonify(weather), 502

    multi_cell = radar_multi_cell_tracker(label, lat, lon)
    impact = impact_forecast(label, lat, lon, weather, multi_cell)
    radar_motion = radar_motion_engine(label, lat, lon, weather, storm_arrival_engine("gps impact", weather))
    radar_cell = radar_cell_tracker(label, lat, lon)
    lightning = lightning_intelligence(label, lat, lon, weather, radar_motion, radar_cell)
    decision = watchman_decision_engine(label, weather, impact, lightning, multi_cell)

    result = gps_impact_forecast(label, lat, lon, weather, multi_cell, impact, decision)

    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman GPS-Aware Impact Forecast V1",
        "result": result,
    })


@app.route("/api/watchman/gps-watch/update")
def api_watchman_gps_watch_update():
    label = request.args.get("label", "Phone GPS").strip() or "Phone GPS"

    try:
        lat = float(request.args.get("lat", ""))
        lon = float(request.args.get("lon", ""))
    except Exception:
        return jsonify({
            "error": "missing_or_invalid_gps",
            "required": "lat and lon query parameters",
        }), 400

    weather = weather_lookup_for_gps(label, lat, lon, _fetch_weather_direct)

    if "error" in weather:
        return jsonify(weather), 502

    multi_cell = radar_multi_cell_tracker(label, lat, lon)
    impact = impact_forecast(label, lat, lon, weather, multi_cell)
    radar_motion = radar_motion_engine(label, lat, lon, weather, storm_arrival_engine("gps watch", weather))
    radar_cell = radar_cell_tracker(label, lat, lon)
    lightning = lightning_intelligence(label, lat, lon, weather, radar_motion, radar_cell)
    decision = watchman_decision_engine(label, weather, impact, lightning, multi_cell)
    gps_result = gps_impact_forecast(label, lat, lon, weather, multi_cell, impact, decision)

    risk_change = gps_risk_change_notifier(label, gps_result)

    if risk_change.get("changed") and risk_change.get("escalated"):
        item = add_notification(
            "gps_risk_change",
            "GPS weather risk increased",
            f"Watchman GPS risk changed for {label}: " + "; ".join(risk_change.get("changes") or []),
            severity="urgent",
            place=label,
            data=risk_change,
        )
        deliveries = queue_deliveries([item])
        send_pending_android_notifications(deliveries)

    summary = update_gps_watch(lat, lon, gps_result, label)
    summary["riskChange"] = risk_change

    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman Continuous GPS Watch V1",
        "summary": summary,
    })


@app.route("/api/watchman/gps-watch/status")
def api_watchman_gps_watch_status():
    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman Continuous GPS Watch V1",
        "summary": gps_watch_summary(),
    })


@app.route("/api/watchman/gps-watch/stop")
def api_watchman_gps_watch_stop():
    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman Continuous GPS Watch V1",
        "summary": stop_gps_watch(),
    })


@app.route("/api/watchman/gps-risk/status")
def api_watchman_gps_risk_status():
    return jsonify({
        "app": "CHAPNETAI Weather",
        "mode": "Watchman GPS Risk Change Notifier V1",
        "summary": gps_risk_notifier_summary(),
    })


@app.route("/api/watchman/mission")
def api_watchman_mission():
    place = request.args.get("place", "Jasper, Alabama").strip() or "Jasper, Alabama"
    mission = request.args.get("mission", "travel").strip() or "travel"

    weather = _fetch_weather_direct(place)
    if "error" in weather:
        return jsonify(weather), 502

    mission_result = mission_planner(mission, weather)
    explanation = explain_watchman_decision(weather, mission_result)
    memory_item = record_weather_memory(place, weather, mission_result, explanation)

    return jsonify({
        "app": APP_NAME,
        "mode": "Watchman Mission Planner V1",
        "place": place,
        "mission": mission_result,
        "explanation": explanation,
        "memoryItem": memory_item,
    })


@app.route("/api/watchman/decision-explanation")
def api_watchman_decision_explanation():
    place = request.args.get("place", "Jasper, Alabama").strip() or "Jasper, Alabama"

    weather = _fetch_weather_direct(place)
    if "error" in weather:
        return jsonify(weather), 502

    explanation = explain_watchman_decision(weather)

    return jsonify({
        "app": APP_NAME,
        "mode": "Watchman Decision Explanation Engine V1",
        "place": place,
        "explanation": explanation,
    })


@app.route("/api/watchman/weather-memory")
def api_watchman_weather_memory():
    place = request.args.get("place", "").strip() or None

    return jsonify({
        "app": APP_NAME,
        "mode": "ChapNetAI Watchman Memory Timeline V1",
        "summary": weather_memory_summary(place),
    })


@app.route("/api/watchman/mission-time-machine")
def api_watchman_mission_time_machine():
    place = request.args.get("place", "Jasper, Alabama").strip() or "Jasper, Alabama"
    mission = request.args.get("mission", "travel").strip() or "travel"

    weather = _fetch_weather_direct(place)
    if "error" in weather:
        return jsonify(weather), 502

    result = mission_time_machine(mission, weather)

    return jsonify({
        "app": APP_NAME,
        "mode": "Watchman Mission Time Machine V1",
        "place": place,
        "result": result,
    })


@app.route("/api/watchman/live-timeline")
def api_watchman_live_timeline():
    place = request.args.get("place", "Jasper, Alabama").strip() or "Jasper, Alabama"

    weather = _fetch_weather_direct(place)
    if "error" in weather:
        return jsonify(weather), 502

    result = build_live_timeline(place, weather)

    return jsonify({
        "app": APP_NAME,
        "mode": "Watchman Live Timeline",
        "place": place,
        "result": result,
    })


@app.route("/api/watchman/notification-diagnostic")
def api_watchman_notification_diagnostic():
    place = request.args.get("place", "Jasper, Alabama").strip() or "Jasper, Alabama"

    weather = _fetch_weather_direct(place)
    if "error" in weather:
        return jsonify(weather), 502

    timeline = build_live_timeline(place, weather)
    alerts = weather.get("alerts") or []
    watchman = weather.get("watchman") or {}

    reasons = []
    if alerts:
        reasons.append("NWS alert exists, but browser notification still depends on Watchman push permission and pending push creation.")
    else:
        reasons.append("No active NWS alert returned for this location at diagnostic time.")

    reasons.append("WBRC can send editorial newsroom push alerts. Watchman currently sends only app-generated Watchman events.")
    reasons.append("Chrome/Android notification permission must be allowed for this localhost app.")
    reasons.append("The app must be open or the Watchman phone push bridge must be polling to surface local notifications.")

    return jsonify({
        "app": APP_NAME,
        "mode": "Watchman Notification Diagnostic",
        "place": place,
        "activeAlerts": len(alerts),
        "threatLevel": watchman.get("threatLevel"),
        "threatScore": watchman.get("threatScore"),
        "timelineNotificationReason": timeline.get("notificationReason"),
        "likelyReasons": reasons,
    })

@app.route("/api/watchman/device/register", methods=["GET", "POST"])
def api_watchman_device_register():
    payload = request.get_json(silent=True) or {}
    if request.method == "GET":
        payload.update(dict(request.args))
    return jsonify(register_device(payload))


@app.route("/api/watchman/device/location", methods=["GET", "POST"])
def api_watchman_device_location():
    payload = request.get_json(silent=True) or {}
    if request.method == "GET":
        payload.update(dict(request.args))
    return jsonify(update_location(payload))


@app.route("/api/watchman/device/push/pending", methods=["GET"])
def api_watchman_device_push_pending():
    device_id = request.args.get("deviceId") or request.args.get("device_id") or ""
    return jsonify(pending_pushes(device_id))


@app.route("/api/watchman/device/push/ack", methods=["GET", "POST"])
def api_watchman_device_push_ack():
    push_id = request.args.get("id") or ""
    device_id = request.args.get("deviceId") or request.args.get("device_id") or ""
    return jsonify(ack_push(push_id, device_id))


@app.route("/api/watchman/device/status", methods=["GET"])
def api_watchman_device_status():
    device_id = request.args.get("deviceId") or request.args.get("device_id")
    return jsonify(current_device_status(device_id))



@app.route("/watchman_service_worker.js")
def watchman_service_worker_root():
    response = app.send_static_file("watchman_service_worker.js")
    response.headers["Service-Worker-Allowed"] = "/"
    return response

@app.route("/api/watchman/web-push/public-key", methods=["GET"])
def api_watchman_web_push_public_key():
    return jsonify(get_vapid_public_key())


@app.route("/api/watchman/web-push/subscribe", methods=["POST"])
def api_watchman_web_push_subscribe():
    payload = request.get_json(silent=True) or {}
    return jsonify(save_subscription(payload))


@app.route("/api/watchman/web-push/subscription", methods=["GET"])
def api_watchman_web_push_subscription():
    device_id = request.args.get("deviceId") or request.args.get("device_id") or ""
    return jsonify(get_subscription(device_id))


@app.route("/api/watchman/web-push/status", methods=["GET"])
def api_watchman_web_push_status():
    return jsonify(web_push_status())


@app.route("/api/watchman/web-push/test", methods=["GET", "POST"])
def api_watchman_web_push_test():
    payload = request.get_json(silent=True) or {}
    device_id = payload.get("deviceId") or request.args.get("deviceId") or request.args.get("device_id") or ""
    return jsonify(send_web_push(
        device_id,
        "ChapNetAI Watchman Test",
        "Background push is connected for your current device.",
        {"test": True},
    ))



@app.route("/api/watchman/route-planner", methods=["GET", "POST"])
def api_watchman_route_planner():
    from watchman_knowledge.route_planner import plan_route_weather

    payload = request.get_json(silent=True) or {}
    if request.method == "GET":
        payload.update(dict(request.args))

    origin_lat = payload.get("originLat") or payload.get("origin_lat") or payload.get("lat")
    origin_lon = payload.get("originLon") or payload.get("origin_lon") or payload.get("lon")
    destination = payload.get("destination") or payload.get("dest") or payload.get("to")
    samples = payload.get("samples") or 5

    return jsonify(plan_route_weather(origin_lat, origin_lon, destination, samples))



@app.route("/api/watchman/navigation-route", methods=["GET", "POST"])
def api_watchman_navigation_route():
    from watchman_knowledge.route_planner import build_navigation_route

    payload = request.get_json(silent=True) or {}
    if request.method == "GET":
        payload.update(dict(request.args))

    origin_lat = payload.get("originLat") or payload.get("origin_lat") or payload.get("lat")
    origin_lon = payload.get("originLon") or payload.get("origin_lon") or payload.get("lon")
    destination = payload.get("destination") or payload.get("dest") or payload.get("to")
    samples = payload.get("samples") or 8

    return jsonify(build_navigation_route(origin_lat, origin_lon, destination, samples))



@app.route("/api/watchman/safety-layer", methods=["GET"])
def api_watchman_safety_layer():
    from watchman_knowledge.safety_layer import safety_layer

    lat = request.args.get("lat")
    lon = request.args.get("lon")
    radius = request.args.get("radius") or 10000

    return jsonify(safety_layer(lat, lon, radius))


@app.route("/api/watchman/road-speed-limit", methods=["GET"])
def api_watchman_road_speed_limit():
    from watchman_knowledge.safety_layer import road_speed_limit

    lat = request.args.get("lat")
    lon = request.args.get("lon")

    return jsonify(road_speed_limit(lat, lon))



@app.route("/api/watchman/skills")
def api_watchman_skills():
    from watchman_knowledge.skills_registry import registry_summary
    return jsonify(registry_summary())


@app.route("/api/watchman/skills/classify")
def api_watchman_skills_classify():
    from watchman_knowledge.skills_registry import classify_question
    question = request.args.get("q") or request.args.get("question") or ""
    return jsonify(classify_question(question))



@app.route("/api/watchman/travel/ask", methods=["POST"])
def api_watchman_travel_ask():
    from watchman_knowledge.travel_companion import answer_travel_question

    payload = request.get_json(silent=True) or {}
    question = payload.get("question") or payload.get("q") or ""
    route_payload = payload.get("route") or {}
    destination = payload.get("destination") or ""

    return jsonify(answer_travel_question(question, route_payload, destination))



@app.route("/api/watchman/highways")
def api_watchman_highways():
    from watchman_knowledge.highway_knowledge import highway_registry_summary
    return jsonify(highway_registry_summary())


@app.route("/api/watchman/highways/ask")
def api_watchman_highways_ask():
    from watchman_knowledge.highway_knowledge import answer_highway_question
    question = request.args.get("q") or request.args.get("question") or ""
    return jsonify(answer_highway_question(question))



@app.route("/api/watchman/geo")
def api_watchman_geo():
    from watchman_knowledge.geo_knowledge import geo_registry_summary
    return jsonify(geo_registry_summary())


@app.route("/api/watchman/geo/ask")
def api_watchman_geo_ask():
    from watchman_knowledge.geo_knowledge import answer_geo_question
    question = request.args.get("q") or request.args.get("question") or ""
    return jsonify(answer_geo_question(question))



@app.route("/api/watchman/road")
def api_watchman_road():
    from watchman_knowledge.road_intelligence import road_registry_summary
    return jsonify(road_registry_summary())


@app.route("/api/watchman/road/ask", methods=["GET", "POST"])
def api_watchman_road_ask():
    from watchman_knowledge.road_intelligence import answer_road_question

    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        question = payload.get("question") or payload.get("q") or ""
        route_payload = payload.get("route") or {}
    else:
        question = request.args.get("q") or request.args.get("question") or ""
        route_payload = {}

    return jsonify(answer_road_question(question, route_payload))



@app.route("/api/watchman/local-services")
def api_watchman_local_services():
    from watchman_knowledge.local_services import local_services_summary
    return jsonify(local_services_summary())


@app.route("/api/watchman/local-services/ask", methods=["GET", "POST"])
def api_watchman_local_services_ask():
    from watchman_knowledge.local_services import answer_local_service_question

    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        question = payload.get("question") or payload.get("q") or ""
        route_payload = payload.get("route") or {}
    else:
        question = request.args.get("q") or request.args.get("question") or ""
        route_payload = {}

    return jsonify(answer_local_service_question(question, route_payload))



@app.route("/api/watchman/outdoor")
def api_watchman_outdoor():
    from watchman_knowledge.outdoor_intelligence import outdoor_registry_summary
    return jsonify(outdoor_registry_summary())


@app.route("/api/watchman/outdoor/ask", methods=["GET", "POST"])
def api_watchman_outdoor_ask():
    from watchman_knowledge.outdoor_intelligence import answer_outdoor_question

    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        question = payload.get("question") or payload.get("q") or ""
        weather = payload.get("weather") or {}
    else:
        question = request.args.get("q") or request.args.get("question") or ""
        weather = {}

    return jsonify(answer_outdoor_question(question, weather))



@app.route("/api/watchman/vehicle")
def api_watchman_vehicle():
    from watchman_knowledge.vehicle_intelligence import vehicle_registry_summary
    return jsonify(vehicle_registry_summary())


@app.route("/api/watchman/vehicle/ask", methods=["GET", "POST"])
def api_watchman_vehicle_ask():
    from watchman_knowledge.vehicle_intelligence import answer_vehicle_question

    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        question = payload.get("question") or payload.get("q") or ""
        weather = payload.get("weather") or {}
        route_payload = payload.get("route") or {}
    else:
        question = request.args.get("q") or request.args.get("question") or ""
        weather = {}
        route_payload = {}

    return jsonify(answer_vehicle_question(question, weather, route_payload))



@app.route("/api/watchman/emergency")
def api_watchman_emergency():
    from watchman_knowledge.emergency_intelligence_v1 import emergency_registry_summary
    return jsonify(emergency_registry_summary())


@app.route("/api/watchman/emergency/ask", methods=["GET", "POST"])
def api_watchman_emergency_ask():
    from watchman_knowledge.emergency_intelligence_v1 import answer_emergency_question

    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        question = payload.get("question") or payload.get("q") or ""
        weather = payload.get("weather") or {}
        route_payload = payload.get("route") or {}
    else:
        question = request.args.get("q") or request.args.get("question") or ""
        weather = {}
        route_payload = {}

    return jsonify(answer_emergency_question(question, weather, route_payload))



@app.route("/api/watchman/real-life")
def api_watchman_real_life():
    from watchman_knowledge.real_life_questions import real_life_questions_summary
    return jsonify(real_life_questions_summary())


@app.route("/api/watchman/real-life/ask", methods=["GET", "POST"])
def api_watchman_real_life_ask():
    from watchman_knowledge.real_life_questions import answer_real_life_question

    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        question = payload.get("question") or payload.get("q") or ""
        context = payload.get("context") or {}
    else:
        question = request.args.get("q") or request.args.get("question") or ""
        context = {}

    return jsonify(answer_real_life_question(question, context))



@app.route("/api/watchman/brain")
def api_watchman_brain():
    from watchman_knowledge.brain_router import brain_router_summary
    return jsonify(brain_router_summary())


@app.route("/api/watchman/brain/ask", methods=["GET", "POST"])
def api_watchman_brain_ask():
    from watchman_knowledge.brain_router import answer_with_brain

    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        question = payload.get("question") or payload.get("q") or ""
        context = payload.get("context") or {}
    else:
        question = request.args.get("q") or request.args.get("question") or ""
        context = {}

    return jsonify(answer_with_brain(question, context))



@app.route("/api/watchman/learning")
def api_watchman_learning():
    from watchman_knowledge.learning_memory import learning_summary
    return jsonify(learning_summary())


@app.route("/api/watchman/learning/recent")
def api_watchman_learning_recent():
    from watchman_knowledge.learning_memory import read_recent_questions
    limit = int(request.args.get("limit", 50))
    return jsonify(read_recent_questions(limit))


@app.route("/api/watchman/learning/weak")
def api_watchman_learning_weak():
    from watchman_knowledge.learning_memory import read_weak_questions
    limit = int(request.args.get("limit", 50))
    return jsonify(read_weak_questions(limit))



@app.route("/api/watchman/learning/review")
def api_watchman_learning_review():
    from watchman_knowledge.learning_review import review_learning
    limit = int(request.args.get("limit", 300))
    return jsonify(review_learning(limit))



@app.route("/api/watchman/learning/suggestions")
def api_watchman_learning_suggestions():
    from watchman_knowledge.learning_suggestions import suggest_learning_patches
    limit = int(request.args.get("limit", 500))
    return jsonify(suggest_learning_patches(limit))


@app.route("/api/watchman/learning/patch-plan")
def api_watchman_learning_patch_plan():
    from watchman_knowledge.learning_suggestions import export_patch_plan
    limit = int(request.args.get("limit", 500))
    return jsonify(export_patch_plan(limit))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5077)

