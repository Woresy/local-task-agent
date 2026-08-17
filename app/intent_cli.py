"""独立运行意图识别，不执行任何工具。"""

import argparse
import logging
import sys
from collections.abc import Sequence

from app.config import load_settings
from app.errors import (
    ConfigurationError,
    IntentRecognitionError,
    ProviderError,
    UserInputError,
)
from app.intent import IntentRecognizer
from app.llm_client import create_client
from app.logging_config import configure_logging


logger = logging.getLogger(__name__)


def parse_args(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="intent-cli",
        description="查看用户文本的结构化意图结果",
    )
    parser.add_argument(
        "-m",
        "--message",
        help="需要识别意图的用户文本。",
    )
    return parser.parse_args(argv)


def read_user_text(
    argument_text: str | None,
) -> str:
    if argument_text is not None:
        return argument_text

    return input("用户输入：")


def main(
    argv: Sequence[str] | None = None,
) -> int:
    args = parse_args(argv)

    try:
        settings = load_settings()
        configure_logging(settings.log_level)

        user_text = read_user_text(args.message)
        client = create_client(settings)

        recognizer = IntentRecognizer(
            client=client,
            model=settings.model,
        )
        result = recognizer.recognize(user_text)

        print(result.to_json())
        return 0
    except ConfigurationError as exc:
        print(f"配置错误：{exc}", file=sys.stderr)
        return 2
    except UserInputError as exc:
        print(f"输入错误：{exc}", file=sys.stderr)
        return 2
    except IntentRecognitionError as exc:
        print(f"意图识别失败：{exc}", file=sys.stderr)
        return 1
    except ProviderError as exc:
        print(f"模型调用失败：{exc}", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\n已取消。", file=sys.stderr)
        return 130
    except Exception:
        logger.exception("意图识别 CLI 未处理异常")
        print(
            "程序发生未预期异常，请查看日志。",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())