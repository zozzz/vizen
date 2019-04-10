from asyncio import AbstractEventLoop, new_event_loop, set_event_loop, set_event_loop_policy, get_event_loop
from yapic.di import Injector
from .server import Server

Loop = AbstractEventLoop


@Server.on_init
def init_loop(injector: Injector):
    try:
        import uvloop
    except ImportError:
        loop = new_event_loop()
        set_event_loop(loop)
    else:
        set_event_loop_policy(uvloop.EventLoopPolicy())
        loop = get_event_loop()
    injector[Loop] = loop
