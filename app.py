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

app = Flask(__name__)

APP_NAME = "CHAPNETAI Weather"
TAGLINE = "ChapNetAI Weather"
CREDIT = "Your Hometown Weather App"
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

    points = nws_points(float(lat), float(lon))
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


/* ChapNetAI Weather centered branding lock */
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

</style>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
</head>
<body>
<div class="wrap">
<section class="hero">

<div class="kicker">CHAPNETAI WEATHER</div>

<h1>ChapNetAI Weather</h1>

<p class="heroTagline"><strong>Your Hometown Weather App</strong></p>

<p class="watchmanPower">
  <strong>Powered by Watchman™</strong><br>
  AI Weather Intelligence
</p>

<p>
  <span class="sourcePill">Official weather data from NOAA • National Weather Service</span>
</p>

<input id="place" value="Jasper, Alabama" placeholder="City, state">
<button onclick="loadWeather()">Run Watchman Scan</button>

</div>

<div class="copilotBox">
  <div class="kicker">WATCHMAN AI COPILOT</div>
  <h2>Ask Watchman</h2>
  <p>Press the microphone and ask a weather question. Watchman will answer and read it out loud.</p>
  <div class="copilotControls">
    <input id="copilotQuestion" placeholder="Ask: Should I mow today? Is lightning nearby? When will rain start?">
    <button class="micBtn" onclick="startWatchmanVoice()">🎙 Ask</button>
    <button class="speakBtn" onclick="speakLastWatchmanAnswer()">🔊 Read Again</button>
  </div>
  <div id="copilotAnswer" class="copilotAnswer">Ready.</div>
</div>
</section>

<div id="app"></div>
<div class="footer">Independent ChapNetAI platform. Official warnings remain NOAA / National Weather Service products.</div>
</div>

<script>
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
            <strong>Watchman AI Briefing</strong>
            <p>${safe(w.aiBriefing)}</p>
          </div>

          <div class="day" style="margin-top:.8rem">
            <strong>AI Weather Narrative</strong>
            <p>${safe(w.aiWeatherNarrative)}</p>
          </div>

          <div class="day" style="margin-top:.8rem">
            <strong>Live Watchman Scanner</strong>
            <p>${safe(w.liveScanner?.refreshNote)}</p>
            ${(w.liveScanner?.steps || []).map(step=>`
              <div class="row">
                <span>${safe(step.label)}</span>
                <strong>${safe(step.status)} · ${safe(step.detail)}</strong>
              </div>
            `).join('')}
          </div>

          <div class="day" style="margin-top:.8rem">
            <strong>Watchman Hazard Board</strong>
            <div id="hazardBoard">Ask Watchman: "What is the biggest risk?"</div>
          </div>

          <div class="day" style="margin-top:.8rem">
            <strong>Live Storm Intelligence</strong>
            <div class="row"><span>Storm Signal</span><strong>${safe(w.liveStormIntelligence?.stormSignal)}</strong></div>
            <div class="row"><span>Heat Signal</span><strong>${safe(w.liveStormIntelligence?.heatSignal)}</strong></div>
            <div class="row"><span>Flood Signal</span><strong>${safe(w.liveStormIntelligence?.floodSignal)}</strong></div>
            <div class="row"><span>Next Window</span><strong>${safe(w.liveStormIntelligence?.nextWindow)}</strong></div>
            <div class="row"><span>Precip Chance</span><strong>${safe(w.liveStormIntelligence?.precipChance,0)}%</strong></div>
          </div>

          <div class="day" style="margin-top:.8rem">
            <strong>Street-Level Arrival</strong>
            <p>${safe(w.streetLevelArrival?.rainEta)}</p>
            <p>${safe(w.streetLevelArrival?.lightningEta)}</p>
          </div>

          <div class="day" style="margin-top:.8rem">
            <strong>Watchman Storm Tracker</strong>
            <div class="row"><span>Nearest Storm</span><strong>${safe(w.stormTracker?.nearestStorm)}</strong></div>
            <div class="row"><span>Intensity</span><strong>${safe(w.stormTracker?.intensity)}</strong></div>
            <div class="row"><span>Window</span><strong>${safe(w.stormTracker?.forecastWindow)}</strong></div>
            <div class="row"><span>Arrival</span><strong>${safe(w.stormTracker?.estimatedArrival)}</strong></div>
            <div class="row"><span>Movement</span><strong>${safe(w.stormTracker?.movement)}</strong></div>
            <div class="row"><span>Confidence</span><strong>${safe(w.stormTracker?.confidence)}%</strong></div>
          </div>

          <div class="day" style="margin-top:.8rem">
            <strong>What Changed Since Last Scan</strong>
            <p>${safe(w.whatChanged?.summary)}</p>
            ${(w.whatChanged?.changes || []).map(c=>`<div class="row"><span>Change</span><strong>${safe(c)}</strong></div>`).join('')}
          </div>
          <div class="row"><span>Outdoor Index</span><strong>${w.outdoorIndex}/100</strong></div>
          <div class="row"><span>Travel Index</span><strong>${w.travelIndex}/100</strong></div>
          <div class="row"><span>Active Alerts</span><strong>${alerts.length}</strong></div>
          <div class="row"><span>Engine</span><strong>${safe(w.engine)} ${safe(w.version)}</strong></div>\n          <div class="row"><span>Real Watchman Core</span><strong>${w.coreAvailable ? "CONNECTED" : "NOT CONNECTED"}</strong></div>\n          <div class="row"><span>Core Modules</span><strong>${w.coreModules.length}</strong></div>\n          <div class="row"><span>Reasons</span><strong>${w.reasons.join(', ')}</strong></div>
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
        <iframe
id="radarMap"
loading="lazy"
allowfullscreen
referrerpolicy="no-referrer-when-downgrade"
src="">
</iframe>
        <div class="radarNote">Live radar-only map. Forecast panels are handled by ChapNetAI Weather below.</div>
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
      const radar=document.getElementById('radarMap');
      if(radar){
        radar.src='https://www.rainviewer.com/map.html?loc='
          +data.location.latitude+','+data.location.longitude+',8'
          +'&layer=radar&oAP=1&oF=0&oC=0&c=1&sm=1&sn=1';
      }
  }catch(e){
    root.innerHTML='<div class="card" style="margin-top:1rem;color:#ff9b9b;font-weight:900">'+e.message+'</div>';
  }
}
loadWeather();
</script>
<script src="/static/watchman_phone_push.js"></script>
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

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5077, debug=False, use_reloader=False)
