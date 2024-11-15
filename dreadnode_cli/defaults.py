import os
import pathlib

#
# Environment
#

# enable debugging
DEBUG = bool(os.getenv("DREADNODE_DEBUG")) or False

# default platform domain
PLATFORM_BASE_DOMAIN = "dreadnode.io"
# default server URL
PLATFORM_BASE_URL = os.getenv("DREADNODE_SERVER", f"https://crucible.{PLATFORM_BASE_DOMAIN}")
# default docker registry subdomain
DOCKER_REGISTRY_SUBDOMAIN = "registry"
# default docker registry local port
DOCKER_REGISTRY_LOCAL_PORT = 5005
# default docker registry image tag
DOCKER_REGISTRY_IMAGE_TAG = "registry"

# path to the user configuration file
USER_CONFIG_PATH = pathlib.Path(
    # allow overriding the user config file via env variable
    os.getenv("DREADNODE_USER_CONFIG_FILE") or pathlib.Path.home() / ".dreadnode" / "config"
)

#
# Constants
#

# name of the default server profile
DEFAULT_PROFILE_NAME = "main"
# default poll interval for the authentication flow
DEFAULT_POLL_INTERVAL = 5
# default maximum poll time for the authentication flow
DEFAULT_MAX_POLL_TIME = 300
# default maximum token TTL in seconds
DEFAULT_TOKEN_MAX_TTL = 60
