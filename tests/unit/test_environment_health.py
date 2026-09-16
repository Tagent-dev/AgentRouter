"""Guards on the environment health command created by spec task 1.2.

Requirement 3.4 asks for a documented command reporting PostgreSQL and Redis as
reachable. These tests cover both directions, because a health check that only
ever reports success is worse than none:

  * against a stub speaking the PostgreSQL SSLRequest handshake, and a stub
    speaking RESP, both checks report reachable
  * against a closed port, both report unreachable with actionable remediation
    and a non-zero exit status
  * against a listener that answers with something else, the check says the port
    is occupied by the wrong process rather than claiming the service is up
  * a Redis requiring AUTH is reported as an auth problem, not as unreachable
  * `.env` never overrides an exported environment variable
  * the password is never printed

The stubs are single-connection loopback sockets, so no container is needed.
"""

from __future__ import annotations

import socket
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager, suppress
from pathlib import Path

import pytest

from scripts.development import health

ROOT = Path(__file__).resolve().parents[2]

Handler = Callable[[socket.socket], None]


@contextmanager
def _serve_once(handler: Handler) -> Iterator[int]:
    """Bind a loopback port, serve exactly one connection, yield the port."""
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    port = int(listener.getsockname()[1])

    def serve() -> None:
        try:
            conn, _ = listener.accept()
        except OSError:
            return
        with conn, suppress(OSError):
            handler(conn)

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    try:
        yield port
    finally:
        listener.close()
        thread.join(timeout=2)


def _closed_port() -> int:
    """A port that nothing is listening on."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _postgres_stub(reply: bytes) -> Handler:
    def handler(conn: socket.socket) -> None:
        conn.recv(8)
        conn.sendall(reply)

    return handler


def _redis_stub(*, password: str | None = None) -> Handler:
    def handler(conn: socket.socket) -> None:
        while True:
            request = conn.recv(1024)
            if not request:
                return
            if b"AUTH" in request:
                conn.sendall(b"+OK\r\n" if password else b"-ERR Client sent AUTH\r\n")
                continue
            if b"PING" in request:
                conn.sendall(b"-NOAUTH Authentication required.\r\n" if password else b"+PONG\r\n")
                return

    return handler


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin host settings to loopback and drop any inherited values."""
    for name in (
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_DB",
        "REDIS_HOST",
        "REDIS_PORT",
        "REDIS_PASSWORD",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("POSTGRES_HOST", "127.0.0.1")
    monkeypatch.setenv("REDIS_HOST", "127.0.0.1")


@pytest.mark.unit
@pytest.mark.parametrize("reply", [b"S", b"N", b"E"])
def test_postgres_handshake_reply_means_reachable(
    reply: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    with _serve_once(_postgres_stub(reply)) as port:
        monkeypatch.setenv("POSTGRES_PORT", str(port))
        result = health.check_postgres()

    assert result.ok
    assert "reachable" in result.detail
    # The caveat is the honest part: no driver, so no credential verification.
    assert "not verified" in result.caveat


@pytest.mark.unit
def test_postgres_closed_port_is_unreachable_with_remediation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("POSTGRES_PORT", str(_closed_port()))
    result = health.check_postgres()

    assert not result.ok
    assert "cannot connect" in result.detail
    assert any("docker compose" in line for line in result.remedy)


@pytest.mark.unit
def test_postgres_wrong_listener_is_not_reported_as_up(monkeypatch: pytest.MonkeyPatch) -> None:
    with _serve_once(_postgres_stub(b"X")) as port:
        monkeypatch.setenv("POSTGRES_PORT", str(port))
        result = health.check_postgres()

    assert not result.ok
    assert "not PostgreSQL" in result.detail


@pytest.mark.unit
def test_redis_ping_means_reachable(monkeypatch: pytest.MonkeyPatch) -> None:
    with _serve_once(_redis_stub()) as port:
        monkeypatch.setenv("REDIS_PORT", str(port))
        result = health.check_redis()

    assert result.ok
    assert "PONG" in result.detail


@pytest.mark.unit
def test_redis_closed_port_is_unreachable_with_remediation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("REDIS_PORT", str(_closed_port()))
    result = health.check_redis()

    assert not result.ok
    assert "cannot connect" in result.detail
    assert any("docker compose" in line for line in result.remedy)


@pytest.mark.unit
def test_redis_requiring_auth_is_reported_as_an_auth_problem(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with _serve_once(_redis_stub(password="secret")) as port:
        monkeypatch.setenv("REDIS_PORT", str(port))
        result = health.check_redis()

    assert not result.ok
    assert "requires authentication" in result.detail
    assert any("REDIS_PASSWORD" in line for line in result.remedy)


@pytest.mark.unit
def test_redis_wrong_listener_is_not_reported_as_up(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(conn: socket.socket) -> None:
        conn.recv(1024)
        conn.sendall(b"HTTP/1.1 400 Bad Request\r\n")

    with _serve_once(handler) as port:
        monkeypatch.setenv("REDIS_PORT", str(port))
        result = health.check_redis()

    assert not result.ok
    assert "not Redis" in result.detail


@pytest.mark.unit
def test_report_exits_non_zero_and_hides_no_failure(capsys: pytest.CaptureFixture[str]) -> None:
    checks = [
        health.Check(name="PostgreSQL", target="h:1", ok=True, detail="reachable"),
        health.Check(
            name="Redis",
            target="h:2",
            ok=False,
            detail="cannot connect",
            remedy=("start it",),
        ),
    ]

    assert health.report(checks) == 1

    out = capsys.readouterr().out
    assert "[OK  ] PostgreSQL" in out
    assert "[DOWN] Redis" in out
    assert "start it" in out


@pytest.mark.unit
def test_report_exits_zero_when_all_reachable(capsys: pytest.CaptureFixture[str]) -> None:
    checks = [
        health.Check(name="PostgreSQL", target="h:1", ok=True, detail="reachable"),
        health.Check(name="Redis", target="h:2", ok=True, detail="reachable"),
    ]

    assert health.report(checks) == 0
    assert "all dependencies reachable" in capsys.readouterr().out


@pytest.mark.unit
def test_password_is_never_printed(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("REDIS_PASSWORD", "hunter2-should-not-appear")
    with _serve_once(_redis_stub(password="hunter2-should-not-appear")) as port:
        monkeypatch.setenv("REDIS_PORT", str(port))
        monkeypatch.setenv("POSTGRES_PORT", str(_closed_port()))
        assert health.report([health.check_postgres(), health.check_redis()]) == 1

    assert "hunter2-should-not-appear" not in capsys.readouterr().out


@pytest.mark.unit
def test_env_file_does_not_override_the_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# comment\nPOSTGRES_HOST=from-file\nREDIS_PORT=6380\nMALFORMED\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("POSTGRES_HOST", "from-environment")

    health.load_env_file(env_file)

    assert health.setting("POSTGRES_HOST", "localhost") == "from-environment"
    assert health.port_setting("REDIS_PORT", 6379) == 6380


@pytest.mark.unit
def test_port_setting_falls_back_when_unparseable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POSTGRES_PORT", "not-a-port")
    assert health.port_setting("POSTGRES_PORT", 5432) == 5432


@pytest.mark.unit
def test_resp_command_encoding() -> None:
    assert health.resp_command("PING") == b"*1\r\n$4\r\nPING\r\n"
    assert health.resp_command("AUTH", "pw") == b"*2\r\n$4\r\nAUTH\r\n$2\r\npw\r\n"


@pytest.mark.unit
def test_makefile_and_taskfile_expose_the_health_command() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    taskfile = (ROOT / "Taskfile.yml").read_text(encoding="utf-8")

    assert "\nhealth:" in makefile
    assert "python scripts/development/health.py" in makefile
    assert "python scripts/development/health.py" in taskfile
