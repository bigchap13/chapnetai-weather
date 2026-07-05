from __future__ import annotations

import re
from typing import Any, Dict, List


MAJOR_HIGHWAY_CORRIDORS: Dict[str, Dict[str, Any]] = {
    "I-10": {
        "name": "Interstate 10",
        "type": "interstate",
        "corridor": "Southern transcontinental corridor",
        "runs": "California to Florida",
        "states": ["CA", "AZ", "NM", "TX", "LA", "MS", "AL", "FL"],
        "watchmanNotes": [
            "Major hurricane evacuation and Gulf Coast travel corridor.",
            "Flooding, tropical systems, heat, smoke, fog, and high wind can matter on this route.",
        ],
    },
    "I-20": {
        "name": "Interstate 20",
        "type": "interstate",
        "corridor": "Southern east-west corridor",
        "runs": "Texas to South Carolina",
        "states": ["TX", "LA", "MS", "AL", "GA", "SC"],
        "watchmanNotes": [
            "Important Deep South travel corridor.",
            "Storm lines, flooding, heat, fog, and construction delays are common Watchman concerns.",
        ],
    },
    "I-22": {
        "name": "Interstate 22",
        "type": "interstate",
        "corridor": "Memphis to Birmingham corridor",
        "runs": "Tennessee/Mississippi to Alabama",
        "states": ["TN", "MS", "AL"],
        "watchmanNotes": [
            "Important northwest Alabama and Birmingham connector.",
            "Storm timing, fog, flooding, and rural response distance matter on this route.",
        ],
    },
    "I-40": {
        "name": "Interstate 40",
        "type": "interstate",
        "corridor": "Major cross-country east-west corridor",
        "runs": "California to North Carolina",
        "states": ["CA", "AZ", "NM", "TX", "OK", "AR", "TN", "NC"],
        "watchmanNotes": [
            "Long-haul national route.",
            "Mountain snow/ice, high wind, desert heat, and severe storms can change decisions.",
        ],
    },
    "I-59": {
        "name": "Interstate 59",
        "type": "interstate",
        "corridor": "Louisiana/Mississippi/Alabama/Georgia corridor",
        "runs": "Louisiana to Georgia",
        "states": ["LA", "MS", "AL", "GA"],
        "watchmanNotes": [
            "Important Alabama and Gulf-region connector.",
            "Watch for severe storms, flooding, fog, construction, and Birmingham traffic impacts.",
        ],
    },
    "I-65": {
        "name": "Interstate 65",
        "type": "interstate",
        "corridor": "Gulf Coast to Midwest corridor",
        "runs": "Alabama to Indiana",
        "states": ["AL", "TN", "KY", "IN"],
        "watchmanNotes": [
            "Major Alabama north-south route.",
            "Storm lines, holiday traffic, fog, flooding, and winter impacts north of Alabama matter.",
        ],
    },
    "I-75": {
        "name": "Interstate 75",
        "type": "interstate",
        "corridor": "Florida to Great Lakes corridor",
        "runs": "Florida to Michigan",
        "states": ["FL", "GA", "TN", "KY", "OH", "MI"],
        "watchmanNotes": [
            "Major north-south travel corridor.",
            "Hurricane evacuation, mountain weather, fog, snow/ice, and congestion can matter.",
        ],
    },
    "I-85": {
        "name": "Interstate 85",
        "type": "interstate",
        "corridor": "Southeastern metro corridor",
        "runs": "Alabama to Virginia",
        "states": ["AL", "GA", "SC", "NC", "VA"],
        "watchmanNotes": [
            "Major Atlanta/Carolinas travel corridor.",
            "Traffic, storms, fog, flooding, and construction are common concerns.",
        ],
    },
    "I-95": {
        "name": "Interstate 95",
        "type": "interstate",
        "corridor": "East Coast corridor",
        "runs": "Florida to Maine",
        "states": ["FL", "GA", "SC", "NC", "VA", "DC", "MD", "DE", "PA", "NJ", "NY", "CT", "RI", "MA", "NH", "ME"],
        "watchmanNotes": [
            "Main East Coast route.",
            "Hurricanes, coastal flooding, winter storms, fog, and traffic delays can dominate decisions.",
        ],
    },
    "US-78": {
        "name": "U.S. Route 78",
        "type": "us_highway",
        "corridor": "Memphis to Charleston corridor",
        "runs": "Tennessee/Mississippi through Alabama and Georgia to South Carolina",
        "states": ["TN", "MS", "AL", "GA", "SC"],
        "watchmanNotes": [
            "Important Walker County / Birmingham-area corridor.",
            "Fog, heavy rain, flooding, local traffic, and severe storms matter.",
        ],
    },
}


HIGHWAY_ALIASES = {
    "INTERSTATE": "I",
    "I": "I",
    "US": "US",
    "U.S.": "US",
    "HIGHWAY": "US",
    "HWY": "US",
}


def normalize_highway_id(text: str) -> str | None:
    raw = (text or "").upper().strip()
    raw = raw.replace("INTERSTATE", "I")
    raw = raw.replace("U.S.", "US")
    raw = raw.replace("U S", "US")
    raw = raw.replace("HIGHWAY", "US")
    raw = raw.replace("HWY", "US")
    raw = raw.replace("ROUTE", "US")
    raw = raw.replace(" ", "-")
    raw = raw.replace("--", "-")

    m = re.search(r"\b(I|US)-?(\d{1,3})\b", raw)
    if not m:
        return None

    prefix, number = m.group(1), int(m.group(2))
    return f"{prefix}-{number}"


def extract_highways(question: str) -> List[str]:
    q = (question or "").upper()
    found: List[str] = []

    patterns = [
        r"\bI[-\s]?(\d{1,3})\b",
        r"\bINTERSTATE\s+(\d{1,3})\b",
        r"\bUS[-\s]?(\d{1,3})\b",
        r"\bU\.S\.\s*(\d{1,3})\b",
        r"\bHIGHWAY\s+(\d{1,3})\b",
        r"\bHWY\s+(\d{1,3})\b",
        r"\bROUTE\s+(\d{1,3})\b",
    ]

    for pat in patterns:
        for m in re.finditer(pat, q):
            if "INTERSTATE" in pat or "I[-" in pat:
                hid = f"I-{int(m.group(1))}"
            else:
                hid = f"US-{int(m.group(1))}"
            if hid not in found:
                found.append(hid)

    return found


def describe_highway(highway_id: str) -> Dict[str, Any]:
    hid = normalize_highway_id(highway_id) or highway_id.upper()
    known = MAJOR_HIGHWAY_CORRIDORS.get(hid)

    if known:
        return {
            "ok": True,
            "known": True,
            "highwayId": hid,
            **known,
        }

    if re.match(r"^I-\d{1,3}$", hid):
        return {
            "ok": True,
            "known": False,
            "highwayId": hid,
            "name": f"Interstate {hid.split('-')[1]}",
            "type": "interstate",
            "corridor": "Interstate highway",
            "runs": "Exact corridor not loaded in Phase 1 registry yet.",
            "states": [],
            "watchmanNotes": [
                "Watchman recognizes this as an Interstate route.",
                "Later phases should attach full state-by-state corridor data, geometry, exits, closures, and weather/traffic intelligence.",
            ],
        }

    if re.match(r"^US-\d{1,3}$", hid):
        return {
            "ok": True,
            "known": False,
            "highwayId": hid,
            "name": f"U.S. Route {hid.split('-')[1]}",
            "type": "us_highway",
            "corridor": "U.S. highway",
            "runs": "Exact corridor not loaded in Phase 1 registry yet.",
            "states": [],
            "watchmanNotes": [
                "Watchman recognizes this as a U.S. highway.",
                "Later phases should attach full state-by-state corridor data, geometry, towns, closures, and road-condition intelligence.",
            ],
        }

    return {
        "ok": False,
        "error": "highway_not_recognized",
        "input": highway_id,
    }


def answer_highway_question(question: str) -> Dict[str, Any]:
    highways = extract_highways(question)

    if not highways:
        return {
            "ok": True,
            "mode": "Watchman Highway Knowledge",
            "handled": False,
            "answer": "I did not detect a specific highway number. Ask about a route like I-65, I-20, US-78, or Highway 280.",
            "highways": [],
        }

    descriptions = [describe_highway(h) for h in highways]

    first = descriptions[0]
    if first.get("known"):
        answer = (
            f"{first['name']} is a {first['corridor']} running {first['runs']}. "
            f"Watchman should watch this route for: "
            + "; ".join(first.get("watchmanNotes", []))
        )
    else:
        answer = (
            f"I recognize {first.get('name', highways[0])}, but full corridor details are not loaded yet. "
            "Watchman can still use routing geometry for trips, and later registry phases should add full map knowledge for this highway."
        )

    return {
        "ok": True,
        "mode": "Watchman Highway Knowledge",
        "handled": True,
        "answer": answer,
        "highways": descriptions,
    }


def highway_registry_summary() -> Dict[str, Any]:
    return {
        "ok": True,
        "mode": "Watchman Highway Knowledge Registry V1",
        "knownCorridorCount": len(MAJOR_HIGHWAY_CORRIDORS),
        "knownCorridors": MAJOR_HIGHWAY_CORRIDORS,
        "phase": "Phase 1 recognizes highway language and seeds major corridors. Later phases attach full U.S. route inventory, geometry, states, exits, closures, and road-condition feeds.",
    }
