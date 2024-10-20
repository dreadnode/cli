import pathlib
from uuid import UUID

import pydantic
from ruamel.yaml import YAML

AGENT_CONFIG_FILENAME = ".dreadnode.yaml"


class AgentConfig(pydantic.BaseModel):
    name: str
    strike: str | None = None
    active: UUID | None = None
    links: list[UUID] = []

    def _update_active(self) -> None:
        if self.active not in self.links:
            self.active = next(iter(self.links), None)

    @classmethod
    def read(cls, directory: pathlib.Path = pathlib.Path(".")) -> "AgentConfig":
        path = directory / AGENT_CONFIG_FILENAME
        if not path.exists():
            raise Exception(f"{path} does not exist")

        with path.open("r") as f:
            return cls.model_validate(YAML().load(f))

    def write(self, directory: pathlib.Path = pathlib.Path(".")) -> None:
        self._update_active()
        with (directory / AGENT_CONFIG_FILENAME).open("w") as f:
            YAML().dump(self.model_dump(mode="json"), f)

    def add_link(self, id: UUID) -> "AgentConfig":
        self.links.append(id)
        return self

    def remove_link(self, id: UUID) -> "AgentConfig":
        self.links.remove(id)
        return self
