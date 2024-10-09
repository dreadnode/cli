import typing as t

import typer
from rich import box, print
from rich.table import Table

from dreadnode_cli.agent import cli as agent_cli
from dreadnode_cli.config import ServerConfig, UserConfig

cli = typer.Typer(no_args_is_help=True, help="Interact with the Dreadnode platform")
cli.add_typer(agent_cli, name="agent", help="Manage agents")


@cli.command(help="Authenticate to the platform")
def login(
    server: t.Annotated[
        str, typer.Option("--server", "-s", help="URL of the server")
    ] = "https://crucible.dreadnode.io",
    profile: t.Annotated[str, typer.Option("--profile", "-p", help="Profile alias to assign / update")] = "main",
) -> None:
    # TODO: Actually authenticate
    api_key = "sk-1234"
    username = "monoxgas"

    config = UserConfig.read()
    config.servers[profile] = ServerConfig(username=username, url=server, api_key=api_key)
    config.write()

    print()
    print(f":key: Authenticated to [bold link]{server}[/] as [bold cyan]{username}[/]")

    pass


@cli.command(help="List all server profiles")
def list() -> None:
    config = UserConfig.read()

    table = Table(box=box.ROUNDED)
    table.add_column("Profile")
    table.add_column("URL")
    table.add_column("Username")

    current = config.server

    for profile, server in config.servers.items():
        active_profile = server == current
        table.add_row(
            f"[bold]{profile}*[/]" if active_profile else profile,
            server.url,
            server.username,
            style="cyan" if active_profile else None,
        )

    print(table)


@cli.command(help="Set the active server profile")
def switch(profile: t.Annotated[str, typer.Argument(help="Profile to switch to")]) -> None:
    config = UserConfig.read()

    if profile not in config.servers:
        print(f":exclamation: Profile [bold]{profile}[/] is not configured")
        return

    config.active = profile
    config.write()

    print()
    print(f":white_check_mark: Switched to [bold]{profile}[/]")
    print(f"|- user: [bold]{config.servers[profile].username}[/]")
    print(f"|- url:  [bold]{config.servers[profile].url}[/]")


@cli.command(help="Remove a server profile")
def forget(profile: t.Annotated[str, typer.Argument(help="Profile of the server to remove")]) -> None:
    config = UserConfig.read()

    if profile not in config.servers:
        print(f":exclamation: Profile [bold]{profile}[/] is not configured")
        return

    del config.servers[profile]
    config.write()

    print()
    print(f":axe: Forgot about [bold]{profile}[/]")
