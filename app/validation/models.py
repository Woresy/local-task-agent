"""工具参数校验使用的数据结构。"""

import json
from dataclasses import dataclass
from typing import Literal

from app.tools.models import (
    JSONValue,
    ToolName,
)


ValidationStatus = Literal[
    "ready",
    "needs_clarification",
    "invalid",
]

ValidationIssueCode = Literal[
    "invalid_type",
    "unexpected_parameter",
]


@dataclass(frozen=True)
class ValidationIssue:
    """一个具体的参数问题。"""

    parameter: str
    code: ValidationIssueCode
    message: str

    def __post_init__(self) -> None:
        if not self.parameter.strip():
            raise ValueError(
                "ValidationIssue.parameter 不能为空。"
            )

        if not self.message.strip():
            raise ValueError(
                "ValidationIssue.message 不能为空。"
            )

    def to_dict(self) -> dict[str, JSONValue]:
        return {
            "parameter": self.parameter,
            "code": self.code,
            "message": self.message,
        }


@dataclass(frozen=True)
class ArgumentValidationResult:
    """一次工具参数校验的结构化结果。"""

    tool_name: ToolName
    status: ValidationStatus
    validated_arguments: dict[str, JSONValue]
    missing_parameters: tuple[str, ...] = ()
    issues: tuple[ValidationIssue, ...] = ()

    def __post_init__(self) -> None:
        if self.status == "ready":
            if self.missing_parameters or self.issues:
                raise ValueError(
                    "ready 状态不能包含缺失参数或参数问题。"
                )

        if self.status == "needs_clarification":
            if not self.missing_parameters:
                raise ValueError(
                    "needs_clarification 状态必须包含缺失参数。"
                )

            if self.issues:
                raise ValueError(
                    "needs_clarification 状态不能包含参数问题。"
                )

        if self.status == "invalid":
            if not self.issues:
                raise ValueError(
                    "invalid 状态必须包含参数问题。"
                )

    @property
    def is_ready(self) -> bool:
        return self.status == "ready"

    def to_dict(self) -> dict[str, JSONValue]:
        return {
            "tool_name": self.tool_name,
            "status": self.status,
            "validated_arguments": (
                self.validated_arguments
            ),
            "missing_parameters": list(
                self.missing_parameters
            ),
            "issues": [
                issue.to_dict()
                for issue in self.issues
            ],
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
        )