"""CLI 入口测试。"""

from unittest.mock import Mock

import pytest

from app.config import Settings
from app.errors import ConfigurationError
from app.main import main


def test_main_returns_nonzero_for_config_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        "app.main.load_settings",
        Mock(
            side_effect=ConfigurationError(
                "测试配置错误"
            )
        ),
    )

    exit_code = main(["--message", "你好"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "配置错误" in captured.err


def test_main_prints_model_reply(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    settings = Settings(
        api_key="test-key",
        model="test-model",
        log_level="ERROR",
    )
    fake_client = Mock()

    monkeypatch.setattr(
        "app.main.load_settings",
        Mock(return_value=settings),
    )
    monkeypatch.setattr(
        "app.main.create_client",
        Mock(return_value=fake_client),
    )
    monkeypatch.setattr(
        "app.main.ask_once",
        Mock(return_value="测试回复"),
    )

    exit_code = main(["--message", "你好"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "助手：测试回复" in captured.out