"""OpenAI-compatible Agent 模型调用。"""

import logging
from collections.abc import Sequence
from typing import Protocol

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    OpenAIError,
    RateLimitError,
)
from openai.types.chat import (
    ChatCompletionMessageParam,
)

from app.agent.models import (
    AgentModelReply,
    ModelToolCall,
)
from app.errors import (
    AgentProtocolError,
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderTimeoutError,
)
from app.tools.definitions import TOOL_DEFINITIONS


logger = logging.getLogger(__name__)


class AgentModel(Protocol):
    """AgentRunner 依赖的模型接口。"""

    def complete(
        self,
        messages: Sequence[
            ChatCompletionMessageParam
        ],
    ) -> AgentModelReply:
        """根据当前 messages 返回文本或 tool calls."""


class OpenAICompatibleAgentModel:
    """通过 Chat Completions tools 调用模型。"""

    def __init__(
        self,
        client: OpenAI,
        model: str,
        max_tokens: int = 1024,
    ) -> None:
        if not model.strip():
            raise ValueError(
                "model 不能为空。"
            )

        if max_tokens <= 0:
            raise ValueError(
                "max_tokens 必须大于 0。"
            )

        self._client = client
        self._model = model
        self._max_tokens = max_tokens

    def complete(
        self,
        messages: Sequence[
            ChatCompletionMessageParam
        ],
    ) -> AgentModelReply:
        """调用一次带 function schema 的模型。"""

        logger.info(
            "发送 Agent 模型请求：model=%s "
            "message_count=%d",
            self._model,
            len(messages),
        )

        try:
            response = (
                self._client.chat.completions.create(
                    model=self._model,
                    messages=list(messages),
                    tools=list(TOOL_DEFINITIONS),
                    tool_choice="auto",
                    max_tokens=self._max_tokens,
                    extra_body={
                        "thinking":{
                            "type": "disabled"
                        }
                    },
                )
            )
        except APITimeoutError as exc:
            raise ProviderTimeoutError(
                "Agent 模型响应超时，请稍后重试。"
            ) from exc
        except AuthenticationError as exc:
            raise ProviderAuthenticationError(
                "Agent 模型认证失败，请检查 API Key。"
            ) from exc
        except RateLimitError as exc:
            raise ProviderRateLimitError(
                "Agent 请求触发限流或额度不足。"
            ) from exc
        except APIConnectionError as exc:
            raise ProviderConnectionError(
                "无法连接 Agent 模型 Provider。"
            ) from exc
        except APIStatusError as exc:
            request_id = (
                getattr(exc, "request_id", None)
                or "unknown"
            )

            if exc.status_code == 402:
                raise ProviderRateLimitError(
                    "模型账户余额不足。"
                ) from exc

            raise ProviderResponseError(
                "Agent 模型服务返回异常，"
                f"HTTP {exc.status_code}，"
                f"request_id={request_id}。"
            ) from exc
        except OpenAIError as exc:
            raise ProviderResponseError(
                "Agent 模型 SDK 返回未分类异常。"
            ) from exc

        choices = getattr(response, "choices", None)
        if not choices:
            raise ProviderResponseError(
                "Agent 模型响应中没有 choices。"
            )

        choice = choices[0]

        if getattr(choice, "finish_reason", None) == "length":
            raise ProviderResponseError(
                "Agent 模型响应因长度限制被截断。"
            )

        message = getattr(choice, "message", None)
        if message is None:
            raise ProviderResponseError(
                "Agent 模型响应中没有 message。"
            )

        raw_content = getattr(
            message,
            "content",
            None,
        )
        content = (
            raw_content.strip()
            if isinstance(raw_content, str)
            and raw_content.strip()
            else None
        )

        raw_tool_calls = (
            getattr(message, "tool_calls", None)
            or []
        )

        tool_calls: list[ModelToolCall] = []

        for raw_tool_call in raw_tool_calls:
            call_id = getattr(
                raw_tool_call,
                "id",
                None,
            )
            function = getattr(
                raw_tool_call,
                "function",
                None,
            )
            name = getattr(
                function,
                "name",
                None,
            )
            arguments_json = getattr(
                function,
                "arguments",
                None,
            )

            if not isinstance(call_id, str):
                raise AgentProtocolError(
                    "模型 tool call 缺少 id。"
                )

            if not isinstance(name, str):
                raise AgentProtocolError(
                    "模型 tool call 缺少函数名称。"
                )

            if not isinstance(arguments_json, str):
                raise AgentProtocolError(
                    "模型 tool call 缺少 arguments。"
                )

            tool_calls.append(
                ModelToolCall(
                    call_id=call_id,
                    name=name,
                    arguments_json=arguments_json,
                )
            )

        try:
            return AgentModelReply(
                content=content,
                tool_calls=tuple(tool_calls),
            )
        except ValueError as exc:
            raise AgentProtocolError(
                "Agent 模型返回了空响应。"
            ) from exc