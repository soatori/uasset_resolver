# PLAN: Phase 4 — CLI 与验证

**Phase Number:** 4
**Goal:** 工具提供完整的命令行体验，包含加载策略回退和已验证的输出正确性。
**Requirements:** OUT-03, LOAD-01, LOAD-02, VERIFY-01
**Depends on:** Phase 2B (CUE4Parse 后端), Phase 3 (输出格式化 — formatter.py 已存在)

---

## Context Summary

### 当前状态
- Phase 2B 完成：CUE4Parse 后端提取 12 节点，378ms
- `controller.py` 已有 `--format` / `--backend` / `--uasset` 参数，但以内部脚本形式运行
- `formatter.py` 已实现 `format_md()` 和 `format_json()`
- `cue4parse_extractor.py` 提供类型化 dataclass（BlueprintNode/Pin/Graph）
- `.usmap` 缺失导致坐标/GUID/Pins 为空（Phase 4 不解决此问题）

### 需求定义
| 需求 | 描述 |
|------|------|
| OUT-03 | 通过命令行参数选择输出格式（`--format md` / `--format json`） |
| LOAD-01 | 支持直接加载裸 `.uasset` 文件路径 |
| LOAD-02 | 如果裸文件加载失败，提示用户指定 UE 项目的 Content 目录 |
| VERIFY-01 | 对 `BP_FirstPersonCharacter.uasset` 的解析结果与 `蓝图节点文本参考.md` 对比验证 |

### 成功标准
1. 用户可通过单条 CLI 命令运行，使用 `--format md` 或 `--format json` 选择输出格式
2. 用户可传入裸 `.uasset` 文件路径并成功加载；若加载失败，显示清晰提示要求指定 UE 项目 Content 目录
3. 在 `BP_FirstPersonCharacter.uasset` 上运行工具的输出与 `蓝图节点文本参考.md` 中的关键字段匹配

---

## Tasks

### Task 1: CLI 入口点封装（OUT-03, LOAD-01, LOAD-02）

**文件：** `scripts/cli.py`（新建）

将 `controller.py` 的核心逻辑封装为可复用的库函数，创建独立的 CLI 入口点 `cli.py`，提供：

1. **单函数入口 `run(argv=None)`** — 接受 argv 参数列表，便于测试和作为 module 调用（`python -m scripts.cli`）
2. **参数解析** — 复用 controller.py 的 argparse 定义（--uasset, --format, --backend, --ue-path, --usmap, --timeout）
3. **加载策略**：
   - LOAD-01: 接受裸 `.uasset` 路径 → 自动复制到 `temp/Content/` 后用 CUE4Parse 或 UE headless 加载
   - LOAD-02: 裸文件加载失败 → 输出清晰错误信息，提示用户指定 `--content-dir` 参数（UE 项目的 Content 目录），或使用 `--auto-discover` 扫描同级目录查找 `.uproject`
4. **后端自动选择** — 默认 `--backend auto`，优先 CUE4Parse，回退 UE headless
5. **输出** — stdout 直接打印结果，stderr 打印日志/错误；支持 `--output` 写入文件
6. **验证触发** — 支持 `--verify` 标志，提取完成后自动调用 `verify.py` 对结果进行交叉验证（VERIFY-01），验证报告追加到输出末尾

**不变性约束：**
- 不修改 `controller.py` 现有逻辑（向后兼容）
- 不修改 `cue4parse_extractor.py` / `formatter.py`
- 新建 `cli.py` 只调用已有模块的公开接口

**files:** `scripts/cli.py`, `scripts/__init__.py`
**action:** create
**verify:** `python -m scripts.cli --help` 显示用法信息，包含 --format, --backend, --uasset, --output, --verify, --content-dir 参数
**done:** `python -m scripts.cli --help` 返回 0，输出包含参数列表

### Task 2: 加载策略实现（LOAD-01, LOAD-02）

**文件：** `scripts/cli.py`（Task 1 的扩展）

实现 `resolve_asset_path()` 函数：

```
输入: 用户传入的路径（裸文件 / Content 目录 / .uproject）
流程:
  1. 如果是 .uasset 文件 → 直接加载（LOAD-01）
  2. 如果加载失败 → 提示指定 --content-dir（LOAD-02）
  3. 如果传入目录 → 扫描 .uasset 文件，提示选择
输出: (uasset_path, content_dir) 元组
```

**files:** `scripts/cli.py`
**action:** update
**verify:** 传入不存在的路径时，stderr 输出包含 "请指定 --content-dir" 提示；传入有效 .uasset 路径时成功加载
**done:** LOAD-01 和 LOAD-02 两条路径均走通，错误信息可读

### Task 3: 交叉验证模块（VERIFY-01）

读取 `蓝图节点文本参考.md`，解析其中的 `Begin Object ... End Object` 块，提取参考数据（节点类型、名称、函数引用、引脚结构）。

实现 `verify_output(result_dict) -> VerificationReport`：

```
对比维度:
  1. 节点数量匹配
  2. 节点名称集合匹配
  3. 函数引用匹配（CallFunction 节点）
  4. 引脚结构匹配（PinId/PinName/PinType/Direction）
  5. 连线关系匹配

输出:
  - 匹配项列表
  - 不匹配项列表（预期 vs 实际）
  - 缺失项列表
  - 总体 PASS/FAIL 判定
```

**注意：** .usmap 缺失导致坐标/GUID 为空，验证模块跳过 NodePosX/NodePosY/NodeGuid 字段比对。

**files:** `scripts/verify.py`
**action:** create
**verify:** `python -m scripts.verify --reference "蓝图节点文本参考.md" --result temp/result.json` 输出 PASS/FAIL 报告
**done:** 对 BP_FirstPersonCharacter.uasset 的提取结果运行验证，输出 PASS 报告，且 `scripts/cli.py` 支持 `--verify` 标志自动调用此模块

### Task 4: 端到端冒烟测试

3 个集成测试：
1. `--format json` 输出可解析为合法 JSON，包含 nodes/connections 字段
2. `--format md` 输出包含 Begin Object / End Object 块
3. `--backend cue4parse` 对 `BP_FirstPersonCharacter.uasset` 提取结果通过验证（VERIFY-01）

**files:** `scripts/test_cli.py`
**action:** create
**verify:** `python -m pytest scripts/test_cli.py -v` 全部 3 个测试通过
**done:** pytest 输出 `3 passed`

### Task 5: 验证与文档

1. 对 `BP_FirstPersonCharacter.uasset` 运行 `python -m scripts.cli --backend cue4parse --format json`
2. 运行 `python -m scripts.cli --backend cue4parse --format json --verify` 确认关键字段匹配
3. 创建 VERIFICATION.md
4. 更新 `.planning/STATE.md`（标记 Phase 4 完成）
5. 更新 `.planning/ROADMAP.md`（Phase 4 打勾，覆盖率表更新）

**files:** `.planning/phases/04-cli-validation/VERIFICATION.md`, `.planning/STATE.md`, `.planning/ROADMAP.md`
**action:** create, update
**verify:** VERIFICATION.md 包含 E2E 结果摘要（退出码、节点数、验证结果）；STATE.md workflow 标记为 complete；ROADMAP.md Phase 4 checkbox 为 [x]
**done:** 3 个文件均已更新，commit 记录完整

---

## Wave 编排

| Wave | Tasks | 并行 | 依赖 |
|------|-------|------|------|
| 1 | Task 1 | 否 | 无 |
| 2 | Task 2 | 否 | Task 1（cli.py 框架） |
| 3 | Task 3 | 否 | Task 2（需提取结果用于验证） |
| 4 | Task 4, Task 5 | 否 | Task 3（验证模块就绪） |

---

## Risks

1. **参考文件缺失或格式不一致** — `蓝图节点文本参考.md` 可能不存在或格式不匹配参考文档。需要先确认文件存在且可解析。
2. **LOAD-02 提示的用户体验** — 命令行中"提示用户指定 Content 目录"在没有交互式 TUI 的情况下退化为错误信息输出，需要确保信息清晰可操作。
3. **VERIFY-01 的坐标/GUID 比对** — 由于 .usmap 缺失，坐标和 GUID 将为空，验证模块需要跳过这些字段或使用降级策略。
