"""已校验工具请求的安全路由与执行。"""

from collections.abc import Mapping
from types import MappingProxyType

from app.errors import (
    ToolContractError,
    ToolExecutionError,
    ToolNotReadyError,
    UnknownToolError,
)
from app.tools.models import ToolResult
from app.tools.registry import (
    TOOL_REGISTRY,
    ToolCallable,
)
from app.validation.models import (
    ArgumentValidationResult,
)


class ToolRouter:
    """通过静态白名单执行已完成参数校验的工具。"""

    def __init__(
        self,
        registry: Mapping[
            str,
            ToolCallable,
        ] | None = None,
    ) -> None:
        selected_registry = (
            TOOL_REGISTRY
            if registry is None
            else registry
        )

        self._registry: Mapping[
            str,
            ToolCallable,
        ] = MappingProxyType(
            dict(selected_registry)
        )

    @property
    def available_tools(self) -> tuple[str, ...]:
        """返回当前允许执行的工具名称。"""

        return tuple(sorted(self._registry))

    def resolve_tool(
        self,
        tool_name: str,
    ) -> ToolCallable:
        """从白名单中取得工具函数。"""

        if (
            not isinstance(tool_name, str)
            or tool_name not in self._registry
        ):
            raise UnknownToolError(
                f"未知工具：{tool_name!r}"
            )

        tool = self._registry[tool_name]
        if not callable(tool):
            raise ToolContractError(
                f"工具 {tool_name!r} 的注册值不可调用。"
            )

        return tool

    def execute(
        self,
        validation: ArgumentValidationResult,
    ) -> ToolResult:
        """执行一次已经通过参数校验的工具调用。"""

        if not validation.is_ready:
            raise ToolNotReadyError(
                f"工具 {validation.tool_name!r} 的参数尚未就绪。"
            )

        tool = self.resolve_tool(validation.tool_name)

        try:
            result = tool(
                **validation.validated_arguments
            )
        except Exception as exc:
            raise ToolExecutionError(
                f"工具 {validation.tool_name!r} 执行失败。"
            ) from exc

        if not isinstance(result, ToolResult):
            raise ToolContractError(
                f"工具 {validation.tool_name!r} 未返回 ToolResult。"
            )

        if result.tool_name != validation.tool_name:
            raise ToolContractError(
                f"工具 {validation.tool_name!r} 返回了不一致的"
                f"工具名称 {result.tool_name!r}。"
            )

        return result
