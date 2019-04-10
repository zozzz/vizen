import sys
from os import path

VIZEN_DIR = path.join(path.dirname(path.realpath(__file__)), "..", "src")

if path.isdir(VIZEN_DIR):
    sys.path.insert(0, VIZEN_DIR)

from vizen import Server  # noqa


@Server.get("/")
async def index():
    # await response.send(b"DATA")
    pass


if __name__ == "__main__":
    Server.start("127.0.0.1", 8080)
