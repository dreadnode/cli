import pathlib
import typing as t

from jinja2 import Environment, FileSystemLoader
from rich.prompt import Prompt


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
