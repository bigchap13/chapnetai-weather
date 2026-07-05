WEATHER_TERMS = {
    "tornado watch": "A tornado watch means conditions are favorable for tornadoes. Stay weather aware and be ready to shelter.",
    "tornado warning": "A tornado warning means a tornado has been indicated by radar or spotted. Take shelter immediately.",
    "severe thunderstorm warning": "A severe thunderstorm warning means damaging wind or large hail is expected. Move indoors and away from windows.",
    "flash flood warning": "A flash flood warning means flooding is happening or about to happen. Do not drive through water-covered roads.",
    "heat advisory": "A heat advisory means heat illness is possible. Limit outdoor work, hydrate, and use shade or air conditioning.",
    "wind advisory": "A wind advisory means strong winds could make driving difficult and blow unsecured objects around.",
    "frost advisory": "A frost advisory means cold temperatures may damage sensitive plants.",
    "red flag warning": "A red flag warning means fire danger is high because of dry air, wind, and dry fuels.",
    "winter storm warning": "A winter storm warning means dangerous winter weather is expected or occurring.",
    "dense fog advisory": "A dense fog advisory means visibility may be dangerously low.",
}


def explain_weather_term(question):
    q = str(question or "").lower()
    for term, explanation in WEATHER_TERMS.items():
        if term in q:
            return explanation
    return None
