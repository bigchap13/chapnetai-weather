def smart_home_status():
    return {
        "enabled": False,
        "mode": "simulation",
        "status": "ready",
        "devices_connected": 0
    }

def create_device(device_id, name, device_type, room="general", status="offline"):
    return {
        "device_id": device_id,
        "name": name,
        "type": device_type,
        "room": room,
        "status": status
    }

def default_devices():
    return [
        create_device("light-001", "Morning Lights", "light", "main"),
        create_device("alarm-001", "House Wake-Up Alarm", "alarm", "house"),
        create_device("thermo-001", "House Thermostat", "thermostat", "house"),
        create_device("announce-001", "House Announcement Speaker", "speaker", "house")
    ]
