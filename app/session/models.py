"""短期内存会话状态。"""

import json
from dataclasses import dataclass
from typing import cast

from openai.types.chat import (
    ChatCompletionMessageParam,
)

from app.agent.models import AgentFinishReason
from app.tools.models import JSONValue


@dataclass(frozen=True)
class SessionState:
    """一个 CLI 会话的不可变状态快照。"""

    session_id: str
    messages: tuple[
        ChatCompletionMessageParam,
        ...
    ]
    turn_count: int = 0
    last_finish_reason: (
        AgentFinishReason | None
    ) = None

    def __post_init__(self) -> None:
        if not self.session_id.strip():
            raise ValueError(
                "session_id 不能为空。"
            )

        if self.turn_count < 0:
            raise ValueError(
                "turn_count 不能小于 0。"
            )

        if not self.messages:
            raise ValueError(
                "SessionState 至少需要 system message。"
            )

        first_role = self.messages[0].get("role")
        if first_role != "system":
            raise ValueError(
                "SessionState 第一条必须是 system message。"
            )

    @property
    def message_count(self) -> int:
        return len(self.messages)

    @property
    def waiting_for_clarification(self) -> bool:
        return (
            self.last_finish_reason
            == "needs_clarification"
        )

    def to_dict(self) -> dict[str, JSONValue]:
        serialized_messages = cast(
            list[JSONValue],
            [
                dict(message)
                for message in self.messages
            ],
        )

        return {
            "session_id": self.session_id,
            "turn_count": self.turn_count,
            "message_count": self.message_count,
            "waiting_for_clarification": (
                self.waiting_for_clarification
            ),
            "last_finish_reason": (
                self.last_finish_reason
            ),
            "messages": serialized_messages,
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            indent=2,
        )