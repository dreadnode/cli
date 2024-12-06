import typing as t

import typer
from rich import box, print
from rich.table import Table

from dreadnode_cli import utils
from dreadnode_cli.api import Token
from dreadnode_cli.config import UserConfig
from dreadnode_cli.utils import pretty_cli

cli = typer.Typer(no_args_is_help=True)


@cli.command(help="List all server profiles")
@pretty_cli
def list() -> None:
    config = UserConfig.read()
    if not config.servers:
        print(":exclamation: No server profiles are configured")
        return

    table = Table(box=box.ROUNDED)
    table.add_column("Profile", style="magenta")
    table.add_column("URL", style="cyan")
    table.add_column("Email")
    table.add_column("Username")
    table.add_column("Valid Until")

    for profile, server in config.servers.items():
        active = profile == config.active
        refresh_token = Token(server.refresh_token)

        table.add_row(
            profile + ("*" if active else ""),
            server.url,
            server.email,
            server.username,
            "[red]expired[/]"
            if refresh_token.is_expired()
            else f'{refresh_token.expires_at.astimezone().strftime("%c")} ({utils.time_to(refresh_token.expires_at)})',
            style="bold" if active else None,
        )

    print(table)


@cli.command(help="Set the active server profile")
@pretty_cli
def switch(profile: t.Annotated[str, typer.Argument(help="Profile to switch to")]) -> None:
    config = UserConfig.read()
    if profile not in config.servers:
        print(f":exclamation: Profile [bold]{profile}[/] does not exist")
        return

    config.active = profile
    config.write()

    print(f":laptop_computer: Switched to [bold magenta]{profile}[/]")
    print(f"|- email:    [bold]{config.servers[profile].email}[/]")
    print(f"|- username: {config.servers[profile].username}")
    print(f"|- url:      {config.servers[profile].url}")
    print()


@cli.command(help="Remove a server profile")
@pretty_cli
def forget(profile: t.Annotated[str, typer.Argument(help="Profile of the server to remove")]) -> None:
    config = UserConfig.read()
    if profile not in config.servers:
        print(f":exclamation: Profile [bold]{profile}[/] does not exist")
        return

    del config.servers[profile]
    config.write()

    print(f":axe: Forgot about [bold]{profile}[/]")
