import pathlib

from pydantic import BaseModel, field_validator
from rich import print
from ruamel.yaml import YAML

from dreadnode_cli.dreadnode.defaults import DEFAULT_PROFILE_NAME, USER_CONFIG_PATH, USER_MODELS_CONFIG_PATH

AGENT_CONFIG_FILENAME = ".dreadnode.yaml"


class ServerConfig(BaseModel):
    """Server specific authentication data and API URL."""

    url: str
    email: str
    username: str
    api_key: str
    access_token: str
    refresh_token: str


class UserConfig(BaseModel):
    """User configuration supporting multiple server profiles."""

    active: str | None = None
    servers: dict[str, ServerConfig] = {}

    def _update_active(self) -> None:
        """If active is not set, set it to the first available server and raise an error if no servers are configured."""

        if self.active not in self.servers:
            self.active = next(iter(self.servers)) if self.servers else None

    @classmethod
    def read(cls, from_path: pathlib.Path = USER_CONFIG_PATH) -> "UserConfig":
        """Read the user configuration from the file system or return an empty instance."""

        if not from_path.exists():
            return cls()

        with from_path.open("r") as f:
            return cls.model_validate(YAML().load(f))

    def write(self, to_path: pathlib.Path = USER_CONFIG_PATH) -> None:
        """Write the user configuration to the file system."""

        self._update_active()

        if not to_path.parent.exists():
            print(f":rocket: Creating config at {to_path.parent}")
            to_path.parent.mkdir(parents=True)

        with to_path.open("w") as f:
            YAML().dump(self.model_dump(mode="json"), f)

    @property
    def active_profile_name(self) -> str | None:
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


class UserModel(BaseModel):
    """
    A user defined inference model.
    """

    name: str | None = None
    provider: str | None = None
    generator_id: str
    api_key: str

    @field_validator("generator_id", mode="after")
    def check_for_api_key_in_generator_id(cls, value: str) -> str:
        """Print a warning if an API key is included in the generator ID."""

        if ",api_key=" in value:
            print(f":heavy_exclamation_mark: API keys should not be included in generator ids: [bold]{value}[/]")
            print()

        return value


class UserModels(BaseModel):
    """User models configuration."""

    models: dict[str, UserModel] = {}

    @classmethod
    def read(cls, from_path: pathlib.Path = USER_MODELS_CONFIG_PATH) -> "UserModels":
        """Read the user models configuration from the file system or return an empty instance."""

        if not from_path.exists():
            return cls()

        with from_path.open("r") as f:
            return cls.model_validate(YAML().load(f))

    def write(self, to_path: pathlib.Path = USER_MODELS_CONFIG_PATH) -> None:
        """Write the user models configuration to the file system."""

        with to_path.open("w") as f:
            YAML().dump(self.model_dump(mode="json", exclude_none=True), f)
