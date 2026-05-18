"""BPExtractor 封装单元测试。

使用 unittest，无需 pytest。覆盖：
- extract_to_dict 返回结构
- extract 返回 BlueprintGraph
- 不存在文件的错误处理
- exe 未找到的错误处理
- 自动发现 exe
"""

import os
import unittest
from pathlib import Path

from scripts.cue4parse_extractor import (
    BPExtractor,
    BPExtractorError,
    BPExtractorNotFoundError,
    BPExtractorParseError,
    BPExtractorTimeoutError,
    BlueprintGraph,
    BlueprintNode,
    BlueprintPin,
)


# 测试文件路径（项目根目录下的 BP_FirstPersonCharacter.uasset）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_TEST_UASSET = _PROJECT_ROOT / "BP_FirstPersonCharacter.uasset"


class TestBPExtractor(unittest.TestCase):

    # -- 辅助 -------------------------------------------------------------------

    def setUp(self) -> None:
        self.extractor = BPExtractor()

    # -- 测试用例 ----------------------------------------------------------------

    def test_extract_to_dict(self) -> None:
        """对真实 .uasset 调用 extract_to_dict，验证返回结构。"""
        self.assertTrue(_TEST_UASSET.is_file(), f"Test file missing: {_TEST_UASSET}")

        result = self.extractor.extract_to_dict(_TEST_UASSET)

        self.assertIsInstance(result, dict)
        # BPExtractor 输出 PascalCase 键，兼容 snake_case
        pkg = result.get("package_name") or result.get("PackageName")
        self.assertIsNotNone(pkg, "Expected package_name or PackageName in result")
        nodes = result.get("nodes") or result.get("Nodes")
        self.assertIsInstance(nodes, list)
        self.assertGreaterEqual(
            len(nodes),
            5,
            "Expected at least 5 nodes in BP_FirstPersonCharacter",
        )

    def test_extract_returns_graph(self) -> None:
        """extract() 应返回 BlueprintGraph dataclass 实例。"""
        graph = self.extractor.extract(_TEST_UASSET)

        self.assertIsInstance(graph, BlueprintGraph)
        self.assertIsInstance(graph.nodes, list)
        self.assertGreaterEqual(len(graph.nodes), 5)
        # 每个节点都应该是 BlueprintNode
        for node in graph.nodes:
            self.assertIsInstance(node, BlueprintNode)

    def test_nonexistent_file(self) -> None:
        """传入不存在的 .uasset 路径应抛出 BPExtractorError。"""
        with self.assertRaises(BPExtractorError):
            self.extractor.extract_to_dict(
                _PROJECT_ROOT / "nonexistent_file_xyz.uasset"
            )

    def test_exe_not_found(self) -> None:
        """构造不存在的 exe 路径应抛出 BPExtractorNotFoundError。"""
        with self.assertRaises(BPExtractorNotFoundError):
            BPExtractor(exe_path=r"C:\nonexistent\path\BPExtractor.exe")

    def test_auto_detect_exe(self) -> None:
        """默认自动发现应能找到 BPExtractor.exe。"""
        extractor = BPExtractor()  # exe_path=None → auto-detect
        self.assertTrue(
            extractor.exe_path.is_file(),
            f"Auto-detected exe not found: {extractor.exe_path}",
        )
        self.assertEqual(extractor.exe_path.name, "BPExtractor.exe")


# -- 数据类快速测试（不依赖 exe） ----------------------------------------------


class TestDataclasses(unittest.TestCase):

    def test_blueprint_pin_defaults(self) -> None:
        pin = BlueprintPin()
        self.assertEqual(pin.pin_id, "")
        self.assertEqual(pin.linked_to, [])
        self.assertFalse(pin.is_reference)

    def test_blueprint_node_defaults(self) -> None:
        node = BlueprintNode()
        self.assertEqual(node.node_type, "")
        self.assertEqual(node.pins, [])

    def test_blueprint_graph_defaults(self) -> None:
        graph = BlueprintGraph()
        self.assertEqual(graph.package_name, "")
        self.assertEqual(graph.nodes, [])
        self.assertEqual(graph.warnings, [])


if __name__ == "__main__":
    unittest.main()
