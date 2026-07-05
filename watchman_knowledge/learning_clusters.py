from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

WEAK_QUESTIONS = Path("data/watchman_learning/weak_questions.jsonl")
APPROVED_PLANS = Path("data/watchman_learning/approved_patch_plans.jsonl")

CLUSTER_RULES = {
    "daily_planning": ["day", "today", "weird", "thing", "worry", "worried", "plan"],
    "leave_wait_drive": ["leave", "wait", "drive", "route", "trip", "arrive"],
    "yard_work": ["mow", "yard", "grass", "roof", "outside", "work"],
    "family_pets": ["kids", "dog", "park", "baby", "family"],
    "local_stops": ["gas", "food", "bathroom", "hotel", "charger", "rest"],
    "emergency_safety": ["tornado", "flood", "shelter", "stranded", "danger", "911"],
    "vehicle_towing": ["tow", "camper", "trailer", "rv", "truck", "semi"],
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    return re.findall(r"[a-z0-9']+", (text or "").lower())


def cluster_weak_questions(limit: int = 500) -> Dict[str, Any]:
    rows = _read_jsonl(WEAK_QUESTIONS, limit)
    clusters: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for row in rows:
        q = row.get("question") or ""
        toks = set(_tokens(q))
        best = "uncategorized"
        best_score = 0

        for cluster, terms in CLUSTER_RULES.items():
            score = sum(1 for t in terms if t in toks or t in q.lower())
            if score > best_score:
                best = cluster
                best_score = score

        clusters[best].append(row)

    output = []
    for name, items in sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True):
        examples = [i.get("question") for i in items[:10]]
        lead_skills = {}
        for i in items:
            k = i.get("leadSkill") or "unknown"
            lead_skills[k] = lead_skills.get(k, 0) + 1

        output.append({
            "cluster": name,
            "count": len(items),
            "leadSkills": lead_skills,
            "examples": examples,
            "recommendedAction": f"Review {name} and add stronger router terms or answer patterns if this repeats.",
        })

    return {
        "ok": True,
        "mode": "Watchman Learning Clusters V1",
        "weakQuestionsReviewed": len(rows),
        "clusterCount": len(output),
        "clusters": output,
    }


def approve_patch_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    APPROVED_PLANS.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": _now(),
        "approved": True,
        "plan": plan,
    }
    with APPROVED_PLANS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return {
        "ok": True,
        "mode": "Watchman Approved Patch Plan",
        "approvedPlan": row,
    }


def approved_patch_plans(limit: int = 100) -> Dict[str, Any]:
    rows = _read_jsonl(APPROVED_PLANS, limit)
    return {
        "ok": True,
        "mode": "Watchman Approved Patch Plans",
        "count": len(rows),
        "plans": rows,
    }


def cluster_patch_plan(limit: int = 500) -> Dict[str, Any]:
    clusters = cluster_weak_questions(limit)
    plans = []

    for c in clusters.get("clusters", []):
        if c["count"] < 1:
            continue
        plans.append({
            "cluster": c["cluster"],
            "patchType": "improve_cluster_handling",
            "count": c["count"],
            "examples": c["examples"][:5],
            "humanReviewRequired": True,
            "recommendedAction": c["recommendedAction"],
        })

    return {
        "ok": True,
        "mode": "Watchman Cluster Patch Plan V1",
        "planCount": len(plans),
        "plans": plans,
    }
