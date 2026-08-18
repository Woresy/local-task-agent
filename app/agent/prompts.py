"""真实 tool calling Agent 使用的提示词。"""

from openai.types.chat import (
    ChatCompletionMessageParam,
)

from app.errors import UserInputError
from app.prompts import MAX_USER_TEXT_LENGTH


AGENT_SYSTEM_PROMPT = """
你是一个本地任务型 AI 助手。

你只支持以下任务：

1. 查询业务指标；
2. 查询任务状态；
3. 为结构化数据创建摘要；
4. 回答简短的系统使用问题。

执行规则：

- 需要业务数据时必须调用对应工具，不得编造结果。
- 不得声称执行了未实际调用的工具。
- 不得调用工具列表之外的名称。
- 不得猜测用户没有提供的工具参数。
- 参数不足时直接向用户询问缺失信息。
- 一次模型响应最多请求一个工具。
- 收到 tool message 后，根据真实工具结果回答。
- 工具返回失败时明确说明失败原因。
- 对陪聊、角色扮演及范围外操作，说明当前系统不支持。
""".strip()


def normalize_agent_user_text(
    user_text: str,
) -> str:
    """校验并规范化一条用户输入。"""

    if not isinstance(user_text, str):
        raise UserInputError(
            "Agent 输入必须是字符串。"
        )

    normalized = user_text.strip()

    if not normalized:
        raise UserInputError(
            "Agent 输入不能为空。"
        )

    if len(normalized) > MAX_USER_TEXT_LENGTH:
        raise UserInputError(
            "Agent 输入不能超过 "
            f"{MAX_USER_TEXT_LENGTH} 个字符。"
        )

    return normalized


def build_agent_system_message(
) -> ChatCompletionMessageParam:
    """构造 Agent system message。"""

    return {
        "role": "system",
        "content": AGENT_SYSTEM_PROMPT,
    }


def build_agent_user_message(
    user_text: str,
) -> ChatCompletionMessageParam:
    """构造一条经过校验的 user message。"""

    return {
        "role": "user",
        "content": normalize_agent_user_text(
            user_text
        ),
    }


def build_agent_messages(
    user_text: str,
) -> list[ChatCompletionMessageParam]:
    """构造不带历史记录的单轮初始 messages。"""

    return [
        build_agent_system_message(),
        build_agent_user_message(user_text),
    ]