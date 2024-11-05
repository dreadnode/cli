from typing import Any

import httpx
import pytest

from dreadnode_cli import api


def test_client_init() -> None:
    client = api.Client("http://test.com")
    assert client._base_url == "http://test.com"
    assert client._client.headers["Accept"] == "application/json"


def test_client_init_strips_trailing_slash() -> None:
    client = api.Client("http://test.com/")
    assert client._base_url == "http://test.com"


def test_get_error_message_json() -> None:
    client = api.Client()
    response = httpx.Response(
        status_code=400,
        json={"detail": "test error"},
        request=httpx.Request("GET", "http://test.com"),
    )
    assert client._get_error_message(response) == "400: test error"


def test_get_error_message_raw() -> None:
    client = api.Client()
    response = httpx.Response(
        status_code=400,
        content=b"raw error",
        request=httpx.Request("GET", "http://test.com"),
    )
    assert client._get_error_message(response) == "b'raw error'"


def test_does_not_install_debug_event_hooks_by_default() -> None:
    client = api.Client()
    assert client._client.event_hooks["request"] == []
    assert client._client.event_hooks["response"] == []


def test_installs_debug_event_hooks_if_needed() -> None:
    client = api.Client(debug=True)
    assert client._client.event_hooks["request"]
    assert client._client.event_hooks["response"]


def test_url_for_user_code() -> None:
    client = api.Client("http://test.com")
    assert client.url_for_user_code("ABC123") == "http://test.com/account/device?code=ABC123"


def test_poll_for_token_success(monkeypatch: pytest.MonkeyPatch) -> None:
    client = api.Client()

    # Mock successful response after first try
    def mock_request(*args: Any, **kwargs: Any) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={"access_token": "access123", "refresh_token": "refresh123"},
            request=httpx.Request("POST", "http://test.com"),
        )

    monkeypatch.setattr(client, "_request", mock_request)

    result = client.poll_for_token("device123", interval=0)
    assert result.access_token == "access123"
    assert result.refresh_token == "refresh123"


def test_poll_for_token_retry_then_success(monkeypatch: pytest.MonkeyPatch) -> None:
    client = api.Client()

    # Mock response that succeeds after one 401
    attempts = 0

    def mock_request(*args: Any, **kwargs: Any) -> httpx.Response:
        nonlocal attempts
        attempts += 1

        if attempts == 1:
            return httpx.Response(status_code=401, request=httpx.Request("POST", "http://test.com"))
        return httpx.Response(
            status_code=200,
            json={"access_token": "access123", "refresh_token": "refresh123"},
            request=httpx.Request("POST", "http://test.com"),
        )

    monkeypatch.setattr(client, "_request", mock_request)

    result = client.poll_for_token("device123", interval=0)
    assert result.access_token == "access123"
    assert result.refresh_token == "refresh123"
    assert attempts == 2


def test_poll_for_token_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    client = api.Client()

    # Mock response that always returns 401
    def mock_request(*args: Any, **kwargs: Any) -> httpx.Response:
        return httpx.Response(status_code=401, request=httpx.Request("POST", "http://test.com"))

    monkeypatch.setattr(client, "_request", mock_request)

    with pytest.raises(Exception, match="Polling for token timed out"):
        client.poll_for_token("device123", interval=0, max_poll_time=0)
