"""
节点和引脚提取辅助函数模块。

本模块定义了从蓝图 EventGraph 中提取节点、引脚、连线和画布坐标的完整接口契约。
所有函数目前为骨架实现，仅包含签名和 docstring，返回占位值。

Phase 2 Wave 1: 接口定义
Phase 2 Wave 2: 实现逻辑
"""

import unreal
from typing import Optional


def extract_nodes(event_graph: unreal.EdGraph) -> list[dict]:
    """
    从 EventGraph 提取所有节点信息。

    遍历 event_graph.nodes，为每个节点调用 extract_single_node() 构建节点字典列表。
    D-12: 单个节点提取失败时跳过，记录 warning，继续处理其他节点。

    Args:
        event_graph: UE EdGraph 对象，通常是蓝图的 EventGraph。

    Returns:
        节点字典列表，每个节点包含：
        - node_class: str — 节点类型名称（如 K2Node_Event, K2Node_CallFunction）
        - node_name: str — 节点实例名称
        - node_pos_x: int — 画布 X 坐标
        - node_pos_y: int — 画布 Y 坐标
        - node_guid: str — 唯一标识符（32 字符十六进制）
        - pins: list[dict] — 引脚列表（内嵌连线信息）
        - function_reference: dict | None — 函数引用（仅 K2Node_CallFunction）
        - node_comment: str | None — 注释框文本（仅 EdGraphNode_Comment）

        返回空列表如果 graph 为 None 或无节点。
    """
    if event_graph is None:
        return []

    nodes = []
    for node in event_graph.nodes:
        try:
            node_data = extract_single_node(node)
            if node_data is not None:  # D-12: 跳过失败节点
                nodes.append(node_data)
        except Exception as e:
            # D-12: 节点级异常捕获，跳过失败节点
            node_name = "unknown"
            try:
                node_name = node.get_fname().to_string()
            except:
                pass
            unreal.log_warning(f"[Phase2] 节点提取失败 '{node_name}': {e}")

    return nodes


def extract_single_node(node: unreal.EdGraphNode) -> Optional[dict]:
    """
    提取单个节点的完整信息。

    提取节点属性：类型、名称、画布坐标、GUID。
    调用 extract_pins() 获取引脚列表。
    对于 K2Node_CallFunction，调用 extract_function_reference() 获取函数引用。
    对于 EdGraphNode_Comment，提取 node_comment 属性。

    Args:
        node: UE EdGraphNode 对象。

    Returns:
        节点字典（格式同 extract_nodes 返回的单个元素），或 None 表示提取失败（异常时跳过）。
    """
    try:
        # 基本属性提取
        node_class = node.get_class().get_name()
        node_name = node.get_fname().to_string()
        node_pos_x = node.node_pos_x  # Python API 使用 snake_case
        node_pos_y = node.node_pos_y
        node_guid = format_guid(node.node_guid)

        node_data = {
            'node_class': node_class,
            'node_name': node_name,
            'node_pos_x': node_pos_x,
            'node_pos_y': node_pos_y,
            'node_guid': node_guid,
            'pins': extract_pins(node),
            'function_reference': None,  # D-04: 缺失字段为 None
        }

        # K2Node_CallFunction 特有字段：函数引用
        if isinstance(node, unreal.K2Node_CallFunction):
            func_ref = extract_function_reference(node)
            node_data['function_reference'] = func_ref

        # EdGraphNode_Comment 特有字段：注释文本
        if hasattr(node, 'node_comment'):
            try:
                comment = node.node_comment
                if comment:
                    node_data['node_comment'] = comment
            except:
                pass  # D-04: 缺失字段为 None

        return node_data

    except Exception as e:
        # D-12: 单节点异常捕获，返回 None 表示跳过
        node_name = "unknown"
        try:
            node_name = node.get_fname().to_string()
        except:
            pass
        unreal.log_warning(f"[Phase2] 单节点提取失败 '{node_name}': {e}")
        return None


def extract_pins(node: unreal.EdGraphNode) -> list[dict]:
    """
    从节点提取所有顶层引脚信息。

    遍历 node.pins，跳过 parent_pin 不为 None 的 SubPin（D-07 决策）。
    对每个顶层 Pin 调用 extract_single_pin()。

    Args:
        node: UE EdGraphNode 对象。

    Returns:
        引脚字典列表，每个引脚包含：
        - pin_id: str — Pin GUID
        - pin_name: str — 引脚名称
        - direction: str — 方向（"EGPD_Input" / "EGPD_Output"）
        - pin_type: dict — FEdGraphPinType 完整结构（9 子字段）
        - linked_to: list[dict] — 连接目标列表
        - default_value: str | None — 默认值
        - b_hidden: bool — 是否隐藏
        - b_not_connectable: bool — 是否不可连接
        - b_advanced_view: bool — 是否高级视图
        - b_orphaned_pin: bool — 是否孤立引脚
        - sub_pins: list[dict] — 子引脚列表（递归结构）
    """
    pins = []

    # UEdGraphNode.pins 属性返回 UEdGraphPin 数组
    for pin in node.pins:
        try:
            # D-07: 检查是否为 SubPin（有 ParentPin），跳过在父 Pin 中处理
            if pin.parent_pin is not None:
                continue  # SubPin 在父 Pin 的 sub_pins 中处理

            pin_data = extract_single_pin(pin)
            pins.append(pin_data)

        except Exception as e:
            # 引脚提取失败，记录警告并跳过
            pin_name = "unknown"
            try:
                pin_name = pin.pin_name.to_string()
            except:
                pass
            unreal.log_warning(f"[Phase2] 引脚提取失败 '{pin_name}': {e}")

    return pins


def extract_single_pin(pin: unreal.EdGraphPin) -> dict:
    """
    提取单个引脚的完整信息。

    提取 Pin 所有属性，包括 PinType 结构和 LinkedTo 连接信息。
    递归处理 SubPins（如果存在）。

    Args:
        pin: UE EdGraphPin 对象。

    Returns:
        引脚字典（格式同 extract_pins 返回的单个元素）。
    """
    # D-08: Pin 字段完整提取
    pin_id = format_guid(pin.pin_id)
    pin_name = pin.pin_name.to_string()

    # Direction: 转换为字符串表示
    direction = 'EGPD_Input' if pin.direction == unreal.EdGraphPinDirection.INPUT else 'EGPD_Output'

    pin_data = {
        'pin_id': pin_id,
        'pin_name': pin_name,
        'direction': direction,
        'pin_type': extract_pin_type(pin.pin_type),
        'linked_to': extract_linked_to(pin),
        'default_value': pin.default_value or None,
        'autogenerated_default_value': pin.autogenerated_default_value or None,
        'default_object': str(pin.default_object) if pin.default_object else None,
        'persistent_guid': format_guid(pin.persistent_guid) if hasattr(pin, 'persistent_guid') and pin.persistent_guid else None,
        'b_hidden': pin.b_hidden,
        'b_not_connectable': pin.b_not_connectable,
        'b_default_value_is_read_only': pin.b_default_value_is_read_only,
        'b_default_value_is_ignored': pin.b_default_value_is_ignored,
        'b_advanced_view': pin.b_advanced_view,
        'b_orphaned_pin': pin.b_orphaned_pin,
    }

    # D-07: 处理 SubPins（拆分引脚，如 Vector2D 的 X/Y）
    if hasattr(pin, 'sub_pins') and len(pin.sub_pins) > 0:
        pin_data['sub_pins'] = []
        for sub_pin in pin.sub_pins:
            try:
                sub_data = {
                    'pin_id': format_guid(sub_pin.pin_id),
                    'pin_name': sub_pin.pin_name.to_string(),
                    'parent_pin': pin_id,  # 引用父 Pin ID
                    'pin_type': extract_pin_type(sub_pin.pin_type),
                    'linked_to': extract_linked_to(sub_pin),
                }
                pin_data['sub_pins'].append(sub_data)
            except Exception as e:
                unreal.log_warning(f"[Phase2] SubPin 提取失败: {e}")

    return pin_data


def extract_pin_type(pin_type: unreal.FEdGraphPinType) -> dict:
    """
    提取 FEdGraphPinType 的完整结构。

    D-06: 提取所有子字段（完整提取）：
    - pin_category: str — 类别（如 "bool", "int", "float", "object" 等）
    - pin_sub_category: str — 子类别
    - pin_sub_category_object: str | None — 子类别对象路径
    - pin_sub_category_member_reference: dict | None — 成员引用
    - pin_value_type: dict | None — 值类型
    - container_type: str — 容器类型（None, Array, Set, Map）
    - b_is_reference: bool — 是否引用
    - b_is_const: bool — 是否常量
    - b_is_weak_pointer: bool — 是否弱指针
    - b_is_uobject_wrapper: bool — 是否 UObject 包装
    - b_serialize_as_single_precision_float: bool — 是否单精度浮点序列化

    Args:
        pin_type: UE FEdGraphPinType 对象。

    Returns:
        PinType 字典，包含上述字段。
    """
    result = {
        'pin_category': pin_type.pin_category.to_string() if pin_type.pin_category else '',
        'pin_sub_category': pin_type.pin_sub_category.to_string() if pin_type.pin_sub_category else '',
        'pin_sub_category_object': str(pin_type.pin_sub_category_object) if pin_type.pin_sub_category_object else None,
        'container_type': str(pin_type.container_type),  # EPinContainerType: None/Array/Set/Map
        'b_is_reference': pin_type.b_is_reference,
        'b_is_const': pin_type.b_is_const,
        'b_is_weak_pointer': pin_type.b_is_weak_pointer,
        'b_is_uobject_wrapper': pin_type.b_is_uobject_wrapper,
    }

    # 可选字段（D-10: 无法提取的字段设置为 None）
    if hasattr(pin_type, 'pin_sub_category_member_reference'):
        try:
            member_ref = pin_type.pin_sub_category_member_reference
            if member_ref:
                # 提取成员引用结构
                result['pin_sub_category_member_reference'] = {
                    'member_name': member_ref.member_name.to_string() if hasattr(member_ref, 'member_name') and member_ref.member_name else None,
                    'member_parent': str(member_ref.member_parent) if hasattr(member_ref, 'member_parent') and member_ref.member_parent else None,
                }
            else:
                result['pin_sub_category_member_reference'] = None
        except:
            result['pin_sub_category_member_reference'] = None
    else:
        result['pin_sub_category_member_reference'] = None

    if hasattr(pin_type, 'pin_value_type'):
        try:
            value_type = pin_type.pin_value_type
            if value_type:
                result['pin_value_type'] = {
                    'pin_category': value_type.pin_category.to_string() if hasattr(value_type, 'pin_category') and value_type.pin_category else '',
                    'pin_sub_category': value_type.pin_sub_category.to_string() if hasattr(value_type, 'pin_sub_category') and value_type.pin_sub_category else '',
                }
            else:
                result['pin_value_type'] = None
        except:
            result['pin_value_type'] = None
    else:
        result['pin_value_type'] = None

    if hasattr(pin_type, 'b_serialize_as_single_precision_float'):
        try:
            result['b_serialize_as_single_precision_float'] = pin_type.b_serialize_as_single_precision_float
        except:
            result['b_serialize_as_single_precision_float'] = False
    else:
        result['b_serialize_as_single_precision_float'] = False

    return result


def extract_linked_to(pin: unreal.EdGraphPin) -> list[dict]:
    """
    提取引脚的连接目标列表。

    D-05: LinkedTo 作为 Pin 内嵌属性。
    遍历 pin.linked_to，转换为标准格式。

    Args:
        pin: UE EdGraphPin 对象。

    Returns:
        连接目标字典列表，每个元素包含：
        - node_name: str — 目标节点名称
        - pin_id: str — 目标引脚 ID
    """
    connections = []

    # LinkedTo 是 TArray<UEdGraphPin*>，包含所有连接的目标引脚
    for linked_pin in pin.linked_to:
        try:
            # T-02-03: 立即转换为 (node_name, pin_id)，不保留 UE 对象引用
            owning_node = linked_pin.get_owning_node()
            connection = {
                'node_name': owning_node.get_fname().to_string(),
                'pin_id': format_guid(linked_pin.pin_id),
            }
            connections.append(connection)
        except Exception as e:
            unreal.log_warning(f"[Phase2] 连线解析失败: {e}")

    return connections


def extract_function_reference(node: unreal.K2Node_CallFunction) -> Optional[dict]:
    """
    提取 K2Node_CallFunction 的函数引用信息。

    提取 FMemberReference 结构：
    - member_name: str — 函数名称
    - member_parent: str — 父类路径
    - member_guid: str — 成员 GUID
    - b_self_context: bool — 是否自上下文

    Args:
        node: UE K2Node_CallFunction 对象。

    Returns:
        函数引用字典，或 None 表示提取失败。
        仅对 K2Node_CallFunction 类型节点调用此函数。
    """
    try:
        # 仅适用于 K2Node_CallFunction 类型节点
        if not isinstance(node, unreal.K2Node_CallFunction):
            return None

        func_ref = node.function_reference
        if func_ref is None:
            return None

        result = {
            'member_name': func_ref.member_name.to_string() if hasattr(func_ref, 'member_name') and func_ref.member_name else None,
            'member_parent': str(func_ref.member_parent) if hasattr(func_ref, 'member_parent') and func_ref.member_parent else None,
            'member_guid': format_guid(func_ref.member_guid) if hasattr(func_ref, 'member_guid') and func_ref.member_guid else None,
            'b_self_context': func_ref.b_self_context if hasattr(func_ref, 'b_self_context') else False,
        }

        return result

    except Exception as e:
        unreal.log_warning(f"[Phase2] 函数引用提取失败: {e}")
        return None


def format_guid(guid: unreal.FGuid) -> str:
    """
    格式化 UE FGuid 为标准字符串。

    D-09: 直接使用 UE 返回的原始值（32 字符十六进制）。
    T-02-04: 移除可能存在的连字符，转为大写。

    Args:
        guid: UE FGuid 对象。

    Returns:
        32 字符大写十六进制字符串，如 "A1B2C3D4E5F67890A1B2C3D4E5F67890"。
        如果 guid 为空或无效，返回 None。
    """
    if guid is None:
        return None

    try:
        guid_str = str(guid)
        if not guid_str:
            return None

        # T-02-04: 移除连字符，转为大写（与参考文本格式一致）
        formatted = guid_str.replace('-', '').upper()
        return formatted

    except Exception as e:
        unreal.log_warning(f"[Phase2] GUID 格式化失败: {e}")
        return None