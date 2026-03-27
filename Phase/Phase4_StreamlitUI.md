# Phase 4 — Streamlit UI 구현 `✅ 완료`

> 코드 입력부터 리뷰 결과 확인까지 가능한 웹 인터페이스를 구현한다.

**완료일**: 2026-03-26
**상태**: ✅ 완료
**선행 조건**: Phase 3 완료 (파이프라인 전체 동작)

---

## 개요

Streamlit 기반 웹 UI를 구현하여 사용자가 코드를 입력하고,
Agent별 리뷰 결과를 탭으로 구분하여 확인하며,
Markdown 리포트를 다운로드할 수 있도록 한다.

---

## 완료 예정 항목

| # | 모듈 / 작업 | 상태 | 설명 |
|---|---|---|---|
| 1 | `app.py` — 메인 Streamlit 앱 | ✅ | 전체 UI 레이아웃 구성 |
| 2 | 코드 입력 영역 | ✅ | 텍스트 입력 + 언어 선택 |
| 3 | Agent 실행 상태 표시 | ✅ | 진행 중/완료 상태 실시간 표시 |
| 4 | 결과 탭 UI (Overview/Security/Performance/Quality) | ✅ | 탭별 이슈 테이블 렌더링 |
| 5 | 점수 시각화 | ✅ | 전체 점수, 등급, 이슈 통계 |
| 6 | Markdown 리포트 다운로드 | ✅ | .md 파일 생성 + 다운로드 버튼 |
| 7 | 교차 반론 충돌 섹션 | ✅ | 트레이드오프 이슈 강조 표시 |
| 8 | 모델 선택 드롭다운 | ✅ | Anthropic API에서 최신 모델 자동 조회 + 사용자 선택 |
| 9 | 언어 감지 confidence 경고 | ✅ | 자동 감지 불확실 시 사용자에게 직접 선택 권장 |

---

## UI 레이아웃 (설계)

```
┌─────────────────────────────────────────────────────┐
│  AI Code Review Pipeline                            │
├──────────────────────┬──────────────────────────────┤
│  모델: [Sonnet ▼]    │  [Overview] [Security]       │
│                      │  [Performance] [Quality]     │
│  입력: ○직접 ○PR ○파일│                              │
│                      │  ┌──────────────────────┐    │
│  코드 입력 영역       │  │ 전체 점수: 72/100    │    │
│  (st.text_area)      │  │ 등급: C+             │    │
│                      │  │ Critical: 1건        │    │
│  언어: [Python ▼]    │  │ Warning: 3건         │    │
│                      │  │ Info: 5건            │    │
│  [🔍 리뷰 시작]      │  └──────────────────────┘    │
│                      │                              │
│                      │  Top 3 수정 사항             │
│                      │  1. SQL Injection (5분)      │
│                      │  2. N+1 Query (30분)         │
│                      │  3. Error Handling (15분)     │
├──────────────────────┴──────────────────────────────┤
│  Agent 실행 상태                                     │
│  ✅ Security → ✅ Performance → 🔄 Quality → ⬜ Summary │
├─────────────────────────────────────────────────────┤
│  [📥 Markdown 리포트 다운로드]                       │
└─────────────────────────────────────────────────────┘
```

---

## 주요 컴포넌트

### 코드 입력 영역 (좌측)
```python
code = st.text_area("리뷰할 코드를 붙여넣으세요", height=500)
language = st.selectbox("언어", ["자동 감지", "Python", "JavaScript", "TypeScript"])
run_button = st.button("🔍 리뷰 시작")
```

### Agent 실행 상태 (하단)
```python
status_placeholder = st.empty()
# 각 Agent 실행 시 상태 업데이트
# ✅ Security → 🔄 Performance → ⬜ Quality → ⬜ Summary
```

### 결과 탭 (우측)
```python
tab_overview, tab_security, tab_perf, tab_quality = st.tabs([
    "Overview", "Security", "Performance", "Quality"
])
```

### Markdown 리포트 생성
```python
def generate_markdown_report(result: dict) -> str:
    """Summary Agent 결과를 Markdown 문서로 변환"""
    # 점수, 이슈 목록, 교차 반론 충돌, 수정 우선순위 포함
    ...

st.download_button("📥 리포트 다운로드", md_content, file_name="review_report.md")
```

---

## 선행 조건 및 의존성

- Phase 3 파이프라인 전체 동작 (Orchestrator → Agent 4종 → 결과 반환)
- `streamlit` 패키지 설치

---

## 개발 시 주의사항

- Agent 실행 중 UI가 블로킹되지 않도록 상태 표시 구현
- 700줄 초과 코드 입력 시 구체적 해결 방법 포함한 에러 메시지 표시
- 에러 발생 시 사용자에게 친절한 메시지 (API 키 미설정, 네트워크 오류 등)
- 리뷰 결과에서 severity별 색상 구분 (critical: 빨강, warning: 주황, info: 파랑)

---

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-03-25 | 최초 작성 |
| 2026-03-27 | 전체 항목 완료 상태 반영 |
| 2026-03-27 | 모델 선택 드롭다운 추가 (API 자동 조회), 언어 감지 confidence 경고 추가, 700줄 제한 반영 |
