"""IntentResult 测试。"""

import json

import pytest

from app.intent.models import IntentResult


def test_intent_result_serializes_to_json() -> None:
    result = IntentResult(
        intent="query_status",
        arguments={
            "id": "TASK-1001",
        },
        confidence=0.95,
        reason="用户询问具体任务状态",
    )

    payload = json.loads(result.to_json())

    assert payload == {
        "intent": "query_status",
        "arguments": {
            "id": "TASK-1001",
        },
        "confidence": 0.95,
        "reason": "用户询问具体任务状态",
    }


@pytest.mark.parametrize(
    "confidence",
    [-0.1, 1.1],
)
def test_intent_result_rejects_invalid_confidence(
    confidence: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="confidence",
    ):
        IntentResult(
            intent="general_chat",
            arguments={},
            confidence=confidence,
            reason="普通聊天",
        )