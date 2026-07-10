import json
import time
import sys
import os
from pathlib import Path
import os
from openai import AzureOpenAI
from tavily import TavilyClient
from .app_list import APPS
from .researcher import research_app


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_FILE = DATA_DIR / "research_pass1.json"


def load_existing() -> dict[str, dict]:
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {r["app_name"]: r for r in data}
    return {}


def save_results(results: dict[str, dict]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(list(results.values()), f, indent=2, ensure_ascii=False)


def run(start_from: int = 0, dry_run: bool = False):
    openai_client = AzureOpenAI(
        azure_endpoint=os.environ["LLM_API_BASE"],
        api_key=os.environ["LLM_API_KEY"],
        api_version=os.environ["LLM_API_VERSION"],
    )
    tavily_client = TavilyClient()
    completed = load_existing()
    total = len(APPS)
    failures = []

    print(f"Starting research: {total} apps, {len(completed)} already done")

    for i, app in enumerate(APPS):
        if i < start_from:
            continue

        if app["name"] in completed:
            print(f"[{i+1}/{total}] {app['name']} — skipped (already done)")
            continue

        if dry_run:
            print(f"[{i+1}/{total}] {app['name']} — would research (dry run)")
            continue

        print(f"[{i+1}/{total}] {app['name']} ({app['category']})...", end=" ", flush=True)

        for attempt in range(3):
            try:
                result = research_app(app, openai_client=openai_client, tavily_client=tavily_client)
                completed[app["name"]] = result.model_dump()
                save_results(completed)
                print(f"done (confidence: {result.confidence:.1f})")
                break
            except Exception as e:
                if attempt < 2:
                    print(f"retry {attempt+1}...", end=" ", flush=True)
                    time.sleep(2 ** attempt)
                else:
                    print(f"FAILED: {e}")
                    failures.append({"app": app["name"], "error": str(e)})

        time.sleep(1.0)

    print(f"\nComplete: {len(completed)}/{total} apps researched")
    if failures:
        print(f"Failures ({len(failures)}):")
        for f in failures:
            print(f"  - {f['app']}: {f['error']}")

    return completed


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    start = 0
    for arg in sys.argv[1:]:
        if arg.startswith("--start="):
            start = int(arg.split("=")[1])
    run(start_from=start, dry_run=dry)
