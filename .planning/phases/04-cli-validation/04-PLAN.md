---
title: "Phase 4 — CLI 与验证"
created: 2026-05-19
phase: "4"
milestone: "0.1.0"
status: "planned"
plans: 1
waves: 4
---

# Phase 4: CLI 与验证

**目标:** 工具提供完整的命令行体验，包含加载策略回退和已验证的输出正确性。

**依赖:** Phase 3 (输出格式化), Phase 2B (CUE4Parse 后端)

**需求:** OUT-03, LOAD-01, LOAD-02, VERIFY-01

**成功标准**（必须满足）:
1. 用户可通过单条 CLI 命令运行，使用 `--format md` 或 `--format json` 选择输出格式
2. 用户可传入裸 .uasset 文件路径并成功加载；若加载失败，显示清晰提示要求指定 UE 项目 Content 目录
3. 在 `BP_FirstPersonCharacter.uasset` 上运行工具的输出与 `蓝图节点文本参考.md` 中的关键字段匹配（节点数量、节点名称、函数引用、引脚结构）

## 计划

- [ ] `04-01-PLAN.md` — CLI 统一入口、加载策略、交叉验证

## 当前状态分析

### 已有能力
- `scripts/controller.py` — 统一控制器，支持 `--backend cue4parse|ue-headless|auto`，`--format json|md`，`--output`，`--ue-path`
- `scripts/cue4parse_controller.py` — 独立 CUE4Parse CLI，支持 `--format`，`--output`，`--usmap`
- `scripts/formatter.py` — `format_md()` 和 `format_json()` 输出格式化
- `scripts/cue4parse_extractor.py` — BPExtractor Python 封装

### 差距（Phase 4 需解决）
1. **CLI 体验碎片化** — 两个入口（controller.py + cue4parse_controller.py），无统一主入口，无 `--help` 友好输出，无 `--version`
2. **加载策略** — 当前 controller.py 默认假设文件在项目根目录，未处理"裸 .uasset 文件"路径；CUE4Parse 可直接读取任意路径的 .uasset，但 UE headless 模式需要文件在 Content 目录
3. **交叉验证** — 无自动化验证逻辑对比输出与 `蓝图节点文本参考.md`

## 执行状态

- [ ] Wave 1: 统一 CLI 入口 — 合并两个控制器，完善参数/帮助/退出码
- [ ] Wave 2: 加载策略 — 裸 .uasset 直接加载（CUE4Parse），失败回退提示 Content 目录
- [ ] Wave 3: 交叉验证 — 输出与参考文件关键字段比对
- [ ] Wave 4: 端到端 UAT — 3 个成功标准全部验证通过
