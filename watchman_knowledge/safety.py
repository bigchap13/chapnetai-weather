def safety_actions(weather):
    weather = weather or {}
    alerts = weather.get("alerts") or []
    watchman = weather.get("watchman") or {}
    storm = watchman.get("stormTracker") or {}
    intel = watchman.get("liveStormIntelligence") or {}

    text = " ".join(
        str(a.get("event", "")) + " " + str(a.get("headline", "")) + " " + str(a.get("description", ""))
        for a in alerts if isinstance(a, dict)
    ).lower()

    actions = []
    avoid = []
    watch_for = []

    if "tornado warning" in text:
        actions += ["Move to shelter immediately.", "Use an interior room on the lowest floor.", "Stay away from windows."]
        avoid += ["Do not wait outside to look for the tornado.", "Do not drive into warned areas."]
        watch_for += ["Official NWS warning updates.", "Sirens or emergency alerts."]

    if "severe thunderstorm" in text or storm.get("nearestStorm") == "Detected":
        actions += ["Move indoors if thunder is heard.", "Secure loose outdoor items.", "Keep radar open."]
        avoid += ["Avoid open fields, water, tall trees, and metal equipment."]
        watch_for += ["Lightning, damaging wind, hail, and sudden heavy rain."]

    if "heat advisory" in text or intel.get("heatSignal") == "detected":
        actions += ["Drink water often.", "Take breaks in shade or air conditioning.", "Check on elderly people and pets."]
        avoid += ["Avoid heavy outdoor work during peak heat.", "Do not leave children or pets in vehicles."]
        watch_for += ["Dizziness, confusion, heavy sweating, or heat exhaustion symptoms."]

    if "flood" in text or intel.get("floodSignal") == "detected":
        actions += ["Avoid low-water crossings.", "Move away from flood-prone roads.", "Keep alerts enabled."]
        avoid += ["Never drive through water-covered roads."]
        watch_for += ["Rapid rises in creeks, poor drainage flooding, and road closures."]

    if not actions:
        actions = ["No immediate emergency action is indicated by the current Watchman scan."]
        avoid = ["Avoid ignoring changing conditions."]
        watch_for = ["New alerts, radar changes, and Watchman change detection."]

    return {
        "doNow": actions,
        "avoid": avoid,
        "watchFor": watch_for,
    }
