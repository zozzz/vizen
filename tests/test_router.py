import pytest
from decimal import Decimal
from uuid import UUID

from yapic.di import Injector

from vizen.router import Router

url_params = [
    ("{var:int}", "/42", int, 42),
    ("{var:int}", "42", int, 42),
    ("/{var:int}", "/42", int, 42),
    ("/{var:int}", "42", int, 42),
    ("/{var:str}", "todo", str, "todo"),
    ("/{var:float}", ".1", float, .1),
    ("/{var:float}", "0.1", float, 0.1),
    ("/{var:float}", "1e2", float, 1e2),
    ("/{var:decimal}", ".1", Decimal, Decimal(".1")),
    ("/{var:decimal}", "0.1", Decimal, Decimal("0.1")),
    ("/{var:decimal}", "1e2", Decimal, Decimal("1e2")),
    ("/{var:uuid}", "16fd2706-8baf-433b-82eb-8c7fada847da", UUID, UUID("16fd2706-8baf-433b-82eb-8c7fada847da")),
]


@pytest.mark.parametrize("pattern,url,type,value", url_params, ids=[f"{x[1]}--{x[0]}" for x in url_params])
def test_params(pattern, url, type, value):
    injector = Injector()
    r = Router()

    @r.on(pattern)
    def action():
        return "OK"

    handler, params = r.find(url, b"GET")

    assert handler(injector) == "OK"
    assert isinstance(params["var"], type)
    assert params["var"] == value


def test_multi_params():
    injector = Injector()
    r = Router()

    @r.on("/{name: str}-{id :int}/page-{page : int}")
    def action():
        return "OK"

    handler, params = r.find("/asdfÁéőwrwerwesdasx-3434543/page-1", b"GET")

    assert handler(injector) == "OK"
    assert isinstance(params["name"], str)
    assert isinstance(params["id"], int)
    assert isinstance(params["page"], int)
    assert params["name"] == "asdfÁéőwrwerwesdasx"
    assert params["id"] == 3434543
    assert params["page"] == 1


def test_regex_params():
    injector = Injector()
    r = Router()

    @r.on("{re:A\\d+A}")
    def action():
        return "OK"

    handler, params = r.find("/A42A", b"GET")

    assert handler(injector) == "OK"
    assert isinstance(params["re"], str)
    assert params["re"] == "A42A"


def test_multiple_dynamic():
    injector = Injector()
    r = Router()

    @r.on("/test/{string:str}")
    def action_string():
        return "string"

    @r.on("/test/{string:str}-{id:int}")
    def action_string_id():
        return "string-id"

    @r.on("/test/{number:int}")
    def action_number():
        return "number"

    @r.on("/test/{number:int}-{id:int}")
    def action_number_id():
        return "number-id"

    @r.on("/test/exact")
    def action_exact():
        return "exact"

    handler, params = r.find("/test/42", b"GET")
    assert handler(injector) == "number"
    assert params["number"] == 42

    handler, params = r.find("/test/something", b"GET")
    assert handler(injector) == "string"
    assert params["string"] == "something"

    handler, params = r.find("/test/exact", b"GET")
    assert handler(injector) == "exact"
    assert len(params) == 0

    handler, params = r.find("/test/exact-42", b"GET")
    assert handler(injector) == "string-id"
    assert params["string"] == "exact"
    assert params["id"] == 42

    handler, params = r.find("/test/24-42", b"GET")
    assert handler(injector) == "number-id"
    assert params["number"] == 24
    assert params["id"] == 42


def test_params_wo_type():
    injector = Injector()
    r = Router()

    @r.on("/test/{any}")
    def action_any():
        return "any"

    @r.on("/test/{number:int}")
    def action_number():
        return "number"

    @r.on("/test/exact")
    def action_exact():
        return "exact"

    handler, params = r.find("/test/42", b"GET")
    assert handler(injector) == "number"
    assert params["number"] == 42

    handler, params = r.find("/test/something", b"GET")
    assert handler(injector) == "any"
    assert params["any"] == "something"

    handler, params = r.find("/test/exact", b"GET")
    assert handler(injector) == "exact"
    assert len(params) == 0
