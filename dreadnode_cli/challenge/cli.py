import typer
from rich import print

import dreadnode_cli.api as api
from dreadnode_cli.config import UserConfig

cli = typer.Typer()


@cli.command(help="List challenges")
def list() -> None:
    try:
        config = UserConfig.read().active_server
        client = api.Client(base_url=config.url, access_token=config.access_token)

        print(client.list_challenges())
    except Exception as e:
        print(f":cross_mark: {e}")

    """
    table = Table(box=box.ROUNDED)
    table.add_column("Profile")
    table.add_column("URL")
    table.add_column("Username")

    current = config.active_server

    for profile, server in config.servers.items():
        active_profile = server == current
        table.add_row(
            f"[bold]{profile}*[/]" if active_profile else profile,
            server.url,
            server.username,
            style="cyan" if active_profile else None,
        )

    print(table)
    """
