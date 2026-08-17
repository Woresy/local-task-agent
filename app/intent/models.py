"""意图名称和结构化识别结果。"""

import json
from dataclasses import dataclass
from typing import Literal

from app.tools.models import JSONValue


IntentName = Literal[
    "lookup_metric",
    "query_status",
    "create_summary",
    "general_chat",
    "unknown",
]

ALLOWED_INTENTS: frozenset[str] = frozenset(
    {
        "lookup_metric",
        "query_status",
        "create_summary",
        "general_chat",
        "unknown",
    }
)


@dataclass(frozen=True)
class IntentResult:
    """一次结构化意图识别结果。"""

    intent: IntentName
    arguments: dict[str, JSONValue]
    confidence: float
    reason: str

    def __post_init__(self) -> None:
        if self.intent not in ALLOWED_INTENTS:
            raise ValueError(
                f"不支持的 intent：{self.intent}"
            )

        if not 0 <= self.confidence <= 1:
            raise ValueError(
                "confidence 必须在 0 到 1 之间。"
            )

        if not self.reason.strip():
            raise ValueError(
                "reason 不能为空。"
            )

    def to_dict(self) -> dict[str, JSONValue]:
        return {
            "intent": self.intent,
            "arguments": self.arguments,
            "confidence": self.confidence,
            "reason": self.reason,
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
        )