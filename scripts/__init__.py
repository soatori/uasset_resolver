"""uasset_resolver — Unreal Engine .uasset 蓝图节点提取工具。"""

# 后端函数（从 controller.py）
from controller import (
    _run_cue4parse_backend,
    _run_ue_headless_backend,
    _select_backend_auto,
    find_ue_editor,
    find_ue_via_registry,
    find_ue_via_known_paths,
    prepare_asset,
    run_ue_headless,
    read_result,
    cache_ue_path,
    derive_virtual_path,
)

# CLI 入口
from main import run

__all__ = [
    "run",
    "_run_cue4parse_backend",
    "_run_ue_headless_backend",
    "_select_backend_auto",
    "find_ue_editor",
    "find_ue_via_registry",
    "find_ue_via_known_paths",
    "prepare_asset",
    "run_ue_headless",
    "read_result",
    "cache_ue_path",
    "derive_virtual_path",
]
