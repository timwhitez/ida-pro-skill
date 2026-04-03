# ida-pro-skill

## 中文

`ida-pro-skill` 是一个面向 Codex、Claude Code 和 OpenCode 的开源
IDA Pro Skill 集成项目。

它通过一个本地 Skill 和一个轻量 IDA 插件桥接，让 AI 代理直接对接正在
运行的 IDA 数据库，而不要求用户先配置 MCP。

### 特性

- 面向 Codex、Claude Code、OpenCode 的 Skill 安装
- 轻量 IDA 插件，本地暴露 HTTP JSON bridge
- 运行时仅依赖 Python 标准库
- 更适合代理调用的短命令界面
- 支持 WSL 到 Windows IDA 的实例发现
- 内置支持：
  - 元数据、入口点、函数、调用者、导入、字符串、xref、全局变量
  - 反编译与反汇编
  - 结构体列表和结构体成员详情
  - 重命名、注释、补丁、函数定义
  - 必要时显式退回 IDAPython

### 公开仓库结构

本仓库的公开结构刻意保持极简：

- `skills/ida-pro-skill/`
- `plugin/`
- 根目录 `install.sh`

其中 `skills/ida-pro-skill/` 内包含：

- `SKILL.md`
- `references/`
- `scripts/run_cli.py`
- `ida_pro_skill/`

### 环境要求

- 安装了 IDAPython 的 IDA Pro
- 本地可用的 `python3` 或 `python`
- 以下客户端之一：
  - Codex
  - Claude Code
  - OpenCode

### 安装

安装到全部支持的客户端：

```bash
./install.sh
```

安装并自动复制 plugin 到指定 IDA 插件目录：

```bash
./install.sh --ida-plugin-dir "/mnt/c/Program Files/IDA Professional 9.1/plugins"
```

只安装指定客户端：

```bash
./install.sh --targets codex,claude
./install.sh --targets opencode
./install.sh --targets all
```

当前脚本会安装到：

- Codex: `~/.codex/skills/ida-pro-skill`
- Claude Code: `~/.claude/skills/ida-pro-skill`
- OpenCode: `~/.config/opencode/skills/ida-pro-skill`

依赖说明：

- 正常运行路径只依赖标准库
- `install.sh` 不需要额外执行 `pip install`

### Plugin 复制

如果没有传 `--ida-plugin-dir`，请手动复制以下内容到真实 IDA plugins 目录：

- `plugin/ida_pro_skill_plugin.py`
- `plugin/ida_pro_skill_plugin_runtime/`

WSL 到 Windows 的典型示例：

```bash
cp plugin/ida_pro_skill_plugin.py "/mnt/c/Program Files/IDA Professional 9.1/plugins/"
cp -R plugin/ida_pro_skill_plugin_runtime "/mnt/c/Program Files/IDA Professional 9.1/plugins/"
```

### Plugin 启用

复制完成后：

1. 重启 IDA
2. 打开任意数据库
3. 在 Output 窗口确认类似日志：
   `[ida-pro-skill] bridge started on ...`
4. 如需手工确认，可在菜单中查看：
   `Edit -> Plugins -> ida-pro-skill`

这个插件会在 IDA 插件初始化时自动启动，菜单项更多用于状态确认。

### 首次验证

插件启动后，建议先执行：

```bash
PYTHONPATH=skills/ida-pro-skill python3 -m ida_pro_skill ida list-instances
PYTHONPATH=skills/ida-pro-skill python3 -m ida_pro_skill ida metadata
PYTHONPATH=skills/ida-pro-skill python3 -m ida_pro_skill ida tools
```

本仓库已经基于更大的 live DLL 数据库再次做过真实回归，覆盖了：

- 实例发现
- metadata
- tool manifest
- entrypoints
- functions 分页
- imports / import-callers
- strings
- `py-eval --stdin`
- `structs --query`
- `struct GUID`
- `decompile DllGetClassObject`

### 使用示例

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
python3 skills/ida-pro-skill/scripts/run_cli.py ida decompile 0x1802092a0
python3 skills/ida-pro-skill/scripts/run_cli.py ida structs --query GUID --limit 10
python3 skills/ida-pro-skill/scripts/run_cli.py ida struct GUID
printf 'print(hex(0x401000))\n' | python3 skills/ida-pro-skill/scripts/run_cli.py ida py-eval --stdin
```

### 运行时说明

- 支持 WSL
- 当 Windows IDA 无法通过 `127.0.0.1` 访问时，客户端会尝试 bridge
  广播的 host candidates
- 在可能的情况下，工具调用会复用已选中或唯一发现的实例，而不是每次强制
  新做一次 health probe
- `decompile`、`disassemble`、`py-eval` 这类重操作最好串行执行

### 故障排查

优先看：

- `skills/ida-pro-skill/references/troubleshooting.md`

常见检查项：

- `PYTHONPATH=skills/ida-pro-skill python3 -m ida_pro_skill ida list-instances`
- 确认 plugin 已复制到真实 IDA plugins 目录
- 确认复制后已重启 IDA
- 确认 Output 窗口能看到 bridge 启动日志

### 开发

私有开发验证保留在 `spec/`，不影响公开结构：

```bash
python3 -m unittest discover -s spec/tests -v
PYTHONPATH=skills/ida-pro-skill python3 -m ida_pro_skill doctor
```

### 安全说明

- 默认工作流仅面向静态分析
- 在 IDA 内执行 Python 明显高于内置 bridge 工具的风险级别
- 用户仍需自行承担二进制分析中的法律、许可和策略合规责任

## English

`ida-pro-skill` is an open-source, skill-first IDA Pro integration for Codex,
Claude Code, and OpenCode.

It allows AI agents to work against a live IDA database through a local skill
and a thin IDA plugin bridge, without requiring client-side MCP setup.

### Features

- Skill installation for Codex, Claude Code, and OpenCode
- Thin IDA plugin exposing a local HTTP JSON bridge
- Stdlib-only runtime path
- Agent-friendly short commands
- WSL-aware discovery for Windows-hosted IDA sessions
- Built-in support for:
  - metadata, entrypoints, functions, callers, imports, strings, xrefs, globals
  - decompilation and disassembly
  - struct listing and struct member details
  - rename, comment, patch, and define-function flows
  - explicit IDAPython fallback when required

### Public Repository Layout

The public repository layout intentionally stays minimal:

- `skills/ida-pro-skill/`
- `plugin/`
- root `install.sh`

Inside `skills/ida-pro-skill/`:

- `SKILL.md`
- `references/`
- `scripts/run_cli.py`
- `ida_pro_skill/`

### Requirements

- IDA Pro with IDAPython enabled
- Local `python3` or `python`
- One of:
  - Codex
  - Claude Code
  - OpenCode

### Installation

Install into all supported clients:

```bash
./install.sh
```

Install and automatically copy the plugin into a known IDA plugins directory:

```bash
./install.sh --ida-plugin-dir "/mnt/c/Program Files/IDA Professional 9.1/plugins"
```

Install only selected clients:

```bash
./install.sh --targets codex,claude
./install.sh --targets opencode
./install.sh --targets all
```

Current install targets:

- Codex: `~/.codex/skills/ida-pro-skill`
- Claude Code: `~/.claude/skills/ida-pro-skill`
- OpenCode: `~/.config/opencode/skills/ida-pro-skill`

Dependency note:

- The runtime path is stdlib-only.
- `install.sh` does not require extra `pip install` steps for normal use.

### Plugin Deployment

If you do not pass `--ida-plugin-dir`, manually copy:

- `plugin/ida_pro_skill_plugin.py`
- `plugin/ida_pro_skill_plugin_runtime/`

Typical WSL to Windows example:

```bash
cp plugin/ida_pro_skill_plugin.py "/mnt/c/Program Files/IDA Professional 9.1/plugins/"
cp -R plugin/ida_pro_skill_plugin_runtime "/mnt/c/Program Files/IDA Professional 9.1/plugins/"
```

### Plugin Enable

After copying the plugin:

1. Restart IDA
2. Open any database
3. Check the Output window for:
   `[ida-pro-skill] bridge started on ...`
4. Optionally verify from:
   `Edit -> Plugins -> ida-pro-skill`

The plugin starts during IDA plugin initialization. The menu item is mainly for
manual confirmation.

### First Verification

After the plugin is active:

```bash
PYTHONPATH=skills/ida-pro-skill python3 -m ida_pro_skill ida list-instances
PYTHONPATH=skills/ida-pro-skill python3 -m ida_pro_skill ida metadata
PYTHONPATH=skills/ida-pro-skill python3 -m ida_pro_skill ida tools
```

This repository was re-validated again against a larger live DLL database,
including:

- instance discovery
- metadata
- tool manifest
- entrypoints
- paged function listing
- imports / import-callers
- strings
- `py-eval --stdin`
- `structs --query`
- `struct GUID`
- `decompile DllGetClassObject`

### Usage Examples

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
python3 skills/ida-pro-skill/scripts/run_cli.py ida decompile 0x1802092a0
python3 skills/ida-pro-skill/scripts/run_cli.py ida structs --query GUID --limit 10
python3 skills/ida-pro-skill/scripts/run_cli.py ida struct GUID
printf 'print(hex(0x401000))\n' | python3 skills/ida-pro-skill/scripts/run_cli.py ida py-eval --stdin
```

### Runtime Notes

- WSL is supported
- When Windows IDA is not reachable via `127.0.0.1`, the client can use the
  bridge's advertised host candidates
- Tool calls reuse the selected or sole discovered instance when possible,
  instead of forcing a new health probe every time
- Heavy bridge calls such as `decompile`, `disassemble`, and `py-eval` are best
  used serially

### Troubleshooting

Start with:

- `skills/ida-pro-skill/references/troubleshooting.md`

Common checks:

- `PYTHONPATH=skills/ida-pro-skill python3 -m ida_pro_skill ida list-instances`
- confirm the plugin was copied into the real IDA plugins directory
- confirm IDA was restarted after copying
- confirm the Output window shows the bridge startup log

### Development

Private development verification remains under `spec/`:

```bash
python3 -m unittest discover -s spec/tests -v
PYTHONPATH=skills/ida-pro-skill python3 -m ida_pro_skill doctor
```

### Safety

- The default workflow is static analysis only
- Python execution inside IDA is higher risk than built-in bridge tools
- Users remain responsible for legal, licensing, and policy compliance

## License

MIT. See [LICENSE](LICENSE).
