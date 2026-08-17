"""OpenAI-compatible 模型客户端。"""

import logging
from collections.abc import Sequence

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    OpenAIError,
    RateLimitError,
)
from openai.types.chat import ChatCompletionMessageParam

from app.config import Settings
from app.errors import (
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderTimeoutError,
)
from app.prompts import build_messages


logger = logging.getLogger(__name__)


def create_client(settings: Settings) -> OpenAI:
    """根据配置创建 OpenAI-compatible 客户端。"""

    return OpenAI(
        api_key=settings.api_key,
        base_url=settings.base_url,
        timeout=settings.timeout,
        max_retries=settings.max_retries,
    )


def chat_once(
    client: OpenAI,
    model: str,
    messages: Sequence[ChatCompletionMessageParam],
) -> str:
    """执行一次不带 tools 的 Chat Completions 请求。"""

    logger.info(
        "发送普通聊天请求：model=%s message_count=%d",
        model,
        len(messages),
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=list(messages),
        )
    except APITimeoutError as exc:
        raise ProviderTimeoutError(
            "模型响应超时，请检查网络或稍后重试。"
        ) from exc
    except AuthenticationError as exc:
        raise ProviderAuthenticationError(
            "API 身份验证失败，请检查 API Key。"
        ) from exc
    except RateLimitError as exc:
        raise ProviderRateLimitError(
            "请求过于频繁或账户额度不足，请稍后重试。"
        ) from exc
    except APIConnectionError as exc:
        raise ProviderConnectionError(
            "无法连接 DeepSeek，请检查网络和 Base URL。"
        ) from exc
    except APIStatusError as exc:
        request_id = (
            getattr(exc, "request_id", None) or "unknown"
        )

        if exc.status_code == 402:
            raise ProviderRateLimitError(
                "DeepSeek API 账户余额不足，请检查余额。"
            ) from exc

        raise ProviderResponseError(
            "模型服务返回异常，"
            f"HTTP {exc.status_code}，"
            f"request_id={request_id}。"
        ) from exc
    except OpenAIError as exc:
        raise ProviderResponseError(
            "模型 SDK 返回未分类异常，请查看日志。"
        ) from exc

    choices = getattr(response, "choices", None)
    if not choices:
        raise ProviderResponseError(
            "模型响应中没有 choices。"
        )

    message = getattr(choices[0], "message", None)
    if message is None:
        raise ProviderResponseError(
            "模型响应中没有 assistant message。"
        )

    content = getattr(message, "content", None)
    if not isinstance(content, str) or not content.strip():
        raise ProviderResponseError(
            "模型响应中没有可显示的文本。"
        )

    logger.info("普通聊天请求完成")
    return content.strip()


def ask_once(
    client: OpenAI,
    model: str,
    prompt: str,
) -> str:
    """从用户文本构造 messages 并执行一次聊天。"""

    messages = build_messages(prompt)
    return chat_once(
        client=client,
        model=model,
        messages=messages,
    )