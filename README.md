# AI Code Review Pipeline

Multi-Agent 코드 리뷰 자동화 시스템

코드를 입력하면 AI Agent 4명이 **보안 → 성능 → 코드 품질 → 종합** 순서로 리뷰하고,
점수와 수정 제안이 포함된 리포트를 생성합니다.

---

## 개발 배경

AI를 활용해 다양한 업무 자동화 프로그램을 개발하는 과정에서, 생성된 코드가 작동은 하지만 아래 문제가 반복 발생:

- **비효율적 코드**: 불필요한 반복, 최적화되지 않은 로직
- **중복 코드**: 같은 기능이 여러 곳에 복사-붙여넣기
- **위험한 코드**: 보안 취약점, 에러 핸들링 누락, 하드코딩된 민감 정보

코드가 "돌아간다"는 것만으로는 충분하지 않으며, 여러 전문가 관점을 AI Agent로 분리하여 빠짐없이, 빠르게, 일관된 기준으로 리뷰합니다.

---

## 시스템 아키텍처

```
사용자 입력 (코드 텍스트 / GitHub PR URL / 파일 업로드)
  → Orchestrator (순서 제어 + 컨텍스트 관리)
    → Agent 1: Security     (보안 취약점 탐지)
    → Agent 2: Performance  (성능 병목 탐지)
    → Agent 3: Code Quality (코드 품질 + 가독성)
    → Agent 4: Summary      (종합 + 점수 + 수정 제안)
  → 결과 출력 (Streamlit UI + Markdown 리포트)
```

### 설계 원칙

| 원칙 | 설명 |
|---|---|
| **순차 실행 + 컨텍스트 누적** | 각 Agent가 이전 Agent의 발견 사항을 함께 받아 교차 분석 |
| **같은 LLM, 다른 페르소나** | Claude API 하나로 시스템 프롬프트만 달리하여 전문가 역할 분리 (모델은 UI에서 선택 가능) |
| **Tool Use 기반 구조화 출력** | tool_use + tool_choice로 JSON 스키마 강제, 파싱 실패율 0 |
| **Agent 간 교차 반론** | 후행 Agent가 선행 Agent 제안에 동의/주의/반대 의견 제시 |

---

## Agent 상세

### Agent 1: Security Agent
보안 취약점 탐지

- SQL Injection, XSS 취약점
- 하드코딩된 비밀번호/API 키
- 안전하지 않은 API 사용 (eval, exec, pickle.loads 등)
- 인증/권한 체크 누락
- 의존성 보안

### Agent 2: Performance Agent
성능 병목 탐지 + Security 결과 교차 검토

- N+1 쿼리 패턴
- 불필요한 중첩 루프 (O(n^2) 이상)
- 메모리 누수 가능성
- 블로킹 호출, 캐시 미활용
- 보안 수정이 성능에 미치는 영향 분석

### Agent 3: Code Quality Agent
코드 품질 + 가독성 + 이전 결과 교차 검토

- 네이밍 컨벤션, 함수 길이/복잡도
- DRY 위반 (중복 코드)
- 타입 힌트 누락, 에러 핸들링 누락
- 매직 넘버, 주석/문서화 부족

### Agent 4: Summary Agent
전체 종합 + 최종 판정

- 중복 이슈 제거 및 병합
- 교차 반론 충돌 시 최종 판단
- 100점 만점 점수 산정 (critical -15, warning -5, info -1)
- 수정 우선순위 Top 3 선정

---

## 입력 방식

| 방식 | 설명 | 상태 |
|---|---|---|
| 코드 직접 입력 | Streamlit 텍스트 영역에 붙여넣기 | MVP |
| GitHub PR URL | GitHub API로 PR diff 가져와 리뷰 | 확장 |
| 파일 업로드 | .py, .js, .jsx, .ts, .tsx, .java, .go 파일 직접 업로드 | 확장 |

---

## 출력 형식

### Streamlit 웹 UI
- **Overview 탭**: 전체 점수, 등급, Top 3 수정 사항
- **Security 탭**: 보안 이슈 상세
- **Performance 탭**: 성능 이슈 상세
- **Quality 탭**: 코드 품질 이슈 상세
- **하단**: Agent 실행 과정 실시간 표시

### Markdown 리포트
- 다운로드 가능한 .md 파일
- GitHub / Notion에 바로 활용 가능

---

## 기술 스택

| 역할 | 도구 | 이유 |
|---|---|---|
| Agent LLM | Claude API (Sonnet/Haiku/Opus 선택 가능) | API에서 최신 모델 자동 조회 |
| 오케스트레이터 | 순수 Python 클래스 | 의존성 최소, 직관적 |
| 웹 UI | Streamlit | 빠른 프로토타이핑 |
| 코드 입력 | GitHub API (확장) | PR 연동 |
| 출력 | Markdown + Streamlit | 이중 출력 |

---

## 프로젝트 구조

```
code-review-pipeline/
├── app.py                          # Streamlit 웹 UI
├── requirements.txt
├── .env.example
├── src/
│   ├── __init__.py
│   ├── orchestrator.py             # 파이프라인 제어 (Agent 순차 호출)
│   ├── review_state.py             # 상태 관리 + 언어 자동 감지
│   ├── config.py                   # 설정 관리 (API 키, 모델명 등)
│   ├── github_client.py            # GitHub PR 연동 (diff 추출)
│   └── agents/
│       ├── __init__.py
│       ├── base_agent.py           # Agent 베이스 클래스 (Claude API + Tool Use)
│       ├── security.py             # Agent 1: 보안 취약점 탐지
│       ├── performance.py          # Agent 2: 성능 병목 탐지
│       ├── quality.py              # Agent 3: 코드 품질/가독성
│       └── summary.py              # Agent 4: 종합 판정 + 점수 산정
├── prompts/
│   ├── security.txt
│   ├── performance.txt
│   ├── quality.txt
│   └── summary.txt
├── eval_samples/                   # Eval Set (Phase 5)
│   ├── run_eval.py
│   ├── sample_01~08_*.py|jsx
│   ├── sample_01~08_expected.json
│   └── sample_cross_review_conflict.py
└── Phase/                          # Phase별 상세 개발 문서
    ├── Phase1_프로젝트구조_오케스트레이터.md
    ├── Phase2_Agent구현.md
    ├── Phase3_교차반론.md
    ├── Phase4_StreamlitUI.md
    ├── Phase5_EvalSet.md
    └── Phase6_GitHub연동.md
```

---

## 평가/검증 (Eval Set)

의도적으로 문제를 심어둔 샘플 코드 8~10개 + 정답지로 시스템 성능을 정량 측정합니다.

```
eval_samples/
├── sample_01_sql_injection.py      # SQL Injection + 하드코딩 비번
├── sample_01_expected.json
├── sample_02_n_plus_one.py         # N+1 쿼리
├── sample_02_expected.json
├── sample_03_xss_react.jsx         # XSS 취약점
├── sample_03_expected.json
├── sample_04_bad_naming.py         # 네이밍 + 매직 넘버
├── sample_04_expected.json
├── sample_05_mixed_issues.py       # 보안+성능+품질 복합
├── sample_05_expected.json
├── sample_06_clean_code.py         # 오탐 테스트 (문제 없는 코드)
├── sample_06_expected.json
├── sample_07_tricky_false_pos.py   # 오탐하면 안 되는 코드
├── sample_07_expected.json
├── sample_08_async_blocking.py     # async 내 동기 I/O
├── sample_08_expected.json
├── sample_cross_review_conflict.py # 교차 반론 충돌 테스트
└── run_eval.py                     # 자동 채점 스크립트
```

### 측정 지표

| 지표 | 설명 | 목표 |
|---|---|---|
| 정탐률 (Recall) | 심어둔 이슈 중 실제 탐지 비율 | 80% 이상 |
| 오탐률 (FP Rate) | 없는 문제를 있다고 한 건수 | 샘플당 평균 1건 이하 |
| 교차 반론 유효율 | cross_review 의견의 타당성 | 수동 확인 |

---

## 대상 사용자

- **개발자**: PR 올리기 전 셀프 리뷰
- **팀 리드**: 리뷰 기준 일관성 확보
- **주니어 개발자**: 코드 품질 학습 도구

---

## 개발 현황

| Phase | 내용 | 상태 | 문서 |
|---|---|---|---|
| Phase 1 | 프로젝트 구조 설계 + Orchestrator 기본 구현 | ✅ 완료 | [상세](Phase/Phase1_프로젝트구조_오케스트레이터.md) |
| Phase 2 | Agent 4종 구현 (Security/Performance/Quality/Summary) | ✅ 완료 | [상세](Phase/Phase2_Agent구현.md) |
| Phase 3 | 교차 반론(Cross-Review) 로직 구현 | ✅ 완료 | [상세](Phase/Phase3_교차반론.md) |
| Phase 4 | Streamlit UI 구현 | ✅ 완료 | [상세](Phase/Phase4_StreamlitUI.md) |
| Phase 5 | Eval Set 구성 + 자동 채점 | ✅ 완료 | [상세](Phase/Phase5_EvalSet.md) |
| Phase 6 | GitHub PR 연동 (확장) | ✅ 완료 | [상세](Phase/Phase6_GitHub연동.md) |
