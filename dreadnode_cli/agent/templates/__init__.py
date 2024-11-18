import enum
import pathlib

TEMPLATES_DIR = pathlib.Path(__file__).parent.parent / "templates"

# collect available template names
TEMPLATE_NAMES = [
    d.name for d in TEMPLATES_DIR.iterdir() if d.is_dir() and not d.name.startswith(".") and not d.name.startswith("__")
]

# define enum with template names
Template = enum.Enum("Template", {name: name for name in TEMPLATE_NAMES})
