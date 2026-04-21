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
            parts.append("\n## 이전 Agent 분석 결과 (요약)")
            for finding in previous:
                summary = self._summarize_finding(finding)
                parts.append(f"```json\n{json.dumps(summary, ensure_ascii=False, indent=2)}\n```")

        return "\n".join(parts)

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
                }
                for issue in issues
                if issue.get("severity") in ("critical", "warning")
            ]
        finding_summary = finding.get("summary", "")
        if finding_summary:
            summary["summary"] = finding_summary[:200]
        return summary

    _LEVEL_CONTEXTS = {
        "personal": (
            "## 프로젝트 레벨: personal (개인 학습 / 사이드 프로젝트)\n"
            "아래 규칙을 반드시 따르세요:\n"
            "- 인증/인가(authentication/authorization) 누락 → severity를 **info**로 설정 (참고사항으로만 언급)\n"
            "- Rate Limiting 없음 → **지적하지 마세요** (이슈 목록에 포함하지 마세요)\n"
            "- HTTPS 미적용 → **지적하지 마세요**\n"
            "- 모니터링/로깅 미흡 → severity를 **info**로 설정\n"
            "- 에러 메시지 내부 정보 노출 → severity를 **info**로 설정\n"
            "- 로그 인젝션 → severity를 **info**로 설정\n"
            "단, 실제 보안 취약점(SQL Injection, XSS, 하드코딩된 비밀키, eval/exec 사용 등)은 "
            "프로젝트 레벨과 무관하게 원래 severity를 유지하세요.\n"
        ),
        "internal": (
            "## 프로젝트 레벨: internal (사내 / 팀 내부용)\n"
            "아래 규칙을 반드시 따르세요:\n"
            "- 인증/인가(authentication/authorization) 누락 → severity를 **warning**으로 설정\n"
            "- Rate Limiting 없음 → severity를 **info**로 설정\n"
            "- HTTPS 미적용 → severity를 **warning**으로 설정\n"
            "- 모니터링/로깅 미흡 → severity를 **info**로 설정\n"
            "단, 실제 보안 취약점(SQL Injection, XSS, 하드코딩된 비밀키, eval/exec 사용 등)은 "
            "프로젝트 레벨과 무관하게 원래 severity를 유지하세요.\n"
        ),
    }

    def _build_system_prompt(self) -> str:
        level_ctx = self._LEVEL_CONTEXTS.get(self.config.project_level, "")
        if level_ctx:
            return level_ctx + "\n" + self.system_prompt
        return self.system_prompt

    def analyze(self, state: ReviewState) -> dict:
        response = self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            system=self._build_system_prompt(),
            messages=[{"role": "user", "content": self._build_prompt(state)}],
            tools=[self.tool_schema],
            tool_choice={"type": "tool", "name": self.tool_name},
        )

        for block in response.content:
            if block.type == "tool_use":
                return block.input

        raise RuntimeError(f"{self.name}: tool_use 응답을 받지 못했습니다.")
