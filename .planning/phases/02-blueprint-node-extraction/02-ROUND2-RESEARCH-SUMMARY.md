# Phase 2: 蓝图节点提取 — 第二轮研究总结

**Created:** 2026-05-18
**Scope:** CUE4Parse 编译验证、UE 5.7/5.8 兼容性、虚幻盒子分析、UnrealBridge Skill、C++ 工具可行性、uasset_read 项目分析

---

## 研究概览

| 研究方向 | 结论 | 状态 |
|----------|------|------|
| uasset_read 项目 | 中高复杂度，可借鉴模块设计 | ✅ 完成 |
| 剪贴板方案 (ExportNodesToText) | 需 C++ 插件包装，用户不倾向 | ✅ 完成 |
| CUE4Parse-Python | 已编译验证，支持 UE 5.7/5.8 | ✅ 完成 |
| 虚幻盒子 (ue5box.com) | 商业产品，具体实现未公开 | ✅ 完成 |
| C++ 独立工具 | UnrealEd 构建守卫阻止，不可行 | ✅ 完成 |
| C# 方案对比 (CUE4Parse vs UAssetAPI) | CUE4Parse 更优，已编译验证 | ✅ 完成 |
| UE 5.7/5.8 兼容性验证 | CUE4Parse 完整支持，27 天前有修复 | ✅ 完成 |
| UnrealBridge Skill | 编辑器内自动化工具，互补但非替代 | ✅ 完成 |

---

## 核心发现

### 1. CUE4Parse 编译验证

```
✅ .NET 8.0 编译通过
✅ 0 错误, 0 警告
✅ 内置 UEdGraphNode/UEdGraphPin 解析类
✅ 支持 NodePosX/NodePosY (通过 Properties 访问)
✅ 支持 PinName/Direction/PinType/LinkedTo
️ UE5+ cooked 文件需要 .usmap 映射文件
```

### 2. UE 版本兼容性

| 工具 | UE 5.6 | UE 5.7 | UE 5.8 |
|------|--------|--------|--------|
| CUE4Parse | ✅ | ✅ | ✅ (27 天前修复) |
| UAssetAPI | ✅ | ✅ | ❌ |

### 3. 方案对比

| 方案 | 需要 UE | 实施时间 | 数据完整度 | 维护成本 |
|------|---------|----------|-----------|----------|
| 现有 Python API | ✅ 编辑器 | 已完成 | 节点类型 ✅ | 低 |
| CUE4Parse CLI |  无 | 2-4 天 | 坐标/引脚 ✅ | 中 |
| UE 源码抽取 | ✅ 引擎编译环境 | 1-2 周 | 100% | 高 |
| C++ 独立工具 | ✅ UE SDK | 1-2 周 | 100% | 高 (构建守卫阻止) |

---

## 推荐方案

**混合方案：现有 Python API + CUE4Parse CLI**

```
C# CLI (CUE4Parse) → JSON stdout → Python subprocess → 结构化数据
```

**优势：**
- 无需 UE 编辑器
- 无需 UE 插件
- 已编译验证
- 支持 UE 5.7/5.8
- 2-4 天可完成集成

**风险：**
- UE5+ cooked 文件需要 `.usmap` 映射文件
- `BP_FirstPersonCharacter.uasset` 如果是 uncooked 项目源文件，可能不需要

---

## 详细报告

所有研究详情见：
- `02-ALTERNATIVE-PATHWAYS-RESEARCH.md` — 方向 9-15（第二轮研究）
- `02-VALIDATION.md` — Wave 3 验证结果 + 推荐方案
- `ROADMAP.md` — 项目整体进度

---

**研究日期:** 2026-05-18
**状态:** 第二轮研究完成，等待决策进入 Phase 2 Wave 4
