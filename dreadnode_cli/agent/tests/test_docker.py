import typing as t
from pathlib import Path

import dreadnode_cli.agent.docker as docker


class MockDockerClient:
    """Simple mock Docker client for testing."""

    class api:
        @staticmethod
        def build(*args, **kwargs) -> list[dict[str, t.Any]]:
            return [{"stream": "Step 1/1 : FROM hello-world\n"}, {"aux": {"ID": "sha256:mock123"}}]

        @staticmethod
        def push(*args, **kwargs) -> list[dict[str, t.Any]]:
            return [
                {"status": "Preparing", "id": "layer1"},
                {"status": "Layer already exists", "id": "layer1"},
                {"status": "Pushed", "id": "layer1"},
            ]

        @staticmethod
        def login(*args, **kwargs) -> dict[str, t.Any]:
            return {"Status": "Login Succeeded"}

    class images:
        @staticmethod
        def get(id: str) -> "MockDockerClient.images.MockImage":
            class MockImage:
                def tag(self, *args, **kwargs):
                    pass

            return MockImage()


async def test_build(tmp_path: Path) -> None:
    # set mock client
    docker.client = MockDockerClient()

    # Create a test Dockerfile
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("FROM hello-world")

    # Test building image
    image = docker.build(tmp_path)
    assert image is not None


async def test_push(tmp_path: Path) -> None:
    # set mock client
    docker.client = MockDockerClient()

    # Create and build test image
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("FROM hello-world")
    image = docker.build(tmp_path)

    # Test pushing image
    docker.push(image, "test-repo", "latest")


async def test_get_registry() -> None:
    from dreadnode_cli.config import ServerConfig

    # Test production registry
    config = ServerConfig(
        url="https://crucible.dreadnode.io",
        email="test@example.com",
        username="test",
        api_key="test",
        access_token="test",
        refresh_token="test",
    )
    assert docker.get_registry(config) == "registry.dreadnode.io"

    # Test staging registry
    config = ServerConfig(
        url="https://staging-crucible.dreadnode.io",
        email="test@example.com",
        username="test",
        api_key="test",
        access_token="test",
        refresh_token="test",
    )
    assert docker.get_registry(config) == "staging-registry.dreadnode.io"

    # Test dev registry
    config = ServerConfig(
        url="https://dev-crucible.dreadnode.io",
        email="test@example.com",
        username="test",
        api_key="test",
        access_token="test",
        refresh_token="test",
    )
    assert docker.get_registry(config) == "dev-registry.dreadnode.io"

    # Test localhost registry
    config = ServerConfig(
        url="http://localhost:8000",
        email="test@example.com",
        username="test",
        api_key="test",
        access_token="test",
        refresh_token="test",
    )
    assert docker.get_registry(config) == "localhost:5000"
