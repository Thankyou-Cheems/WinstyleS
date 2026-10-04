import http.client
import json
import threading
from http.server import ThreadingHTTPServer

import pytest

from start_web_ui import ApiHandler


@pytest.fixture
def server():
    calls = []

    class Handler(ApiHandler):
        def log_message(self, *args):
            pass

        def dispatch_command(self, name, payload):
            calls.append((name, payload))
            return {"fixture": True}

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield httpd.server_port, calls
    httpd.shutdown()
    httpd.server_close()
    thread.join(timeout=2)


def request(port, method, path, body=None, headers=None):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    connection.request(method, path, body=body, headers=headers or {})
    response = connection.getresponse()
    result = response.status, dict(response.getheaders()), response.read()
    connection.close()
    return result


def test_only_same_origin_json_with_ephemeral_session_can_dispatch(server):
    port, calls = server
    status, headers, _ = request(port, "GET", "/")
    assert status == 200
    cookie = headers["Set-Cookie"]
    assert "HttpOnly" in cookie and "SameSite=Strict" in cookie
    assert headers["Cache-Control"] == "no-store"
    trusted = {
        "Cookie": cookie.split(";", 1)[0],
        "Content-Type": "application/json",
        "Origin": f"http://127.0.0.1:{port}",
    }
    status, _, raw = request(port, "POST", "/api/review_import", "{}", trusted)
    assert status == 200 and json.loads(raw)["ok"] is True
    assert calls == [("review_import", {})]
    for modified in [
        {"Cookie": ""},
        {"Cookie": "winstyles_session=bad"},
        {"Origin": "https://evil.example"},
        {"Host": "evil.example"},
        {"Content-Type": "text/plain"},
    ]:
        status, _, raw = request(
            port, "POST", "/api/apply_reviewed_import", "{}", {**trusted, **modified}
        )
        assert status == 403
        assert json.loads(raw)["code"] == "request_forbidden"
    assert len(calls) == 1


def test_untrusted_host_and_status_without_session_are_rejected(server):
    port, calls = server
    assert request(port, "GET", "/", headers={"Host": "evil.example"})[0] == 403
    assert request(port, "GET", "/api/status")[0] == 403
    assert calls == []


def test_invalid_payload_and_size_are_rejected_without_dispatch(server):
    port, calls = server
    _, headers, _ = request(port, "GET", "/")
    trusted = {"Cookie": headers["Set-Cookie"].split(";", 1)[0], "Content-Type": "application/json"}
    for body in ["[]", "malformed"]:
        assert request(port, "POST", "/api/review_import", body, trusted)[0] == 400
    assert (
        request(
            port,
            "POST",
            "/api/review_import",
            "",
            {**trusted, "Content-Length": str(48 * 1024 * 1024 + 1)},
        )[0]
        == 413
    )
    assert (
        request(port, "POST", "/api/review_import", "", {**trusted, "Content-Length": "bad"})[0]
        == 400
    )
    assert calls == []
