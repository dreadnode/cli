import pathlib
import webbrowser

from dreadnode_cli.dreadnode import api, defaults
from dreadnode_cli.dreadnode.agent.config import AgentConfig
from dreadnode_cli.dreadnode.agent.templates.manager import Template, TemplateManager
from dreadnode_cli.dreadnode.config import ServerConfig, UserConfig, UserModel, UserModels


class Dreadnode:
    def __init__(
        self,
        config_path: pathlib.Path = defaults.USER_CONFIG_PATH,
        user_models_path: pathlib.Path = defaults.USER_MODELS_CONFIG_PATH,
        verbose: bool = False,
    ):
        """
        Initialize the Dreadnode client.

        :param config_path: Path to the user configuration file.
        :param verbose: Whether to print verbose output.
        """
        self.config_path = config_path
        self.config = UserConfig.read(config_path)
        self.user_models_path = user_models_path
        self.user_models = UserModels.read(user_models_path)
        self.verbose = verbose
        self.template_manager = TemplateManager()

    def _print(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)

    def profile_exists(self, profile: str) -> bool:
        """Check if a profile exists."""
        return profile in self.config.servers

    def set_active_profile(self, profile: str) -> None:
        """Set the active profile."""
        self.config.active = profile
        self.config.write(self.config_path)

    def forget_profile(self, profile: str) -> None:
        """Forget a profile."""
        del self.config.servers[profile]
        self.config.write(self.config_path)

    def login(self, server: str | None = None, profile: str | None = None) -> None:
        """
        Authenticate to the platform.

        :param server: URL of the server to authenticate to.
        :param profile: Profile alias to assign / update.
        """

        # if no server is provided, use the one from the config
        if not server:
            try:
                server = self.config.get_server_config(profile).url
            except Exception:
                # fallback to the default server
                server = defaults.PLATFORM_BASE_URL

        # create client with no auth data
        client = api.Client(base_url=server)

        self._print(":laptop_computer: Requesting device code ...")

        # request user and device codes
        codes = client.get_device_codes()

        # present verification URL to user
        verification_url = client.url_for_user_code(codes.user_code)
        verification_url_base = verification_url.split("?")[0]

        self._print(
            f"""\n\
    Attempting to automatically open the authorization page in your default browser.
    If the browser does not open or you wish to use a different device, open the following URL:

    :link: [bold]{verification_url_base}[/]

    Then enter the code: [bold]{codes.user_code}[/]
    """
        )

        webbrowser.open(verification_url)

        # poll for the access token after user verification
        tokens = client.poll_for_token(codes.device_code)

        client = api.Client(
            server, cookies={"refresh_token": tokens.refresh_token, "access_token": tokens.access_token}
        )
        user = client.get_user()

        UserConfig.read().set_server_config(
            ServerConfig(
                url=server,
                access_token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                email=user.email_address,
                username=user.username,
                api_key=user.api_key.key,
            ),
            profile,
        ).write(self.config_path)

        self._print(f":white_check_mark: Authenticated as {user.email_address} ({user.username})")

    def refresh(self) -> None:
        """
        Refresh the access token.
        """
        server_config = self.config.get_server_config()
        client = api.create_client()
        user = client.get_user()

        server_config.email = user.email_address
        server_config.username = user.username
        server_config.api_key = user.api_key.key

        self.config.set_server_config(server_config).write(self.config_path)

        self._print(
            f":white_check_mark: Refreshed '[bold]{self.config.active}[/bold]' ([magenta]{user.email_address}[/] / [cyan]{user.username}[/])"
        )

    def user_model_exists(self, id: str) -> bool:
        """Check if a user model exists."""
        return id in self.user_models.models

    def add_user_model(self, id: str, generator_id: str, api_key: str, name: str, provider: str | None) -> None:
        """
        Add a user model.

        :param id: Model identifier.
        :param generator_id: Generator identifier.
        :param api_key: API key for the inference provider.
        :param name: Friendly name for the model.
        :param provider: Provider name.
        """
        self.user_models.models[id] = UserModel(
            name=name, provider=provider, generator_id=generator_id, api_key=api_key
        )
        self.user_models.write(self.user_models_path)

    def forget_user_model(self, id: str) -> None:
        """Forget a user model."""
        del self.user_models.models[id]
        self.user_models.write(self.user_models_path)

    def get_strike_by_name(self, name: str) -> api.StrikeResponse:
        self._print(f":coffee: Fetching strike '{name}' ...")

        client = api.create_client()
        try:
            return client.get_strike(name)
        except Exception as e:
            raise Exception(f"Failed to find strike '{name}': {e}") from e

    def get_agent_templates_for_strike(self, strike: api.StrikeResponse) -> dict[str, Template]:
        # get the templates that match the strike
        available = self.template_manager.get_templates_for_strike(strike.name, strike.type)
        # none available
        if not available:
            if not self.template_manager.templates:
                raise Exception(
                    "No templates installed, use [bold]dreadnode agent templates install[/] to install some."
                )
            else:
                raise Exception("No templates found for the given strike.")
        return available

    def is_agent_path(self, path: pathlib.Path) -> bool:
        """Check if an agent exists in a path."""
        try:
            AgentConfig.read(path)
            return True
        except Exception:
            return False

    def create_agent(
        self,
        name: str,
        strike: api.StrikeResponse,
        template: str,
        directory: pathlib.Path = pathlib.Path("."),
    ) -> None:
        """
        Create an agent.
        """
        directory.mkdir(exist_ok=True)
        context = {"project_name": name, "strike": strike}
        if template in self.template_manager.templates:
            self.template_manager.install(template, directory, context)
        else:
            self.template_manager.install_from_dir(pathlib.Path(template), directory, context)

        # Wait to write this until after the template is installed
        AgentConfig(project_name=name, strike=strike).write(directory=directory)
