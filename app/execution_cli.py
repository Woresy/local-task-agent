"""校验并单次执行指定的本地工具。"""

import argparse
import json
import logging
import sys
from collections.abc import Sequence
from typing import cast

from app.errors import (
    ArgumentValidationError,
    ToolExecutionError,
    ToolNotReadyError,
    UnknownToolError,
    UserInputError,
)
from app.execution import ToolRouter
from app.tools.models import (
    JSONValue,
    ToolName,
)
from app.validation import (
    validate_tool_arguments,
)


logger = logging.getLogger(__name__)


def parse_args(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="execution-cli",
        description=(
            "校验参数并安全执行一次本地工具"
        ),
    )
    parser.add_argument(
        "--tool",
        required=True,
        help="需要执行的工具名称。",
    )
    parser.add_argument(
        "--arguments",
        required=True,
        help='JSON object，例如 {"id":"TASK-1001"}。',
    )
    return parser.parse_args(argv)


def parse_arguments_json(
    raw_arguments: str,
) -> dict[str, JSONValue]:
    """解析 CLI 传入的 arguments。"""

    try:
        payload = json.loads(raw_arguments)
    except json.JSONDecodeError as exc:
        raise UserInputError(
            "arguments 必须是合法 JSON。"
        ) from exc

    if not isinstance(payload, dict):
        raise UserInputError(
            "arguments 顶层必须是 JSON object。"
        )

    return payload


def main(
    argv: Sequence[str] | None = None,
) -> int:
    args = parse_args(argv)

    try:
        tool_name = cast(ToolName, args.tool)
        arguments = parse_arguments_json(
            args.arguments
        )

        validation = validate_tool_arguments(
            tool_name=tool_name,
            arguments=arguments,
        )

        router = ToolRouter()
        result = router.execute(validation)

        print(result.to_json())
        return 0

    except UserInputError as exc:
        print(
            f"输入错误：{exc}",
            file=sys.stderr,
        )
        return 2

    except ArgumentValidationError as exc:
        print(
            f"参数校验失败：{exc}",
            file=sys.stderr,
        )
        return 2

    except ToolNotReadyError as exc:
        print(
            f"工具尚不可执行：{exc}",
            file=sys.stderr,
        )
        return 2

    except UnknownToolError as exc:
        print(
            f"未知工具：{exc}",
            file=sys.stderr,
        )
        return 2

    except ToolExecutionError as exc:
        print(
            f"工具执行失败：{exc}",
            file=sys.stderr,
        )
        return 1

    except (EOFError, KeyboardInterrupt):
        print(
            "\n已取消。",
            file=sys.stderr,
        )
        return 130

    except Exception:
        logger.exception(
            "工具执行 CLI 未处理异常"
        )
        print(
            "程序发生未预期异常，请查看日志。",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())