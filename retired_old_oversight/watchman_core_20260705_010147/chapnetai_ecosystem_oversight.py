import json
import subprocess
from pathlib import Path
from datetime import datetime

HOME = Path.home()

REPOS = [
    {
        "name": "ChapNetAI Main",
        "path": HOME / "chapnetai",
        "role": "Federation command and ecosystem backbone",
    },
    {
        "name": "ChapNetAI Portfolio",
        "path": HOME / "chapnetai-portfolio",
        "role": "Public-facing portfolio and founder narrative",
    },
    {
        "name": "ChapNetAI Project History",
        "path": HOME / "chapnetai-project-history",
        "role": "Milestone archive and historical record",
    },
    {
        "name": "ChapNetAI Ecosystem Registry",
        "path": HOME / "chapnetai-ecosystem-registry",
        "role": "Ecosystem registry and command documentation",
    },
    {
        "name": "ChapNetAI Community Hub",
        "path": HOME / "chapnetai-community-hub",
        "role": "Community hub layer",
    },
]

OUTPUT_FILE = Path("watchman_v104_chapnetai_ecosystem_oversight.json")


def run_git(path, args):
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=path,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return ""
        return result.stdout.strip()
    except Exception:
        return ""


def inspect_repo(repo):
    path = repo["path"]
    exists = path.exists()
    is_git = (path / ".git").exists()

    status = "missing"
    branch = ""
    latest_commit = ""
    dirty = False
    file_count = 0

    if exists:
        file_count = sum(1 for p in path.rglob("*") if p.is_file())

    if exists and is_git:
        status_raw = run_git(path, ["status", "--short"])
        branch = run_git(path, ["branch", "--show-current"])
        latest_commit = run_git(path, ["log", "--oneline", "-1"])
        dirty = bool(status_raw.strip())
        status = "dirty" if dirty else "clean"
    elif exists:
        status = "not_git"

    risk_flags = []
    recommendations = []

    if not exists:
        risk_flags.append("Repository path missing.")
        recommendations.append("Verify repository exists on device.")
    elif not is_git:
        risk_flags.append("Directory exists but is not a git repository.")
        recommendations.append("Verify repository initialization and tracking.")
    elif dirty:
        risk_flags.append("Repository has uncommitted changes.")
        recommendations.append("Inspect git status before continuing ecosystem work.")
    elif not latest_commit:
        risk_flags.append("Latest commit could not be read.")
        recommendations.append("Inspect git log and repository health.")

    return {
        "name": repo["name"],
        "path": str(path),
        "role": repo["role"],
        "exists": exists,
        "is_git": is_git,
        "status": status,
        "branch": branch,
        "latest_commit": latest_commit,
        "file_count": file_count,
        "risk_flags": risk_flags,
        "recommendations": recommendations,
    }


def build_chapnetai_ecosystem_oversight():
    repo_reports = [inspect_repo(repo) for repo in REPOS]

    total = len(repo_reports)
    clean = sum(1 for r in repo_reports if r["status"] == "clean")
    dirty = sum(1 for r in repo_reports if r["status"] == "dirty")
    missing = sum(1 for r in repo_reports if not r["exists"])

    risks = []
    recommendations = []

    for repo in repo_reports:
        for risk in repo["risk_flags"]:
            risks.append(f'{repo["name"]}: {risk}')
        for rec in repo["recommendations"]:
            recommendations.append(f'{repo["name"]}: {rec}')

    health = "Healthy"
    if dirty or missing or risks:
        health = "Watch"
    if missing >= 2:
        health = "Risk"

    report = {
        "module": "Watchman V104 ChapNetAI Ecosystem Oversight",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "health": health,
        "metrics": {
            "repos_monitored": total,
            "clean_repos": clean,
            "dirty_repos": dirty,
            "missing_repos": missing,
        },
        "repositories": repo_reports,
        "risks": risks,
        "recommendations": recommendations,
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == "__main__":
    report = build_chapnetai_ecosystem_oversight()
    print(json.dumps(report, indent=2))
