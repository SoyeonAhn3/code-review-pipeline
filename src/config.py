import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

# 관심 있는 모델 패밀리 (표시명 → 검색 키워드)
MODEL_FAMILIES = {
    "opus": "Claude Opus (최고 성능)",
    "sonnet": "Claude Sonnet (권장 — 균형)",
    "haiku": "Claude Haiku (빠르고 저렴)",
}

# API 실패 시 사용할 기본값
FALLBACK_MODELS = {
    "opus": "claude-opus-4-20250514",
    "sonnet": "claude-sonnet-4-20250514",
    "haiku": "claude-haiku-4-5-20251001",
}


def fetch_latest_models(api_key: str) -> dict[str, str]:
    """
    Anthropic API에서 모델 목록을 조회하여 패밀리별 최신 모델 ID를 반환한다.

    반환 예시: {"sonnet": "claude-sonnet-4-20250514", "opus": "...", "haiku": "..."}
    API 실패 시 FALLBACK_MODELS를 반환한다.
    """
    if not api_key:
        return dict(FALLBACK_MODELS)

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.models.list(limit=100)

        # 패밀리별로 모델을 수집
        family_models: dict[str, list[str]] = {f: [] for f in MODEL_FAMILIES}

        for model in response.data:
            model_id = model.id
            for family in MODEL_FAMILIES:
                if family in model_id:
                    family_models[family].append(model_id)

        # 각 패밀리에서 최신(사전순 마지막) 모델 선택
        result = {}
        for family in MODEL_FAMILIES:
            candidates = sorted(family_models[family])
            result[family] = candidates[-1] if candidates else FALLBACK_MODELS[family]

        return result

    except Exception:
        return dict(FALLBACK_MODELS)


class Config:
    VALID_PROJECT_LEVELS = ("personal", "internal", "production")

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.max_code_lines = int(os.getenv("MAX_CODE_LINES", "700"))
        self.max_tokens = int(os.getenv("MAX_TOKENS", "4096"))
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.project_level = "production"

        # 모델: .env에 지정된 값 → 없으면 API에서 최신 sonnet 자동 조회 → 실패 시 fallback
        env_model = os.getenv("MODEL_NAME", "")
        if env_model:
            self.model = env_model
        else:
            latest = fetch_latest_models(self.api_key)
            self.model = latest["sonnet"]

    def validate(self):
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
