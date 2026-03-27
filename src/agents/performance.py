from pathlib import Path
from src.agents.base_agent import BaseAgent

PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "performance.txt"


class PerformanceAgent(BaseAgent):
    name = "performance"
    tool_name = "report_performance_issues"

    def __init__(self, config):
        super().__init__(config)
        self.system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
        self.tool_schema = {
            "name": self.tool_name,
            "description": "성능 분석 결과를 구조화된 형식으로 보고",
            "input_schema": {
                "type": "object",
                "properties": {
                    "agent": {"type": "string", "enum": ["performance"]},
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
                    "cross_review": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "target_agent": {"type": "string"},
                                "target_issue": {"type": "string"},
                                "opinion": {"type": "string", "enum": ["agree", "caution", "disagree"]},
                                "comment": {"type": "string"},
                            },
                            "required": ["target_agent", "target_issue", "opinion", "comment"],
                        },
                    },
                    "summary": {"type": "string"},
                },
                "required": ["agent", "issues", "cross_review", "summary"],
            },
        }
