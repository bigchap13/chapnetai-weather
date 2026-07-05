def build_morning_brief(data):
    return f"""
🌅 WATCHMAN MORNING BRIEF

Programs Active: {data.get('programs_active',0)}
People Monitored: {data.get('people_monitored',0)}
Open Alerts: {data.get('alerts_open',0)}
Risk Flags: {data.get('risk_flags',0)}

Status: {data.get('system_status','GREEN')}
""".strip()

def build_executive_brief(data):
    return f"""
📊 EXECUTIVE BRIEF

Programs: {data.get('programs_active',0)}
AI Agents: {data.get('ai_agents_monitored',0)}
Alerts: {data.get('alerts_open',0)}

System Status:
{data.get('system_status','GREEN')}
""".strip()
