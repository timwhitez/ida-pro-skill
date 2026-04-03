from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from .common import ensure_dir, read_json, state_path, write_json


def load_state(app_home: Path) -> dict[str, Any]:
    return read_json(
        state_path(app_home),
        {
            "selected_instance": None,
            "skill_targets": {},
            "plugin_files": [],
            "plugin_dir": None,
            "python_executable": None,
            "app_bundle_dir": None,
            "installed_at": None,
        },
    )


def save_state(app_home: Path, payload: dict[str, Any]) -> None:
    ensure_dir(app_home)
    write_json(state_path(app_home), payload)


def remove_tree(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    elif path.exists():
        path.unlink()
