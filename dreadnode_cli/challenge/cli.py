import pathlib
import typing as t

import typer
from rich import box, print
from rich.table import Table

import dreadnode_cli.api as api
from dreadnode_cli.utils import pretty_cli

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
@pretty_cli
def list() -> None:
    challenges = api.create_client().list_challenges()

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
@pretty_cli
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
    content = api.create_client().get_challenge_artifact(challenge_id, artifact_name)
    file_path = output_path / artifact_name
    file_path.write_bytes(content)

    print(f":floppy_disk: Saved to [bold]{file_path}[/]")


@cli.command(help="Submit a flag to a challenge")
@pretty_cli
def submit_flag(
    challenge: t.Annotated[str, typer.Argument(help="Challenge name")],
    flag: t.Annotated[str, typer.Argument(help="Challenge flag")],
) -> None:
    print(f":pirate_flag: submitting flag to challenge [bold]{challenge}[/] ...")

    correct = api.create_client().submit_challenge_flag(challenge, flag)

    if correct:
        print(":tada: The flag was correct. Congrats!")
    else:
        print(":cross_mark: The flag was incorrect. Keep trying!")
