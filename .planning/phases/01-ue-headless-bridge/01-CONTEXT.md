# Phase 1: UE Headless Bridge - Context

**Gathered:** 2026-05-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Python 工具能启动 UE 5.7 无头模式，加载指定 `.uasset` 文件，确认其是否为 Blueprint 资产。UE 进程退出后不残留窗口。交付物：一个可执行的 Python 脚本 + 一个 UE 内嵌 Python 脚本，能完成 "加载文件 → 判断类型 → 输出结果" 的最小闭环。

</domain>

<decisions>
## Implementation Decisions

### 脚本传递方式
- **D-01:** 使用外部 .py 文件，通过 UE 命令行参数 `-ExecutePythonScript=path/to/script.py` 传入。脚本放在项目 `scripts/ue_extract.py`，便于迭代调试。

### 输出采集策略
- **D-02:** UE 内嵌脚本将结果写入 `temp/` 目录下的 JSON 文件，外部 Python 控制脚本读取该文件。不依赖 stdout 管道（UE 日志系统不可靠）。
- **D-03:** 临时文件路径由外部脚本传入参数指定，格式：`--output temp/result.json`。

### Blueprint 识别策略
- **D-04:** 检查加载后的包中是否包含 `UBlueprintGeneratedClass` 类型的对象来判定 Blueprint。
- **D-05:** 架构需保留可扩展性——未来支持其他资产类型（材质、动画等）时，类型检测逻辑应可插拔。

### 错误处理 & 超时策略
- **D-06:** Phase 1 使用固定超时（60-120 秒），超时后 `subprocess.kill()`。只需报告成功/失败，不做详细诊断。
- **D-07:** 后续 Phase 可演进为智能超时 + 重试（监控输出关键词判断状态）。

### 引擎路径检测
- **D-08:** 混合模式：自动扫描 Windows 注册表（`HKLM\SOFTWARE\EpicGames\Unreal Engine`）和已知安装路径 → 失败后提示用户通过 CLI 参数 `--ue-path` 手动指定。
- **D-09:** 首次检测成功后，将引擎路径缓存到项目配置文件中，避免重复扫描。

### Claude's Discretion
- 临时文件的 JSON 结构由实现者决定，只要能被外部脚本正确读取即可。
- UE 内嵌脚本中的 `print` 输出格式无特殊要求，主要用于调试日志。

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Requirements
- `.planning/REQUIREMENTS.md` — PARSE-01, PARSE-02（Phase 1 需求）
- `.planning/ROADMAP.md` — Phase 1 目标和成功标准

### UE Reference Docs
- `UnrealEditor_uasset加载流程.md` — UE 加载管线文档，理解 LoadPackage → FLinkerLoad 流程
- `蓝图节点文本参考.md` — 蓝图节点文本序列化格式参考（后续 Phase 使用）

### UE Source Code
- `E:\Develop\lib\UnrealEngine\Engine\Source\Runtime\CoreUObject\Private\UObject\LinkerLoad.cpp` — FLinkerLoad 核心实现（274KB）

### Project Context
- `.planning/PROJECT.md` — 项目概述和关键决策
- `.planning/codebase/ARCHITECTURE.md` — 目标架构
- `.planning/codebase/CONCERNS.md` — 风险分析（Binary Format Complexity, Version Compatibility）

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- 暂无应用代码。项目目前只有测试资产（`BP_FirstPersonCharacter.uasset`）和参考文档。

### Established Patterns
- 无既有模式——从零构建。

### Integration Points
- UE 5.7 安装路径：`D:\Program Files\Epic Games\Engine\UE_5.7`
- UE 编辑器源码：`E:\Develop\lib\UnrealEngine\`
- 测试资产：`BP_FirstPersonCharacter.uasset`（56KB，真实蓝图文件）

</code_context>

<specifics>
## Specific Ideas

- 外部 Python 脚本文件应放在项目根目录下的 `scripts/` 目录中，便于版本控制。
- 临时输出文件统一放在 `temp/` 目录（已在 `.gitignore` 中排除）。
- 引擎路径缓存建议放在 `temp/ue_config.json` 或类似位置。

</specifics>

<deferred>
## Deferred Ideas

- 智能超时 + 重试（D-07）——后续 Phase 实现
- 非 Blueprint 资产类型支持（D-05 扩展性）—— v2 需求，已列在 REQUIREMENTS.md v2 中

None — discussion stayed within phase scope

</deferred>

---

*Phase: 1-UE Headless Bridge*
*Context gathered: 2026-05-18*
