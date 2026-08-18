"""工具参数校验测试。"""

from app.validation import (
    validate_tool_arguments,
)


def test_lookup_metric_arguments_are_ready() -> None:
    result = validate_tool_arguments(
        tool_name="lookup_metric",
        arguments={
            "name": "active_users",
        },
    )

    assert result.status == "ready"
    assert result.is_ready is True
    assert result.validated_arguments == {
        "name": "active_users",
    }
    assert result.missing_parameters == ()
    assert result.issues == ()


def test_query_status_arguments_are_ready() -> None:
    result = validate_tool_arguments(
        tool_name="query_status",
        arguments={
            "id": "TASK-1001",
        },
    )

    assert result.status == "ready"
    assert result.validated_arguments == {
        "id": "TASK-1001",
    }


def test_missing_metric_name_needs_clarification() -> None:
    result = validate_tool_arguments(
        tool_name="lookup_metric",
        arguments={},
    )

    assert result.status == "needs_clarification"
    assert result.is_ready is False
    assert result.missing_parameters == ("name",)
    assert result.issues == ()


def test_blank_task_id_needs_clarification() -> None:
    result = validate_tool_arguments(
        tool_name="query_status",
        arguments={
            "id": "   ",
        },
    )

    assert result.status == "needs_clarification"
    assert result.missing_parameters == ("id",)


def test_empty_summary_data_needs_clarification() -> None:
    result = validate_tool_arguments(
        tool_name="create_summary",
        arguments={
            "data": {},
        },
    )

    assert result.status == "needs_clarification"
    assert result.missing_parameters == ("data",)


def test_wrong_parameter_type_is_invalid() -> None:
    result = validate_tool_arguments(
        tool_name="query_status",
        arguments={
            "id": 1001,
        },
    )

    assert result.status == "invalid"
    assert result.is_ready is False
    assert result.missing_parameters == ()
    assert len(result.issues) == 1
    assert result.issues[0].parameter == "id"
    assert result.issues[0].code == "invalid_type"


def test_summary_data_must_be_object() -> None:
    result = validate_tool_arguments(
        tool_name="create_summary",
        arguments={
            "data": ["stage", 4],
        },
    )

    assert result.status == "invalid"
    assert result.issues[0].parameter == "data"
    assert result.issues[0].code == "invalid_type"


def test_unexpected_parameter_is_invalid() -> None:
    result = validate_tool_arguments(
        tool_name="lookup_metric",
        arguments={
            "name": "active_users",
            "limit": 10,
        },
    )

    assert result.status == "invalid"
    assert any(
        issue.parameter == "limit"
        and issue.code == "unexpected_parameter"
        for issue in result.issues
    )


def test_invalid_takes_priority_over_missing() -> None:
    result = validate_tool_arguments(
        tool_name="lookup_metric",
        arguments={
            "limit": 10,
        },
    )

    assert result.status == "invalid"
    assert any(
        issue.code == "unexpected_parameter"
        for issue in result.issues
    )