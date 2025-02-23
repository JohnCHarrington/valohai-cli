import platform

import click
import requests
from requests.auth import AuthBase
from urllib.parse import urljoin, urlparse

from valohai_cli import __version__ as VERSION
from valohai_cli.exceptions import APIError, APINotFoundError, CLIException, NotLoggedIn
from valohai_cli.settings import settings
from valohai_cli.utils import force_text
from requests.models import PreparedRequest, Request, Response
from typing import Any, Optional, Tuple


class TokenAuth(AuthBase):

    def __init__(self, netloc: str, token: Optional[str]) -> None:
        super().__init__()
        self.netloc = netloc
        self.token = token

    def __call__(self, request: PreparedRequest) -> PreparedRequest:
        if not request.headers.get('Authorization') and urlparse(request.url).netloc == self.netloc:
            if self.token:
                request.headers['Authorization'] = f'Token {self.token}'
        return request


class APISession(requests.Session):

    def __init__(self, base_url: str, token: Optional[str]=None) -> None:
        super().__init__()
        self.base_url = base_url
        self.base_netloc = urlparse(self.base_url).netloc
        self.auth = TokenAuth(self.base_netloc, token)
        self.headers['Accept'] = 'application/json'
        self.headers['User-Agent'] = 'valohai-cli/{version} on {py_version} ({uname})'.format(
            version=VERSION,
            uname=';'.join(platform.uname()),
            py_version=f'{platform.python_implementation()} {platform.python_version()}',
        )

    def prepare_request(self, request: Request) -> PreparedRequest:
        url_netloc: str = urlparse(request.url).netloc
        if not url_netloc:
            request.url = urljoin(self.base_url, request.url)
        prepared_request: PreparedRequest = super().prepare_request(request)  # type: ignore[no-untyped-call]
        return prepared_request

    def request(self, method, url, **kwargs) -> Response:  # type: ignore
        api_error_class = kwargs.pop('api_error_class', APIError)
        handle_errors = bool(kwargs.pop('handle_errors', True))
        try:
            resp = super().request(method, url, **kwargs)
        except requests.ConnectionError as ce:
            host = urlparse(ce.request.url).netloc
            if 'Connection refused' in str(ce):
                raise CLIException(
                    f'Unable to connect to {host} (connection refused); try again soon.'
                ) from ce
            raise

        if handle_errors and resp.status_code >= 400:
            cls = (APINotFoundError if resp.status_code == 404 else api_error_class)
            raise cls(resp)
        return resp


def _get_current_api_session() -> APISession:
    """
    Get an API session, either from the Click context cache, or a new one from the config.
    """
    host, token = get_host_and_token()
    ctx = click.get_current_context(silent=True) or None
    cache_key: str = force_text(f'_api_session_{host}_{token}')
    session: Optional[APISession] = (getattr(ctx, cache_key, None) if ctx else None)
    if not session:
        session = APISession(host, token)
        if ctx:
            setattr(ctx, cache_key, session)
    return session


def get_host_and_token() -> Tuple[str, str]:
    host = settings.host
    token = settings.token
    if not (host and token):
        raise NotLoggedIn('You\'re not logged in; try `vh login` first.')
    return (host, token)


def request(method: str, url: str, **kwargs: Any) -> Response:
    """
    Make an authenticated API request.

    See the documentation for `requests.Session.request()`.

    :param method: HTTP Method
    :param url: URL
    :param kwargs: Other kwargs, see `APISession.request()`
    :return: requests.Response
    """
    session = _get_current_api_session()
    if url.startswith(session.base_url):
        url = url[len(session.base_url):]
    return session.request(method, url, **kwargs)
