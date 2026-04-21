from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ..common import IdaProSkillError, default_app_home, stdout_json
from ..runtime.client import call_tool, current_instance, list_instances, select_instance


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ida-pro-skill")
    parser.add_argument("--app-home", default=str(default_app_home()))

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor")

    ida_parser = subparsers.add_parser("ida")
    ida_sub = ida_parser.add_subparsers(dest="ida_command", required=True)
    ida_sub.add_parser("list-instances")
    ida_sub.add_parser("current")
    select_parser = ida_sub.add_parser("select")
    select_parser.add_argument("--instance", required=True)

    metadata_parser = ida_sub.add_parser("metadata")
    _add_instance_arg(metadata_parser)
    cursor_parser = ida_sub.add_parser("cursor")
    _add_instance_arg(cursor_parser)
    selection_parser = ida_sub.add_parser("selection")
    _add_instance_arg(selection_parser)
    segments_parser = ida_sub.add_parser("segments")
    _add_instance_arg(segments_parser)
    entrypoints_parser = ida_sub.add_parser("entrypoints")
    _add_instance_arg(entrypoints_parser)
    tools_parser = ida_sub.add_parser("tools")
    _add_instance_arg(tools_parser)
    structs_parser = ida_sub.add_parser("structs")
    structs_parser.add_argument("--query")
    structs_parser.add_argument("--offset", type=int, default=0)
    structs_parser.add_argument("--limit", type=int, default=100)
    _add_instance_arg(structs_parser)

    struct_parser = ida_sub.add_parser("struct")
    struct_parser.add_argument("name")
    _add_instance_arg(struct_parser)

    functions_parser = ida_sub.add_parser("functions")
    functions_parser.add_argument("--query")
    functions_parser.add_argument("--offset", type=int, default=0)
    functions_parser.add_argument("--limit", type=int, default=50)
    _add_instance_arg(functions_parser)

    function_parser = ida_sub.add_parser("function")
    function_parser.add_argument("address")
    _add_instance_arg(function_parser)

    decompile_parser = ida_sub.add_parser("decompile")
    decompile_parser.add_argument("address")
    _add_instance_arg(decompile_parser)

    disassemble_parser = ida_sub.add_parser("disassemble")
    disassemble_parser.add_argument("address")
    _add_instance_arg(disassemble_parser)

    imports_parser = ida_sub.add_parser("imports")
    imports_parser.add_argument("--query")
    imports_parser.add_argument("--offset", type=int, default=0)
    imports_parser.add_argument("--limit", type=int, default=100)
    _add_instance_arg(imports_parser)

    import_callers_parser = ida_sub.add_parser("import-callers")
    import_callers_parser.add_argument("query")
    import_callers_parser.add_argument("--import-limit", type=int, default=20)
    import_callers_parser.add_argument("--caller-limit", type=int, default=100)
    _add_instance_arg(import_callers_parser)

    strings_parser = ida_sub.add_parser("strings")
    strings_parser.add_argument("--query")
    strings_parser.add_argument("--offset", type=int, default=0)
    strings_parser.add_argument("--limit", type=int, default=100)
    strings_parser.add_argument("--min-length", type=int, default=4)
    _add_instance_arg(strings_parser)

    string_xrefs_parser = ida_sub.add_parser("string-xrefs")
    string_xrefs_parser.add_argument("query")
    string_xrefs_parser.add_argument("--string-limit", type=int, default=20)
    string_xrefs_parser.add_argument("--xref-limit", type=int, default=100)
    string_xrefs_parser.add_argument("--min-length", type=int, default=4)
    _add_instance_arg(string_xrefs_parser)

    globals_parser = ida_sub.add_parser("globals")
    globals_parser.add_argument("--query")
    globals_parser.add_argument("--offset", type=int, default=0)
    globals_parser.add_argument("--limit", type=int, default=100)
    _add_instance_arg(globals_parser)

    callers_parser = ida_sub.add_parser("callers")
    callers_parser.add_argument("address")
    _add_instance_arg(callers_parser)

    xrefs_to_parser = ida_sub.add_parser("xrefs-to")
    xrefs_to_parser.add_argument("address")
    _add_instance_arg(xrefs_to_parser)

    xrefs_from_parser = ida_sub.add_parser("xrefs-from")
    xrefs_from_parser.add_argument("address")
    _add_instance_arg(xrefs_from_parser)

    rename_parser = ida_sub.add_parser("rename")
    rename_parser.add_argument("address")
    rename_parser.add_argument("name")
    _add_instance_arg(rename_parser)

    comment_parser = ida_sub.add_parser("comment")
    comment_parser.add_argument("address")
    comment_parser.add_argument("comment")
    _add_instance_arg(comment_parser)

    append_comment_parser = ida_sub.add_parser("append-comment")
    append_comment_parser.add_argument("address")
    append_comment_parser.add_argument("comment")
    _add_instance_arg(append_comment_parser)

    patch_bytes_parser = ida_sub.add_parser("patch-bytes")
    patch_bytes_parser.add_argument("address")
    patch_bytes_parser.add_argument("hex")
    _add_instance_arg(patch_bytes_parser)

    define_function_parser = ida_sub.add_parser("define-function")
    define_function_parser.add_argument("address")
    _add_instance_arg(define_function_parser)

    export_ai_parser = ida_sub.add_parser("export-ai")
    export_ai_parser.add_argument("output_dir", nargs="?")
    export_ai_parser.add_argument("--query")
    export_ai_parser.add_argument("--offset", type=int, default=0)
    export_ai_parser.add_argument("--limit", type=int, default=100)
    export_ai_parser.add_argument("--all-functions", action="store_true")
    export_ai_parser.add_argument("--string-limit", type=int, default=1000)
    export_ai_parser.add_argument("--all-strings", action="store_true")
    export_ai_parser.add_argument("--min-string-length", type=int, default=4)
    export_ai_parser.add_argument("--no-decompile", action="store_true")
    export_ai_parser.add_argument("--max-function-bytes", type=int, default=16 * 1024)
    export_ai_parser.add_argument("--max-instructions", type=int, default=3000)
    export_ai_parser.add_argument("--timeout", type=float, default=120.0)
    _add_instance_arg(export_ai_parser)

    py_eval_parser = ida_sub.add_parser("py-eval")
    py_eval_parser.add_argument("code", nargs="?")
    py_eval_parser.add_argument("--stdin", action="store_true")
    _add_instance_arg(py_eval_parser)

    py_file_parser = ida_sub.add_parser("py-file")
    py_file_parser.add_argument("path")
    _add_instance_arg(py_file_parser)

    tool_parser = ida_sub.add_parser("tool")
    tool_parser.add_argument("tool_name")
    tool_parser.add_argument("--json-args")
    tool_parser.add_argument("--stdin-json", action="store_true")
    _add_instance_arg(tool_parser)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    app_home = Path(args.app_home).expanduser()

    try:
        if args.command == "doctor":
            payload = doctor(app_home)
        elif args.command == "ida":
            payload = ida_command(app_home, args)
        else:
            raise IdaProSkillError(f"Unsupported command: {args.command}")
    except IdaProSkillError as exc:
        print(stdout_json({"ok": False, "error": str(exc)}))
        return 1

    print(stdout_json({"ok": True, "result": payload}))
    return 0


def doctor(app_home: Path) -> dict[str, Any]:
    return {"app_home": str(app_home), "instances": list_instances(app_home)}


def ida_command(app_home: Path, args: argparse.Namespace) -> Any:
    if args.ida_command == "list-instances":
        return list_instances(app_home)
    if args.ida_command == "current":
        return current_instance(app_home)
    if args.ida_command == "select":
        return select_instance(app_home, args.instance)
    if args.ida_command == "metadata":
        return _call_alias_tool(app_home, args, "get_metadata")
    if args.ida_command == "cursor":
        return _call_alias_tool(app_home, args, "get_cursor")
    if args.ida_command == "selection":
        return _call_alias_tool(app_home, args, "get_selection")
    if args.ida_command == "segments":
        return _call_alias_tool(app_home, args, "get_segments")
    if args.ida_command == "entrypoints":
        return _call_alias_tool(app_home, args, "get_entrypoints")
    if args.ida_command == "tools":
        return _call_alias_tool(app_home, args, "list_tools")
    if args.ida_command == "structs":
        return _call_alias_tool(
            app_home,
            args,
            "get_structs",
            {"query": args.query, "offset": args.offset, "limit": args.limit},
        )
    if args.ida_command == "struct":
        return _call_alias_tool(app_home, args, "get_struct", {"name": args.name})
    if args.ida_command == "functions":
        return _call_alias_tool(
            app_home,
            args,
            "list_functions",
            {"query": args.query, "offset": args.offset, "limit": args.limit},
        )
    if args.ida_command == "function":
        return _call_alias_tool(app_home, args, "get_function", {"address": args.address})
    if args.ida_command == "decompile":
        return _call_alias_tool(app_home, args, "decompile", {"address": args.address})
    if args.ida_command == "disassemble":
        return _call_alias_tool(app_home, args, "disassemble", {"address": args.address})
    if args.ida_command == "imports":
        return _call_alias_tool(
            app_home,
            args,
            "list_imports",
            {"query": args.query, "offset": args.offset, "limit": args.limit},
        )
    if args.ida_command == "import-callers":
        return _call_alias_tool(
            app_home,
            args,
            "list_import_callers",
            {"query": args.query, "import_limit": args.import_limit, "caller_limit": args.caller_limit},
        )
    if args.ida_command == "strings":
        return _call_alias_tool(
            app_home,
            args,
            "list_strings",
            {
                "query": args.query,
                "offset": args.offset,
                "limit": args.limit,
                "min_length": args.min_length,
            },
        )
    if args.ida_command == "string-xrefs":
        return _call_alias_tool(
            app_home,
            args,
            "list_string_xrefs",
            {
                "query": args.query,
                "string_limit": args.string_limit,
                "xref_limit": args.xref_limit,
                "min_length": args.min_length,
            },
        )
    if args.ida_command == "globals":
        return _call_alias_tool(
            app_home,
            args,
            "list_globals",
            {"query": args.query, "offset": args.offset, "limit": args.limit},
        )
    if args.ida_command == "callers":
        return _call_alias_tool(app_home, args, "list_callers", {"address": args.address})
    if args.ida_command == "xrefs-to":
        return _call_alias_tool(app_home, args, "xrefs_to", {"address": args.address})
    if args.ida_command == "xrefs-from":
        return _call_alias_tool(app_home, args, "xrefs_from", {"address": args.address})
    if args.ida_command == "rename":
        return _call_alias_tool(app_home, args, "rename", {"address": args.address, "name": args.name})
    if args.ida_command == "comment":
        return _call_alias_tool(
            app_home, args, "set_comment", {"address": args.address, "comment": args.comment}
        )
    if args.ida_command == "append-comment":
        return _call_alias_tool(
            app_home, args, "append_comment", {"address": args.address, "comment": args.comment}
        )
    if args.ida_command == "patch-bytes":
        return _call_alias_tool(app_home, args, "patch_bytes", {"address": args.address, "hex": args.hex})
    if args.ida_command == "define-function":
        return _call_alias_tool(app_home, args, "define_function", {"address": args.address})
    if args.ida_command == "export-ai":
        return call_tool(
            app_home,
            "export_ai_context",
            {
                "output_dir": args.output_dir,
                "query": args.query,
                "offset": args.offset,
                "limit": None if args.all_functions else args.limit,
                "string_limit": None if args.all_strings else args.string_limit,
                "min_string_length": args.min_string_length,
                "include_decompile": not args.no_decompile,
                "max_function_bytes": args.max_function_bytes,
                "max_instructions": args.max_instructions,
            },
            instance=args.instance,
            timeout=args.timeout,
        )
    if args.ida_command == "py-eval":
        return _call_alias_tool(app_home, args, "py_eval", {"code": _py_eval_code(args)})
    if args.ida_command == "py-file":
        return _call_alias_tool(app_home, args, "py_exec_file", {"path": args.path})
    if args.ida_command == "tool":
        arguments = _tool_arguments(args)
        return call_tool(app_home, args.tool_name, arguments, instance=args.instance)
    raise IdaProSkillError(f"Unsupported ida command: {args.ida_command}")


def _call_alias_tool(
    app_home: Path,
    args: argparse.Namespace,
    tool_name: str,
    arguments: dict[str, Any] | None = None,
) -> Any:
    return call_tool(app_home, tool_name, arguments or {}, instance=getattr(args, "instance", None))


def _add_instance_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--instance")


def _tool_arguments(args: argparse.Namespace) -> dict[str, Any]:
    if args.stdin_json:
        import sys

        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    if args.json_args:
        return json.loads(args.json_args)
    return {}


def _py_eval_code(args: argparse.Namespace) -> str:
    if args.stdin and args.code is not None:
        raise IdaProSkillError("Use either `ida py-eval <code>` or `ida py-eval --stdin`, not both")
    if args.stdin:
        import sys

        code = sys.stdin.read()
        if not code.strip():
            raise IdaProSkillError("No Python code was provided on stdin")
        return code
    if args.code is None:
        raise IdaProSkillError("Python code is required. Use `ida py-eval <code>` or `ida py-eval --stdin`.")
    return args.code
