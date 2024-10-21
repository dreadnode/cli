import pathlib

import docker  # type: ignore
from docker.models.images import Image  # type: ignore
from rich import print

from dreadnode_cli.config import ServerConfig

client = docker.from_env()


def get_registry(config: ServerConfig) -> str:
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
    client.api.login(username=username, password=password, registry=registry)


def build(directory: str | pathlib.Path) -> Image:
    id: str | None = None
    for item in client.api.build(path=str(directory), platform="linux/amd64", decode=True):
        if "error" in item:
            print()
            raise Exception(item["error"])
        elif "stream" in item:
            print("[dim]" + item["stream"].strip() + "[/]")
        elif "aux" in item:
            id = item["aux"]["ID"]

    if id is None:
        raise Exception("Failed to build image")

    return client.images.get(id)


def push(image: Image, repository: str, tag: str) -> None:
    image.tag(repository, tag=tag)
    for item in client.api.push(repository, tag=tag, stream=True, decode=True):
        if "error" in item:
            print()
            raise Exception(item["error"])
        elif "status" in item:
            print("[dim]" + item["status"].strip() + "[/]")
