from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from yapic.di import Token, Inject


class Restarter(FileSystemEventHandler):
    __slots__ = ("_observer", "_changed")

    PATHS = Token("RESTARTER_PATHS")

    def __init__(self, paths: PATHS = None):
        self._changed = False
        self._observer = PollingObserver()

        if paths:
            for p in paths:  # type: ignore
                print("watching for changes %r" % p)
                self._observer.schedule(self, str(p), recursive=True)
            self._observer.start()

    def restart_required(self) -> bool:
        changed = self._changed
        self._changed = False
        return changed

    def on_any_event(self, event: FileSystemEvent):
        self._changed = self._changed or (not event.is_directory and event.src_path.endswith(".py"))

    def stop(self):
        self._observer.unschedule_all()
