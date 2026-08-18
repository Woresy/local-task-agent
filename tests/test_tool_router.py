"""ToolRouter 白名单路由和执行测试。"""

from typing import cast
from unittest.mock import Mock

import pytest

from app.errors import (
    ToolContractError,
    ToolExecutionError,
    ToolNotReadyError,
    UnknownToolError,
)
from app.execution import ToolRouter
from app.tools.models import (
    ToolName,
    ToolResult,
)
from app.tools.registry import ToolCallable
from app.validation.models import (
    ArgumentValidationResult,
    ValidationIssue,
)


def make_ready_validation(
    tool_name: ToolName,
    arguments: dict,
) -> ArgumentValidationResult:
    """构造已通过校验的测试数据。"""

    return ArgumentValidationResult(
        tool_name=tool_name,
        status="ready",
        validated_arguments=arguments,
        missing_parameters=(),
        issues=(),
    )


def test_router_lists_registered_tools() -> None:
    router = ToolRouter()

    assert router.available_tools == (
        "create_summary",
        "lookup_metric",
        "query_status",
    )


def test_resolve_known_tool_returns_callable() -> None:
    tool = Mock()
    router = ToolRouter(
        registry={
            "lookup_metric": tool,
        }
    )

    resolved = router.resolve_tool(
        "lookup_metric"
    )

    assert resolved is tool


def test_unknown_tool_is_rejected() -> None:
    allowed_tool = Mock()
    router = ToolRouter(
        registry={
            "lookup_metric": allowed_tool,
        }
    )

    with pytest.raises(
        UnknownToolError,
        match="delete_database",
    ):
        router.resolve_tool(
            "delete_database"
        )

    allowed_tool.assert_not_called()


def test_ready_metric_tool_is_really_executed() -> None:
    router = ToolRouter()
    validation = make_ready_validation(
        tool_name="lookup_metric",
        arguments={
            "name": "active_users",
        },
    )

    result = router.execute(validation)

    assert result.ok is True
    assert result.tool_name == "lookup_metric"
    assert result.data is not None
    assert result.data["value"] == 1280


def test_ready_status_tool_is_really_executed() -> None:
    router = ToolRouter()
    validation = make_ready_validation(
        tool_name="query_status",
        arguments={
            "id": "TASK-1001",
        },
    )

    result = router.execute(validation)

    assert result.ok is True
    assert result.tool_name == "query_status"
    assert result.data is not None
    assert result.data["status"] == "running"


def test_ready_summary_tool_is_really_executed() -> None:
    router = ToolRouter()
    validation = make_ready_validation(
        tool_name="create_summary",
        arguments={
            "data": {
                "stage": 5,
            },
        },
    )

    result = router.execute(validation)

    assert result.ok is True
    assert result.tool_name == "create_summary"
    assert result.data is not None
    assert result.data["field_count"] == 1


def test_tool_failure_result_is_preserved() -> None:
    router = ToolRouter()
    validation = make_ready_validation(
        tool_name="lookup_metric",
        arguments={
            "name": "missing_metric",
        },
    )

    result = router.execute(validation)

    assert result.ok is False
    assert result.error is not None
    assert result.error.code == "not_found"


def test_missing_parameters_are_not_executed() -> None:
    tool = Mock()
    router = ToolRouter(
        registry={
            "query_status": tool,
        }
    )
    validation = ArgumentValidationResult(
        tool_name="query_status",
        status="needs_clarification",
        validated_arguments={},
        missing_parameters=("id",),
        issues=(),
    )

    with pytest.raises(ToolNotReadyError):
        router.execute(validation)

    tool.assert_not_called()


def test_invalid_arguments_are_not_executed() -> None:
    tool = Mock()
    router = ToolRouter(
        registry={
            "query_status": tool,
        }
    )
    validation = ArgumentValidationResult(
        tool_name="query_status",
        status="invalid",
        validated_arguments={},
        missing_parameters=(),
        issues=(
            ValidationIssue(
                parameter="id",
                code="invalid_type",
                message="id 必须是字符串。",
            ),
        ),
    )

    with pytest.raises(ToolNotReadyError):
        router.execute(validation)

    tool.assert_not_called()


def test_forged_unknown_tool_is_not_executed() -> None:
    allowed_tool = Mock()
    router = ToolRouter(
        registry={
            "lookup_metric": allowed_tool,
        }
    )

    forged_name = cast(
        ToolName,
        "delete_database",
    )
    validation = make_ready_validation(
        tool_name=forged_name,
        arguments={},
    )

    with pytest.raises(UnknownToolError):
        router.execute(validation)

    allowed_tool.assert_not_called()


def test_unexpected_tool_exception_is_wrapped() -> None:
    tool = Mock(
        side_effect=RuntimeError(
            "database unavailable"
        )
    )
    router = ToolRouter(
        registry={
            "lookup_metric": tool,
        }
    )
    validation = make_ready_validation(
        tool_name="lookup_metric",
        arguments={
            "name": "active_users",
        },
    )

    with pytest.raises(
        ToolExecutionError,
        match="lookup_metric",
    ) as exc_info:
        router.execute(validation)

    assert isinstance(
        exc_info.value.__cause__,
        RuntimeError,
    )


def test_non_tool_result_is_rejected() -> None:
    invalid_tool = Mock(
        return_value={
            "ok": True,
        }
    )
    router = ToolRouter(
        registry={
            "lookup_metric": cast(
                ToolCallable,
                invalid_tool,
            ),
        }
    )
    validation = make_ready_validation(
        tool_name="lookup_metric",
        arguments={
            "name": "active_users",
        },
    )

    with pytest.raises(ToolContractError):
        router.execute(validation)


def test_mismatched_tool_result_is_rejected() -> None:
    wrong_result_tool = Mock(
        return_value=ToolResult.success(
            tool_name="query_status",
            data={
                "id": "TASK-1001",
            },
        )
    )
    router = ToolRouter(
        registry={
            "lookup_metric": wrong_result_tool,
        }
    )
    validation = make_ready_validation(
        tool_name="lookup_metric",
        arguments={
            "name": "active_users",
        },
    )

    with pytest.raises(ToolContractError):
        router.execute(validation)

def test_non_callable_registry_value_is_rejected() -> None:
    invalid_tool = cast(
        ToolCallable,
        123,
    )
    router = ToolRouter(
        registry={
            "lookup_metric": invalid_tool,
        }
    )

    with pytest.raises(
        ToolContractError,
        match="不可调用",
    ):
        router.resolve_tool(
            "lookup_metric"
        )

def test_blank_tool_name_is_rejected() -> None:
    router = ToolRouter()

    with pytest.raises(UnknownToolError):
        router.resolve_tool("")