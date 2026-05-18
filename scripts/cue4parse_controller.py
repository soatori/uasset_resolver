"""
独立的 CUE4Parse 控制器：通过 BPExtractor.exe 从 .uasset 文件中提取蓝图节点信息。

用法：
  python scripts/cue4parse_controller.py [选项]
    --uasset PATH   .uasset 文件路径（默认：BP_FirstPersonCharacter.uasset）
    --format FMT    输出格式：json|md（默认：json）
    --output PATH   输出路径（默认：temp/cue4parse_result.json 或 .md）
    --usmap PATH    .usmap 映射文件路径（可选）
    --timeout SECS  超时秒数（默认：30）

退出码：0=成功, 1=文件不存在/参数错误, 2=提取失败
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser(
        description="CUE4Parse 蓝图节点提取控制器"
    )
    parser.add_argument(
        "--uasset",
        default="BP_FirstPersonCharacter.uasset",
        help=".uasset 文件路径（默认：BP_FirstPersonCharacter.uasset）",
    )
    parser.add_argument(
        "--format",
        choices=["json", "md"],
        default="json",
        help="输出格式：json（结构化 JSON）、md（UE 编辑器文本格式）",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="输出路径（默认：temp/cue4parse_result.json 或 .md，随 --format 变化）",
    )
    parser.add_argument(
        "--usmap",
        default=None,
        help=".usmap 映射文件路径（可选）",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="BPExtractor 超时秒数（默认：30）",
    )
    args = parser.parse_args()

    # 验证 uasset 文件存在
    uasset_abs = os.path.abspath(args.uasset)
    if not os.path.isfile(uasset_abs):
        print(f"[cue4parse] 错误：uasset 文件不存在：{uasset_abs}", file=sys.stderr)
        return 1

    # 导入 BPExtractor
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, scripts_dir)
    try:
        from cue4parse_extractor import BPExtractor, BPExtractorError
    except ImportError as exc:
        print(f"[cue4parse] 错误：无法导入 cue4parse_extractor：{exc}", file=sys.stderr)
        return 1

    # 实例化提取器
    try:
        extractor = BPExtractor(
            ue_version="UE5_7",
            usmap_path=args.usmap,
            timeout=args.timeout,
        )
    except Exception as exc:
        print(f"[cue4parse] 错误：无法初始化 BPExtractor：{exc}", file=sys.stderr)
        return 1

    # 执行提取并计时
    print(f"[cue4parse] 开始提取：{uasset_abs}")
    start_ms = time.monotonic()
    try:
        data = extractor.extract_to_dict(uasset_abs)
    except BPExtractorError as exc:
        print(f"[cue4parse] 提取失败：{exc}", file=sys.stderr)
        return 2
    elapsed_ms = round((time.monotonic() - start_ms) * 1000)

    # 注入后端标识和耗时
    if not isinstance(data, dict):
        data = {"raw": data}
    data["backend"] = "cue4parse"
    data["extraction_time_ms"] = elapsed_ms

    # 根据格式选择输出
    if args.format == "md":
        from formatter import format_md
        output_text = format_md(data)
        output_ext = ".md"
    else:
        from formatter import format_json
        output_text = format_json(data)
        output_ext = ".json"

    # 输出路径（默认随格式变化）
    if args.output:
        output_abs = os.path.abspath(args.output)
    else:
        output_abs = os.path.abspath(f"temp/cue4parse_result{output_ext}")
    os.makedirs(os.path.dirname(output_abs), exist_ok=True)
    with open(output_abs, "w", encoding="utf-8") as f:
        f.write(output_text)

    node_count = len(data.get("nodes", data.get("Nodes", [])))
    print(f"[cue4parse] 提取完成：{node_count} 个节点，耗时 {elapsed_ms}ms")
    print(f"[cue4parse] 结果已写入：{output_abs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
