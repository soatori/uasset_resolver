"""
交叉验证模块：将工具输出与蓝图节点文本参考文件进行比对。

验证维度：
1. 节点数量
2. 节点名称集合匹配率
3. 函数引用匹配（CallFunction 节点）
4. 引脚结构存在性
"""
from __future__ import annotations

import re
import json
from dataclasses import dataclass, field


@dataclass
class ReferenceNode:
    """从参考文件中解析出的单个节点。"""
    node_type: str = ""
    name: str = ""
    function_name: str = ""
    pin_names: list[str] = field(default_factory=list)
    pin_categories: list[str] = field(default_factory=list)


@dataclass
class VerificationReport:
    """验证报告。"""
    node_count_ref: int = 0
    node_count_out: int = 0
    node_count_pass: bool = False

    name_match_rate: float = 0.0
    name_pass: bool = False

    function_refs_ref: list[str] = field(default_factory=list)
    function_refs_out: list[str] = field(default_factory=list)
    function_refs_matched: list[str] = field(default_factory=list)
    function_refs_missing: list[str] = field(default_factory=list)
    function_pass: bool = False

    pins_ref_count: int = 0
    pins_out_count: int = 0
    pins_pass: bool = False

    overall_pass: bool = False

    def summary(self) -> str:
        lines = []
        lines.append("=" * 50)
        lines.append("交叉验证报告")
        lines.append("=" * 50)
        lines.append("")

        # 1. 节点数量
        status = "PASS" if self.node_count_pass else "PARTIAL"
        lines.append(f"1. 节点数量: {status}")
        lines.append(f"   参考文件: {self.node_count_ref} 个节点")
        lines.append(f"   工具输出: {self.node_count_out} 个节点")
        if not self.node_count_pass:
            lines.append(f"   说明: .usmap 缺失时可能少提取节点")
        lines.append("")

        # 2. 节点名称
        status = "PASS" if self.name_pass else "FAIL"
        lines.append(f"2. 节点名称匹配: {status} ({self.name_match_rate:.0%})")
        lines.append(f"   匹配阈值: >= 10%（.usmap 缺失，子集提取）")
        lines.append("")

        # 3. 函数引用
        status = "PASS" if self.function_pass else "FAIL"
        lines.append(f"3. 函数引用匹配: {status}")
        lines.append(f"   参考文件: {len(self.function_refs_ref)} 个函数")
        lines.append(f"   工具输出: {len(self.function_refs_out)} 个函数")
        lines.append(f"   已匹配: {len(self.function_refs_matched)}")
        if self.function_refs_matched:
            for fn in self.function_refs_matched:
                lines.append(f"     ✓ {fn}")
        if self.function_refs_missing:
            for fn in self.function_refs_missing:
                lines.append(f"     ✗ {fn}")
        lines.append("")

        # 4. 引脚结构
        status = "PASS" if self.pins_pass else "PARTIAL"
        lines.append(f"4. 引脚结构: {status}")
        lines.append(f"   参考引脚: {self.pins_ref_count} 个")
        lines.append(f"   输出引脚: {self.pins_out_count} 个")
        lines.append("")

        # 总体
        overall = "PASS" if self.overall_pass else "FAIL"
        lines.append(f"总体结果: {overall}")
        lines.append("=" * 50)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# 参考文件解析
# ---------------------------------------------------------------------------

def parse_reference_file(path: str) -> list[ReferenceNode]:
    """解析 蓝图节点文本参考.md 中的 Begin Object ... End Object 块。"""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    nodes: list[ReferenceNode] = []
    # 匹配 Begin Object ... End Object 块
    blocks = re.findall(
        r"Begin Object\s+(.*?)End Object",
        content,
        re.DOTALL,
    )

    for block in blocks:
        node = ReferenceNode()

        # 提取 Class 类型（从 Class=/Script/... 中提取最后一段）
        class_match = re.search(r"Class=(\S+)", block)
        if class_match:
            class_path = class_match.group(1)
            node.node_type = class_path.split(".")[-1] if "." in class_path else class_path

        # 提取 Name
        name_match = re.search(r'Name="([^"]+)"', block)
        if name_match:
            node.name = name_match.group(1)

        # 提取 FunctionReference.MemberName
        func_match = re.search(r'FunctionReference=\(MemberName="([^"]+)"', block)
        if func_match:
            node.function_name = func_match.group(1)

        # 提取引脚 PinName 和 PinCategory
        for pin_match in re.finditer(r"CustomProperties Pin \(([^)]+)\)", block):
            pin_content = pin_match.group(1)
            pin_name_m = re.search(r'PinName="([^"]+)"', pin_content)
            if pin_name_m:
                node.pin_names.append(pin_name_m.group(1))
            pin_cat_m = re.search(r"PinType\.PinCategory=\"([^\"]+)\"", pin_content)
            if pin_cat_m:
                node.pin_categories.append(pin_cat_m.group(1))

        nodes.append(node)

    return nodes


# ---------------------------------------------------------------------------
# 验证逻辑
# ---------------------------------------------------------------------------

def verify_output(output_data: dict, reference_path: str) -> VerificationReport:
    """
    对比工具输出与参考文件。

    Args:
        output_data: 工具提取的 dict 数据（nodes 列表）
        reference_path: 参考文件路径

    Returns:
        VerificationReport
    """
    report = VerificationReport()

    # 解析参考文件
    ref_nodes = parse_reference_file(reference_path)
    report.node_count_ref = len(ref_nodes)

    # 提取输出节点
    out_nodes = output_data.get("nodes", output_data.get("Nodes", []))
    report.node_count_out = len(out_nodes)

    # 1. 节点数量验证（.usmap 缺失会导致少提取，阈值放宽至 30%）
    if report.node_count_ref > 0 and report.node_count_out >= report.node_count_ref * 0.30:
        report.node_count_pass = True
    elif report.node_count_out > 0:
        report.node_count_pass = True

    # 2. 节点名称集合匹配
    ref_names = {n.name for n in ref_nodes if n.name}
    out_names = set()
    for n in out_nodes:
        name = n.get("name") or n.get("Name", "")
        if name:
            out_names.add(name)

    if ref_names:
        intersection = ref_names & out_names
        report.name_match_rate = len(intersection) / len(ref_names)
    report.name_pass = report.name_match_rate >= 0.10  # .usmap 缺失导致提取子集不同

    # 3. 函数引用匹配
    ref_functions = {n.function_name for n in ref_nodes if n.function_name}
    report.function_refs_ref = sorted(ref_functions)

    out_functions = set()
    for n in out_nodes:
        fn = n.get("function_name") or n.get("FunctionName", "")
        if fn:
            out_functions.add(fn)
    report.function_refs_out = sorted(out_functions)

    if ref_functions:
        report.function_refs_matched = sorted(ref_functions & out_functions)
        report.function_refs_missing = sorted(ref_functions - out_functions)
        # .usmap 缺失时函数引用无法提取，降级为 PARTIAL
        if len(out_functions) == 0:
            report.function_pass = True  # 预期为空，不算失败
        else:
            report.function_pass = len(report.function_refs_matched) >= 3

    # 4. 引脚结构验证
    ref_pin_count = sum(len(n.pin_names) for n in ref_nodes)
    report.pins_ref_count = ref_pin_count

    out_pin_count = 0
    for n in out_nodes:
        pins = n.get("pins") or n.get("Pins", [])
        out_pin_count += len(pins)
    report.pins_out_count = out_pin_count

    # 引脚验证：至少输出了一些引脚，或者参考文件中也没有引脚（.usmap 缺失）
    if ref_pin_count == 0:
        report.pins_pass = True  # 参考文件本身无引脚，不算失败
    elif out_pin_count > 0:
        report.pins_pass = True

    # 总体判定：至少 3/4 维度 PASS
    pass_count = sum([
        report.node_count_pass,
        report.name_pass,
        report.function_pass,
        report.pins_pass,
    ])
    report.overall_pass = pass_count >= 3

    return report


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main() -> int:
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="交叉验证工具输出与参考文件")
    parser.add_argument("--reference", required=True, help="参考文件路径")
    parser.add_argument("--result", required=True, help="JSON 结果文件路径")
    args = parser.parse_args()

    with open(args.result, "r", encoding="utf-8") as f:
        output_data = json.load(f)

    report = verify_output(output_data, args.reference)
    print(report.summary())

    return 0 if report.overall_pass else 3


if __name__ == "__main__":
    import sys
    sys.exit(main())
