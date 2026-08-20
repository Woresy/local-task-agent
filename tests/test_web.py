"""本地 WebApplication 测试。"""

from typing import cast
from unittest.mock import Mock

import pytest

from app.agent.models import AgentRunResult
from app.errors import UserInputError
from app.session import ConversationSession
from app.session.models import SessionState
from app.web import STATIC_ROOT, WebApplication


def make_web_application(
) -> tuple[WebApplication, Mock]:
    session = Mock(spec=ConversationSession)
    state = SessionState(
        session_id="web-test",
        messages=(
            {
                "role": "system",
                "content": "测试 system prompt",
            },
        ),
    )
    session.state = state
    session.send.return_value = AgentRunResult(
        answer="任务状态已返回。",
        finish_reason="completed",
        model_rounds=2,
    )
    session.reset.return_value = state

    return (
        WebApplication(
            cast(ConversationSession, session)
        ),
        session,
    )


def test_web_chat_returns_agent_result() -> None:
    application, session = make_web_application()

    payload = application.chat(
        {"message": "查询 TASK-1001"}
    )

    session.send.assert_called_once_with(
        "查询 TASK-1001"
    )
    assert payload["answer"] == "任务状态已返回。"
    assert payload["finish_reason"] == "completed"
    assert payload["state"]["session_id"] == "web-test"


@pytest.mark.parametrize(
    "payload",
    [None, [], "message", {"message": 1001}],
)
def test_web_chat_rejects_invalid_payload(
    payload: object,
) -> None:
    application, session = make_web_application()

    with pytest.raises(UserInputError):
        application.chat(payload)

    session.send.assert_not_called()


def test_web_state_returns_session_snapshot() -> None:
    application, _ = make_web_application()

    payload = application.state()

    assert payload["session_id"] == "web-test"
    assert payload["turn_count"] == 0


def test_web_reset_delegates_to_session() -> None:
    application, session = make_web_application()

    payload = application.reset()

    session.reset.assert_called_once_with()
    assert payload["message_count"] == 1


def test_web_static_assets_exist() -> None:
    assert (STATIC_ROOT / "index.html").is_file()
    assert (STATIC_ROOT / "styles.css").is_file()
    assert (STATIC_ROOT / "app.js").is_file()
