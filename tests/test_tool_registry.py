"""工具注册表测试。"""

from app.tools.implementations import (
    create_summary,
    lookup_metric,
    query_status,
)
from app.tools.registry import TOOL_REGISTRY


def test_registry_contains_expected_tools() -> None:
    assert set(TOOL_REGISTRY) == {
        "lookup_metric",
        "query_status",
        "create_summary",
    }


def test_registry_points_to_real_functions() -> None:
    assert TOOL_REGISTRY["lookup_metric"] is lookup_metric
    assert TOOL_REGISTRY["query_status"] is query_status
    assert TOOL_REGISTRY["create_summary"] is create_summary