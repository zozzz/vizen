from typing import Callable, Any


class App:
    @staticmethod
    def on_init(fn: Callable[[Any], None]) -> None:
        """ Listen application on_init

        example::

            @App.on_init
            def init_di(injector: Injector) -> None:
                injector.provide(Something)

        """
