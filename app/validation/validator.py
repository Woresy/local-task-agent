"""根据工具规格校验模型提取的 arguments。"""

from collections.abc import Mapping

from app.errors import ArgumentValidationError
from app.tools.models import (
    JSONValue,
    ToolName,
)
from app.validation.models import (
    ArgumentValidationResult,
    ValidationIssue,
)
from app.validation.specs import (
    TOOL_ARGUMENT_SPECS,
)


def validate_tool_arguments(
    tool_name: ToolName,
    arguments: Mapping[str, JSONValue],
) -> ArgumentValidationResult:
    """校验一个已确定工具的参数。"""

    tool_spec = TOOL_ARGUMENT_SPECS.get(tool_name)

    if tool_spec is None:
        raise ArgumentValidationError(
            f"没有工具 {tool_name!r} 的参数规格。"
        )

    parameter_specs = {
        parameter.name: parameter
        for parameter in tool_spec.parameters
    }

    missing_parameters: list[str] = []
    validated_arguments: dict[str, JSONValue] = {}
    issues: list[ValidationIssue] = []

    provided_names = set(arguments)
    expected_names = set(parameter_specs)

    extra_names = sorted(
        provided_names - expected_names
    )

    if tool_spec.allow_additional_parameters:
        for parameter_name in extra_names:
            validated_arguments[parameter_name] = (
                arguments[parameter_name]
            )
    else:
        for parameter_name in extra_names:
            issues.append(
                ValidationIssue(
                    parameter=parameter_name,
                    code="unexpected_parameter",
                    message=(
                        f"工具 {tool_name} 不接受参数"
                        f" {parameter_name!r}。"
                    ),
                )
            )

    for parameter_spec in tool_spec.parameters:
        parameter_name = parameter_spec.name

        if parameter_name not in arguments:
            if parameter_spec.required:
                missing_parameters.append(
                    parameter_name
                )
            continue

        value = arguments[parameter_name]

        if parameter_spec.kind == "string":
            if not isinstance(value, str):
                issues.append(
                    ValidationIssue(
                        parameter=parameter_name,
                        code="invalid_type",
                        message=(
                            f"参数 {parameter_name!r}"
                            " 必须是字符串。"
                        ),
                    )
                )
                continue

            if (
                not parameter_spec.allow_empty
                and not value.strip()
            ):
                missing_parameters.append(
                    parameter_name
                )
                continue

        elif parameter_spec.kind == "object":
            if not isinstance(value, dict):
                issues.append(
                    ValidationIssue(
                        parameter=parameter_name,
                        code="invalid_type",
                        message=(
                            f"参数 {parameter_name!r}"
                            " 必须是 JSON object。"
                        ),
                    )
                )
                continue

            if (
                not parameter_spec.allow_empty
                and not value
            ):
                missing_parameters.append(
                    parameter_name
                )
                continue

        else:
            raise ArgumentValidationError(
                f"参数 {parameter_name!r} 使用了"
                f"未知类型 {parameter_spec.kind!r}。"
            )

        validated_arguments[parameter_name] = value

    if issues:
        return ArgumentValidationResult(
            tool_name=tool_name,
            status="invalid",
            validated_arguments=validated_arguments,
            missing_parameters=(),
            issues=tuple(issues),
        )

    if missing_parameters:
        return ArgumentValidationResult(
            tool_name=tool_name,
            status="needs_clarification",
            validated_arguments=validated_arguments,
            missing_parameters=tuple(
                missing_parameters
            ),
            issues=(),
        )

    return ArgumentValidationResult(
        tool_name=tool_name,
        status="ready",
        validated_arguments=validated_arguments,
        missing_parameters=(),
        issues=(),
    )