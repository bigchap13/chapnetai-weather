from __future__ import annotations

from typing import Any, Dict, List


US_STATES: Dict[str, Dict[str, Any]] = {
    "AL": {"name": "Alabama", "capital": "Montgomery", "region": "Southeast"},
    "AK": {"name": "Alaska", "capital": "Juneau", "region": "Pacific/Northwest"},
    "AZ": {"name": "Arizona", "capital": "Phoenix", "region": "Southwest"},
    "AR": {"name": "Arkansas", "capital": "Little Rock", "region": "South"},
    "CA": {"name": "California", "capital": "Sacramento", "region": "West Coast"},
    "CO": {"name": "Colorado", "capital": "Denver", "region": "Mountain West"},
    "CT": {"name": "Connecticut", "capital": "Hartford", "region": "Northeast"},
    "DE": {"name": "Delaware", "capital": "Dover", "region": "Mid-Atlantic"},
    "FL": {"name": "Florida", "capital": "Tallahassee", "region": "Southeast"},
    "GA": {"name": "Georgia", "capital": "Atlanta", "region": "Southeast"},
    "HI": {"name": "Hawaii", "capital": "Honolulu", "region": "Pacific"},
    "ID": {"name": "Idaho", "capital": "Boise", "region": "Mountain West"},
    "IL": {"name": "Illinois", "capital": "Springfield", "region": "Midwest"},
    "IN": {"name": "Indiana", "capital": "Indianapolis", "region": "Midwest"},
    "IA": {"name": "Iowa", "capital": "Des Moines", "region": "Midwest"},
    "KS": {"name": "Kansas", "capital": "Topeka", "region": "Great Plains"},
    "KY": {"name": "Kentucky", "capital": "Frankfort", "region": "South/Midwest"},
    "LA": {"name": "Louisiana", "capital": "Baton Rouge", "region": "Gulf South"},
    "ME": {"name": "Maine", "capital": "Augusta", "region": "Northeast"},
    "MD": {"name": "Maryland", "capital": "Annapolis", "region": "Mid-Atlantic"},
    "MA": {"name": "Massachusetts", "capital": "Boston", "region": "Northeast"},
    "MI": {"name": "Michigan", "capital": "Lansing", "region": "Great Lakes"},
    "MN": {"name": "Minnesota", "capital": "Saint Paul", "region": "Upper Midwest"},
    "MS": {"name": "Mississippi", "capital": "Jackson", "region": "Deep South"},
    "MO": {"name": "Missouri", "capital": "Jefferson City", "region": "Midwest"},
    "MT": {"name": "Montana", "capital": "Helena", "region": "Mountain West"},
    "NE": {"name": "Nebraska", "capital": "Lincoln", "region": "Great Plains"},
    "NV": {"name": "Nevada", "capital": "Carson City", "region": "West"},
    "NH": {"name": "New Hampshire", "capital": "Concord", "region": "Northeast"},
    "NJ": {"name": "New Jersey", "capital": "Trenton", "region": "Mid-Atlantic"},
    "NM": {"name": "New Mexico", "capital": "Santa Fe", "region": "Southwest"},
    "NY": {"name": "New York", "capital": "Albany", "region": "Northeast"},
    "NC": {"name": "North Carolina", "capital": "Raleigh", "region": "Southeast"},
    "ND": {"name": "North Dakota", "capital": "Bismarck", "region": "Northern Plains"},
    "OH": {"name": "Ohio", "capital": "Columbus", "region": "Great Lakes/Midwest"},
    "OK": {"name": "Oklahoma", "capital": "Oklahoma City", "region": "Southern Plains"},
    "OR": {"name": "Oregon", "capital": "Salem", "region": "Pacific Northwest"},
    "PA": {"name": "Pennsylvania", "capital": "Harrisburg", "region": "Mid-Atlantic"},
    "RI": {"name": "Rhode Island", "capital": "Providence", "region": "Northeast"},
    "SC": {"name": "South Carolina", "capital": "Columbia", "region": "Southeast"},
    "SD": {"name": "South Dakota", "capital": "Pierre", "region": "Northern Plains"},
    "TN": {"name": "Tennessee", "capital": "Nashville", "region": "Southeast"},
    "TX": {"name": "Texas", "capital": "Austin", "region": "South/Southwest"},
    "UT": {"name": "Utah", "capital": "Salt Lake City", "region": "Mountain West"},
    "VT": {"name": "Vermont", "capital": "Montpelier", "region": "Northeast"},
    "VA": {"name": "Virginia", "capital": "Richmond", "region": "Mid-Atlantic/Southeast"},
    "WA": {"name": "Washington", "capital": "Olympia", "region": "Pacific Northwest"},
    "WV": {"name": "West Virginia", "capital": "Charleston", "region": "Appalachia"},
    "WI": {"name": "Wisconsin", "capital": "Madison", "region": "Upper Midwest"},
    "WY": {"name": "Wyoming", "capital": "Cheyenne", "region": "Mountain West"},
    "DC": {"name": "District of Columbia", "capital": "Washington", "region": "Mid-Atlantic"},
}


COUNTRIES: Dict[str, Dict[str, Any]] = {
    "US": {"name": "United States", "region": "North America"},
    "CA": {"name": "Canada", "region": "North America"},
    "MX": {"name": "Mexico", "region": "North America"},
    "BZ": {"name": "Belize", "region": "Central America"},
    "GT": {"name": "Guatemala", "region": "Central America"},
    "HN": {"name": "Honduras", "region": "Central America"},
    "SV": {"name": "El Salvador", "region": "Central America"},
    "NI": {"name": "Nicaragua", "region": "Central America"},
    "CR": {"name": "Costa Rica", "region": "Central America"},
    "PA": {"name": "Panama", "region": "Central America"},
    "GB": {"name": "United Kingdom", "region": "Europe"},
    "IE": {"name": "Ireland", "region": "Europe"},
    "FR": {"name": "France", "region": "Europe"},
    "DE": {"name": "Germany", "region": "Europe"},
    "ES": {"name": "Spain", "region": "Europe"},
    "IT": {"name": "Italy", "region": "Europe"},
    "JP": {"name": "Japan", "region": "Asia"},
    "KR": {"name": "South Korea", "region": "Asia"},
    "CN": {"name": "China", "region": "Asia"},
    "IN": {"name": "India", "region": "Asia"},
    "AU": {"name": "Australia", "region": "Oceania"},
}


MAJOR_US_CITIES: List[Dict[str, Any]] = [
    {"name": "New York", "state": "NY"},
    {"name": "Los Angeles", "state": "CA"},
    {"name": "Chicago", "state": "IL"},
    {"name": "Houston", "state": "TX"},
    {"name": "Phoenix", "state": "AZ"},
    {"name": "Philadelphia", "state": "PA"},
    {"name": "San Antonio", "state": "TX"},
    {"name": "San Diego", "state": "CA"},
    {"name": "Dallas", "state": "TX"},
    {"name": "Austin", "state": "TX"},
    {"name": "Jacksonville", "state": "FL"},
    {"name": "Fort Worth", "state": "TX"},
    {"name": "Columbus", "state": "OH"},
    {"name": "Charlotte", "state": "NC"},
    {"name": "San Francisco", "state": "CA"},
    {"name": "Indianapolis", "state": "IN"},
    {"name": "Seattle", "state": "WA"},
    {"name": "Denver", "state": "CO"},
    {"name": "Washington", "state": "DC"},
    {"name": "Boston", "state": "MA"},
    {"name": "El Paso", "state": "TX"},
    {"name": "Nashville", "state": "TN"},
    {"name": "Detroit", "state": "MI"},
    {"name": "Oklahoma City", "state": "OK"},
    {"name": "Portland", "state": "OR"},
    {"name": "Las Vegas", "state": "NV"},
    {"name": "Memphis", "state": "TN"},
    {"name": "Louisville", "state": "KY"},
    {"name": "Baltimore", "state": "MD"},
    {"name": "Milwaukee", "state": "WI"},
    {"name": "Albuquerque", "state": "NM"},
    {"name": "Tucson", "state": "AZ"},
    {"name": "Fresno", "state": "CA"},
    {"name": "Sacramento", "state": "CA"},
    {"name": "Atlanta", "state": "GA"},
    {"name": "Kansas City", "state": "MO"},
    {"name": "Miami", "state": "FL"},
    {"name": "Raleigh", "state": "NC"},
    {"name": "Omaha", "state": "NE"},
    {"name": "Minneapolis", "state": "MN"},
    {"name": "New Orleans", "state": "LA"},
    {"name": "Birmingham", "state": "AL"},
    {"name": "Montgomery", "state": "AL"},
    {"name": "Mobile", "state": "AL"},
    {"name": "Huntsville", "state": "AL"},
    {"name": "Tuscaloosa", "state": "AL"},
    {"name": "Biloxi", "state": "MS"},
]


def geo_registry_summary() -> Dict[str, Any]:
    return {
        "ok": True,
        "mode": "Watchman Geo Knowledge Registry V1",
        "stateCount": len(US_STATES),
        "countryCount": len(COUNTRIES),
        "majorCityCount": len(MAJOR_US_CITIES),
        "states": US_STATES,
        "countries": COUNTRIES,
        "majorCities": MAJOR_US_CITIES,
        "phase": "Phase 1 gives Watchman awareness of U.S. states, selected countries/regions, and major U.S. cities. Later phases should add full world city inventory and highway geometry.",
    }


def find_state(query: str) -> Dict[str, Any] | None:
    q = (query or "").strip().lower()
    for abbr, data in US_STATES.items():
        if q == abbr.lower() or q == data["name"].lower():
            return {"abbr": abbr, **data}
    return None


def find_country(query: str) -> Dict[str, Any] | None:
    q = (query or "").strip().lower()
    for code, data in COUNTRIES.items():
        if q == code.lower() or q == data["name"].lower():
            return {"code": code, **data}
    return None


def find_city(query: str) -> Dict[str, Any] | None:
    q = (query or "").strip().lower()
    for city in MAJOR_US_CITIES:
        if q == city["name"].lower() or q == f"{city['name']}, {city['state']}".lower():
            state = US_STATES.get(city["state"], {})
            return {**city, "stateName": state.get("name"), "region": state.get("region")}
    return None


def answer_geo_question(question: str) -> Dict[str, Any]:
    q = (question or "").strip()
    ql = q.lower()
    if not q:
        return {"ok": False, "error": "question_required"}

    # Full state names first so "Tell me about Alabama" cannot match "ME".
    for abbr, data in US_STATES.items():
        if data["name"].lower() in ql:
            item = {"abbr": abbr, **data}
            return {
                "ok": True,
                "mode": "Watchman Geo Knowledge",
                "handled": True,
                "match": item,
                "answer": f"Watchman recognizes {data['name']} as a U.S. state in {data.get('region', 'the travel registry')}. Capital: {data.get('capital')}.",
            }

    # Full country names before short country codes.
    for code, data in COUNTRIES.items():
        if data["name"].lower() in ql:
            item = {"code": code, **data}
            return {
                "ok": True,
                "mode": "Watchman Geo Knowledge",
                "handled": True,
                "match": item,
                "answer": f"Watchman recognizes {data['name']} as a country/region in {data.get('region', 'the travel registry')}.",
            }

    # City phrases.
    for city in MAJOR_US_CITIES:
        if city["name"].lower() in ql:
            state = US_STATES.get(city["state"], {})
            item = {**city, "stateName": state.get("name"), "region": state.get("region")}
            return {
                "ok": True,
                "mode": "Watchman Geo Knowledge",
                "handled": True,
                "match": item,
                "answer": f"Watchman recognizes {city['name']}, {city['state']} as a major U.S. city in {state.get('region', 'the travel registry')}.",
            }

    # Abbreviations/codes only when they are standalone meaningful tokens.
    stop_tokens = {"me", "to", "in", "on", "at", "is", "it", "us", "we", "go"}
    tokens = [w.strip(".?!").upper() for w in q.replace(",", " ").split()]
    for token in tokens:
        if token.lower() in stop_tokens:
            continue
        if token in US_STATES:
            data = US_STATES[token]
            item = {"abbr": token, **data}
            return {
                "ok": True,
                "mode": "Watchman Geo Knowledge",
                "handled": True,
                "match": item,
                "answer": f"Watchman recognizes {data['name']} ({token}) as a U.S. state in {data.get('region', 'the travel registry')}.",
            }
        if token in COUNTRIES:
            data = COUNTRIES[token]
            item = {"code": token, **data}
            return {
                "ok": True,
                "mode": "Watchman Geo Knowledge",
                "handled": True,
                "match": item,
                "answer": f"Watchman recognizes {data['name']} ({token}) as a country/region in {data.get('region', 'the travel registry')}.",
            }

    return {
        "ok": True,
        "mode": "Watchman Geo Knowledge",
        "handled": False,
        "answer": "No exact geography match found in the Phase 1 registry.",
    }
