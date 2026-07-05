from __future__ import annotations

import re
from typing import Any, Dict, List


WATCHMAN_CONCEPTS: Dict[str, Dict[str, Any]] = {
    "mow_grass": {
        "label": "Mowing Grass",
        "terms": ["mow", "mowing", "cut grass", "yard", "lawn"],
        "dependsOn": ["rain_timing", "lightning", "heat_index", "soil_saturation", "wind"],
        "watchmanLogic": "Mowing depends on rain timing, lightning risk, heat, wet ground, and whether the yard can dry before dark.",
    },
    "tow_camper": {
        "label": "Towing Camper",
        "terms": ["tow camper", "pull camper", "camper", "trailer", "tow"],
        "dependsOn": ["crosswind", "heavy_rain", "road_closures", "visibility", "route_grade"],
        "watchmanLogic": "Towing is more sensitive than normal driving. Wind, rain, visibility, and road hazards matter more.",
    },
    "dog_walk": {
        "label": "Dog Walk",
        "terms": ["walk dog", "dog walk", "take the dog out", "pet outside"],
        "dependsOn": ["heat_index", "pavement_heat", "lightning", "air_quality", "rain_timing"],
        "watchmanLogic": "Dog walks depend on heat, pavement temperature, storms, air quality, and rain timing.",
    },
    "kids_outside": {
        "label": "Kids Outside",
        "terms": ["kids outside", "kids play", "children outside", "park", "playground"],
        "dependsOn": ["lightning", "heat_index", "air_quality", "rain_timing", "wind"],
        "watchmanLogic": "Kids outside depends on lightning, heat, air quality, rain timing, and comfort.",
    },
    "boat_lake": {
        "label": "Boating / Lake",
        "terms": ["boat", "boating", "lake", "kayak", "canoe"],
        "dependsOn": ["wind", "gusts", "lightning", "waves", "visibility"],
        "watchmanLogic": "Boating depends heavily on wind, gusts, lightning, visibility, and water conditions.",
    },
    "biloxi": {
        "label": "Biloxi / Gulf Coast",
        "terms": ["biloxi", "gulf coast", "mississippi coast"],
        "dependsOn": ["tropical_weather", "coastal_flooding", "heat_index", "heavy_rain", "fog"],
        "watchmanLogic": "Biloxi is a Gulf Coast destination where tropical systems, flooding, heat, fog, and storms can matter.",
    },
    "road_trip": {
        "label": "Road Trip",
        "terms": ["road trip", "trip", "drive", "route", "travel"],
        "dependsOn": ["route_weather", "road_closures", "fuel", "rest_stops", "arrival_weather"],
        "watchmanLogic": "A road trip depends on route weather, road conditions, stops, timing, and destination conditions.",
    },
    "safe_place": {
        "label": "Safe Place",
        "terms": ["safe place", "where should i go", "shelter", "pull over safely"],
        "dependsOn": ["hazard_type", "nearest_public_place", "emergency_services", "road_safety"],
        "watchmanLogic": "Safe place advice depends on the hazard, location, nearby shelter, road safety, and emergency services.",
    },
}

from pathlib import Path
import json

CUSTOM_CONCEPTS_FILE = Path("data/watchman_knowledge/custom_concepts.json")


def _load_custom_concepts() -> Dict[str, Dict[str, Any]]:
    if not CUSTOM_CONCEPTS_FILE.exists():
        return {}
    try:
        data = json.loads(CUSTOM_CONCEPTS_FILE.read_text(encoding="utf-8"))
        concepts = data.get("concepts", {})
        return concepts if isinstance(concepts, dict) else {}
    except Exception:
        return {}


def all_watchman_concepts() -> Dict[str, Dict[str, Any]]:
    merged = dict(WATCHMAN_CONCEPTS)
    merged.update(_load_custom_concepts())
    return merged


def find_concepts(question: str) -> List[Dict[str, Any]]:
    q = (question or "").lower()
    matches: List[Dict[str, Any]] = []

    for concept_id, data in all_watchman_concepts().items():
        score = 0
        for term in data.get("terms", []):
            t = term.lower()
            if " " in t:
                if t in q:
                    score += 3
            elif re.search(r"\b" + re.escape(t) + r"\b", q):
                score += 1

        if score:
            matches.append({
                "conceptId": concept_id,
                "score": score,
                **data,
            })

    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches


def explain_concepts(question: str) -> Dict[str, Any]:
    concepts = find_concepts(question)

    if not concepts:
        return {
            "ok": True,
            "mode": "Watchman Knowledge Engine",
            "handled": False,
            "answer": "No Watchman knowledge concept matched yet.",
            "concepts": [],
        }

    primary = concepts[0]
    related = []
    seen = set()

    for c in concepts:
        for dep in c.get("dependsOn", []):
            if dep not in seen:
                seen.add(dep)
                related.append(dep)

    return {
        "ok": True,
        "mode": "Watchman Knowledge Engine",
        "handled": True,
        "primaryConcept": primary,
        "concepts": concepts,
        "relatedFactors": related,
        "answer": f"{primary['label']} depends on: " + ", ".join(primary.get("dependsOn", [])) + f". {primary.get('watchmanLogic')}",
    }


def knowledge_summary() -> Dict[str, Any]:
    return {
        "ok": True,
        "mode": "Watchman Knowledge Engine V1",
        "conceptCount": len(all_watchman_concepts()),
        "baseConceptCount": len(WATCHMAN_CONCEPTS),
        "customConceptCount": len(_load_custom_concepts()),
        "concepts": all_watchman_concepts(),
        "purpose": "Structured concept knowledge for reasoning beyond exact question matching.",
    }
