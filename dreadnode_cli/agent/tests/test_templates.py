import pathlib
from unittest.mock import patch

import pytest

from dreadnode_cli.agent import templates


def test_templates_install(tmp_path: pathlib.Path) -> None:
    with patch("rich.prompt.Prompt.ask", return_value="y"):
        templates.install_template(templates.Template.rigging_basic, tmp_path, {"name": "World"})

    assert (tmp_path / "requirements.txt").exists()
    assert (tmp_path / "Dockerfile").exists()
    assert (tmp_path / "agent.py").exists()


def test_templates_install_from_dir(tmp_path: pathlib.Path) -> None:
    templates.install_template_from_dir(templates.TEMPLATES_DIR / "rigging_basic", tmp_path, {"name": "World"})

    assert (tmp_path / "requirements.txt").exists()
    assert (tmp_path / "Dockerfile").exists()
    assert (tmp_path / "agent.py").exists()


def test_templates_install_from_dir_with_dockerfile_template(tmp_path: pathlib.Path) -> None:
    # create source directory
    source_dir = tmp_path / "source"
    source_dir.mkdir()

    # create a Dockerfile.j2 template
    dockerfile_content = """
FROM python:3.9
WORKDIR /app
ENV APP_NAME={{name}}
COPY . .
CMD ["python", "app.py"]
"""
    (source_dir / "Dockerfile.j2").write_text(dockerfile_content)

    # create destination directory
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    # install template
    templates.install_template_from_dir(source_dir, dest_dir, {"name": "TestContainer"})

    # verify Dockerfile was rendered correctly
    expected_dockerfile = """
FROM python:3.9
WORKDIR /app
ENV APP_NAME=TestContainer
COPY . .
CMD ["python", "app.py"]
"""
    assert (dest_dir / "Dockerfile").exists()
    assert (dest_dir / "Dockerfile").read_text().strip() == expected_dockerfile.strip()


def test_templates_install_from_dir_nested_structure(tmp_path: pathlib.Path) -> None:
    # create source directory with nested structure
    source_dir = tmp_path / "source"
    source_dir.mkdir()

    # create some regular files
    (source_dir / "Dockerfile").touch()
    (source_dir / "README.md").write_text("# Test Project")

    # create nested folders with files
    config_dir = source_dir / "config"
    config_dir.mkdir()
    (config_dir / "settings.json").write_text('{"debug": true}')

    templates_dir = source_dir / "templates"
    templates_dir.mkdir()
    (templates_dir / "base.html.j2").write_text("<html><body>Hello {{name}}!</body></html>")

    src_dir = source_dir / "src"
    src_dir.mkdir()
    (src_dir / "main.py").touch()

    # deeper nested folder
    utils_dir = src_dir / "utils"
    utils_dir.mkdir()
    (utils_dir / "helpers.py").touch()
    (utils_dir / "config.py.j2").write_text("APP_NAME = '{{name}}'")

    # create destination directory
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    # install template
    templates.install_template_from_dir(source_dir, dest_dir, {"name": "TestApp"})

    # verify regular files were copied
    assert (dest_dir / "Dockerfile").exists()
    assert (dest_dir / "README.md").read_text() == "# Test Project"

    # verify nested structure and files
    assert (dest_dir / "config" / "settings.json").read_text() == '{"debug": true}'
    assert (dest_dir / "src" / "main.py").exists()
    assert (dest_dir / "src" / "utils" / "helpers.py").exists()

    # verify j2 templates were rendered correctly
    assert (dest_dir / "templates" / "base.html").read_text() == "<html><body>Hello TestApp!</body></html>"
    assert (dest_dir / "src" / "utils" / "config.py").read_text() == "APP_NAME = 'TestApp'"


def test_templates_install_from_dir_missing_source(tmp_path: pathlib.Path) -> None:
    source_dir = tmp_path / "nonexistent"
    with pytest.raises(Exception, match="Source directory '.*' does not exist"):
        templates.install_template_from_dir(source_dir, tmp_path, {"name": "World"})


def test_templates_install_from_dir_source_is_file(tmp_path: pathlib.Path) -> None:
    source_file = tmp_path / "source.txt"
    source_file.touch()

    with pytest.raises(Exception, match="Source '.*' is not a directory"):
        templates.install_template_from_dir(source_file, tmp_path, {"name": "World"})


def test_templates_install_from_dir_missing_dockerfile(tmp_path: pathlib.Path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "agent.py").touch()

    with pytest.raises(Exception, match="Source directory .+ does not contain a Dockerfile"):
        templates.install_template_from_dir(source_dir, tmp_path, {"name": "World"})


def test_templates_install_from_dir_single_inner_folder(tmp_path: pathlib.Path) -> None:
    # create a source directory with a single inner folder to simulate a github zip archive
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    inner_dir = source_dir / "project-main"
    inner_dir.mkdir()

    # create a Dockerfile in the inner directory
    (inner_dir / "Dockerfile").touch()
    (inner_dir / "agent.py").touch()

    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    # install from the outer directory - should detect and use inner directory
    templates.install_template_from_dir(inner_dir, dest_dir, {"name": "World"})

    # assert files were copied from inner directory
    assert (dest_dir / "Dockerfile").exists()
    assert (dest_dir / "agent.py").exists()


def test_templates_install_from_dir_with_path(tmp_path: pathlib.Path) -> None:
    # create source directory with subdirectories
    source_dir = tmp_path / "source"
    source_dir.mkdir()

    # create files in subdirectory
    (source_dir / "Dockerfile").touch()
    (source_dir / "agent.py").touch()

    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    # install from subdirectory path
    templates.install_template_from_dir(tmp_path / "source", dest_dir, {"name": "World"})

    # assert files were copied from subdirectory
    assert (dest_dir / "Dockerfile").exists()
    assert (dest_dir / "agent.py").exists()


def test_templates_install_from_dir_invalid_path(tmp_path: pathlib.Path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "Dockerfile").touch()

    with pytest.raises(Exception, match="Source directory '.*' does not exist"):
        templates.install_template_from_dir(source_dir / "nonexistent", tmp_path, {"name": "World"})
