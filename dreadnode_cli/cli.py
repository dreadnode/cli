import typing as t
import getpass
import os

import typer
from rich import print

from dreadnode_cli.agent import cli as agent_cli
from dreadnode_cli.config import ServerConfig, UserConfig
from dreadnode_cli.defaults import MAIN_PROFILE_NAME, PLATFORM_BASE_URL
from dreadnode_cli.profile import cli as profile_cli

cli = typer.Typer(no_args_is_help=True, help="Interact with the Dreadnode platform")

cli.add_typer(profile_cli, name="profile", help="Manage server profiles")
cli.add_typer(agent_cli, name="agent", help="Manage agents")


@cli.command(help="Authenticate to the platform")
def login(
    username: t.Annotated[str, typer.Option("--username", "-u", help="Username to authenticate as")],
    server: t.Annotated[str, typer.Option("--server", "-s", help="URL of the server")] = PLATFORM_BASE_URL,
    profile: t.Annotated[
        str, typer.Option("--profile", "-p", help="Profile alias to assign / update")
    ] = MAIN_PROFILE_NAME,
) -> None:
    # allow setting the password via the DREADNODE_USER_PASSWORD environment variable
    password = os.getenv("DREADNODE_USER_PASSWORD")

    if not password:
        password = getpass.getpass(f"password for {username}: ")
        print()

    print(f":key: Authenticating to [bold link]{server}[/] ...")

    # TODO: Actually authenticate
    api_key = "sk-1234"

    config = UserConfig.read()
    config.servers[profile] = ServerConfig(username=username, url=server, api_key=api_key)
    config.write()

    print(f":key: Authenticated to [bold link]{server}[/] as [bold cyan]{username}[/]")
