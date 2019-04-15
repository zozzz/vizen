from httptools import HttpRequestParser, parse_url
from cgi import parse_header
from http.client import parse_headers
from abc import ABC, abstractmethod
from typing import Any, List
from enum import Enum
from tempfile import TemporaryFile
from io import BytesIO
# from yapic.di import Inject

from ..headers import Headers
from ..error import handle_error, HTTPError
from .protocol import AbstractProtocol
from .request import Request
from .response import Response
from .body import BodyParser, FormDataParser, RawBody


class HTTP1Protocol(AbstractProtocol):
    __slots__ = ("parser", "headers", "request", "response", "url", "body_parser")

    parser: HttpRequestParser
    body_parser: BodyParser
    request: Request
    response: Response
    headers: Headers
    url: Any

    def __init__(self):
        super().__init__()
        self.parser = HttpRequestParser(self)
        self.headers = Headers()
        self.response = self.injector[Response] = self.injector[Response]
        self.body_parser = None

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
        self.url = parse_url(url)

    def on_header(self, name: bytes, value: bytes) -> None:
        self.headers[name] = value

    def on_headers_complete(self) -> None:
        injector = self.injector.descend()

        method = self.parser.get_method()
        if method == b"POST":
            if b"content-type" in self.headers:
                ct, params = parse_header(self.headers[b"content-type"].decode("ASCII"))

                if ct == "multipart/form-data":
                    self.body_parser = FormDataParser(params["boundary"].encode("ASCII"))

        if self.body_parser is None:
            self.body_parser = RawBody()

        injector[BodyParser] = self.body_parser

        request = self.request = injector[Request] = injector[Request]
        request.method = method
        request.version = self.response.version = self.parser.get_http_version()
        request.url = self.url
        request.headers = self.headers

        task = self.loop.create_task(request())
        task.add_done_callback(self.__finalize_task)
        request.on_headers.set()

    # def on_message_begin(self):
    #     print("on_message_begin")

    def on_body(self, body: bytes):
        if self.body_parser is not None:
            self.body_parser.feed(body)

    def on_message_complete(self):
        self.body_parser.process()
        self.body_parser = None
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
