import pathlib
import typing as t

import pydantic

default_config_path = pathlib.Path(".dreadnode.json")


class AgentConfig(pydantic.BaseModel):
    name: str
    agents: list[str] = []

    @classmethod
    def read(cls, *, path: pathlib.Path | None = None) -> t.Optional["AgentConfig"]:
        path = path or default_config_path
        if not path.exists():
            return None

        with path.open("r") as f:
            return cls.model_validate_json(f.read())

    def write(self, *, path: pathlib.Path | None = None) -> None:
        with (path or default_config_path).open("w") as f:
            f.write(self.model_dump_json(indent=2))
