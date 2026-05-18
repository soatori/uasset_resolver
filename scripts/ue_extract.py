"""
UE 内嵌 Python 脚本：加载 .uasset 资产，检测是否为蓝图，
并将结果写入 JSON 文件。

用法（通过 -ExecutePythonScript）：
  -ExecutePythonScript="scripts/ue_extract.py --output temp/result.json"
"""
import unreal
import json
import sys

# Phase 2: 节点提取辅助函数
from node_utils import extract_nodes, format_guid


def parse_args():
    """从命令行解析 --output 参数。"""
    output_path = "temp/result.json"
    for i, arg in enumerate(sys.argv):
        if arg == "--output" and i + 1 < len(sys.argv):
            output_path = sys.argv[i + 1]
    return output_path


def detect_asset_type(asset):
    """使用 isinstance 检查确定资产类型（按 D-05 可扩展）。"""
    if asset is None:
        return {"error": "Asset not found or failed to load"}

    asset_class = asset.get_class().get_name()
    result = {
        "asset_class": asset_class,
        "is_blueprint": isinstance(asset, unreal.Blueprint),
        "is_material": isinstance(asset, unreal.Material),
        "is_static_mesh": isinstance(asset, unreal.StaticMesh),
        "is_skeletal_mesh": isinstance(asset, unreal.SkeletalMesh),
    }

    if isinstance(asset, unreal.Blueprint):
        bp = asset
        generated_class = bp.generated_class
        result["generated_class"] = str(generated_class) if generated_class else None

        # 尝试获取父类（属性名可能因 UE 版本不同）
        try:
            parent_class = bp.parent_class
            result["parent_class"] = str(parent_class) if parent_class else None
        except AttributeError:
            # UE 5.7 中 Blueprint 可能没有 parent_class 属性
            # 尝试通过 generated_class 获取父类信息
            if generated_class:
                try:
                    # generated_class 的父类通常是蓝图的父类
                    parent = generated_class.get_class()
                    result["parent_class"] = str(parent) if parent else None
                except:
                    result["parent_class"] = None
            else:
                result["parent_class"] = None

        # EventGraph 检测
        event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
        result["has_event_graph"] = event_graph is not None
        if event_graph:
            result["event_graph_name"] = str(event_graph.get_fname())
            # 尝试获取节点数量（API 可能因 UE 版本不同）
            try:
                nodes = event_graph.nodes
                result["node_count"] = len(nodes) if nodes else 0
            except AttributeError:
                # UE 5.7 中 EdGraph 可能没有 nodes 属性
                # 使用 get_nodes() 或其他方法
                try:
                    nodes = event_graph.get_nodes()
                    result["node_count"] = len(nodes) if nodes else 0
                except:
                    result["node_count"] = -1  # 表示无法获取

            # Phase 2: 节点提取入口
            try:
                result['nodes'] = extract_nodes(event_graph)
                result['node_extraction_status'] = 'success'
                result['extracted_node_count'] = len(result['nodes'])
            except Exception as e:
                result['node_extraction_error'] = str(e)
                result['node_extraction_status'] = 'failed'
                unreal.log_warning(f'[Phase2] 节点提取失败: {e}')

        return result


def main():
    output_path = parse_args()
    print(f"[ue_extract] 输出路径：{output_path}")

    # 资产的虚拟路径（必须在 Content/ 目录中）
    asset_path = "/Game/BP_FirstPersonCharacter"
    print(f"[ue_extract] 加载资产：{asset_path}")

    asset = unreal.EditorAssetLibrary.load_asset(asset_path)
    result = detect_asset_type(asset)
    result["asset_path"] = asset_path

    # 写入 JSON
    print(f"[ue_extract] 写入结果...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # Phase 2: 输出节点提取状态
    extraction_status = result.get('node_extraction_status', 'not_attempted')
    if extraction_status == 'success':
        print(f"[ue_extract] 节点提取成功，提取了 {result.get('extracted_node_count', 0)} 个节点")
    elif extraction_status == 'failed':
        print(f"[ue_extract] 节点提取失败: {result.get('node_extraction_error', 'unknown error')}")

    print(f"[ue_extract] 完成。蓝图={result.get('is_blueprint', False)}")

    # 退出编辑器
    unreal.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main()