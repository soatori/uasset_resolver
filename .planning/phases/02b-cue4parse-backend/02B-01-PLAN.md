# PLAN: Phase 2B-01 — CUE4Parse Python 封装

> 创建 Python 模块封装 BPExtractor.exe，提供类型化数据接口。

---
wave: 2
depends_on: ["Phase 2B Wave 1 (BPExtractor.exe 已编译发布)"]
requirements: [PARSE-03]
must_haves:
  - "scripts/cue4parse_extractor.py 可被其他模块 import"
  - "extract_to_dict() 返回可序列化 dict"
  - "错误处理覆盖：exe 不存在、非零退出码、JSON 失败、超时"
  - "至少一个测试文件验证基本功能"
files_modified: []
files_created:
  - "scripts/cue4parse_extractor.py"
  - "scripts/test_cue4parse_extractor.py"
---

## Context

BPExtractor.exe 已编译发布到 `engines/bp_extractor/`。需要 Python 封装层，使其可被控制器和其他模块调用。

**已知限制**：.usmap 缺失，坐标/GUID/Pins 将为空 — 这是 BPExtractor 层面的限制，非本 Wave 解决范围。

## Tasks

### Task 1: 创建 cue4parse_extractor.py

<task>
<files>scripts/cue4parse_extractor.py</files>
<action>
创建 Python 数据类和封装类：

1. Dataclass `BlueprintPin`: pin_id, pin_name, direction, pin_category, pin_sub_category, default_value, linked_to, is_reference, is_const, container_type
2. Dataclass `BlueprintNode`: node_type, name, pos_x, pos_y, guid, function_name, pins(list[BlueprintPin]), note
3. Dataclass `BlueprintGraph`: package_name, blueprint_class, graphs(list[str]), nodes(list[BlueprintNode]), warnings(list[str])
4. 异常类 `BPExtractorError(Exception)`，子类 `ExtractorNotFoundError`, `ExtractorTimeoutError`, `ExtractorParseError`
5. 类 `BPExtractor`:
   - `__init__(exe_path=None, ue_version="UE5_7", usmap_path=None, timeout=30)`
   - exe_path 默认自动发现 `engines/bp_extractor/BPExtractor.exe`（相对于项目根目录）
   - `_find_default_exe()`: 向上查找包含 BPExtractor.exe 的目录
   - `extract_to_dict(uasset_path) -> dict`: subprocess 调用 exe，解析 JSON stdout
     - 构建命令: `BPExtractor.exe <uasset_path> --ue-version UE5_7 [--usmap <path>]`
     - timeout 使用构造函数传入的值
     - 解析 stdout JSON，转换为 dict
   - `extract(uasset_path) -> BlueprintGraph`: 调用 extract_to_dict，将 dict 转为 dataclass 对象
6. 错误处理:
   - exe 不存在 → BPExtractorNotFoundError
   - subprocess 退出码 != 0 → BPExtractorError（含 stderr）
   - stdout 非合法 JSON → BPExtractorParseError
   - subprocess 超时 → BPExtractorTimeoutError
</action>
<verify>
- `python -c "from scripts.cue4parse_extractor import BPExtractor; print('OK')"` 不报错
- `BPExtractor()._find_default_exe()` 返回存在的 .exe 路径
</verify>
<done>cue4parse_extractor.py 可被 import，BPExtractor 实例化成功</done>
</task>

### Task 2: 创建测试文件

<task>
<files>scripts/test_cue4parse_extractor.py</files>
<action>
使用 unittest 编写测试：

1. `TestBPExtractor.test_extract_to_dict`: 对 BP_FirstPersonCharacter.uasset 调用 extract_to_dict，验证返回 dict 包含 package_name、nodes 列表、node_count >= 5（已知限制：无 .usmap，坐标/GUID/pins 为空）
2. `TestBPExtractor.test_extract_returns_graph`: 验证 extract() 返回 BlueprintGraph dataclass 实例
3. `TestBPExtractor.test_nonexistent_file`: 传入不存在的路径，验证抛出 BPExtractorError
4. `TestBPExtractor.test_exe_not_found`: 构造不存在的 exe 路径，验证抛出 BPExtractorNotFoundError
5. `TestBPExtractor.test_auto_detect_exe`: 验证默认自动发现能找到 BPExtractor.exe
</action>
<verify>
- `python -m pytest scripts/test_cue4parse_extractor.py -v` 全部通过
</verify>
<done>测试文件存在且全部通过</done>
</task>
