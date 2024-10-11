import requests
from rich import print

from dreadnode_cli import __version__
from dreadnode_cli.defaults import PLATFORM_BASE_URL


class Client:
    api_key: str
    base_url: str

    def __init__(self, base_url: str = PLATFORM_BASE_URL):
        self.base_url = base_url.rstrip("/")

    def _get_headers(self, with_auth: bool = True, additional: dict[str, str] | None = None) -> dict[str, str]:
        headers = {
            "User-Agent": f"dreadnode-cli/{__version__}",
            "Accept": "application/json",
        }

        if with_auth:
            headers["Authorization"] = f"Bearer {self.api_key}"

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

        print(f":key: Authenticating to [bold link]{url}[/] ...")

        response = requests.post(url, data=form_data, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Authentication failed: {self._get_error_message(response)}")

        return str(response.json().get("access_token"))
