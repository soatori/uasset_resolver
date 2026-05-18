#!/usr/bin/env python
"""
uasset_resolver — Unreal Engine .uasset 蓝图节点提取工具 v0.1.0

统一 CLI 入口，整合 CUE4Parse 和 UE headless 两种后端。

用法：
  python scripts/main.py <uasset> [选项]
  python -m scripts.main <uasset> [选项]

示例：
  python scripts/main.py BP_FirstPersonCharacter.uasset
  python scripts/main.py BP_Test.uasset --format md --output result.md
  python scripts/main.py test.uasset --backend auto --format json
  python scripts/main.py test.uasset --backend cue4parse --usmap mappings.usmap
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import textwrap


def _resolve_project_root() -> str:
    """获取项目根目录（向上查找 temp/minimal.uproject）。"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    # scripts/ 的父目录即为项目根
    project_root = os.path.dirname(project_root)
    return project_root


# ---------------------------------------------------------------------------
# 后端函数 — 从 controller.py 导入
# ---------------------------------------------------------------------------

def _run_cue4parse_backend(uasset_path: str, output_path: str,
                           usmap_path: str | None, timeout: int,
                           project_root: str, output_format: str = "json") -> int:
    """使用 CUE4Parse 后端提取蓝图节点。"""
    scripts_dir = os.path.join(project_root, "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        from cue4parse_extractor import BPExtractor, BPExtractorError
    except ImportError as exc:
        print(f"[main] 错误：无法导入 cue4parse_extractor：{exc}", file=sys.stderr)
        return 1

    try:
        extractor = BPExtractor(
            ue_version="UE5_7",
            usmap_path=usmap_path,
            timeout=timeout,
        )
    except Exception as exc:
        print(f"[main] 错误：无法初始化 BPExtractor：{exc}", file=sys.stderr)
        return 1

    print(f"[main] 使用 CUE4Parse 后端提取：{uasset_path}")
    start_ms = time.monotonic()
    try:
        data = extractor.extract_to_dict(uasset_path)
    except BPExtractorError as exc:
        print(f"[main] CUE4Parse 提取失败：{exc}", file=sys.stderr)
        return 2
    elapsed_ms = round((time.monotonic() - start_ms) * 1000)

    if not isinstance(data, dict):
        data = {"raw": data}
    data["backend"] = "cue4parse"
    data["extraction_time_ms"] = elapsed_ms

    # 格式化输出
    if output_format == "md":
        from formatter import format_md
        output_text = format_md(data)
        output_ext = ".md"
    else:
        from formatter import format_json
        output_text = format_json(data)
        output_ext = ".json"

    # 处理输出路径扩展名
    final_path = output_path
    if output_path.endswith(".json") and output_ext == ".md":
        final_path = output_path[:-5] + output_ext
    elif output_path.endswith(".md") and output_ext == ".json":
        final_path = output_path[:-3] + output_ext

    os.makedirs(os.path.dirname(os.path.abspath(final_path)), exist_ok=True)
    with open(final_path, "w", encoding="utf-8") as f:
        f.write(output_text)

    node_count = len(data.get("Nodes", data.get("nodes", [])))
    print(f"[main] CUE4Parse 提取完成：{node_count} 个节点，耗时 {elapsed_ms}ms")
    return 0


def _run_ue_headless_backend(project_root: str, uasset_path: str,
                              output_path: str, timeout: int,
                              ue_override: str | None = None,
                              output_format: str = "json") -> int:
    """UE headless 后端提取流程。"""
    # 延迟导入 controller.py 的函数以避免循环依赖
    scripts_dir = os.path.join(project_root, "scripts")
    sys.path.insert(0, scripts_dir)
    from controller import (
        find_ue_editor, cache_ue_path, prepare_asset,
        run_ue_headless, read_result,
    )

    cache_path = os.path.join(project_root, "temp", "ue_config.json")
    ue_exe = find_ue_editor(cache_path, ue_override)
    if not ue_exe:
        print("[main] 错误：无法找到 UE 5.7 引擎", file=sys.stderr)
        print("[main] 请通过 --ue-path 参数指定引擎路径", file=sys.stderr)
        return 1

    if not os.path.exists(cache_path):
        cache_ue_path(ue_exe, cache_path)

    content_dir = os.path.join(project_root, "temp", "Content")
    virtual_path = prepare_asset(uasset_path, content_dir)
    if not virtual_path:
        return 1

    project_path = os.path.join(project_root, "temp", "minimal.uproject")
    script_path = os.path.join(project_root, "scripts", "ue_extract.py")

    exit_code = run_ue_headless(ue_exe, project_path, script_path, output_path, timeout)

    result = read_result(output_path)
    if result:
        print("\n[main] === 结果摘要 ===")
        print(f"  资产路径：{result.get('asset_path', 'N/A')}")
        print(f"  资产类型：{result.get('asset_class', 'N/A')}")
        print(f"  是否蓝图：{result.get('is_blueprint', False)}")
        if result.get('is_blueprint'):
            print(f"  生成类：{result.get('generated_class', 'N/A')}")
            print(f"  父类：{result.get('parent_class', 'N/A')}")
            print(f"  有 EventGraph：{result.get('has_event_graph', False)}")
        if result.get('error'):
            print(f"  错误：{result.get('error')}")
        print("[main] === 完成 ===")

    if exit_code == 0 and result and result.get('is_blueprint'):
        print("[main] 成功")
        return 0
    else:
        print(f"[main] 失败（退出码={exit_code}）")
        return 1


def _select_backend_auto(uasset_path: str, output_path: str,
                         timeout: int, project_root: str,
                         usmap_path: str | None = None,
                         output_format: str = "json") -> int:
    """auto 模式：先尝试 CUE4Parse，失败回退 ue-headless。"""
    scripts_dir = os.path.join(project_root, "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        from cue4parse_extractor import BPExtractor
        exe_path = BPExtractor._find_default_exe()
        cue4parse_available = exe_path.is_file()
    except Exception:
        cue4parse_available = False

    if cue4parse_available:
        print("[main] auto 模式：尝试 CUE4Parse 后端...")
        rc = _run_cue4parse_backend(uasset_path, output_path, usmap_path, timeout, project_root, output_format)
        if rc == 0:
            return 0
        print("[main] CUE4Parse 失败，回退到 UE headless 后端...")

    print("[main] auto 模式：使用 UE headless 后端")
    return _run_ue_headless_backend(project_root, uasset_path, output_path, timeout)


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def run(argv: list[str] | None = None) -> int:
    """主入口函数，接受 argv 参数列表，便于测试和模块调用。"""
    parser = argparse.ArgumentParser(
        prog="uasset_resolver",
        description=textwrap.dedent("""\
            Unreal Engine .uasset 蓝图节点提取工具 v0.1.0

            从二进制 .uasset 文件中反序列化出蓝图事件图（EventGraph）的节点结构，
            包括节点类型、函数引用、引脚定义和连线关系。

            支持两种后端：
              CUE4Parse   — C# 二进制解析（推荐，快速，~400ms）
              UE headless — UE 编辑器无头模式（慢，需要完整引擎）
        """),
        epilog=textwrap.dedent("""\
            示例：
              python scripts/main.py BP_Test.uasset
              python scripts/main.py BP_Test.uasset --format md
              python scripts/main.py BP_Test.uasset --backend auto --format json
              python scripts/main.py C:/path/to/BP.uasset --backend cue4parse
        """),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # 基本参数组
    basic_group = parser.add_argument_group("基本参数")
    basic_group.add_argument(
        "uasset",
        help=".uasset 文件路径（支持绝对路径和相对路径）",
    )
    basic_group.add_argument(
        "--version",
        action="version",
        version="uasset_resolver 0.1.0",
    )

    # 后端参数组
    backend_group = parser.add_argument_group("后端参数")
    backend_group.add_argument(
        "--backend",
        choices=["cue4parse", "ue-headless", "auto"],
        default="auto",
        metavar="MODE",
        help="后端选择：cue4parse（C# 二进制解析，推荐）、ue-headless（UE 无头模式）、auto（优先 CUE4Parse，失败回退，默认）",
    )
    backend_group.add_argument(
        "--ue-path",
        metavar="PATH",
        default=None,
        help="UE 引擎路径覆盖（仅 ue-headless/auto 模式）",
    )
    backend_group.add_argument(
        "--usmap",
        metavar="PATH",
        default=None,
        help=".usmap 映射文件路径（仅 cue4parse 模式，用于解析无版本属性）",
    )
    backend_group.add_argument(
        "--timeout",
        type=int,
        default=30,
        metavar="SECS",
        help="后端超时秒数（默认 30，cue4parse）或 300（ue-headless）",
    )

    # 输出参数组
    output_group = parser.add_argument_group("输出参数")
    output_group.add_argument(
        "--format",
        choices=["json", "md"],
        default="json",
        metavar="FMT",
        help="输出格式：json（结构化 JSON，默认）、md（UE 编辑器文本格式）",
    )
    output_group.add_argument(
        "--output",
        metavar="PATH",
        default=None,
        help="输出文件路径（默认：temp/result.json 或 .md，随 --format 变化）",
    )

    args = parser.parse_args(argv)

    # 解析项目根目录
    project_root = _resolve_project_root()

    # 验证 uasset 文件存在
    uasset_abs = os.path.abspath(args.uasset)
    if not os.path.isfile(uasset_abs):
        print(f"[main] 错误：uasset 文件不存在：{uasset_abs}", file=sys.stderr)
        return 1

    if not uasset_abs.lower().endswith(".uasset"):
        print(f"[main] 错误：文件不是 .uasset 格式：{uasset_abs}", file=sys.stderr)
        return 1

    # 默认输出路径
    if args.output:
        output_path = os.path.abspath(args.output)
    else:
        output_ext = ".json" if args.format == "json" else ".md"
        output_path = os.path.join(project_root, f"temp/result{output_ext}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 根据 backend 分支
    if args.backend == "cue4parse":
        rc = _run_cue4parse_backend(
            uasset_abs, output_path, args.usmap, args.timeout, project_root, args.format
        )
    elif args.backend == "ue-headless":
        # ue-headless 默认超时 300s
        ue_timeout = args.timeout if args.timeout != 30 else 300
        rc = _run_ue_headless_backend(
            project_root, uasset_abs, output_path, ue_timeout, args.ue_path, args.format
        )
    else:  # auto
        rc = _select_backend_auto(
            uasset_abs, output_path, args.timeout, project_root, args.usmap, args.format
        )

    if rc == 0:
        print(f"[main] 结果已写入：{output_path}")

    return rc


if __name__ == "__main__":
    sys.exit(run())
