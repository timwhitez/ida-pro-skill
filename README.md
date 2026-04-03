# ida-pro-skill

## Overview / 简介

`ida-pro-skill` is an open-source, skill-first IDA Pro integration for Codex,
Claude Code, and OpenCode. It lets AI agents work against a live IDA database
through a local skill and a thin IDA plugin bridge, without requiring
client-side MCP setup.

`ida-pro-skill` 是一个面向 Codex、Claude Code 和 OpenCode 的开源
IDA Pro Skill 集成项目。它通过本地 skill 和轻量 IDA 插件桥接，让 AI
代理直接对接正在运行的 IDA 数据库，而不要求用户先配置客户端 MCP。

## Project Notes / 项目说明

- This project was developed with Codex
- It references and learned from
  [`mrexodia/ida-pro-mcp`](https://github.com/mrexodia/ida-pro-mcp)
- This repository ships a skill-first integration rather than an MCP-first
  client setup

- 当前项目由 Codex 开发
- 实现思路参考并借鉴了
  [`mrexodia/ida-pro-mcp`](https://github.com/mrexodia/ida-pro-mcp)
- 当前仓库提供的是 skill-first 集成，而不是以 MCP 客户端配置为中心的形态

## Features / 特性

- Skill installation for Codex, Claude Code, and OpenCode
- Thin IDA plugin exposing a local HTTP JSON bridge
- Stdlib-only runtime path
- Agent-friendly short commands
- WSL-aware discovery for Windows-hosted IDA sessions
- Built-in support for metadata, entrypoints, functions, callers, imports,
  strings, xrefs, globals, decompilation, disassembly, structs, renames,
  comments, byte patches, function creation, and explicit IDAPython fallback

- 支持安装到 Codex、Claude Code、OpenCode
- 轻量 IDA 插件，本地暴露 HTTP JSON bridge
- 运行时仅依赖 Python 标准库
- 更适合代理调用的短命令界面
- 支持 WSL 到 Windows IDA 的实例发现
- 内置支持元数据、入口点、函数、调用者、导入、字符串、xref、全局变量、
  反编译、反汇编、结构体、重命名、注释、补丁、函数定义，以及显式回退到
  IDAPython

## Repository Layout / 仓库结构

The public repository layout intentionally stays minimal.
公开仓库结构刻意保持极简。

- `skills/ida-pro-skill/`
- `plugin/`
- root `install.sh` / 根目录 `install.sh`

Inside `skills/ida-pro-skill/`:
`skills/ida-pro-skill/` 内包含：

- `SKILL.md`
- `references/`
- `scripts/run_cli.py`
- `ida_pro_skill/`

## Requirements / 环境要求

- IDA Pro with IDAPython enabled
- Local `python3` or `python`
- One of: Codex, Claude Code, OpenCode

- 安装了 IDAPython 的 IDA Pro
- 本地可用的 `python3` 或 `python`
- 以下客户端之一：Codex、Claude Code、OpenCode

## Installation / 安装

Install into all supported clients:
安装到全部支持的客户端：

```bash
./install.sh
```

Install and automatically copy the plugin into a user-provided IDA plugins
directory:
安装并自动复制 plugin 到用户自己指定的 IDA plugins 目录：

```bash
./install.sh --ida-plugin-dir "/path/to/your/ida/plugins"
```

Notes:
注意：

- `--ida-plugin-dir` has no default value; you must pass your own real IDA
  plugins directory
- In WSL, automatic plugin copy may fail if the target directory is a protected
  Windows path
- Even if automatic plugin copy fails, the skill installation still completes
  and the script continues to print the manual copy and activation steps

- `--ida-plugin-dir` 没有默认值，必须由用户传入自己的真实 IDA plugins
  目录
- 在 WSL 下，如果目标目录位于 Windows 受保护路径，自动复制 plugin 可能因
  权限失败
- 即使自动复制失败，skill 仍会安装完成，脚本会继续输出手动复制与启用指引

Install only selected clients:
只安装指定客户端：

```bash
./install.sh --targets codex,claude
./install.sh --targets opencode
./install.sh --targets all
```

Current install targets:
当前脚本会安装到：

- Codex: `~/.codex/skills/ida-pro-skill`
- Claude Code: `~/.claude/skills/ida-pro-skill`
- OpenCode: `~/.config/opencode/skills/ida-pro-skill`

Dependency note:
依赖说明：

- The runtime path is stdlib-only
- `install.sh` does not require extra `pip install` steps for normal use

- 正常运行路径只依赖标准库
- `install.sh` 不需要额外执行 `pip install`

## Plugin Deployment / Plugin 复制

If you do not pass `--ida-plugin-dir`, manually copy:
如果没有传 `--ida-plugin-dir`，请手动复制以下内容到真实 IDA plugins 目录：

- `plugin/ida_pro_skill_plugin.py`
- `plugin/ida_pro_skill_plugin_runtime/`

When copying manually, replace the placeholder below with your own real IDA
plugins directory.
手动复制时，请把下面的占位符替换为你自己的真实 IDA plugins 目录。

```bash
cp plugin/ida_pro_skill_plugin.py "/path/to/your/ida/plugins/"
cp -R plugin/ida_pro_skill_plugin_runtime "/path/to/your/ida/plugins/"
```

## Plugin Activation / Plugin 启用

After copying the plugin:
复制完成后：

1. Restart IDA
2. Open any database
3. Check the Output window for a line like:
   `[ida-pro-skill] bridge started on ...`
4. Optionally verify from:
   `Edit -> Plugins -> ida-pro-skill`

1. 重启 IDA
2. 打开任意数据库
3. 在 Output 窗口确认类似日志：
   `[ida-pro-skill] bridge started on ...`
4. 如需手工确认，可在菜单中查看：
   `Edit -> Plugins -> ida-pro-skill`

The plugin starts during IDA plugin initialization. The menu item is mainly for
manual confirmation.
这个插件会在 IDA 插件初始化时自动启动，菜单项更多用于状态确认。

Default security behavior:
默认安全行为：

- The plugin defaults to `REMOTE_ACCESS = False`
- Even when the bridge listens on `0.0.0.0`, it only allows localhost and this
  machine's local WSL or Windows addresses by default
- If you intentionally want external machines to connect, edit
  `plugin/ida_pro_skill_plugin.py`, set `REMOTE_ACCESS = True`, recopy the
  plugin, and restart IDA

- plugin 默认使用 `REMOTE_ACCESS = False`
- 即使 bridge 监听在 `0.0.0.0`，默认也只允许本机和本机 WSL 发起访问
- 如果你明确需要让其他机器访问，请先编辑 `plugin/ida_pro_skill_plugin.py`，
  将 `REMOTE_ACCESS` 改为 `True`，再重新复制并重启 IDA

## First Verification / 首次验证

After the plugin is active, start with:
插件启动后，建议先执行：

```bash
PYTHONPATH=skills/ida-pro-skill python3 -m ida_pro_skill ida list-instances
PYTHONPATH=skills/ida-pro-skill python3 -m ida_pro_skill ida metadata
PYTHONPATH=skills/ida-pro-skill python3 -m ida_pro_skill ida tools
```

This repository was re-validated against larger live IDA databases, including:
本仓库已经基于更大的 live IDA 数据库做过真实回归，覆盖了：

- instance discovery / 实例发现
- metadata
- tool manifest
- entrypoints / 入口点
- paged function listing / functions 分页
- imports / import-callers
- strings
- `py-eval --stdin`
- `structs --query`
- `struct GUID`
- `decompile DllGetClassObject`

## Usage Examples / 使用示例

```bash
python3 skills/ida-pro-skill/scripts/run_cli.py doctor
python3 skills/ida-pro-skill/scripts/run_cli.py ida list-instances
python3 skills/ida-pro-skill/scripts/run_cli.py ida metadata
python3 skills/ida-pro-skill/scripts/run_cli.py ida cursor
python3 skills/ida-pro-skill/scripts/run_cli.py ida selection
python3 skills/ida-pro-skill/scripts/run_cli.py ida tools
python3 skills/ida-pro-skill/scripts/run_cli.py ida functions --limit 20
python3 skills/ida-pro-skill/scripts/run_cli.py ida import-callers LoadLibraryExW
python3 skills/ida-pro-skill/scripts/run_cli.py ida string-xrefs kernel32.dll
python3 skills/ida-pro-skill/scripts/run_cli.py ida decompile 0x401000
python3 skills/ida-pro-skill/scripts/run_cli.py ida structs --query GUID --limit 10
python3 skills/ida-pro-skill/scripts/run_cli.py ida struct GUID
printf 'print(hex(0x401000))\n' | python3 skills/ida-pro-skill/scripts/run_cli.py ida py-eval --stdin
```

## Runtime Notes / 运行时说明

- WSL is supported
- When Windows IDA is not reachable via `127.0.0.1`, the client can use the
  bridge's advertised host candidates
- Tool calls reuse the selected or sole discovered instance when possible,
  instead of forcing a new health probe every time
- Heavy bridge calls such as `decompile`, `disassemble`, and `py-eval` are best
  used serially

- 支持 WSL
- 当 Windows IDA 无法通过 `127.0.0.1` 访问时，客户端会尝试 bridge 广播的
  host candidates
- 在可能的情况下，工具调用会复用已选中或唯一发现的实例，而不是每次强制
  新做一次 health probe
- `decompile`、`disassemble`、`py-eval` 这类重操作最好串行执行

## Troubleshooting / 故障排查

Start with:
优先看：

- `skills/ida-pro-skill/references/troubleshooting.md`

Common checks:
常见检查项：

- `PYTHONPATH=skills/ida-pro-skill python3 -m ida_pro_skill ida list-instances`
- confirm the plugin was copied into the real IDA plugins directory
- confirm IDA was restarted after copying
- confirm the Output window shows the bridge startup log

- 确认 plugin 已复制到真实 IDA plugins 目录
- 确认复制后已重启 IDA
- 确认 Output 窗口能看到 bridge 启动日志

## Development / 开发

Private development verification remains under `spec/` and does not affect the
public repository layout.
私有开发验证保留在 `spec/`，不影响公开结构。

```bash
python3 -m unittest discover -s spec/tests -v
PYTHONPATH=skills/ida-pro-skill python3 -m ida_pro_skill doctor
```

## Safety / 安全说明

- The default workflow is static analysis only
- Python execution inside IDA is higher risk than built-in bridge tools
- The plugin defaults to `REMOTE_ACCESS = False`, which keeps `0.0.0.0`
  reachable for localhost and local WSL use without opening the bridge to other
  machines by default
- Users remain responsible for legal, licensing, and policy compliance

- 默认工作流仅面向静态分析
- 在 IDA 内执行 Python 明显高于内置 bridge 工具的风险级别
- plugin 默认使用 `REMOTE_ACCESS = False`；这意味着即使监听在 `0.0.0.0`，
  也只对本机和本机 WSL 保持可达，而不会默认对其他机器开放
- 用户仍需自行承担二进制分析中的法律、许可和策略合规责任

## License / 许可证

MIT. See [LICENSE](LICENSE).
