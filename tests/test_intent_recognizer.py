"""IntentRecognizer 测试。"""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.errors import IntentRecognitionError
from app.intent.recognizer import IntentRecognizer


def test_recognizer_returns_parsed_result(
    sdk_client: Mock,
) -> None:
    sdk_client.chat.completions.create.return_value = (
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    finish_reason="stop",
                    message=SimpleNamespace(
                        content="""
                        {
                          "intent": "query_status",
                          "arguments": {
                            "id": "TASK-1001"
                          },
                          "confidence": 0.96,
                          "reason": "用户询问具体任务状态"
                        }
                        """
                    ),
                )
            ]
        )
    )

    recognizer = IntentRecognizer(
        client=sdk_client,
        model="test-model",
    )

    result = recognizer.recognize(
        "TASK-1001 现在是什么状态"
    )

    assert result.intent == "query_status"
    assert result.arguments == {
        "id": "TASK-1001",
    }

    call_kwargs = (
        sdk_client.chat.completions.create
        .call_args.kwargs
    )

    assert call_kwargs["model"] == "test-model"
    assert call_kwargs["response_format"] == {
        "type": "json_object",
    }
    assert call_kwargs["max_tokens"] == 512
    assert call_kwargs["extra_body"] == {
        "thinking": {
            "type": "disabled",
        }
    }


def test_recognizer_rejects_empty_choices(
    sdk_client: Mock,
) -> None:
    sdk_client.chat.completions.create.return_value = (
        SimpleNamespace(choices=[])
    )

    recognizer = IntentRecognizer(
        client=sdk_client,
        model="test-model",
    )

    with pytest.raises(
        IntentRecognitionError,
        match="没有 choices",
    ):
        recognizer.recognize("你好")


def test_recognizer_rejects_truncated_json(
    sdk_client: Mock,
) -> None:
    sdk_client.chat.completions.create.return_value = (
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    finish_reason="length",
                    message=SimpleNamespace(
                        content='{"intent":',
                    ),
                )
            ]
        )
    )

    recognizer = IntentRecognizer(
        client=sdk_client,
        model="test-model",
    )

    with pytest.raises(
        IntentRecognitionError,
        match="截断",
    ):
        recognizer.recognize("查询任务状态")


def test_recognizer_rejects_empty_content(
    sdk_client: Mock,
) -> None:
    sdk_client.chat.completions.create.return_value = (
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    finish_reason="stop",
                    message=SimpleNamespace(
                        content="",
                    ),
                )
            ]
        )
    )

    recognizer = IntentRecognizer(
        client=sdk_client,
        model="test-model",
    )

    with pytest.raises(
        IntentRecognitionError,
        match="空内容",
    ):
        recognizer.recognize("你好")