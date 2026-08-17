"""工具名称、Python 函数和 schema 的静态注册表。"""

from collections.abc import Callable, Mapping
from types import MappingProxyType
from typing import TypeAlias

from app.tools.definitions import TOOL_DEFINITIONS
from app.tools.implementations import (
    create_summary,
    lookup_metric,
    query_status,
)
from app.tools.models import ToolResult


ToolCallable: TypeAlias = Callable[..., ToolResult]


TOOL_REGISTRY: Mapping[
    str,
    ToolCallable,
] = MappingProxyType(
    {
        "lookup_metric": lookup_metric,
        "query_status": query_status,
        "create_summary": create_summary,
    }
)


__all__ = [
    "TOOL_DEFINITIONS",
    "TOOL_REGISTRY",
]