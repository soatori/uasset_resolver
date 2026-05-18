---
status: testing
phase: 02b-cue4parse-backend
source: 2B-01-SUMMARY.md, 02B-02-SUMMARY.md, 02B-03-SUMMARY.md
started: 2026-05-18T00:00:00Z
updated: 2026-05-18T00:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: Python 工具能导入 BPExtractor 类并成功调用 extract_to_dict()，返回包含蓝图数据的字典
result: pass

### 2. 节点提取功能验证
expected: 提取的蓝图包含 >= 9 个节点（类型和名称），数据结构符合 BlueprintGraph dataclass 定义
result: pass

### 3. 后端标识验证
expected: 控制器输出 JSON 包含 "backend": "cue4parse" 字段，标识使用 CUE4Parse 后端
result: pass

### 4. 性能指标验证
expected: 节点提取耗时 < 10 秒（378ms 目标），退出码为 0
result: pass

### 5. 统一控制器 --backend 参数
expected: `--backend cue4parse`、`--backend ue-headless`、`--backend auto` 三个选项均可正常工作
result: pass

### 6. 错误处理验证
expected: 传入不存在的 .uasset 文件时，控制器返回退出码 1 并显示清晰错误提示
result: pass

### 7. JSON 输出格式验证
expected: JSON 输出包含 PascalCase "Nodes" 键，且兼容 snake_case "nodes" 读取（向后兼容修复）
result: pass

### 8. 导出到文件功能
expected: 使用 --out 参数可将 JSON 输出保存到指定文件，temp/cue4parse_result.json 结构正确
result: pass

## Summary

total: 8
passed: 8
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]
