import enum
import pathlib
import typing as t

import typer
from rich import print
from rich.prompt import Prompt

from dreadnode_cli.agent.config import AgentConfig
from dreadnode_cli.utils import copy_template

cli = typer.Typer()


class Template(str, enum.Enum):
    basic = "basic"
    poetry = "poetry"


TEMPLATES_DIR = pathlib.Path(__file__).parent / "templates"


@cli.command()
def init(
    directory: t.Annotated[
        pathlib.Path, typer.Argument(help="The directory to initialize", file_okay=False, resolve_path=True)
    ] = pathlib.Path("."),
    name: t.Annotated[str | None, typer.Option("--name", "-n", help="The name of the project")] = None,
    template: t.Annotated[
        Template, typer.Option("--template", "-t", help="The template to use for the project")
    ] = Template.basic,
) -> None:
    print()
    name = Prompt.ask("Project name?", default=name or directory.name)
    template = Template(Prompt.ask("Template?", choices=[t.value for t in Template], default=template))
    print()

    directory.mkdir(exist_ok=True)

    config_path = directory / ".dreadnode.json"
    if config_path.exists():
        if Prompt.ask(":axe: Agent config exists, overwrite?", choices=["y", "n"], default="n") == "n":
            return

    AgentConfig(name=name).write(path=config_path)

    print(":rocket: Creating ...")

    context = {"project_name": name}
    copy_template(TEMPLATES_DIR / template.value, directory, context)

    print()
    print(f"Initialized [b]{directory}[/]")
