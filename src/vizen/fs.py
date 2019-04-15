from pathlib import Path
from asyncio import AbstractEventLoop
from aiofile import AIOFile
from tempfile import gettempdir
from uuid import uuid4

from yapic.di import Inject


class File(AIOFile):
    pass


class TempFile(File):
    pass


class Fs:
    loop: Inject[AbstractEventLoop]

    def open(self, filename: str, mode: str = "r", access_mode: int = 0o644, encoding: str = "utf-8") -> File:
        return File(filename, mode, access_mode, self.loop, encoding)

    @property
    def temp_path(self) -> Path:
        return Path(gettempdir())

    def temp_file(self, prefix: str = None, encoding: str = "utf-8") -> TempFile:
        if prefix is None:
            prefix = ""
        else:
            prefix += "-"

        filename = self.temp_path / f"{prefix}{str(uuid4())}"
        return TempFile(filename, "rw", 0o660, encoding)
