import json
import urllib.request

NWS_ACTIVE_ALERTS_URL = "https://api.weather.gov/alerts/active"


def _fetch_active_alerts():
    req = urllib.request.Request(
        NWS_ACTIVE_ALERTS_URL,
        headers={
            "User-Agent": "ChapNetAI-Weather-Watchman/1.0",
            "Accept": "application/geo+json",
        },
    )

    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def national_alert_scan():
    data = _fetch_active_alerts()
    features = data.get("features") or []

    tornado = []
    severe = []
    flood = []

    for item in features:
        props = item.get("properties") or {}

        event = props.get("event") or ""
        headline = props.get("headline") or ""
        area = props.get("areaDesc") or ""
        severity = props.get("severity") or ""
        urgency = props.get("urgency") or ""

        row = {
            "event": event,
            "headline": headline,
            "area": area,
            "severity": severity,
            "urgency": urgency,
        }

        low = event.lower()

        if "tornado" in low:
            tornado.append(row)
        elif "severe thunderstorm" in low:
            severe.append(row)
        elif "flood" in low:
            flood.append(row)

    return {
        "mode": "Watchman National Alert Scan",
        "totalActiveAlerts": len(features),
        "tornadoCount": len(tornado),
        "severeThunderstormCount": len(severe),
        "floodCount": len(flood),
        "tornadoAlerts": tornado[:10],
        "severeThunderstormAlerts": severe[:10],
        "floodAlerts": flood[:10],
    }


def is_national_alert_question(question):
    q = str(question or "").lower()

    national_trigger = any(
        token in q
        for token in [
            "anywhere",
            "united states",
            " u.s.",
            " u s ",
            " usa",
            "america",
            "national",
            "across the country",
            "in the country",
        ]
    )

    alert_trigger = any(
        token in q
        for token in [
            "tornado",
            "tornadoes",
            "severe",
            "warning",
            "warnings",
            "watch",
            "watches",
            "alerts",
        ]
    )

    return national_trigger and alert_trigger


def answer_national_alert_question(question):
    scan = national_alert_scan()
    q = str(question or "").lower()

    if "tornado" in q:
        if scan["tornadoCount"] > 0:
            first = scan["tornadoAlerts"][0]
            return {
                "answer": (
                    f"Yes. Watchman found {scan['tornadoCount']} active tornado-related alert(s). "
                    f"First alert: {first.get('event')} for {first.get('area')}. "
                    f"Headline: {first.get('headline')}"
                ),
                "scan": scan,
            }

        return {
            "answer": "No active tornado-related NWS alerts were found in this Watchman national scan.",
            "scan": scan,
        }

    return {
        "answer": (
            f"Watchman national scan found {scan['totalActiveAlerts']} total active NWS alert(s), "
            f"{scan['tornadoCount']} tornado-related, "
            f"{scan['severeThunderstormCount']} severe-thunderstorm-related, "
            f"and {scan['floodCount']} flood-related."
        ),
        "scan": scan,
    }
