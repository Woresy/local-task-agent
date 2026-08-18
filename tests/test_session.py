"""短期 ConversationSession 测试。"""

from collections.abc import Sequence
from typing import cast

import pytest
from openai.types.chat import (
    ChatCompletionMessageParam,
)

from app.agent.models import (
    AgentRunOutcome,
    AgentRunResult,
)
from app.agent.runner import AgentRunner
from app.errors import ProviderTimeoutError
from app.session import ConversationSession


class FakeStatefulRunner:
    """返回预设回答并记录输入 messages。"""

    def __init__(
        self,
        answers: list[str],
    ) -> None:
        self._answers = list(answers)
        self.received_messages: list[
            list[ChatCompletionMessageParam]
        ] = []

    def run_messages(
        self,
        initial_messages: Sequence[
            ChatCompletionMessageParam
        ],
    ) -> AgentRunOutcome:
        messages = list(initial_messages)
        self.received_messages.append(
            list(messages)
        )

        answer = self._answers.pop(0)
        messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        return AgentRunOutcome(
            result=AgentRunResult(
                answer=answer,
                finish_reason="completed",
                model_rounds=1,
            ),
            messages=tuple(messages),
        )


class FailingRunner:
    """模拟一次 Provider 超时。"""

    def run_messages(
        self,
        initial_messages: Sequence[
            ChatCompletionMessageParam
        ],
    ) -> AgentRunOutcome:
        raise ProviderTimeoutError(
            "测试超时"
        )


def test_new_session_contains_only_system_message() -> None:
    runner = FakeStatefulRunner(["未使用"])
    session = ConversationSession(
        runner=cast(AgentRunner, runner),
        session_id="test-session",
    )

    assert session.state.session_id == "test-session"
    assert session.state.turn_count == 0
    assert session.state.message_count == 1
    assert session.state.messages[0]["role"] == "system"


def test_send_commits_user_and_assistant_messages() -> None:
    runner = FakeStatefulRunner(["第一轮回答"])
    session = ConversationSession(
        runner=cast(AgentRunner, runner),
    )

    result = session.send("第一轮问题")

    assert result.answer == "第一轮回答"
    assert session.state.turn_count == 1
    assert [
        message["role"]
        for message in session.state.messages
    ] == [
        "system",
        "user",
        "assistant",
    ]


def test_second_turn_receives_previous_history() -> None:
    runner = FakeStatefulRunner(
        [
            "第一轮回答",
            "第二轮回答",
        ]
    )
    session = ConversationSession(
        runner=cast(AgentRunner, runner),
    )

    session.send("第一轮问题")
    session.send("第二轮问题")

    second_input = runner.received_messages[1]

    assert [
        message["role"]
        for message in second_input
    ] == [
        "system",
        "user",
        "assistant",
        "user",
    ]
    assert session.state.turn_count == 2


def test_failed_turn_does_not_change_state() -> None:
    session = ConversationSession(
        runner=cast(
            AgentRunner,
            FailingRunner(),
        )
    )
    state_before = session.state

    with pytest.raises(ProviderTimeoutError):
        session.send("会超时的问题")

    assert session.state is state_before
    assert session.state.turn_count == 0
    assert session.state.message_count == 1


def test_reset_clears_conversation_history() -> None:
    runner = FakeStatefulRunner(["回答"])
    session = ConversationSession(
        runner=cast(AgentRunner, runner),
        session_id="keep-this-id",
    )
    session.send("问题")

    state = session.reset()

    assert state.session_id == "keep-this-id"
    assert state.turn_count == 0
    assert state.message_count == 1
    assert state.last_finish_reason is None
    assert state.messages[0]["role"] == "system"