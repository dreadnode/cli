import base64
import json
from datetime import datetime, timedelta


def create_jwt_test_token(exp_s: int) -> str:
    future_exp = int((datetime.now() + timedelta(seconds=exp_s)).timestamp())
    obj = {"exp": future_exp}
    return f"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.{base64.urlsafe_b64encode(json.dumps(obj).encode()).decode()}.mock_signature"
