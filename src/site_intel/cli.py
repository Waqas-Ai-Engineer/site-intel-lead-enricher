from __future__ import annotations
import argparse
import logging
from pathlib import Path
from .pipeline import run


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="site-intel", description="Enrich & score business leads from their websites")
    ap.add_argument("input", type=Path, help="CSV with columns: name,website")
    ap.add_argument("-o", "--output", type=Path, default=Path("output"))
    ap.add_argument("-w", "--workers", type=int, default=4)
    ap.add_argument("--no-llm", action="store_true", help="skip the AI summary")
    ap.add_argument("--ignore-robots", action="store_true", help="not recommended")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if a.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    res = run(a.input, a.output, a.workers, not a.no_llm, not a.ignore_robots)
    hot = sum(r["tier"] == "HOT" for r in res)
    print(f"Done: {len(res)} leads ({hot} HOT) -> {a.output}/enriched_leads.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
