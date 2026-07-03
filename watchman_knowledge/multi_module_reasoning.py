def _safe_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        return {
            "mode": getattr(fn, "__name__", "unknown"),
            "error": str(e),
        }


def _score_value(item):
    if not isinstance(item, dict):
        return None

    for key in ["score", "skyScore", "illuminationPercent"]:
        if key in item:
            try:
                return int(item[key])
            except Exception:
                pass

    verdict = str(item.get("verdict", "")).upper()
    if verdict in ["YES", "GO", "GOOD", "SAFE", "NORMAL", "BEST"]:
        return 85
    if verdict in ["CAUTION", "FAIR", "MODERATE", "OK"]:
        return 55
    if verdict in ["NO", "DELAY", "POOR", "HIGH", "KEEP INSIDE", "DO NOT LAUNCH", "AVOID"]:
        return 25

    return None


def _collect_risks(results):
    risks = []

    for item in results:
        if not isinstance(item, dict):
            continue

        for key in ["risks", "evidence", "skyRisks", "hazards"]:
            values = item.get(key)
            if isinstance(values, list):
                risks.extend(str(v) for v in values[:4])

        if item.get("recommendation"):
            risks.append(str(item.get("recommendation")))

    clean = []
    for r in risks:
        r = r.strip()
        if r and r not in clean:
            clean.append(r)

    return clean[:10]


def _detect_focus(question):
    q = str(question or "").lower()

    if any(x in q for x in ["fish", "fishing", "boat", "lake", "kayak", "swim"]):
        return "water"
    if any(x in q for x in ["drive", "leave", "commute", "travel", "road", "trip"]):
        return "travel"
    if any(x in q for x in ["mow", "roof", "paint", "concrete", "construction", "yard", "work outside"]):
        return "outdoor_work"
    if any(x in q for x in ["dog", "pet", "livestock", "horse", "cat"]):
        return "pets"
    if any(x in q for x in ["stargazing", "meteor", "moon", "milky way", "astronomy", "golden hour", "sunrise", "sunset"]):
        return "astronomy"
    if any(x in q for x in ["practice", "game", "party", "wedding", "event", "cookout"]):
        return "event"

    return "general"


def multi_module_reasoning(question, weather):
    from watchman_knowledge.decision_intelligence import decision_intelligence
    from watchman_knowledge.intelligence import intelligence_summary
    from watchman_knowledge.travel_intelligence import travel_intelligence
    from watchman_knowledge.lightning_intelligence import lightning_intelligence
    from watchman_knowledge.outdoor_work import outdoor_work_intelligence
    from watchman_knowledge.event_intelligence import event_intelligence
    from watchman_knowledge.pet_livestock import pet_livestock_intelligence
    from watchman_knowledge.marine_lake import marine_lake_intelligence
    from watchman_knowledge.moon_phase import moon_phase_intelligence
    from watchman_knowledge.twilight import twilight_intelligence
    from watchman_knowledge.solar_times import solar_times_intelligence

    focus = _detect_focus(question)

    modules = {
        "decision": _safe_call(decision_intelligence, question, weather),
        "hazards": _safe_call(intelligence_summary, weather),
        "lightning": _safe_call(lightning_intelligence, question, weather),
    }

    if focus in ["travel", "general"]:
        modules["travel"] = _safe_call(travel_intelligence, question, weather)

    if focus in ["outdoor_work", "general"]:
        modules["outdoorWork"] = _safe_call(outdoor_work_intelligence, weather)

    if focus in ["event", "general"]:
        modules["event"] = _safe_call(event_intelligence, weather)

    if focus in ["pets", "general"]:
        modules["petLivestock"] = _safe_call(pet_livestock_intelligence, weather)

    if focus in ["water", "general"]:
        modules["marineLake"] = _safe_call(marine_lake_intelligence, weather)

    if focus in ["astronomy", "water", "general"]:
        modules["moonPhase"] = _safe_call(moon_phase_intelligence, question, weather)
        modules["twilight"] = _safe_call(twilight_intelligence, question, weather)
        modules["solarTimes"] = _safe_call(solar_times_intelligence, question, weather)

    scored = []
    for name, item in modules.items():
        value = _score_value(item)
        if value is not None:
            scored.append(value)

    if scored:
        combined_score = max(0, min(100, int(sum(scored) / len(scored))))
    else:
        combined_score = 50

    decision = modules.get("decision", {})
    risks = _collect_risks(list(modules.values()))

    if combined_score >= 75:
        verdict = "YES"
        recommendation = "Conditions look usable, but recheck Watchman before starting."
    elif combined_score >= 45:
        verdict = "CAUTION"
        recommendation = "Conditions are mixed. Proceed only with monitoring and a backup plan."
    else:
        verdict = "NO"
        recommendation = "Delay if possible until risk signals improve."

    if isinstance(decision, dict) and decision.get("verdict") in ["NO", "CAUTION", "YES"]:
        verdict = decision.get("verdict")
        recommendation = decision.get("recommendation") or recommendation

    module_names = ", ".join(k for k in modules.keys())

    evidence_text = "; ".join(risks[:6]) if risks else "available Watchman intelligence modules"

    answer = (
        f"{verdict}: {recommendation} "
        f"Watchman combined {len(modules)} module(s): {module_names}. "
        f"Combined score: {combined_score}/100. "
        f"Evidence: {evidence_text}. "
        f"What would change the answer: new alerts, radar changes, storm movement, forecast timing, "
        f"temperature changes, wind changes, lightning changes, or updated astronomy timing."
    )

    return {
        "mode": "Watchman Multi-Module Reasoning",
        "focus": focus,
        "verdict": verdict,
        "combinedScore": combined_score,
        "confidence": 90,
        "recommendation": recommendation,
        "modulesUsed": list(modules.keys()),
        "evidence": risks,
        "moduleResults": modules,
        "answer": answer,
        "whatWouldChangeTheAnswer": [
            "new NWS alert",
            "radar trend change",
            "storm tracker change",
            "hourly forecast timing change",
            "temperature or heat index change",
            "wind or lightning signal change",
            "astronomy timing update",
        ],
    }
