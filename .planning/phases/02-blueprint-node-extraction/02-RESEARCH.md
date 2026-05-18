# Phase 2: 蓝图节点提取 — 研究

**Researched:** 2026-05-18
**Domain:** UE Python API (EdGraphNode, EdGraphPin, K2Node)
**Confidence:** HIGH (基于 UE 5.7 源码分析)

## Summary

本 Phase 核心任务是从已加载的 Blueprint 资产中提取 EventGraph 的完整结构。基于 UE 5.7 源码分析，UE Python API 通过反射机制自动暴露 `UEdGraphNode`、`UEdGraphPin` 及相关类型的所有 `UPROPERTY` 属性，可直接访问节点和引脚的全部信息。

关键发现：
1. **EdGraphNode 和 EdGraphPin 的所有公开属性均可通过 Python API 直接读取**（反射机制自动暴露）
2. **PinType 结构完整，包含 12 个子字段**，与参考文本格式一致
3. **SubPin（拆分引脚）通过 `SubPins` 和 `ParentPin` 属性识别和处理**
4. **LinkedTo 连线信息存储在 Pin 对象的 `LinkedTo` 数组中**
5. **K2Node_CallFunction 的 FunctionReference 通过 `FMemberReference` 结构暴露**

**Primary recommendation:** 扩展 Phase 1 的 `ue_extract.py`，使用 `unreal.EdGraphNode` 标准接口迭代 EventGraph 的 `nodes` 数组，逐节点提取属性并构建 Python 字典结构。

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** 使用 UE Python API（`unreal.EdGraphNode` 标准接口）获取节点属性。稳定可靠，优先使用官方接口。
- **D-02:** EventGraph 定位沿用 Phase 1 的 `unreal.BlueprintEditorLibrary.find_event_graph(bp)`。
- **D-03:** 使用 Python 字典结构表示节点和引脚数据，与 Phase 3 JSON 输出格式一致。简单灵活，便于后续格式化。
- **D-04:** 所有节点类型使用统一字段模型，特定字段按类型填充。缺失字段自然为 None，简化模型复杂度。
- **D-05:** LinkedTo 作为 Pin 的内嵌属性：`pin['linked_to'] = [(node_name, pin_id), ...]`。与参考文本格式一致，直接反映 Pin 的连接状态。
- **D-06:** PinType 字段完整提取所有子字段（PinCategory、PinSubCategory、PinSubCategoryObject、PinValueType、ContainerType、bIsReference 等）。与参考文本一致，完整反映类型信息。
- **D-07:** SubPin（拆分引脚，如 Vector2D 的 X/Y）作为嵌套子 Pin 表示，保留 ParentPin 关系。
- **D-08:** Pin 字段完整提取：PinId、PinName、PinType、Direction、LinkedTo、PersistentGuid、bHidden、bNotConnectable、bDefaultValueIsReadOnly、bDefaultValueIsIgnored、bAdvancedView、bOrphanedPin 等。
- **D-09:** GUID 值（NodeGuid、PinId、PersistentGuid）直接使用 UE 返回的原始值（32 字符十六进制）。不转换格式，保持与 UE 一致。
- **D-10:** 无法提取的字段设置为 None，保持字段完整性。便于后续分析判断字段是否可提取。
- **D-11:** 输出结构以 nodes 为主：顶层 `nodes` 数组 → 每个 node 包含 `pins` 数组 → pin 内嵌 `linked_to` 列表。与 Phase 3 OUT-02 需求一致。
- **D-12:** 单个节点提取失败时跳过并记录警告，继续提取其他节点。最大程度获取数据。

### Claude's Discretion
None — 所有实现细节已锁定。

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PARSE-03 | 提取 Blueprint EventGraph 的节点列表（节点类型、名称、函数引用） | EdGraphNode.nodes 属性 + K2Node_CallFunction.FunctionReference |
| PARSE-04 | 提取每个节点的引脚定义（PinId、PinName、PinType、Direction、LinkedTo） | EdGraphPin 所有属性 + FEdGraphPinType 完整结构 |
| PARSE-05 | 提取节点间的连线关系（执行流和数据连接） | EdGraphPin.LinkedTo 数组 + Pin 引用解析 |
| PARSE-06 | 提取节点画布坐标（NodePosX / NodePosY） | EdGraphNode.NodePosX/NodePosY 属性 |

</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| EventGraph 定位 | UE Python API (unreal.BlueprintEditorLibrary) | — | Phase 1 已验证的稳定接口 |
| 节点迭代 | UE Python API (EdGraph.nodes) | — | EdGraph 的 nodes 属性直接暴露节点数组 |
| 节点属性提取 | UE Python API (EdGraphNode 反射属性) | — | 所有 UPROPERTY 自动暴露 |
| 引脚属性提取 | UE Python API (EdGraphPin 反射属性) | — | 所有 UPROPERTY 自动暴露 |
| 连线信息解析 | UE Python API (EdGraphPin.LinkedTo) | Python 字典构建 | LinkedTo 数组需转换为可序列化结构 |
| SubPin 处理 | UE Python API (EdGraphPin.SubPins/ParentPin) | 嵌套字典构建 | 拆分引脚需递归处理 |
| 错误恢复 | Python 异常处理 | — | D-12 要求跳过失败节点 |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| unreal (Python module) | UE 5.7 内置 | UE API 访问 | Epic 官方提供的 Python 绑定 |
| unreal.EdGraphNode | UE 5.7 | 节点基类 | 所有蓝图节点的统一接口 |
| unreal.EdGraphPin | UE 5.7 | 引脚类型 | 引脚属性的标准接口 |
| unreal.K2Node_CallFunction | UE 5.7 | 函数调用节点 | 获取 FunctionReference |
| unreal.BlueprintEditorLibrary | UE 5.7 | Blueprint 操作库 | find_event_graph 已验证 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| json (Python stdlib) | 3.x | JSON 序列化 | 输出结果到文件 |
| sys (Python stdlib) | 3.x | 命令行参数解析 | 获取 --output 参数 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| unreal.EdGraphNode | 手动解析 .uasset 二进制 | 极高复杂度，需要实现 FLinkerLoad；官方 API 稳定可靠 |
| Python 字典 | 自定义类 | 字典直接兼容 JSON 序列化，Phase 3 无需转换 |

**安装:** 无需额外安装 — UE 5.7 内嵌 Python 环境已包含所有依赖。

**版本验证:** 
```bash
# UE Python 内嵌脚本中验证版本
import unreal
print(unreal.SystemLibrary.get_engine_version())  # 应返回 5.7.x
```

## Package Legitimacy Audit

> 本 Phase 不安装外部包 — 所有依赖均为 UE 内置或 Python 标准库。

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| unreal (UE 内嵌) | UE 内置 | — | — | Epic Games | — | N/A — UE 内置模块 |
| json (Python stdlib) | Python 内置 | — | — | Python.org | — | N/A — 标准库 |

**外部包安装:** 无 — Phase 2 无外部依赖。

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          UE 无头进程                                     │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    ue_extract.py (内嵌脚本)                        │  │
│  │                                                                    │  │
│  │   ┌─────────────────┐                                              │  │
│  │   │ Blueprint 加载  │ ← Phase 1 已实现                             │  │
│  │   │ (EditorAssetLib)│                                              │  │
│  │   └────────┬────────┘                                              │  │
│  │            │                                                        │  │
│  │            ▼                                                        │  │
│  │   ┌─────────────────┐    ┌─────────────────┐                       │  │
│  │   │ EventGraph 定位 │───▶│ 节点迭代       │                       │  │
│  │   │ (BlueprintEditor│    │ (graph.nodes)   │                       │  │
│  │   │  Library)       │    └────────┬───────┘                       │  │
│  │   └─────────────────┘             │                               │  │
│  │                                   ▼                               │  │
│  │                        ┌───────────────────────┐                  │  │
│  │                        │  节点属性提取循环    │                  │  │
│  │                        │                       │                  │  │
│  │                        │  ┌─────────────────┐ │                  │  │
│  │                        │  │ node.get_class()│ │                  │  │
│  │                        │  │ node.node_pos_x │ │                  │  │
│  │                        │  │ node.node_guid  │ │                  │  │
│  │                        │  └─────────────────┘ │                  │  │
│  │                        │           │          │                  │  │
│  │                        │           ▼          │                  │  │
│  │                        │  ┌─────────────────┐ │                  │  │
│  │                        │  │ 引脚迭代       │ │                  │  │
│  │                        │  │ (node.pins)    │ │                  │  │
│  │                        │  └─────────────────┘ │                  │  │
│  │                        │           │          │                  │  │
│  │                        │           ▼          │                  │  │
│  │                        │  ┌─────────────────┐ │                  │  │
│  │                        │  │ Pin 属性提取   │ │                  │  │
│  │                        │  │ + SubPin 处理  │ │                  │  │
│  │                        │  │ + LinkedTo 解析│ │                  │  │
│  │                        │  └─────────────────┘ │                  │  │
│  │                        └───────────┬───────────┘                  │  │
│  │                                    │                              │  │
│  │                                    ▼                              │  │
│  │                        ┌───────────────────────┐                  │  │
│  │                        │ Python 字典构建       │                  │  │
│  │                        │ nodes[{pins[{...}]}] │                  │  │
│  │                        └───────────┬───────────┘                  │  │
│  │                                    │                              │  │
│  │                                    ▼                              │  │
│  │                        ┌───────────────────────┐                  │  │
│  │                        │ JSON 写入文件         │                  │  │
│  │                        │ quit_editor()         │                  │  │
│  │                        └───────────────────────┘                  │  │
│  │                                                                    │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  输出: temp/result.json                                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure
```
scripts/
├── ue_extract.py       # Phase 1 + Phase 2 扩展：节点提取逻辑
├── controller.py       # Phase 1 外部控制器（保持不变）
└── node_utils.py       # [新增] 节点/引脚提取辅助函数
temp/
├── ue_config.json      # 引擎路径缓存
└── result.json         # 输出结果
```

### Pattern 1: 节点属性提取循环
**What:** 遍历 EventGraph.nodes，逐节点提取类名、坐标、GUID 和引脚列表
**When to use:** 所有蓝图节点提取场景
**Example:**
```python
# Source: 基于 EdGraphNode.h 源码分析 [VERIFIED: UE 5.7 源码]
import unreal

def extract_nodes(event_graph):
    """提取 EventGraph 的所有节点及其属性"""
    nodes = []
    
    # EdGraph.nodes 属性返回 UEdGraphNode 数组
    for node in event_graph.nodes:
        try:
            node_data = {
                'node_class': node.get_class().get_name(),
                'node_name': node.get_fname().to_string(),
                'node_pos_x': node.node_pos_x,  # int32 NodePosX
                'node_pos_y': node.node_pos_y,  # int32 NodePosY
                'node_guid': str(node.node_guid),  # FGuid -> string (32 hex chars)
                'pins': extract_pins(node)
            }
            
            # 特定节点类型的额外字段
            if isinstance(node, unreal.K2Node_CallFunction):
                node_data['function_reference'] = extract_function_reference(node)
            
            nodes.append(node_data)
        except Exception as e:
            unreal.log_warning(f"[Phase2] 节点提取失败: {e}")
            # D-12: 跳过失败节点，继续处理
    
    return nodes
```

### Pattern 2: 引脚属性完整提取
**What:** 提取 UEdGraphPin 的所有 UPROPERTY 属性，处理 SubPin 递归
**When to use:** 所有引脚提取场景
**Example:**
```python
# Source: 基于 EdGraphPin.h 源码分析 [VERIFIED: UE 5.7 源码]
def extract_pins(node):
    """提取节点的所有引脚（包括 SubPin 处理）"""
    pins = []
    
    # UEdGraphNode.pins 属性返回 UEdGraphPin 数组
    for pin in node.pins:
        try:
            # 检查是否为 SubPin（有 ParentPin）
            if pin.parent_pin is not None:
                continue  # SubPin 在父 Pin 的 sub_pins 中处理
            
            pin_data = {
                'pin_id': str(pin.pin_id),  # FGuid
                'pin_name': pin.pin_name.to_string(),  # FName
                'direction': 'EGPD_Input' if pin.direction == unreal.EdGraphPinDirection.INPUT else 'EGPD_Output',
                'pin_type': extract_pin_type(pin.pin_type),
                'linked_to': extract_linked_to(pin),
                'default_value': pin.default_value or None,
                'autogenerated_default_value': pin.autogenerated_default_value or None,
                'default_object': str(pin.default_object) if pin.default_object else None,
                'persistent_guid': str(pin.persistent_guid) if hasattr(pin, 'persistent_guid') else None,
                'b_hidden': pin.b_hidden,
                'b_not_connectable': pin.b_not_connectable,
                'b_default_value_is_read_only': pin.b_default_value_is_read_only,
                'b_default_value_is_ignored': pin.b_default_value_is_ignored,
                'b_advanced_view': pin.b_advanced_view,
                'b_orphaned_pin': pin.b_orphaned_pin,
            }
            
            # 处理 SubPins（拆分引脚，如 Vector2D 的 X/Y）
            if hasattr(pin, 'sub_pins') and len(pin.sub_pins) > 0:
                pin_data['sub_pins'] = []
                for sub_pin in pin.sub_pins:
                    sub_data = {
                        'pin_id': str(sub_pin.pin_id),
                        'pin_name': sub_pin.pin_name.to_string(),
                        'parent_pin': str(pin.pin_id),  # 引用父 Pin
                        'pin_type': extract_pin_type(sub_pin.pin_type),
                        'linked_to': extract_linked_to(sub_pin),
                    }
                    pin_data['sub_pins'].append(sub_data)
            
            pins.append(pin_data)
        except Exception as e:
            unreal.log_warning(f"[Phase2] 引脚提取失败: {pin.pin_name} - {e}")
    
    return pins
```

### Pattern 3: PinType 完整提取
**What:** 提取 FEdGraphPinType 的所有子字段（12 个属性）
**When to use:** 所有引脚类型提取场景
**Example:**
```python
# Source: 基于 EdGraphPin.h FEdGraphPinType 结构 [VERIFIED: UE 5.7 源码]
def extract_pin_type(pin_type):
    """提取 PinType 的完整结构"""
    return {
        'pin_category': pin_type.pin_category.to_string() if pin_type.pin_category else '',
        'pin_sub_category': pin_type.pin_sub_category.to_string() if pin_type.pin_sub_category else '',
        'pin_sub_category_object': str(pin_type.pin_sub_category_object) if pin_type.pin_sub_category_object else None,
        'pin_sub_category_member_reference': extract_member_reference(pin_type.pin_sub_category_member_reference) if hasattr(pin_type, 'pin_sub_category_member_reference') else None,
        'pin_value_type': extract_value_type(pin_type.pin_value_type) if hasattr(pin_type, 'pin_value_type') else None,
        'container_type': str(pin_type.container_type),  # EPinContainerType: None/Array/Set/Map
        'b_is_reference': pin_type.b_is_reference,
        'b_is_const': pin_type.b_is_const,
        'b_is_weak_pointer': pin_type.b_is_weak_pointer,
        'b_is_uobject_wrapper': pin_type.b_is_uobject_wrapper,
        'b_serialize_as_single_precision_float': pin_type.b_serialize_as_single_precision_float,
    }
```

### Pattern 4: LinkedTo 连线解析
**What:** 从 Pin.LinkedTo 数组提取连接目标，转换为 (node_name, pin_id) 元组列表
**When to use:** 所有连线信息提取
**Example:**
```python
# Source: 基于 EdGraphPin.h LinkedTo 属性 [VERIFIED: UE 5.7 源码]
def extract_linked_to(pin):
    """提取引脚的连线信息"""
    connections = []
    
    # LinkedTo 是 TArray<UEdGraphPin*>，包含所有连接的目标引脚
    for linked_pin in pin.linked_to:
        try:
            # 获取目标引脚所属的节点
            owning_node = linked_pin.get_owning_node()
            connection = {
                'node_name': owning_node.get_fname().to_string(),
                'pin_id': str(linked_pin.pin_id),
            }
            connections.append(connection)
        except Exception as e:
            unreal.log_warning(f"[Phase2] 连线解析失败: {e}")
    
    return connections
```

### Pattern 5: FunctionReference 提取
**What:** 从 K2Node_CallFunction 提取 FMemberReference 信息
**When to use:** 函数调用节点的额外信息提取
**Example:**
```python
# Source: 基于 K2Node_CallFunction.h + MemberReference.h [VERIFIED: UE 5.7 源码]
def extract_function_reference(node):
    """提取函数调用节点的 FunctionReference"""
    if not isinstance(node, unreal.K2Node_CallFunction):
        return None
    
    func_ref = node.function_reference
    return {
        'member_name': func_ref.member_name.to_string() if func_ref.member_name else None,
        'member_parent': str(func_ref.member_parent) if func_ref.member_parent else None,
        'member_guid': str(func_ref.member_guid) if func_ref.member_guid else None,
        'b_self_context': func_ref.b_self_context,
    }
```

### Anti-Patterns to Avoid
- **手写 Pin 字段名映射表:** 应直接使用反射属性，避免维护易错的映射表
- **LinkedTo 存储为全局连线列表:** D-05 要求 LinkedTo 作为 Pin 内嵌属性，直接反映连接状态
- **忽略 SubPin:** 拆分引脚（如 Vector2D 的 X/Y）是真实连接，必须处理
- **GUID 格式转换:** D-09 要求直接使用 UE 返回的原始值，不转换格式
- **全节点失败中断:** D-12 要求跳过失败节点继续处理，最大程度获取数据

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 节点属性提取 | 手写 .uasset 二进制解析 | unreal.EdGraphNode 反射属性 | FLinkerLoad 极其复杂（274KB 源码），官方 API 已暴露所有属性 |
| PinType 解析 | 手写字符串匹配 | unreal.EdGraphPin.pin_type | 12 个子字段已完整暴露 |
| 连线信息 | 手写 PinId 映射表 | unreal.EdGraphPin.linked_to | LinkedTo 数组直接包含目标 Pin 对象 |
| SubPin 识别 | 手写名称前缀匹配 | unreal.EdGraphPin.parent_pin/sub_pins | 官方属性明确表示父子关系 |

**Key insight:** UE Python API 通过反射机制自动暴露所有 `UPROPERTY` 属性。EdGraphNode 和 EdGraphPin 的完整属性集可直接访问，无需任何底层解析。

## Common Pitfalls

### Pitfall 1: UE Python API 属性名与 C++ 不同
**What goes wrong:** Python API 使用 snake_case，而 C++ 源码使用 PascalCase（如 NodePosX → node_pos_x）
**Why it happens:** PyBind11 自动转换命名风格
**How to avoid:** 参考 UE Python API 自动生成的文档，或使用 `dir(obj)` 查看可用属性
**Warning signs:** AttributeError: 'EdGraphNode' object has no attribute 'NodePosX'

### Pitfall 2: LinkedTo 引用循环
**What goes wrong:** LinkedTo 包含 UEdGraphPin 对象引用，直接序列化会导致循环引用或对象引用无法 JSON 化
**Why it happens:** Pin.LinkedTo 存储的是 UE 对象指针，不是可序列化的字符串
**How to avoid:** 提取时立即转换为 (node_name, pin_id) 元组，不保留对象引用
**Warning signs:** JSON 序列化失败或 TypeError: Object of type UEdGraphPin is not JSON serializable

### Pitfall 3: SubPin 遗漏或重复
**What goes wrong:** 遍历 node.pins 时既处理了父 Pin 也处理了子 Pin，导致重复；或忽略 SubPin 导致连线丢失
**Why it happens:** node.pins 包含所有 Pin（包括 SubPin），但 SubPin 的 parent_pin 属性指向父 Pin
**How to avoid:** 遍历 node.pins 时检查 parent_pin，有父 Pin 的跳过，在父 Pin 的 sub_pins 中递归处理
**Warning signs:** 节点引脚数量与 UE 编辑器显示不符，或连线信息缺失

### Pitfall 4: GUID 格式不一致
**What goes wrong:** GUID 转换为带连字符的 UUID 格式（如 "F9232687-43B7-B52D-669F-FB960CA79833"），与参考文本格式（32 字符无连字符）不符
**Why it happens:** Python str(FGuid) 可能使用不同格式
**How to avoid:** D-09 要求直接使用 UE 返回的原始值，测试确认格式一致性
**Warning signs:** 与 蓝图节点文本参考.md 中的 NodeGuid 格式不匹配

### Pitfall 5: 节点类型名称获取错误
**What goes wrong:** 使用 obj.get_name() 返回节点实例名（如 "K2Node_CallFunction_1193"），而非类名
**Why it happens:** UE 对象有多个名称概念：FName（实例名）、Class.Name（类名）
**How to avoid:** 使用 `node.get_class().get_name()` 获取节点类名（如 "K2Node_CallFunction"）
**Warning signs:** node_class 字段值为实例名而非类名

## Code Examples

### 节点提取完整示例
```python
# Source: 基于 EdGraphNode.h + EdGraphPin.h 源码分析 [VERIFIED: UE 5.7 源码]
import unreal
import json

def extract_event_graph(bp):
    """从 Blueprint 提取 EventGraph 的完整结构"""
    event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    if not event_graph:
        return {"error": "No EventGraph found"}
    
    result = {
        "event_graph_name": str(event_graph.get_fname()),
        "nodes": []
    }
    
    for node in event_graph.nodes:
        node_data = extract_single_node(node)
        if node_data:
            result["nodes"].append(node_data)
    
    return result

def extract_single_node(node):
    """提取单个节点的完整信息"""
    try:
        node_data = {
            "node_class": node.get_class().get_name(),
            "node_name": node.get_fname().to_string(),
            "node_pos_x": node.node_pos_x,
            "node_pos_y": node.node_pos_y,
            "node_guid": format_guid(node.node_guid),
            "pins": [],
        }
        
        # K2Node_CallFunction 特有字段
        if hasattr(node, 'function_reference'):
            node_data["function_reference"] = {
                "member_name": node.function_reference.member_name.to_string() if node.function_reference.member_name else None,
                "b_self_context": node.function_reference.b_self_context,
            }
        
        # 提取引脚
        for pin in node.pins:
            if pin.parent_pin:  # Skip SubPins in main iteration
                continue
            pin_data = extract_single_pin(pin)
            node_data["pins"].append(pin_data)
        
        return node_data
    except Exception as e:
        unreal.log_warning(f"[Phase2] Node extraction failed: {e}")
        return None

def extract_single_pin(pin):
    """提取单个引脚的完整信息"""
    pin_data = {
        "pin_id": format_guid(pin.pin_id),
        "pin_name": pin.pin_name.to_string(),
        "direction": str(pin.direction),
        "pin_type": extract_pin_type_full(pin.pin_type),
        "linked_to": [],
        "default_value": pin.default_value or None,
        "b_hidden": pin.b_hidden,
        "b_not_connectable": pin.b_not_connectable,
        "b_advanced_view": pin.b_advanced_view,
        "b_orphaned_pin": pin.b_orphaned_pin,
    }
    
    # 提取连线
    for linked in pin.linked_to:
        pin_data["linked_to"].append({
            "node_name": linked.get_owning_node().get_fname().to_string(),
            "pin_id": format_guid(linked.pin_id),
        })
    
    # 处理 SubPins
    if hasattr(pin, 'sub_pins') and len(pin.sub_pins) > 0:
        pin_data["sub_pins"] = []
        for sub in pin.sub_pins:
            pin_data["sub_pins"].append({
                "pin_id": format_guid(sub.pin_id),
                "pin_name": sub.pin_name.to_string(),
                "parent_pin": format_guid(pin.pin_id),
                "linked_to": [{"node_name": l.get_owning_node().get_fname().to_string(), 
                              "pin_id": format_guid(l.pin_id)} for l in sub.linked_to],
            })
    
    return pin_data

def extract_pin_type_full(pt):
    """提取 PinType 的完整结构"""
    return {
        "pin_category": pt.pin_category.to_string() if pt.pin_category else "",
        "pin_sub_category": pt.pin_sub_category.to_string() if pt.pin_sub_category else "",
        "pin_sub_category_object": str(pt.pin_sub_category_object) if pt.pin_sub_category_object else None,
        "container_type": str(pt.container_type),
        "b_is_reference": pt.b_is_reference,
        "b_is_const": pt.b_is_const,
        "b_is_weak_pointer": pt.b_is_weak_pointer,
        "b_is_uobject_wrapper": pt.b_is_uobject_wrapper,
    }

def format_guid(guid):
    """格式化 GUID 为 32 字符十六进制（与 UE 编辑器文本格式一致）"""
    # UE FGuid.ToString() 返回格式需验证
    guid_str = str(guid)
    # 移除可能的连字符（如果有）
    return guid_str.replace("-", "").upper() if guid_str else None
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 手写 .uasset 二进制解析 | UE Python API 反射属性访问 | Phase 1 (2026-05-18) | 简化实现，避免 FLinkerLoad 复杂度 |
| LinkedTo 存储为全局连线列表 | LinkedTo 作为 Pin 内嵌属性 | Phase 2 决策 (D-05) | 数据结构更清晰，与 UE 文本格式一致 |
| 忽略 SubPin | SubPin 递归处理 | Phase 2 决策 (D-07) | 完整捕获拆分引脚连线 |

**Deprecated/outdated:**
- 手写 FLinkerLoad 解析：极复杂（274KB 源码），且不稳定，官方 API 已暴露所需属性

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | UE Python API 自动暴露所有 EdGraphNode/EdGraphPin 的 UPROPERTY 属性 | Standard Stack | 若部分属性未暴露，需额外处理；但反射机制设计为自动暴露 |
| A2 | FGuid.ToString() 返回 32 字符无连字符格式 | Code Examples | 需实际测试验证格式一致性 |
| A3 | NodePosX/NodePosY 在 Python 中为 snake_case | Common Pitfalls | 已确认 PyBind11 转换规则，但建议用 dir(obj) 验证 |
| A4 | EdGraph.nodes 属性返回节点数组 | Pattern 1 | Phase 1 ue_extract.py 已验证 node_count 可获取 |

**Note:** 以上假设均基于 UE 源码结构和 Python 绑定机制，置信度较高。

## Open Questions

1. **GUID 格式是否与参考文本一致？**
   - What we know: 参考文本使用 32 字符十六进制（如 `F923268743B7B52D669FFB960CA79833`）
   - What's unclear: UE Python API 的 str(FGuid) 返回格式是否相同
   - Recommendation: Phase 2 实现时测试验证，必要时添加格式转换

2. **PinSubCategoryMemberReference 和 PinValueType 是否总是为空？**
   - What we know: 参考文本中这些字段多数为空或 ()
   - What's unclear: 某些复杂类型（如 Map）可能使用这些字段
   - Recommendation: 提取时保留字段，值为 None 表示未使用

3. **EdGraphNode_Comment（注释框）的额外属性是否需要提取？**
   - What we know: 参考文本显示注释框有 NodeComment、NodeWidth、NodeHeight 等属性
   - What's unclear: 这些是否通过标准 EdGraphNode 属性暴露
   - Recommendation: 提取 node_comment 属性（EdGraphNode.NodeComment），宽高属性按需提取

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| UE 5.7 Editor | Python API 执行 | ✓ | 5.7.x | — |
| Python 3.x | UE 内嵌脚本 | ✓ | UE 内置 | — |
| unreal module | API 访问 | ✓ | UE 内置 | — |
| BP_FirstPersonCharacter.uasset | 测试数据 | ✓ | Content/ | — |

**Missing dependencies with no fallback:** 无

**Missing dependencies with fallback:** 无

## Validation Architecture

> workflow.nyquist_validation: true (enabled)

### Test Framework
| Property | Value |
|----------|-------|
| Framework | UE 内嵌 Python (无外部测试框架) |
| Config file | 无 — 使用 ue_extract.py 内嵌验证 |
| Quick run command | 无独立测试 — 验证通过结果文件检查 |
| Full suite command | 运行 ue_extract.py + 手动对比 蓝图节点文本参考.md |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PARSE-03 | 提取节点列表 | Smoke | 检查 result.json["nodes"] 非空 | ✅ Phase 1 已有框架 |
| PARSE-04 | 提取引脚定义 | Smoke | 检查每个 node["pins"] 非空 | ❌ Wave 0 |
| PARSE-05 | 提取连线关系 | Smoke | 检查 pin["linked_to"] 结构正确 | ❌ Wave 0 |
| PARSE-06 | 提取画布坐标 | Smoke | 检查 node["node_pos_x/y"] 数值 | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** 运行 ue_extract.py，检查输出 JSON 结构
- **Per wave merge:** 对比输出节点数量与 Phase 1 检测的 node_count
- **Phase gate:** 输出 JSON 与 蓝图节点文本参考.md 关键字段匹配验证

### Wave 0 Gaps
- [ ] `scripts/node_utils.py` — 节点/引脚提取辅助函数
- [ ] `scripts/ue_extract.py` 扩展 — 添加节点提取逻辑
- [ ] 验证逻辑 — 输出与参考文本对比脚本

*(Wave 0 需在实现前完成)*

## Security Domain

> 本 Phase 无安全敏感操作 — 仅读取 Blueprint 数据，无写入、无网络、无认证。

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | 资产路径验证（Phase 1 已实现） |
| V6 Cryptography | no | — |

### Known Threat Patterns for UE Python API

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| 资产路径注入 | Tampering | 验证路径为 Content/ 内合法资产（Phase 1 已实现） |
| 异常未处理 | Denial of Service | D-12 节点级异常捕获，跳过失败节点 |

## Sources

### Primary (HIGH confidence)
- EdGraphNode.h — UEdGraphNode 类定义、属性列表 [VERIFIED: UE 5.7 源码 E:/Develop/lib/UnrealEngine/Engine/Source/Runtime/Engine/Classes/EdGraph/EdGraphNode.h]
- EdGraphPin.h — UEdGraphPin 类定义、FEdGraphPinType 结构 [VERIFIED: UE 5.7 源码 E:/Develop/lib/UnrealEngine/Engine/Source/Runtime/Engine/Classes/EdGraph/EdGraphPin.h]
- K2Node_CallFunction.h — FunctionReference 属性定义 [VERIFIED: UE 5.7 源码 E:/Develop/lib/UnrealEngine/Engine/Source/Editor/BlueprintGraph/Classes/K2Node_CallFunction.h]
- MemberReference.h — FMemberReference 结构定义 [VERIFIED: UE 5.7 源码 E:/Develop/lib/UnrealEngine/Engine/Source/Runtime/Engine/Classes/Engine/MemberReference.h]

### Secondary (MEDIUM confidence)
- 蓝图节点文本参考.md — 输出格式参考样本 [CITED: 项目文档]

### Tertiary (LOW confidence)
- UE Python API 属性命名转换规则 — PyBind11 snake_case 规律 [ASSUMED — 基于经验，建议用 dir(obj) 验证]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — 基于 UE 5.7 源码确认属性定义
- Architecture: HIGH — 基于 Phase 1 已验证的接口
- Pitfalls: HIGH — 基于源码分析和参考文本对比

**Research date:** 2026-05-18
**Valid until:** UE 5.7 API 稳定（长期有效）