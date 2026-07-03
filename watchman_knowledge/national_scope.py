def national_scope_answer(question):
    q = str(question or "").lower()

    limited_triggers = [
        "only jasper",
        "only for jasper",
        "just jasper",
        "jasper only",
        "walker county",
        "only walker county",
        "only for walker county",
        "jasper and walker county",
        "only alabama",
        "only for alabama",
        "just alabama",
        "alabama only",
    ]

    national_triggers = [
        "whole country",
        "entire country",
        "all states",
        "united states",
        "u.s.",
        "usa",
        "america",
        "anywhere in america",
        "nationwide",
        "national coverage",
        "where do you work",
        "what locations",
        "what cities",
        "can you check any city",
        "can you check other states",
        "other states",
        "do you work nationwide",
    ]

    if any(t in q for t in limited_triggers):
        return {
            "mode": "Watchman National Scope Intelligence",
            "answer": (
                "No. Watchman is not limited to Jasper, Walker County, or Alabama. "
                "Watchman AI was developed by Brandon Douglas Chappell for CHAPNETAI Weather "
                "as a nationwide United States weather intelligence system. Jasper is only a fallback "
                "location when no place is supplied."
            ),
            "confidence": 96,
            "coverage": "United States nationwide",
            "defaultLocationNote": "Jasper may be used as a fallback only when no place is provided.",
        }

    if any(t in q for t in national_triggers):
        return {
            "mode": "Watchman National Scope Intelligence",
            "answer": (
                "Watchman supports nationwide weather intelligence across the United States. "
                "Give Watchman a city, town, county, or state, and it can analyze that location using "
                "official weather data and Watchman intelligence modules."
            ),
            "confidence": 96,
            "coverage": "United States nationwide",
            "defaultLocationNote": "Jasper may be used as a fallback only when no place is provided.",
        }

    return None
