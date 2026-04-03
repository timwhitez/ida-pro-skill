# Workflow

## Recommended sequence

1. Run `python3 scripts/run_cli.py ida list-instances`.
2. Select the intended IDA instance when more than one is active.
3. Start with `ida metadata`, `ida cursor`, `ida selection`, `ida tools`,
   `ida segments`, and `ida entrypoints`.
4. Use `ida functions`, `ida imports`, `ida strings`, `ida import-callers`,
   and xref tools to
   locate interesting code paths.
5. For type recovery, use `ida structs --query ...` before `ida struct <name>`
   so the model does not dump an unbounded type list.
6. Use `ida decompile` first and only drop to `ida disassemble` when pseudocode is not
   enough.
7. Record findings with `ida comment`, `ida append-comment`, and `ida rename`.
8. Use `ida patch-bytes` and `ida define-function` when the user explicitly
   wants IDB edits beyond comments and renames.
9. Use `ida py-eval`, `ida py-file`, or raw `ida tool py_exec_file` only when
   the built-in tools are not enough.
10. In WSL, trust the CLI's discovered host candidates instead of hard-coding
   `127.0.0.1`.

## Common goals

- Malware triage
- Protocol reversing
- Crackme analysis
- Library identification
- Algorithm recovery
- Patch planning
