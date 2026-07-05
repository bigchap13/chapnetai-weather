def build_alert_message(title, message, priority="normal"):
    return f"""
🚨 WATCHMAN ALERT

Priority: {priority.upper()}

{title}

{message}
""".strip()
