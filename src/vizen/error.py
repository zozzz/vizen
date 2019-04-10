from typing import Optional
from http import HTTPStatus

from .headers import Headers


__all__ = "VizenError", "HTTPError", "HTTPRedirect"


class VizenError(Exception):
    pass


class HTTPError(VizenError):
    content: Optional[bytes]
    headers: Optional[Headers]

    def __init__(self, code: int, message: bytes = None, content: bytes = None):
        if message is None:
            status = HTTPStatus(code)
            message = status.phrase.encode("ascii")

            if content is None:
                content = status.description.encode("ascii")

        super().__init__(message, code)
        self.content = content


class HTTPRedirect(HTTPError):
    def __init__(self, url: bytes, code: int = HTTPStatus.FOUND):
        super().__init__(code)
        self.headers = Headers()
        self.headers[b"location"] = url
