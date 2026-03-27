import re


LANGUAGE_PATTERNS = {
    "python": [r"\bdef \w+\(", r"\bimport \w+", r"\bclass \w+.*:", r"print\("],
    "javascript": [r"\bfunction\b", r"\bconst \w+\s*=", r"\blet \w+\s*=", r"console\.log\("],
    "typescript": [r":\s*(string|number|boolean|any)\b", r"\binterface \w+", r"<\w+>"],
    "java": [r"\bpublic\s+(class|static|void)\b", r"System\.out\.print"],
    "go": [r"\bfunc \w+\(", r"\bpackage \w+", r":="],
}


def detect_language(code: str) -> tuple[str, float]:
    """
    코드의 언어를 감지한다.

    반환: (언어, confidence)
      - confidence = 1등 점수와 2등 점수의 차이 비율 (0.0 ~ 1.0)
      - 1.0에 가까울수록 확실, 0.0에 가까울수록 불확실
    """
    scores = {}
    for lang, patterns in LANGUAGE_PATTERNS.items():
        scores[lang] = sum(1 for p in patterns if re.search(p, code))

    best = max(scores, key=scores.get)

    if scores[best] == 0:
        return "unknown", 0.0

    # confidence 계산: 1등과 2등의 차이가 클수록 확실
    sorted_scores = sorted(scores.values(), reverse=True)
    first, second = sorted_scores[0], sorted_scores[1]
    confidence = (first - second) / first if first > 0 else 0.0

    return best, confidence


class ReviewState:
    def __init__(self):
        self.code: str = ""
        self.language: str = ""
        self.findings: dict = {}
        self.errors: list = []

    # confidence 임계값: 이 값 미만이면 "감지가 불확실"
    LOW_CONFIDENCE_THRESHOLD = 0.4

    def set_code(self, code: str, language: str = None):
        self.code = code
        if language:
            self.language = language
            self.language_confidence = 1.0
        else:
            self.language, self.language_confidence = detect_language(code)

    def add_finding(self, agent_name: str, result: dict):
        self.findings[agent_name] = result

    def add_error(self, agent_name: str, error_msg: str):
        self.errors.append({"agent": agent_name, "error": error_msg})

    def get_previous_findings(self) -> list[dict]:
        return list(self.findings.values())

    def get_summary(self) -> dict:
        return {
            "code": self.code,
            "language": self.language,
            "findings": self.findings,
            "errors": self.errors,
        }
