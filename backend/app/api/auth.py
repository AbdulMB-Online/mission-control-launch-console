import secrets
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials


security = HTTPBasic(auto_error=False)


class DirectorAuthenticationError(Exception):
    pass


def authenticated_director(request: Request, credentials: Annotated[HTTPBasicCredentials | None, Depends(security)]) -> str:
    settings = request.app.state.settings
    username = credentials.username if credentials else ""
    password = credentials.password if credentials else ""
    user_matches = secrets.compare_digest(username.encode("utf-8"), settings.director_username.encode("utf-8"))
    password_matches = secrets.compare_digest(password.encode("utf-8"), settings.director_password.get_secret_value().encode("utf-8"))
    if not (user_matches and password_matches):
        raise DirectorAuthenticationError
    return settings.director_username
