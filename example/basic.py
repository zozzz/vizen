import sys
from os import path

VIZEN_DIR = path.join(path.dirname(path.realpath(__file__)), "..", "src")

if path.isdir(VIZEN_DIR):
    sys.path.insert(0, VIZEN_DIR)

from vizen import Server, Request, Response, Host  # noqa


@Server.on_url("/")
async def index(request: Request, resp: Response, host: Host):
    print("ez beszaras", request)
    await resp.send(b"Hello World from: " + host.value.encode("utf-8"))


if __name__ == "__main__":
    Server.start("127.0.0.1", 8080)
