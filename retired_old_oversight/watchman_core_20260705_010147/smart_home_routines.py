def routine(name, time, action, target):
    return {
        "name": name,
        "time": time,
        "action": action,
        "target": target,
        "status": "scheduled"
    }

def default_house_routines():
    return [
        routine("Wake-Up Alarm", "07:00", "alarm_on", "alarm-001"),
        routine("Morning Lights On", "07:15", "lights_on", "light-001"),
        routine("Morning Check-In Reminder", "08:00", "announce", "announce-001"),
        routine("Evening Meeting Reminder", "18:00", "announce", "announce-001"),
        routine("Quiet Hours", "22:00", "lights_dim", "light-001")
    ]
