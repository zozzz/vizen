import sys
from os import path
from random import randint

VIZEN_DIR = path.join(path.dirname(path.realpath(__file__)), "..", "src")

if path.isdir(VIZEN_DIR):
    sys.path.insert(0, VIZEN_DIR)

from vizen import Server, Request, Response, Session  # noqa


@Server.on_url("/")
async def index(request: Request, resp: Response, sess: Session):
    print("user_id", await sess.get("user_id", None))
    await sess.set("user_id", randint(1, 200))
    await resp.send(b"OK")


if __name__ == "__main__":
    Server.start("127.0.0.1", 8080)
