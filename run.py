#!/usr/bin/env python3
"""Main entry point — runs the full pipeline: research → verify → patterns → export."""
import sys
import argparse


def main():
    parser = argparse.ArgumentParser(description="Composio App Research Agent")
    parser.add_argument("step", nargs="?", default="all",
                        choices=["all", "research", "verify", "patterns", "export"],
                        help="Which step to run (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without API calls")
    parser.add_argument("--start", type=int, default=0, help="Start from app index N")
    args = parser.parse_args()

    if args.step in ("all", "research"):
        print("=== Step 1: Research ===")
        from agent.orchestrator import run as run_research
        run_research(start_from=args.start, dry_run=args.dry_run)

    if args.step in ("all", "verify"):
        print("\n=== Step 2: Verification ===")
        from agent.verifier import run_verification
        run_verification()

    if args.step in ("all", "patterns"):
        print("\n=== Step 3: Pattern Analysis ===")
        from agent.patterns import run as run_patterns
        run_patterns()

    if args.step in ("all", "export"):
        print("\n=== Step 4: HTML Export ===")
        from agent.export import run as run_export
        run_export()

    print("\nDone!")


if __name__ == "__main__":
    main()
