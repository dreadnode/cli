import enum
import pathlib
import typing as t

from jinja2 import Environment, FileSystemLoader
from rich.prompt import Prompt

TEMPLATES_DIR = pathlib.Path(__file__).parent.parent / "templates"


class Template(str, enum.Enum):
    rigging_basic = "rigging_basic"
    rigging_loop = "rigging_loop"
    nerve_basic = "nerve_basic"


def template_description(template: Template) -> str:
    """Return the description of a template."""

    readme = TEMPLATES_DIR / template.value / "README.md"
    if readme.exists():
        return readme.read_text()

    return ""


def install_template(template: Template, dest: pathlib.Path, context: dict[str, t.Any]) -> None:
    """Install a template into a directory."""
    install_template_from_dir(TEMPLATES_DIR / template.value, dest, context)


def install_template_from_dir(src: pathlib.Path, dest: pathlib.Path, context: dict[str, t.Any]) -> None:
    """Install a template from a source directory into a destination directory."""

    if not src.exists():
        raise Exception(f"Source directory '{src}' does not exist")

    elif not src.is_dir():
        raise Exception(f"Source '{src}' is not a directory")

    elif not (src / "Dockerfile").exists() and not (src / "Dockerfile.j2").exists():
        # if src has been downloaded from a ZIP archive, it may contain a single
        # 'project-main' folder, that is the actual source we want to use.
        # Check if src contains only one folder and update it if so.
        subdirs = [d for d in src.iterdir() if d.is_dir()]
        if len(subdirs) == 1:
            src = subdirs[0]

        # check again for Dockerfile in the subdirectory
        if not (src / "Dockerfile").exists() and not (src / "Dockerfile.j2").exists():
            raise Exception("Source directory does not contain a Dockerfile")

    env = Environment(loader=FileSystemLoader(src))

    # iterate over all items in the source directory
    for src_item in src.glob("**/*"):
        # get the relative path of the item
        src_item_path = str(src_item.relative_to(src))
        # get the destination path
        dest_item = dest / src_item_path

        # if the destination item is not the root directory and it exists,
        # ask the user if they want to overwrite it
        if dest_item != dest and dest_item.exists():
            if Prompt.ask(f":axe: Overwrite {dest_item}?", choices=["y", "n"], default="n") == "n":
                continue

        # if the source item is a file
        if src_item.is_file():
            # if the file has a .j2 extension, render it using Jinja2
            if src_item.name.endswith(".j2"):
                # we can read as text
                content = src_item.read_text()
                j2_template = env.get_template(src_item_path)
                content = j2_template.render(context)
                dest_item = dest / src_item_path.removesuffix(".j2")
                dest_item.write_text(content)
            else:
                # otherwise, copy the file as is
                dest_item.write_bytes(src_item.read_bytes())

        # if the source item is a directory, create it in the destination
        elif src_item.is_dir():
            dest_item.mkdir(exist_ok=True)
