import atexit
import json
import time
import typing as t
from datetime import datetime, timezone
from uuid import UUID

import httpx
from rich import print

from dreadnode_cli import __version__, utils
from dreadnode_cli.config import UserConfig
from dreadnode_cli.defaults import (
    DEBUG,
    DEFAULT_MAX_POLL_TIME,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_TOKEN_MAX_TTL,
    PLATFORM_BASE_URL,
)


class Token:
    """A JWT token with an expiration time."""

    data: str
    expires_at: datetime

    def __init__(self, token: str):
        self.data = token
        self.expires_at = utils.parse_jwt_token_expiration(token)

    def ttl(self) -> int:
        """Get number of seconds left until the token expires."""
        return int((self.expires_at - datetime.now()).total_seconds())

    def is_expired(self) -> bool:
        """Return True if the token is expired."""
        return self.ttl() <= 0

    def is_close_to_expiry(self) -> bool:
        """Return True if the token is close to expiry."""
        return self.ttl() <= DEFAULT_TOKEN_MAX_TTL


class Client:
    """Client for the Dreadnode API."""

    def __init__(
        self,
        base_url: str = PLATFORM_BASE_URL,
        *,
        cookies: dict[str, str] | None = None,
        debug: bool = DEBUG,
    ):
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            cookies=cookies,
            headers={
                "User-Agent": f"dreadnode-cli/{__version__}",
                "Accept": "application/json",
            },
            base_url=self._base_url,
        )

        if debug:
            self._client.event_hooks["request"].append(self._log_request)
            self._client.event_hooks["response"].append(self._log_response)

    def _log_request(self, request: httpx.Request) -> None:
        """Log every request to the console if debug is enabled."""

        print("-------------------------------------------")
        print(f"[bold]{request.method}[/] {request.url}")
        print("Headers:", request.headers)
        print("Content:", request.content)
        print("-------------------------------------------")

    def _log_response(self, response: httpx.Response) -> None:
        """Log every response to the console if debug is enabled."""

        print("-------------------------------------------")
        print(f"Response: {response.status_code}")
        print("Headers:", response.headers)
        print("Content:", response.read())
        print("--------------------------------------------")

    def _get_error_message(self, response: httpx.Response) -> str:
        """Get the error message from the response."""

        try:
            obj = response.json()
            return f'{response.status_code}: {obj.get("detail", json.dumps(obj))}'
        except Exception:
            return str(response.content)

    def _request(
        self,
        method: str,
        path: str,
        json_data: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Make a raw request to the API."""

        return self._client.request(method, path, json=json_data)

    def request(
        self,
        method: str,
        path: str,
        json_data: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Make a request to the API. Raise an exception for non-200 status codes."""

        response = self._request(method, path, json_data)

        if response.status_code == 401:
            raise Exception("Authentication expired, use [bold]dreadnode login[/]")

        try:
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            raise Exception(self._get_error_message(response)) from e

    def url_for_user_code(self, user_code: str) -> str:
        """Get the URL to verify the user code."""

        return f"{self._base_url}/account/device?code={user_code}"

    class DeviceCodeResponse(t.TypedDict):
        id: UUID
        completed: bool
        device_code: str
        expires_at: datetime
        expires_in: int
        user_code: str
        verification_url: str

    def get_device_codes(self) -> DeviceCodeResponse:
        """Start the authentication flow by requesting user and device codes."""

        response = self.request("POST", "/api/auth/device/code")
        return t.cast(Client.DeviceCodeResponse, response.json())

    class AccessRefreshTokenResponse(t.TypedDict):
        access_token: str
        refresh_token: str

    def poll_for_token(
        self, device_code: str, interval: int = DEFAULT_POLL_INTERVAL, max_poll_time: int = DEFAULT_MAX_POLL_TIME
    ) -> AccessRefreshTokenResponse:
        """Poll for the access token with the given device code."""

        start_time = datetime.now(timezone.utc)
        while (datetime.now(timezone.utc) - start_time).total_seconds() < max_poll_time:
            response = self._request("POST", "/api/auth/device/token", json_data={"device_code": device_code})

            if response.status_code == 200:
                return t.cast(Client.AccessRefreshTokenResponse, response.json())
            elif response.status_code != 401:
                raise Exception(self._get_error_message(response))

            time.sleep(interval)

        raise Exception("Polling for token timed out")

    # User

    class UserResponse(t.TypedDict):
        id: UUID
        email_address: str
        username: str

    def get_user(self) -> UserResponse:
        """Get the user email and username."""

        response = self.request("GET", "/api/user")
        return t.cast(Client.UserResponse, response.json())

    # Challenges

    class ChallengeResponse(t.TypedDict):
        authors: list[str]
        difficulty: str
        key: str
        lead: str
        name: str
        status: str
        title: str
        tags: list[str]

    def list_challenges(self) -> list[ChallengeResponse]:
        """List all challenges."""

        response = self.request("GET", "/api/challenges")
        return t.cast(list[Client.ChallengeResponse], response.json())

    def get_challenge_artifact(self, challenge: str, artifact_name: str) -> bytes:
        """Get a challenge artifact."""

        response = self.request("GET", f"/api/artifacts/{challenge}/{artifact_name}")
        return response.content

    def submit_challenge_flag(self, challenge: str, flag: str) -> bool:
        """Submit a flag to a challenge."""

        print(f":pirate_flag: submitting flag to challenge [bold]{challenge}[/] ...")

        response = self.request("POST", f"/api/challenges/{challenge}/submit-flag", json_data={"flag": flag})

        return bool(response.json().get("correct", False))


def client(*, profile: str | None = None) -> Client:
    """Create an authenticated API client using stored configuration data."""

    user_config = UserConfig.read()
    config = user_config.get_server_config(profile)
    client = Client(config.url, cookies={"refresh_token": config.refresh_token, "access_token": config.access_token})

    # Pre-emptively check if the token is expired
    if Token(config.refresh_token).is_expired():
        raise Exception("Authentication expired, use [bold]dreadnode login[/]")

    def _flush_auth_changes() -> None:
        """Flush the authentication data to disk if it has been updated."""

        # Weird hack to get around the fact that httpx assigns
        # a strange domain name for localhost requests that cause
        # conflict errors if we try to get the cookies directly

        cookies = list(client._client.cookies.jar)
        access_token = next((cookie.value for cookie in reversed(cookies) if cookie.name == "access_token"), None)
        refresh_token = next((cookie.value for cookie in reversed(cookies) if cookie.name == "refresh_token"), None)

        changed: bool = False
        if access_token and access_token != config.access_token:
            changed = True
            config.access_token = access_token

        if refresh_token and refresh_token != config.refresh_token:
            changed = True
            config.refresh_token = refresh_token

        if changed:
            user_config.set_server_config(config, profile).write()

    atexit.register(_flush_auth_changes)

    return client
