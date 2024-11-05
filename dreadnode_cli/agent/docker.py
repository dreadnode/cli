import pathlib
import typing as t

import docker  # type: ignore
from docker.models.images import Image  # type: ignore
from rich import print
from rich.live import Live
from rich.text import Text

from dreadnode_cli.config import ServerConfig

try:
    client = docker.from_env()
except docker.errors.DockerException:
    client = None


# TODO: Poor form having a fixed list of registries IMO
def get_registry(config: ServerConfig) -> str:
    # fail early if docker is not available
    if client is None:
        raise Exception("Docker not available")

    if config.url.startswith("https://crucible.dreadnode.io"):
        return "registry.dreadnode.io"
    elif config.url.startswith("https://staging-crucible.dreadnode.io"):
        return "staging-registry.dreadnode.io"
    elif config.url.startswith("https://dev-crucible.dreadnode.io"):
        return "dev-registry.dreadnode.io"
    elif config.url.startswith("https://dev-crucible.dreadnode.io"):
        return "dev-registry.dreadnode.io"
    elif "localhost" in config.url:
        return "localhost:5000"

    raise Exception(f"Unknown registry for {config.url}")


def login(registry: str, username: str, password: str) -> None:
    if client is None:
        raise Exception("Docker not available")

    client.api.login(username=username, password=password, registry=registry)


def build(directory: str | pathlib.Path) -> Image:
    if client is None:
        raise Exception("Docker not available")

    id: str | None = None
    for item in client.api.build(path=str(directory), platform="linux/amd64", decode=True):
        if "error" in item:
            print()
            raise Exception(item["error"])
        elif "stream" in item:
            print("[dim]" + item["stream"].strip() + "[/]")
        elif "aux" in item:
            id = item["aux"].get("ID")

    if id is None:
        raise Exception("Failed to build image")

    return client.images.get(id)


class DockerPushDisplay:
    def __init__(self) -> None:
        self.lines: list[str | dict[str, t.Any]] = []

    def add_event(self, event: dict[str, t.Any]) -> None:
        if "id" in event:
            if matching_line := next(
                (line for line in self.lines if isinstance(line, dict) and line["id"] == event["id"]), None
            ):
                matching_line.update(event)
            else:
                self.lines.append(event)
        elif "status" in event:
            self.lines.append(event["status"])

    def render(self) -> Text:
        output = Text(style="dim")

        for line in self.lines:
            if isinstance(line, str):
                output.append(line + "\n", style="bold")
                continue

            status = line.get("status", "")

            # Style based on status
            style = {
                "Preparing": "yellow",
                "Waiting": "blue",
                "Layer already exists": "green",
                "Pushed": "green",
            }.get(status, "white")

            # Write the line
            output.append(f"{line['id']}: ")
            output.append(status, style=style)

            # Add progress if available
            if "progressDetail" in line and line["progressDetail"]:
                current = line["progressDetail"].get("current", 0)
                total = line["progressDetail"].get("total", 0)
                if total > 0:
                    percentage = (current / total) * 100
                    output.append(f" {percentage:.1f}%", style="cyan")

            output.append("\n")

        return output


def push(image: Image, repository: str, tag: str) -> None:
    if client is None:
        raise Exception("Docker not available")

    image.tag(repository, tag=tag)

    display = DockerPushDisplay()

    with Live(Text(), refresh_per_second=10) as live:
        for event in client.api.push(repository, tag=tag, stream=True, decode=True):
            if "error" in event:
                live.stop()
                raise Exception(event["error"])

            display.add_event(event)
            live.update(display.render())
