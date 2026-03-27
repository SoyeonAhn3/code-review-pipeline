import json
import anthropic
from src.config import Config
from src.review_state import ReviewState


class BaseAgent:
    name: str = ""
    system_prompt: str = ""
    tool_schema: dict = {}
    tool_name: str = ""

    def __init__(self, config: Config):
        self.config = config
        self.client = anthropic.Anthropic(api_key=config.api_key)

    def _build_prompt(self, state: ReviewState) -> str:
        parts = [
            f"## 리뷰 대상 코드 ({state.language})\n```\n{state.code}\n```"
        ]

        previous = state.get_previous_findings()
        if previous:
            parts.append("\n## 이전 Agent 분석 결과")
            for finding in previous:
                parts.append(f"```json\n{json.dumps(finding, ensure_ascii=False, indent=2)}\n```")

        return "\n".join(parts)

    def analyze(self, state: ReviewState) -> dict:
        response = self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            system=self.system_prompt,
            messages=[{"role": "user", "content": self._build_prompt(state)}],
            tools=[self.tool_schema],
            tool_choice={"type": "tool", "name": self.tool_name},
        )

        for block in response.content:
            if block.type == "tool_use":
                return block.input

        raise RuntimeError(f"{self.name}: tool_use 응답을 받지 못했습니다.")
