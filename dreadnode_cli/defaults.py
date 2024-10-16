import os
import pathlib

MAIN_PROFILE_NAME = "main"
PLATFORM_BASE_URL = "https://crucible.dreadnode.io"

USER_CONFIG_PATH = pathlib.Path(
    os.getenv("DREADNODE_USER_CONFIG_FILE") or pathlib.Path.home() / ".dreadnode" / "config.json"
)

DEFAULT_POLL_INTERVAL = 5
DEFAULT_MAX_POLL_TIME = 300

DEFAULT_TOKEN_MAX_TTL = 60
