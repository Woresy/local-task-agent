"""三个本地工具的行为测试。"""

import json

import pytest

from app.tools.implementations import (
    create_summary,
    lookup_metric,
    query_status,
)


def test_lookup_metric_returns_known_metric() -> None:
    result = lookup_metric("active_users")

    assert result.ok is True
    assert result.error is None
    assert result.data is not None
    assert result.data["name"] == "active_users"
    assert result.data["value"] == 1280
    assert result.data["unit"] == "users"


def test_lookup_metric_accepts_surrounding_whitespace() -> None:
    result = lookup_metric("  active_users  ")

    assert result.ok is True
    assert result.data is not None
    assert result.data["name"] == "active_users"


def test_lookup_metric_rejects_empty_name() -> None:
    result = lookup_metric("   ")

    assert result.ok is False
    assert result.error is not None
    assert result.error.code == "invalid_input"


def test_lookup_metric_reports_unknown_metric() -> None:
    result = lookup_metric("unknown_metric")

    assert result.ok is False
    assert result.error is not None
    assert result.error.code == "not_found"


def test_lookup_metric_does_not_expose_store_reference() -> None:
    first_result = lookup_metric("active_users")
    assert first_result.data is not None

    first_result.data["value"] = 0

    second_result = lookup_metric("active_users")
    assert second_result.data is not None
    assert second_result.data["value"] == 1280


def test_query_status_returns_known_task() -> None:
    result = query_status("TASK-1001")

    assert result.ok is True
    assert result.error is None
    assert result.data is not None
    assert result.data["id"] == "TASK-1001"
    assert result.data["status"] == "running"
    assert result.data["progress"] == 65


def test_query_status_normalizes_lowercase_id() -> None:
    result = query_status("task-1002")

    assert result.ok is True
    assert result.data is not None
    assert result.data["id"] == "TASK-1002"


def test_query_status_reports_unknown_id() -> None:
    result = query_status("TASK-9999")

    assert result.ok is False
    assert result.error is not None
    assert result.error.code == "not_found"


@pytest.mark.parametrize("task_id", ["", " ", "\n"])
def test_query_status_rejects_empty_id(
    task_id: str,
) -> None:
    result = query_status(task_id)

    assert result.ok is False
    assert result.error is not None
    assert result.error.code == "invalid_input"


def test_create_summary_returns_stable_structure() -> None:
    result = create_summary(
        {
            "project": "local-task-agent",
            "stage": 2,
        }
    )

    assert result.ok is True
    assert result.error is None
    assert result.data is not None
    assert result.data["field_count"] == 2
    assert result.data["fields"] == [
        "project",
        "stage",
    ]
    assert isinstance(result.data["summary"], str)
    assert result.data["summary"]


def test_create_summary_rejects_empty_data() -> None:
    result = create_summary({})

    assert result.ok is False
    assert result.error is not None
    assert result.error.code == "invalid_input"


def test_tool_result_can_be_serialized_to_json() -> None:
    result = query_status("TASK-1001")

    serialized = result.to_json()
    parsed = json.loads(serialized)

    assert parsed["tool_name"] == "query_status"
    assert parsed["ok"] is True
    assert parsed["data"]["id"] == "TASK-1001"