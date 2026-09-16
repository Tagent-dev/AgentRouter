#!/usr/bin/env python3
"""Report whether the local PostgreSQL and Redis are reachable.

Requirement 3.4 asks for a documented health command that reports both backing
services as reachable. That command is:

    make health         (or: python scripts/development/health.py)

Connection settings come from the environment, using the variable names declared
in `.env.example` (POSTGRES_HOST, POSTGRES_PORT, REDIS_HOST, REDIS_PORT,
REDIS_PASSWORD). A `.env` file at the repository root is read when present, and
never overrides a value already exported in the environment.

What is verified, and what is not
---------------------------------
No database driver is used. There is no runtime dependency group in this
repository yet and adding `psycopg` or `redis` to satisfy a health probe would
put a production dependency in the tree ahead of the code that needs it. Both
checks therefore run over a raw TCP socket from the standard library:

  * PostgreSQL: a TCP connect plus the protocol-level SSLRequest handshake. The
    server answers a single byte, 'S' or 'N', only if it speaks the PostgreSQL
    frontend/backend protocol. This proves a PostgreSQL server is listening.
    It does NOT verify credentials, the database name, or that the schema is
    migrated: authenticating requires the full startup and SASL exchange, which
    is a driver's job.

  * Redis: a TCP connect plus a real PING command over RESP. A `+PONG` reply
    proves a Redis server is listening and answering commands. When
    REDIS_PASSWORD is set, AUTH is sent before PING, so a wrong password is
    reported rather than passed over. The password is never printed.

Exit status:
    0   every dependency reachable
    1   at least one dependency unreachable; remediation is printed for each
"""

from __future__ import annotations

import os
import socket
import struct
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / ".env"

CONNECT_TIMEOUT_SECONDS = 3.0

# PostgreSQL SSLRequest: int32 length (8) followed by the request code
# 1234 << 16 | 5679. Documented in the PostgreSQL frontend/backend protocol as
# the message a client may send before the StartupMessage.
POSTGRES_SSL_REQUEST = struct.pack("!ii", 8, 80877103)

COMPOSE_UP = (
    "docker compose -f deployments/docker/docker-compose.yml "
    "-f deployments/docker/docker-compose.dev.yml up -d"
)


@dataclass(frozen=True)
class Check:
    """Outcome of one dependency check."""

    name: str
    target: str
    ok: bool
    detail: str
    remedy: tuple[str, ...] = ()
    caveat: str = ""


def load_env_file(path: Path = ENV_FILE) -> None:
    """Read KEY=VALUE lines from `.env` without overriding the real environment.

    Deliberately minimal: no interpolation, no export keyword, no multi-line
    values. Anything more belongs in packages/configuration (task 5.1), which
    owns real configuration loading.
    """
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip('"').strip("'")


def setting(name: str, default: str) -> str:
    value = os.environ.get(name, "").strip()
    return value or default


def port_setting(name: str, default: int) -> int:
    raw = setting(name, str(default))
    try:
        return int(raw)
    except ValueError:
        return default


def open_socket(host: str, port: int) -> socket.socket:
    """TCP connect with a bounded timeout. Raises OSError on failure."""
    sock = socket.create_connection((host, port), timeout=CONNECT_TIMEOUT_SECONDS)
    sock.settimeout(CONNECT_TIMEOUT_SECONDS)
    return sock


def unreachable(name: str, target: str, exc: OSError, remedy: tuple[str, ...]) -> Check:
    reason = exc.strerror or str(exc) or exc.__class__.__name__
    return Check(
        name=name,
        target=target,
        ok=False,
        detail=f"cannot connect: {reason}",
        remedy=remedy,
    )


def check_postgres() -> Check:
    """TCP reachability plus the PostgreSQL SSLRequest handshake. No auth check."""
    host = setting("POSTGRES_HOST", "localhost")
    port = port_setting("POSTGRES_PORT", 5432)
    target = f"{host}:{port}"
    database = setting("POSTGRES_DB", "agentrouter")
    remedy = (
        f"start it: {COMPOSE_UP}",
        "confirm POSTGRES_HOST and POSTGRES_PORT in .env match the published port",
        "check the container: docker compose -f deployments/docker/docker-compose.yml ps",
    )

    try:
        with open_socket(host, port) as sock:
            sock.sendall(POSTGRES_SSL_REQUEST)
            reply = sock.recv(1)
    except OSError as exc:
        return unreachable("PostgreSQL", target, exc, remedy)

    caveat = (
        f"protocol handshake only; credentials, database {database!r} and "
        "migration state are not verified (no driver installed yet)"
    )
    if reply in (b"S", b"N"):
        tls = "available" if reply == b"S" else "not offered"
        return Check(
            name="PostgreSQL",
            target=target,
            ok=True,
            detail=f"reachable, speaks the PostgreSQL protocol (TLS {tls})",
            caveat=caveat,
        )
    if reply == b"E":
        # An ErrorResponse still proves a PostgreSQL server answered.
        return Check(
            name="PostgreSQL",
            target=target,
            ok=True,
            detail="reachable, PostgreSQL answered the handshake with an error response",
            caveat=caveat,
        )
    return Check(
        name="PostgreSQL",
        target=target,
        ok=False,
        detail=(
            f"port accepts connections but answered {reply!r} to the SSLRequest handshake, "
            "so the listener is not PostgreSQL"
        ),
        remedy=(
            f"another process is bound to {target}; stop it or set POSTGRES_PORT to a free port",
            f"then: {COMPOSE_UP}",
        ),
    )


def resp_command(*parts: str) -> bytes:
    """Encode a Redis command as a RESP array of bulk strings."""
    out = [f"*{len(parts)}\r\n".encode()]
    for part in parts:
        encoded = part.encode()
        out.append(f"${len(encoded)}\r\n".encode() + encoded + b"\r\n")
    return b"".join(out)


def check_redis() -> Check:
    """TCP reachability plus a real PING over RESP, with AUTH when configured."""
    host = setting("REDIS_HOST", "localhost")
    port = port_setting("REDIS_PORT", 6379)
    password = os.environ.get("REDIS_PASSWORD", "")
    target = f"{host}:{port}"
    remedy = (
        f"start it: {COMPOSE_UP}",
        "confirm REDIS_HOST and REDIS_PORT in .env match the published port",
        "check the container: docker compose -f deployments/docker/docker-compose.yml ps",
    )

    try:
        with open_socket(host, port) as sock:
            if password:
                sock.sendall(resp_command("AUTH", password))
                auth_reply = sock.recv(256)
                # A server with no password set rejects AUTH; PING still decides.
                if auth_reply.startswith(b"-") and b"without any password" not in auth_reply:
                    return Check(
                        name="Redis",
                        target=target,
                        ok=False,
                        detail="reachable but AUTH was refused",
                        remedy=(
                            "REDIS_PASSWORD does not match the running server",
                            "clear REDIS_PASSWORD in .env when the local Redis has no password",
                        ),
                    )
            sock.sendall(resp_command("PING"))
            reply = sock.recv(256)
    except OSError as exc:
        return unreachable("Redis", target, exc, remedy)

    if reply.startswith(b"+PONG"):
        scope = "authenticated" if password else "no password configured"
        return Check(
            name="Redis",
            target=target,
            ok=True,
            detail=f"reachable, PING answered PONG ({scope})",
        )
    if reply.startswith(b"-NOAUTH"):
        return Check(
            name="Redis",
            target=target,
            ok=False,
            detail="reachable, but the server requires authentication",
            remedy=("set REDIS_PASSWORD in .env to the password the running Redis expects",),
        )
    return Check(
        name="Redis",
        target=target,
        ok=False,
        detail=(
            f"port accepts connections but answered {reply[:40]!r} to PING, "
            "so the listener is not Redis"
        ),
        remedy=(
            f"another process is bound to {target}; stop it or set REDIS_PORT to a free port",
            f"then: {COMPOSE_UP}",
        ),
    )


def report(checks: Sequence[Check]) -> int:
    """Print each result with remediation and return the process exit status."""
    print("AgentRouter local environment health")
    print("=" * 72)
    for check in checks:
        status = "OK  " if check.ok else "DOWN"
        print(f"  [{status}] {check.name:<11} {check.target:<22} {check.detail}")
        if check.caveat:
            print(f"           note: {check.caveat}")

    failed = [check for check in checks if not check.ok]
    if not failed:
        print("\nall dependencies reachable")
        return 0

    print(f"\n{len(failed)} dependency(ies) unreachable:")
    for check in failed:
        print(f"\n  {check.name} at {check.target}: {check.detail}")
        for line in check.remedy:
            print(f"    - {line}")
    print(
        "\nA local .env is required by the compose file: cp .env.example .env and set "
        "POSTGRES_PASSWORD."
    )
    return 1


def main() -> int:
    load_env_file()
    return report([check_postgres(), check_redis()])


if __name__ == "__main__":
    sys.exit(main())
