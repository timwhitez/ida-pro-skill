# Safety

- Use the installed IDA instance for static analysis only.
- Do not execute unknown binaries from the skill workflow.
- Prefer built-in bridge tools before using `py_eval` or `py_exec_file`.
- When using `py_eval`, keep snippets small and explicit.
- When patching bytes or renaming symbols, capture the reason in comments so
  the resulting IDB stays explainable.
