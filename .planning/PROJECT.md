---
title: "uasset_resolver"
created: 2026-05-18
updated: 2026-05-19
---

# uasset_resolver

## What This Is

Unreal Engine `.uasset` 文件解析工具 — 通过 CUE4Parse 直接解析二进制文件，提取蓝图事件图节点结构，输出为人类可读的文本和结构化 JSON。**无需启动 UE 编辑器即可读取蓝图。**

AI 代理需要在不打开 UE 编辑器的情况下理解蓝图文件（`.uasset`）。`.uasset` 是 UE 内部二进制格式，直接反序列化复杂度极高（`FLinkerLoad` 约 274KB C++ 代码）。

**技术路径演进：**
- 初始方案：Python 启动 UE5Editor.exe 无头模式 → 通过 UE 内置 Python 加载资产 → 提取 → **发现 API 限制**（NodeGuid、NodePosX/Y、Pins 不可访问）
- 当前方案：CUE4Parse C# 库直接解析 .uasset 二进制文件，不需要 UE 编辑器 → 架构验证成功，提取速度 ~400ms（对比 UE 无头 >60s）

**参考材料：**
- `BP_FirstPersonCharacter.uasset` — 真实测试文件（56KB）
- `UnrealEditor_uasset加载流程.md` — UE 加载管线文档
- `蓝图节点文本参考.md` — UE 编辑器中复制的蓝图节点文本（输出格式参考）
- `测试对照C++类/` — 对应的 C++ 参考类
- UE 5.7 源码：`E:\Develop\lib\UnrealEngine\`

## Core Value

**一条命令读取 .uasset 文件，输出蓝图节点的结构化表示（文本+JSON），无需打开 UE 编辑器。**

## Requirements

### Validated

- ✓ 解析 `.uasset` 文件，提取 Blueprint EventGraph 节点类型/名称 — v0.1.0
- ✓ 输出格式 1：类 UE 编辑器文本格式（Begin Object...End Object）— v0.1.0
- ✓ 输出格式 2：结构化 JSON，对 AI 代理友好（nodes/pins/connections 三级嵌套）— v0.1.0
- ✓ 加载策略：优先直接加载裸文件，失败则要求指定 UE 项目内容目录 — v0.1.0
- ✓ CLI 支持 `--format` 参数选择输出格式 — v0.1.0
- ✓ `--verify` 参数支持交叉验证输出与参考文件 — v0.1.0
- ✓ 启动 UE 5.7 无头模式执行内嵌 Python（备用后端）— v0.1.0
- ✓ 正确识别 Blueprint 资产（备用后端）— v0.1.0

### Active

- [ ] 完整提取引脚定义（PinId/PinName/PinType/Direction）— 需要 .usmap
- [ ] 提取节点间连线关系（LinkedTo）— 需要 .usmap
- [ ] 记录画布坐标（NodePosX/NodePosY）和 NodeGuid — 需要 .usmap

### Out of Scope

- 蓝图节点编辑/修改 — 只读解析
- 非 Blueprint 资产（纹理、材质、动画等）— 专注 Blueprint
- 跨版本兼容 — 初始仅支持 UE 5.7

## Key Decisions

| Decision | Rationale | Outcome | Status |
|----------|-----------|---------|--------|
| Python 控制 UE 无头调用 | `.uasset` 是二进制，纯 Python 复刻 FLinkerLoad 工程量过大且易错 | Phase 1 验证可行，Phase 2 发现 API 限制 → 切换到 CUE4Parse | ✓ 已解决 |
| 双格式输出（MD + JSON） | MD 用于对照 UE 编辑器格式验证，JSON 用于程序化消费 | 实现完成，两种格式满足各自目标 ✓ | ✓ Good |
| 优先参考 UE 源码 | 理解 `FLinkerLoad` 加载管线是正确解析的基础 | 以 `LinkerLoad.h/cpp` 为技术参考，帮助理解 CUE4Parse 工作原理 ✓ | ✓ Good |
| 不依赖 UnrealBridge | UnrealBridge 需要编辑器已运行，与无头模式目标不符 | 直接使用 UE 命令行 + Python 脚本 ✓ | ✓ Good |
| CUE4Parse 替代 UE Python API | UE Python API 不暴露 NodeGuid、NodePosX/Y、Pins | Phase 2B 完成，提取速度从 >60s → ~400ms 提升 150x ✓ | ✓ Good |
| .usmap 映射文件问题暂挂 | UE 5.7 无 GenerateMappingFile 命令let，属性值解析阻塞 | 架构已完成，数据占位正确，等待后续里程碑解决 | ⚠️ Pending |

## Current State (v0.1.0)

- **Shipped:** 2026-05-19
- **Python:** 2524 行代码
- **Tech Stack:** Python 3.9+ + CUE4Parse (.NET 8.0) + UE 5.7 (备用后端)
- **Capability:** 能提取节点类型和名称，缺少坐标/GUID/Pins（.usmap 缺失）
- **Performance:** 12 节点提取 ~400ms (CUE4Parse 后端)
- **Known Issue:** UE 5.7 默认无版本属性格式需要 .usmap 映射文件才能完全解析

## Constraints

- UE 源码引用位置：`E:\Develop\lib\UnrealEngine/`
- 本地 UE 5.7 安装位置：`D:\Program Files\Epic Games\Engine\UE_5.7`
- 所有缓存/临时生成文件统一放在 `temp/` 目录（已 `.gitignore`）

---

*Last updated: 2026-05-19 after v0.1.0 milestone*
