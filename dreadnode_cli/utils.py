import base64
import functools
import json
import os
import pathlib
import sys
import tempfile
import typing as t
import zipfile
from datetime import datetime

import httpx
from rich import print

from dreadnode_cli.defaults import DEBUG
from dreadnode_cli.types import GithubRepo

P = t.ParamSpec("P")
R = t.TypeVar("R")


def pretty_cli(func: t.Callable[P, R]) -> t.Callable[P, R]:
    """Decorator to pad function output and catch/pretty print any exceptions."""

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            print()
            return func(*args, **kwargs)
        except Exception as e:
            if DEBUG:
                raise

            print(f":exclamation: {e}")
            sys.exit(1)

    return wrapper


def time_to(future_datetime: datetime) -> str:
    """Get a string describing the time difference between a future datetime and now."""

    now = datetime.now()
    time_difference = future_datetime - now

    days = time_difference.days
    seconds = time_difference.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    result = []
    if days > 0:
        result.append(f"{days}d")
    if hours > 0:
        result.append(f"{hours}hr")
    if minutes > 0:
        result.append(f"{minutes}m")

    return ", ".join(result) if result else "Just now"


def parse_jwt_token_expiration(token: str) -> datetime:
    """Return the expiration date from a JWT token."""

    _, b64payload, _ = token.split(".")
    payload = base64.urlsafe_b64decode(b64payload + "==").decode("utf-8")
    return datetime.fromtimestamp(json.loads(payload).get("exp"))


def repo_exists(repo: GithubRepo) -> bool:
    """Check if a repo exists (or is private) on GitHub."""
    response = httpx.get(f"https://github.com/{repo.namespace}/{repo.repo}")
    return response.status_code == 200


def download_and_unzip_archive(url: str, *, headers: dict[str, str] | None = None) -> pathlib.Path:
    """
    Downloads a ZIP archive from the given URL and unzips it into a temporary directory.
    """

    temp_dir = pathlib.Path(tempfile.mkdtemp())
    local_zip_path = pathlib.Path(os.path.join(temp_dir, "archive.zip"))

    print(f":arrow_double_down: Downloading {url} ...")

    # download to temporary file
    with httpx.stream("GET", url, follow_redirects=True, verify=True, headers=headers) as response:
        response.raise_for_status()
        with open(local_zip_path, "wb") as zip_file:
            for chunk in response.iter_bytes(chunk_size=8192):
                zip_file.write(chunk)

    # unzip to temporary directory
    try:
        with zipfile.ZipFile(local_zip_path, "r") as zf:
            for member in zf.infolist():
                file_path = os.path.realpath(os.path.join(temp_dir, member.filename))
                if file_path.startswith(os.path.realpath(temp_dir)):
                    zf.extract(member, temp_dir)
                else:
                    raise Exception("Attempted Path Traversal Attack Detected")

    finally:
        # always remove the zip file
        if local_zip_path.exists():
            os.remove(local_zip_path)

    return temp_dir
