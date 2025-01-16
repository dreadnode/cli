import enum
import pathlib
import typing as t

import typer
from rich import box, print
from rich.table import Table

from dreadnode_cli.dreadnode import api
from dreadnode_cli.utils import pretty_cli

cli = typer.Typer(no_args_is_help=True)


class Sorting(str, enum.Enum):
    none = "none"
    by_difficulty = "difficulty"
    by_status = "status"
    by_title = "title"
    by_authors = "authors"
    by_tags = "tags"


class SortingOrder(str, enum.Enum):
    ascending = "ascending"
    descending = "descending"


def map_difficulty(difficulty: str) -> int:
    if difficulty == "easy":
        return 1
    elif difficulty == "medium":
        return 2
    else:
        return 3


def format_difficulty(difficulty: str) -> str:
    return ":skull:" * map_difficulty(difficulty)


@cli.command(help="List challenges")
@pretty_cli
def list(
    sorting: t.Annotated[Sorting, typer.Option("--sort-by", help="The sorting order")] = Sorting.none,
    sorting_order: t.Annotated[
        SortingOrder, typer.Option("--sort-order", help="The sorting order")
    ] = SortingOrder.ascending,
) -> None:
    challenges = api.create_client().list_challenges()

    if sorting == Sorting.by_difficulty:
        challenges.sort(key=lambda x: map_difficulty(x.difficulty), reverse=sorting_order == SortingOrder.descending)
    elif sorting == Sorting.by_status:
        challenges.sort(key=lambda x: x.status, reverse=sorting_order == SortingOrder.descending)
    elif sorting == Sorting.by_title:
        challenges.sort(key=lambda x: x.title, reverse=sorting_order == SortingOrder.descending)
    elif sorting == Sorting.by_authors:
        challenges.sort(key=lambda x: ", ".join(x.authors), reverse=sorting_order == SortingOrder.descending)
    elif sorting == Sorting.by_tags:
        challenges.sort(key=lambda x: ", ".join(x.tags), reverse=sorting_order == SortingOrder.descending)

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
