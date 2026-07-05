import json
import subprocess
from pathlib import Path
from datetime import datetime

JJ_DIR = Path.home() / "joshuas-journey-command-center"
JJ_DATA = JJ_DIR / "jj_command_data.json"
JJ_ROUTE_AUDIT = JJ_DIR / "jj_route_audit_report.json"
OUTPUT_FILE = Path("watchman_v105_joshuas_journey_oversight.json")


def load_json(path):
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as exc:
        return {"_error": str(exc)}


def run_git(path, args):
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=path,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return ""
        return result.stdout.strip()
    except Exception:
        return ""


def flatten_count(data):
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        total = 0
        for value in data.values():
            if isinstance(value, list):
                total += len(value)
            elif isinstance(value, dict):
                total += len(value)
        return total if total else len(data)
    return 0


def build_joshuas_journey_oversight():
    jj_data = load_json(JJ_DATA)
    route_audit = load_json(JJ_ROUTE_AUDIT)

    status_raw = run_git(JJ_DIR, ["status", "--short"])
    branch = run_git(JJ_DIR, ["branch", "--show-current"])
    latest_commit = run_git(JJ_DIR, ["log", "--oneline", "-1"])

    risks = []
    recommendations = []

    if "_error" in jj_data:
        risks.append("Joshua's Journey command data could not be read.")
        recommendations.append("Inspect jj_command_data.json for JSON corruption.")

    if "_error" in route_audit:
        risks.append("Joshua's Journey route audit report could not be read.")
        recommendations.append("Inspect jj_route_audit_report.json for JSON corruption.")

    if status_raw.strip():
        risks.append("Joshua's Journey repository has uncommitted changes.")
        recommendations.append("Inspect Joshua's Journey git status before continuing ecosystem work.")

    if not latest_commit:
        risks.append("Joshua's Journey latest commit could not be read.")
        recommendations.append("Inspect Joshua's Journey git log.")

    data_items = flatten_count(jj_data)
    route_audit_items = flatten_count(route_audit)

    if data_items == 0:
        recommendations.append("Joshua's Journey command data appears empty. Validate resident, workforce, recovery, and operations persistence.")

    if route_audit_items == 0:
        recommendations.append("Route audit report appears empty. Re-run route audit if navigation validation is needed.")

    health = "Healthy"
    if risks:
        health = "Watch"

    report = {
        "module": "Watchman V105 Joshua's Journey Oversight",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "joshuas_journey_path": str(JJ_DIR),
        "health": health,
        "git": {
            "branch": branch,
            "latest_commit": latest_commit,
            "dirty": bool(status_raw.strip()),
        },
        "metrics": {
            "jj_command_data_items": data_items,
            "route_audit_items": route_audit_items,
        },
        "risks": risks,
        "recommendations": recommendations,
        "source_files": {
            "jj_command_data": str(JJ_DATA),
            "jj_route_audit_report": str(JJ_ROUTE_AUDIT),
        },
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == "__main__":
    report = build_joshuas_journey_oversight()
    print(json.dumps(report, indent=2))
