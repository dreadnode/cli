import pytest

import dreadnode_cli.api as api
from dreadnode_cli.tests.test_lib import create_jwt_test_token


def test_invalid_token() -> None:
    with pytest.raises(ValueError):
        api.Token("invalid_token")


def test_expired_token() -> None:
    token = api.Token(create_jwt_test_token(0))

    assert token.is_expired() is True
    assert token.is_close_to_expiry() is True
    assert token.ttl() <= 0


def test_close_to_expiry_token() -> None:
    token = api.Token(create_jwt_test_token(30))

    assert token.is_expired() is False
    assert token.is_close_to_expiry() is True
    assert token.ttl() > 0
