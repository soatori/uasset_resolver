---
title: "uasset_resolver"
created: 2026-05-18
updated: 2026-05-18
---

# uasset_resolver

## What This Is

Unreal Engine `.uasset` 文件解析工具 — 通过 Python 控制 UE 5.7 无头模式加载 Blueprint 资产，提取 EventGraph 的节点结构，输出为人类可读的文本和结构化 JSON。

## Context

AI 代理需要在不打开 UE 编辑器的情况下理解蓝图文件（`.uasset`）。`.uasset` 是 UE 内部二进制格式，直接反序列化复杂度极高（`FLinkerLoad` 约 274KB C++ 代码）。

**技术路径**：Python 启动 UE5Editor.exe 无头模式（`-unattended -NullRHI`）→ 通过 UE 内置 Python 加载资产 → 提取蓝图事件图节点 → 输出到 JSON/MD 文件。

**参考材料**：
- `BP_FirstPersonCharacter.uasset` — 真实测试文件（56KB）
- `UnrealEditor_uasset加载流程.md` — UE 加载管线文档
- `蓝图节点文本参考.md` — UE 编辑器中复制的蓝图节点文本（输出格式参考）
- `测试对照C++类/` — 对应的 C++ 参考类
- UE 5.7 源码：`E:\Develop\lib\UnrealEngine\`

## Core Value

**一条命令读取 .uasset 文件，输出蓝图节点的结构化表示（文本+JSON），无需打开 UE 编辑器。**

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] 解析 `.uasset` 文件，提取 Blueprint EventGraph 节点信息
- [ ] 输出格式 1：类 UE 编辑器文本格式（Begin Object...End Object）
- [ ] 输出格式 2：结构化 JSON，对 AI 代理友好
- [ ] 加载策略：优先直接加载裸文件，失败则要求指定 UE 项目内容目录
- [ ] 提取节点类型、函数引用、引脚定义和连线关系

### Out of Scope

- 蓝图节点编辑/修改 — 只读解析
- 非 Blueprint 资产（纹理、材质、动画等）— 专注 Blueprint
- 跨版本兼容 — 初始仅支持 UE 5.7

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python 控制 UE 无头调用 | `.uasset` 是二进制，纯 Python 复刻 FLinkerLoad 工程量过大且易错 | Python 启动 UE 无头模式加载，提取数据 |
| 双格式输出（MD + JSON） | MD 用于对照 UE 编辑器格式验证，JSON 用于程序化消费 | 先实现 MD 文本对齐，再提供 JSON |
| 优先参考 UE 源码 | 理解 `FLinkerLoad` 加载管线是正确解析的基础 | 以 `LinkerLoad.h/cpp` 为技术参考 |
| 不依赖 UnrealBridge | UnrealBridge 需要编辑器已运行，与无头模式目标不符 | 直接使用 UE 命令行 + Python 脚本 |

## Tech Stack

- **Python 3.9+** — 控制脚本和输出格式化
- **UE 5.7** — 资产加载引擎（`D:\Program Files\Epic Games\Engine\UE_5.7`）
- **UE 内置 Python** — 通过 `-ExecutePythonScript` 在引擎内执行提取逻辑
- **subprocess** — Python 标准库，启动 UE 无头进程

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-18 after initialization*
