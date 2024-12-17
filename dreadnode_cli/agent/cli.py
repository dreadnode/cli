import pathlib
import shutil
import time
import typing as t

import typer
from rich import box, print
from rich.live import Live
from rich.prompt import Prompt
from rich.table import Table

from dreadnode_cli import api
from dreadnode_cli.agent import docker
from dreadnode_cli.agent.config import AgentConfig
from dreadnode_cli.agent.docker import get_registry
from dreadnode_cli.agent.format import (
    format_agent,
    format_agent_versions,
    format_models,
    format_run,
    format_runs,
    format_strikes,
    format_templates,
)
from dreadnode_cli.agent.templates import Template, install_template, install_template_from_dir
from dreadnode_cli.config import UserConfig
from dreadnode_cli.profile.cli import switch as switch_profile
from dreadnode_cli.types import GithubRepo
from dreadnode_cli.utils import download_and_unzip_archive, pretty_cli, repo_exists

cli = typer.Typer(no_args_is_help=True)


def ensure_profile(agent_config: AgentConfig, *, user_config: UserConfig | None = None) -> None:
    """Ensure the active agent link matches the current server profile."""

    user_config = user_config or UserConfig.read()

    if not user_config.active_profile_name:
        raise Exception("No server profile is set, use [bold]dreadnode login[/] to authenticate")

    if agent_config.links and not agent_config.has_link_to_profile(user_config.active_profile_name):
        linked_profiles = ", ".join(agent_config.linked_profiles)
        plural = "s" if len(agent_config.linked_profiles) > 1 else ""
        raise Exception(
            f"This agent is linked to the [magenta]{linked_profiles}[/] server profile{plural}, "
            f"but the current server profile is [yellow]{user_config.active_profile_name}[/], ",
            "use [bold]dreadnode agent push[/] to create a new link with this profile.",
        )

    if agent_config.active_link.profile != user_config.active_profile_name:
        if (
            Prompt.ask(
                f"Current agent link points to the [yellow]{agent_config.active_link.profile}[/] server profile, "
                f"would you like to switch to it?",
                choices=["y", "n"],
                default="y",
            )
            == "n"
        ):
            print()
            raise Exception(
                "Agent link does not match the current server profile. Use [bold]dreadnode agent switch[/] or [bold]dreadnode profile switch[/]."
            )

        switch_profile(agent_config.active_link.profile)


def get_repo_archive_source_path(source_dir: pathlib.Path) -> pathlib.Path:
    """Return the actual source directory from a git repositoryZIP archive."""

    if not (source_dir / "Dockerfile").exists() and not (source_dir / "Dockerfile.j2").exists():
        # if src has been downloaded from a ZIP archive, it may contain a single
        # '<user>-<repo>-<commit hash>' folder, that is the actual source we want to use.
        # Check if source_dir contains only one folder and update it if so.
        children = list(source_dir.iterdir())
        if len(children) == 1 and children[0].is_dir():
            source_dir = children[0]

    return source_dir


@cli.command(help="List available agent templates with their descriptions")
@pretty_cli
def templates() -> None:
    print(format_templates())


@cli.command(help="Initialize a new agent project")
@pretty_cli
def init(
    strike: t.Annotated[str, typer.Argument(help="The target strike")],
    directory: t.Annotated[
        pathlib.Path,
        typer.Option("--dir", "-d", help="The directory to initialize", file_okay=False, resolve_path=True),
    ] = pathlib.Path("."),
    name: t.Annotated[
        str | None, typer.Option("--name", "-n", help="The project name (used for container naming)")
    ] = None,
    template: t.Annotated[
        Template, typer.Option("--template", "-t", help="The template to use for the agent")
    ] = Template.rigging_basic,
    source: t.Annotated[
        str | None,
        typer.Option(
            "--source",
            "-s",
            help="Initialize the agent using a custom template from a github repository, ZIP archive URL or local folder",
        ),
    ] = None,
    path: t.Annotated[
        str | None,
        typer.Option(
            "--path",
            "-p",
            help="If --source has been provided, use --path to specify a subfolder to initialize from",
        ),
    ] = None,
) -> None:
    try:
        AgentConfig.read(directory)
        if Prompt.ask(":axe: Agent config exists, overwrite?", choices=["y", "n"], default="n") == "n":
            return
        print()
    except Exception:
        pass

    print(f":coffee: Fetching strike '{strike}' ...")

    client = api.create_client()

    try:
        strike_response = client.get_strike(strike)
    except Exception as e:
        raise Exception(f"Failed to find strike '{strike}': {e}") from e

    print(f":crossed_swords: Linking to strike '{strike_response.name}' ({strike_response.type})")
    print()

    project_name = Prompt.ask("Project name?", default=name or directory.name)
    print()

    directory.mkdir(exist_ok=True)

    context = {"project_name": project_name, "strike": strike_response}

    if source is None:
        # initialize from builtin template
        template = Template(Prompt.ask("Template?", choices=[t.value for t in Template], default=template.value))

        install_template(template, directory, context)
    else:
        source_dir = pathlib.Path(source)
        cleanup = False

        if not source_dir.exists():
            # source is not a local folder, so it can be:
            # - full ZIP archive URL
            # - github compatible reference

            try:
                github_repo = GithubRepo(source)

                # Check if the repo is accessible
                if repo_exists(github_repo):
                    source_dir = download_and_unzip_archive(github_repo.zip_url)

                # This could be a private repo that the user can access
                # by getting an access token from our API
                elif github_repo.namespace == "dreadnode":
                    github_access_token = client.get_github_access_token([github_repo.repo])
                    print(":key: Accessed private repository")
                    source_dir = download_and_unzip_archive(
                        github_repo.api_zip_url, headers={"Authorization": f"Bearer {github_access_token.token}"}
                    )

                else:
                    raise Exception(f"Repository '{github_repo}' not found or inaccessible")

                # github repos zip archives usually contain a single branch folder, the real source dir,
                # and the path is not known beforehand
                source_dir = get_repo_archive_source_path(source_dir)

            except ValueError:
                # not a repo, download and unzip as a ZIP archive URL
                source_dir = download_and_unzip_archive(source)

            # make sure the temporary directory is cleaned up
            cleanup = True

        try:
            # add subpath if specified
            if path is not None:
                source_dir = source_dir / path

            install_template_from_dir(source_dir, directory, context)
        except Exception:
            if cleanup and source_dir.exists():
                shutil.rmtree(source_dir)
            raise

    # Wait to write this until after the template is installed
    AgentConfig(project_name=project_name, strike=strike).write(directory=directory)

    print()
    print(f"Initialized [b]{directory}[/]")


@cli.command(help="Push a new version of the active agent")
@pretty_cli
def push(
    directory: t.Annotated[
        pathlib.Path,
        typer.Option("--dir", "-d", help="The agent directory", file_okay=False, resolve_path=True),
    ] = pathlib.Path("."),
    tag: t.Annotated[str | None, typer.Option("--tag", "-t", help="The tag to use for the image")] = None,
    env_vars: t.Annotated[
        list[str] | None,
        typer.Option("--env-var", "-e", help="Environment vars to use when executing the image (key=value)"),
    ] = None,
    new: t.Annotated[bool, typer.Option("--new", "-n", help="Create a new agent instead of a new version")] = False,
    notes: t.Annotated[str | None, typer.Option("--message", "-m", help="Notes for the new version")] = None,
    rebuild: t.Annotated[bool, typer.Option("--rebuild", "-r", help="Force rebuild the agent image")] = False,
) -> None:
    env = {env_var.split("=")[0]: env_var.split("=")[1] for env_var in env_vars or []}

    agent_config = AgentConfig.read(directory)
    user_config = UserConfig.read()

    if not user_config.active_profile_name:
        raise Exception("No server profile is set, use [bold]dreadnode login[/] to authenticate")

    if agent_config.links and not agent_config.has_link_to_profile(user_config.active_profile_name):
        print(f":link: Linking as a fresh agent to the current profile [magenta]{user_config.active_profile_name}[/]")
        new = True

    server_config = user_config.get_server_config()

    registry = get_registry(server_config)

    print(f":key: Authenticating with [bold]{registry}[/] ...")
    docker.login(registry, server_config.username, server_config.api_key)

    print()
    print(f":wrench: Building agent from [b]{directory}[/] ...")
    image = docker.build(directory, force_rebuild=rebuild)
    repository = f"{registry}/{server_config.username}/agents/{agent_config.project_name}"
    tag = tag or image.id[-8:]

    print()
    print(f":package: Pushing agent to [b]{repository}:{tag}[/] ...")
    docker.push(image, repository, tag)

    client = api.create_client()
    container = api.Client.Container(image=f"{repository}:{tag}", env=env, name=None)

    if new or not agent_config.links:
        print()
        print(":robot: Creating a new agent ...")
        name = Prompt.ask("Agent name?", default=agent_config.project_name)
        notes = notes or Prompt.ask("Notes?")

        agent = client.create_strike_agent(container, name, strike=agent_config.strike, notes=notes)
        agent_config.add_link(agent.key, agent.id, user_config.active_profile_name).write(directory)
    else:
        active_agent_id = agent_config.active
        if active_agent_id is None:
            raise Exception("No active agent link found. Use 'switch' command to set an active link.")

        print()
        print(":robot: Creating a new version ...")
        notes = notes or Prompt.ask("Notes?")

        try:
            agent = client.create_strike_agent_version(str(active_agent_id), container, notes)
        except Exception as e:
            # 404 is expected if the agent was created on a different server profile
            if str(e).startswith("404"):
                raise Exception(
                    f"Agent '{active_agent_id}' not found for the current server profile, create the agent again."
                ) from e
            else:
                raise e

    print(format_agent(agent))

    print()
    print(":tada: Agent pushed. use [bold]dreadnode agent deploy[/] to start a new run.")


@cli.command(help="Start a new run using the latest active agent version")
@pretty_cli
def deploy(
    model: t.Annotated[
        str | None, typer.Option("--model", "-m", help="The inference model to use for this run")
    ] = None,
    directory: t.Annotated[
        pathlib.Path,
        typer.Option("--dir", "-d", help="The agent directory", file_okay=False, resolve_path=True),
    ] = pathlib.Path("."),
    strike: t.Annotated[str | None, typer.Option("--strike", "-s", help="The strike to use for this run")] = None,
    watch: t.Annotated[bool, typer.Option("--watch", "-w", help="Watch the run status")] = True,
) -> None:
    agent_config = AgentConfig.read(directory)
    ensure_profile(agent_config)

    active_link = agent_config.active_link

    client = api.create_client()
    agent = client.get_strike_agent(active_link.id)

    strike = strike or agent_config.strike
    if strike is None:
        raise Exception("No strike specified, use -s/--strike or set the strike in the agent config")

    # Verify the model if it was supplied
    if model is not None:
        strike_response = client.get_strike(strike)
        if not any(m.key == model for m in strike_response.models):
            print(format_models(strike_response.models))
            raise Exception(f"Model '{model}' not found in strike '{strike_response.name}'")

    run = client.start_strike_run(agent.latest_version.id, strike=strike, model=model)
    agent_config.add_run(run.id).write(directory)
    formatted = format_run(run)

    if not watch:
        print(formatted)
        return

    try:
        with Live(formatted, refresh_per_second=2) as live:
            while run.is_running():
                time.sleep(1)
                run = client.get_strike_run(run.id)
                live.update(format_run(run))
    except KeyboardInterrupt:
        print("\n:warning: Terminating run...")
        client.terminate_strike_run(run.id)
        run = client.get_strike_run(run.id)
        print(format_run(run))
        return


@cli.command(help="List available models for the current (or specified) strike")
@pretty_cli
def models(
    directory: t.Annotated[
        pathlib.Path, typer.Argument(help="The agent directory", file_okay=False, resolve_path=True)
    ] = pathlib.Path("."),
    strike: t.Annotated[str | None, typer.Option("--strike", "-s", help="The strike to query")] = None,
) -> None:
    if strike is None:
        agent_config = AgentConfig.read(directory)
        ensure_profile(agent_config)

    strike = strike or agent_config.strike
    if strike is None:
        raise Exception("No strike specified, use -s/--strike or set the strike in the agent config")

    strike_response = api.create_client().get_strike(strike)
    print(format_models(strike_response.models))


@cli.command(help="List available strikes")
@pretty_cli
def strikes() -> None:
    client = api.create_client()
    strikes = client.list_strikes()
    print(format_strikes(strikes))


@cli.command(help="Show the latest run of the active agent")
@pretty_cli
def latest(
    directory: t.Annotated[
        pathlib.Path,
        typer.Option("--dir", "-d", help="The agent directory", file_okay=False, resolve_path=True),
    ] = pathlib.Path("."),
    verbose: t.Annotated[bool, typer.Option("--verbose", "-v", help="Show detailed run information")] = False,
    logs: t.Annotated[
        bool, typer.Option("--logs", "-l", help="Show all container logs for the run (only in verbose mode)")
    ] = False,
    raw: t.Annotated[bool, typer.Option("--raw", help="Show raw JSON output")] = False,
) -> None:
    agent_config = AgentConfig.read(directory)
    ensure_profile(agent_config)

    active_link = agent_config.active_link
    if not active_link.runs:
        print(":exclamation: No runs yet, use [bold]dreadnode agent deploy[/]")
        return

    client = api.create_client()
    run = client.get_strike_run(str(active_link.runs[-1]))

    if raw:
        print(run.model_dump(mode="json"))
    else:
        print(format_run(run, verbose=verbose, include_logs=logs))


@cli.command(help="Show the status of the active agent")
@pretty_cli
def show(
    directory: t.Annotated[
        pathlib.Path,
        typer.Option("--dir", "-d", help="The agent directory", file_okay=False, resolve_path=True),
    ] = pathlib.Path("."),
) -> None:
    agent_config = AgentConfig.read(directory)
    ensure_profile(agent_config)

    client = api.create_client()
    agent = client.get_strike_agent(agent_config.active_link.id)
    print(format_agent(agent))


@cli.command(help="List historical versions of the active agent")
@pretty_cli
def versions(
    directory: t.Annotated[
        pathlib.Path, typer.Argument(help="The agent directory", file_okay=False, resolve_path=True)
    ] = pathlib.Path("."),
) -> None:
    agent_config = AgentConfig.read(directory)
    ensure_profile(agent_config)

    client = api.create_client()
    agent = client.get_strike_agent(agent_config.active_link.id)
    print(format_agent_versions(agent))


@cli.command(help="List runs for the active agent")
@pretty_cli
def runs(
    directory: t.Annotated[
        pathlib.Path, typer.Argument(help="The agent directory", file_okay=False, resolve_path=True)
    ] = pathlib.Path("."),
) -> None:
    agent_config = AgentConfig.read(directory)
    ensure_profile(agent_config)

    client = api.create_client()
    runs = [
        run for run in client.list_strike_runs() if run.id in agent_config.active_link.runs and run.start is not None
    ]
    runs = sorted(runs, key=lambda r: r.start or 0, reverse=True)

    if not runs:
        print(":exclamation: No runs yet, use [bold]dreadnode agent deploy[/]")
        return

    print(format_runs(runs))


@cli.command(help="List available agent links")
@pretty_cli
def links(
    directory: t.Annotated[
        pathlib.Path, typer.Argument(help="The agent directory", file_okay=False, resolve_path=True)
    ] = pathlib.Path("."),
) -> None:
    agent_config = AgentConfig.read(directory)
    user_config = UserConfig.read()
    _ = agent_config.active_link

    table = Table(box=box.ROUNDED)
    table.add_column("Key", style="magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Profile")
    table.add_column("ID")

    for key, link in agent_config.links.items():
        active_link = key == agent_config.active
        mismatched_profile = active_link and user_config.active_profile_name != link.profile
        client = api.create_client(profile=agent_config.links[key].profile)
        agent = client.get_strike_agent(link.id)
        table.add_row(
            agent.key + ("*" if active_link else ""),
            agent.name or "N/A",
            link.profile + ("[bold red]* (not-active)[/]" if mismatched_profile else ""),
            f"[dim]{agent.id}[/]",
            style="bold" if active_link else None,
        )

    print(table)


@cli.command(help="Switch to a different agent link")
@pretty_cli
def switch(
    agent_or_profile: t.Annotated[str, typer.Argument(help="Agent key/id or profile name")],
    directory: t.Annotated[
        pathlib.Path, typer.Argument(help="The agent directory", file_okay=False, resolve_path=True)
    ] = pathlib.Path("."),
) -> None:
    agent_config = AgentConfig.read(directory)

    for key, link in agent_config.links.items():
        if agent_or_profile in (key, link.id) or agent_or_profile == link.profile:
            print(
                f":robot: Switched to link [bold magenta]{key}[/] for profile [cyan]{link.profile}[/] ([dim]{link.id}[/])"
            )
            agent_config.active = key
            agent_config.write(directory)
            return

    print(f":exclamation: '{agent_or_profile}' not found, use [bold]dreadnode agent links[/]")


@cli.command(help="Clone a github repository")
@pretty_cli
def clone(
    repo: t.Annotated[str, typer.Argument(help="Repository name or URL")],
    target: t.Annotated[
        pathlib.Path | None, typer.Argument(help="The target directory", file_okay=False, resolve_path=True)
    ] = None,
) -> None:
    github_repo = GithubRepo(repo)

    # Check if the target directory exists
    target = target or pathlib.Path(github_repo.repo)
    if target.exists():
        if Prompt.ask(f":axe: Overwrite {target.absolute()}?", choices=["y", "n"], default="n") == "n":
            return
        print()
        shutil.rmtree(target)

    # Check if the repo is accessible
    if repo_exists(github_repo):
        temp_dir = download_and_unzip_archive(github_repo.zip_url)

    # This could be a private repo that the user can access
    # by getting an access token from our API
    elif github_repo.namespace == "dreadnode":
        github_access_token = api.create_client().get_github_access_token([github_repo.repo])
        print(":key: Accessed private repository")
        temp_dir = download_and_unzip_archive(
            github_repo.api_zip_url, headers={"Authorization": f"Bearer {github_access_token.token}"}
        )

    else:
        raise Exception(f"Repository '{github_repo}' not found or inaccessible")

    # We assume the repo download results in a single
    # child folder which is the real target
    sub_dirs = list(temp_dir.iterdir())
    if len(sub_dirs) == 1 and sub_dirs[0].is_dir():
        temp_dir = sub_dirs[0]

    shutil.move(temp_dir, target)

    print()
    print(f":tada: Cloned [b]{repo}[/] to [b]{target.absolute()}[/]")
