"""Agent 内部消息与 Chat Completions 消息的转换。"""

from typing import cast

from openai.types.chat import (
    ChatCompletionMessageParam,
)

from app.agent.models import (
    AgentModelReply,
)
from app.tools.models import ToolResult


def build_assistant_message(
    reply: AgentModelReply,
) -> ChatCompletionMessageParam:
    """把标准化模型响应转换成 assistant message。"""

    payload: dict[str, object] = {
        "role": "assistant",
        "content": reply.content,
    }

    if reply.tool_calls:
        payload["tool_calls"] = [
            {
                "id": tool_call.call_id,
                "type": "function",
                "function": {
                    "name": tool_call.name,
                    "arguments": (
                        tool_call.arguments_json
                    ),
                },
            }
            for tool_call in reply.tool_calls
        ]

    return cast(
        ChatCompletionMessageParam,
        payload,
    )


def build_tool_result_message(
    call_id: str,
    result: ToolResult,
) -> ChatCompletionMessageParam:
    """把真实工具结果转换成 tool message。"""

    return cast(
        ChatCompletionMessageParam,
        {
            "role": "tool",
            "tool_call_id": call_id,
            "content": result.to_json(),
        },
    )