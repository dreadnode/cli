import pathlib
import typing as t

import pydantic
from ruamel.yaml import YAML

default_config_path = pathlib.Path(".dreadnode.yaml")

yaml = YAML(typ="safe", pure=True)


class AgentConfig(pydantic.BaseModel):
    name: str
    agents: list[str] = []

    @classmethod
    def read(cls, *, path: pathlib.Path | None = None) -> t.Optional["AgentConfig"]:
        path = path or default_config_path
        if not path.exists():
            return None

        with path.open("r") as f:
            return cls.model_validate(yaml.load(f))

    def write(self, *, path: pathlib.Path | None = None) -> None:
        with (path or default_config_path).open("w") as f:
            yaml.dump(self.model_dump(), f)
