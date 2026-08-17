"""pytest 公共 fixture。"""

from unittest.mock import Mock

import pytest

from app.config import Settings


PROVIDER_ENV_NAMES = [
    "DEEPSEEK_API_KEY",
    "DEEPSEEK_BASE_URL",
    "DEEPSEEK_MODEL",
    "REQUEST_TIMEOUT",
    "MAX_RETRIES",
    "LOG_LEVEL",
]


@pytest.fixture
def clean_provider_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """清理会影响 Settings 的环境变量。"""

    for name in PROVIDER_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def settings() -> Settings:
    """返回不会访问真实 Provider 的测试配置。"""

    return Settings(
        api_key="test-api-key",
        base_url="https://example.com",
        model="test-model",
        timeout=5,
        max_retries=0,
        log_level="ERROR",
    )


@pytest.fixture
def sdk_client() -> Mock:
    """模拟 OpenAI SDK client。"""

    client = Mock()
    client.chat = Mock()
    client.chat.completions = Mock()
    return client