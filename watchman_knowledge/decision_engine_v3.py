def _safe_score(value, default=50):
    try:
        return int(value)
    except Exception:
        return default


def decision_engine_v3(question, weather):
    from watchman_knowledge.timeline_intelligence import timeline_intelligence
    from watchman_knowledge.scenario_simulator import scenario_simulator
    from watchman_knowledge.reasoning_engine_v2 import reasoning_engine_v2

    weather = weather or {}
    watchman = weather.get("watchman") or {}

    timeline = timeline_intelligence(question, weather)
    scenarios = scenario_simulator(question, weather)
    reasoning = reasoning_engine_v2(question, weather)

    best_window = timeline.get("bestWindow") or {}
    best_scenario = scenarios.get("bestScenario") or {}

    base = _safe_score(reasoning.get("score"), 50)
    timeline_score = _safe_score(best_window.get("score"), base)
    scenario_score = _safe_score(best_scenario.get("score"), base)

    final_score = int((base * 0.45) + (timeline_score * 0.30) + (scenario_score * 0.25))

    if final_score >= 75:
        verdict = "YES"
        recommendation = "Do it, but keep Watchman open and recheck before starting."
    elif final_score >= 45:
        verdict = "CAUTION"
        recommendation = "It is possible, but timing matters. Use the best window and have a backup plan."
    else:
        verdict = "NO"
        recommendation = "Delay if possible until Watchman risk signals improve."

    answer = (
        f"Decision Engine V3: {verdict}. {recommendation} "
        f"Final score: {final_score}/100. "
        f"Best window: {best_window.get('window', 'unknown')} "
        f"({best_window.get('score', 'unknown')}/100). "
        f"Best scenario: {best_scenario.get('scenario', 'unknown')} "
        f"({best_scenario.get('score', 'unknown')}/100). "
        f"Main reasoning: {reasoning.get('recommendation', 'Watchman evaluated available evidence')}."
    )

    return {
        "mode": "Watchman Decision Engine V3",
        "verdict": verdict,
        "score": final_score,
        "confidence": 88,
        "recommendation": recommendation,
        "bestWindow": best_window,
        "bestScenario": best_scenario,
        "reasoning": reasoning,
        "answer": answer,
    }
