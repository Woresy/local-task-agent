"""意图 JSON parser 测试。"""

import pytest

from app.errors import IntentRecognitionError
from app.intent.parser import parse_intent_response


def test_parse_complete_intent_result() -> None:
    result = parse_intent_response(
        """
        {
          "intent": "lookup_metric",
          "arguments": {
            "name": "active_users"
          },
          "confidence": 0.98,
          "reason": "用户明确查询业务指标"
        }
        """
    )

    assert result.intent == "lookup_metric"
    assert result.arguments == {
        "name": "active_users",
    }
    assert result.confidence == 0.98


def test_parser_allows_incomplete_arguments() -> None:
    result = parse_intent_response(
        """
        {
          "intent": "query_status",
          "arguments": {},
          "confidence": 0.8,
          "reason": "用户想查询状态但没有提供 ID"
        }
        """
    )

    assert result.intent == "query_status"
    assert result.arguments == {}


def test_parser_rejects_invalid_json() -> None:
    with pytest.raises(
        IntentRecognitionError,
        match="合法 JSON",
    ):
        parse_intent_response(
            '{"intent": "general_chat"'
        )


def test_parser_rejects_unknown_intent() -> None:
    with pytest.raises(
        IntentRecognitionError,
        match="不支持的意图",
    ):
        parse_intent_response(
            """
            {
              "intent": "delete_database",
              "arguments": {},
              "confidence": 0.9,
              "reason": "测试未知意图"
            }
            """
        )


def test_parser_rejects_non_object_arguments() -> None:
    with pytest.raises(
        IntentRecognitionError,
        match="arguments",
    ):
        parse_intent_response(
            """
            {
              "intent": "query_status",
              "arguments": "TASK-1001",
              "confidence": 0.9,
              "reason": "错误参数结构"
            }
            """
        )


def test_parser_rejects_missing_field() -> None:
    with pytest.raises(
        IntentRecognitionError,
        match="缺少字段",
    ):
        parse_intent_response(
            """
            {
              "intent": "general_chat",
              "arguments": {},
              "confidence": 0.9
            }
            """
        )


def test_parser_rejects_extra_field() -> None:
    with pytest.raises(
        IntentRecognitionError,
        match="未知字段",
    ):
        parse_intent_response(
            """
            {
              "intent": "general_chat",
              "arguments": {},
              "confidence": 0.9,
              "reason": "普通聊天",
              "tool": null
            }
            """
        )


@pytest.mark.parametrize(
    "confidence",
    [-1, 2, True, "high"],
)
def test_parser_rejects_invalid_confidence(
    confidence: object,
) -> None:
    import json

    payload = {
        "intent": "general_chat",
        "arguments": {},
        "confidence": confidence,
        "reason": "普通聊天",
    }

    with pytest.raises(
        IntentRecognitionError,
        match="confidence",
    ):
        parse_intent_response(
            json.dumps(payload)
        )