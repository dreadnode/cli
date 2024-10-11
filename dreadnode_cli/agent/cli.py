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
    """Initialize a new agent project."""

    if not name:
        name = Prompt.ask("Project name: ")

    template = Template(template)

    directory = directory / name
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


@cli.command()
def status(
    directory: t.Annotated[
        pathlib.Path, typer.Argument(help="The agent directory", file_okay=False, resolve_path=True)
    ] = pathlib.Path("."),
) -> None:
    """If currenty linked (some kind of active agent state) - show it's state."""
    print("TODO")


@cli.command()
def versions(
    directory: t.Annotated[
        pathlib.Path, typer.Argument(help="The agent directory", file_okay=False, resolve_path=True)
    ] = pathlib.Path("."),
) -> None:
    """List historical versions of this agent."""
    print("TODO")


@cli.command()
def push(
    directory: t.Annotated[
        pathlib.Path, typer.Argument(help="The agent directory", file_okay=False, resolve_path=True)
    ] = pathlib.Path("."),
) -> None:
    """Push a new version of the agent."""
    print("TODO")


@cli.command()
def switch(
    directory: t.Annotated[
        pathlib.Path, typer.Argument(help="The agent directory", file_okay=False, resolve_path=True)
    ] = pathlib.Path("."),
    agent_id: t.Annotated[str | None, typer.Argument(help="Agent id")] = None,
) -> None:
    """Switch/link to a different agent."""
    print("TODO")


@cli.command()
def links(
    directory: t.Annotated[
        pathlib.Path, typer.Argument(help="The agent directory", file_okay=False, resolve_path=True)
    ] = pathlib.Path("."),
) -> None:
    """List all available links."""
    print("TODO")
