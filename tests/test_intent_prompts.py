"""意图识别 messages 测试。"""

import pytest

from app.errors import UserInputError
from app.intent.models import ALLOWED_INTENTS
from app.intent.prompts import build_intent_messages

def test_build_intent_messages_normalizes_user_text() -> None:
    messages = build_intent_messages(
        " \n 查询 active_users \n "
    )

    assert messages[1]["content"] == "查询 active_users"


def test_build_intent_messages_rejects_non_string() -> None:
    with pytest.raises(
        UserInputError,
        match="必须是字符串",
    ):
        build_intent_messages(None)  # type: ignore[arg-type]

def test_intent_messages_have_system_and_user_roles() -> None:
    messages = build_intent_messages(
        "查询 active_users"
    )

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1] == {
        "role": "user",
        "content": "查询 active_users",
    }


def test_system_message_contains_json_protocol() -> None:
    messages = build_intent_messages(
        "查询 active_users"
    )
    system_content = messages[0]["content"]

    assert isinstance(system_content, str)
    assert "JSON" in system_content

    for intent in ALLOWED_INTENTS:
        assert intent in system_content


@pytest.mark.parametrize(
    "user_text",
    ["", " ", "\n\t"],
)
def test_intent_messages_reject_blank_input(
    user_text: str,
) -> None:
    with pytest.raises(
        UserInputError,
        match="不能为空",
    ):
        build_intent_messages(user_text)