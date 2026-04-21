---
name: ida-pro-skill
description: "Use this skill only when Codex needs to work with a currently running IDA Pro database through the local ida-pro-skill CLI and installed IDA HTTP bridge. Trigger it for live IDA tasks such as: discovering or selecting IDA instances; reading metadata, cursor or selection, segments, entrypoints, functions, callers/callees, xrefs, imports, strings, globals, structs, or types; decompiling or disassembling code from the open IDB; exporting bounded AI context packs from IDA; applying deliberate IDB edits such as rename/comment/patch/define-function; or running explicit IDAPython with py-eval or py-file. Do not use it for generic reverse-engineering advice that does not require a live IDA session. This skill explicitly covers WSL-to-Windows IDA bridge workflows."
---

# ida-pro-skill

Drive static analysis against a live IDA database from Codex, Claude Code, or
OpenCode.

If the skill is not installed yet, the supported repo entrypoint is root
`./install.sh`.

## Operating Rules

- Default to static analysis only.
- Do not execute the target binary.
- Prefer built-in aliases before raw `ida tool ...` or IDAPython.
- Treat `py-eval`, `py-file`, `patch-bytes`, and `define-function` as
  deliberate, higher-risk actions.
- Keep `REMOTE_ACCESS = False` unless the user explicitly wants another
  machine to connect.

## Quick Workflow

1. Confirm the local installation if needed:
   `python3 scripts/run_cli.py doctor`
2. Discover live IDA instances:
   `python3 scripts/run_cli.py ida list-instances`
3. Inspect bridge and database state before analysis:
   `python3 scripts/run_cli.py ida metadata`
   `python3 scripts/run_cli.py ida tools`
   Read `access_mode`, `remote_access_enabled`, `input_path`, `idb_path`,
   `imagebase`, and available tools.
4. If multiple instances are running, select one:
   `python3 scripts/run_cli.py ida select --instance 127.0.0.1:39091`
5. Use short aliases first; use raw `ida tool ...` only for unaliased bridge
   methods.

## Command Selection

- **Overview:** `ida metadata`, `ida cursor`, `ida selection`, `ida segments`,
  `ida entrypoints`, `ida tools`
- **Function map:** `ida functions --limit 20`, `ida function <addr-or-name>`,
  `ida callers <addr>`, `ida xrefs-to <addr>`, `ida xrefs-from <addr>`
- **Code understanding:** `ida decompile <addr>`, `ida disassemble <addr>`,
  `ida imports --query <api>`, `ida import-callers <api>`,
  `ida strings --query <text>`, `ida string-xrefs <text>`, `ida globals`
- **Types:** `ida structs --query <name> --limit 20`, then
  `ida struct <name>`
- **Offline context:** `ida export-ai [output_dir] --query <term> --limit 100`
- **IDB updates:** `ida rename <addr> <name>`, `ida comment <addr> <text>`,
  `ida append-comment <addr> <text>`, `ida patch-bytes <addr> "90 90"`,
  `ida define-function <addr>`
- **Python escape hatch:** `ida py-eval "print(hex(here()))"`,
  `cat script.py | python3 scripts/run_cli.py ida py-eval --stdin`,
  `ida py-file /tmp/script.py`

## Analysis Heuristics

- Start from cursor/selection when the user references the current IDA view.
- Use `ida import-callers <api>` for Windows API tracing instead of manually
  copying import addresses.
- Use `ida string-xrefs <text>` for user-visible strings before issuing manual
  xref calls.
- Use `ida structs --query ...` before `ida struct ...` to avoid unbounded type
  dumps.
- Use `ida decompile` first; fall back to `ida disassemble` when Hex-Rays is
  unavailable or pseudocode is misleading.
- Use `ida export-ai` when the user wants a source-tree-style handoff for
  broader AI IDE indexing. Keep it bounded by default; use `--all-functions` or
  `--all-strings` only after explicit user intent.

## WSL And Connectivity

- Trust discovered host candidates; do not assume `127.0.0.1` reaches
  Windows-hosted IDA from WSL.
- If WSL `cmd.exe` interop is unavailable, discovery can still use mounted
  Windows registry files such as
  `/mnt/c/Users/<user>/.ida-pro-skill/instances`.
- Treat `ida export-ai` output paths as paths from the IDA process perspective.
  If IDA runs on Windows and Codex runs in WSL, omit `output_dir` or use a
  Windows path.
- Diagnose bridge access with `access_mode` and `remote_access_enabled` from
  `ida metadata` or `ida tools`; do not recommend enabling `REMOTE_ACCESS`
  unless the user explicitly wants external-machine access.
- Run heavy bridge calls such as `decompile`, `export-ai`, and `py-eval`
  serially.

## References

- Read `references/workflow.md` for full analysis flow.
- Read `references/cli-reference.md` for command details.
- Read `references/safety.md` before write operations or IDAPython.
- Read `references/troubleshooting.md` for discovery, WSL, or bridge failures.
