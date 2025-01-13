import typing as t

from rich import box
from rich.console import RenderableType
from rich.table import Table
from rich.text import Text

from dreadnode_cli.model.config import UserModel

P = t.ParamSpec("P")


def format_api_key(api_key: str) -> RenderableType:
    if api_key.startswith("$"):  # Environment variable
        return Text(api_key, style="blue")
    return Text(api_key[:5] + "***" if len(api_key) > 5 else "***", style="magenta")


def format_user_models(models: dict[str, UserModel]) -> RenderableType:
    table = Table(box=box.ROUNDED)
    table.add_column("ID", style="bold cyan")
    table.add_column("Name")
    table.add_column("Provider")
    table.add_column("Generator ID")
    table.add_column("API Key")

    for model_id, model in models.items():
        table.add_row(
            Text(model_id, style="bold"),
            Text(model.name or "-", style="dim" if not model.name else ""),
            Text(model.provider or "-", style="dim" if not model.provider else ""),
            Text(model.generator_id),
            format_api_key(model.api_key),
        )

    return table
