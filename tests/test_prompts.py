"""system prompt 与 messages 测试。"""

import pytest

from app.errors import UserInputError
from app.prompts import SYSTEM_PROMPT, build_messages


def test_build_messages_preserves_role_order() -> None:
    messages = build_messages("查询任务状态")

    assert messages == [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": "查询任务状态",
        },
    ]


@pytest.mark.parametrize(
    "user_text",
    ["", " ", "\n\t"],
)
def test_build_messages_rejects_blank_text(
    user_text: str,
) -> None:
    with pytest.raises(
        UserInputError,
        match="不能为空",
    ):
        build_messages(user_text)