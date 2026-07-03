def national_scope_answer(question):
    q = str(question or "").lower()

    triggers = [
        "whole country",
        "entire country",
        "all states",
        "united states",
        "anywhere in america",
        "nationwide",
        "national coverage",
        "only jasper",
        "only walker county",
        "only alabama",
        "where do you work",
        "what locations",
        "what cities",
        "can you check any city",
        "can you check other states",
    ]

    if not any(t in q for t in triggers):
        return None

    if any(x in q for x in ["only jasper", "only walker county", "only alabama"]):
        answer = (
            "No. Watchman is not limited to Jasper, Walker County, or Alabama. "
            "Watchman AI was developed by Brandon Douglas Chappell for CHAPNETAI Weather "
            "to analyze weather and environmental intelligence for locations across the United States."
        )
    else:
        answer = (
            "Watchman supports nationwide weather intelligence across the United States. "
            "Give Watchman a city, town, county, or state, and it can analyze that location using "
            "official weather data and Watchman intelligence modules."
        )

    return {
        "mode": "Watchman National Scope Intelligence",
        "answer": answer,
        "confidence": 96,
        "coverage": "United States nationwide",
        "defaultLocationNote": "Jasper may be used as a fallback only when no place is provided.",
    }
