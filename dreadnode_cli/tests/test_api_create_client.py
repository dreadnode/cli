import base64
import json
import pathlib
from collections.abc import Callable
from datetime import datetime, timedelta

import httpx
import pytest

import dreadnode_cli.api as api
from dreadnode_cli.config import ServerConfig, UserConfig


async def test_create_client_without_config() -> None:
    with pytest.raises(Exception, match="No profile is set"):
        _ = api.create_client()


def _create_test_config(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path, token: str) -> UserConfig:
    # Mock config path to use temporary directory
    mock_config_path = tmp_path / "config.yaml"
    monkeypatch.setattr("dreadnode_cli.config.USER_CONFIG_PATH", mock_config_path)

    # Create test config
    config = UserConfig()
    server_config = ServerConfig(
        url="https://crucible.dreadnode.io",
        email="test@example.com",
        username="test",
        api_key="test123",
        access_token=token,
        refresh_token=token,
    )
    config.set_server_config(server_config, "default")
    config.active = "default"
    config.write()

    return config


async def test_create_client_with_exipired_refresh_token(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    _ = _create_test_config(
        monkeypatch, tmp_path, "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3MDg2NTYwMDB9.mock_signature"
    )

    with pytest.raises(Exception, match="Authentication expired"):
        _ = api.create_client()


async def test_create_client_with_valid_token(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    future_exp = int((datetime.now() + timedelta(seconds=30)).timestamp())
    obj = {"exp": future_exp}
    token = f"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.{base64.urlsafe_b64encode(json.dumps(obj).encode()).decode()}.mock_signature"

    _ = _create_test_config(monkeypatch, tmp_path, token)

    client = api.create_client()

    assert client._base_url == "https://crucible.dreadnode.io"
    assert client._client.cookies["access_token"] == token
    assert client._client.cookies["refresh_token"] == token


async def test_create_client_flushes_auth_changes(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    future_exp = int((datetime.now() + timedelta(seconds=30)).timestamp())
    obj = {"exp": future_exp}
    token = f"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.{base64.urlsafe_b64encode(json.dumps(obj).encode()).decode()}.mock_signature"

    # Mock config path to use temporary directory
    mock_config_path = tmp_path / "config.yaml"
    monkeypatch.setattr("dreadnode_cli.config.USER_CONFIG_PATH", mock_config_path)

    _ = _create_test_config(monkeypatch, tmp_path, token)

    at_exit_called = False

    # patch atexit.register
    with monkeypatch.context() as m:
        teardown_fn: Callable[[], None] = lambda: None  # noqa

        def set_teardown_fn(fn: Callable[[], None]) -> None:
            nonlocal teardown_fn
            nonlocal at_exit_called
            teardown_fn = fn
            at_exit_called = True

        m.setattr("atexit.register", set_teardown_fn)

        client = api.create_client()

        assert client._client.cookies["access_token"] == token
        assert client._client.cookies["refresh_token"] == token

        client._client.cookies = httpx.Cookies(
            {
                "access_token": "new_access_token",
                "refresh_token": "new_refresh_token",
            }
        )

        # explicitly call the atexit registered function
        teardown_fn()

    assert at_exit_called

    # read from disk again and expect the new cookies to be written
    new_config = UserConfig.read().get_server_config()

    assert new_config.access_token == "new_access_token"
    assert new_config.refresh_token == "new_refresh_token"
