from pathlib import Path
from src.agents.base_agent import BaseAgent

PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "summary.txt"


class SummaryAgent(BaseAgent):
    name = "summary"
    tool_name = "report_summary"

    def __init__(self, config):
        super().__init__(config)
        self.system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
        self.tool_schema = {
            "name": self.tool_name,
            "description": "전체 리뷰 결과를 종합하여 최종 리포트 생성",
            "input_schema": {
                "type": "object",
                "properties": {
                    "overall_score": {"type": "integer", "minimum": 0, "maximum": 100},
                    "grade": {"type": "string", "enum": ["A", "B", "C", "D", "F"]},
                    "total_issues": {
                        "type": "object",
                        "properties": {
                            "critical": {"type": "integer"},
                            "warning": {"type": "integer"},
                            "info": {"type": "integer"},
                        },
                        "required": ["critical", "warning", "info"],
                    },
                    "top_3_actions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "priority": {"type": "integer"},
                                "issue": {"type": "string"},
                                "effort": {"type": "string"},
                            },
                            "required": ["priority", "issue", "effort"],
                        },
                    },
                    "cross_review_conflicts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "issue": {"type": "string"},
                                "conflict": {"type": "string"},
                                "resolution": {"type": "string"},
                            },
                            "required": ["issue", "conflict", "resolution"],
                        },
                    },
                    "comment": {"type": "string"},
                    "all_issues": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "agent": {"type": "string"},
                                "severity": {"type": "string", "enum": ["critical", "warning", "info"]},
                                "line": {"type": "integer"},
                                "issue": {"type": "string"},
                                "suggestion": {"type": "string"},
                            },
                            "required": ["agent", "severity", "line", "issue", "suggestion"],
                        },
                    },
                },
                "required": [
                    "overall_score", "grade", "total_issues",
                    "top_3_actions", "cross_review_conflicts",
                    "comment", "all_issues",
                ],
            },
        }
