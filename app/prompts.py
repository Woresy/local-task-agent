"""普通聊天阶段的 system prompt 与 messages。"""

from openai.types.chat import ChatCompletionMessageParam

from app.errors import UserInputError


MAX_USER_TEXT_LENGTH = 8000

SYSTEM_PROMPT = """
你是一个简洁、可靠的任务型 AI 助手。

当前版本只支持普通聊天：
- 使用清晰的中文回答。
- 不虚构已经执行过的外部操作。
- 如果用户要求查询指标、查询状态或创建摘要，
  明确说明工具功能尚未接入。
""".strip()


def build_messages(
    user_text: str,
) -> list[ChatCompletionMessageParam]:
    """构造普通单轮聊天的 messages。"""

    normalized = user_text.strip()

    if not normalized:
        raise UserInputError("用户输入不能为空。")

    if len(normalized) > MAX_USER_TEXT_LENGTH:
        raise UserInputError(
            f"用户输入不能超过 {MAX_USER_TEXT_LENGTH} 个字符。"
        )

    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": normalized,
        },
    ]