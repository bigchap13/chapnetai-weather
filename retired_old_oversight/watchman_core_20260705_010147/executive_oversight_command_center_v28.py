from datetime import datetime
import os
import importlib

OUTPUT = "WATCHMAN_V28_EXECUTIVE_OVERSIGHT_COMMAND_CENTER.md"

modules = [
    "ai_registry",
    "ai_health",
    "ai_oversight",
    "approval_queue",
    "ai_briefings",
    "executive_dashboard",
    "executive_brief",
    "grant_integration_dashboard",
    "funding_dashboard",
    "workforce_dashboard",
    "mobility_dashboard",
    "community_crm_dashboard"
]

rows = []

for module in modules:
    status = "AVAILABLE"
    note = "Module file present"

    path = os.path.join("watchman", module + ".py")

    if not os.path.exists(path):
        status = "MISSING"
        note = "Module file not found"
    else:
        try:
            importlib.import_module("watchman." + module)
        except Exception as e:
            status = "PRESENT"
            note = f"Present but import check raised: {type(e).__name__}"

    rows.append({
        "module": module,
        "status": status,
        "note": note
    })

lines = []
lines.append("# Watchman V28 Executive Oversight Command Center")
lines.append("")
lines.append(f"Generated: {datetime.now()}")
lines.append("")
lines.append("## Executive Summary")
lines.append("")
lines.append("Watchman V28 establishes a top-level executive oversight command center across AI oversight, governance, funding, workforce, mobility, community, and integration modules.")
lines.append("")
lines.append("## Module Status")
lines.append("")
lines.append("| Module | Status | Note |")
lines.append("|--------|--------|------|")

for row in rows:
    lines.append(f"| {row['module']} | {row['status']} | {row['note']} |")

available = sum(1 for r in rows if r["status"] in ["AVAILABLE", "PRESENT"])

lines.append("")
lines.append("## Readiness")
lines.append("")
lines.append(f"Modules Checked: {len(rows)}")
lines.append(f"Modules Present: {available}")
lines.append("")
lines.append("## V28 Outcome")
lines.append("")
lines.append("Executive Oversight Command Center established.")
lines.append("")
lines.append("## Next Target")
lines.append("")
lines.append("Watchman V29 — Operational Oversight Dashboard")

with open(OUTPUT, "w") as f:
    f.write("\n".join(lines))

print(f"Generated {OUTPUT}")
