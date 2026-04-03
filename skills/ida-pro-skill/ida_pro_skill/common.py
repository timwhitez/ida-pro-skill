from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

APP_DIR_NAME = ".ida-pro-skill"
APP_BUNDLE_NAME = "app"
INSTANCE_DIR_NAME = "instances"
STATE_FILE_NAME = "state.json"
SKILL_NAME = "ida-pro-skill"
PLUGIN_ENTRY_FILE = "ida_pro_skill_plugin.py"
PLUGIN_PACKAGE_DIR = "ida_pro_skill_plugin_runtime"
SUPPORTED_TARGETS = ("codex", "claude")


class IdaProSkillError(RuntimeError):
    """Base exception for CLI-facing failures."""


@dataclass(slots=True)
class TargetInstall:
    target: str
    path: Path


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def user_home() -> Path:
    return Path.home()


def default_app_home() -> Path:
    return user_home() / APP_DIR_NAME


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def parse_targets(raw: str | None) -> list[str]:
    if not raw:
        return list(SUPPORTED_TARGETS)
    result: list[str] = []
    for part in raw.split(","):
        item = part.strip().lower()
        if not item:
            continue
        if item in ("claude-code", "claude_code"):
            item = "claude"
        if item not in SUPPORTED_TARGETS:
            raise IdaProSkillError(
                f"Unsupported target '{item}'. Supported targets: {', '.join(SUPPORTED_TARGETS)}"
            )
        if item not in result:
            result.append(item)
    if not result:
        raise IdaProSkillError("No installation targets were provided")
    return result


def package_root() -> Path:
    return Path(__file__).resolve().parent


def bundle_root(app_home: Path) -> Path:
    return app_home / APP_BUNDLE_NAME


def state_path(app_home: Path) -> Path:
    return app_home / STATE_FILE_NAME


def instance_dir(app_home: Path) -> Path:
    return app_home / INSTANCE_DIR_NAME


def is_wsl() -> bool:
    if os.environ.get("WSL_DISTRO_NAME"):
        return True
    return "microsoft" in platform.release().lower()


def windows_path_to_wsl(path: str | None) -> Path | None:
    if not path:
        return None
    raw = path.strip().strip('"')
    if len(raw) < 3 or raw[1] != ":":
        return None
    drive = raw[0].lower()
    rest = raw[2:].replace("\\", "/").lstrip("/")
    return Path("/mnt") / drive / rest


def wsl_windows_home() -> Path | None:
    if not is_wsl():
        return None

    env_candidates = [
        os.environ.get("USERPROFILE"),
        (
            f"{os.environ.get('HOMEDRIVE', '')}{os.environ.get('HOMEPATH', '')}"
            if os.environ.get("HOMEDRIVE") and os.environ.get("HOMEPATH")
            else None
        ),
    ]
    for candidate in env_candidates:
        resolved = windows_path_to_wsl(candidate)
        if resolved is not None:
            return resolved

    try:
        completed = subprocess.run(
            ["cmd.exe", "/C", "echo", "%USERPROFILE%"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    resolved = windows_path_to_wsl(completed.stdout.strip().splitlines()[0] if completed.stdout.strip() else None)
    return resolved


def instance_registry_dirs(app_home: Path) -> list[Path]:
    result = [instance_dir(app_home)]
    if is_wsl():
        windows_home = wsl_windows_home()
        if windows_home is not None:
            result.append(windows_home / APP_DIR_NAME / INSTANCE_DIR_NAME)

    unique: list[Path] = []
    seen: set[str] = set()
    for path in result:
        key = str(path)
        if key not in seen:
            unique.append(path)
            seen.add(key)
    return unique


def stdout_json(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)


def merge_pythonpath(app_bundle_dir: Path) -> str:
    existing = os.environ.get("PYTHONPATH", "")
    parts = [str(app_bundle_dir)]
    if existing:
        parts.append(existing)
    return os.pathsep.join(parts)


def system_name() -> str:
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "darwin"
    return "linux"
