# -*- coding: utf-8 -*-
"""stock-analyzer 코드를 project_level=personal로 재리뷰하는 배치 스크립트."""

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.orchestrator import Orchestrator

STOCK_ANALYZER = Path(r"C:\Users\sy.ahn\OneDrive - Bosch Group\AI Development\stock-analyzer")

BATCHES = {
    "review_personal_batch1.json": {
        "desc": "Core (api_client, orchestrator, database, cache, analysis router)",
        "files": [
            ("data/api_client.py", "python"),
            ("agents/orchestrator.py", "python"),
            ("data/database.py", "python"),
            ("data/cache.py", "python"),
            ("backend/routers/analysis.py", "python"),
        ],
    },
    "review_personal_batch2a.json": {
        "desc": "Agents (analyst, claude_client, cross_validation, compare)",
        "files": [
            ("agents/analyst_agent.py", "python"),
            ("agents/claude_client.py", "python"),
            ("agents/cross_validation.py", "python"),
            ("agents/compare_agent.py", "python"),
        ],
    },
    "review_personal_batch2b.json": {
        "desc": "Agents (news, data, macro, sector_analyzer)",
        "files": [
            ("agents/news_agent.py", "python"),
            ("agents/data_agent.py", "python"),
            ("agents/macro_agent.py", "python"),
            ("agents/sector_analyzer.py", "python"),
        ],
    },
    "review_personal_batch3.json": {
        "desc": "Backend Routers (main, quote, sector, compare, market, watchlist, search, alerts, guide)",
        "files": [
            ("backend/main.py", "python"),
            ("backend/routers/quote.py", "python"),
            ("backend/routers/sector.py", "python"),
            ("backend/routers/compare.py", "python"),
            ("backend/routers/market.py", "python"),
            ("backend/routers/watchlist.py", "python"),
            ("backend/routers/search.py", "python"),
            ("backend/routers/alerts.py", "python"),
            ("backend/routers/guide.py", "python"),
        ],
    },
    "review_personal_batch4a.json": {
        "desc": "Data Clients (finnhub, finviz, fmp, fred)",
        "files": [
            ("data/finnhub_client.py", "python"),
            ("data/finviz_client.py", "python"),
            ("data/fmp_client.py", "python"),
            ("data/fred_client.py", "python"),
        ],
    },
    "review_personal_batch4b.json": {
        "desc": "Data Clients (twelvedata, yfinance, watchlist, alerts)",
        "files": [
            ("data/twelvedata_client.py", "python"),
            ("data/yfinance_client.py", "python"),
            ("data/watchlist.py", "python"),
            ("data/alerts.py", "python"),
        ],
    },
}


def read_and_concat(files: list[tuple[str, str]]) -> str:
    parts = []
    for rel_path, _ in files:
        full = STOCK_ANALYZER / rel_path
        if not full.exists():
            print(f"  [SKIP] {rel_path} not found")
            continue
        code = full.read_text(encoding="utf-8")
        parts.append(f"# === FILE: {Path(rel_path).name} ===\n{code}")
    return "\n\n".join(parts)


def main():
    config = Config()
    config.project_level = "personal"
    config.max_code_lines = 1500

    print(f"Model: {config.model}")
    print(f"Project Level: {config.project_level}")
    print(f"Max Lines: {config.max_code_lines}")
    print()

    for out_file, batch_info in BATCHES.items():
        out_path = Path(__file__).parent / out_file
        if out_path.exists():
            print(f"[SKIP] {out_file} already exists")
            continue

        desc = batch_info["desc"]
        files = batch_info["files"]

        print(f"{'='*60}")
        print(f"Batch: {desc}")
        print(f"Files: {[f[0] for f in files]}")

        code = read_and_concat(files)
        lines = code.strip().split("\n")
        print(f"Total lines: {len(lines)}")

        if len(lines) > config.max_code_lines:
            print(f"  [WARN] Exceeds max ({config.max_code_lines}). Truncating.")
            code = "\n".join(lines[:config.max_code_lines])

        orchestrator = Orchestrator(config)

        t0 = time.time()
        try:
            result = orchestrator.run(code, language="python")
            elapsed = time.time() - t0

            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            summary = result.get("findings", {}).get("summary", {})
            score = summary.get("overall_score", "?")
            grade = summary.get("grade", "?")
            print(f"  => Score: {score}/100 | Grade: {grade} | Time: {elapsed:.1f}s")
            print(f"  => Saved: {out_file}")
        except Exception as e:
            print(f"  => ERROR: {e}")

        print()

    print("All batches done!")


if __name__ == "__main__":
    main()
