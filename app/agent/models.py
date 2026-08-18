"""Agent 模型响应、工具步骤和最终结果。"""

from dataclasses import dataclass
from typing import Literal

from app.tools.models import (
    JSONValue,
    ToolName,
    ToolResult,
)


AgentFinishReason = Literal[
    "completed",
    "needs_clarification",
    "invalid_arguments",
]


@dataclass(frozen=True)
class ModelToolCall:
    """模型返回的一次 function tool call。"""

    call_id: str
    name: str
    arguments_json: str

    def __post_init__(self) -> None:
        if not self.call_id.strip():
            raise ValueError(
                "tool call id 不能为空。"
            )

        if not self.name.strip():
            raise ValueError(
                "tool call name 不能为空。"
            )

        if not self.arguments_json.strip():
            raise ValueError(
                "tool call arguments 不能为空。"
            )


@dataclass(frozen=True)
class AgentModelReply:
    """一次模型响应的标准化表示。"""

    content: str | None
    tool_calls: tuple[ModelToolCall, ...] = ()

    def __post_init__(self) -> None:
        has_content = (
            isinstance(self.content, str)
            and bool(self.content.strip())
        )

        if not has_content and not self.tool_calls:
            raise ValueError(
                "模型响应必须包含文本或 tool calls。"
            )


@dataclass(frozen=True)
class AgentToolStep:
    """Agent 已真实执行的一次工具步骤。"""

    call_id: str
    tool_name: ToolName
    arguments: dict[str, JSONValue]
    result: ToolResult

    def to_dict(self) -> dict[str, JSONValue]:
        return {
            "call_id": self.call_id,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "result": self.result.to_dict(),
        }


@dataclass(frozen=True)
class AgentRunResult:
    """一次 Agent 运行的最终结果。"""

    answer: str
    finish_reason: AgentFinishReason
    model_rounds: int
    tool_steps: tuple[AgentToolStep, ...] = ()

    def __post_init__(self) -> None:
        if not self.answer.strip():
            raise ValueError(
                "Agent 最终回答不能为空。"
            )

        if self.model_rounds <= 0:
            raise ValueError(
                "model_rounds 必须大于 0。"
            )

    def to_dict(self) -> dict[str, JSONValue]:
        return {
            "answer": self.answer,
            "finish_reason": self.finish_reason,
            "model_rounds": self.model_rounds,
            "tool_steps": [
                step.to_dict()
                for step in self.tool_steps
            ],
        }