from httptools import HttpRequestParser
from url import URL
# from yapic.di import Inject

from ..headers import Headers
from ..error import handle_error, HTTPError
from .protocol import AbstractProtocol
from .request import Request
from .response import Response


class HTTP1Protocol(AbstractProtocol):
    __slots__ = ("parser", "headers", "request", "response", "url")

    parser: HttpRequestParser
    request: Request
    response: Response
    headers: Headers
    url: URL

    def __init__(self):
        super().__init__()
        self.parser = HttpRequestParser(self)
        self.headers = Headers()
        self.response = self.injector[Response] = self.injector[Response]

    # ---------------- #
    # PROTOCOL METHODS #
    # ---------------- #

    def connection_lost(self, exc):
        # print("HTTP1Protocol.connection_lost")
        pass

    def pause_writing(self):
        print("HTTP1Protocol.pause_writing")

    def resume_writing(self):
        print("HTTP1Protocol.resume_writing")

    def data_received(self, data):
        self.parser.feed_data(data)

    def eof_received(self):
        print("HTTP1Protocol.eof_received")

    # --------------------- #
    # PARSER EVENT HANDLERS #
    # --------------------- #

    def on_url(self, url: bytes) -> None:
        self.url = URL.parse(url)

    def on_header(self, name: bytes, value: bytes) -> None:
        self.headers[name] = value

    def on_headers_complete(self) -> None:
        injector = self.injector.descend()

        request = self.request = injector[Request] = self.injector[Request]
        request.method = self.parser.get_method()
        request.version = self.response.version = self.parser.get_http_version()
        request.url = self.url
        request.headers = self.headers

        task = self.loop.create_task(request())
        task.add_done_callback(self.__finalize_task)
        request.on_headers.set()

    # def on_message_begin(self):
    #     print("on_message_begin")

    def on_body(self):
        print("on_body")

    def on_message_complete(self):
        self.request.on_body.set()

    def on_chunk_header(self):
        print("on_chunk_header")

    def on_chunk_complete(self):
        print("on_chunk_header")

    def __finalize_task(self, task):
        if task.cancelled():
            if not self.response.headers_sent:
                self.loop.create_task(self.response.begin(503))
        else:
            exc = task.exception()
            if exc is not None:
                self.loop.create_task(handle_error(self.injector, exc))
