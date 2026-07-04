def _safe_score(value, default=50):
    try:
        return int(value)
    except Exception:
        return default


def _worst_verdict(*items):
    order = {
        "NO": 0,
        "DELAY": 0,
        "AVOID": 0,
        "CAUTION": 1,
        "MONITOR": 1,
        "OK": 2,
        "GOOD": 2,
        "YES": 2,
        "GO": 2,
    }

    worst = "YES"
    worst_rank = 2

    for item in items:
        if not isinstance(item, dict):
            continue
        verdict = str(item.get("verdict") or "").upper()
        if verdict in order and order[verdict] < worst_rank:
            worst = "NO" if order[verdict] == 0 else "CAUTION"
            worst_rank = order[verdict]

    return worst


def decision_engine_v3(question, weather):
    from watchman_weather.timeline_intelligence import timeline_intelligence
    from watchman_knowledge.scenario_simulator import scenario_simulator
    from watchman_knowledge.reasoning_engine_v2 import reasoning_engine_v2

    weather = weather or {}

    timeline = timeline_intelligence(question, weather)
    scenarios = scenario_simulator(question, weather)
    reasoning = reasoning_engine_v2(question, weather)

    best_window = timeline.get("bestWindow") or {}
    best_scenario = scenarios.get("bestScenario") or {}

    reasoning_score = _safe_score(reasoning.get("score"), 50)
    timeline_score = _safe_score(best_window.get("score"), reasoning_score)
    scenario_score = _safe_score(best_scenario.get("score"), reasoning_score)

    final_score = int((reasoning_score * 0.50) + (timeline_score * 0.25) + (scenario_score * 0.25))

    forced = _worst_verdict(reasoning, best_window, best_scenario)

    if forced == "NO" or reasoning_score < 45:
        verdict = "NO"
        recommendation = "Delay if possible until Watchman risk signals improve."
    elif final_score >= 75 and forced != "CAUTION":
        verdict = "YES"
        recommendation = "Do it, but keep Watchman open and recheck before starting."
    elif final_score >= 45:
        verdict = "CAUTION"
        recommendation = "It is possible, but timing matters. Use the best window and have a backup plan."
    else:
        verdict = "NO"
        recommendation = "Delay if possible until Watchman risk signals improve."

    reason_text = reasoning.get("recommendation") or "Watchman evaluated available evidence"

    answer = (
        f"Decision Engine V3: {verdict}. {recommendation} "
        f"Final score: {final_score}/100. "
        f"Reasoning score: {reasoning_score}/100. "
        f"Best window: {best_window.get('window', 'unknown')} "
        f"({best_window.get('score', 'unknown')}/100). "
        f"Best scenario: {best_scenario.get('scenario', 'unknown')} "
        f"({best_scenario.get('score', 'unknown')}/100). "
        f"Main reasoning: {reason_text}."
    )

    return {
        "mode": "Watchman Decision Engine V3",
        "verdict": verdict,
        "score": final_score,
        "reasoningScore": reasoning_score,
        "timelineScore": timeline_score,
        "scenarioScore": scenario_score,
        "confidence": 88,
        "recommendation": recommendation,
        "bestWindow": best_window,
        "bestScenario": best_scenario,
        "reasoning": reasoning,
        "answer": answer,
    }
