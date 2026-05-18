"""
输出格式化模块：将 BPExtractor 提取的蓝图数据转换为可读格式。

两种输出：
- format_md():  UE 编辑器文本格式（Begin Object ... End Object 块）
- format_json(): 结构化 JSON（snake_case 键，nodes/pins/connections 三级嵌套）
"""
from __future__ import annotations

import json

# 节点类型 → UE 类路径映射
_NODE_CLASS_MAP = {
    "K2Node_CallFunction": "/Script/BlueprintGraph.K2Node_CallFunction",
    "K2Node_Event": "/Script/BlueprintGraph.K2Node_Event",
    "K2Node_FunctionEntry": "/Script/BlueprintGraph.K2Node_FunctionEntry",
    "K2Node_FunctionResult": "/Script/BlueprintGraph.K2Node_FunctionResult",
    "K2Node_Knot": "/Script/BlueprintGraph.K2Node_Knot",
    "K2Node_IfThenElse": "/Script/BlueprintGraph.K2Node_IfThenElse",
    "K2Node_VariableGet": "/Script/BlueprintGraph.K2Node_VariableGet",
    "K2Node_VariableSet": "/Script/BlueprintGraph.K2Node_VariableSet",
    "K2Node_MacroInstance": "/Script/BlueprintGraph.K2Node_MacroInstance",
    "K2Node_EnhancedInputAction": "/Script/InputBlueprintNodes.K2Node_EnhancedInputAction",
    "EdGraphNode_Comment": "/Script/UnrealEd.EdGraphNode_Comment",
    "EdGraph": "/Script/Engine.EdGraph",
}

_FALLBACK_CLASS = "/Script/CoreUObject.Object"


def _node_class_path(node_type: str) -> str:
    """将短类型名映射为 UE 类路径。"""
    return _NODE_CLASS_MAP.get(node_type, _FALLBACK_CLASS)


def _fmt_pin(pin: dict) -> str:
    """格式化单个引脚为 CustomProperties Pin 行。"""
    parts = []
    if pin.get("PinId"):
        parts.append(f"PinId={pin['PinId']}")
    if pin.get("PinName"):
        parts.append(f"PinName=\"{pin['PinName']}\"")
    if pin.get("PinType"):
        pin_type = pin["PinType"]
        if isinstance(pin_type, dict):
            type_parts = []
            if pin_type.get("PinCategory"):
                type_parts.append(f"PinCategory=\"{pin_type['PinCategory']}\"")
            if pin_type.get("PinSubCategory"):
                type_parts.append(f"PinSubCategory=\"{pin_type['PinSubCategory']}\"")
            if pin_type.get("ContainerType"):
                type_parts.append(f"ContainerType={pin_type['ContainerType']}")
            if type_parts:
                parts.append(f"PinType.{','.join(type_parts)}")
        else:
            parts.append(f"PinType=\"{pin_type}\"")
    if pin.get("Direction"):
        parts.append(f"Direction=\"{pin['Direction']}\"")
    linked = pin.get("LinkedTo", [])
    if linked:
        linked_str = ",".join(linked)
        parts.append(f"LinkedTo=({linked_str},)")

    return f"   CustomProperties Pin ({','.join(parts)})"


def format_md(data: dict) -> str:
    """将提取数据转换为 UE 编辑器文本格式。"""
    nodes = data.get("Nodes", data.get("nodes", []))
    package = data.get("PackageName", data.get("package_name", "Unknown"))
    blueprint_class = data.get("BlueprintClass", data.get("blueprint_class", "Unknown"))

    lines = []
    lines.append(f"// Package: {package}")
    lines.append(f"// BlueprintClass: {blueprint_class}")
    lines.append(f"// Backend: {data.get('backend', 'unknown')}")
    if data.get("extraction_time_ms"):
        lines.append(f"// ExtractionTime: {data['extraction_time_ms']}ms")
    lines.append(f"// NodeCount: {len(nodes)}")
    lines.append("")

    for node in nodes:
        node_type = node.get("Type", node.get("type", "Unknown"))
        name = node.get("Name", node.get("name", "Unknown"))
        class_path = _node_class_path(node_type)

        # Begin Object 行
        lines.append(f'Begin Object Class={class_path} Name="{name}"')

        # FunctionReference（仅 CallFunction 类型）
        func_name = node.get("FunctionName") or node.get("function_name")
        if func_name and node_type == "K2Node_CallFunction":
            lines.append(f'   FunctionReference=(MemberName="{func_name}",bSelfContext=True)')

        # 坐标（非零时输出）
        pos_x = node.get("NodePosX", node.get("pos_x", 0.0)) or 0.0
        pos_y = node.get("NodePosY", node.get("pos_y", 0.0)) or 0.0
        if pos_x != 0.0:
            lines.append(f"   NodePosX={int(pos_x)}")
        if pos_y != 0.0:
            lines.append(f"   NodePosY={int(pos_y)}")

        # GUID（非空时输出）
        guid = node.get("NodeGuid", node.get("guid"))
        if guid:
            lines.append(f"   NodeGuid={guid}")

        # 引脚（非空时输出）
        pins = node.get("Pins", node.get("pins", [])) or []
        for pin in pins:
            lines.append(_fmt_pin(pin))

        # Note（调试信息）
        note = node.get("Note", node.get("note"))
        if note:
            lines.append(f"   // {note}")

        lines.append("End Object")
        lines.append("")

    return "\n".join(lines)


def _normalize_node(raw: dict) -> dict:
    """将 PascalCase 节点 dict 转换为 snake_case。"""
    return {
        "type": raw.get("Type", raw.get("type", "")),
        "name": raw.get("Name", raw.get("name", "")),
        "position": {
            "x": raw.get("NodePosX", raw.get("pos_x", 0.0)) or 0.0,
            "y": raw.get("NodePosY", raw.get("pos_y", 0.0)) or 0.0,
        },
        "guid": raw.get("NodeGuid", raw.get("guid")),
        "function_name": raw.get("FunctionName", raw.get("function_name")),
        "pins": _normalize_pins(raw.get("Pins", raw.get("pins", [])) or []),
        "note": raw.get("Note", raw.get("note")),
    }


def _normalize_pin(raw: dict) -> dict:
    """将 PascalCase 引脚 dict 转换为 snake_case。"""
    pin_type = raw.get("PinType", raw.get("pin_type"))
    if isinstance(pin_type, str):
        pin_type = {"raw": pin_type}
    elif pin_type is None:
        pin_type = {}
    else:
        pin_type = {
            "pin_category": pin_type.get("PinCategory", pin_type.get("pin_category", "")),
            "pin_sub_category": pin_type.get("PinSubCategory", pin_type.get("pin_sub_category", "")),
            "container_type": pin_type.get("ContainerType", pin_type.get("container_type", "")),
        }

    return {
        "pin_id": raw.get("PinId", raw.get("pin_id", "")),
        "pin_name": raw.get("PinName", raw.get("pin_name", "")),
        "direction": raw.get("Direction", raw.get("direction", "")),
        "pin_type": pin_type,
        "default_value": raw.get("DefaultValue", raw.get("default_value", "")),
        "linked_to": raw.get("LinkedTo", raw.get("linked_to", [])) or [],
        "is_reference": raw.get("bIsReference", raw.get("is_reference", False)),
        "is_const": raw.get("bIsConst", raw.get("is_const", False)),
    }


def _normalize_pins(raw_pins: list) -> list:
    return [_normalize_pin(p) for p in raw_pins]


def _build_connections(nodes: list) -> list:
    """从节点的引脚数据中提取连线关系。"""
    connections = []
    for node in nodes:
        for pin in node.get("pins", []):
            for linked in pin.get("linked_to", []):
                # linked 格式: "NodeName.PinId" 或只是 "PinId"
                if "." in linked:
                    target_node, target_pin = linked.split(".", 1)
                else:
                    target_node = ""
                    target_pin = linked
                connections.append({
                    "from": {"node": node["name"], "pin": pin["pin_id"]},
                    "to": {"node": target_node, "pin": target_pin},
                })
    return connections


def format_json(data: dict) -> str:
    """将提取数据转换为结构化 JSON（snake_case）。"""
    raw_nodes = data.get("Nodes", data.get("nodes", []))
    nodes = [_normalize_node(n) for n in raw_nodes]
    connections = _build_connections(nodes)

    result = {
        "package_name": data.get("PackageName", data.get("package_name", "")),
        "blueprint_class": data.get("BlueprintClass", data.get("blueprint_class", "")),
        "graphs": data.get("Graphs", data.get("graphs", [])),
        "node_count": len(nodes),
        "nodes": nodes,
        "connections": connections,
        "warnings": data.get("Warnings", data.get("warnings", [])),
        "backend": data.get("backend", "unknown"),
        "extraction_time_ms": data.get("extraction_time_ms", 0),
    }

    return json.dumps(result, ensure_ascii=False, indent=2)
