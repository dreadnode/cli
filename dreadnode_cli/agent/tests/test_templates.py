import pathlib
from unittest.mock import patch

from dreadnode_cli.agent import templates


def test_templates_install(tmp_path: pathlib.Path) -> None:
    with patch("rich.prompt.Prompt.ask", return_value="y"):
        templates.install_template(templates.Template.rigging_basic, tmp_path, {"name": "World"})

    assert (tmp_path / "requirements.txt").exists()
    assert (tmp_path / "Dockerfile").exists()
    assert (tmp_path / "agent.py").exists()
