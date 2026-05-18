---
phase: 02-blueprint-node-extraction
plan: 02
wave: 2
subsystem: node extraction
tags: [implementation, python, ue-api]
dependency_graph:
  requires: [02-01]
  provides: [node_utils.py implementation]
  affects: [ue_extract.py]
tech_stack:
  added:
    - unreal.EdGraphNode reflection
    - unreal.EdGraphPin reflection
    - FEdGraphPinType structure
    - FMemberReference structure
  patterns:
    - node traversal with exception handling (D-12)
    - SubPin recursive extraction (D-07)
    - LinkedTo immediate conversion (T-02-03)
    - GUID formatting (T-02-04)
key_files:
  created: []
  modified:
    - scripts/node_utils.py (401 lines, 8 functions)
decisions:
  - D-04: unified field model, missing fields = None
  - D-05: LinkedTo as Pin embedded attribute
  - D-06: PinType complete extraction (11 fields)
  - D-07: SubPin nested in parent's sub_pins
  - D-08: Pin complete field extraction
  - D-09: GUID as 32-char hex (no hyphens)
  - D-10: unextractable fields = None
  - D-12: single node failure = skip + warning
metrics:
  duration: 5 min
  tasks_completed: 3
  files_modified: 1
  lines_added: 243
  lines_removed: 22
  commit_hash: 0849ee4
  completed_date: 2026-05-18
---

# Phase 2 Plan 02 Wave 2: Node Utils Implementation Summary

**One-liner:** 实现了 node_utils.py 中 8 个辅助函数的完整逻辑，包括节点遍历、引脚提取、SubPin 递归处理、LinkedTo 连线转换和 GUID 格式化。

## Completed Tasks

### Task 1: 实现 extract_nodes() 和 extract_single_node()

**实现内容：**
- `extract_nodes()`: 遍历 `event_graph.nodes`，对每个节点调用 `extract_single_node()`
- D-12 异常处理：单个节点提取失败时跳过，记录 warning，继续处理其他节点
- `extract_single_node()` 提取属性：`node_class`、`node_name`、`node_pos_x/y`、`node_guid`
- K2Node_CallFunction 特殊处理：调用 `extract_function_reference()`
- EdGraphNode_Comment 特殊处理：提取 `node_comment` 属性

**验证结果：**
```
def extract_nodes: line 15 ✓
def extract_single_node: line 59 ✓
event_graph.nodes: line 42 ✓
node.get_class().get_name(): line 76 ✓
node.node_pos_x: line 78 ✓
```

### Task 2: 实现 extract_pins() 和 extract_single_pin()

**实现内容：**
- `extract_pins()`: 遍历 `node.pins`，跳过 `parent_pin != None` 的 SubPin（D-07）
- `extract_single_pin()` 提取属性：`pin_id`、`pin_name`、`direction`、`pin_type`、`linked_to`
- 所有 `b_*` 标志字段：`b_hidden`、`b_not_connectable`、`b_advanced_view`、`b_orphaned_pin` 等
- SubPin 递归处理：嵌套在父 Pin 的 `sub_pins` 字段中

**验证结果：**
```
def extract_pins: line 119 ✓
def extract_single_pin: line 167 ✓
pin.parent_pin: line 149 ✓
pin.pin_id: line 181 ✓
pin.sub_pins: line 206 ✓
```

### Task 3: 实现 extract_pin_type()、extract_linked_to()、extract_function_reference() 和 format_guid()

**实现内容：**
- `extract_pin_type()`: 提取 11 个子字段（pin_category、container_type、b_is_reference 等）
- `extract_linked_to()`: 转换为 `(node_name, pin_id)` 格式（T-02-03 安全缓解）
- `extract_function_reference()`: 提取 FMemberReference 结构（member_name、member_parent、b_self_context）
- `format_guid()`: 移除连字符，转为大写（T-02-04 安全缓解）

**验证结果：**
```
def extract_pin_type: line 224 ✓
def extract_linked_to: line 301 ✓
def extract_function_reference: line 334 ✓
def format_guid: line 374 ✓
pin_type.pin_category: line 248 ✓
pin.linked_to: line 319 ✓
func_ref.member_name: line 361 ✓
guid_str.replace: line 397 ✓
```

## Key Implementation Details

### 节点遍历（D-12 异常捕获）
```python
for node in event_graph.nodes:
    try:
        node_data = extract_single_node(node)
        if node_data is not None:
            nodes.append(node_data)
    except Exception as e:
        unreal.log_warning(f"[Phase2] 节点提取失败 '{node_name}': {e}")
```

### SubPin 处理（D-07）
```python
for pin in node.pins:
    if pin.parent_pin is not None:
        continue  # Skip SubPins in main iteration

    # SubPin 递归处理
    if hasattr(pin, 'sub_pins') and len(pin.sub_pins) > 0:
        pin_data['sub_pins'] = [...]  # 递归提取
```

### LinkedTo 转换（T-02-03）
```python
for linked_pin in pin.linked_to:
    connection = {
        'node_name': linked_pin.get_owning_node().get_fname().to_string(),
        'pin_id': format_guid(linked_pin.pin_id),
    }
```

### GUID 格式化（T-02-04）
```python
def format_guid(guid):
    guid_str = str(guid)
    return guid_str.replace('-', '').upper()
```

## Deviations from Plan

**None** — 计划按预期执行，所有实现符合 RESEARCH.md 代码模式和决策文档。

## Threat Model Compliance

| Threat ID | Mitigation | Status |
|-----------|------------|--------|
| T-02-02 | D-12 单节点异常捕获，跳过继续处理 | ✓ 实现完成 |
| T-02-03 | LinkedTo 立即转换为 (node_name, pin_id) | ✓ 实现完成 |
| T-02-04 | GUID 移除连字符转大写 | ✓ 实现完成 |

## Success Criteria Verification

| Criteria | Status |
|----------|--------|
| node_utils.py 包含 8 个函数完整实现 | ✓ 401 行 |
| extract_nodes() 返回节点列表 | ✓ 包含所有字段 |
| extract_single_pin() 返回引脚字典 | ✓ 包含 pin_id、pin_name、direction、pin_type、linked_to |
| SubPin 正确嵌套在 sub_pins | ✓ parent_pin 检查 + 递归处理 |
| K2Node_CallFunction 包含 function_reference | ✓ isinstance 检查 + 提取 |
| 单节点失败跳过继续 | ✓ D-12 异常捕获 |
| GUID 格式化为 32 字符 | ✓ 移除连字符转大写 |

## Self-Check

**验证命令执行结果：**
```bash
# Task 1 验证
grep -n "def extract_nodes" scripts/node_utils.py      # 15 ✓
grep -n "event_graph.nodes" scripts/node_utils.py      # 42 ✓
grep -n "node.node_pos_x" scripts/node_utils.py        # 78 ✓

# Task 2 验证
grep -n "pin.parent_pin" scripts/node_utils.py         # 149 ✓
grep -n "pin.sub_pins" scripts/node_utils.py           # 206 ✓

# Task 3 验证
grep -n "pin_type.pin_category" scripts/node_utils.py  # 248 ✓
grep -n "guid_str.replace" scripts/node_utils.py       # 397 ✓
```

**文件行数验证：**
- `scripts/node_utils.py`: 401 行 (> min_lines: 200) ✓

**提交验证：**
- Commit hash: `0849ee4` ✓
- Message: `feat(02-02): implement all node_utils.py helper functions` ✓

## Self-Check: PASSED

所有验证项通过。