"""提供给 Chat Completions 的 function schema。"""

from openai.types.chat import ChatCompletionToolParam


LOOKUP_METRIC_DEFINITION: ChatCompletionToolParam = {
    "type": "function",
    "function": {
        "name": "lookup_metric",
        "description": (
            "按指标名称查询一个业务指标。"
            "只有用户明确要求查询指标、数值、比例或耗时时使用。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": (
                        "指标名称，例如 active_users、"
                        "conversion_rate 或 avg_response_ms。"
                    ),
                },
            },
            "required": ["name"],
            "additionalProperties": False,
        },
        "strict": False,
    },
}


QUERY_STATUS_DEFINITION: ChatCompletionToolParam = {
    "type": "function",
    "function": {
        "name": "query_status",
        "description": (
            "按任务 ID 查询任务当前状态和完成进度。"
            "只有用户询问具体任务状态时使用。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": (
                        "任务 ID，例如 TASK-1001。"
                    ),
                },
            },
            "required": ["id"],
            "additionalProperties": False,
        },
        "strict": False,
    },
}


CREATE_SUMMARY_DEFINITION: ChatCompletionToolParam = {
    "type": "function",
    "function": {
        "name": "create_summary",
        "description": (
            "为一组结构化数据生成简短摘要。"
            "输入必须是 JSON object。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "description": (
                        "需要概括的结构化键值数据。"
                    ),
                },
            },
            "required": ["data"],
            "additionalProperties": False,
        },
        "strict": False,
    },
}


TOOL_DEFINITIONS: tuple[
    ChatCompletionToolParam,
    ...,
] = (
    LOOKUP_METRIC_DEFINITION,
    QUERY_STATUS_DEFINITION,
    CREATE_SUMMARY_DEFINITION,
)