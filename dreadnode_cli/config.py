import pydantic
from rich import print

from dreadnode_cli.defaults import USER_CONFIG_PATH


class ServerConfig(pydantic.BaseModel):
    """Server specific authentication data and API URL."""

    url: str
    access_token: str
    refresh_token: str


class UserConfig(pydantic.BaseModel):
    """User configuration supporting multiple server profiles."""

    servers: dict[str, ServerConfig] = {}
    active: str = ""

    def _update_active(self) -> None:
        """If active is not set, set it to the first available server and raise an error if no servers are configured."""

        if self.active not in self.servers:
            self.active = next(iter(self.servers)) if self.servers else ""

        if not self.active or not self.servers:
            raise Exception("no servers are configured, use [bold]dreadnode login[/] to authenticate")

    @classmethod
    def read(cls) -> "UserConfig":
        """Read the user configuration from the file system or return an empty instance."""

        if not USER_CONFIG_PATH.exists():
            return cls()

        with USER_CONFIG_PATH.open("r") as f:
            return cls.model_validate_json(f.read())

    def write(self) -> None:
        """Write the user configuration to the file system."""

        if not USER_CONFIG_PATH.parent.exists():
            print(f":rocket: creating user configuration directory: {USER_CONFIG_PATH.parent}")
            USER_CONFIG_PATH.parent.mkdir(parents=True)

        with USER_CONFIG_PATH.open("w") as f:
            f.write(self.model_dump_json(indent=2))

    def get_profile_config(self, profile: str) -> ServerConfig | None:
        """Get the server configuration for the given profile or None if not set."""

        return self.servers.get(profile)

    def set_profile_config(self, profile: str, config: ServerConfig) -> "UserConfig":
        """Set the server configuration for the given profile."""

        self.servers[profile] = config
        return self

    def set_active_config(self, config: ServerConfig) -> "UserConfig":
        """Set the active server configuration."""

        self._update_active()
        self.servers[self.active] = config
        return self

    def remove_profile_config(self, profile: str) -> "UserConfig":
        """Remove the server configuration for the given profile."""

        if profile in self.servers:
            del self.servers[profile]
        return self

    @property
    def active_server(self) -> ServerConfig:
        """Get the active server configuration."""

        self._update_active()
        if not self.active or not self.servers:
            raise Exception("no servers are configured, use [bold]dreadnode login[/] to authenticate")

        return self.servers[self.active]
