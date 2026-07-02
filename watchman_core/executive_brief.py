from watchman.executive_dashboard import executive_dashboard

def generate_executive_brief():
    data = executive_dashboard()

    r = data["resident_summary"]

    lines = [
        "WATCHMAN EXECUTIVE COMMAND BRIEF",
        "",
        f"System Status: {data['system_status']}",
        "",
        f"Residents Active: {r['residents_active']}",
        f"Average Readiness: {r['average_readiness']}",
        f"Employment Ready: {r['employment_ready']}",
        f"Transportation Requests: {r['transportation_requests']}",
        f"Wellness Alerts: {r['wellness_alerts']}",
        "",
        f"AI Agents: {data['ai_oversight']['total_agents']}",
        f"AI Escalations: {data['ai_oversight']['escalations_required']}",
        "",
        f"Telegram Enabled: {data['telegram']['enabled']}",
        f"Smart Home Enabled: {data['smart_home']['enabled']}"
    ]

    return "\n".join(lines)
