from __future__ import annotations

from typing import Any, Dict, List


def build_skill_growth_plan() -> Dict[str, Any]:
    review: Dict[str, Any] = {}
    suggestions: Dict[str, Any] = {}
    clusters: Dict[str, Any] = {}
    feedback: Dict[str, Any] = {}

    try:
        from .learning_review import review_learning
        review = review_learning(500)
    except Exception as exc:
        review = {"ok": False, "error": str(exc)[:200]}

    try:
        from .learning_suggestions import suggest_learning_patches
        suggestions = suggest_learning_patches(500)
    except Exception as exc:
        suggestions = {"ok": False, "error": str(exc)[:200]}

    try:
        from .learning_clusters import cluster_weak_questions, cluster_patch_plan
        clusters = cluster_weak_questions(500)
        cluster_plans = cluster_patch_plan(500)
    except Exception as exc:
        clusters = {"ok": False, "error": str(exc)[:200]}
        cluster_plans = {"ok": False, "plans": []}

    try:
        from .feedback_engine import feedback_summary
        feedback = feedback_summary()
    except Exception as exc:
        feedback = {"ok": False, "error": str(exc)[:200]}

    priorities: List[Dict[str, Any]] = []

    for s in suggestions.get("suggestions", []):
        priorities.append({
            "source": "learning_suggestions",
            "priorityScore": int(s.get("priority") or 0) + 10,
            "target": s.get("domain"),
            "action": "expand_router_terms",
            "reason": s.get("recommendedAction"),
            "candidateTerms": s.get("candidateTerms", []),
            "examples": s.get("exampleQuestions", []),
        })

    for c in clusters.get("clusters", []):
        priorities.append({
            "source": "learning_clusters",
            "priorityScore": int(c.get("count") or 0) * 5,
            "target": c.get("cluster"),
            "action": "improve_cluster_handling",
            "reason": c.get("recommendedAction"),
            "candidateTerms": [],
            "examples": c.get("examples", []),
        })

    for ex in feedback.get("weakExamples", []):
        priorities.append({
            "source": "feedback",
            "priorityScore": 20,
            "target": ex.get("leadSkill") or "unknown",
            "action": "improve_answer_quality",
            "reason": ex.get("feedback") or "User marked this answer weak.",
            "candidateTerms": [],
            "examples": [ex.get("question")],
        })

    priorities.sort(key=lambda x: x.get("priorityScore", 0), reverse=True)

    top = priorities[:10]

    return {
        "ok": True,
        "mode": "Watchman Skill Growth Planner V1",
        "signals": {
            "weakQuestionsReviewed": review.get("weakQuestionsReviewed"),
            "suggestionCount": suggestions.get("suggestionCount"),
            "clusterCount": clusters.get("clusterCount"),
            "badFeedback": feedback.get("badFeedback"),
            "successRate": feedback.get("successRate"),
        },
        "priorityCount": len(priorities),
        "priorities": top,
        "nextRecommendedBuild": top[0] if top else None,
        "safeMode": True,
        "note": "Planner recommends improvements only. It does not rewrite code automatically.",
    }


def growth_plan_summary() -> Dict[str, Any]:
    return build_skill_growth_plan()
