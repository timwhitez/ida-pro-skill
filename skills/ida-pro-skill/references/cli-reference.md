# CLI Reference

## Install and diagnostics

- `python3 scripts/run_cli.py doctor`
- `python3 scripts/run_cli.py ida list-instances`
- `python3 scripts/run_cli.py ida current`
- `python3 scripts/run_cli.py ida select --instance 127.0.0.1:39091`

## Short aliases

- `python3 scripts/run_cli.py ida metadata`
- `python3 scripts/run_cli.py ida cursor`
- `python3 scripts/run_cli.py ida selection`
- `python3 scripts/run_cli.py ida tools`
- `python3 scripts/run_cli.py ida segments`
- `python3 scripts/run_cli.py ida entrypoints`
- `python3 scripts/run_cli.py ida functions --limit 20`
- `python3 scripts/run_cli.py ida function main`
- `python3 scripts/run_cli.py ida decompile 0x401000`
- `python3 scripts/run_cli.py ida disassemble 0x401000`
- `python3 scripts/run_cli.py ida strings --query http`
- `python3 scripts/run_cli.py ida imports --query OpenService`
- `python3 scripts/run_cli.py ida import-callers OpenService`
- `python3 scripts/run_cli.py ida string-xrefs uninstall`
- `python3 scripts/run_cli.py ida callers 0x401000`
- `python3 scripts/run_cli.py ida xrefs-to 0x401000`
- `python3 scripts/run_cli.py ida structs --query IMAGE --limit 20`
- `python3 scripts/run_cli.py ida struct IMAGE_DOS_HEADER`

## Write tools

- `python3 scripts/run_cli.py ida rename 0x401000 decrypt_config`
- `python3 scripts/run_cli.py ida comment 0x401000 "config decryptor"`
- `python3 scripts/run_cli.py ida append-comment 0x401000 "called before network init"`
- `python3 scripts/run_cli.py ida patch-bytes 0x401000 "90 90"`
- `python3 scripts/run_cli.py ida define-function 0x401000`

## Python escape hatch

- `python3 scripts/run_cli.py ida py-eval "print(hex(here()))"`
- `cat script.py | python3 scripts/run_cli.py ida py-eval --stdin`
- `python3 scripts/run_cli.py ida py-file /tmp/script.py`

## Raw tool mode

Keep `ida tool ... --json-args ...` for advanced calls that do not yet have a
short alias.

## Runtime notes

- When exactly one registry-backed instance exists, tool calls use it directly
  instead of forcing a new health probe first.
- In WSL, the client can auto-try Windows-side host candidates advertised by
  the bridge.
