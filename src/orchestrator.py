from typing import Callable
from src.config import Config
from src.review_state import ReviewState
from src.agents import ALL_AGENTS


class Orchestrator:
    def __init__(self, config: Config):
        self.config = config
        self.agent_classes = list(ALL_AGENTS)

    def register_agents(self, agent_classes: list):
        self.agent_classes = agent_classes

    def run(
        self,
        code: str,
        language: str = None,
        on_progress: Callable[[str, str], None] = None,
    ) -> dict:
        """
        파이프라인 실행.

        on_progress: 콜백 함수 (agent_name, status) — status는 "start" | "done" | "error"
        """
        self.config.validate()

        lines = code.strip().split("\n")
        if len(lines) > self.config.max_code_lines:
            over = len(lines) - self.config.max_code_lines
            raise ValueError(
                f"코드가 {len(lines)}줄입니다 (최대 {self.config.max_code_lines}줄). "
                f"{over}줄을 줄이거나, 핵심 부분만 붙여넣어 주세요. "
                f"GitHub PR 입력을 사용하면 파일별로 나눠서 리뷰할 수 있습니다."
            )

        state = ReviewState()
        state.set_code(code, language)

        for agent_cls in self.agent_classes:
            agent = agent_cls(self.config)

            if on_progress:
                on_progress(agent.name, "start")

            try:
                result = agent.analyze(state)
                state.add_finding(agent.name, result)
                if on_progress:
                    on_progress(agent.name, "done")
            except Exception as e:
                state.add_error(agent.name, str(e))
                if on_progress:
                    on_progress(agent.name, "error")

        return state.get_summary()
