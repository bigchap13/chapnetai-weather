from datetime import datetime
import os
import json

OUTPUT_MD = "WATCHMAN_V29_OPERATIONAL_OVERSIGHT_DASHBOARD.md"
OUTPUT_HTML = "watchman_v29_operational_oversight_dashboard.html"
OUTPUT_JSON = "watchman_v29_operational_status.json"

modules = [
    "ai_registry",
    "ai_health",
    "ai_oversight",
    "approval_queue",
    "ai_briefings",
    "executive_dashboard",
    "executive_brief",
    "workforce_dashboard",
    "employment_dashboard",
    "mobility_dashboard",
    "funding_dashboard",
    "grant_integration_dashboard",
    "community_crm_dashboard"
]

rows = []

for module in modules:
    path = os.path.join("watchman", module + ".py")
    exists = os.path.exists(path)

    rows.append({
        "module": module,
        "file": path,
        "status": "ONLINE" if exists else "MISSING",
        "category": "Operational Module"
    })

online = sum(1 for row in rows if row["status"] == "ONLINE")

data = {
    "generated": str(datetime.now()),
    "dashboard": "Watchman V29 Operational Oversight Dashboard",
    "modules_checked": len(rows),
    "modules_online": online,
    "operational_readiness": round((online / len(rows)) * 100, 2),
    "modules": rows
}

with open(OUTPUT_JSON, "w") as f:
    json.dump(data, f, indent=2)

md = []
md.append("# Watchman V29 Operational Oversight Dashboard")
md.append("")
md.append(f"Generated: {data['generated']}")
md.append("")
md.append("## Summary")
md.append("")
md.append(f"Modules Checked: {data['modules_checked']}")
md.append(f"Modules Online: {data['modules_online']}")
md.append(f"Operational Readiness: {data['operational_readiness']}%")
md.append("")
md.append("## Module Status")
md.append("")
md.append("| Module | Status | File |")
md.append("|--------|--------|------|")

for row in rows:
    md.append(f"| {row['module']} | {row['status']} | {row['file']} |")

md.append("")
md.append("## Outcome")
md.append("")
md.append("Operational Oversight Dashboard established.")
md.append("")
md.append("## Next Target")
md.append("")
md.append("Watchman V30 — Major Executive Operations Platform")

with open(OUTPUT_MD, "w") as f:
    f.write("\n".join(md))

html_rows = ""

for row in rows:
    html_rows += f"""
    <tr>
      <td>{row['module']}</td>
      <td>{row['status']}</td>
      <td>{row['file']}</td>
    </tr>
    """

html = f"""
<!DOCTYPE html>
<html>
<head>
<title>Watchman V29 Operational Oversight Dashboard</title>
<style>
body {{
  background:#07111f;
  color:white;
  font-family:Arial;
  padding:20px;
}}
.card {{
  background:#10243d;
  padding:16px;
  border-radius:12px;
  margin:12px 0;
}}
h1,h2 {{
  color:#6ec1ff;
}}
table {{
  width:100%;
  border-collapse:collapse;
}}
td, th {{
  border:1px solid #2d4a69;
  padding:10px;
}}
th {{
  color:#6ec1ff;
}}
.metric {{
  font-size:30px;
  font-weight:bold;
}}
</style>
</head>
<body>

<h1>Watchman V29 Operational Oversight Dashboard</h1>

<div class="card">
<h2>Operational Readiness</h2>
<div class="metric">{data['operational_readiness']}%</div>
<p>Generated: {data['generated']}</p>
</div>

<div class="card">
<h2>Module Coverage</h2>
<p>{data['modules_online']}/{data['modules_checked']} modules online</p>
</div>

<table>
<tr>
<th>Module</th>
<th>Status</th>
<th>File</th>
</tr>
{html_rows}
</table>

</body>
</html>
"""

with open(OUTPUT_HTML, "w") as f:
    f.write(html)

print("Generated", OUTPUT_MD)
print("Generated", OUTPUT_HTML)
print("Generated", OUTPUT_JSON)
