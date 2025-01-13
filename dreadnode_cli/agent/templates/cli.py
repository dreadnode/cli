import pathlib
import shutil
import typing as t

import typer
from rich import print

from dreadnode_cli import api
from dreadnode_cli.agent.templates.format import format_templates
from dreadnode_cli.agent.templates.manager import TemplateManager
from dreadnode_cli.defaults import TEMPLATES_DEFAULT_REPO
from dreadnode_cli.ext.typer import AliasGroup
from dreadnode_cli.types import GithubRepo
from dreadnode_cli.utils import download_and_unzip_archive, get_repo_archive_source_path, pretty_cli

cli = typer.Typer(no_args_is_help=True, cls=AliasGroup)


@cli.command("show|list", help="List available agent templates with their descriptions")
@pretty_cli
def show() -> None:
    template_manager = TemplateManager()
    if not template_manager.templates:
        raise Exception("No templates installed, use [bold]dreadnode agent templates install[/] to install some.")

    print(format_templates(template_manager.templates))


@cli.command(help="Install a template pack")
@pretty_cli
def install(
    source: t.Annotated[str, typer.Argument(help="The source of the template pack")] = TEMPLATES_DEFAULT_REPO,
) -> None:
    template_manager = TemplateManager()
    source_dir: pathlib.Path = pathlib.Path(source)
    pack_name: str | None = None
    cleanup = False

    if not source_dir.exists():
        # source is not a local folder, so it can be:
        # - full ZIP archive URL
        # - github compatible reference
        try:
            github_repo = GithubRepo(source)

            # Check if the repo is accessible
            if github_repo.exists:
                source_dir = download_and_unzip_archive(github_repo.zip_url)

            # This could be a private repo that the user can access
            # by getting an access token from our API
            elif github_repo.namespace == "dreadnode":
                try:
                    github_access_token = api.create_client().get_github_access_token([github_repo.repo])
                    print(":key: Accessed private repository")
                    source_dir = download_and_unzip_archive(
                        github_repo.api_zip_url, headers={"Authorization": f"Bearer {github_access_token.token}"}
                    )
                except Exception as e:
                    raise Exception(f"Failed to access private repository '{github_repo}': {e}") from e

            else:
                raise Exception(f"Repository '{github_repo}' not found or inaccessible")

            # github repos zip archives usually contain a single branch folder, the real source dir,
            # and the path is not known beforehand
            source_dir = get_repo_archive_source_path(source_dir)
            pack_name = f"{github_repo.namespace}-{github_repo.repo}"

        except ValueError:
            # not a repo, download and unzip as a ZIP archive URL
            source_dir = download_and_unzip_archive(source)

        # make sure the temporary directory is cleaned up
        cleanup = True

    try:
        # install the template pack
        template_manager.install_template_pack(source_dir, pack_name)
    except Exception:
        if cleanup and source_dir.exists():
            shutil.rmtree(source_dir)
        raise
