"""三个本地工具的实现。"""

import json

from app.tools.data import (
    METRIC_STORE,
    STATUS_STORE,
)
from app.tools.models import (
    JSONValue,
    ToolResult,
)


def lookup_metric(name: str) -> ToolResult:
    """按名称查询本地业务指标。"""

    normalized_name = name.strip().lower()

    if not normalized_name:
        return ToolResult.failure(
            tool_name="lookup_metric",
            code="invalid_input",
            message="指标名称不能为空。",
        )

    metric = METRIC_STORE.get(normalized_name)
    if metric is None:
        return ToolResult.failure(
            tool_name="lookup_metric",
            code="not_found",
            message=f"未找到指标：{normalized_name}",
        )

    return ToolResult.success(
        tool_name="lookup_metric",
        data=dict(metric),
    )


def query_status(id: str) -> ToolResult:
    """按任务 ID 查询本地任务状态。"""

    normalized_id = id.strip().upper()

    if not normalized_id:
        return ToolResult.failure(
            tool_name="query_status",
            code="invalid_input",
            message="任务 ID 不能为空。",
        )

    status = STATUS_STORE.get(normalized_id)
    if status is None:
        return ToolResult.failure(
            tool_name="query_status",
            code="not_found",
            message=f"未找到任务：{normalized_id}",
        )

    return ToolResult.success(
        tool_name="query_status",
        data=dict(status),
    )


def create_summary(
    data: dict[str, JSONValue],
) -> ToolResult:
    """为结构化数据生成确定性的本地摘要。"""

    if not isinstance(data, dict) or not data:
        return ToolResult.failure(
            tool_name="create_summary",
            code="invalid_input",
            message="摘要数据不能为空。",
        )

    if not all(
        isinstance(field, str)
        for field in data
    ):
        return ToolResult.failure(
            tool_name="create_summary",
            code="invalid_input",
            message="摘要数据的字段名必须是字符串。",
        )

    fields = sorted(data)

    try:
        serialized_values = {
            field: json.dumps(
                data[field],
                ensure_ascii=False,
                sort_keys=True,
                allow_nan=False,
            )
            for field in fields
        }
    except (TypeError, ValueError):
        return ToolResult.failure(
            tool_name="create_summary",
            code="invalid_input",
            message="摘要数据必须能够序列化为 JSON。",
        )

    summary = "; ".join(
        f"{field}={serialized_values[field]}"
        for field in fields
    )

    return ToolResult.success(
        tool_name="create_summary",
        data={
            "summary": summary,
            "field_count": len(fields),
            "fields": fields,
        },
    )