import pathlib
import re
import typing as t

import docker  # type: ignore
from docker.models.images import Image  # type: ignore
from rich import print
from rich.live import Live
from rich.text import Text

from dreadnode_cli.config import ServerConfig
from dreadnode_cli.defaults import (
    DOCKER_REGISTRY_IMAGE_TAG,
    DOCKER_REGISTRY_LOCAL_PORT,
    DOCKER_REGISTRY_SUBDOMAIN,
    PLATFORM_BASE_DOMAIN,
)

try:
    client = docker.from_env()
except docker.errors.DockerException:
    client = None


def get_local_registry_port() -> int:
    if client is None:
        raise Exception("Docker not available")

    for container in client.containers.list():
        if DOCKER_REGISTRY_IMAGE_TAG in container.image.tags:
            ports = container.attrs["NetworkSettings"]["Ports"]
            assert len(ports) == 1
            for _container_port, port_bindings in ports.items():
                if port_bindings:
                    for binding in port_bindings:
                        return int(binding["HostPort"])

    # fallback to the default port if we can't find the running container
    return DOCKER_REGISTRY_LOCAL_PORT


def get_registry(config: ServerConfig) -> str:
    # fail early if docker is not available
    if client is None:
        raise Exception("Docker not available")

    # localhost is a special case
    if "localhost" in config.url or "127.0.0.1" in config.url:
        return f"localhost:{get_local_registry_port()}"

    prefix = ""
    if "staging-" in config.url:
        prefix = "staging-"
    elif "dev-" in config.url:
        prefix = "dev-"

    return f"{prefix}{DOCKER_REGISTRY_SUBDOMAIN}.{PLATFORM_BASE_DOMAIN}"


def login(registry: str, username: str, password: str) -> None:
    if client is None:
        raise Exception("Docker not available")

    client.api.login(username=username, password=password, registry=registry)


def sanitized_agent_name(name: str) -> str:
    """
    Sanitizes an agent name to be used as a Docker repository name.
    """

    # convert to lowercase
    name = name.lower()
    # replace non-alphanumeric characters with hyphens
    name = re.sub(r"[^\w\s-]", "", name)
    # replace one or more whitespace characters with a single hyphen
    name = re.sub(r"[-\s]+", "-", name)
    # remove leading or trailing hyphens
    name = name.strip("-")

    return name


def build(directory: str | pathlib.Path, *, force_rebuild: bool = False) -> Image:
    if client is None:
        raise Exception("Docker not available")

    id: str | None = None
    for item in client.api.build(
        path=str(directory), platform="linux/amd64", decode=True, nocache=force_rebuild, pull=force_rebuild
    ):
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
                    # (ENG-280) sometimes docker returns not entirely synced current vs totals
                    percentage = min((current / total) * 100, 100.0)
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
