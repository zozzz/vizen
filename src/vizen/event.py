from typing import Callable, Any, List
from yapic.di import Injectable, Injector, Inject


class Event:
    __slots__ = ("is_prevented", )

    is_prevented: bool

    def __init__(self):
        self.is_prevented = False

    def prevent_default(self):
        self.is_prevented = True


class EventEmitter:
    __slots__ = ("handlers", "injector")

    handlers: List[Injectable]
    injector: Inject[Injector]

    def __init__(self):
        self.handlers = []

    def on(self, handler: Callable[[Any], None]) -> Callable[[], None]:
        injectable = self.injector.injectable(handler)

        self.handlers.insert(0, injectable)

        def off():
            self.handlers.remove(injectable)

        return off

    def emit(self, event: Event) -> bool:
        injector = self.injector.descend()
        injector[Event] = event
        injector[type(event)] = event

        for item in self.handlers:
            if not event.is_prevented:
                item(injector)
            else:
                break

        return event.is_prevented
