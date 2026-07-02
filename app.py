from flask import Flask, request, jsonify
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import json
import math
from datetime import datetime, timezone
from watchman_weather_engine import analyze_weather
from watchman_voice_copilot import answer_watchman_question, top_questions_flat, extract_place_from_question

app = Flask(__name__)

APP_NAME = "CHAPNETAI Weather"
TAGLINE = "National Weather Intelligence"
CREDIT = "Powered by NOAA • National Weather Service"
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
    question = request.args.get("q", "").strip()

    if not question:
        return jsonify({"error": "Missing q question parameter"}), 400

    place = extract_place_from_question(question, requested_place)

    with app.test_client() as client:
        resp = client.get("/api/nws", query_string={"place": place})
        weather = resp.get_json() or {}

    if "error" in weather:
        return jsonify(weather), 502

    answer = answer_watchman_question(question, weather)

    return jsonify({
        "app": APP_NAME,
        "mode": "Watchman AI Copilot",
        "place": place,
        "requestedPlace": requested_place,
        "question": question,
        "answer": answer,
        "watchman_version": (weather.get("watchman") or {}).get("watchman_version", "Watchman V108"),
    })

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
.footer{text-align:center;color:var(--muted);padding:2rem 0}
@media(max-width:780px){.grid{grid-template-columns:1fr}.search{flex-direction:column}.big{font-size:3rem}}
</style>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
</head>
<body>
<div class="wrap">
<section class="hero">
<div class="kicker">CHAPNETAI WEATHER</div>
<h1>National Weather Intelligence</h1>
<p><strong>Powered by NOAA • National Weather Service</strong></p>
<p>Watchman Intelligence transforms official weather data into threat levels, briefings, and decision support.</p>
<div class="search">
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
        <h2>Watchman Live Radar</h2>
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
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5077, debug=False, use_reloader=False)
