# PLAN: Phase 2B-03 — 验证与文档

> 端到端验证、性能测量、项目文档更新。

---
wave: 5
depends_on: ["Phase 2B-02 (统一控制器)"]
requirements: [PARSE-03]
must_haves:
  - "端到端 CLI 命令成功执行"
  - "JSON 输出包含 >=9 节点"
  - "执行时间 < 10 秒（vs UE headless > 60s）"
  - "ROADMAP.md 更新 Phase 2B 状态"
  - ".gitignore 包含 engines/bp_extractor/"
files_modified:
  - ".planning/ROADMAP.md"
  - ".planning/STATE.md"
  - ".gitignore"
---

## Context

Wave 2-3 完成后，需要端到端验证和文档更新。

**已知限制**：.usmap 缺失，坐标/GUID/Pins 将为空。验证标准已调整。

## Tasks

### Task 1: 端到端验证

<task>
<files>scripts/cue4parse_controller.py</files>
<action>
运行端到端测试：

1. `python scripts/cue4parse_controller.py --uasset BP_FirstPersonCharacter.uasset`
2. 验证退出码 0
3. 验证 JSON 输出：
   - node_count >= 9（节点类型/名称应可提取）
   - backend == "cue4parse"
   - extraction_time_ms 存在
4. 记录实际提取的节点数量和执行时间
</action>
<verify>
- 命令退出码 0
- JSON 解析成功，node_count >= 9
- 执行时间 < 10000ms
</verify>
<done>端到端测试通过，记录性能数据</done>
</task>

### Task 2: 更新 .gitignore

<task>
<files>.gitignore</files>
<action>
添加 `engines/bp_extractor/` 到 .gitignore。该目录包含编译产物（.exe, .dll, .pdb），不应提交到 git。

确认 temp/ 已在 .gitignore 中。
</action>
<verify>
- `git status engines/bp_extractor/` 显示被 .gitignore 忽略
- 如果已追踪，需要 `git rm --cached -r engines/bp_extractor/`
</verify>
<done>engines/bp_extractor/ 被 .gitignore 排除</done>
</task>

### Task 3: 更新 ROADMAP.md 和 STATE.md

<task>
<files>.planning/ROADMAP.md, .planning/STATE.md</files>
<action>
更新 ROADMAP.md：
1. Phase 2B 状态标记为完成（或进行中状态更新）
2. 记录已知限制：.usmap 缺失导致坐标/GUID/Pins 为空
3. 更新进度表
4. 更新覆盖率表（PARSE-03 为完成，PARSE-04/05/06 仍为部分完成）

更新 STATE.md：
1. 当前阶段更新
2. 记录 Phase 2B Waves 2-3 完成状态
3. 记录遗留 .usmap 问题
</action>
<verify>
- ROADMAP.md Phase 2B 行显示完成状态
- 覆盖率表中 PARSE-03 标记为 Complete
</verify>
<done>ROADMAP.md 和 STATE.md 反映最新状态</done>
</task>
