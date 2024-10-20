import pathlib
import typing as t

import typer
from rich import box, print
from rich.table import Table

import dreadnode_cli.api as api
from dreadnode_cli.utils import exit_with_pretty_error

cli = typer.Typer(no_args_is_help=True)


def format_difficulty(difficulty: str) -> str:
    if difficulty == "easy":
        return ":skull:"
    elif difficulty == "medium":
        return ":skull::skull:"
    else:
        return ":skull::skull::skull:"


# TODO: add sorting and filtering
@cli.command(help="List challenges")
@exit_with_pretty_error
def list() -> None:
    client = api.client()
    challenges = client.list_challenges()

    table = Table(box=box.ROUNDED)
    table.add_column("Title")
    table.add_column("Done", justify="center")
    table.add_column("Lead")
    table.add_column("Difficulty")
    table.add_column("Authors")
    table.add_column("Tags")

    for challenge in challenges:
        table.add_row(
            f"[bold]{challenge.title}[/]",
            ":white_check_mark:" if challenge.status == "completed" else "",
            f"[dim]{challenge.lead}[/]",
            format_difficulty(challenge.difficulty),
            ", ".join(challenge.authors),
            ", ".join(challenge.tags),
        )

    print(table)


@cli.command(help="Download a challenge artifact.")
@exit_with_pretty_error
def artifact(
    challenge_id: t.Annotated[str, typer.Argument(help="Challenge name")],
    artifact_name: t.Annotated[str, typer.Argument(help="Artifact name")],
    output_path: t.Annotated[
        pathlib.Path,
        typer.Option(
            "--output", "-o", help="The directory to save the artifact to.", file_okay=False, resolve_path=True
        ),
    ] = pathlib.Path("."),
) -> None:
    client = api.client()
    content = client.get_challenge_artifact(challenge_id, artifact_name)
    file_path = output_path / artifact_name
    file_path.write_bytes(content)

    print(f":floppy_disk: Saved to [bold]{file_path}[/]")


@cli.command(help="Submit a flag to a challenge")
@exit_with_pretty_error
def submit_flag(
    challenge_id: t.Annotated[str, typer.Argument(help="Challenge name")],
    flag: t.Annotated[str, typer.Argument(help="Challenge flag")],
) -> None:
    client = api.client()
    correct = client.submit_challenge_flag(challenge_id, flag)

    if correct:
        print(":white_check_mark: The flag was correct. Congrats!")
    else:
        print(":cross_mark: The flag was incorrect. Keep trying!")
