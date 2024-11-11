import typing as t
from pathlib import Path

import pytest

import dreadnode_cli.agent.docker as docker
from dreadnode_cli.config import ServerConfig


class MockImage:
    def tag(self, *args: t.Any, **kwargs: t.Any) -> None:
        pass


class MockDockerClient:
    """Simple mock Docker client for testing."""

    class api:
        @staticmethod
        def build(*args: t.Any, **kwargs: t.Any) -> list[dict[str, t.Any]]:
            return [{"stream": "Step 1/1 : FROM hello-world\n"}, {"aux": {"ID": "sha256:mock123"}}]

        @staticmethod
        def push(*args: t.Any, **kwargs: t.Any) -> list[dict[str, t.Any]]:
            return [
                {"status": "Preparing", "id": "layer1"},
                {"status": "Layer already exists", "id": "layer1"},
                {"status": "Pushed", "id": "layer1"},
            ]

        @staticmethod
        def login(*args: t.Any, **kwargs: t.Any) -> dict[str, t.Any]:
            return {"Status": "Login Succeeded"}

    class images:
        @staticmethod
        def get(id: str) -> MockImage:
            return MockImage()


def _create_test_server_config(url: str = "https://crucible.dreadnode.io") -> ServerConfig:
    return ServerConfig(
        url=url,
        email="test@example.com",
        username="test",
        api_key="test",
        access_token="test",
        refresh_token="test",
    )


def test_docker_not_available_get_registry() -> None:
    docker.client = None
    with pytest.raises(Exception, match="Docker not available"):
        docker.get_registry(_create_test_server_config())


def test_docker_not_available_build(tmp_path: Path) -> None:
    docker.client = None
    with pytest.raises(Exception, match="Docker not available"):
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("FROM hello-world")

        image = docker.build(tmp_path)
        assert image is None


def test_docker_not_available_push() -> None:
    docker.client = None
    with pytest.raises(Exception, match="Docker not available"):
        image = MockImage()
        docker.push(image, "test-repo", "latest")


def test_build(tmp_path: Path) -> None:
    # set mock client
    docker.client = MockDockerClient()

    # Create a test Dockerfile
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("FROM hello-world")

    # Test building image
    image = docker.build(tmp_path)
    assert image is not None


def test_push(tmp_path: Path) -> None:
    # set mock client
    docker.client = MockDockerClient()

    # Create and build test image
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("FROM hello-world")
    image = docker.build(tmp_path)

    # Test pushing image
    docker.push(image, "test-repo", "latest")


def test_get_registry() -> None:
    # Test production registry
    config = _create_test_server_config()
    assert docker.get_registry(config) == "registry.dreadnode.io"

    # Test staging registry
    config = _create_test_server_config("https://staging-crucible.dreadnode.io")
    assert docker.get_registry(config) == "staging-registry.dreadnode.io"

    # Test dev registry
    config = _create_test_server_config("https://dev-crucible.dreadnode.io")
    assert docker.get_registry(config) == "dev-registry.dreadnode.io"

    # Test localhost registry
    config = _create_test_server_config("http://localhost:8000")
    assert docker.get_registry(config) == "localhost:5000"


def test_get_registry_without_schema() -> None:
    # Test without schema
    config = _create_test_server_config("crucible.dreadnode.io")
    assert docker.get_registry(config) == "registry.dreadnode.io"

    config = _create_test_server_config("staging-crucible.dreadnode.io")
    assert docker.get_registry(config) == "staging-registry.dreadnode.io"

    config = _create_test_server_config("dev-crucible.dreadnode.io")
    assert docker.get_registry(config) == "dev-registry.dreadnode.io"

    config = _create_test_server_config("localhost:8000")
    assert docker.get_registry(config) == "localhost:5000"


def test_get_registry_custom_platform_base_domain() -> None:
    # Test custom platform base domain
    config = _create_test_server_config("crucible.example.com")
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("dreadnode_cli.agent.docker.PLATFORM_BASE_DOMAIN", "example.com")
        assert docker.get_registry(config) == "registry.example.com"

        config = _create_test_server_config("staging-crucible.example.com")
        assert docker.get_registry(config) == "staging-registry.example.com"

        config = _create_test_server_config("dev-crucible.example.com")
        assert docker.get_registry(config) == "dev-registry.example.com"
