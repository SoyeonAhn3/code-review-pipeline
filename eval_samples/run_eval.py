"""
자동 채점 스크립트
eval 샘플을 파이프라인에 실행하고 정답지와 비교하여 정탐률/오탐률을 측정한다.

사용법:
    py eval_samples/run_eval.py
    py eval_samples/run_eval.py --sample 01    # 특정 샘플만 실행
"""

import json
import sys
import os
from pathlib import Path

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import Config
from src.orchestrator import Orchestrator

EVAL_DIR = Path(__file__).resolve().parent

# ── 샘플 목록 ──
SAMPLES = [
    {"id": "01", "file": "sample_01_sql_injection.py", "name": "sql_injection"},
    {"id": "02", "file": "sample_02_n_plus_one.py", "name": "n_plus_one"},
    {"id": "03", "file": "sample_03_xss_react.jsx", "name": "xss_react"},
    {"id": "04", "file": "sample_04_bad_naming.py", "name": "bad_naming"},
    {"id": "05", "file": "sample_05_mixed_issues.py", "name": "mixed_issues"},
    {"id": "06", "file": "sample_06_clean_code.py", "name": "clean_code"},
    {"id": "07", "file": "sample_07_tricky_false_pos.py", "name": "tricky_false_pos"},
    {"id": "08", "file": "sample_08_async_blocking.py", "name": "async_blocking"},
]


def load_expected(sample_id: str) -> dict:
    path = EVAL_DIR / f"sample_{sample_id}_expected.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_code(filename: str) -> str:
    path = EVAL_DIR / filename
    with open(path, encoding="utf-8") as f:
        return f.read()


def collect_all_issues(result: dict) -> list[dict]:
    """파이프라인 결과에서 모든 Agent의 이슈를 하나의 리스트로 합침."""
    all_issues = []
    for agent_name in ["security", "performance", "quality"]:
        finding = result.get("findings", {}).get(agent_name, {})
        for issue in finding.get("issues", []):
            all_issues.append({
                "type": agent_name,
                "line": issue.get("line", 0),
                "issue": issue.get("issue", ""),
                "severity": issue.get("severity", ""),
            })
    return all_issues


def check_must_find(actual_issues: list[dict], must_find: list[dict]) -> tuple[int, int]:
    """must_find 항목 중 실제 탐지된 수를 반환. (found, total)"""
    found = 0
    for expected in must_find:
        exp_type = expected["type"]
        exp_keyword = expected["keyword"].lower()
        exp_lines = expected.get("line_range", [0, 9999])

        matched = False
        for actual in actual_issues:
            if actual["type"] != exp_type:
                continue
            if exp_keyword in actual["issue"].lower():
                line = actual["line"]
                if exp_lines[0] <= line <= exp_lines[1]:
                    matched = True
                    break
                # 키워드 매치만으로도 허용 (라인은 유동적)
                matched = True
                break

        if matched:
            found += 1

    return found, len(must_find)


def check_false_positives(actual_issues: list[dict], should_not_find: list[dict]) -> int:
    """should_not_find에 해당하는 오탐 수를 반환."""
    fp_count = 0
    for snf in should_not_find:
        snf_type = snf["type"]
        snf_line = snf["line"]

        for actual in actual_issues:
            if actual["type"] == snf_type and actual["line"] == snf_line:
                fp_count += 1
                break

    return fp_count


def check_cross_review(result: dict) -> str:
    """교차 반론이 존재하는지 간단 확인."""
    for agent_name in ["performance", "quality"]:
        finding = result.get("findings", {}).get(agent_name, {})
        cr = finding.get("cross_review", [])
        if cr:
            return "있음"
    return "-"


def run_single(sample: dict, orchestrator: Orchestrator) -> dict:
    """단일 샘플 실행 및 채점."""
    code = load_code(sample["file"])
    expected = load_expected(sample["id"])

    print(f"  실행 중: {sample['name']}...", end=" ", flush=True)

    try:
        result = orchestrator.run(code)
    except Exception as e:
        print(f"에러: {e}")
        return {
            "name": sample["name"],
            "recall": "-",
            "fp": "-",
            "cross_review": "-",
            "error": str(e),
        }

    actual_issues = collect_all_issues(result)

    # 정탐률
    must_find = expected.get("must_find", [])
    if must_find:
        found, total = check_must_find(actual_issues, must_find)
        recall = f"{found}/{total} ({found * 100 // total}%)"
    else:
        recall = "-"

    # 오탐수
    should_not_find = expected.get("should_not_find", [])
    fp = check_false_positives(actual_issues, should_not_find)

    # 교차 반론
    cr = check_cross_review(result)

    print(f"완료 (이슈 {len(actual_issues)}건)")

    # 상세 결과 저장
    result_path = EVAL_DIR / f"sample_{sample['id']}_result.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return {
        "name": sample["name"],
        "recall": recall,
        "fp": fp,
        "cross_review": cr,
    }


def print_table(rows: list[dict]):
    """결과 테이블 출력."""
    header = f"{'샘플':<25} {'정탐률':<15} {'오탐수':<8} {'교차반론':<10}"
    sep = "-" * len(header)

    print(f"\n{sep}")
    print(header)
    print(sep)
    for row in rows:
        print(
            f"{row['name']:<25} {str(row['recall']):<15} "
            f"{str(row['fp']):<8} {row['cross_review']:<10}"
        )
    print(sep)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Eval Set 자동 채점")
    parser.add_argument("--sample", type=str, help="특정 샘플 ID만 실행 (예: 01)")
    args = parser.parse_args()

    config = Config()
    config.validate()
    orchestrator = Orchestrator(config)

    if args.sample:
        samples = [s for s in SAMPLES if s["id"] == args.sample]
        if not samples:
            print(f"샘플 {args.sample}을 찾을 수 없습니다.")
            sys.exit(1)
    else:
        samples = SAMPLES

    print(f"=== Eval Set 채점 시작 ({len(samples)}개 샘플) ===\n")

    results = []
    for sample in samples:
        row = run_single(sample, orchestrator)
        results.append(row)

    print_table(results)
    print("\n각 샘플의 상세 결과: eval_samples/sample_XX_result.json")


if __name__ == "__main__":
    main()
