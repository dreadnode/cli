import pydantic
from rich import print
from ruamel.yaml import YAML

from dreadnode_cli.defaults import DEFAULT_PROFILE_NAME, USER_CONFIG_PATH


class ServerConfig(pydantic.BaseModel):
    """Server specific authentication data and API URL."""

    url: str
    email: str
    username: str
    api_key: str
    access_token: str
    refresh_token: str


class UserConfig(pydantic.BaseModel):
    """User configuration supporting multiple server profiles."""

    active: str | None = None
    servers: dict[str, ServerConfig] = {}

    def _update_active(self) -> None:
        """If active is not set, set it to the first available server and raise an error if no servers are configured."""

        if self.active not in self.servers:
            self.active = next(iter(self.servers)) if self.servers else None

    @classmethod
    def read(cls) -> "UserConfig":
        """Read the user configuration from the file system or return an empty instance."""

        if not USER_CONFIG_PATH.exists():
            return cls()

        with USER_CONFIG_PATH.open("r") as f:
            return cls.model_validate(YAML().load(f))

    def write(self) -> None:
        """Write the user configuration to the file system."""

        self._update_active()

        if not USER_CONFIG_PATH.parent.exists():
            print(f":rocket: Creating config at {USER_CONFIG_PATH.parent}")
            USER_CONFIG_PATH.parent.mkdir(parents=True)

        with USER_CONFIG_PATH.open("w") as f:
            YAML().dump(self.model_dump(mode="json"), f)

    @property
    def active_profile_name(self) -> str:
        """Get the name of the active profile."""
        self._update_active()
        return self.active

    def get_server_config(self, profile: str | None = None) -> ServerConfig:
        """Get the server configuration for the given profile or None if not set."""

        profile = profile or self.active
        if not profile:
            raise Exception("No profile is set, use [bold]dreadnode login[/] to authenticate")

        if profile not in self.servers:
            raise Exception(f"No server configuration for profile: {profile}")

        return self.servers[profile]

    def set_server_config(self, config: ServerConfig, profile: str | None = None) -> "UserConfig":
        """Set the server configuration for the given profile."""

        profile = profile or self.active or DEFAULT_PROFILE_NAME
        self.servers[profile] = config
        return self
