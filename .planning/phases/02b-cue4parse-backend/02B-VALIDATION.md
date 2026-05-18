# VALIDATION: Phase 2B — CUE4Parse Backend

## Test Definitions

### T-2B-01: Python 封装模块可导入
**Given**: cue4parse_extractor.py 已创建
**When**: `python -c "from scripts.cue4parse_extractor import BPExtractor, BlueprintGraph, BlueprintNode, BlueprintPin, BPExtractorError"`
**Then**: 无异常退出

### T-2B-02: BPExtractor 自动发现 exe
**Given**: BPExtractor.exe 存在于 engines/bp_extractor/
**When**: `BPExtractor()._find_default_exe()`
**Then**: 返回存在的 .exe 绝对路径

### T-2B-03: extract_to_dict 返回有效 JSON
**Given**: BP_FirstPersonCharacter.uasset 存在于项目根目录
**When**: `BPExtractor().extract_to_dict("BP_FirstPersonCharacter.uasset")`
**Then**: 返回 dict，包含 package_name、nodes、node_count 字段

### T-2B-04: 节点数量 >= 5
**Given**: extract_to_dict 成功
**When**: 检查 node_count
**Then**: node_count >= 5（已知 .usmap 缺失限制下）

### T-2B-05: 错误处理 — 不存在的文件
**Given**: 有效的 BPExtractor 实例
**When**: extract_to_dict("nonexistent.uasset")
**Then**: 抛出 BPExtractorError

### T-2B-06: 错误处理 — exe 不存在
**Given**: BPExtractor(exe_path="/nonexistent/BPExtractor.exe")
**When**: extract_to_dict(any_path)
**Then**: 抛出 BPExtractorNotFoundError

### T-2B-07: 端到端 CLI — cue4parse_controller
**Given**: cue4parse_controller.py 已创建
**When**: `python scripts/cue4parse_controller.py --uasset BP_FirstPersonCharacter.uasset`
**Then**: 退出码 0，输出 JSON 包含 "backend": "cue4parse"

### T-2B-08: 端到端 CLI — controller.py --backend cue4parse
**Given**: controller.py 已更新
**When**: `python scripts/controller.py --backend cue4parse --uasset BP_FirstPersonCharacter.uasset`
**Then**: 退出码 0，JSON 输出有效

### T-2B-09: 向后兼容 — controller.py --backend ue-headless
**Given**: controller.py 已更新
**When**: `python scripts/controller.py --backend ue-headless --uasset BP_FirstPersonCharacter.uasset`
**Then**: 行为与更新前相同（UE headless 流程）

### T-2B-10: 性能 — CUE4Parse < 10 秒
**Given**: BPExtractor.exe 和 cue4parse_controller.py 可用
**When**: 计时运行 extract_to_dict
**Then**: 执行时间 < 10000ms

### T-2B-11: .gitignore 包含 engines/bp_extractor/
**Given**: .gitignore 已更新
**When**: `git status engines/bp_extractor/`
**Then**: 文件被忽略（不显示为 untracked）
