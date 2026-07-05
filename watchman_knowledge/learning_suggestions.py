from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List

WEAK_QUESTIONS = Path("data/watchman_learning/weak_questions.jsonl")

DOMAIN_HINTS = {
    "travel": ["drive", "trip", "route", "leave", "wait", "arrive", "destination", "traffic"],
    "road": ["road", "highway", "interstate", "closed", "closure", "icy", "slick", "construction"],
    "vehicle": ["tow", "camper", "trailer", "rv", "truck", "semi", "motorcycle", "ev"],
    "outdoor": ["mow", "fish", "boat", "hike", "camp", "roof", "outside", "yard"],
    "local_services": ["gas", "food", "bathroom", "hotel", "charger", "tow", "hospital"],
    "emergency": ["tornado", "flood", "shelter", "stranded", "911", "danger", "evacuate"],
    "real_life": ["should", "would", "better", "worse", "worth", "suck", "worry", "weird"],
}

STOPWORDS = {
    "the", "and", "for", "you", "that", "this", "what", "when", "where",
    "should", "would", "could", "watchman", "today", "tonight", "tomorrow",
    "with", "from", "have", "will", "need", "know", "like",
}


def _read_weak(limit: int = 500) -> List[Dict[str, Any]]:
    rows = []
    if not WEAK_QUESTIONS.exists():
        return rows

    for line in WEAK_QUESTIONS.read_text(encoding="utf-8").splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
    return rows


def _tokens(text: str) -> List[str]:
    words = re.findall(r"[a-z0-9']+", (text or "").lower())
    return [w for w in words if len(w) >= 3 and w not in STOPWORDS]


def suggest_learning_patches(limit: int = 500) -> Dict[str, Any]:
    rows = _read_weak(limit)

    domain_scores = Counter()
    word_counts = Counter()
    examples_by_domain = defaultdict(list)

    for row in rows:
        q = row.get("question") or ""
        toks = _tokens(q)
        word_counts.update(toks)

        for domain, hints in DOMAIN_HINTS.items():
            score = sum(1 for h in hints if h in toks or h in q.lower())
            if score:
                domain_scores[domain] += score
                if len(examples_by_domain[domain]) < 10:
                    examples_by_domain[domain].append(q)

    suggestions = []

    for domain, score in domain_scores.most_common():
        candidate_terms = []
        for word, count in word_counts.most_common(40):
            if word not in DOMAIN_HINTS.get(domain, []) and count >= 1:
                candidate_terms.append(word)

        suggestions.append({
            "domain": domain,
            "priority": score,
            "candidateTerms": candidate_terms[:12],
            "exampleQuestions": examples_by_domain[domain],
            "recommendedAction": f"Review these weak questions and consider adding candidate terms to the {domain} router/module.",
        })

    return {
        "ok": True,
        "mode": "Watchman Learning Suggestions V1",
        "weakQuestionsReviewed": len(rows),
        "suggestionCount": len(suggestions),
        "suggestions": suggestions,
        "safeMode": True,
        "note": "This does not rewrite code automatically. It proposes changes for review.",
    }


def export_patch_plan(limit: int = 500) -> Dict[str, Any]:
    suggestions = suggest_learning_patches(limit)
    plan = []

    for s in suggestions.get("suggestions", []):
        domain = s["domain"]
        terms = s.get("candidateTerms", [])
        if not terms:
            continue

        plan.append({
            "domain": domain,
            "patchType": "add_router_terms",
            "terms": terms,
            "humanReviewRequired": True,
            "reason": f"Weak questions repeatedly look related to {domain}.",
        })

    return {
        "ok": True,
        "mode": "Watchman Learning Patch Plan V1",
        "planCount": len(plan),
        "plans": plan,
    }
