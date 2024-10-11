import typing as t

import typer
from rich import print

import dreadnode_cli.api as api
from dreadnode_cli.config import UserConfig

cli = typer.Typer()


# TODO: add sorting and filtering
@cli.command(help="List challenges")
def list() -> None:
    try:
        config = UserConfig.read().active_server
        client = api.Client(base_url=config.url, access_token=config.access_token)

        print(client.list_challenges())
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
