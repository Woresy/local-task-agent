"""支持短期状态的多轮 Agent CLI。"""

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
    AppError,
    ConfigurationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from app.execution import ToolRouter
from app.llm_client import create_client
from app.logging_config import configure_logging
from app.session import ConversationSession


logger = logging.getLogger(__name__)


HELP_TEXT = """
可用命令：
  /state  查看当前短期会话状态
  /reset  清空当前会话
  /help   查看命令
  /exit   退出程序
""".strip()


def parse_args(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="local-task-agent-chat",
        description="多轮任务型 AI CLI",
    )
    parser.add_argument(
        "--session-id",
        default="local",
        help="本地会话标识，默认 local。",
    )
    parser.add_argument(
        "--show-steps",
        action="store_true",
        help="显示本轮真实工具执行步骤。",
    )
    return parser.parse_args(argv)


def run_repl(
    session: ConversationSession,
    show_steps: bool = False,
) -> int:
    """运行连续输入输出循环。"""

    print("本地任务 Agent 已启动。")
    print(HELP_TEXT)

    while True:
        try:
            user_text = input("你：").strip()
        except EOFError:
            print()
            return 0
        except KeyboardInterrupt:
            print("\n已取消。", file=sys.stderr)
            return 130

        if not user_text:
            print("助手：输入不能为空。")
            continue

        if user_text == "/exit":
            return 0

        if user_text == "/help":
            print(HELP_TEXT)
            continue

        if user_text == "/state":
            print(session.state.to_json())
            continue

        if user_text == "/reset":
            session.reset()
            print("助手：会话已重置。")
            continue

        try:
            result = session.send(user_text)
            print(f"助手：{result.answer}")

            if show_steps:
                for index, step in enumerate(
                    result.tool_steps,
                    start=1,
                ):
                    print(
                        f"工具步骤 {index}："
                        f"{step.result.to_json()}"
                    )

        except ProviderTimeoutError as exc:
            print(
                f"助手：模型响应超时：{exc}",
                file=sys.stderr,
            )
        except ProviderRateLimitError as exc:
            print(
                f"助手：请求受限：{exc}",
                file=sys.stderr,
            )
        except AppError as exc:
            print(
                f"助手：本轮处理失败：{exc}",
                file=sys.stderr,
            )
        except Exception:
            logger.exception(
                "多轮 CLI 未处理异常"
            )
            print(
                "助手：程序发生未预期异常，"
                "本轮状态未保存。",
                file=sys.stderr,
            )


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
        session = ConversationSession(
            runner=runner,
            session_id=args.session_id,
        )

        return run_repl(
            session=session,
            show_steps=args.show_steps,
        )

    except ConfigurationError as exc:
        print(
            f"配置错误：{exc}",
            file=sys.stderr,
        )
        return 2
    except ValueError as exc:
        print(
            f"启动参数错误：{exc}",
            file=sys.stderr,
        )
        return 2
    except Exception:
        logger.exception(
            "多轮 CLI 启动失败"
        )
        print(
            "程序启动失败，请查看日志。",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())