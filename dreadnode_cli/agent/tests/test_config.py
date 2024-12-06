from pathlib import Path
from unittest.mock import patch
from uuid import UUID

import pytest

from dreadnode_cli.agent.cli import ensure_active_profile
from dreadnode_cli.agent.config import AgentConfig
from dreadnode_cli.config import ServerConfig, UserConfig


def test_agent_config_read_not_initialized(tmp_path: Path) -> None:
    with pytest.raises(Exception, match="is not initialized"):
        AgentConfig.read(tmp_path)


def test_agent_config_active_link_no_links() -> None:
    config = AgentConfig(project_name="test")
    with pytest.raises(Exception, match="No agent is currently linked"):
        _ = config.active_link


def test_agent_config_add_link() -> None:
    config = AgentConfig(project_name="test")
    id = UUID("00000000-0000-0000-0000-000000000000")

    config.add_link("test", id, "test")

    assert config.active == "test"
    assert config.links["test"].id == id
    assert config.links["test"].runs == []
    assert config.links["test"].profile == "test"
    assert config.linked_profiles == ["test"]
    assert config.has_link_to_profile("test")
    assert not config.has_link_to_profile("other")


def test_agent_config_add_run() -> None:
    config = AgentConfig(project_name="test")
    agent_id = UUID("00000000-0000-0000-0000-000000000000")
    run_id = UUID("11111111-1111-1111-1111-111111111111")

    config.add_link("test", agent_id, "test")
    config.add_run(run_id)

    assert config.links["test"].runs == [run_id]


def test_agent_config_write_read(tmp_path: Path) -> None:
    config = AgentConfig(project_name="test")
    agent_id = UUID("00000000-0000-0000-0000-000000000000")
    run_id = UUID("11111111-1111-1111-1111-111111111111")

    config.add_link("test", agent_id, "test")
    config.add_run(run_id)
    config.write(tmp_path)

    loaded = AgentConfig.read(tmp_path)
    assert loaded.project_name == "test"
    assert loaded.active == "test"
    assert loaded.links["test"].id == agent_id
    assert loaded.links["test"].runs == [run_id]
    assert loaded.links["test"].profile == "test"


def test_agent_config_update_active() -> None:
    config = AgentConfig(project_name="test")
    id1 = UUID("00000000-0000-0000-0000-000000000000")
    id2 = UUID("11111111-1111-1111-1111-111111111111")

    # Add first link
    config.add_link("test1", id1, "test1")
    assert config.active == "test1"

    # Add second link
    config.add_link("test2", id2, "test2")
    assert config.active == "test2"

    # Remove active link
    config.links.pop("test2")
    config._update_active()
    assert config.active == "test1"

    # Remove all links
    config.links.clear()
    config._update_active()
    assert config.active is None


def test_ensure_profile() -> None:
    agent_config = AgentConfig(project_name="test")
    user_config = UserConfig()

    # We don't have any profiles
    with pytest.raises(Exception, match="No server profile is set"):
        ensure_active_profile(agent_config, user_config=user_config)

    server_config = ServerConfig(
        url="http://test",
        email="test@test.com",
        username="test",
        api_key="test",
        access_token="test",
        refresh_token="test",
    )

    user_config.set_server_config(server_config, profile="main")
    user_config.set_server_config(server_config, profile="other")
    user_config.active = "main"

    # We have no links
    with pytest.raises(Exception, match="No agent is currently linked"):
        ensure_active_profile(agent_config, user_config=user_config)

    # We have a link, but none are available for the current profile
    agent_config.add_link("test-other", UUID("00000000-0000-0000-0000-000000000000"), "other")
    with pytest.raises(Exception, match="This agent is linked to the"):
        ensure_active_profile(agent_config, user_config=user_config)

    # We have another link, but the profiles don't match
    agent_config.add_link("test-main", UUID("00000000-0000-0000-0000-000000000000"), "main")
    agent_config.active = "test-other"
    with patch("rich.prompt.Prompt.ask", return_value="n"):
        with pytest.raises(Exception, match="Agent link does not match the current server profile"):
            ensure_active_profile(agent_config, user_config=user_config)

    # We should switch if the user agrees
    assert user_config.active == "main"
    with patch("rich.prompt.Prompt.ask", return_value="y"), patch("dreadnode_cli.config.UserConfig.write"), patch(
        "dreadnode_cli.config.UserConfig.read", return_value=user_config
    ):
        ensure_active_profile(agent_config, user_config=user_config)
    assert user_config.active == "other"
