import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:5077"

ROUTES = [
    "/health",
    "/api/nws?place=Jasper,%20Alabama",
    "/api/briefing?place=Jasper,%20Alabama",
    "/api/copilot/ask?place=Jasper,%20Alabama&q=What%20is%20the%20biggest%20risk%20right%20now%3F",
    "/api/watchman/decision?place=Jasper,%20Alabama",
    "/api/watchman/mission?place=Jasper,%20Alabama&mission=mow",
    "/api/watchman/mission-time-machine?place=Jasper,%20Alabama&mission=mow",
    "/api/watchman/decision-explanation?place=Jasper,%20Alabama",
    "/api/watchman/weather-memory?place=Jasper,%20Alabama",
    "/api/watchman/notification-diagnostic?place=Jasper,%20Alabama",
    "/api/watchman/live-timeline?place=Jasper,%20Alabama",
    "/api/watchman/gps-impact?lat=33.8312&lon=-87.2775&label=Audit%20GPS",
    "/api/watchman/gps-watch/status",
    "/api/watchman/notifications",
]

PAGE_TOKENS = [
    "ChapNetAI Weather",
    "Run Watchman Scan",
    "Ask Watchman",
    'id="place"',
    'id="app"',
    "Mission Planner",
    "Mission Time Machine",
    "Weather Memory",
    "async function loadWeather",
]


def sh(cmd):
    return subprocess.run(cmd, cwd=ROOT, shell=True, text=True, capture_output=True)


def fetch(path, timeout=45):
    with urlopen(BASE + path, timeout=timeout) as r:
        body = r.read().decode("utf-8", errors="replace")
        return r.status, body


def main():
    report = {
        "status": "pass",
        "checks": [],
        "failures": [],
    }

    py_files = ["app.py"] + [str(p) for p in sorted((ROOT / "watchman_knowledge").glob("*.py"))]
    compile_cmd = "python -m py_compile " + " ".join(py_files)
    c = sh(compile_cmd)
    ok = c.returncode == 0
    report["checks"].append({"name": "python_compile", "ok": ok})
    if not ok:
        report["status"] = "fail"
        report["failures"].append({"name": "python_compile", "stderr": c.stderr[-4000:]})

    routes_raw = sh("grep -Rho \"@app.route([^)]*)\" app.py | sort | uniq -c | sort -nr")
    duplicates = []
    for line in routes_raw.stdout.splitlines():
        parts = line.strip().split(maxsplit=1)
        if len(parts) == 2 and parts[0].isdigit() and int(parts[0]) > 1:
            duplicates.append(line.strip())
    ok = not duplicates
    report["checks"].append({"name": "duplicate_routes", "ok": ok, "duplicates": duplicates})
    if not ok:
        report["status"] = "fail"
        report["failures"].append({"name": "duplicate_routes", "duplicates": duplicates})

    try:
        status, page = fetch("/")
        ok = status == 200
    except Exception as e:
        page = ""
        ok = False
        report["failures"].append({"name": "homepage_fetch", "error": str(e)})
    report["checks"].append({"name": "homepage_200", "ok": ok})

    missing_tokens = [t for t in PAGE_TOKENS if t not in page]
    ok = not missing_tokens
    report["checks"].append({"name": "homepage_tokens", "ok": ok, "missing": missing_tokens})
    if not ok:
        report["status"] = "fail"
        report["failures"].append({"name": "homepage_tokens", "missing": missing_tokens})

    for route in ROUTES:
        try:
            route_timeout = 75 if any(x in route for x in ["copilot/ask", "watchman/decision", "gps-impact"]) else 45
            status, body = fetch(route, timeout=route_timeout)
            parsed = json.loads(body)
            ok = status == 200 and isinstance(parsed, dict)
            report["checks"].append({
                "name": "route",
                "route": route,
                "ok": ok,
                "status_code": status,
                "mode": parsed.get("mode"),
                "app": parsed.get("app"),
            })
            if not ok:
                report["status"] = "fail"
                report["failures"].append({"name": "route", "route": route, "status_code": status})
        except Exception as e:
            report["status"] = "fail"
            report["checks"].append({"name": "route", "route": route, "ok": False})
            report["failures"].append({"name": "route", "route": route, "error": str(e)})

    out = ROOT / "reports" / "watchman_full_audit_latest.json"
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
