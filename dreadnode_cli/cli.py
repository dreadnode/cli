import os
import typing as t

import typer
from rich import print
from rich.prompt import Prompt

import dreadnode_cli.api as api
from dreadnode_cli.agent import cli as agent_cli
from dreadnode_cli.challenge import cli as challenge_cli
from dreadnode_cli.config import ServerConfig, UserConfig
from dreadnode_cli.defaults import MAIN_PROFILE_NAME, PLATFORM_BASE_URL
from dreadnode_cli.profile import cli as profile_cli

cli = typer.Typer(no_args_is_help=True, help="Interact with the Dreadnode platform")

cli.add_typer(profile_cli, name="profile", help="Manage server profiles")
cli.add_typer(challenge_cli, name="challenge", help="Crucible challenges")
cli.add_typer(agent_cli, name="agent", help="Manage agents")


@cli.command(help="Authenticate to the platform.")
def login(
    username: t.Annotated[str, typer.Option("--username", "-u", help="Username to authenticate as")],
    server: t.Annotated[str, typer.Option("--server", "-s", help="URL of the server")] = PLATFORM_BASE_URL,
    profile: t.Annotated[
        str, typer.Option("--profile", "-p", help="Profile alias to assign / update")
    ] = MAIN_PROFILE_NAME,
) -> None:
    # allow setting the password via the DREADNODE_USER_PASSWORD environment variable
    # useful for Dockerized applications and whatnot
    password = os.getenv("DREADNODE_USER_PASSWORD")
    if not password:
        password = Prompt.ask(f":key: Password for {username}: ", password=True)

    try:
        client = api.Client(base_url=server)
        access_token = client.login(username=username, password=password)

        UserConfig.read().set_profile_config(
            profile, ServerConfig(username=username, url=server, access_token=access_token)
        ).write()

        print(f":white_check_mark: Authenticated as [bold cyan]{username}[/]")
    except Exception as e:
        print(f":cross_mark: {e}")


@cli.command(help="Refresh the access token for a profile.")
def refresh(
    profile: t.Annotated[
        str, typer.Option("--profile", "-p", help="Profile alias to assign / update")
    ] = MAIN_PROFILE_NAME,
) -> None:
    try:
        config = UserConfig.read().get_profile_config(profile)
        if not config:
            raise Exception(f"Profile [bold cyan]{profile}[/] not found")

        client = api.Client(base_url=config.url, access_token=config.access_token)
        new_access_token = client.refresh_token()

        print(f":white_check_mark: Token refreshed for [bold cyan]{config.username}[/] -> {new_access_token}")
    except Exception as e:
        print(f":cross_mark: {e}")


@cli.command(help="Logout from the current profile.")
def logout(
    profile: t.Annotated[
        str, typer.Option("--profile", "-p", help="Profile alias to assign / update")
    ] = MAIN_PROFILE_NAME,
) -> None:
    try:
        UserConfig.read().remove_profile_config(profile).write()

        print(":white_check_mark: Logged out")
    except Exception as e:
        print(f":cross_mark: {e}")
