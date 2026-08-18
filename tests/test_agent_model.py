"""带 tools 的模型调用测试。"""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.agent import (
    OpenAICompatibleAgentModel,
)
from app.errors import ProviderResponseError


def test_agent_model_parses_text_reply(
    sdk_client: Mock,
) -> None:
    sdk_client.chat.completions.create.return_value = (
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    finish_reason="stop",
                    message=SimpleNamespace(
                        content="你好，需要查询什么？",
                        tool_calls=None,
                    ),
                )
            ]
        )
    )

    model = OpenAICompatibleAgentModel(
        client=sdk_client,
        model="test-model",
    )

    reply = model.complete(
        [
            {
                "role": "user",
                "content": "你好",
            }
        ]
    )

    assert reply.content == "你好，需要查询什么？"
    assert reply.tool_calls == ()

    call_kwargs = (
        sdk_client.chat.completions.create
        .call_args.kwargs
    )
    assert call_kwargs["tool_choice"] == "auto"
    assert len(call_kwargs["tools"]) == 3


def test_agent_model_parses_tool_call(
    sdk_client: Mock,
) -> None:
    sdk_client.chat.completions.create.return_value = (
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    finish_reason="tool_calls",
                    message=SimpleNamespace(
                        content=None,
                        tool_calls=[
                            SimpleNamespace(
                                id="call-1",
                                function=SimpleNamespace(
                                    name="query_status",
                                    arguments=(
                                        '{"id":"TASK-1001"}'
                                    ),
                                ),
                            )
                        ],
                    ),
                )
            ]
        )
    )

    model = OpenAICompatibleAgentModel(
        client=sdk_client,
        model="test-model",
    )

    reply = model.complete(
        [
            {
                "role": "user",
                "content": "查询 TASK-1001",
            }
        ]
    )

    assert reply.content is None
    assert len(reply.tool_calls) == 1
    assert reply.tool_calls[0].call_id == "call-1"
    assert reply.tool_calls[0].name == "query_status"
    assert (
        reply.tool_calls[0].arguments_json
        == '{"id":"TASK-1001"}'
    )


def test_agent_model_rejects_empty_response(
    sdk_client: Mock,
) -> None:
    sdk_client.chat.completions.create.return_value = (
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    finish_reason="stop",
                    message=SimpleNamespace(
                        content=None,
                        tool_calls=None,
                    ),
                )
            ]
        )
    )

    model = OpenAICompatibleAgentModel(
        client=sdk_client,
        model="test-model",
    )

    with pytest.raises(
        Exception,
        match="空响应",
    ):
        model.complete(
            [
                {
                    "role": "user",
                    "content": "你好",
                }
            ]
        )


def test_agent_model_rejects_empty_choices(
    sdk_client: Mock,
) -> None:
    sdk_client.chat.completions.create.return_value = (
        SimpleNamespace(choices=[])
    )

    model = OpenAICompatibleAgentModel(
        client=sdk_client,
        model="test-model",
    )

    with pytest.raises(
        ProviderResponseError,
        match="没有 choices",
    ):
        model.complete(
            [
                {
                    "role": "user",
                    "content": "你好",
                }
            ]
        )