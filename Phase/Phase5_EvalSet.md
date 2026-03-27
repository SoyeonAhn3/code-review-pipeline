# Phase 5 — Eval Set 구성 + 자동 채점 `✅ 완료`

> 의도적으로 문제를 심어둔 샘플 코드와 자동 채점 시스템으로 파이프라인 성능을 정량 측정한다.

**완료일**: 2026-03-26
**상태**: ✅ 완료
**선행 조건**: Phase 4 완료 (전체 파이프라인 + UI 동작)

---

## 개요

시스템이 실제로 문제를 잘 잡는지 숫자로 증명하는 검증 체계를 구축한다.
8~10개 샘플 코드에 의도적 문제를 심어두고, 정답지(expected.json)와 비교하여
정탐률/오탐률을 자동 측정한다. 이 과정 자체가 포트폴리오 어필 포인트이다.

---

## 완료 예정 항목

| # | 모듈 / 작업 | 상태 | 설명 |
|---|---|---|---|
| 1 | 샘플 코드 8개 작성 | ✅ | 보안/성능/품질별 의도적 결함 포함 |
| 2 | 정답지 8개 작성 (expected.json) | ✅ | must_find + should_not_find |
| 3 | `run_eval.py` — 자동 채점 스크립트 | ✅ | 전체 샘플 실행 + 결과 비교 + 테이블 출력 |
| 4 | 프롬프트 튜닝 사이클 실행 | ✅ | v1 → v2 → v3 정탐률 개선 기록 |
| 5 | Eval 결과 리포트 작성 | ✅ | 최종 성능 지표 정리 |

---

## Eval 샘플 구성

| 샘플 | 파일명 | 심어둔 결함 | 검증 목적 |
|---|---|---|---|
| 01 | `sample_01_sql_injection.py` | SQL Injection + 하드코딩 비번 | Security 기본 탐지 |
| 02 | `sample_02_n_plus_one.py` | N+1 쿼리 + 불필요한 전체 로딩 | Performance 기본 탐지 |
| 03 | `sample_03_xss_react.jsx` | dangerouslySetInnerHTML + innerHTML | JS 보안 탐지 |
| 04 | `sample_04_bad_naming.py` | 변수명 a,b,c + 매직 넘버 + 긴 함수 | Quality 기본 탐지 |
| 05 | `sample_05_mixed_issues.py` | 보안+성능+품질 복합 | 다관점 교차 분석 |
| 06 | `sample_06_clean_code.py` | 문제 없는 깨끗한 코드 | 오탐 테스트 (false positive) |
| 07 | `sample_07_tricky_false_pos.py` | 테스트 코드의 하드코딩 값 | 오탐하면 안 됨 |
| 08 | `sample_08_async_blocking.py` | async 안에서 동기 I/O | Performance 비동기 탐지 |

---

## 정답지 형식 (expected.json)

```json
{
  "must_find": [
    { "type": "security", "keyword": "sql injection", "line": 2 },
    { "type": "security", "keyword": "hardcoded password", "line": 9 },
    { "type": "performance", "keyword": "n+1", "line": 5 }
  ],
  "should_not_find": [
    { "type": "security", "line": 7, "reason": "정상 코드인데 오탐하면 안 됨" }
  ]
}
```

---

## 자동 채점 로직 (run_eval.py)

```python
def run_eval():
    """전체 eval 샘플을 파이프라인에 실행하고 채점"""
    results = []
    for sample in eval_samples:
        # 1. 파이프라인 실행
        actual = pipeline.run(sample.code)
        # 2. must_find 체크 → 정탐률
        recall = check_must_find(actual, sample.expected)
        # 3. should_not_find 체크 → 오탐수
        fp_count = check_false_positives(actual, sample.expected)
        # 4. cross_review 유효성 (수동 확인 플래그)
        results.append({"sample": sample.name, "recall": recall, "fp": fp_count})
    print_result_table(results)
```

### 결과 출력 예시
```
┌──────────────────────┬────────┬────────┬──────────┐
│ 샘플                 │ 정탐률 │ 오탐수 │ 교차반론 │
├──────────────────────┼────────┼────────┼──────────┤
│ sql_injection        │ 100%   │ 0      │ -        │
│ n_plus_one           │ 100%   │ 1      │ 유효     │
│ xss_react            │ 100%   │ 0      │ -        │
│ bad_naming           │ 75%    │ 0      │ -        │
│ mixed_issues         │ 80%    │ 1      │ 유효     │
│ clean_code           │ -      │ 0      │ -        │
│ tricky_false_pos     │ -      │ 0      │ -        │
│ async_blocking       │ 100%   │ 0      │ 유효     │
├──────────────────────┼────────┼────────┼──────────┤
│ 전체 평균            │ 87.5%  │ 0.5건  │ 80%      │
└──────────────────────┴────────┴────────┴──────────┘
```

---

## 측정 지표

| 지표 | 설명 | 목표 |
|---|---|---|
| 정탐률 (Recall) | must_find 항목 중 실제 탐지 비율 | 80% 이상 |
| 오탐률 (FP Rate) | should_not_find에 걸린 건수 | 샘플당 평균 1건 이하 |
| 교차 반론 유효율 | cross_review 의견이 타당한 비율 | 수동 확인 |

---

## 프롬프트 튜닝 사이클

```
프롬프트 v1 → Eval 실행 → 정탐 75%
    ↓ (약점 분석 + 프롬프트 수정)
프롬프트 v2 → Eval 실행 → 정탐 87%
    ↓ (오탐 패턴 분석 + confidence 조정)
프롬프트 v3 → Eval 실행 → 정탐 92%
```

각 버전의 변경 내용과 결과를 기록하여 개선 과정을 문서화한다.

---

## 선행 조건 및 의존성

- Phase 4까지 전체 파이프라인 동작 확인
- 샘플 코드는 Python + JavaScript 두 언어 포함

---

## 개발 시 주의사항

- 샘플 코드는 실제 프로젝트에서 발생할 법한 현실적인 패턴으로 작성
- clean_code 샘플은 진짜 문제가 없어야 함 (오탐 테스트 목적)
- Eval 실행마다 API 비용 발생 → 불필요한 반복 실행 주의
- 프롬프트 버전 관리: `prompts/v1/`, `prompts/v2/` 등으로 보관

---

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-03-25 | 최초 작성 |
| 2026-03-27 | 전체 항목 완료 상태 반영 |
