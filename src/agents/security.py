from pathlib import Path
from src.agents.base_agent import BaseAgent

PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "security.txt"


class SecurityAgent(BaseAgent):
    name = "security"
    tool_name = "report_security_issues"

    def __init__(self, config):
        super().__init__(config)
        self.system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
        self.tool_schema = {
            "name": self.tool_name,
            "description": "보안 분석 결과를 구조화된 형식으로 보고",
            "input_schema": {
                "type": "object",
                "properties": {
                    "agent": {"type": "string", "enum": ["security"]},
                    "issues": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "severity": {"type": "string", "enum": ["critical", "warning", "info"]},
                                "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                                "line": {"type": "integer"},
                                "code_snippet": {"type": "string"},
                                "issue": {"type": "string"},
                                "suggestion": {"type": "string"},
                            },
                            "required": ["severity", "confidence", "line", "issue", "suggestion"],
                        },
                    },
                    "summary": {"type": "string"},
                },
                "required": ["agent", "issues", "summary"],
            },
        }
