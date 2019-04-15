import sys
from os import path

VIZEN_DIR = path.join(path.dirname(path.realpath(__file__)), "..", "src")

if path.isdir(VIZEN_DIR):
    sys.path.insert(0, VIZEN_DIR)

from vizen import Server, Request, Response  # noqa


@Server.on_url("/")
async def index(resp: Response):
    await resp.html("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Vizen - File Upload</title>
</head>
<body>
    <form action="/upload" method="post" enctype="multipart/form-data">
        File 1: <input type="file" name="file1"><br>
        File 2: <input type="file" name="file2"><br>
        File 3: <input type="file" name="file3"><br>
        <input type="submit" value="Upload File" name="submit">
    </form>
</body>
</html>""")


@Server.on_post("/upload")
async def upload(req: Request, resp: Response):
    async for name, file in req.files:
        print(name, file)

    await req.on_body.wait()

    # full body parsed


if __name__ == "__main__":
    Server.start("127.0.0.1", 8080)
