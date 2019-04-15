import re
from asyncio import Protocol, AbstractEventLoop
from yapic.di import Injector, Inject, Token

from .protocol import AbstractProtocol, SOCK_LISTEN, SOCK_TRANSPORT  # noqa
from .http1 import HTTP1Protocol
from .http2 import HTTP2Protocol
from .websocket import WebsocketProtocol  # noqa
from .request import Request  # noqa
from .response import Response  # noqa
from .output import Output
from .cookie import Cookie

HTTP_VERSION = Token("HTTP_VERSION")
HTTP_METHOD = Token("HTTP_METHOD")


class ProtocolFactory(Protocol):
    injector: Inject[Injector]

    def __call__(self):
        injector = self.injector.descend()
        return injector[ProtocolSelector]


_HTTP_VERSION_PROTO = {
    b"1.0": HTTP1Protocol,
    b"1.1": HTTP1Protocol,
    b"2.0": HTTP2Protocol,
}

_RE_HTTP_VERSION = re.compile(rb"^.+HTTP/(.+)\r\n", re.I).match


class ProtocolSelector(Protocol):
    injector: Inject[Injector]
    output: Output

    # ---------------- #
    # PROTOCOL METHODS #
    # ---------------- #

    def connection_made(self, transport):
        self.injector[SOCK_TRANSPORT] = transport
        self.injector[Output] = self.injector[Output]

    def connection_lost(self, exc):
        # print("connection_lost", exc)
        pass

    def pause_writing(self):
        self.output.writable.clear()
        print("pause_writing")

    def resume_writing(self):
        self.output.writable.set()
        print("resume_writing")

    def data_received(self, data):
        version = _RE_HTTP_VERSION(data)
        if version:
            protocol = self.injector[_HTTP_VERSION_PROTO[version[1]]]
            self.connection_lost = protocol.connection_lost
            self.pause_writing = protocol.pause_writing
            self.resume_writing = protocol.resume_writing
            self.data_received = protocol.data_received
            self.eof_received = protocol.eof_received
            protocol.data_received(data)
        else:
            raise RuntimeError()

    def eof_received(self):
        pass

    # --------------------- #
    # PARSER EVENT HANDLERS #
    # --------------------- #

    # def on_url(self, url: bytes) -> None:
    #     self.url = url

    # def on_header(self, name: bytes, value: bytes) -> None:
    #     self.headers[name] = value

    # def on_headers_complete(self) -> None:
    #     version = self.parser.get_http_version()
    #     method = self.parser.get_method()

    #     self.proto = self.injector[_HTTP_VERSION_PROTO[version]]
    #     request = self.proto.create_request()
    #     request.headers = self.headers
    #     request.version = version
    #     request.method = method
    #     request.url = self.url
    #     self.loop.create_task(request())

    # # def on_message_begin(self):
    # #     print("on_message_begin")

    # def on_body(self):
    #     print("on_body")

    # def on_message_complete(self):
    #     print("on_message_complete")

    # def on_chunk_header(self):
    #     print("on_chunk_header")

    # def on_chunk_complete(self):
    #     print("on_chunk_header")
