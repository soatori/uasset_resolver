# Phase 2: 蓝图节点提取 — Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-18
**Phase:** 02-蓝图节点提取
**Areas discussed:** 节点提取方法, 数据模型, 连线存储, 节点类型处理, PinType提取, SubPin处理, Pin字段范围, GUID处理, 缺失字段处理, JSON结构, 错误恢复

---

## 节点提取方法

| Option | Description | Selected |
|--------|-------------|----------|
| UE Python API（推荐） | 使用 unreal.EdGraphNode 的标准接口获取节点属性。稳定可靠，但某些内部字段可能无法直接访问。 | ✓ |
| 内部属性访问 | 绕过 API 直接访问节点的内部属性（如通过 get_editor_property()）。能获取更完整数据，但可能依赖 UE 版本。 | |
| 混合方式 | API 获取标准字段 + 内部属性补充缺失字段。平衡稳定性和完整性。 | |

**User's choice:** UE Python API（推荐）
**Notes:** None

---

## 数据模型

| Option | Description | Selected |
|--------|-------------|----------|
| 字典结构（推荐） | 直接使用 Python dict，与 Phase 3 JSON 输出格式一致。简单灵活，便于后续格式化。 | ✓ |
| 类对象模型 | 定义 Node/Pin/Connection 类，封装属性和验证逻辑。更严谨但增加转换开销。 | |
| dataclass 模型 | 使用 Python dataclass，既有类型提示又有 dict() 方法。中间方案，兼顾结构和灵活性。 | |

**User's choice:** 字典结构（推荐）
**Notes:** None

---

## 连线存储

| Option | Description | Selected |
|--------|-------------|----------|
| Pin 内嵌（推荐） | LinkedTo 作为 Pin 的属性，如 pin['linked_to'] = [(node_name, pin_id), ...]。与参考文本格式一致，直接反映 Pin 的连接状态。 | ✓ |
| 独立连接列表 | 单独的 connections 数组，每条连接包含 (source_node, source_pin, target_node, target_pin)。便于构建拓扑图，但与文本格式结构不同。 | |
| 双向表示 | Pin 内嵌 + 独立连接列表同时生成。最完整但可能冗余。 | |

**User's choice:** Pin 内嵌（推荐）
**Notes:** None

---

## 节点类型处理

| Option | Description | Selected |
|--------|-------------|----------|
| 统一字段模型（推荐） | 所有节点共用一套字段字典，特定字段按类型填充。简单直接，缺失字段自然为 None。 | ✓ |
| 类型分离模型 | 不同节点类型有独立的 Python 类/结构（CallFunctionNode、EventNode 等）。更清晰但增加模型复杂度。 | |
| 通用 + 扩展字段 | 基础字段 + type_specific 字典存放类型专属数据。灵活但层次更深。 | |

**User's choice:** 统一字段模型（推荐）
**Notes:** None

---

## PinType 提取

| Option | Description | Selected |
|--------|-------------|----------|
| 完整提取（推荐） | 提取 PinType 的所有字段（PinCategory、PinSubCategory、PinSubCategoryObject、PinValueType、ContainerType、bIsReference 等）。与参考文本一致，完整但可能大量空值。 | ✓ |
| 精简提取 | 只提取非空/非默认的字段。精简输出，但后续分析需处理缺失字段。 | |
| 核心字段 | 只提取 PinCategory + PinSubCategory（核心分类），忽略其他复杂字段。最小化结构，适用于简化分析。 | |

**User's choice:** 完整提取（推荐）
**Notes:** None

---

## SubPin 处理

| Option | Description | Selected |
|--------|-------------|----------|
| 嵌套子 Pin（推荐） | 检测 SubPins 字段，将拆分 Pin（如 Vector2D 的 X/Y）作为嵌套子 Pin 表示。与参考文本结构一致，完整反映 Pin 拆分。 | ✓ |
| 忽略拆分 | 忽略 SubPins 关系，所有 Pin 平铺。简化结构，但丢失拆分信息。 | |
| 平铺 + ParentPin 标记 | 检测 SubPins 但标记 ParentPin 字段而不嵌套。保持层级关系但扁平存储。 | |

**User's choice:** 嵌套子 Pin（推荐）
**Notes:** None

---

## Pin 字段范围

| Option | Description | Selected |
|--------|-------------|----------|
| 完整字段（推荐） | 提取所有可访问的字段（包括 bHidden、bNotConnectable、bDefaultValueIsReadOnly、bAdvancedView 等）。完整但输出较大。 | ✓ |
| 核心语义 | 只提取语义核心字段（PinId、PinName、PinType、Direction、LinkedTo）。精简输出，便于快速分析。 | |
| 核心 + 元数据 | 核心语义 + 可选的元数据字段（PersistentGuid、bOrphanedPin 等）。平衡完整度和输出大小。 | |

**User's choice:** 完整字段（推荐）
**Notes:** None

---

## GUID 处理

| Option | Description | Selected |
|--------|-------------|----------|
| 直接输出（推荐） | 直接使用 UE 返回的 GUID 值（32 字符十六进制）。与参考文本一致，便于交叉验证。 | ✓ |
| 格式化转换 | 将 GUID 转换为统一格式（如添加连字符的标准 UUID 格式）。便于外部工具处理。 | |
| Node 级别 | 仅在 Node 级别保留 NodeGuid，Pin 级别不提取 PinId/PersistentGuid。简化结构，依赖 Node 唯一标识。 | |

**User's choice:** 直接输出（推荐）
**Notes:** None

---

## 缺失字段处理

| Option | Description | Selected |
|--------|-------------|----------|
| None 填充（推荐） | 缺失/无法访问的字段设置为 None。保持字段完整性，便于后续分析判断字段是否可提取。 | ✓ |
| 省略字段 | 完全省略缺失字段，输出 JSON 中不包含该 key。精简输出，但后续处理需处理字段缺失情况。 | |
| 默认值填充 | 缺失字段用默认值填充（如空字符串、0、False）。保证所有字段有值，但可能误导后续分析。 | |

**User's choice:** None 填充（推荐）
**Notes:** None

---

## JSON 结构

| Option | Description | Selected |
|--------|-------------|----------|
| nodes 为主（推荐） | 顶层 nodes 数组，每个 node 包含 pins 数组，pin 内嵌 linked_to 列表。与 Phase 3 OUT-02 需求一致，便于后续 JSON 输出。 | ✓ |
| 三层分离 | 包含 nodes、pins、connections 三个顶层数组，引用通过 ID/GUID 关联。三元分离结构，便于构建拓扑图，但与 Phase 3 OUT-02 需求不一致。 | |
| nodes + connections | nodes 数组 + connections 数组（pins 作为 node 内嵌）。平衡嵌套和分离，便于可视化处理。 | |

**User's choice:** nodes 为主（推荐）
**Notes:** None

---

## 错误恢复

| Option | Description | Selected |
|--------|-------------|----------|
| 终止提取 | 提取失败时抛出异常，终止流程。确保数据完整性，但可能因小问题导致整体失败。 | |
| 跳过 + 警告（推荐） | 失败节点跳过并记录警告，继续提取其他节点。最大程度获取数据，但可能不完整。 | ✓ |
| 占位 + 继续 | 失败节点输出占位数据（如 class=Unknown），继续提取。不中断流程，但需后续处理占位节点。 | |

**User's choice:** 跳过 + 警告（推荐）
**Notes:** None

---

## Claude's Discretion

None — user selected all recommended options

## Deferred Ideas

None — discussion stayed within phase scope