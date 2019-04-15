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
    <title>Vizen - Json POST</title>
    <script src="https://code.jquery.com/jquery-2.2.4.min.js" integrity="sha256-BbhdlvQf/xTY9gja0Dq3HiwQF8LaCRTXxZKRutelT44=" crossorigin="anonymous"></script>
    <script>
        function send() {
            $.ajax('/rpc', {
                type: "POST",
                cache: false,
                data: JSON.stringify({'method': 'call_xyz'}),
                contentType : "application/json",
                dataType: "json",
                complete: function(r){ $("#r").val(JSON.stringify(r)) }
            });
        }
    </script>
</head>
<body>
    <button onclick="send()">SEND</button>
    <textarea id="r"></textarea>
</body>
</html>""")


@Server.on_post("/rpc")
async def upload(req: Request, resp: Response):
    data = await req.json()
    data["xyz_result"] = 42
    await resp.json(data)

    # full body parsed


if __name__ == "__main__":
    Server.start("127.0.0.1", 8080)
