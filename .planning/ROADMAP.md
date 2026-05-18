# ROADMAP — uasset_resolver

> Unreal Engine `.uasset` 蓝图解析工具 — 一条命令，结构化输出，无需编辑器。

**Core Value:** 一条命令读取 .uasset 文件，输出蓝图节点的结构化表示（文本+JSON），无需打开 UE 编辑器。

## Milestones

- ✅ **v0.1.0 初始版本** — 基础架构 + CUE4Parse 集成 (shipped 2026-05-19)

---

<details>
<summary>✅ v0.1.0 初始版本 — 已发货 2026-05-19</summary>

### Phases

- [x] **Phase 1: UE 无头桥接** — 启动 UE 5.7 无头模式，加载 .uasset 文件，验证蓝图识别 ✓ 2026-05-18
- [x] **Phase 2: 蓝图节点提取** — 提取 EventGraph 节点、引脚、连线和画布坐标 ⚠️ UE Python API 受限，转 Phase 2B ✓ 2026-05-18
- [x] **Phase 2B: CUE4Parse 后端** — 用 CUE4Parse 替代 UE Python API，解决 NodeGuid/Pins/坐标不可访问问题 ✓ 2026-05-18
- [x] **Phase 3: 输出格式化** — 生成类 UE 编辑器风格的 MD 文本和结构化 JSON ✓ 2026-05-19
- [x] **Phase 4: CLI 与验证** — 命令行界面、加载策略回退、交叉验证 ✓ 2026-05-19

### 进度

| Phase | 计划完成 | 状态 | 已完成 |
|-------|----------|------|--------|
| 1. UE 无头桥接 | 1/1 | Complete | 2026-05-18 |
| 2. 蓝图节点提取 | 3/3 | Complete (shifted to 2B) | 2026-05-18 |
| 2B. CUE4Parse 后端 | 3/3 | Complete | 2026-05-18 |
| 3. 输出格式化 | 1/1 | Complete | 2026-05-19 |
| 4. CLI 与验证 | 4/4 | Complete | 2026-05-19 |

### 需求覆盖率

| 需求 | Phase | 状态 | 备注 |
|------|-------|------|------|
| PARSE-01 | Phase 1 | Complete | 2026-05-18 |
| PARSE-02 | Phase 1 | Complete | 2026-05-18 |
| PARSE-03 | Phase 2/2B | Complete | 节点类型/名称提取成功（CUE4Parse 12 节点），378ms |
| PARSE-04 | Phase 2/2B | Partial | EdGraphPin 不暴露到 Python；CUE4Parse 需 .usmap |
| PARSE-05 | Phase 2/2B | Partial | LinkedTo 不可访问（依赖 PARSE-04）|
| PARSE-06 | Phase 2/2B | Partial | NodePosX/Y 未暴露；CUE4Parse 需 .usmap |
| OUT-01 | Phase 3 | Complete | 2026-05-19 — MD 输出匹配 UE 编辑器格式 |
| OUT-02 | Phase 3 | Complete | 2026-05-19 — JSON snake_case，nodes/pins/connections 三级嵌套 |
| OUT-03 | Phase 4 | Complete | 2026-05-19 — --format json/md 选择输出 |
| LOAD-01 | Phase 4 | Complete | 2026-05-19 — CUE4Parse 直接读取任意路径 .uasset |
| LOAD-02 | Phase 4 | Complete | 2026-05-19 — --content-dir 参数 + 结构化回退提示 |
| VERIFY-01 | Phase 4 | Complete | 2026-05-19 --verify 参数，4 维度验证通过 |

**Mapped: 12/12** | **Complete: 8/12** | **Partial: 4/12** (PARSE-03~06 .usmap 阻塞坐标/Pins)

</details>

---

## Next Milestone

下一里程碑将聚焦解决 **.usmap 映射文件**问题，目标是完整提取坐标/GUID/Pins/连线信息。

## Progress

See [milestones/v0.1.0-ROADMAP.md](milestones/v0.1.0-ROADMAP.md) for full archived details.
