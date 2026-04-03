---
name: ida-pro-skill
description: IDA Pro reverse-engineering skill for Codex, Claude Code, and OpenCode. Use when a user needs live IDA or Hex-Rays analysis through the local ida-pro-skill CLI and installed IDA bridge, especially for instance discovery, metadata, cursor or selection context, entrypoints, functions, callers, imports, strings, xrefs, pseudocode, globals, structs, renames, comments, byte patches, function creation, or explicit IDAPython, including WSL-to-Windows IDA setups.
---

# ida-pro-skill

Use this skill when the user wants IDA Pro driven static analysis from Codex,
Claude Code, or OpenCode.

If the skill is not installed yet, the supported repo entrypoint is root
`./install.sh`.

## Safety

- Default to static analysis only.
- Do not execute the target binary.
- Treat `py_eval` and `py_exec_file` as higher-risk escape hatches.

## Workflow

1. Confirm the local installation if needed:
   `python3 scripts/run_cli.py doctor`
2. Discover live IDA instances:
   `python3 scripts/run_cli.py ida list-instances`
3. Immediately inspect the active bridge state:
   `python3 scripts/run_cli.py ida metadata`
   `python3 scripts/run_cli.py ida tools`
   Read `access_mode` and `remote_access_enabled` before diagnosing connectivity.
4. If multiple instances are running, select one:
   `python3 scripts/run_cli.py ida select --instance 127.0.0.1:39091`
5. Prefer the short alias commands over raw JSON-heavy `ida tool ...` calls:
   `python3 scripts/run_cli.py ida metadata`
   `python3 scripts/run_cli.py ida cursor`
   `python3 scripts/run_cli.py ida selection`
   `python3 scripts/run_cli.py ida tools`
   `python3 scripts/run_cli.py ida functions --limit 20`
   `python3 scripts/run_cli.py ida decompile 0x401000`
   `python3 scripts/run_cli.py ida imports --query OpenService`
   `python3 scripts/run_cli.py ida import-callers OpenService`
   `python3 scripts/run_cli.py ida string-xrefs uninstall`
   `python3 scripts/run_cli.py ida structs --query IMAGE --limit 20`
   `python3 scripts/run_cli.py ida struct IMAGE_DOS_HEADER`
   `python3 scripts/run_cli.py ida patch-bytes 0x401000 "90 90"`
   `python3 scripts/run_cli.py ida define-function 0x401000`
6. Use `ida tool ...` only for advanced or not-yet-aliased operations.
7. Use explicit Python only when the built-in tools are not enough:
   `python3 scripts/run_cli.py ida py-eval "print(hex(here()))"`
   `cat script.py | python3 scripts/run_cli.py ida py-eval --stdin`
   `python3 scripts/run_cli.py ida py-file /tmp/script.py`

## Preferred tool order

- Metadata and overview: `ida metadata`, `ida cursor`, `ida selection`, `ida segments`, `ida entrypoints`
- Tool discovery: `ida tools`
- Function discovery: `ida functions`, `ida function`, `ida callers`, `ida xrefs-to`, `ida xrefs-from`, `ida define-function`
- Code understanding: `ida decompile`, `ida disassemble`, `ida strings`, `ida imports`, `ida import-callers`, `ida string-xrefs`, `ida globals`, `ida structs`, `ida struct`
- Database updates: `ida rename`, `ida comment`, `ida append-comment`, `ida patch-bytes`
- Escape hatch: `ida py-eval`, `ida py-file`, raw `py_exec_file`

## Agent Tips

- When tracing a Windows API, prefer `ida import-callers <name>` over manually
  copying import addresses from the import table.
- When tracing a user-visible string, prefer `ida string-xrefs <query>` over
  manually searching strings and then issuing separate xref lookups.
- When the user asks about "where the cursor is" or selected code, use
  `ida cursor` and `ida selection` before guessing addresses.
- When the user asks about data structures or type layouts, use
  `ida structs --query ...` to narrow candidates, then `ida struct <name>` for
  the member list.
- When Python snippets are multiline or shell quoting is awkward, prefer
  `ida py-eval --stdin` or `ida py-file` over packing large code into one shell
  argument.
- When a single live IDA instance exists, do not waste turns selecting it; the
  CLI auto-selects it.
- The CLI is WSL-aware and can reach a Windows-hosted IDA bridge through the
  advertised host candidates; do not assume `127.0.0.1` will work from WSL.
- Check `ida metadata` or `ida tools` early; they expose `access_mode` and
  `remote_access_enabled`, which are the fastest way to distinguish a bridge ACL
  restriction from a normal connectivity issue.
- The plugin now defaults to `REMOTE_ACCESS = False`; this still allows
  localhost and local WSL access, but intentionally rejects other machines
  unless the user explicitly enables remote access in the plugin file.
- Do not suggest changing `REMOTE_ACCESS` just because WSL cannot use
  `127.0.0.1`; first try the advertised host candidates. Only suggest enabling
  remote access when the user explicitly wants other machines to connect.
- Prefer one bridge call at a time for heavier work such as `decompile` or
  `py-eval`; the CLI no longer requires a fresh health probe for every tool
  call, but serial reads are still easier on a live IDA session.

## References

- Workflow guide: `references/workflow.md`
- CLI reference: `references/cli-reference.md`
- Safety notes: `references/safety.md`
- Troubleshooting: `references/troubleshooting.md`
