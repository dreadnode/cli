import typing as t
from datetime import datetime

from rich import box
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table
from rich.text import Text

from dreadnode_cli import api

P = t.ParamSpec("P")


def get_status_style(status: str | None) -> str:
    return (
        {
            "pending": "dim",
            "running": "bold cyan",
            "completed": "bold green",
            "failed": "bold red",
            "timeout": "bold yellow",
        }.get(status, "")
        if status
        else ""
    )


def get_model_provider_style(provider: str) -> str:
    return {
        "OpenAI": "spring_green4",
        "Hugging Face": "blue",
        "Dreadnode": "magenta",
        "Anthropic": "tan",
        "MistralAI": "orange_red1",
        "Groq": "red",
    }.get(provider, "")


def pretty_container_logs(logs: str) -> str:
    lines: list[str] = []
    for line in logs.splitlines():
        parts = line.split(" ", 1)
        lines.append(f"[dim]{parts[0]}[/] {parts[1]}")
    return "\n".join(lines)


def format_duration(start: datetime | None, end: datetime | None) -> str:
    if not (start and end):
        return "..."
    return f"{(end - start).total_seconds():.1f}s"


def format_time(dt: datetime | None) -> str:
    return dt.astimezone().strftime("%c") if dt else "-"


def format_models(models: list[api.Client.StrikeModel]) -> RenderableType:
    table = Table(box=box.ROUNDED)
    table.add_column("key")
    table.add_column("name")
    table.add_column("provider")

    for model in models:
        provider_style = get_model_provider_style(model.provider)
        table.add_row(
            Text(model.key),
            Text(model.name, style=f"bold {provider_style}"),
            Text(model.provider, style=provider_style),
        )

    return table


def format_runs(runs: list[api.Client.StrikeRunSummaryResponse]) -> RenderableType:
    table = Table(box=box.ROUNDED)
    table.add_column("id", style="dim")
    table.add_column("agent")
    table.add_column("status")
    table.add_column("started")
    table.add_column("duration")

    for run in runs:
        table.add_row(
            str(run.id),
            f"[bold magenta]{run.agent_key}[/] [dim]:[/] [yellow]{run.agent_revision}[/]",
            Text(run.status, style="bold " + get_status_style(run.status)),
            format_time(run.start),
            Text(format_duration(run.start, run.end), style="bold cyan"),
        )

    return table


def format_strikes(strikes: list[api.Client.StrikeSummaryResponse]) -> RenderableType:
    table = Table(box=box.ROUNDED)
    table.add_column("key")
    table.add_column("name")
    table.add_column("type")
    table.add_column("competitive", justify="center")
    table.add_column("models")

    def _format_model(model: api.Client.StrikeModel) -> str:
        provider_style = get_model_provider_style(model.provider)
        return f"[{provider_style}]{model.key}[/]"

    for strike in strikes:
        table.add_row(
            Text(strike.key),
            Text(strike.name, style="bold cyan"),
            Text(strike.type, style="magenta"),
            ":skull:" if strike.competitive else "-",
            ", ".join(_format_model(model) for model in strike.models),
        )

    return table


def format_agent(agent: api.Client.StrikeAgentResponse) -> RenderableType:
    table = Table(show_header=False, box=box.ROUNDED)
    table.add_column("Property", justify="right")
    table.add_column("Value")

    table.add_row("id", f"[dim]{agent.id}[/]")
    table.add_row("key", f"[magenta]{agent.key}[/]")
    table.add_row("name", f"[magenta]{agent.name or '-'}[/]")
    table.add_row("revision", f"[yellow]{agent.revision}[/]")
    table.add_row("last status", Text(agent.last_run_status or "-", style=get_status_style(agent.last_run_status)))
    table.add_row("created", f"[cyan]{agent.created_at.astimezone().strftime('%c')}[/]")
    table.add_row("", "")

    latest_table = Table(show_header=False, box=box.ROUNDED)
    latest_table.add_column("Property", justify="right")
    latest_table.add_column("Value")

    latest_table.add_row("id", f"[dim]{agent.latest.id}[/]")
    latest_table.add_row("created", f"[cyan]{agent.latest.created_at.astimezone().strftime('%c')}[/]")
    latest_table.add_row("notes", agent.latest.notes or "-")

    table.add_row("latest", latest_table)

    return table


def format_agent_versions(agent: api.Client.StrikeAgentResponse) -> RenderableType:
    table = Table(box=box.ROUNDED)
    table.add_column("rev", style="yellow")
    table.add_column("notes", style="cyan")
    table.add_column("image")
    table.add_column("created")

    for i, version in enumerate(sorted(agent.versions, key=lambda v: v.created_at)):
        latest = version.id == agent.latest.id
        table.add_row(
            str(i + 1) + ("*" if latest else ""),
            version.notes or "-",
            version.container.image,
            f"[dim]{version.created_at.astimezone().strftime('%c')}[/]",
            style="bold" if latest else None,
        )

    return table


def format_zones_summary(zones: list[api.Client.StrikeRunZone]) -> RenderableType:
    table = Table(box=box.SIMPLE, padding=(0, 1))
    table.add_column("zone", style="cyan")
    table.add_column("status")
    table.add_column("duration")
    table.add_column("inferences", justify="center")
    table.add_column("outputs", justify="center")
    table.add_column("score", justify="center")

    for zone in zones:
        zone_score = sum(
            output.score.value if hasattr(output, "score") and output.score else 0 for output in zone.outputs
        )

        table.add_row(
            zone.key,
            Text(zone.status, style=get_status_style(zone.status)),
            Text(format_duration(zone.start, zone.end) if zone.end else "...", style="bold"),
            Text(str(len(zone.inferences)) if zone.inferences else "-", style="dim"),
            Text(str(len(zone.outputs)) if zone.outputs else "-", style="magenta"),
            Text(str(zone_score), style="yellow" if zone_score > 0 else "dim"),
        )

    return table


def format_zones_verbose(zones: list[api.Client.StrikeRunZone], *, include_logs: bool = False) -> RenderableType:
    components: list[RenderableType] = []

    for zone in zones:
        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("Property", style="dim")
        table.add_column("Value")

        zone_score = sum(output.score.value if output.score else 0 for output in zone.outputs)

        table.add_row("id", f"[dim]{zone.id}[/]")
        table.add_row("score", f"[yellow]{zone_score}[/]" if zone_score else "[dim]0[/]")
        table.add_row("outputs", f"[magenta]{len(zone.outputs)}[/]" if zone.outputs else "[dim]0[/]")
        table.add_row("start", format_time(zone.start))
        table.add_row("end", format_time(zone.end))
        table.add_row("duration", Text(format_duration(zone.start, zone.end), style="bold cyan"))
        table.add_row("", "")

        sub_components: list[RenderableType] = [table]

        if zone.outputs:
            outputs_table = Table(box=box.SIMPLE, padding=(0, 1))
            outputs_table.add_column("score", justify="center", style="yellow")
            outputs_table.add_column("output", style="cyan")
            outputs_table.add_column("explanation")

            for output in zone.outputs:
                outputs_table.add_row(
                    str(output.score.value) if output.score else "-",
                    Pretty(output.data),
                    output.score.explanation if output.score else "-",
                )

            outputs_panel = Panel(
                outputs_table,
                title="outputs",
                title_align="left",
                style="magenta",
            )
            sub_components.append(outputs_panel)

        if zone.agent_logs:
            agent_log_panel = Panel(
                pretty_container_logs(zone.agent_logs),
                title="[dim]logs:[/] [bold]agent[/]",
                title_align="left",
                style="cyan",
            )
            sub_components.append(agent_log_panel)

        if include_logs:
            for container, logs in zone.container_logs.items():
                container_log_panel = Panel(
                    pretty_container_logs(logs),
                    title=f"[dim]logs:[/] [bold]{container}[/]",
                    title_align="left",
                    style="blue",
                )
                sub_components.append(container_log_panel)

        panel = Panel(
            Group(*sub_components),
            title=f"[dim]zone:[/] [bold]{zone.key} [{get_status_style(zone.status)}]({zone.status})[/]",
            title_align="left",
            border_style="cyan",
        )
        components.append(panel)

    return Group(*components)


def format_run(run: api.Client.StrikeRunResponse, *, verbose: bool = False, include_logs: bool = False) -> Panel:
    # Main run information
    table = Table(show_header=False, box=box.SIMPLE)
    table.add_column("Property", style="dim")
    table.add_column("Value")

    table.add_row("status", Text(run.status, style=get_status_style(run.status)))
    table.add_row("strike", f"[magenta]{run.strike_name}[/] ([dim]{run.strike_key}[/])")
    table.add_row("type", run.strike_type)

    table.add_row("", "")
    table.add_row("agent", f"[bold magenta]{run.agent_key}[/] ([dim]rev[/] [yellow]{run.agent_revision}[/])")
    table.add_row("image", Text(run.agent_version.container.image, style="cyan"))
    table.add_row("notes", run.agent_version.notes or "-")

    table.add_row("", "")
    table.add_row("duration", Text(format_duration(run.start, run.end), style="bold cyan"))
    table.add_row("start", format_time(run.start))
    table.add_row("end", format_time(run.end))

    components: list[RenderableType] = [
        table,
        format_zones_verbose(run.zones, include_logs=include_logs) if verbose else format_zones_summary(run.zones),
    ]

    return Panel(Group(*components), title=f"[bold]run [dim]{run.id}[/]", title_align="left", border_style="blue")
