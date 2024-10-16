import asyncio
import typing as t

import typer
from rich import box, print
from rich.table import Table

import dreadnode_cli.api as api
from dreadnode_cli.config import UserConfig

cli = typer.Typer(no_args_is_help=True, help="Visualize and interact with the Crucible challenges")


def format_difficulty(difficulty: str) -> str:
    if difficulty == "easy":
        return ":skull:"
    elif difficulty == "medium":
        return ":skull::skull:"
    else:
        return ":skull::skull::skull:"


# TODO: add sorting and filtering
@cli.command(help="List challenges")
def list() -> None:
    try:
        config = UserConfig.read().active_server
        auth = api.Authentication(config.access_token, config.refresh_token)
        client = api.Client(base_url=config.url, auth=auth)

        if auth.is_expired():
            # this returns: 401: Token has expired
            # asyncio.run(client.refresh_auth())
            raise Exception("authentication expired")

        challenges = asyncio.run(client.list_challenges())

        table = Table(box=box.ROUNDED)
        table.add_column("Title")
        table.add_column("Lead")
        table.add_column("Difficulty")
        table.add_column("Authors")
        table.add_column("Tags")

        for challenge in challenges:
            table.add_row(
                f"[bold]{challenge["title"]}[/]" if challenge["status"] != "completed" else challenge["title"],
                f"[dim]{challenge["lead"]}[/]",
                format_difficulty(challenge["difficulty"]),
                ", ".join(challenge["authors"]),
                ", ".join(challenge["tags"]),
            )

        print(table)

    except Exception as e:
        print(f":cross_mark: {e}")


@cli.command(help="Submit a flag to a challenge")
def submit_flag(
    challenge_id: t.Annotated[str, typer.Argument(help="Challenge name")],
    flag: t.Annotated[str, typer.Argument(help="Challenge flag")],
) -> None:
    try:
        # config = UserConfig.read().active_server
        # client = api.Client(base_url=config.url, access_token=config.access_token)
        print("TODO")
    except Exception as e:
        print(f":cross_mark: {e}")
