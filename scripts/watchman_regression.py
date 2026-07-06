import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app
import json
from urllib.parse import quote

client = app.test_client()

tests = [
    ("what is the weather in Laramie Wyoming", "Watchman AI Copilot", "Laramie"),
    ("weather in Tupelo Mississippi", "Watchman AI Copilot", "Tupelo"),
    ("how hot is El Paso right now", "Watchman AI Copilot", "El Paso"),
    ("what time is sunrise in Pensacola", "Watchman AI Copilot", "Sunrise"),
    ("what time is sunset in Helena Montana", "Watchman AI Copilot", "Sunset"),

    ("compare weather between Fargo and Charleston", "Watchman Weather Comparison", "Fargo"),
    ("which has better weather today, Knoxville or Topeka", "Watchman Weather Comparison", "Knoxville"),

    ("capital of Vermont", "Watchman Geography Knowledge", "Montpelier"),
    ("what is the capital of New Mexico", "Watchman Geography Knowledge", "Santa Fe"),

    ("are roads safe near Rapid City South Dakota", "Watchman Road Safety", "Road readout"),
    ("should I drive to Missoula today", "Watchman Travel Decision", "Travel readout"),
    ("when should I leave for Savannah Georgia", "Watchman Travel Decision", "Travel readout"),

    ("what is the weather along the route from Huntsville to Memphis", "Watchman AI Copilot", "Route Intelligence V2"),

    ("find gas near me", "Watchman Live Local Services", "GPS permission"),
    ("find a hospital near me", "Watchman Live Local Services", "GPS permission"),
    ("find food on my route to Little Rock", "Watchman Route Stop Search", "GPS permission"),
    ("find a hotel on the way to Knoxville", "Watchman Route Stop Search", "GPS permission"),
]

bad = []

for q, expected, must in tests:
    r = client.get("/api/copilot/ask?q=" + quote(q))
    data = json.loads(r.get_data(as_text=True))
    mode = data.get("mode")
    answer = data.get("answer") or ""
    ok = r.status_code < 500 and mode == expected and must.lower() in answer.lower()

    print("=" * 90)
    print("QUESTION:", q)
    print("EXPECTED:", expected)
    print("MODE:", mode)
    print("PASS:", ok)
    print("ANSWER:", answer[:900])

    if not ok:
        bad.append((q, expected, mode, must, answer[:300]))

if bad:
    print("\nFAILURES:")
    for item in bad:
        print(item)
    raise SystemExit(1)

print("\nVARIED REGRESSION PASS")
