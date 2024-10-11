import typing as t

import typer
from rich import box, print
from rich.table import Table

from dreadnode_cli.config import UserConfig

cli = typer.Typer()


@cli.command(help="List all server profiles")
def list() -> None:
    config = UserConfig.read()

    table = Table(box=box.ROUNDED)
    table.add_column("Profile")
    table.add_column("URL")
    table.add_column("Username")
    table.add_column("Created At")

    current = config.active_server

    for profile, server in config.servers.items():
        active_profile = server == current
        table.add_row(
            f"[bold]{profile}*[/]" if active_profile else profile,
            server.url,
            server.username,
            server.created_at.strftime("%Y-%m-%d %H:%M:%S"),
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

    config.remove_profile_config(profile).write()

    print()
    print(f":axe: Forgot about [bold]{profile}[/]")
