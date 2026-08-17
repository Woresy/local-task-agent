"""模型客户端测试。"""

from types import SimpleNamespace
from unittest.mock import Mock

import httpx2
import pytest
from openai import APITimeoutError

from app.config import Settings
from app.errors import (
    ProviderResponseError,
    ProviderTimeoutError,
)
from app.llm_client import chat_once


def test_chat_once_returns_text(
    settings: Settings,
    sdk_client: Mock,
) -> None:
    sdk_client.chat.completions.create.return_value = (
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="  模型已连通。  "
                    )
                )
            ]
        )
    )

    result = chat_once(
        client=sdk_client,
        model=settings.model,
        messages=[
            {
                "role": "user",
                "content": "你好",
            }
        ],
    )

    assert result == "模型已连通。"
    sdk_client.chat.completions.create.assert_called_once_with(
        model="test-model",
        messages=[
            {
                "role": "user",
                "content": "你好",
            }
        ],
    )


def test_chat_once_rejects_empty_choices(
    settings: Settings,
    sdk_client: Mock,
) -> None:
    sdk_client.chat.completions.create.return_value = (
        SimpleNamespace(choices=[])
    )

    with pytest.raises(
        ProviderResponseError,
        match="没有 choices",
    ):
        chat_once(
            client=sdk_client,
            model=settings.model,
            messages=[
                {
                    "role": "user",
                    "content": "你好",
                }
            ],
        )


@pytest.mark.parametrize(
    "content",
    [None, "", "   "],
)
def test_chat_once_rejects_empty_content(
    content: str | None,
    settings: Settings,
    sdk_client: Mock,
) -> None:
    sdk_client.chat.completions.create.return_value = (
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=content)
                )
            ]
        )
    )

    with pytest.raises(
        ProviderResponseError,
        match="没有可显示的文本",
    ):
        chat_once(
            client=sdk_client,
            model=settings.model,
            messages=[
                {
                    "role": "user",
                    "content": "你好",
                }
            ],
        )


def test_chat_once_translates_timeout(
    settings: Settings,
    sdk_client: Mock,
) -> None:
    sdk_client.chat.completions.create.side_effect = (
        APITimeoutError(
            request=httpx2.Request(
                "POST",
                "https://example.com/chat/completions",
            )
        )
    )

    with pytest.raises(
        ProviderTimeoutError,
        match="响应超时",
    ):
        chat_once(
            client=sdk_client,
            model=settings.model,
            messages=[
                {
                    "role": "user",
                    "content": "你好",
                }
            ],
        )