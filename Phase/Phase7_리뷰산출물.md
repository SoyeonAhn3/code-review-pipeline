# Phase 7 — 리뷰 산출물 포맷 (Review Deliverable) `🔧 진행 중`

> 파이프라인 분석 결과를 포트폴리오 + 코드 수정 가이드로 활용할 수 있는 정제된 산출물을 생성하는 Skill을 구현한다.

**상태**: 🔧 진행 중
**선행 조건**: Phase 6 완료 (전체 파이프라인 동작)

---

## 개요

현재 파이프라인은 `_full_review.txt`(원본)과 `_personal_review.md`(정제 리포트)를 출력한다.
하지만 이 결과물은 **배치별 정리** 구조라 실제 코드 수정 시 같은 유형의 이슈가 흩어져 있고,
포트폴리오 산출물로 보여주기에는 가공이 필요하다.

Phase 7에서는:
- 리뷰 결과를 **유형별**(보안/성능/품질)로 재구성한 산출물 포맷을 정의
- Critical 이슈에 **Before/After**(구조 수준 설명)를 포함
- Skill(`/review-deliverable`)로 사용자 요청 시에만 생성

---

## 완료 예정 항목

| # | 작업 | 상태 | 설명 |
|---|------|------|------|
| 1 | 산출물 템플릿 구조 확정 | ✅ | 5-Section 구조 합의 완료 |
| 2 | `/review-deliverable` Skill 구현 | ✅ | SKILL.md + references/report-template.md 구현 완료 |
| 3 | 샘플 산출물 생성 (stock-analyzer) | ✅ | `output/stock-analyzer_review_report.md` 생성 완료 |
| 4 | 리뷰 완료 후 산출물 생성 여부 질문 플로우 | ⬜ | 리뷰 끝나면 사용자에게 "산출물 만들까요?" 질문 |

---

## 산출물 구조

파일명: `output/{프로젝트명}_review_report.md`

### Section 1. Overview

프로젝트 기본 정보 + 전체 점수/등급을 한눈에 보여주는 요약 테이블.

| 항목 | 내용 |
|------|------|
| 프로젝트 | {프로젝트명} |
| 분석 일자 | YYYY-MM-DD |
| 리뷰 레벨 | Production / Personal |
| 분석 도구 | 4-Agent Code Review Pipeline |
| 분석 범위 | N개 파일, ~N,000줄 |
| 전체 점수 | XX / 100 (등급) |

### Section 2. Issue Dashboard

이슈 현황을 3가지 관점으로 요약.

- **심각도별 건수**: Critical / Warning / Info
- **카테고리별 분포**: 보안·성능·코드 품질 × 심각도 매트릭스
- **배치별 점수**: 분석 범위별 점수/등급 테이블

### Section 3. Critical Issues (상세)

Critical 이슈 1건당 아래 블록 반복:

```
#### Critical #N — {이슈 제목}

| 항목 | 내용 |
|------|------|
| 위치 | 파일명.py LN |
| 유형 | 보안 / 성능 / 품질 |
| 난이도 | 상 / 중 / 하 |
| 현재 구조 | (현재 코드가 어떻게 짜여 있는지 구조 수준 설명) |
| 개선 방향 | (어떻게 바꾸어야 하는지 구조 수준 설명) |
| 영향 | (미수정 시 발생 가능한 문제) |
```

- 코드 스니펫이 아닌 **구조/패턴 수준의 Before/After** 기술
- 난이도(상/중/하)를 각 이슈에 개별 표기

### Section 4. Warning Issues (요약)

유형별 테이블로 정리. Before/After 없이 이슈 + 개선 방향 1줄.

- 4.1 보안 관련 Warning (N건)
- 4.2 성능 관련 Warning (N건)
- 4.3 코드 품질 관련 Warning (N건)

각 테이블 컬럼: `#`, `파일`, `Line`, `이슈`, `개선 방향`

### Section 5. Methodology (간략)

- 4-Agent 구조 1줄 설명 (Security → Performance → Quality → Summary)
- 점수 산출 공식
- 등급 기준
- 심각도 기준 (Critical/Warning/Info 각 1줄)

---

## 기존 output과의 관계

| 파일 | 성격 | 생성 시점 |
|------|------|----------|
| `_full_review.txt` | 원본 데이터 (Agent별 raw output) | 파이프라인 실행 시 자동 |
| `_personal_review.md` | 정제 리포트 (배치별 정리) | 파이프라인 실행 시 자동 |
| `_review_report.md` | **포트폴리오 산출물 (유형별 정리)** | **사용자 요청 시 Skill로 생성** |

---

## Skill 동작 방식

- 트리거: `/review-deliverable` 또는 리뷰 후 "산출물 만들어줘"
- 사용자에게 대상 리뷰 파일을 지정받음 (자동 탐색하지 않음)
- 확정된 템플릿 구조에 맞춰 산출물 생성
- `output/{프로젝트명}_review_report.md`로 저장

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-24 | 최초 작성, 산출물 구조 합의 완료 |
| 2026-04-24 | Skill 구현 완료 (SKILL.md + report-template.md) |
| 2026-04-24 | 샘플 산출물 생성 완료 (stock-analyzer_review_report.md) |
