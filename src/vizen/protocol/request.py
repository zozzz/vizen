import asyncio
from enum import Enum
from typing import Any
from urllib.parse import parse_qsl, unquote_to_bytes

from yapic.di import Injector, Inject

from ..headers import Headers
from ..router import Router
from .params import Params, ParamsDict

# from .response import Response


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
    __slots__ = ("injector", "router", "headers", "version", "method", "url", "on_headers", "on_body")

    injector: Inject[Injector]
    router: Inject[Router]

    headers: Headers
    version: str
    method: str
    url: Any

    def __init__(self):
        self.on_headers = asyncio.Event()
        self.on_body = asyncio.Event()

    async def __call__(self):
        await self.on_headers.wait()

        path = unquote_to_bytes(self.url.path).decode("utf-8")
        injectable, params = self.router.find(path, self.method)

        qs = parse_qs(self.url.query)
        self.injector[Params] = Params(params, qs, {})

        await injectable(self.injector)

    async def json(self):
        await self.on_body.wait()


def parse_qs(qs: str) -> ParamsDict:
    query: ParamsDict = {}

    if qs:
        for name, value in parse_qsl(qs, keep_blank_values=True, strict_parsing=True):
            try:
                existing = query[name]
            except KeyError:
                query[name] = value
            else:
                if isinstance(existing, list):
                    existing.append(value)
                else:
                    query[name] = [existing, value]
    return query
