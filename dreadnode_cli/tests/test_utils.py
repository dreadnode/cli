import pathlib
from datetime import datetime, timedelta
from unittest.mock import patch

from dreadnode_cli.utils import copy_template, parse_jwt_token_expiration, time_to


async def test_time_to() -> None:
    now = datetime.now()

    # Test days
    future = now + timedelta(days=2, hours=3, minutes=15)
    assert time_to(future) == "2d, 3hr, 14m"  # not full 15

    # Test hours
    future = now + timedelta(hours=3, minutes=15)
    assert time_to(future) == "3hr, 14m"  # not full 15

    # Test minutes
    future = now + timedelta(minutes=15)
    assert time_to(future) == "14m"  # not full 15

    # Test just now
    future = now + timedelta(seconds=30)
    assert time_to(future) == "Just now"


async def test_parse_jwt_token_expiration() -> None:
    # Test token with expiration
    token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3MDg2NTYwMDB9.mock_signature"
    exp_date = parse_jwt_token_expiration(token)
    assert isinstance(exp_date, datetime)
    assert exp_date == datetime.fromtimestamp(1708656000)


async def test_copy_template(tmp_path: pathlib.Path) -> None:
    # Create source template directory
    src_dir = tmp_path / "templates"
    src_dir.mkdir()

    # Create test template files
    normal_file = src_dir / "normal.txt"
    normal_file.write_text("Hello")

    template_file = src_dir / "template.txt.j2"
    template_file.write_text("Hello {{ name }}")

    # Create destination directory
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    # Test copying templates
    with patch("rich.prompt.Prompt.ask", return_value="y"):
        copy_template(src_dir, dest_dir, {"name": "World"})

    # Check normal file
    assert (dest_dir / "normal.txt").read_text() == "Hello"

    # Check rendered template
    assert (dest_dir / "template.txt").read_text() == "Hello World"

    # Test skipping existing files
    with patch("rich.prompt.Prompt.ask", return_value="n"):
        copy_template(src_dir, dest_dir, {"name": "Test"})
        assert (dest_dir / "template.txt").read_text() == "Hello World"
