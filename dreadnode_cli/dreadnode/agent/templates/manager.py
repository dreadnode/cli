import os
import pathlib
import shutil
import typing as t
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel
from pydantic_yaml import parse_yaml_raw_as
from rich import print
from rich.prompt import Prompt

from dreadnode_cli.dreadnode.defaults import TEMPLATE_MANIFEST_FILE, TEMPLATES_PATH


class Manifest(BaseModel):
    # generic agent info
    description: str
    version: str = "0.0.1"
    homepage: str | None = None
    authors: list[str] | None = None
    keywords: list[str] | None = None
    # optional runtime requirements
    requirements: dict[str, str] | None = None
    # which strike this agent is meant to be used for
    strikes: list[str] | None = None
    # which strike types this agent is meant to be used for
    strikes_types: list[str] | None = None

    def matches_strike(self, strike_name: str, strike_type: str) -> bool:
        """Return True if the manifest matches the given strike."""

        if self.strikes and strike_name.lower() in [s.lower() for s in self.strikes]:
            return True

        elif self.strikes_types and strike_type.lower() in [s.lower() for s in self.strikes_types]:
            return True

        else:
            return not self.strikes and not self.strikes_types


class Template(BaseModel):
    manifest: Manifest
    path: Path


class TemplateManager:
    def __init__(self, base_path: Path = TEMPLATES_PATH) -> None:
        self.base_path = base_path
        self.templates: dict[str, Template] = {}

        # create the templates directory if it doesn't exist
        if not self.base_path.exists():
            self.base_path.mkdir(parents=True)

        # load all templates from the templates directory
        for manifest_path in self.base_path.glob(f"**/{TEMPLATE_MANIFEST_FILE}"):
            manifest = parse_yaml_raw_as(Manifest, manifest_path.read_text())
            # get the template name from <base_path/>whatever/name</manifest.yaml>
            template_name = os.path.dirname(manifest_path.resolve().absolute().relative_to(self.base_path))
            # add to the index
            self.templates[template_name] = Template(manifest=manifest, path=manifest_path.parent)

    def get_templates_for_strike(self, strike_name: str, strike_type: str) -> dict[str, Template]:
        """Return a dictionary of templates that match the given strike."""

        return {
            name: template
            for name, template in self.templates.items()
            if template.manifest.matches_strike(strike_name, strike_type)
        }

    def install_template_pack(self, source: pathlib.Path, pack_name: str | None = None) -> None:
        """Install a template pack given its source directory."""

        pack_name = pack_name or source.name
        destination = self.base_path / pack_name
        if destination.exists():
            if Prompt.ask(f":axe: Overwrite {destination}?", choices=["y", "n"], default="n") == "n":
                raise Exception(f"Template pack '{pack_name}' already exists")
            else:
                shutil.rmtree(destination)

        print(f":arrow_double_down: Installing template pack '{pack_name}' to {destination} ...")

        shutil.copytree(source, destination)

    def install_from_dir(self, source: pathlib.Path, dest: pathlib.Path, context: dict[str, t.Any]) -> None:
        """Install a template given its name into a destination directory."""

        if not source.exists():
            raise Exception(f"Template directory '{source}' does not exist")

        elif not source.is_dir():
            raise Exception(f"Path '{source}' is not a directory")

        # check for Dockerfile in the directory
        elif not (source / "Dockerfile").exists() and not (source / "Dockerfile.j2").exists():
            raise Exception(f"Template directory {source} does not contain a Dockerfile")

        env = Environment(loader=FileSystemLoader(source))

        # iterate over all items in the source directory
        for src_item in source.glob("**/*"):
            # do not copy the manifest itself
            if src_item.name == TEMPLATE_MANIFEST_FILE:
                continue

            # get the relative path of the item
            src_item_path = str(src_item.relative_to(source))
            # get the destination path
            dest_item = dest / src_item_path

            # if the destination item is not the root directory and it exists,
            # ask the user if they want to overwrite it
            if dest_item != dest and dest_item.exists():
                if Prompt.ask(f":axe: Overwrite {dest_item}?", choices=["y", "n"], default="n") == "n":
                    continue

            # if the source item is a file
            if src_item.is_file():
                # if the file has a .j2 extension, render it using Jinja2
                if src_item.name.endswith(".j2"):
                    # we can read as text
                    content = src_item.read_text()
                    j2_template = env.get_template(src_item_path)
                    content = j2_template.render(context)
                    dest_item = dest / src_item_path.removesuffix(".j2")
                    dest_item.write_text(content)
                else:
                    # otherwise, copy the file as is
                    dest_item.write_bytes(src_item.read_bytes())

            # if the source item is a directory, create it in the destination
            elif src_item.is_dir():
                dest_item.mkdir(exist_ok=True)

    def install(self, template_name: str, dest: pathlib.Path, context: dict[str, t.Any]) -> None:
        """Install a template given its name into a destination directory."""

        if template_name not in self.templates:
            raise Exception(f"Template '{template_name}' not found")

        self.install_from_dir(self.templates[template_name].path, dest, context)
