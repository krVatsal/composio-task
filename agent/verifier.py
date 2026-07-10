import json
import requests
import time
from pathlib import Path
from .schemas import AppResearch

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

SPOT_CHECK_APPS = [
    "Salesforce", "Slack", "Stripe", "GitHub", "Shopify",
    "Linear", "Klaviyo", "Supabase", "Ahrefs", "Front",
    "Twenty", "Pylon", "fanbasis", "Paygent Connect", "higgsfield",
]


def load_research(path: Path | None = None) -> list[dict]:
    path = path or DATA_DIR / "research_pass1.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_urls(research: list[dict]) -> dict:
    results = {}
    url_fields = ["auth_evidence_url", "self_serve_evidence_url", "api_evidence_url"]

    for app in research:
        app_results = {}
        for field in url_fields:
            url = app.get(field, "")
            if not url or url.lower() in ("", "n/a", "unknown", "none"):
                app_results[field] = {"url": url, "status": "empty", "reachable": None}
                continue

            try:
                resp = requests.head(url, timeout=10, allow_redirects=True,
                                     headers={"User-Agent": "Mozilla/5.0 (research-bot)"})
                reachable = resp.status_code < 400
                app_results[field] = {
                    "url": url,
                    "status": resp.status_code,
                    "reachable": reachable,
                }
            except Exception as e:
                app_results[field] = {"url": url, "status": str(e), "reachable": False}

            time.sleep(0.3)

        results[app["app_name"]] = app_results

    return results


def compute_url_stats(url_results: dict) -> dict:
    total = 0
    reachable = 0
    broken = 0
    empty = 0

    for app_name, fields in url_results.items():
        for field, result in fields.items():
            if result["reachable"] is None:
                empty += 1
            elif result["reachable"]:
                reachable += 1
            else:
                broken += 1
            total += 1

    return {
        "total_urls": total,
        "reachable": reachable,
        "broken": broken,
        "empty": empty,
        "reachable_pct": round(reachable / max(total - empty, 1) * 100, 1),
    }


def generate_spot_check_template(research: list[dict]) -> list[dict]:
    app_map = {r["app_name"]: r for r in research}
    template = []
    for name in SPOT_CHECK_APPS:
        if name not in app_map:
            continue
        r = app_map[name]
        template.append({
            "app_name": name,
            "agent_auth_methods": r["auth_methods"],
            "agent_self_serve": r["self_serve"],
            "agent_api_type": r["api_type"],
            "agent_api_breadth": r["api_breadth"],
            "agent_buildability": r["buildability_verdict"],
            "agent_confidence": r["confidence"],
            "verified_auth_correct": None,
            "verified_self_serve_correct": None,
            "verified_api_type_correct": None,
            "verified_buildability_correct": None,
            "notes": "",
        })
    return template


def compute_accuracy(spot_checks: list[dict]) -> dict:
    fields = [
        "verified_auth_correct",
        "verified_self_serve_correct",
        "verified_api_type_correct",
        "verified_buildability_correct",
    ]
    field_stats = {}
    total_correct = 0
    total_checked = 0

    for field in fields:
        correct = sum(1 for s in spot_checks if s.get(field) is True)
        checked = sum(1 for s in spot_checks if s.get(field) is not None)
        field_stats[field.replace("verified_", "").replace("_correct", "")] = {
            "correct": correct,
            "checked": checked,
            "accuracy": round(correct / max(checked, 1) * 100, 1),
        }
        total_correct += correct
        total_checked += checked

    return {
        "overall_accuracy": round(total_correct / max(total_checked, 1) * 100, 1),
        "total_correct": total_correct,
        "total_checked": total_checked,
        "per_field": field_stats,
    }


def run_verification(research: list[dict] | None = None) -> dict:
    if research is None:
        research = load_research()

    print(f"Validating URLs for {len(research)} apps...")
    url_results = validate_urls(research)
    url_stats = compute_url_stats(url_results)
    print(f"URLs: {url_stats['reachable']} reachable, {url_stats['broken']} broken, {url_stats['empty']} empty")

    spot_template = generate_spot_check_template(research)

    verification = {
        "url_validation": {"results": url_results, "stats": url_stats},
        "spot_check_template": spot_template,
        "accuracy": None,
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_DIR / "verification.json", "w", encoding="utf-8") as f:
        json.dump(verification, f, indent=2, ensure_ascii=False)

    print(f"Verification saved. Spot-check template for {len(spot_template)} apps ready.")
    return verification


if __name__ == "__main__":
    run_verification()
