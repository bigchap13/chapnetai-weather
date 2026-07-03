def scenario_simulator(question, weather):
    from watchman_knowledge.timeline_intelligence import timeline_intelligence

    timeline = timeline_intelligence(question, weather)
    windows = timeline.get("windows") or []

    scenarios = []
    for row in windows:
        scenarios.append({
            "scenario": f"Do it {row['window']}",
            "score": row["score"],
            "verdict": row["verdict"],
            "reason": "; ".join(row["risks"]),
        })

    best = sorted(scenarios, key=lambda x: x["score"], reverse=True)[0] if scenarios else {}

    return {
        "mode": "Watchman Scenario Simulator",
        "scenarios": scenarios,
        "bestScenario": best,
        "confidence": 82,
        "answer": (
            f"Scenario Simulator: best option is '{best.get('scenario','unknown')}' "
            f"with score {best.get('score','unknown')}/100 and verdict {best.get('verdict','unknown')}. "
            f"Reason: {best.get('reason','available timing looks best')}."
        ),
    }
