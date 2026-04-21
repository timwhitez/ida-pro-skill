# Workflow

## Recommended sequence

1. Run `python3 scripts/run_cli.py ida list-instances`.
2. Run `ida metadata` and `ida tools` early so you can read
   `access_mode` and `remote_access_enabled`.
3. Select the intended IDA instance when more than one is active.
4. Start with `ida metadata`, `ida cursor`, `ida selection`, `ida tools`,
   `ida segments`, and `ida entrypoints`.
5. Use `ida functions`, `ida imports`, `ida strings`, `ida import-callers`,
   and xref tools to
   locate interesting code paths.
6. For type recovery, use `ida structs --query ...` before `ida struct <name>`
   so the model does not dump an unbounded type list.
7. Use `ida decompile` first and only drop to `ida disassemble` when pseudocode is not
   enough.
8. When the user wants broader AI IDE indexing or a handoff artifact, run
   `ida export-ai` with a bounded `--query`, `--limit`, or explicit
   `output_dir`.
9. Record findings with `ida comment`, `ida append-comment`, and `ida rename`.
10. Use `ida patch-bytes` and `ida define-function` when the user explicitly
   wants IDB edits beyond comments and renames.
11. Use `ida py-eval`, `ida py-file`, or raw `ida tool py_exec_file` only when
   the built-in tools are not enough.
12. In WSL, trust the CLI's discovered host candidates instead of hard-coding
   `127.0.0.1`.
13. If the bridge reports `access_mode: local-only`, treat that as expected
   default hardening. Do not recommend changing `REMOTE_ACCESS` unless the user
   explicitly wants external-machine access.

## Common goals

- Malware triage
- Protocol reversing
- Crackme analysis
- Library identification
- Algorithm recovery
- Patch planning
- Offline AI IDE context export
