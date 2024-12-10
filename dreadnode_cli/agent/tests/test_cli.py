from pathlib import Path

from dreadnode_cli.agent.cli import get_repo_archive_source_path


def test_get_repo_archive_source_path_from_repo(tmp_path: Path) -> None:
    # single inner folder
    inner_repo_dir = tmp_path / "user-repo-12345"
    inner_repo_dir.mkdir()

    result = get_repo_archive_source_path(tmp_path)
    # source path should be fixed to the inner one
    assert result == inner_repo_dir


def test_get_repo_archive_source_path_from_non_repo(tmp_path: Path) -> None:
    # multiple inner folders, not a github repo archive
    inner_repo_dir1 = tmp_path / "something"
    inner_repo_dir1.mkdir()
    inner_repo_dir2 = tmp_path / "something-else"
    inner_repo_dir2.mkdir()

    result = get_repo_archive_source_path(tmp_path)
    # source path should stay unchanged
    assert result == tmp_path


def test_get_repo_archive_source_path_from_non_repo_with_files(tmp_path: Path) -> None:
    # single inner folders but also files, not a repo
    inner_repo_dir1 = tmp_path / "something"
    inner_repo_dir1.mkdir()
    inner_repo_file = tmp_path / "foo.txt"
    inner_repo_file.touch()

    result = get_repo_archive_source_path(tmp_path)
    # source path should stay unchanged
    assert result == tmp_path


def test_get_repo_archive_source_path_from_non_repo_with_one_file(tmp_path: Path) -> None:
    # single inner file, not a repo
    inner_repo_file = tmp_path / "foo.txt"
    inner_repo_file.touch()

    result = get_repo_archive_source_path(tmp_path)
    # source path should stay unchanged
    assert result == tmp_path
