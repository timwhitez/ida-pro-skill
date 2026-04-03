#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="${ROOT_DIR}/skills/ida-pro-skill"
TARGETS="codex,claude,opencode"
IDA_PLUGIN_DIR=""
PYTHON_CMD=""

usage() {
  cat <<'EOF'
Usage:
  ./install.sh [--targets codex,claude,opencode|all] [--ida-plugin-dir /path/to/IDA/plugins]

Behavior:
  - Installs the skill into Codex, Claude Code, and/or OpenCode.
  - Uses only the local Python standard library runtime. No extra pip packages are required.
  - If --ida-plugin-dir is provided, copies the plugin there automatically.
  - Otherwise prints the exact plugin copy and activation steps.
EOF
}

require_path() {
  local path="$1"
  if [[ ! -e "$path" ]]; then
    echo "Required path is missing: $path" >&2
    exit 1
  fi
}

detect_python() {
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
    return
  fi
  if command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
    return
  fi
  echo "python3 or python is required." >&2
  exit 1
}

copy_dir_contents() {
  local src="$1"
  local dest="$2"
  mkdir -p "$dest"
  cp -R "$src"/. "$dest"/
}

normalize_targets() {
  local raw="$1"
  local item
  local normalized=()
  IFS=',' read -r -a input <<< "$raw"
  for item in "${input[@]}"; do
    item="$(echo "$item" | tr '[:upper:]' '[:lower:]' | xargs)"
    [[ -z "$item" ]] && continue
    if [[ "$item" == "all" ]]; then
      normalized=("codex" "claude" "opencode")
      break
    fi
    case "$item" in
      codex|claude|opencode)
        ;;
      *)
        echo "Unsupported target: $item" >&2
        exit 1
        ;;
    esac
    if [[ " ${normalized[*]} " != *" ${item} "* ]]; then
      normalized+=("$item")
    fi
  done
  if [[ ${#normalized[@]} -eq 0 ]]; then
    echo "No installation targets were provided." >&2
    exit 1
  fi
  printf '%s\n' "${normalized[@]}"
}

target_dir_for() {
  local target="$1"
  case "$target" in
    codex)
      echo "${HOME}/.codex/skills/ida-pro-skill"
      ;;
    claude)
      echo "${HOME}/.claude/skills/ida-pro-skill"
      ;;
    opencode)
      echo "${XDG_CONFIG_HOME:-${HOME}/.config}/opencode/skills/ida-pro-skill"
      ;;
  esac
}

install_skill_target() {
  local target="$1"
  local target_dir
  target_dir="$(target_dir_for "$target")"
  rm -rf "$target_dir"
  mkdir -p "$target_dir"
  cp "$SKILL_ROOT/SKILL.md" "$target_dir/SKILL.md"
  copy_dir_contents "$SKILL_ROOT/references" "$target_dir/references"
  copy_dir_contents "$SKILL_ROOT/scripts" "$target_dir/scripts"
  copy_dir_contents "$SKILL_ROOT/ida_pro_skill" "$target_dir/ida_pro_skill"
  copy_dir_contents "$ROOT_DIR/plugin" "$target_dir/plugin"

  echo "Installed skill for ${target}: ${target_dir}"
}

copy_plugin_if_requested() {
  if [[ -z "$IDA_PLUGIN_DIR" ]]; then
    return
  fi

  local copy_log
  copy_log="$(mktemp)"

  if {
    mkdir -p "$IDA_PLUGIN_DIR" &&
    rm -rf "${IDA_PLUGIN_DIR}/ida_pro_skill_plugin.py" "${IDA_PLUGIN_DIR}/ida_pro_skill_plugin_runtime" &&
    cp "$ROOT_DIR/plugin/ida_pro_skill_plugin.py" "${IDA_PLUGIN_DIR}/ida_pro_skill_plugin.py" &&
    cp -R "$ROOT_DIR/plugin/ida_pro_skill_plugin_runtime" "${IDA_PLUGIN_DIR}/ida_pro_skill_plugin_runtime"
  } 2>"$copy_log"; then
    rm -f "$copy_log"
    echo "Copied plugin into: ${IDA_PLUGIN_DIR}"
    return
  fi

  echo "Warning: automatic plugin copy failed for: ${IDA_PLUGIN_DIR}" >&2
  if [[ -s "$copy_log" ]]; then
    sed 's/^/  /' "$copy_log" >&2
  fi
  rm -f "$copy_log"
  echo "Warning: skill installation completed, but you still need to copy the plugin manually." >&2
}

print_install_summary() {
  local target
  echo
  echo "Install summary:"
  for target in "${NORMALIZED_TARGETS[@]}"; do
    echo "  - ${target}: $(target_dir_for "$target")"
  done
  echo "  - runtime: ${PYTHON_CMD}"
}

print_plugin_guidance() {
  cat <<EOF

Plugin files to copy into your IDA plugins directory:
  ${ROOT_DIR}/plugin/ida_pro_skill_plugin.py
  ${ROOT_DIR}/plugin/ida_pro_skill_plugin_runtime
EOF

  if [[ -n "$IDA_PLUGIN_DIR" ]]; then
    cat <<EOF

Plugin target directory:
  ${IDA_PLUGIN_DIR}
EOF
  fi

  cat <<'EOF'

Plugin activation guide:
  1. Copy the two plugin items above into IDA's plugins directory if you did not use --ida-plugin-dir or if automatic copy failed.
  2. Restart IDA.
  3. Open any database.
  4. Check the Output window for a line like:
     [ida-pro-skill] bridge started on ...
  5. If you want to confirm manually, use:
     Edit -> Plugins -> ida-pro-skill
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --targets)
      TARGETS="${2:-}"
      shift 2
      ;;
    --ida-plugin-dir)
      IDA_PLUGIN_DIR="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

detect_python
require_path "$SKILL_ROOT"
require_path "$SKILL_ROOT/SKILL.md"
require_path "$SKILL_ROOT/references"
require_path "$SKILL_ROOT/scripts"
require_path "$SKILL_ROOT/ida_pro_skill"
require_path "$ROOT_DIR/plugin/ida_pro_skill_plugin.py"
require_path "$ROOT_DIR/plugin/ida_pro_skill_plugin_runtime"

echo "Installing ida-pro-skill from: ${SKILL_ROOT}"
echo "Dependency check: no extra Python packages are required."

mapfile -t NORMALIZED_TARGETS < <(normalize_targets "$TARGETS")
for target in "${NORMALIZED_TARGETS[@]}"; do
  install_skill_target "$target"
done

print_install_summary
copy_plugin_if_requested
print_plugin_guidance
