# AGENTS.md

This repository builds and ships `ida-pro-skill`, an open-source MIT-licensed
skill-first integration for IDA Pro.

## Working rules

- Follow SDD, TDD, and DDD for every meaningful change.
- Update private `spec/` artifacts before or alongside public implementation.
- Keep commits non-interactive and free of secrets, local machine identifiers,
  proprietary samples, tokens, IDA databases, and generated analysis output.
- Never commit files under `spec/`, `samples/`, runtime state, or installer
  backups.
- Prefer the smallest correct change that preserves skill compatibility for
  both Codex and Claude Code.

## Product shape

- Codex and Claude Code consume this project as a skill, not as a client-side
  MCP configuration.
- The installed skill may call local shell commands and local helper scripts.
- The IDA side is implemented as a thin Python plugin that exposes a local
  HTTP JSON bridge for the CLI.

## Validation

- New public commands and installer behaviors need tests.
- Changes that affect installed skill files must verify both Codex and Claude
  skill directory rendering.
- Keep runtime dependencies minimal. Standard library only is preferred.
