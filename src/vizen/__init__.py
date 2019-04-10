from yapic.di import Injector

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
from .error import *  # noqa


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
