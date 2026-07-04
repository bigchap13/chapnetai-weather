from __future__ import annotations

import re
from typing import Any, Dict, List


QUESTION_GROUPS: Dict[str, Dict[str, Any]] = {
    "day_outlook": {
        "label": "Day Outlook",
        "examples": [
            "What's my day gonna be like?",
            "Is today gonna suck?",
            "Anything I need to worry about today?",
            "What's the worst part of today?",
            "When does today get better?",
            "Is today a wash?",
            "Am I gonna get rained on?",
            "Is it gonna be hot as hell?",
            "Should I take a jacket?",
        ],
        "answer": "Watchman should summarize the day in plain language: what happens first, worst window, best window, and what to do.",
    },
    "leave_now": {
        "label": "Leave Now / Wait",
        "examples": [
            "Should I leave now?",
            "Should I wait a little while?",
            "Will I beat the storm?",
            "Am I driving into bad weather?",
            "Is the drive gonna suck?",
            "Should I take a different route?",
            "What's the smartest time to leave?",
        ],
        "answer": "Watchman should compare leaving now versus waiting, using route ETA, hazards, and forecast timing.",
    },
    "work_outside": {
        "label": "Outdoor Work",
        "examples": [
            "Can I work outside today?",
            "Can I mow today?",
            "Is today a good roofing day?",
            "Can I pour concrete?",
            "Is it worth starting today?",
            "Is lightning gonna shut us down?",
            "Is it too windy?",
        ],
        "answer": "Watchman should decide if work is reasonable, risky, or not worth starting.",
    },
    "family_day": {
        "label": "Family / Pets",
        "examples": [
            "Can the kids play outside?",
            "Can I take the dog out?",
            "Is today good for the park?",
            "Can we go to the lake?",
            "Is it a good pool day?",
            "Is it safe to grill?",
        ],
        "answer": "Watchman should give practical family-safe guidance, including heat, storms, lightning, and timing.",
    },
    "trip_check": {
        "label": "Trip Check",
        "examples": [
            "Is this trip gonna be okay?",
            "What's the worst spot on my drive?",
            "Am I gonna hit storms?",
            "Will I have to slow down?",
            "Should I stop somewhere?",
            "Should I stay another night?",
        ],
        "answer": "Watchman should explain the trip in normal-driver language: clear, use caution, wait, reroute, or stop.",
    },
    "watchman_self": {
        "label": "Watchman Self Check",
        "examples": [
            "What are you watching?",
            "What worries you?",
            "What changed?",
            "Tell me something I should know.",
            "What am I missing?",
            "If you were me, what would you do?",
            "Would you change your plans?",
            "How sure are you?",
            "Explain why.",
            "Convince me.",
        ],
        "answer": "Watchman should explain what it is watching, why it matters, and what it would do next.",
    },
    "tonight": {
        "label": "Tonight",
        "examples": [
            "Is tonight gonna be rough?",
            "Will storms wake me up?",
            "Am I gonna lose power?",
            "Should I charge my phone?",
            "Should I move my car?",
            "Do I need to bring anything inside?",
        ],
        "answer": "Watchman should focus on overnight hazards, power risk, wind, hail, flooding, and preparation.",
    },
    "tomorrow": {
        "label": "Tomorrow",
        "examples": [
            "Is tomorrow better?",
            "Should I wait until tomorrow?",
            "Is tomorrow gonna be worse?",
            "When's the next good weather?",
            "What's tomorrow look like?",
        ],
        "answer": "Watchman should compare tomorrow against today and recommend whether waiting helps.",
    },
}


def _score_text(question: str, examples: List[str]) -> int:
    q = question.lower().strip()
    score = 0

    for ex in examples:
        e = ex.lower().replace("?", "").strip()
        if e in q:
            score += 10

        for token in re.findall(r"[a-z0-9']+", e):
            if len(token) >= 4 and token in q:
                score += 1

    slang_boosts = {
        "suck": 2,
        "rough": 2,
        "worried": 2,
        "worry": 2,
        "bad": 1,
        "storm": 2,
        "rained": 2,
        "leave": 2,
        "wait": 2,
        "drive": 2,
        "kids": 2,
        "dog": 2,
        "work": 2,
        "mow": 3,
        "tonight": 3,
        "tomorrow": 3,
    }

    for word, boost in slang_boosts.items():
        if word in q:
            score += boost

    return score


def classify_real_life_question(question: str) -> Dict[str, Any]:
    q = (question or "").strip()
    if not q:
        return {"ok": False, "error": "question_required"}

    ranked = []
    for key, data in QUESTION_GROUPS.items():
        score = _score_text(q, data.get("examples", []))
        if score:
            ranked.append({"group": key, "score": score, **data})

    ranked.sort(key=lambda x: x["score"], reverse=True)

    if not ranked:
        return {
            "ok": True,
            "handled": False,
            "group": "unknown",
            "label": "Unknown",
            "answer": "I can answer it, but I need to hand this to the general Watchman companion layer.",
            "confidence": 25,
        }

    best = ranked[0]
    return {
        "ok": True,
        "handled": True,
        "group": best["group"],
        "label": best["label"],
        "answer": best["answer"],
        "confidence": min(100, best["score"] * 10),
        "examples": best.get("examples", []),
        "ranked": ranked[:3],
    }


def answer_real_life_question(question: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
    context = context or {}
    classified = classify_real_life_question(question)

    if not classified.get("handled"):
        return {
            "ok": True,
            "mode": "Watchman Real-Life Question Intelligence",
            "handled": False,
            "classification": classified,
            "answer": classified["answer"],
        }

    group = classified["group"]
    answer = classified["answer"]

    if group == "day_outlook":
        plain = "I should tell you what your day is actually going to feel like, not just list forecast numbers."
    elif group == "leave_now":
        plain = "I should compare leaving now against waiting and tell you which choice makes more sense."
    elif group == "work_outside":
        plain = "I should tell you if the job is worth starting, likely to get interrupted, or unsafe."
    elif group == "family_day":
        plain = "I should give a family-safe answer with timing, heat, lightning, and comfort in mind."
    elif group == "trip_check":
        plain = "I should tell you the worst stretch, whether the drive is still reasonable, and what I would do."
    elif group == "watchman_self":
        plain = "I should explain what I am watching, why it matters, and what I would do next."
    elif group == "tonight":
        plain = "I should tell you whether to prepare for storms, power issues, wind, hail, flooding, or sleep interruption."
    elif group == "tomorrow":
        plain = "I should tell you whether tomorrow is actually better or worse than today."
    else:
        plain = "I should answer like a practical travel companion."

    return {
        "ok": True,
        "mode": "Watchman Real-Life Question Intelligence",
        "handled": True,
        "classification": classified,
        "answer": answer + " " + plain,
    }


def real_life_questions_summary() -> Dict[str, Any]:
    total_examples = sum(len(v.get("examples", [])) for v in QUESTION_GROUPS.values())
    return {
        "ok": True,
        "mode": "Watchman Real-Life Question Intelligence V1",
        "groupCount": len(QUESTION_GROUPS),
        "exampleCount": total_examples,
        "groups": QUESTION_GROUPS,
    }
