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

        返回空列表如果 graph 为 None 或无节点。
    """
    # 骨架实现 — Wave 2 完成
    return []


def extract_single_node(node: unreal.EdGraphNode) -> Optional[dict]:
    """
    提取单个节点的完整信息。

    提取节点属性：类型、名称、画布坐标、GUID。
    调用 extract_pins() 获取引脚列表。
    对于 K2Node_CallFunction，调用 extract_function_reference() 获取函数引用。

    Args:
        node: UE EdGraphNode 对象。

    Returns:
        节点字典（格式同 extract_nodes 返回的单个元素），或 None 表示提取失败（异常时跳过）。
    """
    # 骨架实现 — Wave 2 完成
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
    # 骨架实现 — Wave 2 完成
    return []


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
    # 骨架实现 — Wave 2 完成
    return {}


def extract_pin_type(pin_type: unreal.FEdGraphPinType) -> dict:
    """
    提取 FEdGraphPinType 的完整结构。

    提取所有 9 个子字段（D-06 决策：完整提取）：
    - pin_category: str — 类别（如 "bool", "int", "float", "object" 等）
    - pin_sub_category: str — 子类别
    - pin_sub_category_object: str | None — 子类别对象路径
    - pin_value_type: str | None — 值类型
    - container_type: str — 容器类型（None, Array, Set, Map）
    - b_is_reference: bool — 是否引用
    - b_is_const: bool — 是否常量
    - b_is_weak_pointer: bool — 是否弱指针
    - b_is_uobject_wrapper: bool — 是否 UObject 包装

    Args:
        pin_type: UE FEdGraphPinType 对象。

    Returns:
        PinType 字典，包含上述 9 个字段。
    """
    # 骨架实现 — Wave 2 完成
    return {}


def extract_linked_to(pin: unreal.EdGraphPin) -> list[dict]:
    """
    提取引脚的连接目标列表。

    遍历 pin.linked_to，转换为标准格式（D-05 决策：LinkedTo 作为 Pin 内嵌属性）。

    Args:
        pin: UE EdGraphPin 对象。

    Returns:
        连接目标字典列表，每个元素包含：
        - node_name: str — 目标节点名称
        - pin_id: str — 目标引脚 ID
    """
    # 骨架实现 — Wave 2 完成
    return []


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
    # 骨架实现 — Wave 2 完成
    return None


def format_guid(guid: unreal.FGuid) -> str:
    """
    格式化 UE FGuid 为标准字符串。

    D-09 决策：直接使用 UE 返回的原始值（32 字符十六进制）。
    移除可能存在的连字符，转为大写。

    Args:
        guid: UE FGuid 对象。

    Returns:
        32 字符大写十六进制字符串，如 "A1B2C3D4E5F67890A1B2C3D4E5F67890"。
    """
    # 骨架实现 — Wave 2 完成
    return ""