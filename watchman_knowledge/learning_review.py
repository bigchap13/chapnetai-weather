from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List

WEAK_QUESTIONS = Path("data/watchman_learning/weak_questions.jsonl")
QUESTION_LOG = Path("data/watchman_learning/question_log.jsonl")


STOPWORDS = {
    "the", "and", "for", "you", "with", "that", "this", "what", "when",
    "where", "should", "could", "would", "watchman", "today", "tonight",
    "tomorrow", "like", "need", "know", "have", "will", "about", "from",
}


def _read_jsonl(path: Path, limit: int = 500) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.exists():
        return rows

    for line in path.read_text(encoding="utf-8").splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
    return rows


def _tokens(text: str) -> List[str]:
    words = re.findall(r"[a-z0-9']+", (text or "").lower())
    return [w for w in words if len(w) >= 3 and w not in STOPWORDS]


def review_learning(limit: int = 300) -> Dict[str, Any]:
    weak = _read_jsonl(WEAK_QUESTIONS, limit)
    allq = _read_jsonl(QUESTION_LOG, limit)

    token_counts = Counter()
    lead_counts = Counter()
    decision_counts = Counter()
    low_confidence_examples: List[Dict[str, Any]] = []

    for row in weak:
        question = row.get("question") or ""
        token_counts.update(_tokens(question))
        lead_counts[row.get("leadSkill") or "unknown"] += 1
        decision_counts[row.get("overallDecision") or "unknown"] += 1

        if len(low_confidence_examples) < 15:
            low_confidence_examples.append({
                "question": question,
                "leadSkill": row.get("leadSkill"),
                "confidence": row.get("confidence"),
                "decision": row.get("overallDecision"),
            })

    topic_hints = []
    top_words = [w for w, _ in token_counts.most_common(25)]

    topic_rules = {
        "weather_timing": ["rain", "storm", "storms", "lightning", "wind", "heat", "cold"],
        "travel_decision": ["drive", "route", "leave", "wait", "trip", "arrive"],
        "local_services": ["gas", "food", "hotel", "bathroom", "charger", "tow"],
        "outdoor_work": ["mow", "roof", "work", "outside", "yard"],
        "family_pets": ["kids", "dog", "park", "family", "baby"],
        "emergency": ["tornado", "flood", "shelter", "emergency", "stranded"],
    }

    for topic, keys in topic_rules.items():
        hits = [k for k in keys if k in top_words]
        if hits:
            topic_hints.append({
                "topic": topic,
                "matchedWords": hits,
                "recommendation": f"Expand Brain Router terms and answer patterns for {topic}.",
            })

    missing_intent_suggestions = []
    for word, count in token_counts.most_common(15):
        missing_intent_suggestions.append({
            "keyword": word,
            "count": count,
            "suggestion": f"Check whether '{word}' needs a new intent phrase or module keyword.",
        })

    return {
        "ok": True,
        "mode": "Watchman Learning Review V1",
        "totalRecentQuestions": len(allq),
        "weakQuestionsReviewed": len(weak),
        "weakLeadSkills": dict(lead_counts.most_common()),
        "weakDecisions": dict(decision_counts.most_common()),
        "topWeakWords": token_counts.most_common(25),
        "topicHints": topic_hints,
        "missingIntentSuggestions": missing_intent_suggestions,
        "examples": low_confidence_examples,
        "nextAction": "Add high-frequency weak words to the correct module/router and retest those questions.",
    }


def learning_review_summary() -> Dict[str, Any]:
    return review_learning(300)
