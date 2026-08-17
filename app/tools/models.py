"""工具名称、JSON 数据和统一返回结果。"""

import json
from dataclasses import dataclass
from typing import Literal, TypeAlias


ToolName = Literal[
    "lookup_metric",
    "query_status",
    "create_summary",
]

ToolErrorCode = Literal[
    "invalid_input",
    "not_found",
    "execution_error",
]

JSONScalar: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = (
    JSONScalar
    | list["JSONValue"]
    | dict[str, "JSONValue"]
)


@dataclass(frozen=True)
class ToolError:
    """一次可预期的工具执行错误。"""

    code: ToolErrorCode
    message: str

    def to_dict(self) -> dict[str, JSONValue]:
        return {
            "code": self.code,
            "message": self.message,
        }


@dataclass(frozen=True)
class ToolResult:
    """所有工具统一返回的数据结构。"""

    tool_name: ToolName
    ok: bool
    data: dict[str, JSONValue] | None = None
    error: ToolError | None = None

    def __post_init__(self) -> None:
        if self.ok and self.error is not None:
            raise ValueError(
                "成功的 ToolResult 不能包含 error。"
            )

        if self.ok and self.data is None:
            raise ValueError(
                "成功的 ToolResult 必须包含 data。"
            )

        if not self.ok and self.error is None:
            raise ValueError(
                "失败的 ToolResult 必须包含 error。"
            )

        if not self.ok and self.data is not None:
            raise ValueError(
                "失败的 ToolResult 不能包含 data。"
            )

    @classmethod
    def success(
        cls,
        tool_name: ToolName,
        data: dict[str, JSONValue],
    ) -> "ToolResult":
        return cls(
            tool_name=tool_name,
            ok=True,
            data=data,
        )

    @classmethod
    def failure(
        cls,
        tool_name: ToolName,
        code: ToolErrorCode,
        message: str,
    ) -> "ToolResult":
        return cls(
            tool_name=tool_name,
            ok=False,
            error=ToolError(
                code=code,
                message=message,
            ),
        )

    def to_dict(self) -> dict[str, JSONValue]:
        return {
            "tool_name": self.tool_name,
            "ok": self.ok,
            "data": self.data,
            "error": (
                self.error.to_dict()
                if self.error is not None
                else None
            ),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
        )