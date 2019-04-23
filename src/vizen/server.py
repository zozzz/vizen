import socket
import asyncio
import signal
from enum import Enum
from typing import List, Callable, Optional, Union, Awaitable, Any
from yapic.di import Injector, Inject, Injectable, SINGLETON, KwOnly, NoKwOnly

from .ssl import SSLConfig
from .protocol import ProtocolFactory, SOCK_LISTEN
from .router import Router
from .error import OnErrorHandler, _SERVER_ERROR, handle_error
from .restarter import Restarter

injector = Injector()
injector.provide(Router, Router, SINGLETON)

OnInitHandler = Callable[[Injector], None]
OnStartHandler = Callable[..., Awaitable[Any]]

_SERVER_INIT: List[OnInitHandler] = []
_SERVER_START: List[OnStartHandler] = []


class Shutdown(Enum):
    NONE = 0
    GRACEFULLY = 1
    IMMEDIATELY = 2


class Server:
    __slots__ = ("injector", "loop", "ssl", "_shutdown")

    loop: Inject["Loop"]
    ssl: Optional[SSLConfig]

    @classmethod
    def on_init(cls, fn: OnInitHandler) -> None:
        """ Listen application on_init

        example::

            @Server.on_init
            def init_di(injector: Injector) -> None:
                injector.provide(Something)

        """
        _SERVER_INIT.append(Injectable(fn))

    @classmethod
    def on_erorr(cls, error: type) -> Callable[[OnErrorHandler], OnErrorHandler]:
        """ Listen errors

        example::

            TODO: @Server.on_erorr(HTTPError[300:400])

            @Server.on_erorr(HTTPError)
            def handle_redirect(event: Event, *, error: HTTPError) -> None:
                if 300 <= error.code < 400:
                    event.prevent_default()
                    # ...
        """

        def get_error(exc: Exception, *, name):
            if name == "error":
                return exc
            else:
                raise NoKwOnly()

        def decorator(fn: OnErrorHandler) -> OnErrorHandler:
            handler = Injectable(fn, provide=[KwOnly(get_error)])
            _SERVER_ERROR.insert(0, (error, handler))
            return fn

        return decorator

    @classmethod
    def on_start(cls, fn: OnStartHandler) -> OnStartHandler:
        """ Call this function when server starts

        example::

            @Server.on_start
            def handle_start() -> None:
                pass
        """

        _SERVER_START.append(Injectable(fn))

        return fn

    @classmethod
    def on_url(cls, url: str, *methods: Union[str, bytes]):
        return injector[Router].on(url, *methods)

    @classmethod
    def on_get(cls, url: str):
        return injector[Router].get(url)

    @classmethod
    def on_head(cls, url: str):
        return injector[Router].head(url)

    @classmethod
    def on_post(cls, url: str):
        return injector[Router].post(url)

    @classmethod
    def on_delete(cls, url: str):
        return injector[Router].delete(url)

    @classmethod
    def on_connect(cls, url: str):
        return injector[Router].connect(url)

    @classmethod
    def on_options(cls, url: str):
        return injector[Router].options(url)

    @classmethod
    def on_trace(cls, url: str):
        return injector[Router].trace(url)

    @classmethod
    def on_patch(cls, url: str):
        return injector[Router].patch(url)

    @classmethod
    def start(cls, ip: str, port: int):
        for init in _SERVER_INIT:
            init(injector)

        server = injector[Server] = injector[Server]
        server.run(ip, port)

    def __init__(self, ssl: SSLConfig = None):
        self.ssl = ssl
        self._shutdown = Shutdown.NONE

        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        # signal.signal(signal.SIGKILL, self.exit_immediately)

    def run(self, ip: str, port: int):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((ip, port))

        self.loop.run_until_complete(self.__run(sock))

    async def __run(self, sock: socket.SocketType):
        await self.serve_from_sock(sock)
        await self.run_forever()

    async def serve_from_fd(self, fd: int):
        return self.serve_from_sock(socket.fromfd(fd, socket.AF_INET, socket.SOCK_STREAM))

    async def serve_from_sock(self, sock: socket.SocketType):
        server_injector = injector.descend()
        server_injector[SOCK_LISTEN] = sock
        # https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.create_server
        try:
            await self.loop.create_server(server_injector[ProtocolFactory], sock=sock)
        except Exception as err:
            handled = await handle_error(server_injector, err)
            if not handled:
                raise

        for handler in _SERVER_START:
            await handler(server_injector)

    async def run_forever(self):
        sleep = asyncio.sleep
        restarter = injector[Restarter]

        while self._shutdown is Shutdown.NONE:
            await sleep(0.1, loop=self.loop)

            if restarter.restart_required():
                self._shutdown = Shutdown.GRACEFULLY

        restarter.stop()

        if self._shutdown is Shutdown.GRACEFULLY:
            pass

    def exit_gracefully(self, signal: signal.Signals, frame: Any) -> None:
        print("exit_gracefully...")
        self._shutdown = Shutdown.GRACEFULLY

    def exit_immediately(self, signal: signal.Signals, frame: Any) -> None:
        print("exit_immediately...")
        self._shutdown = Shutdown.IMMEDIATELY


injector.provide(Server)

from .loop import Loop  # noqa
