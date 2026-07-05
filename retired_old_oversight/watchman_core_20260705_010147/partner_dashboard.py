from .employer_scorecard import employer_scorecard

def partner_dashboard():
    scorecards = employer_scorecard()

    return {
        "dashboard": "Employer Partner Network",
        "active_partners": len([e for e in scorecards if e["status"] in ["active", "prospect"]]),
        "open_positions": sum(e["open_positions"] for e in scorecards),
        "applications_sent": sum(e["applications_sent"] for e in scorecards),
        "interviews_generated": sum(e["interviews_generated"] for e in scorecards),
        "offers_generated": sum(e["offers_generated"] for e in scorecards),
        "hires_generated": sum(e["hires_generated"] for e in scorecards),
        "retained_30_days": sum(e["retained_30_days"] for e in scorecards),
        "employers": scorecards
    }

def format_partner_dashboard(data):
    lines = [
        "WATCHMAN EMPLOYER PARTNER NETWORK",
        "",
        f"Active / Prospect Partners: {data['active_partners']}",
        f"Open Positions: {data['open_positions']}",
        f"Applications Sent: {data['applications_sent']}",
        f"Interviews Generated: {data['interviews_generated']}",
        f"Offers Generated: {data['offers_generated']}",
        f"Hires Generated: {data['hires_generated']}",
        f"Retained 30 Days: {data['retained_30_days']}",
        "",
        "EMPLOYERS:"
    ]

    for employer in data["employers"]:
        lines.append(
            f"- {employer['name']} | {employer['industry']} | Open: {employer['open_positions']} | Hires: {employer['hires_generated']}"
        )

    return "\n".join(lines)
