# Phase 2 Plan 03: 端到端节点提取验证 — 摘要

**Plan:** 02-03
**Status:** PARTIAL SUCCESS
**Duration:** ~20 分钟（包含 API 探索时间）

## 执行摘要

Wave 3 端到端验证部分成功。成功提取了 9 个节点（包含类型和名称），但发现了 UE 5.7 Python API 的关键限制：
- `EdGraph.Nodes` 属性是 **protected**，无法直接访问
- `EdGraphNode` 的关键属性（NodePosX、NodePosY、NodeGuid、Pins）均未公开暴露

## 关键发现

### API 探索结果

通过大量 API 探索，发现：

| 属性 | 假设（RESEARCH.md） | 实际状态 | 解决方案 |
|------|---------------------|----------|----------|
| EdGraph.Nodes | 直接访问 | **protected**，不可读 | 使用 `unreal.ObjectIterator(unreal.EdGraphNode)` |
| NodePosX/NodePosY | snake_case: `node_pos_x` | 未暴露 | 无法获取，返回 0 |
| NodeGuid | `node_guid` | 未暴露 | 无法获取，返回 null |
| Pins | `node.pins` | 未暴露 | 无法获取，返回空列表 |
| get_fname() | `to_string()` 方法 | 应使用 `str()` | 已修复 |

### 成功提取的数据

```json
{
  "node_class": "K2Node_CallFunction",
  "node_name": "K2Node_CallFunction_10",
  "node_pos_x": 0,
  "node_pos_y": 0,
  "node_guid": null,
  "pins": [],
  "function_reference": null
}
```

提取的节点类型：
- `EdGraphNode_Comment` (1)
- `K2Node_CallFunction` (4)
- `K2Node_Event` (4)

## 实现变更

### 核心修改

1. **node_utils.py:extract_nodes()** — 使用 ObjectIterator 替代直接属性访问
2. **node_utils.py:get_node_attr()** — 新增辅助函数，尝试多种属性名
3. **node_utils.py:extract_single_node()** — 使用 get_node_attr 处理坐标和 GUID
4. **node_utils.py:extract_pins()** — 使用 get_node_attr 获取 Pins 数组
5. **ue_extract.py** — 添加脚本目录到 Python path（修复 ModuleNotFoundError）

### FName 转 string 问题

RESEARCH.md 假设 `fname.to_string()` 方法存在，实际应使用 `str(fname)`。已修复所有相关代码。

## 验证结果

### 成功项
- ✅ 节点类型提取（node_class）
- ✅ 节点名称提取（node_name）
- ✅ ObjectIterator 遍历 EdGraphNode
- ✅ 模块导入修复

### 未完成项
- ❌ 节点坐标提取（NodePosX/NodePosY 未暴露）
- ❌ 节点 GUID 提取（NodeGuid 未暴露）
- ❌ 引脚提取（Pins 未暴露）
- ❌ 连线信息提取（依赖 Pins）
- ❌ 函数引用提取（依赖 function_reference 属性）

## 下一步建议

### 方案 A：继续研究 API
- 探索蓝图编辑器工具（可能需要打开编辑器窗口）
- 研究 C++ 插件扩展 Python API
- 查找 UE 5.7 新增的公开方法

### 方案 B：转向二进制解析
- 直接解析 .uasset 文件的二进制结构
- 实现 FLinkerLoad 的 Python 版本
- 复杂度显著提升，超出 Phase 2 原定范围

### 方案 C：更新 RESEARCH.md 并记录限制
- 更新研究文档反映实际 API 状态
- Phase 2 交付部分功能（节点类型和名称）
- Phase 3 考虑替代方案

## Commits

- `841552f`: feat(02-01): add node_utils.py skeleton
- `32d73e8`: feat(02-01): extend ue_extract.py
- `0849ee4`: feat(02-02): implement node_utils.py helper functions
- `5d26372`: feat(02-03): implement node extraction via ObjectIterator

---

*Wave 3 完成：节点类型和名称提取成功，关键属性因 API 限制未能获取*