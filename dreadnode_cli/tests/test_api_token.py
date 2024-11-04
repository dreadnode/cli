import base64
import json
from datetime import datetime, timedelta

import pytest

import dreadnode_cli.api as api


async def test_invalid_token() -> None:
    with pytest.raises(ValueError):
        api.Token("invalid_token")


async def test_expired_token() -> None:
    token = api.Token("eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3MDg2NTYwMDB9.mock_signature")

    assert token.is_expired() is True
    assert token.is_close_to_expiry() is True
    assert token.ttl() <= 0


async def test_close_to_expiry_token() -> None:
    # Create token that expires in 5 minutes from now
    future_exp = int((datetime.now() + timedelta(seconds=30)).timestamp())
    obj = {"exp": future_exp}
    token = api.Token(
        f"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.{base64.urlsafe_b64encode(json.dumps(obj).encode()).decode()}.mock_signature"
    )

    assert token.is_expired() is False
    assert token.is_close_to_expiry() is True
    assert token.ttl() > 0
