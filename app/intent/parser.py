"""解析并验证模型返回的意图 JSON。"""

import json
from typing import cast

from app.errors import IntentRecognitionError
from app.intent.models import (
    ALLOWED_INTENTS,
    IntentName,
    IntentResult,
)


EXPECTED_FIELDS = {
    "intent",
    "arguments",
    "confidence",
    "reason",
}


def parse_intent_response(
    raw_content: str,
) -> IntentResult:
    """把模型文本解析为 IntentResult。"""

    if not isinstance(raw_content, str):
        raise IntentRecognitionError(
            "意图识别响应必须是字符串。"
        )

    normalized = raw_content.strip()
    if not normalized:
        raise IntentRecognitionError(
            "意图识别模型返回了空内容。"
        )

    try:
        payload = json.loads(normalized)
    except json.JSONDecodeError as exc:
        raise IntentRecognitionError(
            "意图识别模型没有返回合法 JSON。"
        ) from exc

    if not isinstance(payload, dict):
        raise IntentRecognitionError(
            "意图识别 JSON 顶层必须是 object。"
        )

    payload_fields = set(payload)
    missing_fields = EXPECTED_FIELDS - payload_fields
    extra_fields = payload_fields - EXPECTED_FIELDS

    if missing_fields:
        names = ", ".join(sorted(missing_fields))
        raise IntentRecognitionError(
            f"意图识别结果缺少字段：{names}"
        )

    if extra_fields:
        names = ", ".join(sorted(extra_fields))
        raise IntentRecognitionError(
            f"意图识别结果包含未知字段：{names}"
        )

    intent = payload["intent"]
    if (
        not isinstance(intent, str)
        or intent not in ALLOWED_INTENTS
    ):
        raise IntentRecognitionError(
            f"不支持的意图名称：{intent!r}"
        )

    arguments = payload["arguments"]
    if not isinstance(arguments, dict):
        raise IntentRecognitionError(
            "arguments 必须是 JSON object。"
        )

    if not all(
        isinstance(key, str)
        for key in arguments
    ):
        raise IntentRecognitionError(
            "arguments 的键必须是字符串。"
        )

    confidence = payload["confidence"]
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
    ):
        raise IntentRecognitionError(
            "confidence 必须是数字。"
        )

    normalized_confidence = float(confidence)
    if not 0 <= normalized_confidence <= 1:
        raise IntentRecognitionError(
            "confidence 必须在 0 到 1 之间。"
        )

    reason = payload["reason"]
    if not isinstance(reason, str) or not reason.strip():
        raise IntentRecognitionError(
            "reason 必须是非空字符串。"
        )

    if len(reason) > 500:
        raise IntentRecognitionError(
            "reason 不能超过 500 个字符。"
        )

    return IntentResult(
        intent=cast(IntentName, intent),
        arguments=dict(arguments),
        confidence=normalized_confidence,
        reason=reason.strip(),
    )