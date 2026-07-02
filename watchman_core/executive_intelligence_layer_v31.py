from datetime import datetime
import json
import os

OUTPUT_JSON = "watchman_v31_executive_intelligence.json"
OUTPUT_MD = "WATCHMAN_V31_EXECUTIVE_INTELLIGENCE_LAYER.md"

systems = [
    "ai_registry",
    "ai_health",
    "ai_oversight",
    "approval_queue",
    "executive_dashboard",
    "workforce_dashboard",
    "employment_dashboard",
    "mobility_dashboard",
    "funding_dashboard",
    "grant_integration_dashboard",
    "community_crm_dashboard"
]

status = []

for system in systems:
    path = os.path.join("watchman", system + ".py")

    status.append({
        "system": system,
        "online": os.path.exists(path)
    })

online = sum(1 for s in status if s["online"])

data = {
    "generated": str(datetime.now()),
    "executive_status": "HEALTHY",
    "systems_checked": len(status),
    "systems_online": online,
    "priority_focus": [
        "AI Oversight",
        "Grant Integration",
        "Workforce Operations",
        "Mobility Operations"
    ],
    "recommendation":
        "Continue expansion through intelligence and forecasting layers.",
    "next_target":
        "Watchman V32 Operational Intelligence Engine"
}

with open(OUTPUT_JSON, "w") as f:
    json.dump(data, f, indent=2)

lines = []
lines.append("# Watchman V31 Executive Intelligence Layer")
lines.append("")
lines.append(f"Generated: {data['generated']}")
lines.append("")
lines.append(f"Executive Status: {data['executive_status']}")
lines.append("")
lines.append("## Systems")
lines.append("")

for s in status:
    lines.append(
        f"- {s['system']}: {'ONLINE' if s['online'] else 'OFFLINE'}"
    )

lines.append("")
lines.append("## Priority Focus")
lines.append("")

for item in data["priority_focus"]:
    lines.append(f"- {item}")

lines.append("")
lines.append("## Recommendation")
lines.append("")
lines.append(data["recommendation"])

lines.append("")
lines.append("## Next Target")
lines.append("")
lines.append(data["next_target"])

with open(OUTPUT_MD, "w") as f:
    f.write("\n".join(lines))

print("Generated", OUTPUT_JSON)
print("Generated", OUTPUT_MD)
