# Phase 2: 蓝图节点提取 — 上下文

**Gathered:** 2026-05-18
**Status:** Ready for planning

## Phase Boundary

从已加载的 Blueprint 资产中提取 EventGraph 的完整结构，包括：
- 节点列表（类型、名称、函数引用）
- 每个节点的引脚定义（PinId、PinName、PinType、Direction、LinkedTo）
- 节点间连线关系（执行流和数据连接）
- 节点画布坐标（NodePosX、NodePosY）

**不包含**：输出格式化（Phase 3）或 CLI（Phase 4）。Phase 2 只负责数据提取，输出为 Python 字典结构，便于后续格式化。

## Implementation Decisions

### 节点提取方法
- **D-01:** 使用 UE Python API（`unreal.EdGraphNode` 标准接口）获取节点属性。稳定可靠，优先使用官方接口。
- **D-02:** EventGraph 定位沿用 Phase 1 的 `unreal.BlueprintEditorLibrary.find_event_graph(bp)`。

### 数据模型
- **D-03:** 使用 Python 字典结构表示节点和引脚数据，与 Phase 3 JSON 输出格式一致。简单灵活，便于后续格式化。
- **D-04:** 所有节点类型使用统一字段模型，特定字段按类型填充。缺失字段自然为 None，简化模型复杂度。

### 连线存储
- **D-05:** LinkedTo 作为 Pin 的内嵌属性：`pin['linked_to'] = [(node_name, pin_id), ...]`。与参考文本格式一致，直接反映 Pin 的连接状态。

### Pin 结构
- **D-06:** PinType 字段完整提取所有子字段（PinCategory、PinSubCategory、PinSubCategoryObject、PinValueType、ContainerType、bIsReference 等）。与参考文本一致，完整反映类型信息。
- **D-07:** SubPin（拆分引脚，如 Vector2D 的 X/Y）作为嵌套子 Pin 表示，保留 ParentPin 关系。
- **D-08:** Pin 字段完整提取：PinId、PinName、PinType、Direction、LinkedTo、PersistentGuid、bHidden、bNotConnectable、bDefaultValueIsReadOnly、bAdvancedView、bOrphanedPin 等。

### GUID 处理
- **D-09:** GUID 值（NodeGuid、PinId、PersistentGuid）直接使用 UE 返回的原始值（32 字符十六进制）。不转换格式，保持与 UE 一致。

### 缺失字段处理
- **D-10:** 无法提取的字段设置为 None，保持字段完整性。便于后续分析判断字段是否可提取。

### JSON 结构
- **D-11:** 输出结构以 nodes 为主：顶层 `nodes` 数组 → 每个 node 包含 `pins` 数组 → pin 内嵌 `linked_to` 列表。与 Phase 3 OUT-02 需求一致。

### 错误恢复
- **D-12:** 单个节点提取失败时跳过并记录警告，继续提取其他节点。最大程度获取数据。

## Canonical References

**下游智能体在规划或实现前必须阅读以下内容。**

### 阶段需求
- `.planning/REQUIREMENTS.md` — PARSE-03, PARSE-04, PARSE-05, PARSE-06（Phase 2 需求）
- `.planning/ROADMAP.md` — Phase 2 目标和成功标准

### UE 参考文档
- `蓝图节点文本参考.md` — UE 编辑器复制的节点文本格式，关键字段和结构的参考样本
- `UnrealEditor_uasset加载流程.md` — UE 加载管线文档

### UE 源码
- `E:\Develop\lib\UnrealEngine\Engine\Source\Runtime\CoreUObject\Private\UObject\LinkerLoad.cpp` — FLinkerLoad 核心实现（274KB）

### 项目上下文
- `.planning/PROJECT.md` — 项目概述和关键决策
- `.planning/phases/01-ue-headless-bridge/01-CONTEXT.md` — Phase 1 决策（继承）
- `.planning/codebase/ARCHITECTURE.md` — 目标架构

## Existing Code Insights

### Reusable Assets
- `scripts/ue_extract.py` — Phase 1 已实现 Blueprint 加载和 EventGraph 定位，可扩展提取逻辑
- `scripts/controller.py` — 外部控制器，UE 无头启动机制已验证
- `temp/ue_config.json` — 引擎路径缓存，避免重复扫描

### Established Patterns
- 脚本传递方式：`-ExecutePythonScript=path/to/script.py --output temp/result.json`
- 输出采集：UE 内嵌脚本写入 JSON 文件，外部脚本读取
- 引擎路径检测：缓存 → 注册表 → 已知路径 → 用户指定（D-08）

### Integration Points
- Phase 2 扩展 `ue_extract.py`，在 `detect_asset_type()` 后添加节点提取逻辑
- 输出文件沿用 `temp/result.json`（或扩展为更详细的 JSON 结构）

## Specific Ideas

- 输出 JSON 结构应便于后续 Phase 3 格式化为 MD 文本和结构化 JSON
- 节点提取时优先参考 `蓝图节点文本参考.md` 中的完整节点示例，确保字段覆盖
- 考虑节点提取的完整度验证：对比提取的节点数量与 UE API 返回的 `node_count`

## Deferred Ideas

None — discussion stayed within phase scope

---

*Phase: 02-蓝图节点提取*
*Context gathered: 2026-05-18*