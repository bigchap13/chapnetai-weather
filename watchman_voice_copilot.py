from watchman_knowledge.moon_phase import moon_phase_intelligence
from watchman_knowledge.astronomy_pro import astronomy_pro_intelligence
from watchman_knowledge.astronomy_fire import astronomy_intelligence, fire_weather_intelligence
from watchman_knowledge.sun_uv import sunrise_sunset_intelligence, uv_intelligence
from watchman_knowledge.explain_reasoning import explain_reasoning_intelligence
from watchman_knowledge.change_detection_pro import change_detection_pro
from watchman_knowledge.national_alerts import answer_national_alert_question, is_national_alert_question
from watchman_knowledge.winter_road import winter_road_intelligence
from watchman_knowledge.long_range_planning import long_range_planning_intelligence
from watchman_knowledge.air_quality_smoke import air_quality_smoke_intelligence
from watchman_knowledge.allergy_pollen import allergy_pollen_intelligence
from watchman_knowledge.pet_livestock import pet_livestock_intelligence
from watchman_knowledge.marine_lake import marine_lake_intelligence
from watchman_knowledge.outdoor_work import outdoor_work_intelligence
from watchman_knowledge.event_intelligence import event_intelligence
from watchman_knowledge.lightning_intelligence import lightning_intelligence
from watchman_knowledge.travel_intelligence import travel_intelligence
from watchman_knowledge.reasoning_engine import build_reasoning_answer
from watchman_knowledge.decision_center import decision_center
from watchman_knowledge.intelligence import intelligence_summary
from watchman_knowledge.explain import explain_answer
TOP_100_QUESTIONS = {
    "current_conditions": [
        "What's the weather right now?",
        "Is it raining?",
        "Is it snowing?",
        "How hot is it?",
        "How cold is it?",
        "What's the humidity?",
        "How windy is it?",
        "What's the UV index?",
        "What's the air quality?",
        "What does it feel like?",
    ],
    "rain_storms": [
        "Will it rain today?",
        "When will the rain start?",
        "When will it stop?",
        "Is a thunderstorm coming?",
        "Is lightning nearby?",
        "How far away is the storm?",
        "Is the storm getting stronger?",
        "Which direction is the storm moving?",
        "Will my house get hit?",
        "Should I delay leaving?",
    ],
    "severe_weather": [
        "Is there a tornado warning?",
        "Is there a tornado watch?",
        "Is hail expected?",
        "How big could the hail get?",
        "Are damaging winds expected?",
        "Is flooding possible?",
        "Could flash flooding happen?",
        "Is this storm dangerous?",
        "What should I do?",
        "Should I shelter now?",
    ],
    "travel": [
        "Is it safe to drive?",
        "How are road conditions?",
        "Will I drive through rain?",
        "Will I drive through storms?",
        "Will fog affect my trip?",
        "Will ice form tonight?",
        "Is visibility poor?",
        "Is travel dangerous?",
        "What's the safest departure time?",
        "Should I postpone my trip?",
    ],
    "outdoor": [
        "Can I mow today?",
        "Can I grill today?",
        "Is today good for hiking?",
        "Can I fish today?",
        "Is it good for boating?",
        "Can I go swimming?",
        "Is today good for golfing?",
        "Can I wash my car?",
        "Is it safe for fireworks?",
        "Is today good for camping?",
    ],
    "family": [
        "Is it safe for kids outside?",
        "Is it too hot for children?",
        "Is it too cold?",
        "Is there lightning nearby?",
        "Should pets stay inside?",
        "Is it safe to walk my dog?",
        "Is pollen high?",
        "Will allergies be bad?",
        "Is the air unhealthy?",
        "Should elderly people avoid being outside?",
    ],
    "work": [
        "Can construction continue?",
        "Is it safe to roof today?",
        "Is today good for concrete work?",
        "Is it safe to use cranes?",
        "Are winds too high?",
        "Is heat dangerous for workers?",
        "How long before rain reaches the job site?",
        "Can farmers work today?",
        "Is spraying recommended?",
        "Will machinery get stuck?",
    ],
    "water": [
        "River levels?",
        "Is flooding increasing?",
        "Lake conditions?",
        "Is boating safe?",
        "Wave heights?",
        "Water temperature?",
        "Rip current risk?",
        "Is fishing good?",
        "Safe kayaking?",
        "Any dam releases?",
    ],
    "forecast": [
        "What's tomorrow like?",
        "Weekend forecast?",
        "Seven-day forecast?",
        "Hottest day this week?",
        "Coldest night?",
        "Best day to be outside?",
        "Worst weather this week?",
        "When is the next storm?",
        "Will weather improve tomorrow?",
        "Will this system last all week?",
    ],
    "watchman_ai": [
        "Give me your briefing.",
        "What's changed since my last scan?",
        "What's your biggest concern?",
        "What should I prepare for?",
        "What's the worst-case scenario?",
        "Rate today's weather from 1 to 10.",
        "Give me a 30-second summary.",
        "Give me a detailed weather report.",
        "Explain the weather like I'm five.",
        "What would you do if you were me?",
    ],
}

WATCHMAN_EXCLUSIVE_COMMANDS = [
    "Watch my house.",
    "Watch my route to work.",
    "Wake me if storms become dangerous.",
    "Tell me when it's safe to leave.",
    "Explain why you're worried.",
    "Show me what changed in the last hour.",
    "Summarize overnight weather.",
    "What are you watching right now?",
    "What's the next thing likely to happen?",
    "Give me your confidence level.",
    "Would you cancel today's plans?",
    "How unusual is today's weather compared to normal?",
    "What's the biggest weather risk in the next 6 hours?",
    "Tell me something I haven't asked but should know.",
]


def _norm(text):
    return " ".join(str(text or "").lower().replace("?", "").replace(".", "").split())


def _contains_any(text, words):
    return any(w in text for w in words)


def _with_reasoning(question, weather, answer):
    reasoned = build_reasoning_answer(question, weather, answer)
    return reasoned["plainAnswer"]


def answer_watchman_question(question, weather):
    q = _norm(question)

    if is_national_alert_question(question):
        result = answer_national_alert_question(question)
        return result["answer"]
    weather = weather or {}

    location = weather.get("location", {})
    place = location.get("name") or "this location"
    obs = weather.get("observation") or {}
    forecast = weather.get("forecast") or []
    hourly = weather.get("hourly") or []
    alerts = weather.get("alerts") or []
    watchman = weather.get("watchman") or {}

    first = forecast[0] if forecast else {}
    first_hour = hourly[0] if hourly else {}

    temp = obs.get("temperatureF") or first.get("temperature")
    condition = obs.get("text") or first.get("shortForecast") or "conditions are updating"
    threat = watchman.get("threatLevel", "unknown")
    score = watchman.get("threatScore", "unknown")
    briefing = watchman.get("aiBriefing") or watchman.get("briefing") or "Watchman briefing unavailable."
    narrative = watchman.get("aiWeatherNarrative") or briefing
    storm = watchman.get("stormTracker") or {}
    changed = watchman.get("whatChanged") or {}
    arrival = watchman.get("streetLevelArrival") or {}
    scanner = watchman.get("liveScanner") or {}
    decision = decision_center(question, weather)
    knowledge = explain_answer(question, weather)
    intel_v2 = intelligence_summary(weather)
    travel_ai = travel_intelligence(question, weather)
    lightning_ai = lightning_intelligence(question, weather)
    outdoor_ai = outdoor_work_intelligence(weather)
    event_ai = event_intelligence(weather)
    pet_ai = pet_livestock_intelligence(weather)
    marine_ai = marine_lake_intelligence(weather)
    air_ai = air_quality_smoke_intelligence(weather)
    allergy_ai = allergy_pollen_intelligence(weather)
    winter_ai = winter_road_intelligence(weather)
    long_range_ai = long_range_planning_intelligence(weather)
    reasoning_ai = explain_reasoning_intelligence(question, weather)
    change_ai = change_detection_pro(weather)
    sun_ai = sunrise_sunset_intelligence(weather)
    uv_ai = uv_intelligence(weather)
    astronomy_ai = astronomy_intelligence(weather)
    fire_ai = fire_weather_intelligence(weather)
    astronomy_pro_ai = astronomy_pro_intelligence(question, weather)
    moon_phase_ai = moon_phase_intelligence(question, weather)

    if _contains_any(q, ["drive", "travel", "road", "leave", "trip", "visibility", "commute"]):
        return _with_reasoning(
            question,
            weather,
            f"{travel_ai['verdict']}: {travel_ai['recommendation']} Travel score: {travel_ai['score']}/100. Hazards: {'; '.join(travel_ai['hazards'])}. Confidence: {travel_ai['confidence']}%."
        )

    if _contains_any(q, ["roof","concrete","paint","construction","landscape","pressure wash","tree","mow"]):
        job_aliases = {
            "paint": "painting",
            "painting": "painting",
            "mow": "mowing",
            "yard": "mowing",
            "landscape": "landscaping",
            "pressure wash": "pressure washing",
            "roof": "roofing",
            "tree": "tree work",
            "concrete": "concrete",
            "construction": "construction",
        }
        job = next((v for k, v in job_aliases.items() if k in q), "construction")
        j = outdoor_ai["jobs"][job]
        return _with_reasoning(
            question,
            weather,
            f"Outdoor work intelligence for {job}: {j['verdict']} ({j['score']}/100)."
        )

    if _contains_any(q, ["wedding","festival","concert","cookout","party","fireworks","graduation","church","school","ball game"]):
        event = next((k for k in event_ai["events"] if k in q), "event")
        e = event_ai["events"].get(event, {"verdict":"CAUTION","score":50})
        return _with_reasoning(
            question,
            weather,
            f"Event intelligence for {event}: {e['verdict']} ({e['score']}/100)."
        )

    if _contains_any(q, ["dog", "pet", "pets", "cat", "livestock", "cattle", "horse", "animals", "walk my dog"]):
        return _with_reasoning(
            question,
            weather,
            f"Pet and livestock intelligence: {pet_ai['verdict']} ({pet_ai['score']}/100). {pet_ai['recommendation']} Risks: {'; '.join(pet_ai['risks'])}. {pet_ai['vehicleWarning']}"
        )

    if _contains_any(q, ["boat", "boating", "lake", "kayak", "canoe", "swim", "swimming", "fishing", "fish", "water"]):
        return _with_reasoning(
            question,
            weather,
            f"Marine and lake intelligence: {marine_ai['verdict']} ({marine_ai['score']}/100). {marine_ai['recommendation']} Risks: {'; '.join(marine_ai['risks'])}. {marine_ai['lightningRule']}"
        )

    if _contains_any(q, ["air quality", "smoke", "haze", "wildfire", "dust", "asthma", "breathing"]):
        return _with_reasoning(
            question,
            weather,
            f"Air quality intelligence: {air_ai['verdict']} ({air_ai['score']}/100). {air_ai['recommendation']} Risks: {'; '.join(air_ai['risks'])}."
        )

    if _contains_any(q, ["allergy", "allergies", "pollen", "sinus", "sneezing"]):
        return _with_reasoning(
            question,
            weather,
            f"Allergy and pollen intelligence: {allergy_ai['verdict']} ({allergy_ai['score']}/100). {allergy_ai['recommendation']} Risks: {'; '.join(allergy_ai['risks'])}."
        )

    if _contains_any(q, ["snow", "ice", "sleet", "freezing rain", "black ice", "winter road", "roads freeze", "bridge freeze"]):
        return _with_reasoning(
            question,
            weather,
            f"Winter road intelligence: {winter_ai['verdict']} ({winter_ai['score']}/100). {winter_ai['recommendation']} Risks: {'; '.join(winter_ai['risks'])}. {winter_ai['bridgeRule']}"
        )

    if _contains_any(q, ["best day", "best time", "this week", "weekend", "long range", "plan ahead", "best window", "worst day"]):
        best = long_range_ai["bestWindows"][0] if long_range_ai["bestWindows"] else {}
        return _with_reasoning(
            question,
            weather,
            f"Long-range planning intelligence: best current window is {best.get('name','unknown')} with score {best.get('score','unknown')}/100 and forecast {best.get('forecast','updating')}. {long_range_ai['recommendation']}"
        )

    if _contains_any(q, ["what changed", "changed since", "getting worse", "getting better", "improving", "worsening", "changed in the last hour"]):
        return _with_reasoning(
            question,
            weather,
            f"Watchman Change Detection Pro: trend is {change_ai['trend']}. {change_ai['summary']} Recommendation: {change_ai['recommendation']} Changes: {'; '.join(change_ai['changes'][:3])}."
        )

    if _contains_any(q, ["why", "explain", "reasoning", "evidence", "how do you know", "show your evidence", "why did you"]):
        return _with_reasoning(
            question,
            weather,
            f"{reasoning_ai['answer']} Confidence: {reasoning_ai['confidence']}%. Evidence: {'; '.join(reasoning_ai['evidence'][:5])}."
        )

    if _contains_any(q, ["sunrise", "sunset", "daylight", "dark", "darkness", "golden hour", "blue hour"]):
        sr = sun_ai["sunriseWindow"][0] if sun_ai["sunriseWindow"] else {}
        ss = sun_ai["sunsetWindow"][0] if sun_ai["sunsetWindow"] else {}
        return _with_reasoning(
            question,
            weather,
            f"Sunrise sunset intelligence: sunrise window starts near {sr.get('time','unknown')}; sunset window starts near {ss.get('time','unknown')}. {sun_ai['recommendation']}"
        )

    if _contains_any(q, ["uv", "sunburn", "sunscreen", "sun screen", "sun exposure", "too much sun"]):
        return _with_reasoning(
            question,
            weather,
            f"UV intelligence: {uv_ai['verdict']} ({uv_ai['score']}/100). {uv_ai['recommendation']} Risks: {'; '.join(uv_ai['risks'])}."
        )

    if _contains_any(q, ["meteor", "meteor shower", "perseids", "geminids", "quadrantids", "lyrids", "orionids", "leonids", "ursids", "eta aquariids", "delta aquariids", "shooting star", "shooting stars"]):
        return _with_reasoning(
            question,
            weather,
            f"Watchman Astronomy Pro: {astronomy_pro_ai['answer']} {astronomy_pro_ai['viewingAssessment']} Sky score: {astronomy_pro_ai['skyScore']}/100. Risks: {'; '.join(astronomy_pro_ai['skyRisks'])}."
        )

    if _contains_any(q, [
        "full moon",
        "new moon",
        "moon phase",
        "moonlight",
        "moon illumination",
        "supermoon",
        "blue moon",
        "lunar eclipse",
        "solar eclipse",
        "planet",
        "saturn",
        "jupiter",
        "venus",
        "mars",
        "mercury",
        "iss",
        "space station",
        "aurora",
        "northern lights",
        "constellation",
        "milky way",
        "astrophotography"
    ]):
        return _with_reasoning(
            question,
            weather,
            moon_phase_ai["answer"]
        )

    if _contains_any(q, ["astronomy", "stars", "stargazing", "star gazing", "sky viewing"]):
        return _with_reasoning(
            question,
            weather,
            f"Astronomy intelligence: {astronomy_ai['verdict']} ({astronomy_ai['score']}/100). {astronomy_ai['recommendation']} Risks: {'; '.join(astronomy_ai['risks'])}."
        )

    if _contains_any(q, ["fire weather", "burn", "burning", "wildfire", "red flag", "campfire", "debris fire", "brush fire", "grill fire"]):
        return _with_reasoning(
            question,
            weather,
            f"Fire weather intelligence: {fire_ai['verdict']} ({fire_ai['score']}/100). {fire_ai['recommendation']} Risks: {'; '.join(fire_ai['risks'])}. {fire_ai['burnRule']}"
        )

    if decision:
        why = "; ".join(decision["reasoning"])
        do_now = "; ".join(decision["doNow"])
        avoid = "; ".join(decision["avoid"])
        change = "; ".join(decision["whatWouldChangeTheAnswer"])
        return (
            f"{decision['verdict']}: {decision['recommendation']} "
            f"Confidence: {decision['confidence']}%. "
            f"Why: {why}. Do now: {do_now}. Avoid: {avoid}. "
            f"Safe window: {decision['safeWindow']} "
            f"What would change the answer: {change}."
        )

    if knowledge.get("type") == "weather_term":
        return knowledge["answer"]

    if knowledge.get("type") == "activity_decision" and _contains_any(q, ["should", "can i", "safe", "mow", "grill", "hike", "fish", "boat", "swim", "golf", "wash", "camp", "drive", "roof", "concrete", "crane", "walk dog", "kids", "pets"]):
        why = "; ".join(knowledge.get("why", []))
        return f"{knowledge['answer']} Confidence: {knowledge.get('confidence')}%. Why: {why}."

    if _contains_any(q, ["right now", "weather now", "currently", "feel like", "temperature", "hot", "cold"]):
        return f"Right now in {place}, it is {temp if temp is not None else '--'} degrees with {condition}. Watchman threat level is {threat} at {score}/100."

    if _contains_any(q, ["rain", "start", "stop", "umbrella", "precip"]):
        pop = ((first.get("probabilityOfPrecipitation") or {}).get("value"))
        rain_eta = arrival.get("rainEta") or "No precise rain arrival signal is available."
        return _with_reasoning(question, weather, f"For {place}, precipitation chance is {pop if pop is not None else 'unknown'}%. {rain_eta}")

    if _contains_any(q, ["lightning", "thunder", "safe to go outside", "return outside"]):
        return _with_reasoning(
            question,
            weather,
            f"Lightning intelligence: {lightning_ai['risk']} risk. {lightning_ai['action']} Confidence: {lightning_ai['confidence']}%. Rule: {lightning_ai['safetyRule']}"
        )

    if _contains_any(q, ["storm", "thunderstorm", "hail", "wind", "stronger", "direction"]):
        return f"Storm tracker for {place}: nearest storm is {storm.get('nearestStorm', 'unknown')}. Intensity is {storm.get('intensity', 'unknown')}. Arrival: {storm.get('estimatedArrival', 'unknown')}. Confidence: {storm.get('confidence', 'unknown')}%."

    if _contains_any(q, ["tornado", "shelter", "rotation", "supercell"]):
        t = intel_v2["tornadoIntelligence"]
        return _with_reasoning(question, weather, f"Tornado intelligence: {t['status']}. Action: {t['action']} Confidence: {t['confidence']}%. Shelter rule: {t['shelterRule']}")

    if _contains_any(q, ["heat index", "heat stress", "too hot", "heat illness", "hydration"]):
        h = intel_v2["heatIndexIntelligence"]
        return _with_reasoning(question, weather, f"Heat intelligence: risk is {h['risk']}. Temperature: {h['temperatureF']}°F. {h['action']} {h['vehicleWarning']} {h['petWarning']} Confidence: {h['confidence']}%.")

    if _contains_any(q, ["biggest risk", "top hazard", "hazard board", "rank risks", "threat ranking"]):
        board = intel_v2["hazardBoard"]
        top = board["topHazard"]
        ranked = "; ".join(f"{h['name']} {h['score']}% {h['level']}" for h in board["hazards"][:4])
        return _with_reasoning(question, weather, f"Top Watchman hazard: {top['name']} at {top['score']}% ({top['level']}). Ranking: {ranked}.")

    if _contains_any(q, ["timeline", "next likely", "what happens next", "next change"]):
        timeline = intel_v2["predictiveTimeline"]
        return "Watchman predictive timeline: " + " | ".join(f"{x['time']}: {x['event']} ({x['risk']})" for x in timeline)

    if _contains_any(q, ["tornado", "warning", "watch", "shelter", "dangerous", "severe"]):
        if alerts:
            events = ", ".join(a.get("event", "Alert") for a in alerts[:3])
            return f"Active NWS alert context for {place}: {events}. Watchman threat level is {threat}. Follow official NWS instructions immediately if a warning is active."
        return f"No active NWS warning product is showing for {place} in the current scan. Watchman threat level is {threat}."

    if _contains_any(q, ["drive", "travel", "road", "leave", "trip", "visibility", "commute"]):
        return _with_reasoning(
            question,
            weather,
            f"{travel_ai['verdict']}: {travel_ai['recommendation']} Travel score: {travel_ai['score']}/100. Hazards: {'; '.join(travel_ai['hazards'])}. Confidence: {travel_ai['confidence']}%."
        )

    if _contains_any(q, ["lightning", "thunder", "thunderstorm nearby", "safe to go outside", "return outside"]):
        return _with_reasoning(
            question,
            weather,
            f"Lightning intelligence: {lightning_ai['risk']} risk. {lightning_ai['action']} Confidence: {lightning_ai['confidence']}%. Rule: {lightning_ai['safetyRule']}"
        )

    if _contains_any(q, ["drive", "travel", "road", "leave", "trip", "visibility"]):
        return f"Travel index for {place} is {watchman.get('travelIndex', 'unknown')}/100. {storm.get('estimatedArrival', 'No storm arrival signal detected.')}"

    if _contains_any(q, ["mow", "grill", "hike", "fish", "boat", "swim", "golf", "wash", "camp", "outside"]):
        outdoor = watchman.get("outdoorIndex", 0)
        if outdoor >= 70:
            verdict = "conditions look usable, but keep Watchman open."
        elif outdoor >= 40:
            verdict = "use caution and watch the radar before starting."
        else:
            verdict = "delay outdoor activity if possible."
        return f"Outdoor index is {outdoor}/100. Watchman recommendation: {verdict}"

    if _contains_any(q, ["kids", "children", "pets", "dog", "elderly", "heat", "air quality", "allergies"]):
        return f"Safety readout for {place}: {briefing} If heat or storms are active, limit outdoor exposure for kids, pets, and elderly people."

    if _contains_any(q, ["construction", "roof", "concrete", "crane", "workers", "job site", "farm", "spray"]):
        return f"Job-site guidance for {place}: outdoor index {watchman.get('outdoorIndex', 'unknown')}/100, travel index {watchman.get('travelIndex', 'unknown')}/100. {storm.get('estimatedArrival', '')}"

    if _contains_any(q, ["river", "flood", "lake", "kayak", "dam", "boating", "water"]):
        flood = storm.get("floodSignal") or (watchman.get("liveStormIntelligence") or {}).get("floodSignal")
        return f"Water risk scan for {place}: flood signal is {flood or 'not detected'}. Check official river and lake gauges before water activity."

    if _contains_any(q, ["tomorrow", "weekend", "seven", "forecast", "hottest", "coldest", "best day", "worst"]):
        summary = []
        for item in forecast[:4]:
            summary.append(f"{item.get('name')}: {item.get('shortForecast')} {item.get('temperature')}°{item.get('temperatureUnit')}")
        return "Forecast summary: " + " | ".join(summary)

    if _contains_any(q, ["changed", "last scan", "what changed"]):
        changes = changed.get("changes") or []
        return changed.get("summary", "Change detection unavailable.") + " " + " ".join(changes[:3])

    if _contains_any(q, ["briefing", "summary", "detailed", "explain", "what would you do", "biggest concern", "prepare", "confidence"]):
        return narrative

    if _contains_any(q, ["watch my house", "watching", "next thing", "haven't asked"]):
        steps = scanner.get("steps") or []
        if steps:
            return "Watchman is currently scanning: " + "; ".join(f"{s.get('label')}: {s.get('status')}" for s in steps)
        return "Watchman is watching radar, alerts, storm signals, observations, and forecast changes."

    return f"Watchman heard: '{question}'. Best current answer: {narrative}"


def top_questions_flat():
    rows = []
    for category, questions in TOP_100_QUESTIONS.items():
        for q in questions:
            rows.append({"category": category, "question": q})
    for q in WATCHMAN_EXCLUSIVE_COMMANDS:
        rows.append({"category": "watchman_exclusive", "question": q})
    return rows


def extract_place_from_question(question, default_place=None):
    text = str(question or "").strip()
    default_place = default_place or "Jasper, Alabama"
    lowered = text.lower()

    # Do not treat activity/time-only questions as locations.
    if not any(token in lowered for token in [" in ", " near ", " around ", " for "]):
        return default_place

    bad_place_phrases = [
        "tonight",
        "today",
        "tomorrow",
        "this morning",
        "this afternoon",
        "this evening",
        "right now",
        "now",
        "later",
        "this week",
        "weekend",
        "stargazing",
        "star gazing",
        "astronomy",
        "sunset",
        "sunrise",
        "sunscreen",
        "burn brush",
        "burning",
        "fire weather",
        "the weather",
        "outside",
    ]

    for token in [" in ", " near ", " around ", " for "]:
        if token not in lowered:
            continue

        after = text[lowered.rfind(token) + len(token):].strip()
        candidate = after

        for stop in [
            " today",
            " tonight",
            " tomorrow",
            " this morning",
            " this afternoon",
            " this evening",
            " right now",
            " now",
            " later",
            " this week",
            " weekend",
            "?",
            ".",
            ", please",
        ]:
            idx = candidate.lower().find(stop)
            if idx >= 0:
                candidate = candidate[:idx].strip()

        candidate = candidate.strip(" ?.,!")

        if not candidate:
            return default_place

        if len(candidate.split()) > 4:
            return default_place

        if candidate.lower() in bad_place_phrases:
            return default_place

        if any(bad in candidate.lower() for bad in bad_place_phrases):
            return default_place

        if "," not in candidate and len(candidate.split()) <= 3:
            return candidate.title()

        return candidate

    return default_place

