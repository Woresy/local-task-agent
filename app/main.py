"""阶段 1：单轮普通聊天 CLI。"""

import argparse
import logging
import sys
from collections.abc import Sequence

from app.config import load_settings
from app.errors import (
    ConfigurationError,
    ProviderError,
    UserInputError,
)
from app.llm_client import ask_once, create_client
from app.logging_config import configure_logging


logger = logging.getLogger(__name__)


def parse_args(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    """解析 CLI 参数。"""

    parser = argparse.ArgumentParser(
        prog="local-task-agent",
        description="本地任务型 AI 聊天机器人",
    )
    parser.add_argument(
        "-m",
        "--message",
        help="要发送给模型的单轮消息；省略时从终端读取。",
    )
    return parser.parse_args(argv)


def read_user_text(argument_text: str | None) -> str:
    """优先读取 CLI 参数，否则读取终端输入。"""

    if argument_text is not None:
        return argument_text

    return input("你：")


def main(
    argv: Sequence[str] | None = None,
) -> int:
    """运行单轮聊天并返回进程状态码。"""

    args = parse_args(argv)

    try:
        settings = load_settings()
        configure_logging(settings.log_level)

        user_text = read_user_text(args.message)
        client = create_client(settings)

        reply = ask_once(
            client=client,
            model=settings.model,
            prompt=user_text,
        )

        print(f"助手：{reply}")
        return 0
    except ConfigurationError as exc:
        print(f"配置错误：{exc}", file=sys.stderr)
        return 2
    except UserInputError as exc:
        print(f"输入错误：{exc}", file=sys.stderr)
        return 2
    except ProviderError as exc:
        print(f"模型调用失败：{exc}", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\n已取消。", file=sys.stderr)
        return 130
    except Exception:
        logger.exception("未处理异常")
        print(
            "程序发生未预期异常，请查看日志。",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())