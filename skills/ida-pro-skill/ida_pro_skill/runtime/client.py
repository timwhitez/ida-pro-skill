from __future__ import annotations

import http.client
import json
import socket
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from ..common import IdaProSkillError, ensure_dir, instance_registry_dirs, is_wsl, read_json
from ..state import load_state, save_state


def list_instances(app_home: Path) -> list[dict[str, Any]]:
    result = _registry_instances(app_home)
    for payload in result:
        host = payload.get("host")
        port = payload.get("port")
        payload["reachable"] = False
        if host and port:
            try:
                health, connected_host = _probe_instance(payload, int(port))
                payload["health"] = health
                payload["reachable"] = True
                payload["connected_host"] = connected_host
            except IdaProSkillError as exc:
                payload["probe_error"] = str(exc)
    return result


def select_instance(app_home: Path, instance_spec: str) -> dict[str, Any]:
    matched = _match_instance(_registry_instances(app_home), instance_spec)
    if matched is None:
        matched = _match_instance(list_instances(app_home), instance_spec)
    if matched is None:
        raise IdaProSkillError(f"Unknown instance '{instance_spec}'")
    state = load_state(app_home)
    state["selected_instance"] = matched.get("instance_id")
    save_state(app_home, state)
    return matched


def current_instance(app_home: Path) -> dict[str, Any]:
    instances = list_instances(app_home)
    selected = [item for item in instances if item.get("selected") and item.get("reachable")]
    if selected:
        return selected[0]
    reachable = [item for item in instances if item.get("reachable")]
    if len(reachable) == 1:
        return reachable[0]
    if not reachable:
        raise IdaProSkillError("No reachable IDA instances were discovered")
    raise IdaProSkillError("Multiple reachable IDA instances were found; select one explicitly")


def call_tool(app_home: Path, name: str, arguments: dict[str, Any] | None, *, instance: str | None) -> Any:
    target = _resolve_tool_target(app_home, instance)
    response, _connected_host = _call_instance(
        target,
        "/tool",
        payload={"name": name, "arguments": arguments or {}},
    )
    if not response.get("ok"):
        raise IdaProSkillError(response.get("error", "Bridge call failed"))
    return response.get("result")


def _registry_instances(app_home: Path) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    selected = load_state(app_home).get("selected_instance")
    seen_paths: set[str] = set()
    for registry in instance_registry_dirs(app_home):
        ensure_dir(registry)
        for path in sorted(registry.glob("*.json")):
            key = str(path)
            if key in seen_paths:
                continue
            seen_paths.add(key)
            payload = read_json(path, {})
            instance_id = payload.get("instance_id")
            payload["registry_path"] = str(path)
            payload["selected"] = instance_id == selected
            result.append(payload)
    return result


def _match_instance(instances: list[dict[str, Any]], instance_spec: str | None) -> dict[str, Any] | None:
    if not instance_spec:
        return None
    for item in instances:
        if item.get("instance_id") == instance_spec:
            return item
        for host in _instance_match_hosts(item):
            if f"{host}:{item.get('port')}" == instance_spec:
                return item
    return None


def _instance_match_hosts(instance: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for host in (
        instance.get("connected_host"),
        instance.get("host"),
        *(instance.get("host_candidates") or []),
    ):
        if host and host not in result:
            result.append(str(host))
    return result


def _resolve_tool_target(app_home: Path, instance_spec: str | None) -> dict[str, Any]:
    registry_instances = _registry_instances(app_home)
    if instance_spec:
        matched = _match_instance(registry_instances, instance_spec)
        if matched is None:
            raise IdaProSkillError(f"Unknown instance '{instance_spec}'")
        return matched

    state = load_state(app_home)
    selected = _match_instance(registry_instances, state.get("selected_instance"))
    if selected is not None:
        return selected
    if len(registry_instances) == 1:
        return registry_instances[0]
    if not registry_instances:
        raise IdaProSkillError("No IDA instances were discovered")
    return current_instance(app_home)


def _probe_instance(instance: dict[str, Any], port: int) -> tuple[dict[str, Any], str]:
    response, host = _call_instance(instance, "/health", payload=None)
    if "ok" in response:
        if not response.get("ok"):
            raise IdaProSkillError(response.get("error", "Bridge health probe failed"))
        return response.get("result") or {}, host
    return response, host


def _call_instance(
    instance: dict[str, Any],
    path: str,
    *,
    payload: dict[str, Any] | None,
) -> tuple[dict[str, Any], str]:
    errors: list[str] = []
    port = int(instance["port"])
    for host in _instance_host_candidates(instance):
        try:
            response = _http_json("POST" if payload is not None else "GET", host, port, path, payload)
            return response, host
        except IdaProSkillError as exc:
            errors.append(str(exc))
    raise IdaProSkillError("; ".join(errors) if errors else "No connection candidates were available")


def _instance_host_candidates(instance: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for candidate in (
        instance.get("connected_host"),
        instance.get("host"),
        *(instance.get("host_candidates") or []),
    ):
        if candidate and candidate not in result:
            result.append(str(candidate))

    if is_wsl() and any(host in ("127.0.0.1", "localhost") for host in result):
        for host in _wsl_windows_host_candidates():
            if host not in result:
                result.append(host)
    return result


def _wsl_windows_host_candidates() -> list[str]:
    result: list[str] = []
    gateway = _gateway_from_proc_net_route()
    if gateway:
        result.append(gateway)

    resolv_conf = Path("/etc/resolv.conf")
    if resolv_conf.exists():
        for line in resolv_conf.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line.startswith("nameserver "):
                continue
            host = line.split(None, 1)[1].strip()
            if host and host not in result:
                result.append(host)

    return result


def _gateway_from_proc_net_route() -> str | None:
    route_file = Path("/proc/net/route")
    if not route_file.exists():
        return None

    for line in route_file.read_text(encoding="utf-8", errors="ignore").splitlines()[1:]:
        fields = line.split()
        if len(fields) < 3 or fields[1] != "00000000":
            continue
        gateway_hex = fields[2]
        try:
            raw = bytes.fromhex(gateway_hex)
        except ValueError:
            return None
        if len(raw) != 4:
            return None
        return socket.inet_ntoa(raw[::-1])
    return None


def _http_json(
    method: str,
    host: str,
    port: int,
    path: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    url = urllib.parse.urlunparse(("http", f"{host}:{port}", path, "", "", ""))
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            body = response.read().decode("utf-8")
    except (urllib.error.URLError, http.client.HTTPException, OSError) as exc:
        raise IdaProSkillError(f"Failed to reach {url}: {exc}") from exc
    try:
        return json.loads(body or "{}")
    except json.JSONDecodeError as exc:
        raise IdaProSkillError(f"Invalid JSON response from {url}: {exc}") from exc
