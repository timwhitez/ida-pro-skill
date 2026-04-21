# Safety

- Use the installed IDA instance for static analysis only.
- Do not execute unknown binaries from the skill workflow.
- Prefer built-in bridge tools before using `py_eval` or `py_exec_file`.
- When using `py_eval`, keep snippets small and explicit.
- Keep `plugin/ida_pro_skill_plugin.py` at `REMOTE_ACCESS = False` unless you
  intentionally need to expose the bridge to other machines.
- Keep `ida export-ai` bounded unless the user explicitly requests a full
  export. Large exports can keep IDA busy and may write substantial decompiled
  or disassembled source context to disk.
- Remember that `ida export-ai` paths are resolved inside the IDA process; avoid
  writing exports into repos, sync folders, or shared directories unless the
  user asked for that destination.
- When patching bytes or renaming symbols, capture the reason in comments so
  the resulting IDB stays explainable.
