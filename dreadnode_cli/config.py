import os
import pathlib

import pydantic
import typer
from rich import print

user_config_path = pathlib.Path(
    os.getenv("DREADNODE_USER_CONFIG_FILE") or pathlib.Path.home() / ".dreadnode" / "config.json"
)


class ServerConfig(pydantic.BaseModel):
    url: str
    username: str
    api_key: str


class UserConfig(pydantic.BaseModel):
    servers: dict[str, ServerConfig] = {}
    active: str | None = None

    def _update_active(self) -> None:
        if self.active not in self.servers:
            self.active = next(iter(self.servers)) if self.servers else None

    @classmethod
    def read(cls) -> "UserConfig":
        if not user_config_path.exists():
            return cls()

        with user_config_path.open("r") as f:
            return cls.model_validate_json(f.read())

    def write(self) -> None:
        self._update_active()
        user_config_path.parent.mkdir(parents=True, exist_ok=True)
        with user_config_path.open("w") as f:
            f.write(self.model_dump_json(indent=2))

    @property
    def server(self) -> ServerConfig:
        self._update_active()
        if not self.active or not self.servers:
            print()
            print(":exclamation: No servers are configured")
            print()
            print("Use [bold]dreadnode login[/] to authenticate")
            raise typer.Exit(1)

        return self.servers[self.active]
