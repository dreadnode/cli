import os
import pathlib
import typing as t
import zipfile
from collections.abc import Generator
from datetime import datetime, timedelta

import httpx
import pytest

from dreadnode_cli.utils import (
    download_and_unzip_archive,
    parse_jwt_token_expiration,
    time_to,
)


# Mock the httpx.stream context manager
class MockResponse:
    def __init__(self, zip_path: pathlib.Path):
        self.status_code = 200
        with open(zip_path, "rb") as f:
            self.content = f.read()

    def raise_for_status(self) -> None:
        pass

    def iter_bytes(self, chunk_size: int) -> Generator[bytes, None, None]:
        yield self.content

    def __enter__(self) -> "MockResponse":
        return self

    def __exit__(self, *args: t.Any, **kwargs: t.Any) -> None:
        pass


def test_time_to() -> None:
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


def test_parse_jwt_token_expiration() -> None:
    # Test token with expiration
    token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3MDg2NTYwMDB9.mock_signature"
    exp_date = parse_jwt_token_expiration(token)
    assert isinstance(exp_date, datetime)
    assert exp_date == datetime.fromtimestamp(1708656000)


def test_download_and_unzip_archive_success(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # create a mock zip file with test content
    test_file_content = b"test content"
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("test.txt", test_file_content)

    monkeypatch.setattr(httpx, "stream", lambda *args, **kw: MockResponse(zip_path))

    # test successful download and extraction
    output_dir = download_and_unzip_archive("http://test.com/archive.zip")
    extracted_file = pathlib.Path(output_dir) / "test.txt"

    assert os.path.exists(output_dir)
    assert extracted_file.exists()
    assert extracted_file.read_bytes() == test_file_content


def test_download_and_unzip_archive_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    def mock_stream(*args: t.Any, **kwargs: t.Any) -> MockResponse:
        raise httpx.HTTPError("404 Not Found")

    monkeypatch.setattr(httpx, "stream", mock_stream)

    with pytest.raises(httpx.HTTPError, match="404 Not Found"):
        download_and_unzip_archive("http://test.com/nonexistent.zip")


def test_download_and_unzip_archive_invalid_zip(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # create a mock file that's not a valid zip
    invalid_zip = tmp_path / "invalid.zip"
    invalid_zip.write_bytes(b"not a zip file")

    monkeypatch.setattr(httpx, "stream", lambda *args, **kw: MockResponse(invalid_zip))

    with pytest.raises(zipfile.BadZipFile):
        download_and_unzip_archive("http://test.com/invalid.zip")


def test_download_and_unzip_archive_path_traversal(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # create a mock zip file with path traversal attempt
    test_file_content = b"test content"
    zip_path = tmp_path / "traversal.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("../test.txt", test_file_content)

    monkeypatch.setattr(httpx, "stream", lambda *args, **kw: MockResponse(zip_path))

    with pytest.raises(Exception, match="Attempted Path Traversal Attack Detected"):
        download_and_unzip_archive("http://test.com/archive.zip")
