import re

from click import Command, Context
from typer.core import TyperGroup

# https://github.com/fastapi/typer/issues/132


class AliasGroup(TyperGroup):
    _CMD_SPLIT_P = re.compile(r" ?[,|] ?")

    def get_command(self, ctx: Context, cmd_name: str) -> Command | None:
        cmd_name = self._group_cmd_name(cmd_name)
        return super().get_command(ctx, cmd_name)

    def _group_cmd_name(self, default_name: str) -> str:
        for cmd in self.commands.values():
            name = cmd.name
            if name and default_name in self._CMD_SPLIT_P.split(name):
                return name
        return default_name
