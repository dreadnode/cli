from pathlib import Path
from uuid import UUID

import pytest

from dreadnode_cli.agent.config import AgentConfig


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

    config.add_link("test", id)

    assert config.active == "test"
    assert config.links["test"].id == id
    assert config.links["test"].runs == []


def test_agent_config_add_run() -> None:
    config = AgentConfig(project_name="test")
    agent_id = UUID("00000000-0000-0000-0000-000000000000")
    run_id = UUID("11111111-1111-1111-1111-111111111111")

    config.add_link("test", agent_id)
    config.add_run(run_id)

    assert config.links["test"].runs == [run_id]


def test_agent_config_write_read(tmp_path: Path) -> None:
    config = AgentConfig(project_name="test")
    agent_id = UUID("00000000-0000-0000-0000-000000000000")
    run_id = UUID("11111111-1111-1111-1111-111111111111")

    config.add_link("test", agent_id)
    config.add_run(run_id)
    config.write(tmp_path)

    loaded = AgentConfig.read(tmp_path)
    assert loaded.project_name == "test"
    assert loaded.active == "test"
    assert loaded.links["test"].id == agent_id
    assert loaded.links["test"].runs == [run_id]


def test_agent_config_update_active() -> None:
    config = AgentConfig(project_name="test")
    id1 = UUID("00000000-0000-0000-0000-000000000000")
    id2 = UUID("11111111-1111-1111-1111-111111111111")

    # Add first link
    config.add_link("test1", id1)
    assert config.active == "test1"

    # Add second link
    config.add_link("test2", id2)
    assert config.active == "test2"

    # Remove active link
    config.links.pop("test2")
    config._update_active()
    assert config.active == "test1"

    # Remove all links
    config.links.clear()
    config._update_active()
    assert config.active is None
