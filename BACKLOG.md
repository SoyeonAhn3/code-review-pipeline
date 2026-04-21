# Code Review Pipeline — Backlog

## 발견 일자: 2026-04-21
## 발견 경위: stock-analyzer 프로젝트 전체 리뷰 실행 후 결과 분석

---

## [DONE] BL-001: Quality Agent 토큰 경쟁 패배 (Silent Failure)

**심각도:** Critical (기능 결함)  
**예상 공수:** 1~2시간  
**실제 공수:** 30분  
**영향 범위:** `src/agents/base_agent.py`  
**완료일:** 2026-04-21

### 현상

- Quality Agent가 6회 실행 중 4회에서 issues를 반환하지 못함
- 응답에 `{"agent": "quality"}` 만 존재하고 issues/cross_review 키가 누락
- 파이프라인은 "done"으로 보고하여 사용자가 실패를 인지할 수 없음

### 원인 분석 (수치 근거)

Quality Agent에 전달되는 프롬프트 구성을 측정한 결과:

```
코드 본문:            21,271 chars
이전 Agent 결과 원문:  15,052 chars  ← 병목 원인
────────────────────────────────────
합계 (user 메시지):   36,323 chars (≈ 9,000 토큰)
```

이전 결과 내부 구성:
- suggestion 필드 (수정 코드 예시 포함): 전체의 **48.2%** 차지
- code_snippet 필드: 추가 15% 차지
- 실제 판단에 필요한 정보 (severity, line, issue): **나머지 37%**

즉, 이전 Agent 결과의 **63%가 Quality Agent의 판단에 불필요한 데이터**였으며,
이것이 입력 토큰을 과도하게 소비하여 `max_tokens=4096` 내에서 Quality Agent가
자신의 분석 결과를 출력할 공간이 부족해짐.

Claude는 토큰 한도에 도달하면 tool_use 호출에서 선택적 필드(issues, cross_review)를
생략하고 필수 최소 구조(`{"agent": "quality"}`)만 반환하는 동작을 보임.

### 해결 방법

`src/agents/base_agent.py`에 `_summarize_finding()` 메서드를 추가하여
이전 Agent 결과를 요약본으로 압축 전달:

```python
def _summarize_finding(self, finding: dict) -> dict:
    """이전 Agent 결과에서 핵심만 추출하여 토큰을 절약한다."""
    summary = {"agent": finding.get("agent", "unknown")}
    issues = finding.get("issues", [])
    if issues:
        summary["issues"] = [
            {
                "severity": issue.get("severity"),
                "line": issue.get("line"),
                "issue": issue.get("issue"),
                # suggestion, code_snippet 제거 → 토큰 48% 절감
            }
            for issue in issues
            if issue.get("severity") in ("critical", "warning")  # info 생략
        ]
    finding_summary = finding.get("summary", "")
    if finding_summary:
        summary["summary"] = finding_summary[:200]  # 요약도 200자 제한
    return summary
```

변경 사항:
1. `suggestion` 제거 (코드 예시 불필요 — Quality Agent는 품질만 판단)
2. `code_snippet` 제거 (원본 코드가 이미 프롬프트에 포함됨)
3. `info` 심각도 이슈 필터링 (critical/warning만 교차 검토 대상)
4. `summary` 200자 제한

### 검증 결과

테스트 샘플: stock-analyzer의 3개 파일 (claude_client.py + api_client.py + alerts.py, 395줄)

| 항목 | 수정 전 | 수정 후 |
|------|---------|---------|
| Quality issues | **0건** (키 누락) | **10건** (정상 반환) |
| Quality keys | `['agent']` | `['agent', 'issues']` |
| 이전 결과 크기 | 15,052 chars | ~4,000 chars (**73% 감소**) |

Quality Agent가 naming, magic string, 에러 방어 코드 부재, 파라미터 과다,
타입 안전성 등 실제 코드 품질 이슈를 정확히 탐지함.

### 잔여 사항

- `cross_review`는 이번 테스트에서 빈 배열 → Security 결과가 0건이라 교차 대상 없음 (정상 동작)
- Security 이슈가 있는 코드에서 cross_review 반환 여부는 BL-005에서 재확인 필요

---

## [DONE] BL-002: 프로젝트 레벨 설정 미지원

**심각도:** High (사용자 신뢰도 문제)  
**예상 공수:** 2~3시간  
**영향 범위:** `src/config.py`, `src/agents/base_agent.py`, `app.py`

### 현상

- 개인 학습 프로젝트도 엔터프라이즈 프로덕션 기준으로 평가
- "인증 없음", "Rate Limiting 없음" 등이 무조건 Critical/Warning으로 지적
- 결과적으로 거의 모든 프로젝트가 F 등급 → 도구 신뢰도 하락

### 원인 분석

Security Agent의 system prompt(`prompts/security.txt`)에 아래 규칙이 무조건 적용됨:

```
### 인증/권한
- 인증 체크 없이 민감한 데이터에 접근하는 엔드포인트
- 권한 검증 누락
```

프로젝트 유형(개인/사내/프로덕션) 구분 없이 동일 기준을 적용하므로:
- 개인 학습 프로젝트: 인증 당연히 없음 → Critical 판정
- 라우터 8개 × "인증 없음" = Critical 8건 → -120점 → 즉시 0점

즉, **평가 기준에 컨텍스트(context)가 없어서** 모든 프로젝트가 프로덕션으로 간주됨.

### 해결 방법: 프롬프트 주입 (방안 A)

**핵심 전략:** 프로젝트 레벨을 **system prompt**에 동적으로 주입하여 
AI가 심각도를 컨텍스트에 맞게 자체 판단하도록 함.

system prompt에 넣는 이유:
- Claude의 지시 우선순위: `system prompt > user message > 암묵적 판단`
- user message에 넣으면 AI가 무시할 확률이 높으나, system prompt는 충실히 따름

**수정 파일:**

| 파일 | 변경 내용 |
|------|-----------|
| `src/config.py` | `project_level` 필드 추가 (기본값: "production") |
| `src/agents/base_agent.py` | `_build_system_prompt()` 메서드 추가, `analyze()`에서 동적 system prompt 사용 |
| `app.py` | Streamlit UI에 라디오 버튼 추가 |

**레벨별 심각도 가이드 (system prompt에 주입):**

| 이슈 유형 | personal | internal | production |
|-----------|----------|----------|------------|
| SQL Injection / XSS | critical | critical | critical |
| 하드코딩 API 키 | warning | critical | critical |
| 인증/인가 누락 | info | warning | critical |
| Rate Limiting 없음 | 무시 | info | warning |
| HTTPS 미적용 | 무시 | warning | warning |
| 로그 인젝션 | info | warning | warning |
| 에러 정보 노출 | info | warning | warning |

**원칙:** 실제 취약점(Injection, XSS, 키 노출)은 레벨과 무관하게 유지.
운영 인프라 관련 항목만 레벨에 따라 조정.

**리스크 완화:**
- 레벨 규칙을 system prompt에 배치하여 AI 준수율 극대화
- 향후 필요 시 경량 후처리 safety net(키워드 기반 severity 보정) 추가 가능 (BL-002b로 분리)

### 검증 결과

**완료일:** 2026-04-21

테스트 대상: stock-analyzer의 `alerts.py` + `api_client.py` (272줄)

| 항목 | Production | Personal | 변화 |
|------|-----------|----------|------|
| 점수 | 33/100 (F) | 51/100 (F) | +18점 |
| Critical | 3건 | 0건 | -3건 |
| Warning | 14건 | 8건 | -6건 |
| Info | 0건 | 1건 | +1건 |

심각도 변화 확인:
- "인증 누락" critical → info (프롬프트 지시 준수)
- "Rate Limiting 없음" → 제거됨 (프롬프트 지시 준수)
- "소유권 검증 없음(IDOR)" critical → warning (실제 취약점은 유지)
- "입력값 검증" warning → warning (실제 취약점 유지)

점수가 33→51로 올랐지만 여전히 F인 이유는 BL-003(중복 카운트) + BL-004(가중치) 미수정 때문.
프로젝트 레벨 기능 자체는 정상 동작 확인.

---

## [DONE] BL-003: 동일 패턴 이슈 중복 카운트

**심각도:** High (점수 왜곡)  
**예상 공수:** 2~3시간  
**실제 공수:** 30분  
**영향 범위:** `prompts/summary.txt`, `src/agents/summary.py`  
**완료일:** 2026-04-21

### 현상

- "인증 누락"이 라우터 8개에 각각 Critical로 지적 → 8건 × (-15) = -120점
- "입력값 검증 없음"도 엔드포인트마다 반복 → 추가 -60점
- 동일 패턴인데 라인 번호만 다르면 별개 이슈로 카운트

### 원인 분석

`prompts/summary.txt`의 중복 제거 규칙이 "같은 라인"만 기준으로 판단:

```
같은 라인에 대해 여러 Agent가 비슷한 지적을 한 경우 하나로 병합
```

이 규칙은 **동일 라인에 Security + Performance 등 여러 Agent가 지적한 경우**만 병합함.
"인증 없음"이 Line 12, 25, 38, 50에서 각각 나오면 라인 번호가 다르므로 별개 이슈로 카운트.

Summary Agent(Claude)는 프롬프트에 "동일 패턴 통합"이라는 지시가 없었기 때문에
기계적으로 모든 이슈를 그대로 나열하고 각각 감점을 적용함.

### 해결 방법

**1. `prompts/summary.txt` — 중복 제거 규칙에 "1-B. 동일 패턴 중복" 추가:**

```
#### 1-B. 동일 패턴 중복 (반드시 수행)
- 같은 유형의 이슈가 여러 라인에서 반복되면 1건으로 통합하세요
- 통합 시 affected_lines: [12, 25, 38, 50] 배열을 추가하세요
- 채점은 통합된 1건에 대해서만 감점하세요
- 동일 패턴 판단 기준:
  - issue 설명의 핵심 키워드가 같은 경우
  - 같은 Agent가 같은 종류의 제안을 반복한 경우
  - 수정 방법이 동일한 경우
```

**2. `src/agents/summary.py` — tool_schema에 `affected_lines` 필드 추가:**

```python
"affected_lines": {
    "type": "array",
    "items": {"type": "integer"},
    "description": "동일 패턴이 반복되는 모든 라인 번호 (통합된 이슈일 때만 사용)",
},
```

### 검증 결과

테스트 대상: stock-analyzer Backend 라우터 4개 (alerts, watchlist, quote, search / 168줄)

| 항목 | 수정 전 (기존 배치 기준) | 수정 후 |
|------|------------------------|---------|
| 점수 | 26/100 (F) | **49/100 (F)** |
| 전체 이슈 수 | 30건+ (라인마다 개별) | **12건** (통합) |
| "인증 누락" | Critical × 8~10건 | **Critical × 1건** (affected_lines: 10개) |
| "입력값 검증" | Warning × 5건 | **Warning × 1건** (affected_lines: 3개) |

Summary Agent가 프롬프트 지시대로 동일 패턴을 1건으로 통합하고
`affected_lines` 배열을 첨부하여 어떤 라인들이 해당하는지 표시함.

점수가 26→49로 올랐지만 여전히 F인 이유:
- production 레벨 적용 (인증 누락이 여전히 Critical)
- BL-004(가중치) 미수정
- personal 레벨 + BL-003 통합 적용 시 65~80점(C~B) 예상

---

## [DONE] BL-004: 채점 가중치 불균형

**심각도:** Medium  
**예상 공수:** 30분  
**실제 공수:** 15분  
**영향 범위:** `prompts/summary.txt`  
**완료일:** 2026-04-21

### 현상

- Critical -15점이 너무 강력하여 Critical 7건이면 무조건 0점
- Security Critical 1건 = Quality Info 15건 → 보안 편향 채점
- BL-001~003 해결 시 자연스럽게 완화되나, 독립적으로도 조정 가치 있음

### 원인 분석

기존 가중치: `Critical -15, Warning -5, Info -1`

이 가중치의 문제:
- Critical 7건 = -105점 → 다른 점수와 무관하게 **즉시 0점** (100점 초과 감점)
- Warning 8건 = -40점 → Warning만으로도 C등급 이하 확정
- Critical이 Info의 15배 → Security Agent가 Critical 1건만 내도 채점 전체에 과도한 영향

비교 기준 (일반적인 코드 리뷰 채점):
- Critical은 반드시 수정해야 하지만, 1건으로 전체가 망가지면 도구의 유용성 하락
- Warning 3~5건은 흔한 수준이므로 B등급(-15~25점) 정도가 합리적

### 해결 방법

`prompts/summary.txt`의 점수 산정 규칙을 조정:

```
수정 전: Critical -15, Warning -5, Info -1
수정 후: Critical -10, Warning -3, Info -1
```

조정 근거:
| 시나리오 | 수정 전 | 수정 후 | 기대 등급 |
|----------|---------|---------|-----------|
| Critical 3건 + Warning 5건 | -70점 (30점/F) | -45점 (55점/F) | F (맞음) |
| Critical 1건 + Warning 4건 | -35점 (65점/D) | -22점 (78점/C) | C (합리적) |
| Warning 5건 + Info 3건 | -28점 (72점/C) | -18점 (82점/B) | B (합리적) |
| Warning 2건 + Info 5건 | -15점 (85점/B) | -11점 (89점/B) | B (맞음) |

카테고리별 상한선(방안 2)과 가산점(방안 3)은 과도한 복잡도 추가 없이
단순 가중치 조정만으로 충분히 합리적인 분포를 달성하므로 적용하지 않음.

### 검증 결과

**검증 불가 — API 크레딧 소진**

코드 변경은 완료되었으나, 통합 테스트 실행 시 Anthropic API에서
`credit balance is too low` 에러 반환:

```
BadRequestError: Error code: 400
'Your credit balance is too low to access the Anthropic API.'
```

이는 코드 결함이 아닌 **계정 크레딧 부족**이 원인.
크레딧 충전 후 BL-001~004 통합 테스트 재실행 필요.

**예상 효과** (BL-003 검증 데이터 기준 역산):
- BL-003 production 테스트: 49점 (Critical 1건 + Warning 8건)
  - 기존 가중치: -15 + (-5×8) = -55 → 45점 (실제 49점, Summary 자체 판단 오차)
  - 신규 가중치: -10 + (-3×8) = -34 → **66점 (D등급)**
- Personal 레벨 + 중복 통합 + 신규 가중치 적용 시: **75~85점 (C~B등급)** 예상

---

## [LOW] BL-005: cross_review 미반환

**심각도:** Low  
**예상 공수:** 1시간  
**영향 범위:** `src/agents/quality.py`, `prompts/quality.txt`

**현상:**
- Quality Agent의 cross_review가 6개 배치 모두 빈 배열
- Agent 간 교차 검증이 실질적으로 동작하지 않음
- BL-001 (토큰 경쟁)과 연관 — 토큰 부족 시 cross_review 먼저 생략됨

**수정 방안:**
- BL-001 해결 후 재확인
- 여전히 빈 배열이면 프롬프트에서 cross_review 우선순위 강조

**검증 방법:**
- BL-001 수정 후 cross_review 반환율 확인

---

## [LOW] BL-006: 리뷰 결과 리포트 포맷 개선

**심각도:** Low  
**예상 공수:** 1시간  
**영향 범위:** `generate_report.py`, `output/`

**현상:**
- 현재 txt 포맷만 지원
- 이슈별 코드 스니펫이 줄바꿈 없이 표시되어 가독성 떨어짐

**수정 방안:**
1. Markdown(.md) 포맷 옵션 추가
2. 이슈별 접이식(collapsible) 섹션
3. 배치별 점수 시각화 (ASCII 바 차트)

---

## 의존성 관계

```
BL-001 (Quality 토큰) ──→ BL-005 (cross_review)
                 ↘
BL-002 (프로젝트 레벨)   ──→ BL-004 (채점 가중치)
                 ↗
BL-003 (중복 카운트)
```

## 착수 순서 (권장)

1. **BL-001** → Quality Agent 정상화 (이것 없이는 파이프라인이 불완전)
2. **BL-002** → 프로젝트 레벨 (사용자 체감 효과 최대)
3. **BL-003** → 중복 카운트 (점수 정상화)
4. **BL-004** → 가중치 조정 (미세 조정)
5. **BL-005** → cross_review (BL-001 후 재확인)
6. **BL-006** → 리포트 포맷 (편의성)
