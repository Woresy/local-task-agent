"""工具参数校验规格。"""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal, Mapping

from app.tools.models import ToolName


ParameterKind = Literal[
    "string",
    "object",
]


@dataclass(frozen=True)
class ParameterSpec:
    """单个工具参数的静态规格。"""

    name: str
    kind: ParameterKind
    required: bool
    allow_empty: bool
    follow_up_question: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError(
                "参数规格名称不能为空。"
            )

        if (
            self.required
            and not self.follow_up_question.strip()
        ):
            raise ValueError(
                "必填参数必须提供追问文本。"
            )


@dataclass(frozen=True)
class ToolArgumentSpec:
    """一个工具的完整参数规格。"""

    tool_name: ToolName
    parameters: tuple[ParameterSpec, ...]
    allow_additional_parameters: bool = False


TOOL_ARGUMENT_SPECS: Mapping[
    ToolName,
    ToolArgumentSpec,
] = MappingProxyType(
    {
        "lookup_metric": ToolArgumentSpec(
            tool_name="lookup_metric",
            parameters=(
                ParameterSpec(
                    name="name",
                    kind="string",
                    required=True,
                    allow_empty=False,
                    follow_up_question=(
                        "请提供要查询的指标名称，"
                        "例如 active_users。"
                    ),
                ),
            ),
        ),
        "query_status": ToolArgumentSpec(
            tool_name="query_status",
            parameters=(
                ParameterSpec(
                    name="id",
                    kind="string",
                    required=True,
                    allow_empty=False,
                    follow_up_question=(
                        "请提供要查询的任务 ID，"
                        "例如 TASK-1001。"
                    ),
                ),
            ),
        ),
        "create_summary": ToolArgumentSpec(
            tool_name="create_summary",
            parameters=(
                ParameterSpec(
                    name="data",
                    kind="object",
                    required=True,
                    allow_empty=False,
                    follow_up_question=(
                        "请提供需要生成摘要的结构化数据。"
                    ),
                ),
            ),
        ),
    }
)