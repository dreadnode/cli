import typing as t

import typer
from rich import box, print
from rich.table import Table

from dreadnode_cli.dreadnode import Dreadnode, api, utils
from dreadnode_cli.ext.typer import AliasGroup
from dreadnode_cli.utils import pretty_cli

cli = typer.Typer(no_args_is_help=True, cls=AliasGroup)


@cli.command("show|list", help="List all server profiles")
@pretty_cli
def show() -> None:
    dreadnode = Dreadnode()
    if not dreadnode.config.servers:
        print(":exclamation: No server profiles are configured")
        return

    table = Table(box=box.ROUNDED)
    table.add_column("Profile", style="magenta")
    table.add_column("URL", style="cyan")
    table.add_column("Email")
    table.add_column("Username")
    table.add_column("Valid Until")

    for profile, server in dreadnode.config.servers.items():
        active = profile == dreadnode.config.active
        refresh_token = api.Token(server.refresh_token)

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


@cli.command(help="Set the active server profile", no_args_is_help=True)
@pretty_cli
def switch(profile: t.Annotated[str, typer.Argument(help="Profile to switch to")]) -> None:
    dreadnode = Dreadnode()
    if not dreadnode.profile_exists(profile):
        print(f":exclamation: Profile [bold]{profile}[/] does not exist")
        return

    dreadnode.set_active_profile(profile)

    print(f":laptop_computer: Switched to [bold magenta]{profile}[/]")
    print(f"|- email:    [bold]{dreadnode.config.servers[profile].email}[/]")
    print(f"|- username: {dreadnode.config.servers[profile].username}")
    print(f"|- url:      {dreadnode.config.servers[profile].url}")
    print()


@cli.command(help="Remove a server profile", no_args_is_help=True)
@pretty_cli
def forget(profile: t.Annotated[str, typer.Argument(help="Profile of the server to remove")]) -> None:
    dreadnode = Dreadnode()
    if not dreadnode.profile_exists(profile):
        print(f":exclamation: Profile [bold]{profile}[/] does not exist")
        return

    dreadnode.forget_profile(profile)

    print(f":axe: Forgot about [bold]{profile}[/]")
