from __future__ import annotations

import ipaddress
import socket


REMOTE_DISABLED_ERROR = (
    "Remote access is disabled for this bridge. Only localhost and this machine's "
    "local Windows or WSL addresses are allowed. Edit ida_pro_skill_plugin.py and "
    "set REMOTE_ACCESS = True to allow external clients."
)


def access_mode(remote_access: bool) -> str:
    return "remote-enabled" if remote_access else "local-only"


def advertised_ipv4_hosts() -> list[str]:
    result = ["127.0.0.1"]
    try:
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            udp.connect(("8.8.8.8", 80))
            candidate = udp.getsockname()[0]
            if _valid_ipv4(candidate) and candidate not in result:
                result.append(candidate)
        finally:
            udp.close()
    except OSError:
        pass

    try:
        for entry in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET, socket.SOCK_STREAM):
            candidate = entry[4][0]
            if _valid_ipv4(candidate) and candidate not in result:
                result.append(candidate)
    except OSError:
        pass
    return result


def is_client_allowed(
    client_ip: str,
    *,
    remote_access: bool,
    advertised_hosts: list[str] | None = None,
) -> bool:
    if remote_access:
        return True

    try:
        parsed = ipaddress.ip_address(client_ip)
    except ValueError:
        return False

    if parsed.is_loopback:
        return True

    allowed_hosts = set(advertised_hosts or advertised_ipv4_hosts())
    return client_ip in allowed_hosts


def _valid_ipv4(candidate: str) -> bool:
    try:
        return isinstance(ipaddress.ip_address(candidate), ipaddress.IPv4Address)
    except ValueError:
        return False
