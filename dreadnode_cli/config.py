import datetime

import pydantic
import typer
from rich import print

from dreadnode_cli.defaults import USER_CONFIG_PATH


class ServerConfig(pydantic.BaseModel):
    url: str
    username: str
    access_token: str
    created_at: datetime.datetime = datetime.datetime.now()
    updated_at: datetime.datetime | None = None


class UserConfig(pydantic.BaseModel):
    servers: dict[str, ServerConfig] = {}
    active: str | None = None

    def _update_active(self) -> None:
        if self.active not in self.servers:
            self.active = next(iter(self.servers)) if self.servers else None

    @classmethod
    def read(cls) -> "UserConfig":
        if not USER_CONFIG_PATH.exists():
            return cls()

        with USER_CONFIG_PATH.open("r") as f:
            return cls.model_validate_json(f.read())

    def write(self) -> None:
        self._update_active()

        if not USER_CONFIG_PATH.parent.exists():
            print(f":rocket: Creating user configuration directory: {USER_CONFIG_PATH.parent}")
            USER_CONFIG_PATH.parent.mkdir(parents=True)

        with USER_CONFIG_PATH.open("w") as f:
            f.write(self.model_dump_json(indent=2))

    def set_profile_config(self, profile: str, config: ServerConfig) -> "UserConfig":
        self.servers[profile] = config
        return self

    def remove_profile_config(self, profile: str) -> "UserConfig":
        if profile in self.servers:
            del self.servers[profile]
        return self

    @property
    def active_server(self) -> ServerConfig:
        self._update_active()
        if not self.active or not self.servers:
            print()
            print(":exclamation: No servers are configured")
            print()
            print("Use [bold]dreadnode login[/] to authenticate")
            raise typer.Exit(1)

        return self.servers[self.active]
