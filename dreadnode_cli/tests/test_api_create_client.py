import base64
import json
import pathlib
from datetime import datetime, timedelta

import pytest

import dreadnode_cli.api as api
from dreadnode_cli.config import ServerConfig, UserConfig


async def test_create_client_without_config() -> None:
    with pytest.raises(Exception, match="No profile is set"):
        _ = api.create_client()


async def test_create_client_with_exipired_refresh_token(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
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
        access_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3MDg2NTYwMDB9.mock_signature",
        refresh_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3MDg2NTYwMDB9.mock_signature",
    )
    config.set_server_config(server_config, "default")
    config.active = "default"
    config.write()

    with pytest.raises(Exception, match="Authentication expired"):
        _ = api.create_client()


async def test_create_client_with_valid_token(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    # Mock config path to use temporary directory
    mock_config_path = tmp_path / "config.yaml"
    monkeypatch.setattr("dreadnode_cli.config.USER_CONFIG_PATH", mock_config_path)

    future_exp = int((datetime.now() + timedelta(seconds=30)).timestamp())
    obj = {"exp": future_exp}
    token = f"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.{base64.urlsafe_b64encode(json.dumps(obj).encode()).decode()}.mock_signature"

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

    client = api.create_client()

    assert client._base_url == "https://crucible.dreadnode.io"
    assert client._client.cookies["access_token"] == token
    assert client._client.cookies["refresh_token"] == token
