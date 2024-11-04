import base64
import functools
import json
import pathlib
import sys
import typing as t
from datetime import datetime

from jinja2 import Environment, FileSystemLoader
from rich import print
from rich.prompt import Prompt

from dreadnode_cli.defaults import DEBUG

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


def copy_template(src: pathlib.Path, dest: pathlib.Path, context: dict[str, t.Any]) -> None:
    env = Environment(loader=FileSystemLoader(src))

    for src_item in src.iterdir():
        dest_item = dest / src_item.name
        content = src_item.read_text()

        if src_item.name.endswith(".j2"):
            template = env.get_template(src_item.name)
            content = template.render(context)
            dest_item = dest / src_item.name.removesuffix(".j2")

        if dest_item.exists():
            if Prompt.ask(f":axe: Overwrite {dest_item.name}?", choices=["y", "n"], default="n") == "n":
                continue

        dest_item.write_text(content)
