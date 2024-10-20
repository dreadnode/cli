import enum
import pathlib
import typing as t

import typer
from rich import box, print
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from dreadnode_cli import api
from dreadnode_cli.agent import docker
from dreadnode_cli.agent.config import AgentConfig
from dreadnode_cli.agent.docker import get_registry
from dreadnode_cli.config import UserConfig
from dreadnode_cli.utils import copy_template, exit_with_pretty_error

cli = typer.Typer(no_args_is_help=True)
console = Console()


class Template(str, enum.Enum):
    rigging = "rigging"


TEMPLATES_DIR = pathlib.Path(__file__).parent / "templates"


def _show_agent(agent: api.Client.StrikeAgentResponse) -> None:
    table = Table(box=box.ROUNDED)
    table.add_column("Property", style="cyan")
    table.add_column("Value")

    table.add_row("ID", str(agent.id))
    table.add_row("Key", agent.key)
    table.add_row("Strike ID", str(agent.strike_id) if agent.strike_id else "N/A")
    table.add_row("Created At", agent.created_at.strftime("%Y-%m-%d %H:%M:%S"))
    table.add_row("Revision", str(agent.revision))

    latest_version = agent.latest
    table.add_row("Latest Version ID", str(latest_version.id))
    table.add_row("Latest Version Status", latest_version.status)
    table.add_row("Latest Version Created At", latest_version.created_at.strftime("%Y-%m-%d %H:%M:%S"))

    panel = Panel(table, title=agent.name, expand=False, title_align="left")
    console.print(panel)

    if latest_version.notes:
        console.print("Notes:", style="cyan")
        console.print(latest_version.notes)


@cli.command(help="Initialize a new agent project")
@exit_with_pretty_error
def init(
    strike: t.Annotated[str, typer.Argument(help="The target strike")],
    directory: t.Annotated[
        pathlib.Path, typer.Argument(help="The directory to initialize", file_okay=False, resolve_path=True)
    ] = pathlib.Path("."),
    name: t.Annotated[str | None, typer.Option("--name", "-n", help="The name of the agent")] = None,
    template: t.Annotated[
        Template, typer.Option("--template", "-t", help="The template to use for the agent")
    ] = Template.rigging,
    profile: t.Annotated[str | None, typer.Option("--profile", "-p", help="The server profile to use")] = None,
) -> None:
    print()

    client = api.client(profile=profile)

    name = Prompt.ask("Project name?", default=name or directory.name)
    template = Template(Prompt.ask("Template?", choices=[t.value for t in Template], default=template))

    directory.mkdir(exist_ok=True)

    try:
        AgentConfig.read(directory)
        if Prompt.ask(":axe: Agent config exists, overwrite?", choices=["y", "n"], default="n") == "n":
            return
    except Exception:
        pass

    if strike is not None:
        try:
            strike_response = client.get_strike(strike)
        except Exception as e:
            raise Exception(f"Failed to find strike '{strike}': {e}") from e

        print()
        print(f":crossed_swords: Linking to strike '{strike_response.name}' ({strike_response.type})")

    AgentConfig(name=name, strike=strike).write(directory=directory)
    context = {"project_name": name}
    copy_template(TEMPLATES_DIR / template.value, directory, context)

    print()
    print(f"Initialized [b]{directory}[/]")


@cli.command(help="Push a new version of the agent.")
@exit_with_pretty_error
def push(
    directory: t.Annotated[
        pathlib.Path, typer.Argument(help="The agent directory", file_okay=False, resolve_path=True)
    ] = pathlib.Path("."),
    profile: t.Annotated[str | None, typer.Option("--profile", "-p", help="The server profile to use")] = None,
    tag: t.Annotated[str | None, typer.Option("--tag", "-t", help="The tag to use for the image")] = None,
    env_vars: t.Annotated[
        list[str] | None,
        typer.Option("--env-var", "-e", help="Environment vars to use when executing the image (key=value)"),
    ] = None,
) -> None:
    print()

    env = {env_var.split("=")[0]: env_var.split("=")[1] for env_var in env_vars or []}

    agent_config = AgentConfig.read(directory)
    server_config = UserConfig.read().get_server_config(profile)

    registry = get_registry(server_config)

    print(f":key: Authenticating with [bold]{registry}[/] ...")
    docker.login(registry, server_config.username, server_config.api_key)

    print()
    print(f":wrench: Building agent from [b]{directory}[/] ...")
    image = docker.build(directory)
    repository = f"{registry}/{server_config.username}/agents/{agent_config.name}"
    tag = tag or image.id[-8:]

    print()
    print(f":package: Pushing agent to [b]{repository}:{tag}[/] ...")
    docker.push(image, repository, tag)

    client = api.client(profile=profile)
    container = api.Client.Container(image=f"{repository}:{tag}", env=env, name=None)

    if not agent_config.links:
        print()
        print(":robot: Creating a new agent ...")
        name = Prompt.ask("Agent name?", default=agent_config.name)
        notes = Prompt.ask("Notes?")

        agent = client.create_agent(container, name, strike=agent_config.strike, notes=notes)
        agent_config.add_link(agent.id)
        agent_config.active = agent.id
        _show_agent(agent)
    else:
        active_agent_id = agent_config.active
        if active_agent_id is None:
            raise Exception("No active agent link found. Use 'switch' command to set an active link.")

        print()
        print(":robot: Creating a new agent version ...")
        notes = Prompt.ask("Notes?")

        agent = client.create_agent_version(str(active_agent_id), container, notes)
        _show_agent(agent)

    agent_config.write(directory)

    print(client.start_run(agent.latest.id))


@cli.command(help="Show the status of the currently active agent")
@exit_with_pretty_error
def status(
    directory: t.Annotated[
        pathlib.Path, typer.Argument(help="The agent directory", file_okay=False, resolve_path=True)
    ] = pathlib.Path("."),
    profile: t.Annotated[str | None, typer.Option("--profile", "-p", help="The server profile to use")] = None,
) -> None:
    agent_config = AgentConfig.read(directory)
    if not agent_config.active:
        print(":warning: No active agent link found.")
        return

    client = api.client(profile=profile)
    agent = client.get_agent(str(agent_config.active))
    _show_agent(agent)


@cli.command(help="List historical versions of this agent")
@exit_with_pretty_error
def versions(
    directory: t.Annotated[
        pathlib.Path, typer.Argument(help="The agent directory", file_okay=False, resolve_path=True)
    ] = pathlib.Path("."),
    profile: t.Annotated[str | None, typer.Option("--profile", "-p", help="The server profile to use")] = None,
) -> None:
    print()

    agent_config = AgentConfig.read(directory)
    if not agent_config.active:
        print(":warning: No active agent link found.")
        return

    client = api.client(profile=profile)
    agent = client.get_agent(str(agent_config.active))

    table = Table(box=box.ROUNDED)
    table.add_column("Rev", style="magenta")
    table.add_column("Status")
    table.add_column("Notes", style="cyan")
    table.add_column("Image")
    table.add_column("Created")

    for i, version in enumerate(sorted(agent.versions, key=lambda v: v.created_at)):
        latest = version.id == agent.latest.id
        table.add_row(
            str(i + 1) + ("*" if latest else ""),
            version.status,
            version.notes or "-",
            version.container.image,
            f"[dim]{version.created_at.strftime('%Y-%m-%d %H:%M:%S')}[/]",
            style="bold" if latest else None,
        )

    console.print(table)


@cli.command(help="Switch/link to a different agent")
@exit_with_pretty_error
def switch(
    directory: t.Annotated[
        pathlib.Path, typer.Argument(help="The agent directory", file_okay=False, resolve_path=True)
    ] = pathlib.Path("."),
    agent: t.Annotated[str | None, typer.Argument(help="Agent name, key, or id")] = None,
    profile: t.Annotated[str | None, typer.Option("--profile", "-p", help="The server profile to use")] = None,
) -> None:
    agent_config = AgentConfig.read(directory)
    client = api.client(profile=profile)

    if not agent:
        # List available agents and let user choose
        agents = client.list_agents()
        table = Table(box=box.ROUNDED)
        table.add_column("ID", style="cyan")
        table.add_column("Name")
        table.add_column("Key")

        for a in agents:
            table.add_row(str(a.id), a.name or "N/A", a.key)

        console.print(table)
        agent = Prompt.ask("Enter the ID of the agent to switch to")

    # Find the agent by id, name, or key
    target_agent = next((a for a in agents if str(a.id) == agent or a.name == agent or a.key == agent), None)

    if not target_agent:
        print(f":warning: Agent '{agent}' not found.")
        return

    agent_config.active = target_agent.id
    if target_agent.id not in agent_config.links:
        agent_config.add_link(target_agent.id)

    agent_config.write(directory)
    print(f":white_check_mark: Switched to agent: {target_agent.name} (ID: {target_agent.id})")


@cli.command(help="List all available links")
@exit_with_pretty_error
def links(
    directory: t.Annotated[
        pathlib.Path, typer.Argument(help="The agent directory", file_okay=False, resolve_path=True)
    ] = pathlib.Path("."),
    profile: t.Annotated[str | None, typer.Option("--profile", "-p", help="The server profile to use")] = None,
) -> None:
    print()

    agent_config = AgentConfig.read(directory)
    client = api.client(profile=profile)

    table = Table(box=box.ROUNDED)
    table.add_column("Key", style="magenta")
    table.add_column("Name", style="cyan")
    table.add_column("ID")

    for link in agent_config.links:
        active = link == agent_config.active
        agent = client.get_agent(str(link))
        table.add_row(
            agent.key + ("*" if active else ""),
            agent.name or "N/A",
            f"[dim]{agent.id}[/]",
            style="bold" if not active else None,
        )

    console.print(table)
