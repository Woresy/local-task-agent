"""统一日志配置。"""

import logging


def configure_logging(level: str) -> None:
    """初始化控制台日志。"""

    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
    )