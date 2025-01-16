import pathlib
from uuid import UUID

import pydantic
from ruamel.yaml import YAML

AGENT_CONFIG_FILENAME = ".dreadnode.yaml"


class AgentLink(pydantic.BaseModel):
    profile: str
    id: UUID
    runs: list[UUID] = []


class AgentConfig(pydantic.BaseModel):
    project_name: str
    strike: str | None = None
    active: str | None = None
    links: dict[str, AgentLink] = {}

    def _update_active(self) -> None:
        if self.active not in self.links:
            self.active = next(iter(self.links)) if self.links else None

    @property
    def active_link(self) -> AgentLink:
        if self.active is None:
            raise Exception("No agent is currently linked, use [bold]dreadnode agent push[/]")
        return self.links[self.active]

    @classmethod
    def read(cls, directory: pathlib.Path = pathlib.Path(".")) -> "AgentConfig":
        path = directory / AGENT_CONFIG_FILENAME
        if not path.exists():
            raise Exception(f"{directory} is not initialized, use [bold]dreadnode agent init[/]")

        with path.open("r") as f:
            return cls.model_validate(YAML().load(f))

    def write(self, directory: pathlib.Path = pathlib.Path(".")) -> None:
        self._update_active()
        with (directory / AGENT_CONFIG_FILENAME).open("w") as f:
            YAML().dump(self.model_dump(mode="json"), f)

    def add_link(self, key: str, id: UUID, profile: str) -> "AgentConfig":
        if key not in self.links:
            self.links[key] = AgentLink(id=id, profile=profile)
        self.active = key
        return self

    @property
    def linked_profiles(self) -> list[str]:
        return list({link.profile for link in self.links.values()})

    def has_link_to_profile(self, profile: str) -> bool:
        return any(link.profile == profile for link in self.links.values())

    def add_run(self, id: UUID) -> "AgentConfig":
        self.active_link.runs.append(id)
        return self
