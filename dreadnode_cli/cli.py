import typing as t
import webbrowser

import typer
from rich import print

from dreadnode_cli import api
from dreadnode_cli.agent import cli as agent_cli
from dreadnode_cli.challenge import cli as challenge_cli
from dreadnode_cli.config import ServerConfig, UserConfig
from dreadnode_cli.defaults import PLATFORM_BASE_URL
from dreadnode_cli.model import cli as models_cli
from dreadnode_cli.profile import cli as profile_cli
from dreadnode_cli.utils import pretty_cli

cli = typer.Typer(
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Interact with the Dreadnode platform",
)

cli.add_typer(profile_cli, name="profile", help="Manage server profiles")
cli.add_typer(challenge_cli, name="challenge", help="Interact with Crucible challenges")
cli.add_typer(agent_cli, name="agent", help="Interact with Strike agents")
cli.add_typer(models_cli, name="model", help="Manage user-defined inference models")


@cli.command(help="Authenticate to the platform.")
@pretty_cli
def login(
    server: t.Annotated[str | None, typer.Option("--server", "-s", help="URL of the server")] = None,
    profile: t.Annotated[str | None, typer.Option("--profile", "-p", help="Profile alias to assign / update")] = None,
) -> None:
    if not server:
        try:
            existing_config = UserConfig.read().get_server_config(profile)
            server = existing_config.url
        except Exception:
            server = PLATFORM_BASE_URL

    # create client with no auth data
    client = api.Client(base_url=server)

    print(":laptop_computer: Requesting device code ...")

    # request user and device codes
    codes = client.get_device_codes()

    # present verification URL to user
    verification_url = client.url_for_user_code(codes.user_code)
    verification_url_base = verification_url.split("?")[0]

    print()
    print(
        f"""\
Attempting to automatically open the authorization page in your default browser.
If the browser does not open or you wish to use a different device, open the following URL:

:link: [bold]{verification_url_base}[/]

Then enter the code: [bold]{codes.user_code}[/]
"""
    )

    webbrowser.open(verification_url)

    # poll for the access token after user verification
    tokens = client.poll_for_token(codes.device_code)

    client = api.Client(server, cookies={"refresh_token": tokens.refresh_token, "access_token": tokens.access_token})
    user = client.get_user()

    UserConfig.read().set_server_config(
        ServerConfig(
            url=server,
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            email=user.email_address,
            username=user.username,
            api_key=user.api_key.key,
        ),
        profile,
    ).write()

    print(f":white_check_mark: Authenticated as {user.email_address} ({user.username})")


@cli.command(help="Refresh data for the active server profile.")
@pretty_cli
def refresh() -> None:
    user_config = UserConfig.read()
    server_config = user_config.get_server_config()

    client = api.create_client()
    user = client.get_user()

    server_config.email = user.email_address
    server_config.username = user.username
    server_config.api_key = user.api_key.key

    user_config.set_server_config(server_config).write()

    print(
        f":white_check_mark: Refreshed '[bold]{user_config.active}[/bold]' ([magenta]{user.email_address}[/] / [cyan]{user.username}[/])"
    )


@cli.command(help="Show versions and exit.")
@pretty_cli
def version() -> None:
    import importlib.metadata
    import platform
    import sys

    version = importlib.metadata.version("dreadnode-cli")
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    os_name = platform.system()
    arch = platform.machine()
    print(f"Platform:      {os_name} ({arch})")
    print(f"Python:        {python_version}")
    print(f"Dreadnode CLI: {version}")
