import base64
import json
import pathlib
import typing as t
from datetime import datetime

from jinja2 import Environment, FileSystemLoader
from rich.prompt import Prompt


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
        result.append(f"{days} days")
    if hours > 0:
        result.append(f"{hours} hours")
    if minutes > 0:
        result.append(f"{minutes} minutes")
    if seconds > 0:
        result.append(f"{seconds} seconds")

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
