from yapic.di import Injector, SCOPED_SINGLETON

from .server import Server  # noqa
from .loop import Loop  # noqa
from .protocol import (
    ProtocolFactory,
    ProtocolSelector,
    HTTP1Protocol,
    HTTP2Protocol,
    WebsocketProtocol,
    Request,
    Response,
    Output,
)  # noqa
from .error import (HTTPError, HTTPRedirect)  # noqa
from .json import Json
from .event import Event
from .host import Host
from .cors import CORS, CORS_ORIGINS  # noqa


@Server.on_init
def init_server(injector: Injector):
    injector.provide(ProtocolFactory)
    injector.provide(ProtocolSelector)
    injector.provide(HTTP1Protocol)
    injector.provide(HTTP2Protocol)
    injector.provide(WebsocketProtocol)
    injector.provide(Request)
    injector.provide(Response)
    injector.provide(Output)
    injector.provide(Host, Host.determine, SCOPED_SINGLETON)
    injector[Json] = Json()
    injector.provide(CORS)
    injector[CORS_ORIGINS] = []


@Server.on_erorr(HTTPError)
async def handle_http_error(event: Event, response: Response = None, *, error: HTTPError):
    if response is None:
        return

    response.headers.update(error.headers)
    await response.send(error.content, code=error.code)
    event.prevent_default()
