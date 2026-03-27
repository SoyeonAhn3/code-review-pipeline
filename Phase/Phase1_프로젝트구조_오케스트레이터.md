# Phase 1 — 프로젝트 구조 설계 + Orchestrator 기본 구현 `✅ 완료`

> 프로젝트 디렉토리 구조를 확정하고, Agent 순차 실행을 제어하는 Orchestrator를 구현한다.

**완료일**: 2026-03-26
**상태**: ✅ 완료
**선행 조건**: 없음 (최초 Phase)

---

## 개요

전체 파이프라인의 뼈대를 잡는 단계이다.
디렉토리 구조, 설정 파일, Orchestrator 클래스를 구현하여
Agent 4개를 순차적으로 호출하고 컨텍스트를 누적 전달하는 기반을 만든다.

---

## 완료 예정 항목

| # | 모듈 / 작업 | 상태 | 설명 |
|---|---|---|---|
| 1 | 프로젝트 디렉토리 구조 확정 | ✅ | src/, agents/, config/, eval_samples/ 등 |
| 2 | `config.py` — 설정 관리 | ✅ | API 키, 모델명, 토큰 제한 등 환경변수 관리 |
| 3 | `orchestrator.py` — 파이프라인 제어 | ✅ | Agent 순차 호출 + 컨텍스트 누적 + 에러 핸들링 |
| 4 | `review_state.py` — 상태 관리 | ✅ | review_state dict 구조 정의 + 언어 자동 감지 |
| 5 | `base_agent.py` — Agent 베이스 클래스 | ✅ | Claude API 호출 공통 로직 + Tool Use 처리 |
| 6 | `requirements.txt` 작성 | ✅ | anthropic, streamlit 등 의존성 정리 |

---

## 모듈 상세

### orchestrator.py

#### 목적
Agent 4개를 Security → Performance → Quality → Summary 순서로 호출하고,
이전 Agent의 결과를 다음 Agent의 프롬프트에 포함하여 컨텍스트를 누적한다.

#### 핵심 구조 (설계)
```python
class Orchestrator:
    def __init__(self, config):
        self.agents = [SecurityAgent, PerformanceAgent, QualityAgent, SummaryAgent]
        self.state = ReviewState()

    def run(self, code: str, language: str = None) -> dict:
        """전체 파이프라인 실행"""
        self.state.set_code(code, language)
        for agent_cls in self.agents:
            agent = agent_cls(self.config)
            try:
                result = agent.analyze(self.state)
                self.state.add_finding(agent.name, result)
            except Exception as e:
                self.state.add_error(agent.name, str(e))
        return self.state.get_summary()
```

#### 설계 결정 사항
| 결정 | 이유 |
|---|---|
| 순수 Python 클래스로 구현 | LangGraph 등 프레임워크 의존성 없이 직관적으로 시작 |
| Agent 스킵 정책 | 하나가 실패해도 나머지 Agent는 계속 실행 |
| 언어 자동 감지 + confidence 점수 | 코드 문법 패턴으로 감지, confidence가 낮으면 사용자에게 직접 선택 권장 |
| 코드 최대 700줄 제한 | API 토큰 한도 고려, 초과 시 구체적 해결 방법 안내 |
| 모델 자동 조회 | Anthropic API에서 최신 모델을 자동으로 가져옴 (하드코딩 제거) |

---

### review_state.py

#### 목적
파이프라인 실행 중 코드와 각 Agent 결과를 보관하는 상태 객체.

#### 핵심 구조 (설계)
```python
review_state = {
    "code": "...(원본 코드)...",
    "language": "python",
    "language_confidence": 0.85,   # 언어 감지 확신도 (0.0~1.0)
    "findings": {
        "security": {...},
        "performance": {...},
        "quality": {...},
        "summary": {...}
    },
    "errors": []
}
```

#### 언어 자동 감지 + confidence 점수
- 코드 내 문법 패턴(def, import, function, const 등)의 매칭 횟수로 언어 감지
- 1등과 2등 점수 차이의 비율로 confidence 산출 (0.0 ~ 1.0)
- confidence < 0.4이면 UI에서 "직접 선택을 권장합니다" 경고 표시
- "unknown"이면 감지 불가 안내 후 진행 차단

---

### base_agent.py

#### 목적
모든 Agent가 상속하는 베이스 클래스. Claude API 호출, Tool Use 응답 파싱 공통 로직.

#### 핵심 구조 (설계)
```python
class BaseAgent:
    name: str
    system_prompt: str
    tool_schema: dict

    def analyze(self, state: ReviewState) -> dict:
        """Claude API 호출 + tool_use 응답에서 결과 추출"""
        response = self.client.messages.create(
            model=self.config.model,
            system=self.system_prompt,
            messages=[{"role": "user", "content": self._build_prompt(state)}],
            tools=[self.tool_schema],
            tool_choice={"type": "tool", "name": self.tool_name}
        )
        return response.content[0].input
```

---

## 프로젝트 디렉토리 구조 (목표)

```
code-review-pipeline/
├── src/
│   ├── __init__.py
│   ├── orchestrator.py       # 파이프라인 제어
│   ├── review_state.py       # 상태 관리
│   ├── config.py             # 설정 관리
│   └── agents/
│       ├── __init__.py
│       ├── base_agent.py     # Agent 베이스 클래스
│       ├── security.py       # Phase 2
│       ├── performance.py    # Phase 2
│       ├── quality.py        # Phase 2
│       └── summary.py        # Phase 2
├── prompts/                  # Agent별 시스템 프롬프트
│   ├── security.txt
│   ├── performance.txt
│   ├── quality.txt
│   └── summary.txt
├── eval_samples/             # Phase 5
├── app.py                    # Phase 4 (Streamlit)
├── requirements.txt
├── .env.example
└── README.md
```

---

## 선행 조건 및 의존성

- Python 3.10+
- `anthropic` SDK 설치
- Claude API 키 발급

---

## 개발 시 주의사항

- `.env` 파일에 API 키 저장, `.gitignore`에 반드시 추가
- Orchestrator는 Agent 추가/제거가 쉽도록 리스트 기반 설계
- 코드 최대 700줄 제한 (초과 시 줄이거나 PR 입력 안내)

---

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-03-25 | 최초 작성 |
| 2026-03-27 | 전체 항목 완료 상태 반영 |
| 2026-03-27 | config.py 모델 자동 조회 추가, review_state.py 언어 감지 confidence 추가, 코드 제한 500→700줄 변경 |
