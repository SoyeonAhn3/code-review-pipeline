# Phase 2 — Agent 4종 구현 `✅ 완료`

> Security, Performance, Code Quality, Summary 4개 Agent의 프롬프트와 Tool 스키마를 구현한다.

**완료일**: 2026-03-26
**상태**: ✅ 완료
**선행 조건**: Phase 1 완료 (Orchestrator + BaseAgent)

---

## 개요

파이프라인의 핵심인 4개 전문가 Agent를 구현한다.
각 Agent는 고유한 시스템 프롬프트와 Tool Use 스키마를 가지며,
Claude API를 통해 코드를 분석하고 구조화된 JSON 결과를 반환한다.

---

## 완료 예정 항목

| # | 모듈 / 작업 | 상태 | 설명 |
|---|---|---|---|
| 1 | `security.py` + 프롬프트 | ✅ | 보안 취약점 탐지 Agent |
| 2 | `performance.py` + 프롬프트 | ✅ | 성능 병목 탐지 Agent |
| 3 | `quality.py` + 프롬프트 | ✅ | 코드 품질/가독성 Agent |
| 4 | `summary.py` + 프롬프트 | ✅ | 종합 판정 + 점수 산정 Agent |
| 5 | Tool 스키마 정의 (4종) | ✅ | tool_use용 JSON Schema |
| 6 | Agent 단위 테스트 | ✅ | 각 Agent 독립 실행 검증 |

---

## Agent 1: Security Agent

### 목적
보안 취약점을 탐지하고 severity/confidence와 함께 수정 제안을 제공한다.

### 구현 파일
- `src/agents/security.py`
- `prompts/security.txt`

### 확인 항목
- SQL Injection (문자열 결합으로 쿼리 생성)
- XSS 취약점 (사용자 입력을 필터 없이 렌더링)
- 하드코딩된 비밀번호/API 키
- 안전하지 않은 API 사용 (eval, exec, pickle.loads 등)
- 인증/권한 체크 누락
- 의존성 보안 (알려진 취약 버전)

### Tool 스키마 (설계)
```json
{
  "name": "report_security_issues",
  "description": "보안 분석 결과를 구조화된 형식으로 보고",
  "input_schema": {
    "type": "object",
    "properties": {
      "agent": { "type": "string", "enum": ["security"] },
      "issues": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "severity": { "enum": ["critical", "warning", "info"] },
            "confidence": { "enum": ["high", "medium", "low"] },
            "line": { "type": "integer" },
            "code_snippet": { "type": "string" },
            "issue": { "type": "string" },
            "suggestion": { "type": "string" }
          },
          "required": ["severity", "confidence", "line", "issue", "suggestion"]
        }
      },
      "summary": { "type": "string" }
    },
    "required": ["agent", "issues", "summary"]
  }
}
```

---

## Agent 2: Performance Agent

### 목적
성능 병목을 탐지하고, Security Agent의 수정 제안이 성능에 미치는 영향을 교차 분석한다.

### 구현 파일
- `src/agents/performance.py`
- `prompts/performance.txt`

### 확인 항목
- N+1 쿼리 패턴 (루프 안에서 DB 호출)
- 불필요한 중첩 루프 (O(n^2) 이상)
- 메모리 누수 가능성 (큰 리스트를 계속 append)
- 블로킹 호출 (동기 I/O in async 코드)
- 캐시 미활용
- 불필요한 데이터 로딩 (전체 조회 후 필터)

### 입력
코드 원본 + Security Agent 결과

---

## Agent 3: Code Quality Agent

### 목적
코드 품질과 가독성을 분석하고, 이전 Agent가 지적한 항목은 중복 지적하지 않는다.

### 구현 파일
- `src/agents/quality.py`
- `prompts/quality.txt`

### 확인 항목
- 네이밍 컨벤션 (변수명, 함수명)
- 함수 길이 / 복잡도 (Cyclomatic Complexity 추정)
- DRY 위반 (중복 코드)
- 타입 힌트 누락 (Python)
- 에러 핸들링 누락 (bare except, 빈 catch)
- 주석/문서화 부족
- 매직 넘버 사용

### 입력
코드 원본 + Security 결과 + Performance 결과

---

## Agent 4: Summary Agent

### 목적
3개 Agent 결과를 종합하여 중복 제거, 점수 산정, 수정 우선순위를 결정한다.

### 구현 파일
- `src/agents/summary.py`
- `prompts/summary.txt`

### 처리 로직
1. 중복 이슈 제거 (같은 라인 + 유사 키워드 → 병합)
2. 교차 반론 충돌 시 양쪽 근거 비교 후 최종 판단
3. 점수 산정: 100점 만점 (critical -15, warning -5, info -1)
4. 수정 우선순위 Top 3 선정 (impact x effort)
5. 종합 코멘트 생성

### Tool 스키마 출력 (설계)
```json
{
  "overall_score": 72,
  "grade": "C+",
  "total_issues": { "critical": 1, "warning": 3, "info": 5 },
  "top_3_actions": [
    { "priority": 1, "issue": "...", "effort": "5분" }
  ],
  "cross_review_conflicts": [...],
  "comment": "...",
  "all_issues": [...]
}
```

---

## 프롬프트 설계 원칙

| 원칙 | 설명 |
|---|---|
| 역할 명시 | "당신은 10년 경력의 보안 전문가입니다" 형태의 페르소나 부여 |
| 언어별 체크리스트 | Python: pickle/eval, JS: innerHTML/dangerouslySetInnerHTML |
| 이전 결과 참조 지시 | "이전 Agent가 지적한 이슈는 건너뛰세요" |
| confidence 강제 | "확실하지 않으면 confidence: low로 표시하세요" |
| 교차 반론 지시 | "이전 Agent의 수정 제안이 당신의 관점에서 문제가 없는지 검토하세요" |

---

## 선행 조건 및 의존성

- Phase 1 Orchestrator, BaseAgent, ReviewState 완료
- Claude API 키 설정 완료
- anthropic SDK 설치

---

## 개발 시 주의사항

- 각 Agent는 독립적으로 테스트 가능해야 함
- 프롬프트는 별도 .txt 파일로 관리 (코드와 분리)
- Tool 스키마 변경 시 Summary Agent의 파싱 로직도 함께 수정
- MVP: Python, JavaScript/TypeScript만 공식 지원

---

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-03-25 | 최초 작성 |
| 2026-03-27 | 전체 항목 완료 상태 반영 |
