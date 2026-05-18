---
phase: 02-blueprint-node-extraction
plan: 01
subsystem: node-extraction
tags: [python, skeleton, interface, ue-api]
dependencies:
  requires: [phase-01]
  provides: [node_utils-interface, extraction-entry-point]
  affects: [scripts/ue_extract.py]
tech-stack:
  added: [scripts/node_utils.py]
  patterns: [interface-first, skeleton-module]
key-files:
  created:
    - path: scripts/node_utils.py
      purpose: 节点/引脚提取辅助函数模块骨架
  modified:
    - path: scripts/ue_extract.py
      purpose: 添加节点提取入口调用
decisions:
  - D-01: 使用 UE Python API 标准接口获取节点属性
  - D-05: LinkedTo 作为 Pin 内嵌属性
  - D-06: PinType 字段完整提取所有子字段
  - D-07: SubPin 作为嵌套子 Pin 表示
  - D-09: GUID 直接使用 UE 返回的原始值
  - D-12: 单个节点提取失败时跳过并记录警告
metrics:
  duration: 3m
  completed_date: 2026-05-18
  tasks_completed: 3
  files_created: 1
  files_modified: 1
  commits: 2
---

# Phase 2 Plan 01: 接口骨架创建 Summary

创建辅助函数模块 `node_utils.py`，定义节点和引脚提取的完整接口契约。扩展 `ue_extract.py`，在 EventGraph 定位后添加节点提取入口调用，为 Wave 2 实现提供清晰的函数签名和数据结构约定。

## One-liner

定义 8 个节点提取辅助函数的接口契约，并在 ue_extract.py 中集成节点提取入口点。

## Completed Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | 创建 node_utils.py 辅助函数模块骨架 | 841552f | scripts/node_utils.py |
| 2 | 扩展 ue_extract.py 添加节点提取入口 | 32d73e8 | scripts/ue_extract.py |
| 3 | 验证模块导入和函数调用可执行 | - | (验证任务) |

## Key Deliverables

### node_utils.py (新建)

包含 8 个辅助函数签名：

1. **extract_nodes(event_graph)** — 从 EventGraph 提取所有节点信息
2. **extract_single_node(node)** — 提取单个节点的完整信息
3. **extract_pins(node)** — 从节点提取所有顶层引脚信息
4. **extract_single_pin(pin)** — 提取单个引脚的完整信息
5. **extract_pin_type(pin_type)** — 提取 FEdGraphPinType 的完整结构（9 子字段）
6. **extract_linked_to(pin)** — 提取引脚的连接目标列表
7. **extract_function_reference(node)** — 提取 K2Node_CallFunction 的函数引用信息
8. **format_guid(guid)** — 格式化 UE FGuid 为标准字符串

每个函数包含：
- 完整的类型提示
- 详细的 docstring（用途、参数、返回格式）
- 占位返回值（空列表/None/空字符串）

### ue_extract.py (扩展)

新增功能：
- 导入 `node_utils` 模块（`extract_nodes`, `format_guid`）
- 在 Blueprint 分支 EventGraph 检测后添加节点提取入口
- 输出 `nodes` 数组、`node_extraction_status`、`extracted_node_count`
- 保留原有 `node_count` 用于对比验证
- 添加节点提取状态日志输出

## Deviations from Plan

None — plan executed exactly as written.

## Verification Results

### Task 1 Verification
```
All 8 function signatures defined
```

### Task 2 Verification
```
13:from node_utils import extract_nodes, format_guid
81:                result['nodes'] = extract_nodes(event_graph)
82:                result['node_extraction_status'] = 'success'
86:                result['node_extraction_status'] = 'failed'
110:    extraction_status = result.get('node_extraction_status', 'not_attempted')
```

### Task 3 Verification
```
[PASS] node_utils.py is valid Python
[PASS] All 8 function signatures defined
[PASS] ue_extract.py contains node_utils import
[PASS] ue_extract.py contains node extraction entry point
[PASS] ue_extract.py is valid Python
[PASS] node_utils imports unreal module (required for type hints)
[PASS] All verifications passed
```

## Integration Notes

- `unreal` 模块仅在 UE Editor Python 环境中可用
- 完整集成测试需要在 UE Editor 内运行
- Wave 2 将实现所有 8 个辅助函数的完整逻辑

## Threat Surface

无新增安全相关暴露面。模块为内部 Python 代码，无外部 API、网络或认证操作。

## Self-Check: PASSED

- [x] scripts/node_utils.py 存在
- [x] scripts/ue_extract.py 存在
- [x] Commit 841552f 存在
- [x] Commit 32d73e8 存在

1. 实现 `extract_nodes()` — 遍历 event_graph.nodes
2. 实现 `extract_single_node()` — 提取节点属性
3. 实现 `extract_pins()` — 遍历 node.pins
4. 实现 `extract_single_pin()` — 提取引脚属性
5. 实现 `extract_pin_type()` — 提取 PinType 9 子字段
6. 实现 `extract_linked_to()` — 提取连线目标
7. 实现 `extract_function_reference()` — 提取函数引用
8. 实现 `format_guid()` — 格式化 GUID 字符串