import typing as t

import typer
from rich import box, print
from rich.table import Table

from dreadnode_cli import utils
from dreadnode_cli.api import Token
from dreadnode_cli.config import UserConfig

cli = typer.Typer(no_args_is_help=True, help="Manage server profiles")


@cli.command(help="List all server profiles")
def list() -> None:
    try:
        config = UserConfig.read()

        table = Table(box=box.ROUNDED)
        table.add_column("Profile")
        table.add_column("URL")
        table.add_column("Expires At")

        current = config.active_server

        for profile, server in config.servers.items():
            active_profile = server == current
            refresh_token = Token(server.refresh_token)

            table.add_row(
                f"[bold]{profile}*[/]" if active_profile else profile,
                server.url,
                "[red]expired[/]"
                if refresh_token.is_expired()
                else f'{refresh_token.expires_at.strftime("%Y-%m-%d %H:%M:%S")} ({utils.time_to(refresh_token.expires_at)})',
                style="cyan" if active_profile else None,
            )

        print(table)
    except Exception as e:
        print(f":cross_mark: {e}")


@cli.command(help="Set the active server profile")
def switch(profile: t.Annotated[str, typer.Argument(help="Profile to switch to")]) -> None:
    try:
        config = UserConfig.read()
        if profile not in config.servers:
            print(f":exclamation: Profile [bold]{profile}[/] is not configured")
            return

        config.active = profile
        config.write()

        print()
        print(f":white_check_mark: Switched to [bold]{profile}[/]")
        print(f"|- url:  [bold]{config.servers[profile].url}[/]")
    except Exception as e:
        print(f":cross_mark: {e}")


@cli.command(help="Remove a server profile")
def forget(profile: t.Annotated[str, typer.Argument(help="Profile of the server to remove")]) -> None:
    try:
        config = UserConfig.read()
        if profile not in config.servers:
            print(f":exclamation: Profile [bold]{profile}[/] is not configured")
            return

        config.remove_profile_config(profile).write()

        print()
        print(f":axe: Forgot about [bold]{profile}[/]")
    except Exception as e:
        print(f":cross_mark: {e}")
