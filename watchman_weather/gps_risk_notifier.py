_LAST_GPS_RISK = {}


def _key(label):
    return str(label or "Phone GPS").strip().lower()


def _rank(value):
    order = {
        "unknown": 0,
        "low": 1,
        "guarded": 2,
        "possible": 3,
        "elevated": 4,
        "high": 5,
        "extreme": 6,
    }
    return order.get(str(value or "unknown").lower(), 0)


def gps_risk_change_notifier(label, gps_result):
    label = label or "Phone GPS"
    gps_result = gps_result or {}
    decision = gps_result.get("decision") or {}
    impact = gps_result.get("impact") or {}

    state = {
        "decision": decision.get("decision"),
        "severity": decision.get("severity"),
        "score": decision.get("score"),
        "primaryThreat": decision.get("primaryThreat"),
        "impact": impact.get("highestImpact"),
        "trackedCells": impact.get("trackedCells"),
    }

    old = _LAST_GPS_RISK.get(_key(label))
    _LAST_GPS_RISK[_key(label)] = state

    if not old:
        return {
            "mode": "Watchman GPS Risk Change Notifier V1",
            "changed": False,
            "firstScan": True,
            "changes": ["GPS risk baseline created."],
            "previous": None,
            "current": state,
        }

    changes = []

    if state.get("decision") != old.get("decision"):
        changes.append(f"decision changed from {old.get('decision')} to {state.get('decision')}")

    if state.get("severity") != old.get("severity"):
        changes.append(f"severity changed from {old.get('severity')} to {state.get('severity')}")

    if state.get("impact") != old.get("impact"):
        changes.append(f"impact changed from {old.get('impact')} to {state.get('impact')}")

    old_score = old.get("score") or 0
    new_score = state.get("score") or 0
    if abs(new_score - old_score) >= 10:
        changes.append(f"score changed from {old_score} to {new_score}")

    escalated = (
        _rank(state.get("severity")) > _rank(old.get("severity"))
        or _rank(state.get("impact")) > _rank(old.get("impact"))
        or (new_score - old_score) >= 10
    )

    return {
        "mode": "Watchman GPS Risk Change Notifier V1",
        "changed": bool(changes),
        "escalated": escalated,
        "firstScan": False,
        "changes": changes or ["No meaningful GPS risk change detected."],
        "previous": old,
        "current": state,
    }


def gps_risk_notifier_summary():
    return {
        "mode": "Watchman GPS Risk Change Notifier V1",
        "tracked": _LAST_GPS_RISK,
    }
