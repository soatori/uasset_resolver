# Phase 2: 蓝图节点提取 — 研究勘误

**Created:** 2026-05-18
**Reason:** Wave 3 执行发现原始研究存在关键假设错误
**Supplement:** 参见 `02-API-LIMITATIONS-RESEARCH.md` — Python API 反射机制真实工作原理

## Summary（修订）

**⚠️ 重要发现：原始研究的假设 A1 和 A4 已验证为错误！**

Wave 3 实际测试发现：
- **EdGraphNode 的关键属性（NodePosX、NodePosY、NodeGuid）无法通过 Python API 访问**
- **EdGraphPin 不是 UObject，所有字段均不可通过 Python API 访问**
- **EdGraph.Nodes 属性同样无法访问**

**根本原因：**
1. Python API 只暴露有 `CPF_BlueprintVisible` 标记的 UPROPERTY
2. EdGraphNode 的关键属性使用空 `UPROPERTY()` 标记，无 BlueprintVisible
3. EdGraphPin 不是 UObject，完全没有 UE 反射系统支持

**详细分析：** 参见 `02-API-LIMITATIONS-RESEARCH.md`

---

## Assumptions Log（修订）

| # | Claim | Section | Status | Verification |
|---|-------|---------|--------|--------------|
| A1 | UE Python API 自动暴露所有 EdGraphNode/EdGraphPin 的 UPROPERTY 属性 | Standard Stack | ❌ **错误** | Wave 3 验证：Python API 只暴露有 BlueprintVisible 标记的属性 |
| A2 | FGuid.ToString() 返回 32 字符无连字符格式 | Code Examples | ✅ 正确 | 02-03 端到端验证确认 |
| A3 | NodePosX/NodePosY 在 Python 中为 snake_case | Common Pitfalls | ❌ **错误** | Python API 无法访问这些属性（根本没有暴露） |
| A4 | EdGraph.nodes 属性返回节点数组 | Pattern 1 | ❌ **错误** | Wave 3 验证：Nodes 属性无 BlueprintVisible 标记，不暴露到 Python |

**修正说明：**
- A1 和 A4 基于 UE 源码定义的误导性分析
- 实际 Python API 反射机制要求 BlueprintVisible 标记（参见 PyGenUtil.cpp 第 1608-1612 行）
- EdGraphPin 不是 UObject，完全不暴露（参见 EdGraphPin.h 第 293 行）

---

## Phase Requirements（修订）

| ID | Description | Original Plan | Revised Status |
|----|-------------|---------------|----------------|
| PARSE-03 | 提取 Blueprint EventGraph 的节点列表（节点类型、名称） | EdGraph.nodes 属性 | ❌ **Nodes 属性不可访问** |
| PARSE-04 | 提取每个节点的引脚定义（PinId、PinName、PinType） | EdGraphPin 所有属性 | ❌ **EdGraphPin 不暴露到 Python** |
| PARSE-05 | 提取节点间的连线关系（执行流和数据连接） | EdGraphPin.LinkedTo | ❌ **LinkedTo 不可访问** |
| PARSE-06 | 提取节点画布坐标（NodePosX / NodePosY） | EdGraphNode.NodePosX/NodePosY | ❌ **NodePosX/NodePosY 不可访问** |

**影响评估：**
- Phase 2 的所有核心需求无法通过原始计划实现
- 需要采用替代方案（参见 `02-API-LIMITATIONS-RESEARCH.md` 替代方案评估）

---

## 下一步行动

1. **阅读补充研究：** `02-API-LIMITATIONS-RESEARCH.md`
2. **决策：** 选择替代方案（C++ 插件、开源工具、或调整目标范围）
3. **更新计划：** 根据替代方案重新规划 Wave 4+

---

## Sources

### Primary (HIGH confidence)
- **PyGenUtil.cpp** — Python API 反射机制核心逻辑 [VERIFIED: UE 5.7 源码]
  - `IsScriptExposedProperty()` 函数定义了暴露规则
  - 源码路径：`E:/Develop/lib/UnrealEngine/Engine/Plugins/Experimental/PythonScriptPlugin/Source/PythonScriptPlugin/Private/PyGenUtil.cpp`

- **EdGraphPin.h** — EdGraphPin 类定义 [VERIFIED: UE 5.7 源码]
  - EdGraphPin 不是 UObject（没有 UCLASS 标记）
  - 源码路径：`E:/Develop/lib/UnrealEngine/Engine/Source/Runtime/Engine/Classes/EdGraph/EdGraphPin.h`

- **02-API-LIMITATIONS-RESEARCH.md** — 补充研究 [VERIFIED: 2026-05-18]
  - Python API 反射机制真实工作原理
  - 替代方案评估

### Tertiary (LOW confidence — 需验证)
- 原始研究的假设 A1、A3、A4 已证明错误