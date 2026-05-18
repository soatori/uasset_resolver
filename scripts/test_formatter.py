"""测试 formatter.py 在完整数据下的输出。"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from formatter import format_md, format_json

# 模拟 CUE4Parse 返回的 PascalCase 数据（包含完整字段）
SAMPLE_DATA = {
    "PackageName": "BP_Test",
    "BlueprintClass": "BP_Test_C",
    "Graphs": ["EventGraph"],
    "backend": "cue4parse",
    "extraction_time_ms": 150,
    "Nodes": [
        {
            "Type": "K2Node_Event",
            "Name": "K2Node_Event_0",
            "NodePosX": 100.0,
            "NodePosY": 200.0,
            "NodeGuid": "ABC123DEF456",
            "FunctionName": None,
            "Pins": [
                {
                    "PinId": "PIN_001",
                    "PinName": "then",
                    "Direction": "EGPD_Output",
                    "PinType": {
                        "PinCategory": "exec",
                        "PinSubCategory": "",
                    },
                    "LinkedTo": ["K2Node_CallFunction_0.PIN_002"],
                }
            ],
            "Note": None,
        },
        {
            "Type": "K2Node_CallFunction",
            "Name": "K2Node_CallFunction_0",
            "NodePosX": 300.0,
            "NodePosY": 200.0,
            "NodeGuid": "XYZ789",
            "FunctionName": "MyFunction",
            "Pins": [
                {
                    "PinId": "PIN_002",
                    "PinName": "execute",
                    "Direction": "Input",
                    "PinType": {"PinCategory": "exec", "PinSubCategory": ""},
                    "LinkedTo": [],
                },
                {
                    "PinId": "PIN_003",
                    "PinName": "self",
                    "Direction": "Input",
                    "PinType": {"PinCategory": "object", "PinSubCategory": "self"},
                    "LinkedTo": [],
                },
            ],
            "Note": None,
        },
        {
            "Type": "EdGraphNode_Comment",
            "Name": "Comment_0",
            "NodePosX": 0.0,
            "NodePosY": 0.0,
            "NodeGuid": "GUID_COMMENT",
            "FunctionName": None,
            "Pins": [],
            "Note": "Test Comment",
        },
    ],
}


def test_md():
    output = format_md(SAMPLE_DATA)
    lines = output.split("\n")

    # 检查 header
    assert any("Package: BP_Test" in l for l in lines), "缺少 Package header"
    assert any("NodeCount: 3" in l for l in lines), "缺少 NodeCount"

    # 检查 Begin Object 格式
    assert 'Begin Object Class=/Script/BlueprintGraph.K2Node_Event Name="K2Node_Event_0"' in output, "Event Begin Object 格式错误"
    assert 'Begin Object Class=/Script/BlueprintGraph.K2Node_CallFunction Name="K2Node_CallFunction_0"' in output, "CallFunction Begin Object 格式错误"

    # 检查 FunctionReference
    assert 'FunctionReference=(MemberName="MyFunction",bSelfContext=True)' in output, "FunctionReference 缺失"

    # 检查坐标
    assert "NodePosX=100" in output, "NodePosX 缺失"
    assert "NodePosY=200" in output, "NodePosY 缺失"

    # 检查 GUID
    assert "NodeGuid=ABC123DEF456" in output, "NodeGuid 缺失"

    # 检查引脚
    assert 'CustomProperties Pin (' in output, "引脚缺失"
    assert 'PinName="then"' in output, "PinName 缺失"
    assert 'PinCategory="exec"' in output, "PinCategory 缺失"

    # 检查连线
    assert "LinkedTo=(K2Node_CallFunction_0.PIN_002,)" in output, "LinkedTo 格式错误"

    # 检查 End Object
    assert output.count("End Object") == 3, f"End Object 数量不对: {output.count('End Object')}"

    # 检查零坐标不输出
    assert "NodePosX=0" not in output or "NodePosX=0.0" not in output, "零坐标不应输出"

    print("[PASS] MD 格式验证通过")
    print("\n--- MD 输出 ---")
    print(output)


def test_json():
    output = format_json(SAMPLE_DATA)
    data = json.loads(output)

    # 检查顶层 key
    assert "package_name" in data, "缺少 package_name"
    assert "blueprint_class" in data, "缺少 blueprint_class"
    assert "node_count" in data, "缺少 node_count"
    assert "nodes" in data, "缺少 nodes"
    assert "connections" in data, "缺少 connections"

    # 检查 snake_case
    for key in data.keys():
        assert "_" in key or key in ["backend", "warnings", "graphs", "node_count", "nodes", "connections", "package_name", "blueprint_class", "extraction_time_ms"], f"非 snake_case key: {key}"

    # 检查 nodes
    assert data["node_count"] == 3, f"节点数量错误: {data['node_count']}"
    assert len(data["nodes"]) == 3, "nodes 数组长度错误"

    # 检查 node 结构
    event_node = data["nodes"][0]
    assert event_node["type"] == "K2Node_Event", "type 错误"
    assert event_node["name"] == "K2Node_Event_0", "name 错误"
    assert event_node["position"]["x"] == 100.0, "position.x 错误"
    assert event_node["position"]["y"] == 200.0, "position.y 错误"
    assert event_node["guid"] == "ABC123DEF456", "guid 错误"
    assert len(event_node["pins"]) == 1, "引脚数量错误"

    # 检查 pin 结构
    pin = event_node["pins"][0]
    assert pin["pin_id"] == "PIN_001", "pin_id 错误"
    assert pin["pin_name"] == "then", "pin_name 错误"
    assert pin["direction"] == "EGPD_Output", "direction 错误"
    assert pin["pin_type"]["pin_category"] == "exec", "pin_category 错误"
    assert "K2Node_CallFunction_0.PIN_002" in pin["linked_to"], "linked_to 错误"

    # 检查 connections
    assert len(data["connections"]) == 1, f"connections 数量错误: {len(data['connections'])}"
    conn = data["connections"][0]
    assert conn["from"]["node"] == "K2Node_Event_0", "connection from.node 错误"
    assert conn["from"]["pin"] == "PIN_001", "connection from.pin 错误"
    assert conn["to"]["node"] == "K2Node_CallFunction_0", "connection to.node 错误"
    assert conn["to"]["pin"] == "PIN_002", "connection to.pin 错误"

    print("[PASS] JSON 格式验证通过")
    print("\n--- JSON 输出 ---")
    print(output)


if __name__ == "__main__":
    test_md()
    print()
    test_json()
    print("\n=== 所有测试通过 ===")
