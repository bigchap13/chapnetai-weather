from flask import Flask, request, jsonify
from urllib.parse import urlencode
from urllib.request import urlopen
import json

app = Flask(__name__)

DEFAULT_PLACE = "Jasper, Alabama"

def fetch_json(url):
    with urlopen(url, timeout=12) as r:
        return json.loads(r.read().decode("utf-8"))

def geocode(place):
    q = urlencode({"name": place, "count": 1, "language": "en", "format": "json"})
    data = fetch_json(f"https://geocoding-api.open-meteo.com/v1/search?{q}")
    results = data.get("results") or []
    if not results:
        return None
    return results[0]

def weather(lat, lon, timezone):
    params = urlencode({
        "latitude": lat,
        "longitude": lon,
        "timezone": timezone,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_gusts_10m",
        "hourly": "temperature_2m,precipitation_probability,precipitation,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max",
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "forecast_days": 7,
    })
    return fetch_json(f"https://api.open-meteo.com/v1/forecast?{params}")

def code_label(code):
    table = {
        0: "Clear", 1: "Mostly clear", 2: "Partly cloudy", 3: "Cloudy",
        45: "Fog", 48: "Freezing fog",
        51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
        61: "Light rain", 63: "Rain", 65: "Heavy rain",
        71: "Light snow", 73: "Snow", 75: "Heavy snow",
        80: "Rain showers", 81: "Showers", 82: "Heavy showers",
        95: "Thunderstorms", 96: "Storms with hail", 99: "Severe storms with hail",
    }
    return table.get(int(code or 0), f"Weather code {code}")

@app.route("/api/weather")
def api_weather():
    place = request.args.get("place", DEFAULT_PLACE).strip() or DEFAULT_PLACE
    geo = geocode(place)
    if not geo:
        return jsonify({"error": "Location not found"}), 404

    data = weather(geo["latitude"], geo["longitude"], geo.get("timezone", "auto"))
    current = data.get("current", {})
    current["condition"] = code_label(current.get("weather_code"))

    daily = data.get("daily", {})
    days = []
    for i, day in enumerate(daily.get("time", [])):
        days.append({
            "date": day,
            "condition": code_label(daily["weather_code"][i]),
            "high": daily["temperature_2m_max"][i],
            "low": daily["temperature_2m_min"][i],
            "rainChance": daily["precipitation_probability_max"][i],
            "windMax": daily["wind_speed_10m_max"][i],
        })

    hourly = data.get("hourly", {})
    hours = []
    for i, t in enumerate(hourly.get("time", [])[:24]):
        hours.append({
            "time": t,
            "temp": hourly["temperature_2m"][i],
            "rainChance": hourly["precipitation_probability"][i],
            "rain": hourly["precipitation"][i],
            "condition": code_label(hourly["weather_code"][i]),
            "wind": hourly["wind_speed_10m"][i],
        })

    return jsonify({
        "place": {
            "name": geo.get("name"),
            "admin1": geo.get("admin1"),
            "country": geo.get("country"),
            "latitude": geo.get("latitude"),
            "longitude": geo.get("longitude"),
            "timezone": geo.get("timezone"),
        },
        "current": current,
        "daily": days,
        "hourly": hours,
    })

@app.route("/health")
def health():
    return {"service": "ChapNetAI Weather", "status": "online"}

@app.route("/")
def home():
    return """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ChapNetAI Weather</title>
<style>
:root{--bg:#071018;--panel:#101d2a;--line:#22374a;--text:#eef7ff;--muted:#9fb3c8;--gold:#d4af37;--blue:#4fc3ff}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(circle at top,#16324a,#071018 55%);color:var(--text);font-family:system-ui,Arial,sans-serif}
.wrap{max-width:1100px;margin:auto;padding:1rem}
.hero{padding:1.25rem;border:1px solid var(--line);border-radius:1.5rem;background:rgba(16,29,42,.86);box-shadow:0 20px 60px rgba(0,0,0,.35)}
.kicker{color:var(--gold);font-weight:900;letter-spacing:.08em;text-transform:uppercase;font-size:.78rem}
h1{margin:.35rem 0;font-size:clamp(2rem,8vw,4rem)}
p{color:var(--muted)}
.search{display:flex;gap:.5rem;margin-top:1rem}
input,button{border-radius:999px;border:1px solid var(--line);padding:.85rem 1rem;font:inherit}
input{flex:1;background:#08131d;color:var(--text)}
button{background:var(--gold);color:#111;font-weight:900}
.grid{display:grid;grid-template-columns:1.15fr .85fr;gap:1rem;margin-top:1rem}
.card{border:1px solid var(--line);border-radius:1.25rem;background:rgba(16,29,42,.82);padding:1rem}
.temp{font-size:4rem;font-weight:1000}
.row{display:flex;justify-content:space-between;border-top:1px solid var(--line);padding:.7rem 0;color:var(--muted)}
.days{display:grid;grid-template-columns:repeat(auto-fit,minmax(135px,1fr));gap:.75rem;margin-top:1rem}
.day{border:1px solid var(--line);border-radius:1rem;background:rgba(255,255,255,.04);padding:.75rem}
.hourly{overflow:auto;max-height:420px}
.err{color:#ff9b9b;font-weight:900}
@media(max-width:760px){.grid{grid-template-columns:1fr}.search{flex-direction:column}.temp{font-size:3.25rem}}
</style>
</head>
<body>
<div class="wrap">
<section class="hero">
<div class="kicker">ChapNetAI Weather</div>
<h1>Real Weather Intelligence</h1>
<p>Live current conditions, 24-hour outlook, and 7-day forecast powered by Open-Meteo.</p>
<div class="search">
<input id="place" value="Jasper, Alabama" placeholder="City, state">
<button onclick="loadWeather()">Check Weather</button>
</div>
</section>

<div id="app"></div>
</div>

<script>
async function loadWeather(){
  const place=document.getElementById("place").value || "Jasper, Alabama";
  const root=document.getElementById("app");
  root.innerHTML='<div class="card" style="margin-top:1rem">Loading weather...</div>';
  try{
    const r=await fetch('/api/weather?place='+encodeURIComponent(place));
    const data=await r.json();
    if(!r.ok) throw new Error(data.error || 'Weather failed');

    const c=data.current;
    const p=data.place;
    root.innerHTML=`
      <div class="grid">
        <section class="card">
          <h2>${p.name}, ${p.admin1 || p.country}</h2>
          <div class="temp">${Math.round(c.temperature_2m)}°F</div>
          <h3>${c.condition}</h3>
          <div class="row"><span>Feels Like</span><strong>${Math.round(c.apparent_temperature)}°F</strong></div>
          <div class="row"><span>Humidity</span><strong>${c.relative_humidity_2m}%</strong></div>
          <div class="row"><span>Wind</span><strong>${Math.round(c.wind_speed_10m)} mph</strong></div>
          <div class="row"><span>Gusts</span><strong>${Math.round(c.wind_gusts_10m)} mph</strong></div>
          <div class="row"><span>Precipitation</span><strong>${c.precipitation} in</strong></div>
        </section>
        <section class="card hourly">
          <h2>Next 24 Hours</h2>
          ${data.hourly.map(h=>`
            <div class="row">
              <span>${h.time.replace('T',' ')}</span>
              <strong>${Math.round(h.temp)}° · ${h.rainChance}% rain · ${Math.round(h.wind)} mph</strong>
            </div>
          `).join('')}
        </section>
      </div>
      <section class="card" style="margin-top:1rem">
        <h2>7-Day Forecast</h2>
        <div class="days">
          ${data.daily.map(d=>`
            <div class="day">
              <strong>${d.date}</strong>
              <p>${d.condition}</p>
              <div>High ${Math.round(d.high)}°</div>
              <div>Low ${Math.round(d.low)}°</div>
              <div>${d.rainChance}% rain</div>
              <div>${Math.round(d.windMax)} mph wind</div>
            </div>
          `).join('')}
        </div>
      </section>`;
  }catch(e){
    root.innerHTML='<div class="card err" style="margin-top:1rem">'+e.message+'</div>';
  }
}
loadWeather();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5077, debug=False, use_reloader=False)
