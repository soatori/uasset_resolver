# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v0.1.0 — Initial Blueprint Parser

**Shipped:** 2026-05-19
**Phases:** 5 | **Plans:** 12 | **Commits:** 28

### What Was Built
- UE 5.7 无头桥接后端 — Python 控制 UE 编辑器无头提取
- CUE4Parse C# 二进制解析后端 — 直接解析 .uasset，~400ms 提取
- 双格式输出模块 — MD（UE 编辑器文本格式）+ JSON（结构化三级嵌套）
- 统一 CLI 入口 — 支持后端切换、格式选择、交叉验证

### What Worked
- 分阶段增量验证：每个计划完成后立即 UAT，问题早发现
- 决策开放：UE Python API 遇到限制后迅速切换到 CUE4Parse 替代方案，没有卡在原地
- GSD 分段工作流：每个 Wave/计划独立提交，上下文清晰
- CUE4Parse 社区项目：省去从零开始写二进制解析器的海量工作

### What Was Inefficient
- 初始阶段对 UE Python API 能力限制预估不足 — 需要第二轮研究替代方案
- .usmap 问题在 UE 5.7 中的变化没有提前查到（移除了 GenerateMappingFile），发现后只能暂挂
- 大量计划文档分散在 phase 目录，但这是 GSD 工作流要求，总体可接受

### Patterns Established
- **测试先行：** 输出格式化先写测试用例再实现，验证了格式正确性
- **双后端兼容：** 控制器同时支持 CUE4Parse 和 UE headless，可 fallback
- **PascalCase/snake_case 双兼容：** CUE4Parse 输出 PascalCase，代码同时兼容两种格式避免崩溃

### Key Lessons
1. **UE Python API 暴露程度比预期低很多** — 核心编辑器图形节点属性（NodeGuid、Pins）不暴露给 Python，不要依赖这个路径做完整提取
2. **CUE4Parse 是成熟方案** — 社区已经解决了大部分 .uasset 解析问题，集成比从零开始高效几个数量级
3. **UE 版本变化会移除功能** — UE 5.7 移除了 GenerateMappingFile 命令let，导致 .usmap 生成问题需要重新研究解决方案
4. **分阶段接受不完整** — 架构先验证可行，数据完整度留给后续里程碑，这个节奏正确

### Cost Observations
- Model mix: 0% opus, 0% sonnet, 100% doubao-seed-2.0-lite (user configured)
- Sessions: ~3
- Notable: Parallel subagent execution for research sped up alternatives exploration significantly

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v0.1.0 | ~3 | 5 | Initial project setup, GSD workflow baseline |

### Cumulative Quality

| Milestone | Tests | Zero-Dep Additions |
|-----------|-------|--------------------|
| v0.1.0 | 6 (formatter) + 8 (cue4parse) + UAT = 14 | 2524 LOC Python |

### Top Lessons (Verified Across Milestones)

1. **Don't trust that UE Python API exposes everything** — Editor internals are not fully exported to Python
2. **CUE4Parse is the right abstraction** — avoids the need to re-implement FLinkerLoad from scratch
