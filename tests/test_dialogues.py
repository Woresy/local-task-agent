"""任务型 Agent 的端到端对话验收测试。"""

import json
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
    AgentProtocolError,
    ProviderTimeoutError,
    UnknownToolError,
)
from app.execution import ToolRouter
from app.session import ConversationSession
from app.tools.models import ToolResult


ScriptedEvent = AgentModelReply | Exception


class ScriptedAgentModel:
    """按顺序返回文本、tool call 或异常。"""

    def __init__(
        self,
        events: list[ScriptedEvent],
    ) -> None:
        self._events = list(events)
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

        if not self._events:
            raise AssertionError(
                "ScriptedAgentModel 没有剩余事件。"
            )

        event = self._events.pop(0)
        if isinstance(event, Exception):
            raise event

        return event


def make_tool_call(
    call_id: str,
    name: str,
    arguments_json: str,
) -> AgentModelReply:
    """构造只有一个 function call 的模型响应。"""

    return AgentModelReply(
        content=None,
        tool_calls=(
            ModelToolCall(
                call_id=call_id,
                name=name,
                arguments_json=arguments_json,
            ),
        ),
    )


def make_session(
    events: list[ScriptedEvent],
    router: ToolRouter | None = None,
) -> tuple[ConversationSession, ScriptedAgentModel]:
    """创建使用真实 AgentRunner 的测试会话。"""

    model = ScriptedAgentModel(events)
    runner = AgentRunner(
        model=cast(AgentModel, model),
        router=router or ToolRouter(),
    )
    return ConversationSession(runner), model


def test_dialogue_01_general_greeting_uses_no_tool(
) -> None:
    session, _ = make_session(
        [
            AgentModelReply(
                content="你好，我可以查询指标、任务状态或创建摘要。",
            )
        ]
    )

    result = session.send("你好")

    assert result.finish_reason == "completed"
    assert result.tool_steps == ()
    assert session.state.turn_count == 1


def test_dialogue_02_lookup_metric_succeeds(
) -> None:
    session, model = make_session(
        [
            make_tool_call(
                "metric-1",
                "lookup_metric",
                '{"name":"active_users"}',
            ),
            AgentModelReply(
                content="active_users 当前为 1280 users。",
            ),
        ]
    )

    result = session.send("查询 active_users")

    assert result.finish_reason == "completed"
    assert len(result.tool_steps) == 1
    step = result.tool_steps[0]
    assert step.tool_name == "lookup_metric"
    assert step.result.ok is True
    assert step.result.data is not None
    assert step.result.data["value"] == 1280

    tool_message = model.received_messages[1][-1]
    assert tool_message["role"] == "tool"
    assert tool_message["tool_call_id"] == "metric-1"


def test_dialogue_03_query_status_succeeds(
) -> None:
    session, _ = make_session(
        [
            make_tool_call(
                "status-1",
                "query_status",
                '{"id":"TASK-1001"}',
            ),
            AgentModelReply(
                content="TASK-1001 正在运行，进度为 65%。",
            ),
        ]
    )

    result = session.send(
        "TASK-1001 现在是什么状态？"
    )

    step = result.tool_steps[0]
    assert step.tool_name == "query_status"
    assert step.result.ok is True
    assert step.result.data is not None
    assert step.result.data["progress"] == 65


def test_dialogue_04_create_summary_succeeds(
) -> None:
    session, _ = make_session(
        [
            make_tool_call(
                "summary-1",
                "create_summary",
                '{"data":{"stage":7,"status":"done"}}',
            ),
            AgentModelReply(
                content="摘要已根据两个字段生成。",
            ),
        ]
    )

    result = session.send(
        '总结 {"stage":7,"status":"done"}'
    )

    step = result.tool_steps[0]
    assert step.tool_name == "create_summary"
    assert step.result.ok is True
    assert step.result.data is not None
    assert step.result.data["field_count"] == 2


def test_dialogue_05_tool_not_found_reaches_model(
) -> None:
    session, model = make_session(
        [
            make_tool_call(
                "metric-missing",
                "lookup_metric",
                '{"name":"missing_metric"}',
            ),
            AgentModelReply(
                content="没有找到 missing_metric 指标。",
            ),
        ]
    )

    result = session.send("查询 missing_metric")

    step = result.tool_steps[0]
    assert step.result.ok is False
    assert step.result.error is not None
    assert step.result.error.code == "not_found"

    tool_message = model.received_messages[1][-1]
    content = tool_message["content"]
    assert isinstance(content, str)
    assert json.loads(content)["error"]["code"] == "not_found"


def test_dialogue_06_missing_status_id_is_completed_next_turn(
) -> None:
    session, model = make_session(
        [
            make_tool_call(
                "status-missing",
                "query_status",
                "{}",
            ),
            make_tool_call(
                "status-complete",
                "query_status",
                '{"id":"TASK-1001"}',
            ),
            AgentModelReply(
                content="TASK-1001 正在运行，进度为 65%。",
            ),
        ]
    )

    first = session.send("查询任务状态")

    assert first.finish_reason == "needs_clarification"
    assert "任务 ID" in first.answer
    assert first.tool_steps == ()
    assert session.state.waiting_for_clarification is True

    second = session.send("TASK-1001")

    assert second.finish_reason == "completed"
    assert second.tool_steps[0].tool_name == "query_status"
    assert session.state.turn_count == 2
    assert session.state.waiting_for_clarification is False
    assert any(
        message.get("role") == "assistant"
        and isinstance(message.get("content"), str)
        and "任务 ID" in cast(str, message.get("content"))
        for message in model.received_messages[1]
    )


def test_dialogue_07_missing_metric_name_is_completed_next_turn(
) -> None:
    session, _ = make_session(
        [
            make_tool_call(
                "metric-missing",
                "lookup_metric",
                "{}",
            ),
            make_tool_call(
                "metric-complete",
                "lookup_metric",
                '{"name":"conversion_rate"}',
            ),
            AgentModelReply(
                content="conversion_rate 当前为 0.083。",
            ),
        ]
    )

    first = session.send("查询一个业务指标")
    second = session.send("conversion_rate")

    assert first.finish_reason == "needs_clarification"
    assert "指标名称" in first.answer
    assert second.tool_steps[0].tool_name == "lookup_metric"
    assert second.tool_steps[0].result.ok is True


def test_dialogue_08_missing_summary_data_is_completed_next_turn(
) -> None:
    session, _ = make_session(
        [
            make_tool_call(
                "summary-missing",
                "create_summary",
                "{}",
            ),
            make_tool_call(
                "summary-complete",
                "create_summary",
                '{"data":{"project":"agent"}}',
            ),
            AgentModelReply(
                content="已生成项目摘要。",
            ),
        ]
    )

    first = session.send("创建摘要")
    second = session.send(
        '{"project":"agent"}'
    )

    assert first.finish_reason == "needs_clarification"
    assert "结构化数据" in first.answer
    assert second.tool_steps[0].tool_name == "create_summary"
    assert second.tool_steps[0].result.ok is True


def test_dialogue_09_invalid_argument_does_not_execute(
) -> None:
    tool = Mock(
        return_value=ToolResult.success(
            tool_name="query_status",
            data={"unexpected": True},
        )
    )
    router = ToolRouter(
        registry={
            "query_status": tool,
        }
    )
    session, _ = make_session(
        [
            make_tool_call(
                "invalid-id",
                "query_status",
                '{"id":1001}',
            )
        ],
        router=router,
    )

    result = session.send("查询编号 1001")

    assert result.finish_reason == "invalid_arguments"
    assert "id" in result.answer
    assert result.tool_steps == ()
    tool.assert_not_called()


def test_dialogue_10_unknown_tool_failure_rolls_back(
) -> None:
    allowed_tool = Mock()
    router = ToolRouter(
        registry={
            "lookup_metric": allowed_tool,
        }
    )
    session, _ = make_session(
        [
            make_tool_call(
                "unknown-1",
                "delete_database",
                "{}",
            )
        ],
        router=router,
    )
    state_before = session.state

    with pytest.raises(UnknownToolError):
        session.send("删除数据库")

    assert session.state is state_before
    assert session.state.turn_count == 0
    allowed_tool.assert_not_called()


def test_dialogue_11_out_of_scope_request_is_refused(
) -> None:
    session, _ = make_session(
        [
            AgentModelReply(
                content="当前系统不支持角色扮演。",
            )
        ]
    )

    result = session.send("陪我进行角色扮演")

    assert result.finish_reason == "completed"
    assert "不支持" in result.answer
    assert result.tool_steps == ()


def test_dialogue_12_provider_timeout_rolls_back(
) -> None:
    session, _ = make_session(
        [ProviderTimeoutError("测试超时")]
    )
    state_before = session.state

    with pytest.raises(ProviderTimeoutError):
        session.send("查询 active_users")

    assert session.state is state_before
    assert session.state.turn_count == 0


def test_dialogue_13_multiple_tool_calls_roll_back(
) -> None:
    multiple_calls = AgentModelReply(
        content=None,
        tool_calls=(
            ModelToolCall(
                call_id="multi-1",
                name="lookup_metric",
                arguments_json=(
                    '{"name":"active_users"}'
                ),
            ),
            ModelToolCall(
                call_id="multi-2",
                name="query_status",
                arguments_json=(
                    '{"id":"TASK-1001"}'
                ),
            ),
        ),
    )
    session, _ = make_session([multiple_calls])
    state_before = session.state

    with pytest.raises(AgentProtocolError):
        session.send("同时查询指标和任务状态")

    assert session.state is state_before
    assert session.state.turn_count == 0
