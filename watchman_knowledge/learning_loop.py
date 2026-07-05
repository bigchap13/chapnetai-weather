from __future__ import annotations

from typing import Any, Dict


def _safe_call(name: str, fn):
    try:
        return fn()
    except Exception as exc:
        return {
            "ok": False,
            "mode": name,
            "error": str(exc)[:300],
        }


def learning_loop_status() -> Dict[str, Any]:
    from .learning_memory import learning_summary
    from .learning_review import review_learning
    from .learning_suggestions import suggest_learning_patches, export_patch_plan
    from .learning_clusters import cluster_weak_questions, cluster_patch_plan, approved_patch_plans
    from .feedback_engine import feedback_summary
    from .skill_growth_planner import build_skill_growth_plan
    from .knowledge_engine import knowledge_summary

    memory = _safe_call("Learning Memory", learning_summary)
    review = _safe_call("Learning Review", lambda: review_learning(500))
    suggestions = _safe_call("Learning Suggestions", lambda: suggest_learning_patches(500))
    patch_plan = _safe_call("Patch Plan", lambda: export_patch_plan(500))
    clusters = _safe_call("Learning Clusters", lambda: cluster_weak_questions(500))
    cluster_plan = _safe_call("Cluster Patch Plan", lambda: cluster_patch_plan(500))
    approved = _safe_call("Approved Patch Plans", lambda: approved_patch_plans(100))
    feedback = _safe_call("Feedback Summary", feedback_summary)
    growth = _safe_call("Skill Growth Planner", build_skill_growth_plan)
    knowledge = _safe_call("Knowledge Engine", knowledge_summary)

    health_score = 50

    if memory.get("totalQuestionsLogged", 0) > 0:
        health_score += 10
    if memory.get("weakQuestionsLogged", 0) > 0:
        health_score += 5
    if suggestions.get("suggestionCount", 0) > 0:
        health_score += 10
    if clusters.get("clusterCount", 0) > 0:
        health_score += 10
    if growth.get("priorityCount", 0) > 0:
        health_score += 10
    if knowledge.get("conceptCount", 0) > 0:
        health_score += 5

    health_score = max(0, min(100, health_score))

    next_actions = []

    next_growth = growth.get("nextRecommendedBuild")
    if next_growth:
        next_actions.append({
            "type": "growth_priority",
            "action": next_growth.get("action"),
            "target": next_growth.get("target"),
            "reason": next_growth.get("reason"),
        })

    if suggestions.get("suggestions"):
        top_s = suggestions["suggestions"][0]
        next_actions.append({
            "type": "learning_suggestion",
            "action": "review_candidate_terms",
            "target": top_s.get("domain"),
            "terms": top_s.get("candidateTerms", [])[:8],
        })

    if clusters.get("clusters"):
        top_c = clusters["clusters"][0]
        next_actions.append({
            "type": "cluster_review",
            "action": "review_cluster",
            "target": top_c.get("cluster"),
            "count": top_c.get("count"),
        })

    if not next_actions:
        next_actions.append({
            "type": "collect_more_data",
            "action": "Ask more real user questions",
            "target": "learning_memory",
            "reason": "Not enough weak-question data yet.",
        })

    return {
        "ok": True,
        "mode": "Watchman Continuous Learning Loop V1",
        "healthScore": health_score,
        "pipeline": {
            "memory": memory,
            "review": review,
            "suggestions": suggestions,
            "patchPlan": patch_plan,
            "clusters": clusters,
            "clusterPlan": cluster_plan,
            "approvedPlans": approved,
            "feedback": feedback,
            "growthPlan": growth,
            "knowledge": knowledge,
        },
        "nextActions": next_actions,
        "safeMode": True,
        "note": "This connects Watchman's learning systems into one review loop. It does not rewrite code automatically.",
    }


def learning_loop_summary() -> Dict[str, Any]:
    return learning_loop_status()
