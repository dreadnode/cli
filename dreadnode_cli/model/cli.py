import typing as t

import typer
from rich import print

from dreadnode_cli.defaults import USER_MODELS_CONFIG_PATH
from dreadnode_cli.ext.typer import AliasGroup
from dreadnode_cli.model.config import UserModel, UserModels
from dreadnode_cli.model.format import format_user_models
from dreadnode_cli.utils import pretty_cli

cli = typer.Typer(no_args_is_help=True, cls=AliasGroup)


@cli.command("show|list", help="List all configured models")
@pretty_cli
def show() -> None:
    config = UserModels.read()
    if not config.models:
        print(":exclamation: No models are configured, use [bold]dreadnode models add[/].")
        return

    print(format_user_models(config.models))


@cli.command(
    help="Add a new inference model",
    epilog="If $ENV_VAR syntax is used for the api key, it will be replaced with the environment value when used.",
    no_args_is_help=True,
)
@pretty_cli
def add(
    id: t.Annotated[str, typer.Option("--id", help="Identifier for referencing this model")],
    generator_id: t.Annotated[str, typer.Option("--generator-id", "-g", help="Rigging (LiteLLM) generator id")],
    api_key: t.Annotated[
        str, typer.Option("--api-key", "-k", help="API key for the inference provider (supports $ENV_VAR syntax)")
    ],
    name: t.Annotated[str | None, typer.Option("--name", "-n", help="Friendly name")] = None,
    provider: t.Annotated[str | None, typer.Option("--provider", "-p", help="Provider name")] = None,
    update: t.Annotated[bool, typer.Option("--update", "-u", help="Update an existing model if it exists")] = False,
) -> None:
    config = UserModels.read()
    exists = id in config.models

    if exists and not update:
        print(f":exclamation: Model with id [bold]{id}[/] already exists (use -u/--update to modify)")
        return

    config.models[id] = UserModel(name=name, provider=provider, generator_id=generator_id, api_key=api_key)
    config.write()

    print(f":wrench: {'Updated' if exists else 'Added'} model [bold]{id}[/] in {USER_MODELS_CONFIG_PATH}")


@cli.command(help="Remove an user inference model", no_args_is_help=True)
@pretty_cli
def forget(id: t.Annotated[str, typer.Argument(help="Model to remove")]) -> None:
    config = UserModels.read()
    if id not in config.models:
        print(f":exclamation: Model with id [bold]{id}[/] does not exist")
        return

    del config.models[id]
    config.write()

    print(f":axe: Forgot about [bold]{id}[/] in {USER_MODELS_CONFIG_PATH}")
