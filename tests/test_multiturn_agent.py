"""多轮缺参补齐的全链路测试。"""

from collections.abc import Sequence
from typing import cast

from openai.types.chat import (
    ChatCompletionMessageParam,
)

from app.agent import (
    AgentModelReply,
    AgentRunner,
    ModelToolCall,
)
from app.agent.model import AgentModel
from app.execution import ToolRouter
from app.session import ConversationSession


class SequentialAgentModel:
    """按顺序模拟三次模型响应。"""

    def __init__(self) -> None:
        self._replies = [
            AgentModelReply(
                content=None,
                tool_calls=(
                    ModelToolCall(
                        call_id="missing-id",
                        name="query_status",
                        arguments_json="{}",
                    ),
                ),
            ),
            AgentModelReply(
                content=None,
                tool_calls=(
                    ModelToolCall(
                        call_id="complete-id",
                        name="query_status",
                        arguments_json=(
                            '{"id":"TASK-1001"}'
                        ),
                    ),
                ),
            ),
            AgentModelReply(
                content=(
                    "TASK-1001 正在运行，进度为 65%。"
                ),
            ),
        ]
        self.received_messages: list[
            list[ChatCompletionMessageParam]
        ] = []

    def complete(
        self,
        messages: Sequence[
            ChatCompletionMessageParam
        ],
    ) -> AgentModelReply:
        self.received_messages.append(
            list(messages)
        )
        return self._replies.pop(0)


def test_missing_parameter_can_be_completed_next_turn(
) -> None:
    model = SequentialAgentModel()
    runner = AgentRunner(
        model=cast(AgentModel, model),
        router=ToolRouter(),
    )
    session = ConversationSession(
        runner=runner,
    )

    first = session.send(
        "帮我查询任务状态"
    )

    assert (
        first.finish_reason
        == "needs_clarification"
    )
    assert "任务 ID" in first.answer
    assert first.tool_steps == ()
    assert (
        session.state.waiting_for_clarification
        is True
    )

    second = session.send("TASK-1001")

    assert second.finish_reason == "completed"
    assert len(second.tool_steps) == 1
    assert (
        second.tool_steps[0].tool_name
        == "query_status"
    )
    assert second.tool_steps[0].result.ok is True
    assert session.state.turn_count == 2
    assert (
        session.state.waiting_for_clarification
        is False
    )

    second_turn_model_input = (
        model.received_messages[1]
    )
    contents = [
        message.get("content")
        for message in second_turn_model_input
    ]

    assert any(
        isinstance(content, str)
        and "任务 ID" in content
        for content in contents
    )