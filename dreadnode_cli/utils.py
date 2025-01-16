import functools
import sys
import typing as t

from rich import print

from dreadnode_cli.dreadnode.defaults import DEBUG

P = t.ParamSpec("P")
R = t.TypeVar("R")


def pretty_cli(func: t.Callable[P, R]) -> t.Callable[P, R]:
    """Decorator to pad function output and catch/pretty print any exceptions."""

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            print()
            return func(*args, **kwargs)
        except Exception as e:
            if DEBUG:
                raise

            print(f":exclamation: {e}")
            sys.exit(1)

    return wrapper
