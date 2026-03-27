# Phase 3 — 교차 반론(Cross-Review) 로직 구현 `✅ 완료`

> Agent 간 교차 반론 메커니즘을 구현하여 리뷰 품질을 한 단계 높인다.

**완료일**: 2026-03-26
**상태**: ✅ 완료
**선행 조건**: Phase 2 완료 (Agent 4종 기본 동작)

---

## 개요

단순히 Agent가 순서대로 결과를 전달하는 것을 넘어,
후행 Agent가 선행 Agent의 제안에 대해 동의/주의/반대 의견을 제시하는 교차 반론 메커니즘을 구현한다.
이를 통해 "보안 수정이 성능을 해치는 경우"와 같은 트레이드오프를 자동으로 감지한다.

---

## 완료 예정 항목

| # | 모듈 / 작업 | 상태 | 설명 |
|---|---|---|---|
| 1 | cross_review 스키마 추가 | ✅ | Performance, Quality Agent Tool 스키마에 cross_review 필드 추가 |
| 2 | 교차 반론 프롬프트 강화 | ✅ | 이전 Agent 제안을 검토하고 의견을 제시하도록 지시 |
| 3 | Summary Agent 충돌 해소 로직 | ✅ | caution/disagree 의견 시 최종 판단 도출 |
| 4 | 충돌 이슈 태깅 | ✅ | "보안+성능 트레이드오프" 등 복합 이슈 태깅 |
| 5 | 교차 반론 테스트 케이스 | ✅ | 의도적 충돌 샘플로 검증 |

---

## cross_review 스키마

### Performance/Quality Agent에 추가되는 필드
```json
"cross_review": [
  {
    "target_agent": "security",
    "target_issue": "line 42: 입력값 검증 추가 제안",
    "opinion": "agree | caution | disagree",
    "comment": "루프 내 반복 실행 시 성능 저하 우려. 루프 밖에서 1회 검증 권장"
  }
]
```

### opinion 판정 기준

| opinion | 의미 | 예시 |
|---|---|---|
| **agree** | 이전 Agent의 제안에 동의, 내 관점에서도 문제 없음 | Security가 파라미터 바인딩 권고 → Performance도 동의 |
| **caution** | 동의하나 내 관점에서 주의 필요 | 보안 검증 추가 자체는 맞지만, 루프 안에서 매번 실행하면 성능 저하 |
| **disagree** | 내 관점에서 해당 제안이 오히려 문제를 일으킴 | 캐시 추가 제안이 데이터 일관성(보안)을 해칠 수 있음 |

---

## 교차 반론 흐름

```
Security Agent → 이슈 3건 발견
    ↓ (결과 전달)
Performance Agent
    → 자체 이슈 2건 발견
    → Security 이슈 3건에 대해 cross_review 작성
        - 이슈1: agree
        - 이슈2: caution ("루프 내 실행 시 성능 저하")
        - 이슈3: agree
    ↓ (결과 전달)
Quality Agent
    → 자체 이슈 4건 발견
    → Security 이슈 3건 + Performance 이슈 2건에 대해 cross_review 작성
    ↓ (전체 전달)
Summary Agent
    → caution/disagree 건을 추출
    → 양쪽 근거 비교 후 최종 resolution 도출
    → cross_review_conflicts 필드에 정리
```

---

## Summary Agent 충돌 해소

### cross_review_conflicts 출력 형식
```json
"cross_review_conflicts": [
  {
    "issue": "line 80: 입력값 검증 추가 (Security 제안)",
    "conflict": "Performance Agent가 루프 내 반복 실행 시 성능 저하 경고",
    "resolution": "루프 밖에서 1회만 검증하도록 수정 권장"
  }
]
```

### 해소 원칙
1. **보안 > 성능 > 가독성** 우선순위 원칙 (단, 성능 영향이 극심하면 대안 제시)
2. disagree 건은 반드시 resolution에 구체적 대안 포함
3. 복합 이슈로 태깅하여 사용자가 트레이드오프를 인지하도록 함

---

## 선행 조건 및 의존성

- Phase 2의 4개 Agent가 기본 동작 (cross_review 없이)
- Tool 스키마 확장이 기존 출력과 호환되어야 함

---

## 개발 시 주의사항

- cross_review는 선택적 필드 — 이전 Agent 결과가 없으면 빈 배열
- Agent 1(Security)은 선행 결과가 없으므로 cross_review 필드 없음
- 교차 반론이 지나치게 많으면 노이즈 → "주요 제안에 대해서만 검토" 지시
- 테스트 시 의도적으로 보안↔성능 충돌이 나는 샘플 코드 필요

---

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-03-25 | 최초 작성 |
| 2026-03-27 | 전체 항목 완료 상태 반영 |
