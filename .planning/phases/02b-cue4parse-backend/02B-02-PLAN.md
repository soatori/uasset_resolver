# PLAN: Phase 2B-02 — 统一控制器

> 合并 CUE4Parse 和 UE headless 为统一 CLI 入口，支持 --backend 切换。

---
wave: 3
depends_on: ["Phase 2B-01 (Python 封装)"]
requirements: [PARSE-03]
must_haves:
  - "--backend cue4parse|ue-headless|auto 参数可用"
  - "auto 模式优先 CUE4Parse，失败回退 UE headless"
  - "输出 JSON 含 backend 字段标识实际使用的后端"
  - "现有 ue-headless 流程保持不变"
files_modified:
  - "scripts/controller.py"
files_created:
  - "scripts/cue4parse_controller.py"
---

## Context

Phase 2B-01 完成后，`cue4parse_extractor.py` 提供 Python API。需要统一的 CLI 入口让用户选择后端。

## Tasks

### Task 1: 创建 cue4parse_controller.py

<task>
<files>scripts/cue4parse_controller.py</files>
<action>
创建独立的 CUE4Parse 控制器：

1. argparse 参数:
   - `--uasset` (default: BP_FirstPersonCharacter.uasset)
   - `--output` (default: temp/cue4parse_result.json)
   - `--usmap` (optional, 默认 None)
   - `--timeout` (default: 30)
2. 流程:
   - 验证 uasset 文件存在
   - 实例化 BPExtractor (from cue4parse_extractor import BPExtractor)
   - 调用 extractor.extract_to_dict(uasset_path)
   - 在返回 dict 中注入 `{"backend": "cue4parse", "extraction_time_ms": <timing>}`
   - 写入 output JSON
3. 计时: 记录 extract_to_dict 执行时间
4. 退出码: 0=成功, 1=文件不存在/参数错误, 2=提取失败
</action>
<verify>
- `python scripts/cue4parse_controller.py --uasset BP_FirstPersonCharacter.uasset` 退出码 0
- 输出 JSON 包含 "backend": "cue4parse" 字段
</verify>
<done>cue4parse_controller.py 可独立运行，输出 JSON 结果</done>
</task>

### Task 2: 更新 controller.py 添加 --backend

<task>
<files>scripts/controller.py</files>
<action>
在现有 controller.py 中添加 --backend 参数和委派逻辑：

1. 添加 argparse 参数: `--backend` (choices: cue4parse, ue-headless, auto; default: ue-headless)
2. 在 main() 中，根据 backend 值分支:
   - `cue4parse`: import cue4parse_controller 的主逻辑（或 subprocess 调用）
   - `ue-headless`: 保持现有流程不变
   - `auto`: 先尝试 CUE4Parse（检查 BPExtractor.exe 存在），失败则回退 ue-headless
3. 输出 JSON 统一格式，含 `backend` 字段
4. 保持所有现有参数（--ue-path, --timeout, --output）向后兼容
</action>
<verify>
- `python scripts/controller.py --backend ue-headless --uasset BP_FirstPersonCharacter.uasset` 行为与之前相同
- `python scripts/controller.py --backend cue4parse --uasset BP_FirstPersonCharacter.uasset` 调用 CUE4Parse
- `--help` 显示 --backend 参数选项
</verify>
<done>controller.py 支持 --backend 切换，ue-headless 行为不变</done>
</task>
