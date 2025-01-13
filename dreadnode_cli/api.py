import atexit
import json
import time
import typing as t
from datetime import datetime, timezone
from urllib.parse import urlparse
from uuid import UUID

import httpx
from pydantic import BaseModel
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
        _cookies = httpx.Cookies()
        cookie_domain = urlparse(base_url).hostname
        if cookie_domain is None:
            raise Exception(f"Invalid URL: {base_url}")

        if "localhost" == cookie_domain:
            cookie_domain = "localhost.local"

        for key, value in (cookies or {}).items():
            _cookies.set(key, value, domain=cookie_domain)

        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            cookies=_cookies,
            headers={
                "User-Agent": f"dreadnode-cli/{__version__}",
                "Accept": "application/json",
            },
            base_url=self._base_url,
            timeout=30,
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
        query_params: dict[str, str] | None = None,
        json_data: dict[str, t.Any] | None = None,
    ) -> httpx.Response:
        """Make a raw request to the API."""

        return self._client.request(method, path, json=json_data, params=query_params)

    def request(
        self,
        method: str,
        path: str,
        query_params: dict[str, str] | None = None,
        json_data: dict[str, t.Any] | None = None,
    ) -> httpx.Response:
        """Make a request to the API. Raise an exception for non-200 status codes."""

        response = self._request(method, path, query_params, json_data)

        if response.status_code == 401:
            raise Exception("Authentication expired, use [bold]dreadnode login[/]")

        try:
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            raise Exception(self._get_error_message(response)) from e

    # Auth

    def url_for_user_code(self, user_code: str) -> str:
        """Get the URL to verify the user code."""

        return f"{self._base_url}/account/device?code={user_code}"

    class DeviceCodeResponse(BaseModel):
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
        return self.DeviceCodeResponse(**response.json())

    class AccessRefreshTokenResponse(BaseModel):
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
                return self.AccessRefreshTokenResponse(**response.json())
            elif response.status_code != 401:
                raise Exception(self._get_error_message(response))

            time.sleep(interval)

        raise Exception("Polling for token timed out")

    # User

    class UserAPIKeyResponse(BaseModel):
        key: str

    class UserResponse(BaseModel):
        id: UUID
        email_address: str
        username: str
        api_key: "Client.UserAPIKeyResponse"

    def get_user(self) -> UserResponse:
        """Get the user email and username."""

        response = self.request("GET", "/api/user")
        return self.UserResponse(**response.json())

    # Challenges

    class ChallengeResponse(BaseModel):
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
        return [self.ChallengeResponse(**challenge) for challenge in response.json()]

    def get_challenge_artifact(self, challenge: str, artifact_name: str) -> bytes:
        """Get a challenge artifact."""

        response = self.request("GET", f"/api/artifacts/{challenge}/{artifact_name}")
        return response.content

    def submit_challenge_flag(self, challenge: str, flag: str) -> bool:
        """Submit a flag to a challenge."""

        response = self.request("POST", f"/api/challenges/{challenge}/submit-flag", json_data={"flag": flag})
        return bool(response.json().get("correct", False))

    # Github

    class GithubTokenResponse(BaseModel):
        token: str
        expires_at: datetime
        repos: list[str]

    def get_github_access_token(self, repos: list[str]) -> GithubTokenResponse:
        """Try to get a GitHub access token for the given repositories."""
        response = self.request("POST", "/api/github/token", json_data={"repos": repos})
        return self.GithubTokenResponse(**response.json())

    # Strikes

    StrikeRunStatus = t.Literal[
        "pending",  # Waiting to be processed in the DB
        "deploying",  # Dropship pod is being created and configured
        "running",  # Dropship pod is actively executing
        "completed",  # All zones finished successfully
        "mixed",  # Some zones succeeded, others terminated
        "terminated",  # All zones ended with non-zero exit codes
        "timeout",  # Maximum allowed run time was exceeded
        "failed",  # System/infrastructure error occurred
    ]
    StrikeRunZoneStatus = t.Literal[
        "pending",  # Waiting to be processed in the DB
        "deploying",  # Dropship is creating the zone resources
        "running",  # Zone pods are actively executing
        "completed",  # Agent completed successfully (exit code 0)
        "terminated",  # Agent ended with non-zero exit code
        "timeout",  # Maximum allowed run time was exceeded
        "failed",  # System/infrastructure error occurred
    ]

    class StrikeModel(BaseModel):
        key: str
        name: str
        provider: str

    class StrikeZone(BaseModel):
        key: str
        name: str
        guidance: str | None
        description: str | None

    class StrikeSummaryResponse(BaseModel):
        id: UUID
        key: str
        competitive: bool
        models: list["Client.StrikeModel"]
        type: str
        name: str
        description: str | None

    class StrikeResponse(StrikeSummaryResponse):
        zones: list["Client.StrikeZone"]
        guidance: str | None
        description: str | None

    class Container(BaseModel):
        image: str
        env: dict[str, str]
        name: str | None

    class StrikeAgentVersion(BaseModel):
        id: UUID
        created_at: datetime
        notes: str | None
        container: "Client.Container"

    class StrikeAgentResponse(BaseModel):
        id: UUID
        user_id: UUID
        strike_id: UUID | None
        key: str
        name: str | None
        created_at: datetime
        latest_run_status: "Client.StrikeRunStatus | None"
        latest_run_id: UUID | None
        versions: list["Client.StrikeAgentVersion"]
        latest_version: "Client.StrikeAgentVersion"
        revision: int

    class StrikeAgentSummaryResponse(BaseModel):
        id: UUID
        user_id: UUID
        strike_id: UUID | None
        key: str
        name: str | None
        created_at: datetime
        latest_run_status: "Client.StrikeRunStatus | None"
        latest_run_id: UUID | None
        latest_version: "Client.StrikeAgentVersion"
        revision: int

    class StrikeRunOutputScore(BaseModel):
        value: int | float | bool
        explanation: str | None = None
        metadata: dict[str, t.Any] = {}

    class StrikeRunOutputSummary(BaseModel):
        score: t.Optional["Client.StrikeRunOutputScore"] = None
        metadata: dict[str, t.Any] = {}

    class StrikeRunOutput(StrikeRunOutputSummary):
        data: dict[str, t.Any]

    class _StrikeRunZone(BaseModel):
        key: str
        status: "Client.StrikeRunZoneStatus"
        start: datetime | None
        end: datetime | None

    class StrikeRunZoneSummary(_StrikeRunZone):
        outputs: list["Client.StrikeRunOutputSummary"]

    class StrikeRunZone(_StrikeRunZone):
        agent_logs: str | None
        container_logs: dict[str, str]
        outputs: list["Client.StrikeRunOutput"]
        inferences: list[dict[str, t.Any]]

    class _StrikeRun(BaseModel):
        id: UUID
        strike_id: UUID
        strike_key: str
        strike_name: str
        strike_type: str
        strike_description: str | None
        model: str | None
        agent_id: UUID
        agent_key: str
        agent_name: str | None = None
        agent_revision: int
        agent_version: "Client.StrikeAgentVersion"
        status: "Client.StrikeRunStatus"
        start: datetime | None
        end: datetime | None

        def is_running(self) -> bool:
            return self.status in ["pending", "deploying", "running"]

    class StrikeRunSummaryResponse(_StrikeRun):
        zones: list["Client.StrikeRunZoneSummary"]

    class StrikeRunResponse(_StrikeRun):
        zones: list["Client.StrikeRunZone"]

    class UserModel(BaseModel):
        key: str
        generator_id: str
        api_key: str

    def get_strike(self, strike: str) -> StrikeResponse:
        response = self.request("GET", f"/api/strikes/{strike}")
        return self.StrikeResponse(**response.json())

    def list_strikes(self) -> list[StrikeSummaryResponse]:
        response = self.request("GET", "/api/strikes")
        return [self.StrikeResponse(**strike) for strike in response.json()]

    def list_strike_agents(self, strike_id: UUID | None = None) -> list[StrikeAgentSummaryResponse]:
        response = self.request(
            "GET",
            "/api/strikes/agents",
            query_params={"strike_id": str(strike_id)} if strike_id else None,
        )
        return [self.StrikeAgentSummaryResponse(**agent) for agent in response.json()]

    def get_strike_agent(self, agent: UUID | str) -> StrikeAgentResponse:
        response = self.request("GET", f"/api/strikes/agents/{agent}")
        return self.StrikeAgentResponse(**response.json())

    def create_strike_agent(
        self, container: Container, name: str, strike: str | None = None, notes: str | None = None
    ) -> StrikeAgentResponse:
        response = self.request(
            "POST",
            "/api/strikes/agents",
            json_data={
                "container": container.model_dump(mode="json"),
                "strike": strike,
                "name": name,
                "notes": notes,
            },
        )
        return self.StrikeAgentResponse(**response.json())

    def update_strike_agent(self, agent: str, name: str) -> StrikeAgentResponse:
        response = self.request("PATCH", f"/api/strikes/agents/{agent}", json_data={"name": name})
        return self.StrikeAgentResponse(**response.json())

    def create_strike_agent_version(
        self, agent: str, container: Container, notes: str | None = None
    ) -> StrikeAgentResponse:
        response = self.request(
            "POST",
            f"/api/strikes/agents/{agent}/versions",
            json_data={
                "container": container.model_dump(mode="json"),
                "notes": notes,
            },
        )
        return self.StrikeAgentResponse(**response.json())

    def start_strike_run(
        self,
        agent_version_id: UUID,
        *,
        model: str | None = None,
        user_model: UserModel | None = None,
        strike: UUID | str | None = None,
    ) -> StrikeRunResponse:
        response = self.request(
            "POST",
            "/api/strikes/runs",
            json_data={
                "agent_version_id": str(agent_version_id),
                "model": model,
                "user_model": user_model.model_dump(mode="json") if user_model else None,
                "strike": str(strike) if strike else None,
            },
        )
        return self.StrikeRunResponse(**response.json())

    def get_strike_run(self, run: UUID | str) -> StrikeRunResponse:
        response = self.request("GET", f"/api/strikes/runs/{run}")
        return self.StrikeRunResponse(**response.json())

    def list_strike_runs(self, *, strike_id: UUID | str | None = None) -> list[StrikeRunSummaryResponse]:
        response = self.request(
            "GET", "/api/strikes/runs", query_params={"strike_id": str(strike_id)} if strike_id else None
        )
        return [self.StrikeRunSummaryResponse(**run) for run in response.json()]


def create_client(*, profile: str | None = None) -> Client:
    """Create an authenticated API client using stored configuration data."""

    user_config = UserConfig.read()
    config = user_config.get_server_config(profile)

    client = Client(config.url, cookies={"access_token": config.access_token, "refresh_token": config.refresh_token})

    # Pre-emptively check if the token is expired
    if Token(config.refresh_token).is_expired():
        raise Exception("Authentication expired, use [bold]dreadnode login[/]")

    def _flush_auth_changes() -> None:
        """Flush the authentication data to disk if it has been updated."""

        access_token = client._client.cookies.get("access_token")
        refresh_token = client._client.cookies.get("refresh_token")

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
