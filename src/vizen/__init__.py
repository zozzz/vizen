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
    Cookie,
)  # noqa
from .error import (HTTPError, HTTPRedirect)  # noqa
from .json import Json
from .event import Event
from .host import Host
from .cors import CORS  # noqa
from .session import Session, FileSession  # noqa
from .restarter import Restarter


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
    injector.provide(Cookie)
    injector.provide(Restarter)

    injector[Json] = Json()
    injector.provide(CORS)
    injector[CORS.ALLOWED_ORIGINS] = []

    injector.provide(FileSession)
    injector.provide(Session, Session[FileSession], SCOPED_SINGLETON)
    injector[Session.COOKIE_NAME] = "SID"


@Server.on_erorr(HTTPError)
async def handle_http_error(event: Event, response: Response = None, *, error: HTTPError):
    if response is None:
        return

    response.headers.update(error.headers)
    await response.send(error.content, code=error.code)
    event.prevent_default()
