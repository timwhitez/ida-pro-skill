from __future__ import annotations

import ast
import io
import json
import os
import socket
import sys
import threading
import traceback
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import idaapi
import ida_auto
import ida_bytes
import ida_funcs
import ida_hexrays
import ida_kernwin
import ida_loader
import ida_nalt
import ida_name
import ida_segment
import ida_typeinf
import ida_xref
import idautils
import idc

APP_HOME = Path(os.environ.get("IDA_PRO_SKILL_HOME", str(Path.home() / ".ida-pro-skill")))
INSTANCE_DIR = APP_HOME / "instances"
LISTEN_HOST = "0.0.0.0"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _parse_address(raw: str | int) -> int:
    if isinstance(raw, int):
        return raw
    text = str(raw).strip()
    if text.startswith("0x") or text.startswith("0X"):
        return int(text, 16)
    ea = idc.get_name_ea_simple(text)
    if ea != idc.BADADDR:
        return ea
    try:
        return int(text, 10)
    except ValueError as exc:
        raise ValueError(f"Unable to resolve address: {raw}") from exc


def _json_result(ok: bool, *, result: Any = None, error: str | None = None) -> bytes:
    return json.dumps({"ok": ok, "result": result, "error": error}).encode("utf-8")


def _run_on_main_thread(func):
    result: dict[str, Any] = {}

    def runner():
        try:
            result["value"] = func()
        except Exception as exc:  # pragma: no cover - IDA runtime only
            result["error"] = "".join(traceback.format_exception(exc))
        return 1

    try:
        ida_kernwin.execute_sync(runner, ida_kernwin.MFF_FAST)
    except Exception:
        runner()

    if "error" in result:
        raise RuntimeError(result["error"])
    return result.get("value")


class _BridgeHandler(BaseHTTPRequestHandler):
    bridge = None

    def do_GET(self):  # pragma: no cover - IDA runtime only
        try:
            if self.path == "/health":
                result = _run_on_main_thread(lambda: self.bridge.health())
                self._write(200, _json_result(True, result=result))
                return
            if self.path == "/manifest":
                result = _run_on_main_thread(lambda: self.bridge.manifest())
                self._write(200, _json_result(True, result=result))
                return
        except Exception as exc:
            self._write(200, _json_result(False, error=str(exc)))
            return
        self._write(404, _json_result(False, error="Unknown path"))

    def do_POST(self):  # pragma: no cover - IDA runtime only
        if self.path != "/tool":
            self._write(404, _json_result(False, error="Unknown path"))
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        name = payload.get("name")
        arguments = payload.get("arguments", {})
        try:
            result = self.bridge.call_tool(name, arguments)
            self._write(200, _json_result(True, result=result))
        except Exception as exc:
            self._write(200, _json_result(False, error=str(exc)))

    def log_message(self, format, *args):  # noqa: A003
        return

    def _write(self, code: int, body: bytes):  # pragma: no cover - IDA runtime only
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class BridgeServer:
    def __init__(self) -> None:
        self.httpd: ThreadingHTTPServer | None = None
        self.thread: threading.Thread | None = None
        self.port: int | None = None
        self.instance_path: Path | None = None
        self.started_at = _now()
        self.tool_map = {
            "list_tools": self.manifest,
            "get_metadata": self.get_metadata,
            "get_segments": self.get_segments,
            "get_entrypoints": self.get_entrypoints,
            "get_cursor": self.get_cursor,
            "get_selection": self.get_selection,
            "list_functions": self.list_functions,
            "get_function": self.get_function,
            "decompile": self.decompile,
            "disassemble": self.disassemble,
            "list_strings": self.list_strings,
            "list_imports": self.list_imports,
            "list_import_callers": self.list_import_callers,
            "list_string_xrefs": self.list_string_xrefs,
            "list_globals": self.list_globals,
            "xrefs_to": self.xrefs_to,
            "xrefs_from": self.xrefs_from,
            "list_callers": self.list_callers,
            "get_structs": self.get_structs,
            "get_struct": self.get_struct,
            "set_comment": self.set_comment,
            "append_comment": self.append_comment,
            "rename": self.rename,
            "patch_bytes": self.patch_bytes,
            "define_function": self.define_function,
            "py_eval": self.py_eval,
            "py_exec_file": self.py_exec_file,
        }

    def start(self) -> None:  # pragma: no cover - IDA runtime only
        if self.httpd is not None:
            return
        _ensure_dir(INSTANCE_DIR)
        self.port = self._pick_port()
        _BridgeHandler.bridge = self
        self.httpd = ThreadingHTTPServer((LISTEN_HOST, self.port), _BridgeHandler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self._write_instance()

    def stop(self) -> None:  # pragma: no cover - IDA runtime only
        if self.httpd is not None:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None
        if self.instance_path and self.instance_path.exists():
            self.instance_path.unlink()

    def _pick_port(self) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((LISTEN_HOST, 0))
            return int(sock.getsockname()[1])

    def _write_instance(self) -> None:
        payload = self.health()
        payload["instance_id"] = f"{os.getpid()}:{self.port}"
        payload["host"] = "127.0.0.1"
        payload["host_candidates"] = _advertised_ipv4_hosts()
        payload["port"] = self.port
        self.instance_path = INSTANCE_DIR / f"{os.getpid()}_{self.port}.json"
        self.instance_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def manifest(self, _: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "tools": sorted(self.tool_map.keys()),
            "started_at": self.started_at,
        }

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        if name not in self.tool_map:
            raise RuntimeError(f"Unknown tool: {name}")
        return _run_on_main_thread(lambda: self.tool_map[name](arguments or {}))

    def health(self) -> dict[str, Any]:
        input_path = ida_nalt.get_input_file_path() or ""
        file_name = os.path.basename(input_path) if input_path else ""
        md5_raw = ida_nalt.retrieve_input_file_md5()
        md5_text = md5_raw.hex() if isinstance(md5_raw, (bytes, bytearray)) else ""
        return {
            "pid": os.getpid(),
            "started_at": self.started_at,
            "input_path": input_path,
            "file_name": file_name,
            "idb_path": idc.get_idb_path(),
            "processor": ida_idaapi_get_procname(),
            "imagebase": hex(ida_nalt.get_imagebase()),
            "md5": md5_text,
            "listen_host": LISTEN_HOST,
            "host_candidates": _advertised_ipv4_hosts(),
        }

    def get_metadata(self, _: dict[str, Any]) -> dict[str, Any]:
        ida_auto.auto_wait()
        return self.health()

    def get_segments(self, _: dict[str, Any]) -> list[dict[str, Any]]:
        ida_auto.auto_wait()
        result = []
        for seg_ea in idautils.Segments():
            seg = ida_segment.getseg(seg_ea)
            if not seg:
                continue
            result.append(
                {
                    "name": ida_segment.get_segm_name(seg),
                    "start": hex(seg.start_ea),
                    "end": hex(seg.end_ea),
                    "perm": seg.perm,
                }
            )
        return result

    def get_entrypoints(self, _: dict[str, Any]) -> list[dict[str, Any]]:
        result = []
        for idx in range(idaapi.get_entry_qty()):
            ordinal = idaapi.get_entry_ordinal(idx)
            ea = idaapi.get_entry(ordinal)
            result.append(
                {
                    "ordinal": ordinal,
                    "address": hex(ea),
                    "name": idaapi.get_entry_name(ordinal),
                }
            )
        return result

    def get_cursor(self, _: dict[str, Any]) -> dict[str, Any]:
        ea = ida_kernwin.get_screen_ea()
        return {"address": hex(ea), "name": ida_name.get_name(ea)}

    def get_selection(self, _: dict[str, Any]) -> dict[str, Any]:
        ok, start, end = ida_kernwin.read_range_selection(None)
        if not ok:
            return {"selected": False}
        return {"selected": True, "start": hex(start), "end": hex(end)}

    def list_functions(self, arguments: dict[str, Any]) -> dict[str, Any]:
        ida_auto.auto_wait()
        query = str(arguments.get("query", "") or "").lower()
        offset = int(arguments.get("offset", 0) or 0)
        limit = int(arguments.get("limit", 50) or 50)
        items = []
        for ea in idautils.Functions():
            name = ida_funcs.get_func_name(ea) or ""
            if query and query not in name.lower() and query not in hex(ea):
                continue
            func = ida_funcs.get_func(ea)
            if not func:
                continue
            items.append(
                {
                    "address": hex(ea),
                    "name": name,
                    "size": func.end_ea - func.start_ea,
                }
            )
        window = items[offset : offset + limit]
        next_offset = offset + limit if offset + limit < len(items) else None
        return {"data": window, "next_offset": next_offset, "total": len(items)}

    def get_function(self, arguments: dict[str, Any]) -> dict[str, Any]:
        ea = _parse_address(arguments["address"])
        return _function_info(ea)

    def decompile(self, arguments: dict[str, Any]) -> dict[str, Any]:
        ea = _parse_address(arguments["address"])
        ida_auto.auto_wait()
        if not ida_hexrays.init_hexrays_plugin():
            raise RuntimeError("Hex-Rays decompiler is not available")
        cfunc = ida_hexrays.decompile(ea)
        if not cfunc:
            raise RuntimeError(f"Failed to decompile function at {hex(ea)}")
        return {
            "address": hex(cfunc.entry_ea),
            "name": ida_funcs.get_func_name(cfunc.entry_ea),
            "pseudocode": str(cfunc),
        }

    def disassemble(self, arguments: dict[str, Any]) -> dict[str, Any]:
        ea = _parse_address(arguments["address"])
        func = ida_funcs.get_func(ea)
        if not func:
            raise RuntimeError(f"No function found at {hex(ea)}")
        lines = []
        for head in idautils.FuncItems(func.start_ea):
            lines.append(
                {
                    "address": hex(head),
                    "text": idc.generate_disasm_line(head, 0) or "",
                }
            )
        return {"address": hex(func.start_ea), "lines": lines}

    def list_strings(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = str(arguments.get("query", "") or "").lower()
        offset = int(arguments.get("offset", 0) or 0)
        limit = int(arguments.get("limit", 100) or 100)
        min_length = int(arguments.get("min_length", 4) or 4)
        items = []
        for item in idautils.Strings():
            text = str(item)
            if len(text) < min_length:
                continue
            if query and query not in text.lower():
                continue
            items.append({"address": hex(item.ea), "text": text, "length": len(text)})
        window = items[offset : offset + limit]
        next_offset = offset + limit if offset + limit < len(items) else None
        return {"data": window, "next_offset": next_offset, "total": len(items)}

    def list_imports(self, arguments: dict[str, Any]) -> dict[str, Any]:
        offset = int(arguments.get("offset", 0) or 0)
        limit = int(arguments.get("limit", 100) or 100)
        query = str(arguments.get("query", "") or "").lower()
        items = _collect_import_rows(query)
        window = items[offset : offset + limit]
        next_offset = offset + limit if offset + limit < len(items) else None
        return {"data": window, "next_offset": next_offset, "total": len(items)}

    def list_import_callers(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = str(arguments.get("query", "") or "").lower()
        if not query:
            raise RuntimeError("query is required")
        import_limit = int(arguments.get("import_limit", 20) or 20)
        caller_limit = int(arguments.get("caller_limit", 100) or 100)
        imports = _collect_import_rows(query)[:import_limit]
        callers = []
        seen: set[tuple[int, int]] = set()
        for item in imports:
            import_ea = int(item["address"], 16)
            for xref in idautils.XrefsTo(import_ea):
                caller = ida_funcs.get_func(xref.frm)
                caller_start = caller.start_ea if caller else xref.frm
                key = (import_ea, xref.frm)
                if key in seen:
                    continue
                seen.add(key)
                callers.append(
                    {
                        "import_name": item["name"],
                        "module": item["module"],
                        "import_address": item["address"],
                        "callsite": hex(xref.frm),
                        "caller_address": hex(caller_start),
                        "caller_name": ida_funcs.get_func_name(caller_start) if caller else ida_name.get_name(xref.frm),
                    }
                )
                if len(callers) >= caller_limit:
                    return {"data": callers, "total": len(callers), "truncated": True}
        return {"data": callers, "total": len(callers), "truncated": False}

    def list_globals(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = str(arguments.get("query", "") or "").lower()
        offset = int(arguments.get("offset", 0) or 0)
        limit = int(arguments.get("limit", 100) or 100)
        items = []
        for ea, name in idautils.Names():
            if ida_funcs.get_func(ea):
                continue
            if query and query not in name.lower():
                continue
            items.append({"address": hex(ea), "name": name, "size": idc.get_item_size(ea)})
        window = items[offset : offset + limit]
        next_offset = offset + limit if offset + limit < len(items) else None
        return {"data": window, "next_offset": next_offset, "total": len(items)}

    def xrefs_to(self, arguments: dict[str, Any]) -> list[dict[str, Any]]:
        ea = _parse_address(arguments["address"])
        return [_xref_row(xref.frm, xref.to, xref.type) for xref in idautils.XrefsTo(ea)]

    def xrefs_from(self, arguments: dict[str, Any]) -> list[dict[str, Any]]:
        ea = _parse_address(arguments["address"])
        return [_xref_row(xref.frm, xref.to, xref.type) for xref in idautils.XrefsFrom(ea, 0)]

    def list_callers(self, arguments: dict[str, Any]) -> dict[str, Any]:
        ea = _parse_address(arguments["address"])
        callers = []
        seen: set[int] = set()
        for xref in idautils.XrefsTo(ea):
            caller = ida_funcs.get_func(xref.frm)
            if not caller or caller.start_ea in seen:
                continue
            seen.add(caller.start_ea)
            callers.append(
                {
                    "caller_address": hex(caller.start_ea),
                    "caller_name": ida_funcs.get_func_name(caller.start_ea),
                    "callsite": hex(xref.frm),
                    "target_address": hex(ea),
                }
            )
        return {"data": callers, "total": len(callers)}

    def list_string_xrefs(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = str(arguments.get("query", "") or "").lower()
        if not query:
            raise RuntimeError("query is required")
        string_limit = int(arguments.get("string_limit", 20) or 20)
        xref_limit = int(arguments.get("xref_limit", 100) or 100)
        result = []
        strings = _collect_string_rows(query=query, min_length=int(arguments.get("min_length", 4) or 4))
        for item in strings[:string_limit]:
            string_ea = int(item["address"], 16)
            for xref in idautils.XrefsTo(string_ea):
                caller = ida_funcs.get_func(xref.frm)
                caller_start = caller.start_ea if caller else xref.frm
                result.append(
                    {
                        "string_address": item["address"],
                        "string_text": item["text"],
                        "xref_from": hex(xref.frm),
                        "caller_address": hex(caller_start),
                        "caller_name": ida_funcs.get_func_name(caller_start) if caller else ida_name.get_name(xref.frm),
                    }
                )
                if len(result) >= xref_limit:
                    return {"data": result, "total": len(result), "truncated": True}
        return {"data": result, "total": len(result), "truncated": False}

    def get_structs(self, arguments: dict[str, Any]) -> dict[str, Any]:
        result = []
        idati = ida_typeinf.get_idati()
        query = str(arguments.get("query", "") or "").lower()
        offset = int(arguments.get("offset", 0) or 0)
        limit = int(arguments.get("limit", 100) or 100)
        ordinal_limit = _ordinal_limit(idati)
        for ordinal in range(1, ordinal_limit):
            name = ida_typeinf.get_numbered_type_name(idati, ordinal)
            if name:
                if query and query not in name.lower():
                    continue
                tif = ida_typeinf.tinfo_t()
                if not tif.get_named_type(idati, name):
                    continue
                if not (tif.is_struct() or tif.is_union()):
                    continue
                result.append({"ordinal": ordinal, "name": name, "kind": "union" if tif.is_union() else "struct"})
        window = result[offset : offset + limit]
        next_offset = offset + limit if offset + limit < len(result) else None
        return {"data": window, "next_offset": next_offset, "total": len(result)}

    def get_struct(self, arguments: dict[str, Any]) -> dict[str, Any]:
        name = str(arguments["name"])
        tif = ida_typeinf.tinfo_t()
        if not tif.get_named_type(ida_typeinf.get_idati(), name):
            raise RuntimeError(f"Unknown type: {name}")
        payload = {
            "name": name,
            "kind": "union" if tif.is_union() else "struct" if tif.is_struct() else "type",
            "declaration": tif.dstr(),
        }
        if tif.is_udt():
            udt = ida_typeinf.udt_type_data_t()
            if tif.get_udt_details(udt):
                payload["members"] = [
                    {
                        "name": member.name,
                        "offset_bits": int(member.offset),
                        "size_bits": int(member.size),
                        "type": member.type.dstr(),
                        "comment": member.cmt or "",
                    }
                    for member in udt
                    if not member.is_gap()
                ]
        return payload

    def set_comment(self, arguments: dict[str, Any]) -> dict[str, Any]:
        ea = _parse_address(arguments["address"])
        comment = str(arguments["comment"])
        if not idaapi.set_cmt(ea, comment, False):
            raise RuntimeError(f"Failed to set comment at {hex(ea)}")
        return {"address": hex(ea), "comment": comment}

    def append_comment(self, arguments: dict[str, Any]) -> dict[str, Any]:
        ea = _parse_address(arguments["address"])
        comment = str(arguments["comment"])
        current = idaapi.get_cmt(ea, False) or ""
        merged = comment if not current else f"{current}\n{comment}"
        if not idaapi.set_cmt(ea, merged, False):
            raise RuntimeError(f"Failed to append comment at {hex(ea)}")
        return {"address": hex(ea), "comment": merged}

    def rename(self, arguments: dict[str, Any]) -> dict[str, Any]:
        ea = _parse_address(arguments["address"])
        new_name = str(arguments["name"])
        if not ida_name.set_name(ea, new_name, ida_name.SN_NOCHECK):
            raise RuntimeError(f"Failed to rename {hex(ea)} to {new_name}")
        return {"address": hex(ea), "name": new_name}

    def patch_bytes(self, arguments: dict[str, Any]) -> dict[str, Any]:
        ea = _parse_address(arguments["address"])
        hex_text = str(arguments["hex"]).replace(" ", "")
        patched = bytes.fromhex(hex_text)
        ida_bytes.patch_bytes(ea, patched)
        return {"address": hex(ea), "size": len(patched)}

    def define_function(self, arguments: dict[str, Any]) -> dict[str, Any]:
        ea = _parse_address(arguments["address"])
        if not ida_funcs.add_func(ea):
            raise RuntimeError(f"Failed to define function at {hex(ea)}")
        return {"address": hex(ea)}

    def py_eval(self, arguments: dict[str, Any]) -> dict[str, Any]:
        code = str(arguments["code"])
        return _execute_python(code=code)

    def py_exec_file(self, arguments: dict[str, Any]) -> dict[str, Any]:
        path = Path(str(arguments["path"]))
        code = path.read_text(encoding="utf-8")
        return _execute_python(code=code, file_name=str(path))


def _function_info(ea: int) -> dict[str, Any]:
    func = ida_funcs.get_func(ea)
    if not func:
        raise RuntimeError(f"No function found at {hex(ea)}")
    return {
        "address": hex(func.start_ea),
        "name": ida_funcs.get_func_name(func.start_ea),
        "size": func.end_ea - func.start_ea,
    }


def _collect_import_rows(query: str) -> list[dict[str, Any]]:
    items = []
    for idx in range(ida_nalt.get_import_module_qty()):
        module_name = ida_nalt.get_import_module_name(idx) or "<unnamed>"

        def callback(ea, name, ordinal):
            symbol = name or f"#{ordinal}"
            if query and query not in symbol.lower() and query not in module_name.lower():
                return True
            items.append({"address": hex(ea), "name": symbol, "module": module_name})
            return True

        ida_nalt.enum_import_names(idx, callback)
    return items


def _collect_string_rows(*, query: str, min_length: int) -> list[dict[str, Any]]:
    items = []
    for item in idautils.Strings():
        text = str(item)
        if len(text) < min_length:
            continue
        if query and query not in text.lower():
            continue
        items.append({"address": hex(item.ea), "text": text, "length": len(text)})
    return items


def _ordinal_limit(idati) -> int:
    if hasattr(ida_typeinf, "get_ordinal_limit"):
        return int(ida_typeinf.get_ordinal_limit(idati))
    if hasattr(ida_typeinf, "get_ordinal_count"):
        return int(ida_typeinf.get_ordinal_count()) + 1
    if hasattr(ida_typeinf, "get_ordinal_qty"):
        return int(ida_typeinf.get_ordinal_qty(idati))
    raise RuntimeError("IDA type enumeration API is unavailable")


def _xref_row(frm: int, to: int, xref_type: int) -> dict[str, Any]:
    row = {
        "from": hex(frm),
        "to": hex(to),
        "type": int(xref_type),
    }
    from_func = ida_funcs.get_func(frm)
    if from_func:
        row["from_func_address"] = hex(from_func.start_ea)
        row["from_func_name"] = ida_funcs.get_func_name(from_func.start_ea)
    to_func = ida_funcs.get_func(to)
    if to_func:
        row["to_func_address"] = hex(to_func.start_ea)
        row["to_func_name"] = ida_funcs.get_func_name(to_func.start_ea)
    return row


def _execute_python(code: str, file_name: str = "<string>") -> dict[str, Any]:
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = stdout_capture, stderr_capture
    exec_globals = {
        "__builtins__": __builtins__,
        "__name__": "__main__",
        "__file__": file_name,
        "idaapi": idaapi,
        "idc": idc,
        "idautils": idautils,
        "ida_auto": ida_auto,
        "ida_bytes": ida_bytes,
        "ida_funcs": ida_funcs,
        "ida_hexrays": ida_hexrays,
        "ida_kernwin": ida_kernwin,
        "ida_loader": ida_loader,
        "ida_nalt": ida_nalt,
        "ida_name": ida_name,
        "ida_segment": ida_segment,
        "ida_typeinf": ida_typeinf,
        "ida_xref": ida_xref,
    }
    result_value = ""
    try:
        tree = ast.parse(code)
        if len(tree.body) == 1 and isinstance(tree.body[0], ast.Expr):
            result_value = repr(eval(code, exec_globals))
        else:
            exec(compile(tree, file_name, "exec"), exec_globals)
            if "result" in exec_globals:
                result_value = repr(exec_globals["result"])
    except Exception:
        traceback.print_exc()
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
    return {
        "result": result_value,
        "stdout": stdout_capture.getvalue(),
        "stderr": stderr_capture.getvalue(),
    }


def _advertised_ipv4_hosts() -> list[str]:
    result = ["127.0.0.1"]
    try:
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            udp.connect(("8.8.8.8", 80))
            candidate = udp.getsockname()[0]
            if candidate and candidate not in result:
                result.append(candidate)
        finally:
            udp.close()
    except OSError:
        pass

    try:
        for entry in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET, socket.SOCK_STREAM):
            candidate = entry[4][0]
            if candidate and candidate not in result:
                result.append(candidate)
    except OSError:
        pass
    return result


def ida_idaapi_get_procname() -> str:
    try:
        return idaapi.get_idp_name()
    except Exception:
        return idaapi.get_inf_structure().procname


class IdaProSkillBridgePlugin(idaapi.plugin_t):  # pragma: no cover - IDA runtime only
    flags = idaapi.PLUGIN_KEEP
    comment = "ida-pro-skill local bridge"
    help = "Starts the ida-pro-skill local HTTP bridge"
    wanted_name = "ida-pro-skill"
    wanted_hotkey = ""

    def __init__(self):
        super().__init__()
        self.bridge = BridgeServer()

    def init(self):
        try:
            self.bridge.start()
            ida_kernwin.msg(
                f"[ida-pro-skill] bridge started on {LISTEN_HOST}:{self.bridge.port} "
                f"(hosts: {', '.join(_advertised_ipv4_hosts())})\n"
            )
            return idaapi.PLUGIN_KEEP
        except Exception as exc:
            ida_kernwin.msg(f"[ida-pro-skill] failed to start bridge: {exc}\n")
            return idaapi.PLUGIN_SKIP

    def run(self, arg):
        ida_kernwin.msg(
            f"[ida-pro-skill] active on {LISTEN_HOST}:{self.bridge.port} "
            f"(hosts: {', '.join(_advertised_ipv4_hosts())})\n"
        )

    def term(self):
        self.bridge.stop()
