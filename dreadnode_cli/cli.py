import typing as t

import typer
from rich import print

from dreadnode_cli.agent import cli as agent_cli
from dreadnode_cli.challenge import cli as challenge_cli
from dreadnode_cli.dreadnode import Dreadnode
from dreadnode_cli.model import cli as models_cli
from dreadnode_cli.profile import cli as profile_cli
from dreadnode_cli.utils import pretty_cli

cli = typer.Typer(
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Interact with the Dreadnode platform",
)

cli.add_typer(profile_cli, name="profile", help="Manage server profiles")
cli.add_typer(challenge_cli, name="challenge", help="Interact with Crucible challenges")
cli.add_typer(agent_cli, name="agent", help="Interact with Strike agents")
cli.add_typer(models_cli, name="model", help="Manage user-defined inference models")


@cli.command(help="Authenticate to the platform.")
@pretty_cli
def login(
    server: t.Annotated[str | None, typer.Option("--server", "-s", help="URL of the server")] = None,
    profile: t.Annotated[str | None, typer.Option("--profile", "-p", help="Profile alias to assign / update")] = None,
) -> None:
    Dreadnode(verbose=True).login(server, profile)


@cli.command(help="Refresh data for the active server profile.")
@pretty_cli
def refresh() -> None:
    Dreadnode(verbose=True).refresh()


@cli.command(help="Show versions and exit.")
@pretty_cli
def version() -> None:
    import importlib.metadata
    import platform
    import sys

    version = importlib.metadata.version("dreadnode-cli")
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    os_name = platform.system()
    arch = platform.machine()
    print(f"Platform:      {os_name} ({arch})")
    print(f"Python:        {python_version}")
    print(f"Dreadnode CLI: {version}")
