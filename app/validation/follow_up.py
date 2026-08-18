"""根据参数校验结果生成缺参追问。"""

from app.errors import ArgumentValidationError
from app.validation.models import (
    ArgumentValidationResult,
)
from app.validation.specs import (
    TOOL_ARGUMENT_SPECS,
)


def build_follow_up_question(
    result: ArgumentValidationResult,
) -> str | None:
    """为缺参状态生成追问，其他状态返回 None。"""

    if result.status != "needs_clarification":
        return None

    tool_spec = TOOL_ARGUMENT_SPECS.get(
        result.tool_name
    )
    if tool_spec is None:
        raise ArgumentValidationError(
            f"没有工具 {result.tool_name!r}"
            " 的参数规格。"
        )

    missing_parameters = set(
        result.missing_parameters
    )
    known_parameters = {
        parameter.name
        for parameter in tool_spec.parameters
    }

    unknown_parameters = (
        missing_parameters - known_parameters
    )
    if unknown_parameters:
        names = ", ".join(
            sorted(unknown_parameters)
        )
        raise ArgumentValidationError(
            f"缺失参数不在工具规格中：{names}"
        )

    questions: list[str] = []

    for parameter_spec in tool_spec.parameters:
        if (
            parameter_spec.name
            not in missing_parameters
        ):
            continue

        question = (
            parameter_spec.follow_up_question.strip()
        )
        if not question:
            raise ArgumentValidationError(
                f"参数 {parameter_spec.name!r}"
                " 没有配置追问文本。"
            )

        questions.append(question)

    if not questions:
        raise ArgumentValidationError(
            "缺参状态没有生成任何追问。"
        )

    return "\n".join(questions)