# enforces: docs/specs/web-api.md WEB-01, WEB-02, WEB-03, WEB-04

from start_web_ui import SERVER_HOST, ApiHandler
from winstyles import __version__


def test_web_api_envelope_contract() -> None:
    handler = ApiHandler.__new__(ApiHandler)

    assert handler._api_success({"value": 1}) == {
        "ok": True,
        "data": {"value": 1},
        "error": None,
        "code": "ok",
        "message": "OK",
    }

    assert handler._api_error("bad_request", "Bad request", data={"field": "path"}) == {
        "ok": False,
        "data": {"field": "path"},
        "error": "Bad request",
        "code": "bad_request",
        "message": "Bad request",
    }


def test_status_payload_contract() -> None:
    handler = ApiHandler.__new__(ApiHandler)
    payload = handler.status_payload()

    assert SERVER_HOST == "127.0.0.1"
    assert payload["status"] == "ok"
    assert payload["mode"] in {"development", "frozen"}
    assert payload["version"] == __version__
    assert isinstance(payload["frontend_dir"], str)
    assert isinstance(payload["src_dir"], str)
    assert isinstance(payload["os"], str)
    assert isinstance(payload["is_admin"], bool)
