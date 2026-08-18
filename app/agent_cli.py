"""运行一次真实 tool calling Agent。"""

import argparse
import logging
import sys
from collections.abc import Sequence

from app.agent import (
    AgentRunner,
    OpenAICompatibleAgentModel,
)
from app.config import load_settings
from app.errors import (
    AgentError,
    ArgumentValidationError,
    ConfigurationError,
    ProviderError,
    ToolExecutionError,
    UserInputError,
)
from app.execution import ToolRouter
from app.llm_client import create_client
from app.logging_config import configure_logging


logger = logging.getLogger(__name__)


def parse_args(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="agent-cli",
        description=(
            "运行一次带真实工具调用的 Agent"
        ),
    )
    parser.add_argument(
        "-m",
        "--message",
        help="用户消息；省略时从终端读取。",
    )
    parser.add_argument(
        "--show-steps",
        action="store_true",
        help="显示本轮真实工具执行步骤。",
    )
    return parser.parse_args(argv)


def read_user_text(
    argument_text: str | None,
) -> str:
    if argument_text is not None:
        return argument_text

    return input("你：")


def main(
    argv: Sequence[str] | None = None,
) -> int:
    args = parse_args(argv)

    try:
        settings = load_settings()
        configure_logging(settings.log_level)

        client = create_client(settings)
        model = OpenAICompatibleAgentModel(
            client=client,
            model=settings.model,
        )
        runner = AgentRunner(
            model=model,
            router=ToolRouter(),
        )

        result = runner.run(
            read_user_text(args.message)
        )

        print(f"助手：{result.answer}")

        if args.show_steps:
            for index, step in enumerate(
                result.tool_steps,
                start=1,
            ):
                print(
                    f"步骤 {index}："
                    f"{step.result.to_json()}"
                )

        return 0

    except (
        ConfigurationError,
        UserInputError,
        ArgumentValidationError,
    ) as exc:
        print(
            f"输入或配置错误：{exc}",
            file=sys.stderr,
        )
        return 2

    except (
        ProviderError,
        AgentError,
        ToolExecutionError,
    ) as exc:
        print(
            f"Agent 执行失败：{exc}",
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
            "Agent CLI 未处理异常"
        )
        print(
            "程序发生未预期异常，请查看日志。",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())