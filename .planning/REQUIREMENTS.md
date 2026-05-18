---
title: "Requirements"
created: 2026-05-18
---

# Requirements

## v1 Requirements

### Parser Core (PARSE)

- [ ] **PARSE-01**: Python 工具能启动 UE 5.7 无头模式（`-unattended -NullRHI`）并执行 Python 脚本
- [ ] **PARSE-02**: 能加载指定 `.uasset` 文件并识别是否为 Blueprint 资产
- [ ] **PARSE-03**: 提取 Blueprint EventGraph 的节点列表（节点类型、名称、函数引用）
- [ ] **PARSE-04**: 提取每个节点的引脚定义（PinId、PinName、PinType、Direction、LinkedTo）
- [ ] **PARSE-05**: 提取节点间的连线关系（执行流和数据连接）
- [ ] **PARSE-06**: 提取节点画布坐标（NodePosX / NodePosY）

### Output Format (OUT)

- [ ] **OUT-01**: 输出类 UE 编辑器文本格式（`Begin Object Class=... Name=... End Object` 块）
- [ ] **OUT-02**: 输出结构化 JSON，包含 nodes/pins/connections 三层嵌套结构
- [ ] **OUT-03**: 通过命令行参数选择输出格式（`--format md` / `--format json`）

### Loading Strategy (LOAD)

- [ ] **LOAD-01**: 支持直接加载裸 `.uasset` 文件路径
- [ ] **LOAD-02**: 如果裸文件加载失败，提示用户指定 UE 项目的 Content 目录

### Verification (VERIFY)

- [ ] **VERIFY-01**: 对 `BP_FirstPersonCharacter.uasset` 的解析结果与 `蓝图节点文本参考.md` 中的编辑器输出进行对比验证

## v2 Requirements (Deferred)

- [ ] 批量解析（递归目录扫描）
- [ ] 非 Blueprint 资产解析（材质、动画、DataTable 等）
- [ ] 跨版本支持（UE 5.4 ~ 5.8）
- [ ] JSON 输出添加节点语义分析（自动识别节点类型：事件/函数/变量/流程控制）

## Out of Scope

- 蓝图节点编辑/修改 — 只读解析工具
- 实时编辑器集成（不需要 TCP bridge 或插件）
- 非 .uasset 格式（.umap、.pak 等）

## Traceability

| Requirement | Phase | Plan | Status |
|-------------|-------|------|--------|
| PARSE-01 | Phase 1 | TBD | Pending |
| PARSE-02 | Phase 1 | TBD | Pending |
| PARSE-03 | Phase 2 | TBD | Pending |
| PARSE-04 | Phase 2 | TBD | Pending |
| PARSE-05 | Phase 2 | TBD | Pending |
| PARSE-06 | Phase 2 | TBD | Pending |
| OUT-01 | Phase 3 | TBD | Pending |
| OUT-02 | Phase 3 | TBD | Pending |
| OUT-03 | Phase 4 | TBD | Pending |
| LOAD-01 | Phase 4 | TBD | Pending |
| LOAD-02 | Phase 4 | TBD | Pending |
| VERIFY-01 | Phase 4 | TBD | Pending |

## Definition of Done

1. 对 `BP_FirstPersonCharacter.uasset` 的解析输出包含所有 EventGraph 节点
2. 输出格式与 UE 编辑器复制的文本结构一致（关键字段对齐）
3. JSON 输出可被独立脚本验证结构完整性
4. 不需要手动打开 UE 编辑器窗口
