---
name: review-deliverable
version: 1.1
description: 코드 리뷰 결과를 포트폴리오 + 코드 수정 가이드용 산출물로 정제하여 생성한다. "/review-deliverable", "산출물 만들어줘", "리뷰 리포트 만들어줘", "리뷰 산출물 생성해줘" 등의 요청 시 트리거한다.
depends_on: []
produces:
  - output/{프로젝트명}_review_report.md
references:
  - references/report-template.md   # 산출물 포맷 정의 + 작성 규칙
---

# Review Deliverable Skill

코드 리뷰 결과를 포트폴리오 및 코드 수정 가이드로 활용할 수 있는 정제된 산출물을 생성한다.
포맷 정의 및 작성 규칙은 `references/report-template.md`를 참고한다.

---

## STEP 0 — 레퍼런스 로드

스킬 실행 전 반드시 먼저 실행:

```
Read(".claude/skills/review-deliverable/references/report-template.md")
```

→ 산출물 구조, Section별 작성 규칙, 난이도 기준, 출력 포맷 확인

---

## STEP 1 — 입력 확인

사용자에게 아래 2가지를 확인한다. 대화 컨텍스트에서 파악 가능하면 확인 생략.

| 항목 | 설명 | 기본값 |
|------|------|--------|
| 대상 리뷰 파일 | output/ 내 리뷰 파일 경로 | 없음 (반드시 사용자 지정) |
| 리뷰 레벨 | Production / Personal | 리뷰 파일에서 추출 |

파악이 부족하면 한 번만 질문:
```
"산출물을 만들 리뷰 파일을 알려주세요:
1. 리뷰 파일 경로 (예: output/stock-analyzer_personal_review.md)
2. 리뷰 레벨 (Production / Personal)"
```

---

## STEP 2 — 리뷰 데이터 읽기 + 분석

1. 사용자가 지정한 리뷰 파일을 Read로 읽기
2. 아래 데이터 추출:

| 추출 항목 | 용도 |
|-----------|------|
| 프로젝트명 | 파일명, Section 1 |
| 분석 일자 | Section 1 |
| 리뷰 레벨 | Section 1 |
| 분석 범위 (파일 수, 코드 라인) | Section 1 |
| 전체 점수 / 등급 | Section 1, 2 |
| Critical 이슈 목록 (파일, 라인, 설명, 제안) | Section 2, 3 |
| Warning 이슈 목록 (파일, 라인, 설명, 제안) | Section 2, 4 |
| Info 이슈 건수 | Section 2 |
| 배치별 점수 | Section 2 |

3. Warning 이슈를 **유형별로 재분류**:
   - 보안 관련 → 4.1
   - 성능 관련 → 4.2
   - 코드 품질 관련 → 4.3
   - 복합 이슈는 주된 카테고리에 배치

4. **개선 우선순위 Top 10 선정** (Section 6용):
   - Critical + Warning 전체에서 **영향 범위 × 난이도 역수(ROI)** 기준으로 상위 10건 선정
   - 선정 기준: ① 보안 사고/데이터 손실 위험 → ② 사용자 체감 성능 영향 → ③ 낮은 난이도로 높은 효과 → ④ 여러 파일에 걸친 파급력
   - 각 항목에 예상 소요시간과 선정 근거 1줄 작성

---

## STEP 3 — 산출물 작성

`references/report-template.md`의 구조와 규칙에 따라 6개 Section 작성:

### Section 1. Overview
- 리뷰 데이터에서 추출한 기본 정보 테이블

### Section 2. Issue Dashboard
- 심각도별 건수 테이블
- 카테고리 x 심각도 매트릭스
- 배치별 점수 테이블

### Section 3. Critical Issues (상세)
- 이슈별 블록 작성
- **현재 구조**: 리뷰 원본의 이슈 설명을 구조/패턴 수준으로 재가공
- **개선 방향**: 리뷰 원본의 개선 제안을 구조/패턴 수준으로 재가공
- **난이도**: report-template.md의 기준에 따라 상/중/하 판단
- **영향**: 미수정 시 발생 가능한 문제 기술

### Section 4. Warning Issues (요약)
- STEP 2에서 재분류한 유형별 테이블
- Before/After 없이 이슈 + 개선 방향 1줄

### Section 5. Methodology (간략)
- 4-Agent 구조, 점수 공식, 등급/심각도 기준

### Section 6. 개선 우선순위 Top 10
- STEP 2에서 선정한 Top 10을 테이블로 작���
- Critical과 Warning을 혼합하여 **실제 수정 순서** 제안
- 각 항목에 순위, 이슈 요약, 유형, 심각도, 난이도, 예상 소요, 근거 포함
- 근거는 왜 이 순위인지를 1줄로 설명 (포트폴리오에서 의사결�� 근거로 활용)

---

## STEP 4 — 저장 + 출력

1. 저장 경로: `c:\Users\sy.ahn\OneDrive - Bosch Group\AI Development\code-review-pipeline\output\{프로젝트명}_review_report.md`
2. Write로 저장
3. 채팅에 결과 요약 출력 (report-template.md의 채팅 출력 포맷 참조)

---

## 실패 처리

| 실패 유형 | 처리 방법 |
|----------|----------|
| 리뷰 파일 경로 미지정 | STEP 1 질문 1회 실행 |
| 리뷰 파일 읽기 실패 | 경로 재확인 요청 후 중단 |
| 리뷰 데이터 파싱 불가 | 파일 형식이 맞는지 확인 요청 후 중단 |
| output/ 디렉토리 없음 | Bash로 `mkdir -p output` 후 재시도 |
| 파일 저장 실패 | 채팅에만 출력 후 저장 실패 안내 |
| references 로드 실패 | 경로 확인 요청 후 중단 |

---

## 주의사항

- 대상 프로젝트의 소스코드를 직접 읽지 않음 (리뷰 파일 데이터만 사용)
- 리뷰 파일을 자동 탐색하지 않음 (반드시 사용자가 지정)
- Critical의 Before/After는 코드 스니펫이 아닌 구조/패턴 수준 설명
- 동일 파일명이 이미 존재하면 사용자에게 덮어쓰기 여부 확인
