# ROADMAP — uasset_resolver

> Unreal Engine `.uasset` 蓝图解析工具 — 一条命令，结构化输出，无需编辑器。

**Core Value:** 一条命令读取 .uasset 文件，输出蓝图节点的结构化表示（文本+JSON），无需打开 UE 编辑器。

**Granularity:** standard
**Total Phases:** 4
**Total v1 Requirements:** 12

---

## Phases

- [x] **Phase 1: UE 无头桥接** — 启动 UE 5.7 无头模式，加载 .uasset 文件，验证蓝图识别 ✓ 2026-05-18
- [ ] **Phase 2: 蓝图节点提取** — 提取 EventGraph 节点、引脚、连线和画布坐标
- [ ] **Phase 3: 输出格式化** — 生成类 UE 编辑器风格的 MD 文本和结构化 JSON
- [ ] **Phase 4: CLI 与验证** — 命令行界面、加载策略回退、交叉验证

---

## Phase Details

### Phase 1: UE 无头桥接

**目标**: Python 工具能启动 UE 5.7 无头模式，加载 .uasset 文件，并确认其是否为蓝图资产。

**依赖**: 无（首个 Phase）

**需求**: PARSE-01, PARSE-02

**成功标准**（必须满足）:
  1. 运行 Python 工具以 `-unattended -NullRHI` 参数启动 UE 5.7 并执行内嵌 Python 脚本
  2. 给定有效的 .uasset 路径，工具加载资产并正确报告是否为蓝图
  3. UE 进程在脚本执行后干净退出（无残留编辑器窗口）

**计划**: 1 个计划（4 个任务，3 个 wave）

计划:
- [ ] `01-01-PLAN.md` — 项目脚手架、UE 内嵌脚本、外部控制器、端到端冒烟测试

### Phase 2: 蓝图节点提取

**目标**: 从已加载的蓝图资产中提取完整的 EventGraph 结构，包括节点、引脚、连线和画布坐标。

**依赖**: Phase 1

**需求**: PARSE-03, PARSE-04, PARSE-05, PARSE-06

**成功标准**（必须满足）:
  1. 输出包含所有 EventGraph 节点及其类型、名称和函数引用（函数节点）
  2. 每个节点包含完整的引脚定义：PinId、PinName、PinType、Direction 和 LinkedTo 引用
  3. 捕获所有节点间连线，包括执行流（exec 引脚）和数据连接
  4. 每个节点记录画布坐标（NodePosX、NodePosY）

**计划**: 待定

### Phase 3: 输出格式化

**目标**: 将提取的蓝图数据格式化为类 UE 编辑器风格的 MD 文本和结构化 JSON，两者均可读且可被机器消费。

**依赖**: Phase 2

**需求**: OUT-01, OUT-02

**成功标准**（必须满足）:
  1. MD 输出匹配 UE 编辑器文本格式：`Begin Object Class=... Name=... End Object` 块，包含所有节点字段
  2. JSON 输出包含三层结构：nodes → pins → connections，所有提取数据正确嵌套
  3. 两种格式包含相同数据（MD 和 JSON 字段对等）

**计划**: 待定
**UI 提示**: 是

### Phase 4: CLI 与验证

**目标**: 工具提供完整的命令行体验，包含加载策略回退和已验证的输出正确性。

**依赖**: Phase 3

**需求**: OUT-03, LOAD-01, LOAD-02, VERIFY-01

**成功标准**（必须满足）:
  1. 用户可通过单条 CLI 命令运行，使用 `--format md` 或 `--format json` 选择输出格式
  2. 用户可传入裸 .uasset 文件路径并成功加载；若加载失败，显示清晰提示要求指定 UE 项目 Content 目录
  3. 在 `BP_FirstPersonCharacter.uasset` 上运行工具的输出与 `蓝图节点文本参考.md` 中的关键字段匹配（节点数量、节点名称、函数引用、引脚结构）

**计划**: 待定

---

## 进度

| Phase | 计划完成 | 状态 | 已完成 |
|-------|----------|------|--------|
| 1. UE 无头桥接 | 1/1 | 完成 | 2026-05-18 |
| 2. 蓝图节点提取 | 0/0 | 未开始 | - |
| 3. 输出格式化 | 0/0 | 未开始 | - |
| 4. CLI 与验证 | 0/0 | 未开始 | - |

---

## 覆盖率

| 需求 | Phase | 状态 |
|------|-------|------|
| PARSE-01 | Phase 1 | Complete | 2026-05-18 |
| PARSE-02 | Phase 1 | Complete | 2026-05-18 |
| PARSE-03 | Phase 2 | Pending |
| PARSE-04 | Phase 2 | Pending |
| PARSE-05 | Phase 2 | Pending |
| PARSE-06 | Phase 2 | Pending |
| OUT-01 | Phase 3 | Pending |
| OUT-02 | Phase 3 | Pending |
| OUT-03 | Phase 4 | Pending |
| LOAD-01 | Phase 4 | Pending |
| LOAD-02 | Phase 4 | Pending |
| VERIFY-01 | Phase 4 | Pending |

**Mapped: 12/12**
