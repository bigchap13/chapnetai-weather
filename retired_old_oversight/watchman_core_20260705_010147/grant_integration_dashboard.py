from .grantfinder_sync import grantfinder_sync_status
from .grant_matcher import grant_matches
from .funding_need_mapper import funding_needs

def grant_integration_dashboard():
    needs = funding_needs()
    matches = grant_matches()
    sync = grantfinder_sync_status()

    return {
        "dashboard": "Grant Finder Integration Layer",
        "funding_needs": len(needs),
        "grant_matches": len(matches),
        "sync": sync,
        "needs": needs,
        "matches": matches,
        "status": "operational"
    }

def format_grant_integration_dashboard(data):
    lines = [
        "WATCHMAN GRANT FINDER INTEGRATION LAYER",
        "",
        f"Funding Needs: {data['funding_needs']}",
        f"Grant Matches: {data['grant_matches']}",
        f"Sync Status: {data['sync']['sync_status']}",
        "",
        "MATCHES:"
    ]

    if data["matches"]:
        for match in data["matches"]:
            lines.append(
                f"- {match['need']} -> {match['grant']} | Priority: {match['priority']} | Fit: {match['fit']}"
            )
    else:
        lines.append("- No matches currently available.")

    return "\n".join(lines)
