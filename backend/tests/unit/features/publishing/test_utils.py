"""Unit tests for the Facebook token health check."""

import logging
from unittest.mock import AsyncMock, Mock

import pytest
from app.core.config import settings
from app.features.publishing.utils import check_facebook_token_health
from pytest_mock import MockerFixture

LOGGER = "app.features.publishing.utils"


@pytest.fixture(autouse=True)
def _fb_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "facebook_access_token", "test-token")
    monkeypatch.setattr(settings, "facebook_app_id", "test-app-id")
    monkeypatch.setattr(settings, "facebook_app_secret", "test-app-secret")


def _mock_debug_token(mocker: MockerFixture, data: dict) -> None:
    response = Mock(status_code=200, json=Mock(return_value={"data": data}))
    mocker.patch("httpx.AsyncClient.get", AsyncMock(return_value=response))


async def test_never_expiring_token_logs_info(
    mocker: MockerFixture, caplog: pytest.LogCaptureFixture
) -> None:
    _mock_debug_token(mocker, {"is_valid": True, "expires_at": 0})

    with caplog.at_level(logging.INFO, logger=LOGGER):
        await check_facebook_token_health()

    assert "never expires" in caplog.text


async def test_expiring_token_logs_warning(
    mocker: MockerFixture, caplog: pytest.LogCaptureFixture
) -> None:
    _mock_debug_token(mocker, {"is_valid": True, "expires_at": 1780000000})

    with caplog.at_level(logging.INFO, logger=LOGGER):
        await check_facebook_token_health()

    assert any(record.levelno == logging.WARNING for record in caplog.records)
    assert "expires" in caplog.text


async def test_invalid_token_logs_error(
    mocker: MockerFixture, caplog: pytest.LogCaptureFixture
) -> None:
    _mock_debug_token(mocker, {"is_valid": False})

    with caplog.at_level(logging.INFO, logger=LOGGER):
        await check_facebook_token_health()

    assert any(record.levelno == logging.ERROR for record in caplog.records)
    assert "INVALID" in caplog.text
