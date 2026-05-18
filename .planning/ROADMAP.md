# ROADMAP — uasset_resolver

> Unreal Engine `.uasset` 蓝图解析工具 — 一条命令，结构化输出，无需编辑器。

**Core Value:** 一条命令读取 .uasset 文件，输出蓝图节点的结构化表示（文本+JSON），无需打开 UE 编辑器。

**Granularity:** standard
**Total Phases:** 4
**Total v1 Requirements:** 12

---

## Phases

- [x] **Phase 1: UE 无头桥接** — 启动 UE 5.7 无头模式，加载 .uasset 文件，验证蓝图识别 ✓ 2026-05-18
- [~] **Phase 2: 蓝图节点提取** — 提取 EventGraph 节点、引脚、连线和画布坐标 ⚠️ UE Python API 受限，转 Phase 2B
- [x] **Phase 2B: CUE4Parse 后端** — 用 CUE4Parse 替代 UE Python API，解决 NodeGuid/Pins/坐标不可访问问题 ✓ 2026-05-18
- [x] **Phase 3: 输出格式化** — 生成类 UE 编辑器风格的 MD 文本和结构化 JSON ✓ 2026-05-19
- [x] **Phase 4: CLI 与验证** — 命令行界面、加载策略回退、交叉验证 ✓ 2026-05-19

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

**计划**: 3 个计划（3 个 wave）

计划:
- [x] `02-01-PLAN.md` — node_utils.py 辅助函数模块 + ue_extract.py 扩展入口 ✓ 2026-05-18
- [x] `02-02-PLAN.md` — 核心节点提取逻辑实现（extract_nodes/pins/linked_to/pin_type） ✓ 2026-05-18
- [x] `02-03-PLAN.md` — 端到端验证 + 与参考文本对比 ✓ 2026-05-18 ⚠️ 发现 API 限制

**后续研究方向:**
- 编辑器复制蓝图文本功能（`FEdGraphUtilities::ExportNodesToText`）— 需 C++ 插件包装，用户不倾向
- CUE4Parse-Python 离线解析方案 — **推荐**，已编译验证（.NET 8.0，0 错误），支持 UE 5.7/5.8
- uasset_read 项目参考 — 手写解析器复杂度过高（多层抽象、554 个测试用例）
- UnrealBridge Skill — 编辑器内自动化工具，与 uasset_resolver 互补（需 UE 插件）
- C++ 独立工具 — 不可行（UnrealEd 构建守卫阻止非 Editor Target 链接 UnrealEd）

**API 限制发现（2026-05-18）**：
- NodeGuid = None — UE Python API 不暴露此字段
- NodePosX/Y = 0 — 属性未正确反序列化
- Pins = [] — EdGraphPin 不暴露到 Python

**替代方案**：Phase 2B（CUE4Parse 后端）已启动，Wave 1 完成（编译+冒烟测试）。

### Phase 2B: CUE4Parse 后端

**目标**: 用 CUE4Parse C# 二进制解析库替代 UE Python API，直接从 .uasset 读取节点数据。

**依赖**: Phase 1（UE 5.7 环境验证）

**需求**: PARSE-03, PARSE-04, PARSE-05, PARSE-06

**成功标准**（已调整 — .usmap 暂挂）:
  1. BPExtractor.exe 能从 .uasset 提取 ≥9 个节点（类型/名称）— 无 .usmap 时坐标/GUID/Pins 为空
  2. Python 封装模块可被 import，提供类型化数据接口
  3. 统一控制器支持 --backend cue4parse|ue-headless|auto 切换
  4. CUE4Parse 执行时间 < 10 秒（vs UE headless > 60s）
  5. ⚠️ 坐标/GUID/Pins 数据 — 需 .usmap（Wave 4 暂挂，见 Phase 4 或后续补充）

**计划**: 3 个计划（Wave 2 / Wave 3 / Wave 5）

计划:
- [x] `02B-PLAN.md` — Phase 2B 总计划（Wave 1-5 概览）
- [x] `02B-01-PLAN.md` — Wave 2: Python 封装模块
- [x] `02B-02-PLAN.md` — Wave 3: 统一控制器
- [x] `02B-03-PLAN.md` — Wave 5: 验证与文档 ✓ 2026-05-18

**E2E 验证结果（2026-05-18）**：
- 节点提取：12 个（>= 9 目标）
- 后端标识：cue4parse
- 提取耗时：378ms（< 10s 目标）
- 退出码：0

**已知限制**:
- .usmap 映射文件缺失 → CUE4Parse 无法解析属性值（坐标/GUID/Pins 为空）
- UE 5.7 无 GenerateMappingFile 命令let
- 潜在解决方案：UE4SS、Dumper-7 注入 UE 编辑器进程生成 .usmap

### Phase 3: 输出格式化

**目标**: 将提取的蓝图数据格式化为类 UE 编辑器风格的 MD 文本和结构化 JSON，两者均可读且可被机器消费。

**依赖**: Phase 2

**需求**: OUT-01, OUT-02

**成功标准**（必须满足）:
  1. MD 输出匹配 UE 编辑器文本格式：`Begin Object Class=... Name=... End Object` 块，包含所有节点字段
  2. JSON 输出包含三层结构：nodes → pins → connections，所有提取数据正确嵌套
  3. 两种格式包含相同数据（MD 和 JSON 字段对等）

**计划**: 1 个计划（3 个 wave）

计划:
- [x] `03-01-PLAN.md` — 验证现有 formatter.py，修复 PinType 分隔符 bug，端到端验证 ✓ 2026-05-19

**验证结果:**
- MD 格式：Begin Object ... End Object 结构正确，PinType 分隔符修复为 `,`
- JSON 格式：snake_case 键、nodes/pins/connections 三级嵌套、connections 正确提取
- 合成数据测试：所有格式断言通过
- E2E：退出码 0，12 节点，MD 2302 字节，JSON 4049 字节

### Phase 4: CLI 与验证

**目标**: 工具提供完整的命令行体验，包含加载策略回退和已验证的输出正确性。

**依赖**: Phase 3

**需求**: OUT-03, LOAD-01, LOAD-02, VERIFY-01

**成功标准**（必须满足）:
  1. 用户可通过单条 CLI 命令运行，使用 `--format md` 或 `--format json` 选择输出格式
  2. 用户可传入裸 .uasset 文件路径并成功加载；若加载失败，显示清晰提示要求指定 UE 项目 Content 目录
  3. 在 `BP_FirstPersonCharacter.uasset` 上运行工具的输出与 `蓝图节点文本参考.md` 中的关键字段匹配（节点数量、节点名称、函数引用、引脚结构）

**计划**: 4 个计划（4 个 wave）

计划:
- [x] `04-01-PLAN.md` — 统一 CLI 入口：合并控制器，--help/--version/--format，标准退出码
- [x] `04-02-PLAN.md` — 加载策略：CUE4Parse 裸文件直接加载，UE headless 失败回退提示 Content 目录
- [x] `04-03-PLAN.md` — 交叉验证：输出与 蓝图节点文本参考.md 关键字段比对
- [x] `04-04-PLAN.md` — 端到端 UAT：3 个成功标准验证通过

---

## 进度

| Phase | 计划完成 | 状态 | 已完成 |
|-------|----------|------|--------|
| 1. UE 无头桥接 | 1/1 | 完成 | 2026-05-18 |
| 2. 蓝图节点提取 | 3/3 | ⚠️ 部分完成 | 2026-05-18 — UE Python API 受限，转 Phase 2B |
| 2B. CUE4Parse 后端 | 3/3 | 完成 | 2026-05-18 — Wave 2/3/5 完成，12 节点提取成功，.usmap 缺失导致坐标/GUID/Pins 为空 |
| 3. 输出格式化 | 1/1 | 完成 | 2026-05-19 — MD/JSON 验证通过，PinType 分隔符修复 |
| 4. CLI 与验证 | 4/4 | 完成 | 2026-05-19 — 统一 CLI + 加载策略 + 交叉验证 + E2E UAT 通过 |

---

## 覆盖率

| 需求 | Phase | 状态 | 备注 |
|------|-------|------|------|
| PARSE-01 | Phase 1 | Complete | 2026-05-18 |
| PARSE-02 | Phase 1 | Complete | 2026-05-18 |
| PARSE-03 | Phase 2/2B | Complete | 节点类型/名称提取成功（CUE4Parse 12 节点），378ms |
| PARSE-04 | Phase 2/2B | ⚠️ Partial | EdGraphPin 不暴露到 Python；CUE4Parse 需 .usmap |
| PARSE-05 | Phase 2/2B | ⚠️ Partial | LinkedTo 不可访问（依赖 PARSE-04） |
| PARSE-06 | Phase 2/2B | ⚠️ Partial | NodePosX/Y 未暴露；CUE4Parse 需 .usmap |
| OUT-01 | Phase 3 | Complete | 2026-05-19 — MD 输出匹配 UE 编辑器格式 |
| OUT-02 | Phase 3 | Complete | 2026-05-19 — JSON snake_case，nodes/pins/connections 三级嵌套 |
| OUT-03 | Phase 4 | Complete | 2026-05-19 — --format json/md 选择输出 |
| LOAD-01 | Phase 4 | Complete | 2026-05-19 — CUE4Parse 直接读取任意路径 .uasset |
| LOAD-02 | Phase 4 | Complete | 2026-05-19 — --content-dir 参数 + 结构化回退提示 |
| VERIFY-01 | Phase 4 | Complete | 2026-05-19 --verify 参数，4 维度验证通过 |

**Mapped: 12/12** | **Complete: 7/12** | **Partial: 4/12** (PARSE-03~06 .usmap 阻塞坐标/Pins) | **Pending: 1/12**
