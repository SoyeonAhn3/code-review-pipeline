import re
import requests
from src.config import Config


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """GitHub PR URL에서 owner, repo, pr_number를 추출한다."""
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.search(pattern, url)
    if not match:
        raise ValueError(f"올바른 GitHub PR URL이 아닙니다: {url}")
    return match.group(1), match.group(2), int(match.group(3))


def get_pr_files(owner: str, repo: str, pr_number: int, token: str = None) -> list[dict]:
    """PR의 변경 파일 목록을 가져온다."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_file_content(owner: str, repo: str, path: str, ref: str, token: str = None) -> str:
    """특정 브랜치/커밋의 파일 전체 내용을 가져온다."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {"Accept": "application/vnd.github.v3.raw"}
    if token:
        headers["Authorization"] = f"token {token}"

    response = requests.get(url, headers=headers, params={"ref": ref})
    response.raise_for_status()
    return response.text


def get_pr_info(owner: str, repo: str, pr_number: int, token: str = None) -> dict:
    """PR의 기본 정보(head ref 등)를 가져온다."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    return {
        "title": data.get("title", ""),
        "head_ref": data["head"]["sha"],
        "base_ref": data["base"]["sha"],
        "head_branch": data["head"]["ref"],
    }


def extract_changed_lines(patch: str) -> list[int]:
    """patch(diff)에서 변경된 라인 번호를 추출한다."""
    if not patch:
        return []

    changed = []
    current_line = 0

    for line in patch.split("\n"):
        # @@ -10,6 +15,8 @@ 형식에서 새 파일 시작 라인 추출
        hunk = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
        if hunk:
            current_line = int(hunk.group(1))
            continue

        if line.startswith("+") and not line.startswith("+++"):
            changed.append(current_line)
            current_line += 1
        elif line.startswith("-") and not line.startswith("---"):
            pass  # 삭제된 줄은 라인 번호 증가 안 함
        else:
            current_line += 1

    return changed


SUPPORTED_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go"}


def detect_language_from_filename(filename: str) -> str:
    """파일 확장자로 언어를 감지한다."""
    ext_map = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".java": "java",
        ".go": "go",
    }
    for ext, lang in ext_map.items():
        if filename.endswith(ext):
            return lang
    return "unknown"


def fetch_pr_for_review(
    pr_url: str, token: str = None, max_files: int = 30
) -> list[dict]:
    """
    PR URL에서 리뷰할 파일 목록을 준비한다.

    반환값: [{"filename": ..., "language": ..., "code": ..., "changed_lines": [...], "additions": N, "deletions": N}]
    """
    owner, repo, pr_number = parse_pr_url(pr_url)
    pr_info = get_pr_info(owner, repo, pr_number, token)
    files = get_pr_files(owner, repo, pr_number, token)

    review_files = []
    for f in files:
        filename = f["filename"]
        ext = "." + filename.rsplit(".", 1)[-1] if "." in filename else ""

        if ext not in SUPPORTED_EXTENSIONS:
            continue

        changed_lines = extract_changed_lines(f.get("patch", ""))

        try:
            code = get_file_content(owner, repo, filename, pr_info["head_ref"], token)
        except Exception:
            code = f.get("patch", "")

        review_files.append({
            "filename": filename,
            "language": detect_language_from_filename(filename),
            "code": code,
            "changed_lines": changed_lines,
            "additions": f.get("additions", 0),
            "deletions": f.get("deletions", 0),
        })

        if len(review_files) >= max_files:
            break

    return review_files
