# Troubleshooting

## Instance discovery

- Run `python scripts/run_cli.py ida list-instances` to see the discovered bridge
  instances and their reachable hosts.
- In WSL, do not assume `127.0.0.1` can reach a Windows-hosted IDA bridge. The
  CLI will try the bridge's advertised host candidates.
- When exactly one instance is registered, direct tool calls can still work even
  if a fresh health probe is temporarily blocked by a heavy IDA action.

## Heavy operations

- Prefer one heavy bridge call at a time for `decompile`, `disassemble`, and
  `py-eval`.
- If a tool call fails during active autoanalysis, retry after the current IDA
  task settles.
- If a newly added alias fails with `Unknown tool` or a bridge-side traceback,
  make sure the latest plugin files were recopied into the real IDA plugins
  directory and IDA was restarted.
- If `ida struct <name>` only returns a bare type name, the running plugin is
  older than the repo copy that adds structured member output.

## Python helpers

- Use `python scripts/run_cli.py ida py-eval "print(hex(here()))"` for short
  one-liners.
- Use `cat script.py | python scripts/run_cli.py ida py-eval --stdin` for
  multiline snippets that would be awkward to shell-quote.
- Use `python scripts/run_cli.py ida py-file /path/to/script.py` when the code
  already exists in a local file.

## Plugin install on WSL

- On WSL, pass `--ida-plugin-dir "/mnt/c/.../plugins"` when the Windows IDA
  plugins directory is known when you run root `install.sh`.
- If you do not pass `--ida-plugin-dir`, root `install.sh` will still show the
  exact plugin source paths and the activation steps after copying.
