import os
import pathlib

MAIN_PROFILE_NAME = "main"
PLATFORM_BASE_URL = "https://crucible.dreadnode.io"

USER_CONFIG_PATH = pathlib.Path(
    os.getenv("DREADNODE_USER_CONFIG_FILE") or pathlib.Path.home() / ".dreadnode" / "config.json"
)
