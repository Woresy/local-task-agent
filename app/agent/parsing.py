"""解析模型 function call 中的 arguments。"""

import json

from app.errors import AgentProtocolError
from app.tools.models import JSONValue


def parse_tool_arguments(
    arguments_json: str,
) -> dict[str, JSONValue]:
    """把 function.arguments 解析成 JSON object。"""

    if not isinstance(arguments_json, str):
        raise AgentProtocolError(
            "tool arguments 必须是字符串。"
        )

    try:
        payload = json.loads(arguments_json)
    except json.JSONDecodeError as exc:
        raise AgentProtocolError(
            "模型返回了非法的 tool arguments JSON。"
        ) from exc

    if not isinstance(payload, dict):
        raise AgentProtocolError(
            "tool arguments 顶层必须是 JSON object。"
        )

    if not all(
        isinstance(name, str)
        for name in payload
    ):
        raise AgentProtocolError(
            "tool arguments 的字段名必须是字符串。"
        )

    return payload