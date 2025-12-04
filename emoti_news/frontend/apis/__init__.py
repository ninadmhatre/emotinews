import os
from functools import cache

from fastapi import HTTPException

from emoti_news.constants import EnvVars


class CommonParams:
    def __init__(self, token: str):
        self.token = token


@cache
def _get_admin_token() -> str:
    return os.getenv(EnvVars.JobAdminToken, "")


def has_token(token: str):
    if token != _get_admin_token():
        print(f"{token=} != {_get_admin_token()}")
        raise HTTPException(status_code=403, detail="Access denied. Invalid API key")
