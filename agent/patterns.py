import json
from pathlib import Path
from collections import Counter, defaultdict
from .app_list import CATEGORIES

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_research(path: Path | None = None) -> list[dict]:
    path = path or DATA_DIR / "research_pass1.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_patterns(research: list[dict]) -> dict:
    patterns = {}

    # Auth distribution
    auth_counter = Counter()
    auth_by_category = defaultdict(Counter)
    for r in research:
        for method in r.get("auth_methods", []):
            auth_counter[method] += 1
            auth_by_category[r["category"]][method] += 1
    patterns["auth_distribution"] = {
        "overall": dict(auth_counter.most_common()),
        "by_category": {cat: dict(counts) for cat, counts in auth_by_category.items()},
    }

    # Self-serve rates
    self_serve_by_cat = defaultdict(lambda: {"yes": 0, "no": 0})
    for r in research:
        key = "yes" if r.get("self_serve") else "no"
        self_serve_by_cat[r["category"]][key] += 1
    total_self_serve = sum(1 for r in research if r.get("self_serve"))
    patterns["self_serve"] = {
        "overall_rate": round(total_self_serve / max(len(research), 1) * 100, 1),
        "total_self_serve": total_self_serve,
        "total_gated": len(research) - total_self_serve,
        "by_category": dict(self_serve_by_cat),
    }

    # API landscape
    api_type_counter = Counter(r.get("api_type", "Unknown") for r in research)
    api_breadth_counter = Counter(r.get("api_breadth", "Unknown") for r in research)
    patterns["api_landscape"] = {
        "types": dict(api_type_counter.most_common()),
        "breadth": dict(api_breadth_counter.most_common()),
    }

    # Buildability
    verdict_counter = Counter(r.get("buildability_verdict", "Unknown") for r in research)
    blocker_counter = Counter()
    for r in research:
        blocker = r.get("buildability_blocker", "")
        if blocker:
            blocker_counter[blocker] += 1
    verdict_by_cat = defaultdict(Counter)
    for r in research:
        verdict_by_cat[r["category"]][r.get("buildability_verdict", "Unknown")] += 1
    patterns["buildability"] = {
        "verdicts": dict(verdict_counter.most_common()),
        "top_blockers": dict(blocker_counter.most_common(10)),
        "by_category": {cat: dict(counts) for cat, counts in verdict_by_cat.items()},
    }

    # Easy wins: self-serve + REST + Ready + high confidence
    easy_wins = []
    for r in research:
        if (r.get("self_serve") and
            r.get("buildability_verdict") == "Ready" and
            r.get("api_type", "").startswith("REST") and
            r.get("confidence", 0) >= 0.7):
            easy_wins.append({
                "app_name": r["app_name"],
                "category": r["category"],
                "auth_methods": r["auth_methods"],
                "api_breadth": r["api_breadth"],
                "confidence": r["confidence"],
            })
    patterns["easy_wins"] = easy_wins

    # Needs outreach: Blocked or gated
    needs_outreach = []
    for r in research:
        if r.get("buildability_verdict") == "Blocked" or not r.get("self_serve"):
            needs_outreach.append({
                "app_name": r["app_name"],
                "category": r["category"],
                "blocker": r.get("buildability_blocker", ""),
                "self_serve": r.get("self_serve", False),
            })
    patterns["needs_outreach"] = needs_outreach

    # MCP coverage
    mcp_apps = [
        {"app_name": r["app_name"], "detail": r.get("mcp_server_detail", "")}
        for r in research if r.get("has_mcp_server")
    ]
    patterns["mcp_coverage"] = {
        "count": len(mcp_apps),
        "apps": mcp_apps,
    }

    # Confidence distribution
    confidences = [r.get("confidence", 0) for r in research]
    patterns["confidence"] = {
        "mean": round(sum(confidences) / max(len(confidences), 1), 2),
        "low_confidence_apps": [
            {"app_name": r["app_name"], "confidence": r["confidence"]}
            for r in research if r.get("confidence", 0) < 0.5
        ],
    }

    return patterns


def run(research: list[dict] | None = None) -> dict:
    if research is None:
        research = load_research()

    patterns = extract_patterns(research)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_DIR / "patterns.json", "w", encoding="utf-8") as f:
        json.dump(patterns, f, indent=2, ensure_ascii=False)

    print(f"Patterns extracted from {len(research)} apps")
    print(f"  Auth: {patterns['auth_distribution']['overall']}")
    print(f"  Self-serve: {patterns['self_serve']['overall_rate']}%")
    print(f"  Buildability: {patterns['buildability']['verdicts']}")
    print(f"  Easy wins: {len(patterns['easy_wins'])}")
    print(f"  MCP coverage: {patterns['mcp_coverage']['count']} apps")

    return patterns


if __name__ == "__main__":
    run()
