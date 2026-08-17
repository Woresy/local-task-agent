"""读取并校验 DeepSeek Provider 配置。"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

from app.errors import ConfigurationError


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"


@dataclass(frozen=True)
class Settings:
    """应用运行配置。"""

    api_key: str = field(repr=False)
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-v4-flash"
    timeout: float = 30.0
    max_retries: int = 2
    log_level: str = "INFO"


def _parse_timeout(raw_value: str) -> float:
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ConfigurationError(
            "REQUEST_TIMEOUT 必须是数字。"
        ) from exc

    if value <= 0 or value > 300:
        raise ConfigurationError(
            "REQUEST_TIMEOUT 必须大于 0 且不超过 300 秒。"
        )

    return value


def _parse_max_retries(raw_value: str) -> int:
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ConfigurationError(
            "MAX_RETRIES 必须是整数。"
        ) from exc

    if value < 0 or value > 10:
        raise ConfigurationError(
            "MAX_RETRIES 必须在 0 到 10 之间。"
        )

    return value


def _validate_base_url(raw_value: str) -> str:
    value = raw_value.strip().rstrip("/")

    if not value:
        raise ConfigurationError(
            "DEEPSEEK_BASE_URL 不能为空。"
        )

    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ConfigurationError(
            "DEEPSEEK_BASE_URL 必须是有效的 HTTP 或 HTTPS 地址。"
        )

    return value


def _validate_log_level(raw_value: str) -> str:
    value = raw_value.strip().upper()
    allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR"}

    if value not in allowed_levels:
        raise ConfigurationError(
            "LOG_LEVEL 必须是 DEBUG、INFO、WARNING 或 ERROR。"
        )

    return value


def load_settings(
    env_file: str | Path | None = None,
) -> Settings:
    """读取项目环境变量并生成不可变配置。"""

    selected_env_file = (
        Path(env_file) if env_file is not None else DEFAULT_ENV_FILE
    )
    load_dotenv(dotenv_path=selected_env_file, override=False)

    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise ConfigurationError(
            "未检测到 DEEPSEEK_API_KEY，请复制 "
            ".env.example 为 .env 并填写真实密钥。"
        )

    model = os.getenv(
        "DEEPSEEK_MODEL",
        "deepseek-v4-flash",
    ).strip()
    if not model:
        raise ConfigurationError(
            "DEEPSEEK_MODEL 不能为空。"
        )

    return Settings(
        api_key=api_key,
        base_url=_validate_base_url(
            os.getenv(
                "DEEPSEEK_BASE_URL",
                "https://api.deepseek.com",
            )
        ),
        model=model,
        timeout=_parse_timeout(
            os.getenv("REQUEST_TIMEOUT", "30")
        ),
        max_retries=_parse_max_retries(
            os.getenv("MAX_RETRIES", "2")
        ),
        log_level=_validate_log_level(
            os.getenv("LOG_LEVEL", "INFO")
        ),
    )