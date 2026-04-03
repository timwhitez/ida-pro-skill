from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    skill_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(skill_root) if not pythonpath else os.pathsep.join([str(skill_root), pythonpath])

    cmd = [sys.executable, "-m", "ida_pro_skill", *sys.argv[1:]]
    completed = subprocess.run(cmd, env=env, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
