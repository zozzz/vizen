from typing import Optional, Callable, List, Tuple, Awaitable, Any, Coroutine
from http import HTTPStatus

from yapic.di import Injector

from .headers import Headers
from .event import Event

__all__ = "VizenError", "HTTPError", "HTTPRedirect"


class VizenError(Exception):
    pass


class HTTPError(VizenError):
    code: int
    content: bytes
    headers: Headers

    def __init__(self, code: int, message: bytes = None, content: bytes = None):
        if message is None:
            status = HTTPStatus(code)
            message = status.phrase.encode("ascii")

            if content is None:
                content = status.description.encode("ascii")

        super().__init__(message, code)
        self.code = code
        self.content = content or b""
        self.headers = Headers()


class HTTPRedirect(HTTPError):
    def __init__(self, url: bytes, code: int = HTTPStatus.FOUND):
        super().__init__(code)
        self.headers[b"location"] = url
        self.content = b""


OnErrorHandler = Callable[..., Awaitable[Any]]
_SERVER_ERROR: List[Tuple[type, OnErrorHandler]] = []


async def handle_error(injector: Injector, error: Exception) -> bool:
    try:
        exc_injector = injector.descend()

        event = Event()
        exc_injector[Event] = event
        exc_injector[Exception] = error

        for hexc, hfn in _SERVER_ERROR:
            if isinstance(error, hexc):
                if not event.is_prevented:
                    await hfn(exc_injector)
                else:
                    break

        if event.is_prevented:
            return True
    except Exception:
        # TODO: internal server error
        raise
    else:
        raise error

    return False
