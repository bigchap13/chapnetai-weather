from .safety import safety_actions
from .activities import activity_decision
from .weather_terms import explain_weather_term


def explain_answer(question, weather):
    term = explain_weather_term(question)
    if term:
        return {
            "type": "weather_term",
            "answer": term,
            "confidence": 95,
            "why": ["Matched official weather term in the user question."],
        }

    activity = activity_decision(question, weather)
    if activity:
        return {
            "type": "activity_decision",
            "answer": f"{activity['verdict']}: {activity['recommendation']}",
            "confidence": activity["confidence"],
            "why": activity["reasons"],
        }

    actions = safety_actions(weather)
    return {
        "type": "general_safety",
        "answer": "Watchman safety guidance is available for the current scan.",
        "confidence": 82,
        "why": actions["watchFor"],
        "actions": actions,
    }
