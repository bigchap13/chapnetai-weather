import json
from pathlib import Path
from datetime import datetime

GRANTFINDER_DIR = Path.home() / "grantfinder"
GRANT_DATA = GRANTFINDER_DIR / "grant_data.json"
DISCOVERED_OPPORTUNITIES = GRANTFINDER_DIR / "discovered_opportunities.json"
REAL_SOURCES = GRANTFINDER_DIR / "real_opportunity_sources.json"
OUTPUT_FILE = Path("watchman_v103_grantfinder_oversight.json")


def load_json(path):
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as exc:
        return {"_error": str(exc)}


def item_count(value):
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        return len(value)
    return 0


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


def build_grantfinder_oversight():
    grant_data = load_json(GRANT_DATA)
    discovered = load_json(DISCOVERED_OPPORTUNITIES)
    sources = load_json(REAL_SOURCES)

    risks = []
    recommendations = []

    if "_error" in grant_data:
        risks.append("Grant Finder grant_data.json could not be read.")
        recommendations.append("Inspect grantfinder/grant_data.json for JSON corruption.")

    if "_error" in discovered:
        risks.append("Grant Finder discovered_opportunities.json could not be read.")
        recommendations.append("Inspect grantfinder/discovered_opportunities.json for JSON corruption.")

    if "_error" in sources:
        risks.append("Grant Finder real_opportunity_sources.json could not be read.")
        recommendations.append("Inspect grantfinder/real_opportunity_sources.json for JSON corruption.")

    grant_data_count = flatten_count(grant_data)
    discovered_count = flatten_count(discovered)
    source_count = flatten_count(sources)

    if discovered_count == 0:
        risks.append("No discovered opportunities detected.")
        recommendations.append("Run or validate Grant Finder opportunity discovery.")

    if source_count == 0:
        risks.append("No real opportunity sources detected.")
        recommendations.append("Validate Grant Finder source registry.")

    if grant_data_count == 0:
        recommendations.append("Grant data appears empty. Confirm pipeline, draft, and match data are being saved.")

    health = "Healthy"
    if risks:
        health = "Watch"

    report = {
        "module": "Watchman V103 Grant Finder Oversight",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "grantfinder_path": str(GRANTFINDER_DIR),
        "health": health,
        "metrics": {
            "grant_data_items": grant_data_count,
            "discovered_opportunity_items": discovered_count,
            "real_source_items": source_count,
        },
        "risks": risks,
        "recommendations": recommendations,
        "source_files": {
            "grant_data": str(GRANT_DATA),
            "discovered_opportunities": str(DISCOVERED_OPPORTUNITIES),
            "real_opportunity_sources": str(REAL_SOURCES),
        }
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == "__main__":
    report = build_grantfinder_oversight()
    print(json.dumps(report, indent=2))
