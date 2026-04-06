# Phase 6 — GitHub PR 연동 `✅ 완료`

> GitHub PR URL을 입력받아 변경된 코드만 자동으로 리뷰하는 확장 기능을 구현한다.

**완료일**: 2026-03-26
**상태**: ✅ 완료
**선행 조건**: Phase 5 완료 (Eval 검증 통과)

---

## 개요

코드 직접 입력 방식(MVP)을 넘어, GitHub PR URL을 입력하면
변경된 파일의 diff만 가져와 자동 리뷰하는 확장 기능을 구현한다.
GitHub API를 Claude API Tool Use로 연동하여 포트폴리오 가치를 높인다.

---

## 완료 예정 항목

| # | 모듈 / 작업 | 상태 | 설명 |
|---|---|---|---|
| 1 | `github_client.py` — GitHub API 연동 | ✅ | PR diff 가져오기 |
| 2 | PR URL 파서 | ✅ | owner/repo/pr_number 추출 |
| 3 | diff → 코드 변환 | ✅ | patch 형식에서 변경된 코드 추출 |
| 4 | 다중 파일 리뷰 | ✅ | 파일별 리뷰 후 종합 |
| 5 | Streamlit UI에 PR 입력 추가 | ✅ | URL 입력 필드 + 파일 목록 표시 |
| 6 | 파일 업로드 기능 | ✅ | .py, .js, .jsx, .ts, .tsx, .java, .go 파일 직접 업로드 |

---

## GitHub API 연동

### PR diff 가져오기
```python
# GET /repos/{owner}/{repo}/pulls/{pr_number}/files
# → 변경된 파일 목록 + 각 파일의 patch(diff)

import requests

def get_pr_files(owner, repo, pr_number, token=None):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    headers = {"Authorization": f"token {token}"} if token else {}
    response = requests.get(url, headers=headers)
    return response.json()
```

### 응답 구조
```json
[
  {
    "filename": "src/utils.py",
    "status": "modified",
    "additions": 15,
    "deletions": 3,
    "patch": "@@ -10,6 +10,18 @@ def process_data(...):\n+    new_code_here..."
  }
]
```

### 인증
- 공개 repo: 토큰 불필요
- 비공개 repo: GitHub Personal Access Token 필요
- `.env`에 `GITHUB_TOKEN` 저장

---

## diff 기반 리뷰 전략

| 전략 | 설명 |
|---|---|
| **변경분만 리뷰** | patch에서 추가/수정된 줄만 추출하여 리뷰 |
| **전체 파일 컨텍스트** | 변경된 파일 전체를 가져와 맥락과 함께 리뷰 |
| **하이브리드 (권장)** | 전체 파일을 보되, 변경된 줄에 집중하도록 프롬프트에 명시 |

### 다중 파일 처리
```python
def review_pr(pr_url):
    files = get_pr_files(owner, repo, pr_number)
    results = []
    for file in files:
        if file['additions'] + file['deletions'] > 0:
            result = orchestrator.run(
                code=file['full_content'],
                language=detect_language(file['filename']),
                focus_lines=extract_changed_lines(file['patch'])
            )
            results.append(result)
    return aggregate_results(results)
```

---

## Streamlit UI 확장

```
┌─────────────────────────────────────┐
│  입력 방식 선택                      │
│  ○ 코드 직접 입력                    │
│  ○ GitHub PR URL                    │
│  ○ 파일 업로드                       │
├─────────────────────────────────────┤
│  PR URL: [https://github.com/...]   │
│  [🔍 PR 분석]                        │
├─────────────────────────────────────┤
│  변경된 파일 (3개):                  │
│  ☑ src/utils.py (+15, -3)           │
│  ☑ src/api.py (+42, -10)            │
│  ☐ tests/test_utils.py (+20, -5)   │
│  [🔍 선택 파일 리뷰 시작]            │
└─────────────────────────────────────┘
```

---

## 선행 조건 및 의존성

- Phase 5 Eval 검증 완료
- `requests` 패키지 설치
- GitHub Personal Access Token (비공개 repo용)

---

## 개발 시 주의사항

- GitHub API Rate Limit: 인증 시 시간당 5,000회, 미인증 시 60회
- 대규모 PR (파일 30개 이상)은 주요 파일만 선택 리뷰하도록 안내
- 토큰 제한: 파일당 500줄 초과 시 변경분 위주로 축소
- 테스트 파일은 기본적으로 리뷰 대상에서 제외 옵션 제공

---

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-03-25 | 최초 작성 |
| 2026-03-27 | 전체 항목 완료 상태 반영 |
