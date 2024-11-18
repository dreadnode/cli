import enum
import pathlib
import typing as t

from jinja2 import Environment, FileSystemLoader
from rich.prompt import Prompt

TEMPLATES_DIR = pathlib.Path(__file__).parent.parent / "templates"


class Template(str, enum.Enum):
    rigging_basic = "rigging_basic"
    rigging_loop = "rigging_loop"


def template_description(template: Template) -> str:
    """Return the description of a template."""

    readme = TEMPLATES_DIR / template.value / "README.md"
    if readme.exists():
        return readme.read_text()

    return ""


def install_template(template: Template, dest: pathlib.Path, context: dict[str, t.Any]) -> None:
    """Install a template into a directory."""
    src = TEMPLATES_DIR / template.value
    env = Environment(loader=FileSystemLoader(src))

    for src_item in src.iterdir():
        dest_item = dest / src_item.name
        content = src_item.read_text()

        if src_item.name.endswith(".j2"):
            j2_template = env.get_template(src_item.name)
            content = j2_template.render(context)
            dest_item = dest / src_item.name.removesuffix(".j2")

        if dest_item.exists():
            if Prompt.ask(f":axe: Overwrite {dest_item.name}?", choices=["y", "n"], default="n") == "n":
                continue

        dest_item.write_text(content)
