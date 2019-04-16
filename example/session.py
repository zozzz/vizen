import sys
from os import path
from pathlib import Path
from random import randint
from yapic.di import Injector

SELF_PATH = Path(path.realpath(__file__))
VIZEN_DIR = str(SELF_PATH.parent.parent / "src")

if path.isdir(VIZEN_DIR):
    sys.path.insert(0, VIZEN_DIR)

from vizen import Server, Request, Response, Session, FileSession  # noqa


@Server.on_url("/")
async def index(request: Request, resp: Response, sess: Session):
    print("user_id", await sess.get("user_id", None))
    await sess.set("user_id", randint(1, 200))
    await resp.send(b"OK")


@Server.on_init
def init(injector: Injector):
    injector[FileSession.PATH] = str(SELF_PATH.parent / ".session")


if __name__ == "__main__":
    Server.start("127.0.0.1", 8080)
