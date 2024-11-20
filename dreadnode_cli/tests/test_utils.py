from datetime import datetime, timedelta

from dreadnode_cli.utils import parse_jwt_token_expiration, time_to


def test_time_to() -> None:
    now = datetime.now()

    # Test days
    future = now + timedelta(days=2, hours=3, minutes=15)
    assert time_to(future) == "2d, 3hr, 14m"  # not full 15

    # Test hours
    future = now + timedelta(hours=3, minutes=15)
    assert time_to(future) == "3hr, 14m"  # not full 15

    # Test minutes
    future = now + timedelta(minutes=15)
    assert time_to(future) == "14m"  # not full 15

    # Test just now
    future = now + timedelta(seconds=30)
    assert time_to(future) == "Just now"


def test_parse_jwt_token_expiration() -> None:
    # Test token with expiration
    token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3MDg2NTYwMDB9.mock_signature"
    exp_date = parse_jwt_token_expiration(token)
    assert isinstance(exp_date, datetime)
    assert exp_date == datetime.fromtimestamp(1708656000)
