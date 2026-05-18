"""CUE4Parse 封装 — 通过 BPExtractor.exe 从 .uasset 文件中提取蓝图节点信息。

提供类型化数据类（BlueprintPin / BlueprintNode / BlueprintGraph）
和 BPExtractor 封装类（subprocess 调用 + JSON 解析）。
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# 异常层次
# ---------------------------------------------------------------------------

class BPExtractorError(Exception):
    """BPExtractor 调用失败的基类异常。"""
    pass


class BPExtractorNotFoundError(BPExtractorError):
    """BPExtractor.exe 未找到。"""
    pass


class BPExtractorTimeoutError(BPExtractorError):
    """BPExtractor 执行超时。"""
    pass


class BPExtractorParseError(BPExtractorError):
    """stdout 输出无法解析为合法 JSON。"""
    pass


# ---------------------------------------------------------------------------
# 数据类
# ---------------------------------------------------------------------------

@dataclass
class BlueprintPin:
    """蓝图节点引脚。"""
    pin_id: str = ""
    pin_name: str = ""
    direction: str = ""
    pin_category: str = ""
    pin_sub_category: str = ""
    default_value: str = ""
    linked_to: List[str] = field(default_factory=list)
    is_reference: bool = False
    is_const: bool = False
    container_type: str = ""


@dataclass
class BlueprintNode:
    """蓝图事件图节点。"""
    node_type: str = ""
    name: str = ""
    pos_x: float = 0.0
    pos_y: float = 0.0
    guid: str = ""
    function_name: str = ""
    pins: List[BlueprintPin] = field(default_factory=list)
    note: str = ""


@dataclass
class BlueprintGraph:
    """从 .uasset 反序列化出的蓝图结构。"""
    package_name: str = ""
    blueprint_class: str = ""
    graphs: List[str] = field(default_factory=list)
    nodes: List[BlueprintNode] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 辅助：字典 → dataclass 转换
# ---------------------------------------------------------------------------

def _get(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """从字典中取值，按顺序尝试多个 key 名（兼容 PascalCase / snake_case）。"""
    for k in keys:
        if k in data:
            return data[k]
    return default


def _pin_from_dict(data: Dict[str, Any]) -> BlueprintPin:
    return BlueprintPin(
        pin_id=_get(data, "pin_id", "PinId", "pinId", default=""),
        pin_name=_get(data, "pin_name", "PinName", "pinName", default=""),
        direction=_get(data, "direction", "Direction", default=""),
        pin_category=_get(data, "pin_category", "PinCategory", "pinCategory", default=""),
        pin_sub_category=_get(data, "pin_sub_category", "PinSubCategory", "pinSubCategory", default=""),
        default_value=_get(data, "default_value", "DefaultValue", "defaultValue", default=""),
        linked_to=list(_get(data, "linked_to", "LinkedTo", default=[])),
        is_reference=bool(_get(data, "is_reference", "bIsReference", "isReference", default=False)),
        is_const=bool(_get(data, "is_const", "bIsConst", "isConst", default=False)),
        container_type=_get(data, "container_type", "ContainerType", default=""),
    )


def _node_from_dict(data: Dict[str, Any]) -> BlueprintNode:
    return BlueprintNode(
        node_type=_get(data, "node_type", "Type", default=""),
        name=_get(data, "name", "Name", default=""),
        pos_x=float(_get(data, "pos_x", "NodePosX", default=0)),
        pos_y=float(_get(data, "pos_y", "NodePosY", default=0)),
        guid=_get(data, "guid", "NodeGuid", default="") or "",
        function_name=_get(data, "function_name", "FunctionName", default="") or "",
        pins=[_pin_from_dict(p) for p in _get(data, "pins", "Pins", default=[])],
        note=_get(data, "note", "Note", default=""),
    )


def _graph_from_dict(data: Dict[str, Any]) -> BlueprintGraph:
    nodes_raw = _get(data, "nodes", "Nodes", default=[])
    return BlueprintGraph(
        package_name=_get(data, "package_name", "PackageName", default=""),
        blueprint_class=_get(data, "blueprint_class", "BlueprintClass", default=""),
        graphs=list(_get(data, "graphs", "Graphs", default=[])),
        nodes=[_node_from_dict(n) for n in nodes_raw],
        warnings=list(_get(data, "warnings", "Warnings", default=[])),
    )


# ---------------------------------------------------------------------------
# BPExtractor
# ---------------------------------------------------------------------------

class BPExtractor:
    """封装 BPExtractor.exe 的调用。

    参数
    ----
    exe_path : str | Path | None
        BPExtractor.exe 的绝对路径；为 None 时自动查找。
    ue_version : str
        UE 版本标识，默认 "UE5_7"。
    usmap_path : str | Path | None
        .usmap 映射文件路径；为 None 时不传入（坐标/GUID/pins 将为空）。
    timeout : int
        subprocess 超时秒数，默认 30。
    """

    _EXE_NAME = "BPExtractor.exe"

    def __init__(
        self,
        exe_path: Optional[str | os.PathLike] = None,
        ue_version: str = "UE5_7",
        usmap_path: Optional[str | os.PathLike] = None,
        timeout: int = 30,
    ) -> None:
        self.ue_version = ue_version
        self.usmap_path = usmap_path
        self.timeout = timeout

        if exe_path is not None:
            self.exe_path = Path(exe_path)
        else:
            self.exe_path = self._find_default_exe()

        if not self.exe_path.is_file():
            raise BPExtractorNotFoundError(
                f"BPExtractor.exe not found at: {self.exe_path}"
            )

    # -- 自动发现 ----------------------------------------------------------------

    @staticmethod
    def _find_default_exe() -> Path:
        """从当前文件向上查找 engines/bp_extractor/BPExtractor.exe。

        搜索策略：
        1. 相对于调用者所在目录的 `engines/bp_extractor/`
        2. 逐层向上查找父目录，最多 5 级
        """
        current = Path.cwd()
        for _ in range(6):  # cwd + 5 parents
            candidate = current / "engines" / "bp_extractor" / BPExtractor._EXE_NAME
            if candidate.is_file():
                return candidate
            if current.parent == current:
                break
            current = current.parent

        # 回退：相对于脚本所在文件的位置
        script_dir = Path(__file__).resolve().parent
        for _ in range(6):
            candidate = script_dir / "engines" / "bp_extractor" / BPExtractor._EXE_NAME
            if candidate.is_file():
                return candidate
            if script_dir.parent == script_dir:
                break
            script_dir = script_dir.parent

        raise BPExtractorNotFoundError(
            f"Could not auto-discover {BPExtractor._EXE_NAME}. "
            "Please pass exe_path explicitly."
        )

    # -- 公共 API ----------------------------------------------------------------

    def extract_to_dict(self, uasset_path: str | os.PathLike) -> Dict[str, Any]:
        """调用 BPExtractor.exe，解析 JSON stdout，返回 dict。

        抛出
        ----
        BPExtractorNotFoundError : exe 不存在
        BPExtractorTimeoutError  : 超时
        BPExtractorParseError    : stdout 非合法 JSON
        BPExtractorError         : 非零退出码或其他错误
        """
        uasset = Path(uasset_path)
        if not uasset.is_file():
            raise BPExtractorError(f"uasset file not found: {uasset}")

        cmd: List[str] = [str(self.exe_path), str(uasset), "--ue-version", self.ue_version]
        if self.usmap_path:
            cmd.extend(["--usmap", str(self.usmap_path)])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except FileNotFoundError:
            raise BPExtractorNotFoundError(f"Executable not found: {self.exe_path}")
        except subprocess.TimeoutExpired as exc:
            raise BPExtractorTimeoutError(
                f"BPExtractor timed out after {self.timeout}s: {exc}"
            ) from exc

        if result.returncode != 0:
            stderr = result.stderr.strip() or "(no stderr output)"
            raise BPExtractorError(
                f"BPExtractor exited with code {result.returncode}: {stderr}"
            )

        stdout = result.stdout.strip()
        if not stdout:
            raise BPExtractorParseError("BPExtractor produced empty stdout")

        try:
            data = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise BPExtractorParseError(
                f"Failed to parse BPExtractor stdout as JSON: {exc}\n"
                f"First 500 chars: {stdout[:500]}"
            ) from exc

        return data

    def extract(self, uasset_path: str | os.PathLike) -> BlueprintGraph:
        """调用 BPExtractor.exe，返回类型化 BlueprintGraph 对象。"""
        data = self.extract_to_dict(uasset_path)
        return _graph_from_dict(data)
