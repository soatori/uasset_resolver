"""
UE 内嵌 Python 脚本：加载 .uasset 资产，检测是否为蓝图，
并将结果写入 JSON 文件。

用法（通过 -ExecutePythonScript）：
  -ExecutePythonScript="scripts/ue_extract.py --output temp/result.json"
"""
import unreal
import json
import sys


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
        result["parent_class"] = str(bp.parent_class) if bp.parent_class else None

        # EventGraph 检测
        event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
        result["has_event_graph"] = event_graph is not None
        if event_graph:
            result["event_graph_name"] = str(event_graph.get_fname())
            result["node_count"] = len(event_graph.nodes) if event_graph.nodes else 0

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

    print(f"[ue_extract] 完成。蓝图={result.get('is_blueprint', False)}")

    # 退出编辑器
    unreal.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main()