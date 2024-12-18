import pathlib

import pytest

from dreadnode_cli.agent.templates.manager import TemplateManager


def test_manager_is_empty_when_no_templates(tmp_path: pathlib.Path) -> None:
    assert len(TemplateManager(tmp_path).templates) == 0


def test_manager_is_not_empty_with_test_template(tmp_path: pathlib.Path) -> None:
    (tmp_path / "test").mkdir()
    (tmp_path / "test" / "manifest.yaml").write_text("description: test")
    assert len(TemplateManager(tmp_path).templates) == 1


def test_manager_raises_with_invalid_template(tmp_path: pathlib.Path) -> None:
    manager = TemplateManager(tmp_path)
    with pytest.raises(Exception, match="Template '.*' not found"):
        manager.install("test", tmp_path, {})


def test_manager_can_install_valid_template(tmp_path: pathlib.Path) -> None:
    (tmp_path / "test").mkdir()
    (tmp_path / "test" / "manifest.yaml").write_text("description: test")
    (tmp_path / "test" / "Dockerfile.j2").write_text("FROM python:3.9")

    (tmp_path / "destination").mkdir()

    manager = TemplateManager(tmp_path)
    manager.install("test", tmp_path / "destination", {})

    assert (tmp_path / "destination" / "Dockerfile").exists()


def test_manager_returns_empty_list_for_strike(tmp_path: pathlib.Path) -> None:
    (tmp_path / "test").mkdir()
    (tmp_path / "test" / "manifest.yaml").write_text("description: test\nstrikes: [foo]")
    (tmp_path / "test" / "Dockerfile.j2").write_text("FROM python:3.9")

    manager = TemplateManager(tmp_path)

    assert not manager.get_templates_for_strike("test", "test")


def test_manager_returns_valid_list_for_strike_name(tmp_path: pathlib.Path) -> None:
    (tmp_path / "test").mkdir()
    (tmp_path / "test" / "manifest.yaml").write_text("description: test\nstrikes: [foo]")
    (tmp_path / "test" / "Dockerfile.j2").write_text("FROM python:3.9")

    manager = TemplateManager(tmp_path)

    assert len(manager.get_templates_for_strike("foo", "test")) == 1


def test_manager_returns_valid_list_for_strike_type(tmp_path: pathlib.Path) -> None:
    (tmp_path / "test").mkdir()
    (tmp_path / "test" / "manifest.yaml").write_text("description: test\nstrikes_types: [a_type]")
    (tmp_path / "test" / "Dockerfile.j2").write_text("FROM python:3.9")

    manager = TemplateManager(tmp_path)

    assert len(manager.get_templates_for_strike("foo", "a_type")) == 1


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
    TemplateManager().install_from_dir(source_dir, dest_dir, {"name": "TestContainer"})

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
    TemplateManager().install_from_dir(source_dir, dest_dir, {"name": "TestApp"})

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
    with pytest.raises(Exception, match="Template directory '.*' does not exist"):
        TemplateManager().install_from_dir(source_dir, tmp_path, {"name": "World"})


def test_templates_install_from_dir_source_is_file(tmp_path: pathlib.Path) -> None:
    source_file = tmp_path / "source.txt"
    source_file.touch()

    with pytest.raises(Exception, match="Path '.*' is not a directory"):
        TemplateManager().install_from_dir(source_file, tmp_path, {"name": "World"})


def test_templates_install_from_dir_missing_dockerfile(tmp_path: pathlib.Path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "agent.py").touch()

    with pytest.raises(Exception, match="Template directory .+ does not contain a Dockerfile"):
        TemplateManager().install_from_dir(source_dir, tmp_path, {"name": "World"})


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
    TemplateManager().install_from_dir(inner_dir, dest_dir, {"name": "World"})

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
    TemplateManager().install_from_dir(tmp_path / "source", dest_dir, {"name": "World"})

    # assert files were copied from subdirectory
    assert (dest_dir / "Dockerfile").exists()
    assert (dest_dir / "agent.py").exists()


def test_templates_install_from_dir_invalid_path(tmp_path: pathlib.Path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "Dockerfile").touch()

    with pytest.raises(Exception, match="Template directory '.*' does not exist"):
        TemplateManager().install_from_dir(source_dir / "nonexistent", tmp_path, {"name": "World"})
