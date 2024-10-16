import asyncio
import os
import typing as t

import typer
from rich import print

from dreadnode_cli import api
from dreadnode_cli.agent import cli as agent_cli
from dreadnode_cli.challenge import cli as challenge_cli
from dreadnode_cli.config import ServerConfig, UserConfig
from dreadnode_cli.defaults import MAIN_PROFILE_NAME, PLATFORM_BASE_URL
from dreadnode_cli.profile import cli as profile_cli

cli = typer.Typer(no_args_is_help=True, help="Interact with the Dreadnode platform")

cli.add_typer(profile_cli, name="profile", help="Manage server profiles")
cli.add_typer(challenge_cli, name="challenge", help="Crucible challenges")
cli.add_typer(agent_cli, name="agent", help="Manage agents")


async def authentication_flow(server: str) -> t.Any:
    client = api.Client(base_url=server)

    print(":laptop_computer: requesting device code ...")

    codes = await client.get_device_codes()
    user_code = codes.get("user_code")

    print(
        f":link: visit {client.url_for_user_code(user_code)} in your browser to verify this device with the code [bold]{user_code}[/]"
    )

    return await client.poll_for_token(codes.get("device_code"))


@cli.command(help="Authenticate to the platform.")
def login(
    server: t.Annotated[str, typer.Option("--server", "-s", help="URL of the server")] = PLATFORM_BASE_URL,
    profile: t.Annotated[
        str, typer.Option("--profile", "-p", help="Profile alias to assign / update")
    ] = MAIN_PROFILE_NAME,
) -> None:
    try:
        # allow overriding the server via env variable
        env_server = os.getenv("DREADNODE_SERVER")
        if env_server:
            server = env_server

        auth = asyncio.run(authentication_flow(server))

        UserConfig.read().set_profile_config(
            profile,
            ServerConfig(url=server, access_token=auth.get("access_token"), refresh_token=auth.get("refresh_token")),
        ).write()

        print(":white_check_mark: authentication successful")
    except Exception as e:
        print(f":cross_mark: {e}")


@cli.command(help="Refresh the authentication data for the active server profile.")
def refresh() -> None:
    try:
        asyncio.run(api.setup_authenticated_client(UserConfig.read().active_server, force_refresh=True))
    except Exception as e:
        print(f":cross_mark: {e}")
