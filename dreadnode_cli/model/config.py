from pydantic import BaseModel, field_validator
from rich import print
from ruamel.yaml import YAML

from dreadnode_cli.defaults import USER_MODELS_CONFIG_PATH


class UserModel(BaseModel):
    """
    A user defined inference model.
    """

    name: str | None = None
    provider: str | None = None
    generator_id: str
    api_key: str

    @field_validator("generator_id", mode="after")
    def check_for_api_key_in_generator_id(cls, value: str) -> str:
        """Print a warning if an API key is included in the generator ID."""

        if ",api_key=" in value:
            print(f":heavy_exclamation_mark: API keys should not be included in generator ids: [bold]{value}[/]")
            print()

        return value


class UserModels(BaseModel):
    """User models configuration."""

    models: dict[str, UserModel] = {}

    @classmethod
    def read(cls) -> "UserModels":
        """Read the user models configuration from the file system or return an empty instance."""

        if not USER_MODELS_CONFIG_PATH.exists():
            return cls()

        with USER_MODELS_CONFIG_PATH.open("r") as f:
            return cls.model_validate(YAML().load(f))

    def write(self) -> None:
        """Write the user models configuration to the file system."""

        with USER_MODELS_CONFIG_PATH.open("w") as f:
            YAML().dump(self.model_dump(mode="json", exclude_none=True), f)
