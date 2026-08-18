"""AgentRunner tool loop 测试。"""

from collections.abc import Sequence
from typing import cast
from unittest.mock import Mock

import pytest
from openai.types.chat import (
    ChatCompletionMessageParam,
)

from app.agent import (
    AgentModelReply,
    AgentRunner,
    ModelToolCall,
)
from app.agent.model import AgentModel
from app.errors import (
    AgentLoopLimitError,
    AgentProtocolError,
    UnknownToolError,
)
from app.execution import ToolRouter
from app.tools.models import ToolName


class FakeAgentModel:
    """按顺序返回预设模型响应。"""

    def __init__(
        self,
        replies: list[AgentModelReply],
    ) -> None:
        self._replies = list(replies)
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

        if not self._replies:
            raise AssertionError(
                "FakeAgentModel 没有剩余响应。"
            )

        return self._replies.pop(0)


def test_plain_text_reply_finishes_without_tool() -> None:
    model = FakeAgentModel(
        [
            AgentModelReply(
                content="你好，需要查询什么？",
            )
        ]
    )
    tool = Mock()
    runner = AgentRunner(
        model=cast(AgentModel, model),
        router=ToolRouter(
            registry={
                "lookup_metric": tool,
            }
        ),
    )

    result = runner.run("你好")

    assert result.finish_reason == "completed"
    assert result.answer == "你好，需要查询什么？"
    assert result.model_rounds == 1
    assert result.tool_steps == ()
    tool.assert_not_called()


def test_tool_result_is_returned_to_model() -> None:
    model = FakeAgentModel(
        [
            AgentModelReply(
                content=None,
                tool_calls=(
                    ModelToolCall(
                        call_id="call-1",
                        name="query_status",
                        arguments_json=(
                            '{"id":"TASK-1001"}'
                        ),
                    ),
                ),
            ),
            AgentModelReply(
                content=(
                    "TASK-1001 正在运行，"
                    "当前进度为 65%。"
                ),
            ),
        ]
    )
    runner = AgentRunner(
        model=cast(AgentModel, model),
        router=ToolRouter(),
    )

    result = runner.run(
        "TASK-1001 现在是什么状态？"
    )

    assert result.finish_reason == "completed"
    assert result.model_rounds == 2
    assert len(result.tool_steps) == 1
    assert (
        result.tool_steps[0].tool_name
        == "query_status"
    )
    assert result.tool_steps[0].result.ok is True

    second_request = model.received_messages[1]
    assert [
        message["role"]
        for message in second_request
    ] == [
        "system",
        "user",
        "assistant",
        "tool",
    ]


def test_missing_argument_returns_question() -> None:
    tool = Mock()
    model = FakeAgentModel(
        [
            AgentModelReply(
                content=None,
                tool_calls=(
                    ModelToolCall(
                        call_id="call-1",
                        name="query_status",
                        arguments_json="{}",
                    ),
                ),
            )
        ]
    )
    runner = AgentRunner(
        model=cast(AgentModel, model),
        router=ToolRouter(
            registry={
                "query_status": tool,
            }
        ),
    )

    result = runner.run(
        "帮我查询任务状态"
    )

    assert (
        result.finish_reason
        == "needs_clarification"
    )
    assert "任务 ID" in result.answer
    assert result.tool_steps == ()
    tool.assert_not_called()


def test_invalid_argument_does_not_execute() -> None:
    tool = Mock()
    model = FakeAgentModel(
        [
            AgentModelReply(
                content=None,
                tool_calls=(
                    ModelToolCall(
                        call_id="call-1",
                        name="query_status",
                        arguments_json='{"id":1001}',
                    ),
                ),
            )
        ]
    )
    runner = AgentRunner(
        model=cast(AgentModel, model),
        router=ToolRouter(
            registry={
                "query_status": tool,
            }
        ),
    )

    result = runner.run(
        "查询任务状态"
    )

    assert (
        result.finish_reason
        == "invalid_arguments"
    )
    assert "id" in result.answer
    tool.assert_not_called()


def test_unknown_tool_is_not_executed() -> None:
    allowed_tool = Mock()
    model = FakeAgentModel(
        [
            AgentModelReply(
                content=None,
                tool_calls=(
                    ModelToolCall(
                        call_id="call-1",
                        name="delete_database",
                        arguments_json="{}",
                    ),
                ),
            )
        ]
    )
    runner = AgentRunner(
        model=cast(AgentModel, model),
        router=ToolRouter(
            registry={
                "lookup_metric": allowed_tool,
            }
        ),
    )

    with pytest.raises(UnknownToolError):
        runner.run("删除数据库")

    allowed_tool.assert_not_called()


def test_multiple_tool_calls_are_rejected() -> None:
    tool = Mock()
    model = FakeAgentModel(
        [
            AgentModelReply(
                content=None,
                tool_calls=(
                    ModelToolCall(
                        call_id="call-1",
                        name="lookup_metric",
                        arguments_json=(
                            '{"name":"active_users"}'
                        ),
                    ),
                    ModelToolCall(
                        call_id="call-2",
                        name="query_status",
                        arguments_json=(
                            '{"id":"TASK-1001"}'
                        ),
                    ),
                ),
            )
        ]
    )
    runner = AgentRunner(
        model=cast(AgentModel, model),
        router=ToolRouter(
            registry={
                "lookup_metric": tool,
                "query_status": tool,
            }
        ),
    )

    with pytest.raises(AgentProtocolError):
        runner.run("同时查询两个数据")

    tool.assert_not_called()


def test_repeated_tool_calls_reach_loop_limit() -> None:
    model = FakeAgentModel(
        [
            AgentModelReply(
                content=None,
                tool_calls=(
                    ModelToolCall(
                        call_id="call-1",
                        name="lookup_metric",
                        arguments_json=(
                            '{"name":"active_users"}'
                        ),
                    ),
                ),
            )
        ]
    )
    runner = AgentRunner(
        model=cast(AgentModel, model),
        router=ToolRouter(),
        max_model_rounds=1,
    )

    with pytest.raises(AgentLoopLimitError):
        runner.run("查询 active_users")

def test_run_messages_returns_final_history() -> None:
    model = FakeAgentModel(
        [
            AgentModelReply(
                content="已收到第二轮问题。",
            )
        ]
    )
    runner = AgentRunner(
        model=cast(AgentModel, model),
        router=ToolRouter(),
    )

    outcome = runner.run_messages(
        [
            {
                "role": "system",
                "content": "测试系统提示",
            },
            {
                "role": "user",
                "content": "第一轮问题",
            },
            {
                "role": "assistant",
                "content": "第一轮回答",
            },
            {
                "role": "user",
                "content": "第二轮问题",
            },
        ]
    )

    assert outcome.result.answer == (
        "已收到第二轮问题。"
    )
    assert [
        message["role"]
        for message in outcome.messages
    ] == [
        "system",
        "user",
        "assistant",
        "user",
        "assistant",
    ]