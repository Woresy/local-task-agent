"""缺参追问生成测试。"""

from app.validation import (
    build_follow_up_question,
    validate_tool_arguments,
)


def test_missing_metric_name_generates_question() -> None:
    validation = validate_tool_arguments(
        tool_name="lookup_metric",
        arguments={},
    )

    question = build_follow_up_question(validation)

    assert question is not None
    assert "指标名称" in question
    assert "active_users" in question


def test_missing_task_id_generates_question() -> None:
    validation = validate_tool_arguments(
        tool_name="query_status",
        arguments={},
    )

    question = build_follow_up_question(validation)

    assert question is not None
    assert "任务 ID" in question
    assert "TASK-1001" in question


def test_missing_summary_data_generates_question() -> None:
    validation = validate_tool_arguments(
        tool_name="create_summary",
        arguments={},
    )

    question = build_follow_up_question(validation)

    assert question is not None
    assert "结构化数据" in question


def test_ready_result_does_not_generate_question() -> None:
    validation = validate_tool_arguments(
        tool_name="lookup_metric",
        arguments={
            "name": "active_users",
        },
    )

    assert build_follow_up_question(validation) is None


def test_invalid_result_does_not_generate_question() -> None:
    validation = validate_tool_arguments(
        tool_name="query_status",
        arguments={
            "id": 1001,
        },
    )

    assert build_follow_up_question(validation) is None