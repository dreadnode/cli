from rich import box
from rich.console import RenderableType
from rich.table import Table

from dreadnode_cli.agent.templates.manager import Template


def format_templates(templates: dict[str, Template]) -> RenderableType:
    table = Table(box=box.ROUNDED)
    table.add_column("template")
    table.add_column("version")
    table.add_column("strikes")
    table.add_column("description")

    for name, template in templates.items():
        all = [f"[bold]{s}[/]" for s in template.manifest.strikes or []] + [
            f"[bold green]{s}[/]" for s in template.manifest.strikes_types or []
        ]

        strikes = ", ".join(all) if all else "[dim]-[/]"

        table.add_row(f"[bold magenta]{name}[/]", template.manifest.version, strikes, template.manifest.description)

    return table
