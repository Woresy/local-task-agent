"""通过 DeepSeek JSON mode 执行意图识别。"""

import logging

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    OpenAIError,
    RateLimitError,
)

from app.errors import (
    IntentRecognitionError,
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderTimeoutError,
)
from app.intent.models import IntentResult
from app.intent.parser import parse_intent_response
from app.intent.prompts import build_intent_messages


logger = logging.getLogger(__name__)


class IntentRecognizer:
    """将用户文本转换成结构化意图。"""

    def __init__(
        self,
        client: OpenAI,
        model: str,
        max_tokens: int = 512,
    ) -> None:
        if not model.strip():
            raise ValueError("model 不能为空。")

        if max_tokens <= 0:
            raise ValueError(
                "max_tokens 必须大于 0。"
            )

        self._client = client
        self._model = model
        self._max_tokens = max_tokens

    def recognize(
        self,
        user_text: str,
    ) -> IntentResult:
        """调用模型并解析结构化意图。"""

        messages = build_intent_messages(user_text)

        logger.info(
            "发送意图识别请求：model=%s",
            self._model,
        )

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                response_format={
                    "type": "json_object",
                },
                max_tokens=self._max_tokens,
                extra_body={
                    "thinking": {
                        "type": "disabled",
                    }
                },
            )
        except APITimeoutError as exc:
            raise ProviderTimeoutError(
                "意图识别请求超时，请稍后重试。"
            ) from exc
        except AuthenticationError as exc:
            raise ProviderAuthenticationError(
                "意图识别认证失败，请检查 API Key。"
            ) from exc
        except RateLimitError as exc:
            raise ProviderRateLimitError(
                "意图识别请求触发限流或额度不足。"
            ) from exc
        except APIConnectionError as exc:
            raise ProviderConnectionError(
                "无法连接意图识别模型。"
            ) from exc
        except APIStatusError as exc:
            request_id = (
                getattr(exc, "request_id", None)
                or "unknown"
            )
            raise ProviderResponseError(
                "意图识别服务返回异常，"
                f"HTTP {exc.status_code}，"
                f"request_id={request_id}。"
            ) from exc
        except OpenAIError as exc:
            raise ProviderResponseError(
                "意图识别 SDK 返回未分类异常。"
            ) from exc

        choices = getattr(response, "choices", None)
        if not choices:
            raise IntentRecognitionError(
                "意图识别响应中没有 choices。"
            )

        choice = choices[0]
        finish_reason = getattr(
            choice,
            "finish_reason",
            None,
        )

        if finish_reason == "length":
            raise IntentRecognitionError(
                "意图识别 JSON 被截断，请增加 max_tokens。"
            )

        message = getattr(choice, "message", None)
        if message is None:
            raise IntentRecognitionError(
                "意图识别响应中没有 assistant message。"
            )

        content = getattr(message, "content", None)
        if not isinstance(content, str) or not content.strip():
            raise IntentRecognitionError(
                "意图识别模型返回了空内容。"
            )

        result = parse_intent_response(content)

        logger.info(
            "意图识别完成：intent=%s confidence=%.2f",
            result.intent,
            result.confidence,
        )

        return result