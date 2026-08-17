"""配置加载测试。"""

from pathlib import Path

import pytest

from app.config import load_settings
from app.errors import ConfigurationError


def test_missing_api_key_has_clear_message(
    clean_provider_env: None,
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ConfigurationError,
        match="未检测到 DEEPSEEK_API_KEY",
    ):
        load_settings(tmp_path / "missing.env")


def test_load_settings_uses_defaults(
    clean_provider_env: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv(
        "DEEPSEEK_API_KEY",
        "test-key",
    )

    settings = load_settings(tmp_path / "missing.env")

    assert settings.base_url == "https://api.deepseek.com"
    assert settings.model == "deepseek-v4-flash"
    assert settings.timeout == 30
    assert settings.max_retries == 2


@pytest.mark.parametrize(
    "invalid_value",
    ["abc", "0", "-1", "301"],
)
def test_invalid_timeout_is_rejected(
    invalid_value: str,
    clean_provider_env: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv(
        "DEEPSEEK_API_KEY",
        "test-key",
    )
    monkeypatch.setenv(
        "REQUEST_TIMEOUT",
        invalid_value,
    )

    with pytest.raises(
        ConfigurationError,
        match="REQUEST_TIMEOUT",
    ):
        load_settings(tmp_path / "missing.env")


def test_api_key_is_hidden_from_repr() -> None:
    from app.config import Settings

    settings = Settings(api_key="secret-value")

    assert "secret-value" not in repr(settings)