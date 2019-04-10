import asyncio
from yapic.di import Injector, Inject
from enum import Enum

from ..headers import Headers
from .response import Response


class RequestMethod(Enum):
    GET = "GET"
    HEAD = "HEAD"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    CONNECT = "CONNECT"
    OPTIONS = "OPTIONS"
    TRACE = "TRACE"
    PATCH = "PATCH"


class Request:
    __slots__ = ("injector", "headers", "version", "method", "url", "on_headers", "on_body")

    injector: Inject[Injector]
    headers: Headers
    version: str
    method: str
    url: bytes

    def __init__(self):
        self.on_headers = asyncio.Event()
        self.on_body = asyncio.Event()

    # def __init__(self):
    #     self.on_headers = asyncio.Event()
    #     self.on_body = asyncio.Event()
    # async def __call__(self):
    #     print("Request.__call__ 1")
    #     await asyncio.sleep(5)
    #     print("Request.__call__ 2")
    async def __call__(self):
        await self.on_body.wait()

        resp = self.injector[Response]
        await resp.send(b"Hello World")
