import asyncio
import json
from datetime import datetime, timezone
from typing import Any

import httpx
from rich import print

from dreadnode_cli import __version__, utils
from dreadnode_cli.config import ServerConfig, UserConfig
from dreadnode_cli.defaults import (
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


class Authentication:
    """Authentication data for the Dreadnode API."""

    access_token: Token
    refresh_token: Token

    def __init__(self, access_token: str, refresh_token: str):
        self.access_token = Token(access_token)
        self.refresh_token = Token(refresh_token)

    def is_expired(self) -> bool:
        """Return True if either of the tokens is expired."""
        return self.refresh_token.is_expired() or self.access_token.is_expired()

    def is_close_to_expiry(self) -> bool:
        """Return True if either of the tokens is close to expiry."""
        return self.refresh_token.is_close_to_expiry() or self.access_token.is_close_to_expiry()


class Client:
    """Client for the Dreadnode API."""

    debug: bool = False

    base_url: str
    auth: Authentication | None = None

    def __init__(
        self,
        base_url: str = PLATFORM_BASE_URL,
        auth: Authentication | None = None,
        debug: bool = False,
    ):
        self.base_url = base_url.rstrip("/")
        self.debug = debug
        self.auth = auth

    async def _log_request(self, request: httpx.Request) -> None:
        """Log every request to the console if debug is enabled."""

        if self.debug:
            print("-------------------------------------------")
            print(f"[bold]{request.method}[/] {request.url}")
            print("Headers:", request.headers)
            print("Content:", request.content)
            print("-------------------------------------------")

    def _get_headers(self, additional: dict[str, str] | None = None) -> dict[str, str]:
        """Get the common headers for every request."""

        headers = {
            "User-Agent": f"dreadnode-cli/{__version__}",
            "Accept": "application/json",
        }

        if additional:
            headers.update(additional)

        return headers

    def _get_auth_cookies(self) -> dict[str, str]:
        """Get the authentication cookies for the request. Will raise an error if not authenticated or if the tokens are expired."""

        if not self.auth:
            raise Exception("not authenticated")

        elif self.auth.is_expired():
            raise Exception("authentication expired")

        return {"refresh_token": self.auth.refresh_token.data}

    def _get_error_message(self, response: httpx.Response) -> str:
        """Get the error message from the response."""

        try:
            obj = response.json()
            return f'{response.status_code}: {obj.get("detail", json.dumps(obj))}'
        except Exception:
            return str(response.content)

    async def _request(
        self,
        method: str,
        path: str,
        json_data: dict[str, str] | None = None,
        auth: bool = True,
        allow_non_ok: bool = False,
    ) -> httpx.Response:
        """Make a request to the Dreadnode API."""

        # common headers
        headers = self._get_headers()
        # if authentication is required add the necessary cookies (will check for valid auth data)
        cookies = self._get_auth_cookies() if auth else None

        async with httpx.AsyncClient(
            cookies=cookies, headers=headers, event_hooks={"request": [self._log_request]}
        ) as client:
            response = await client.request(method, f"{self.base_url}{path}", json=json_data)
            if allow_non_ok or response.status_code == 200:
                return response
            else:
                raise Exception(self._get_error_message(response))

    def url_for_user_code(self, user_code: str) -> str:
        """Get the URL to verify the user code."""

        return f"{self.base_url}/account/device?code={user_code}"

    async def get_device_codes(self) -> Any:
        """Start the authentication flow by requesting user and device codes."""

        response = await self._request("POST", "/api/auth/device/code", auth=False)
        return response.json()

    async def poll_for_token(
        self, device_code: str, interval: int = DEFAULT_POLL_INTERVAL, max_poll_time: int = DEFAULT_MAX_POLL_TIME
    ) -> Any | None:
        """Poll for the access token with the given device code."""

        start_time = datetime.now(timezone.utc)
        while (datetime.now(timezone.utc) - start_time).total_seconds() < max_poll_time:
            response = await self._request(
                "POST", "/api/auth/device/token", json_data={"device_code": device_code}, auth=False, allow_non_ok=True
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 400:
                error_data = response.json()
                if error_data.get("detail") == "Device code not verified":
                    print("Waiting for user verification...")
                elif error_data.get("detail") == "Device code expired":
                    raise Exception("Device code has expired.")
                else:
                    raise Exception(f"Unexpected error: {self._get_error_message(response)}")
            elif response.status_code != 401:
                raise Exception(f"Unexpected status code: {response.status_code}")

            await asyncio.sleep(interval)

        return None

    async def refresh_auth(self) -> Authentication:
        """Refresh the authentication data."""

        if not self.auth:
            raise Exception("not authenticated")

        print(":water_wave: refreshing authentication data ...")

        response = await self._request(
            "POST", "/api/auth/refresh", auth=False, json_data={"refresh_token": self.auth.refresh_token.data}
        )
        # new tokens set via cookies
        resp = dict(response.cookies)
        if "access_token" not in resp:
            raise Exception("no access_token in refresh response")
        elif "refresh_token" not in resp:
            raise Exception("no refresh_token in refresh response")

        # update the auth data
        self.auth = Authentication(resp["access_token"], resp["refresh_token"])

        return self.auth

    async def list_challenges(self) -> Any:
        """List all challenges."""

        response = await self._request("GET", "/api/challenges")

        return response.json()


async def setup_authenticated_client(config: ServerConfig, force_refresh: bool = False) -> Client:
    # load existing auth data
    auth = Authentication(config.access_token, config.refresh_token)
    client = Client(base_url=config.url, auth=auth)

    if auth.is_expired():
        raise Exception("authentication expired, use [bold]dreadnode login[/] to authenticate again")
    elif force_refresh or auth.is_close_to_expiry():
        # update the auth data
        new_auth = await client.refresh_auth()
        # save on disk
        config.access_token = new_auth.access_token.data
        config.refresh_token = new_auth.refresh_token.data
        # print(f"new refresh token expires at: {new_auth.refresh_token.expires_at}")
        UserConfig.read().set_active_config(config).write()

    return client
