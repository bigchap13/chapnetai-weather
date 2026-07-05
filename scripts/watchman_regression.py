import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import app

client = app.test_client()

tests = [
    ("weather city", "what is the weather in Seattle Washington", "Watchman AI Copilot"),
    ("weather plain", "what is the weather in Denver", "Watchman AI Copilot"),
    ("capital", "what is the capital of Oregon", "Watchman Geography Knowledge"),
    ("distance", "how many miles to Atlanta", "Watchman Navigation Distance"),
    ("route plan", "plan a route to Chattanooga", "Watchman Navigation Route"),
    ("travel decision", "should I drive to Nashville today", "Watchman Travel Decision"),
    ("departure", "when should I leave for Nashville", "Watchman Travel Decision"),
    ("road safety", "are roads safe near Birmingham Alabama", "Watchman Road Safety"),
    ("sunrise", "what time is sunrise in Miami", "Watchman AI Copilot"),
    ("route weather", "what is the weather along the route from Birmingham to Atlanta", "Watchman AI Copilot"),
    ("comparison or", "which has better weather today, Seattle or Los Angeles", "Watchman Weather Comparison"),
    ("comparison between", "compare weather between Denver and Phoenix", "Watchman Weather Comparison"),
    ("gas gps-needed", "find gas near me", "Watchman Live Local Services"),
    ("hospital gps-needed", "find a hospital near me", "Watchman Live Local Services"),

    ("weather biloxi", "what is the weather in Biloxi", "Watchman AI Copilot"),
    ("temperature phoenix", "how hot is Phoenix right now", "Watchman AI Copilot"),
    ("sunset seattle", "what time is sunset in Seattle", "Watchman AI Copilot"),
    ("capital texas", "capital of Texas", "Watchman Geography Knowledge"),
    ("road jasper", "are roads safe near Jasper Alabama", "Watchman Road Safety"),
    ("route navigate", "navigate to Nashville", "Watchman Navigation Route"),
    ("departure atlanta", "best time to leave for Atlanta", "Watchman Travel Decision"),
    ("comparison vs", "compare weather in Miami vs Tampa", "Watchman Weather Comparison"),

    # Priority guards: these catch router/module stealing regressions.
    ("priority temperature city", "how hot is Phoenix right now", "Watchman AI Copilot"),
    ("priority route weather", "what is the weather along the route from Birmingham to Atlanta", "Watchman AI Copilot"),
    ("priority travel decision", "should I drive to Nashville today", "Watchman Travel Decision"),
    ("priority weather comparison", "which has better weather today, Seattle or Los Angeles", "Watchman Weather Comparison"),
]

bad = []

for name, q, expected_mode in tests:
    r = client.get("/api/copilot/ask?q=" + q.replace(" ", "%20"))
    data = json.loads(r.get_data(as_text=True))
    mode = data.get("mode")
    answer = data.get("answer") or ""

    ok = r.status_code < 500 and mode == expected_mode
    if "briefing unavailable" in answer.lower():
        ok = False
    if "unknown at unknown/100" in answer.lower():
        ok = False

    print("=" * 90)
    print("TEST:", name)
    print("QUESTION:", q)
    print("STATUS:", r.status_code)
    print("EXPECTED:", expected_mode)
    print("MODE:", mode)
    print("PASS:", ok)
    print("ANSWER:", answer[:800])

    if not ok:
        bad.append((name, q, expected_mode, mode, answer[:300]))

print("=" * 90)
print("FAILURES:", bad or "none")

if bad:
    raise SystemExit(1)

print("FULL REGRESSION PASS")
