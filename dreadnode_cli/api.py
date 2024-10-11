from typing import Any

import requests
from rich import print

from dreadnode_cli import __version__
from dreadnode_cli.defaults import PLATFORM_BASE_URL


class Client:
    access_token: str | None = None
    base_url: str

    def __init__(self, base_url: str = PLATFORM_BASE_URL, access_token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token

    def _get_headers(self, with_auth: bool = True, additional: dict[str, str] | None = None) -> dict[str, str]:
        headers = {
            "User-Agent": f"dreadnode-cli/{__version__}",
            "Accept": "application/json",
        }

        if with_auth:
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"
                headers["X-API-Key"] = self.access_token
            else:
                raise Exception("No access token set")

        if additional:
            headers.update(additional)

        return headers

    def _get_error_message(self, response: requests.Response) -> str:
        try:
            return str(response.json().get("detail", "unknown error"))
        except Exception:
            return str(response.content)

    def login(self, username: str, password: str) -> str:
        """Login to the platform and return the API key."""

        url = f"{self.base_url}/api/auth/login"
        headers = self._get_headers(with_auth=False, additional={"Content-Type": "application/x-www-form-urlencoded"})
        form_data = {
            "username": username,
            "password": password,
        }

        print(f":key: Authenticating to [bold link]{self.base_url}[/] as [bold cyan]{username}[/] ...")

        response = requests.post(url, data=form_data, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Authentication failed: {self._get_error_message(response)}")

        self.access_token = str(response.json().get("access_token"))

        return self.access_token

    def refresh_token(self, refresh_token: str | None = None) -> str:
        """Refresh the access token."""

        # FIXME: this doesn't work and always returns "Invalid token" somehow.
        token_to_refresh = refresh_token or self.access_token
        if not token_to_refresh:
            raise Exception("No refresh token set")

        url = f"{self.base_url}/api/auth/refresh"
        headers = self._get_headers(with_auth=False, additional={"Content-Type": "application/x-www-form-urlencoded"})
        cookies = {"refresh_token": token_to_refresh}

        print(f":key: Refreshing access token for [bold link]{self.base_url}[/] ...")

        response = requests.post(url, headers=headers, cookies=cookies, data={})
        if response.status_code != 200:
            raise Exception(f"Refresh token failed: {self._get_error_message(response)}")

        self.access_token = str(response.json().get("access_token"))

        return self.access_token

    def list_challenges(self) -> Any:
        """List all challenges."""

        url = f"{self.base_url}/api/challenges"
        response = requests.get(url, headers=self._get_headers())
        if response.status_code != 200:
            raise Exception(self._get_error_message(response))

        return response.json()
