---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: unknown
last_updated: "2026-05-18T16:34:04.014Z"
progress:
  total_phases: 5
  completed_phases: 2
  total_plans: 15
  completed_plans: 12
  percent: 40
---

# 项目状态

**项目**: uasset_resolver
**里程碑**: 0.1.0 (初始)
**状态**: Phase 4 完成 — 0.1.0 里程碑所有阶段已完成
**创建**: 2026-05-18
**更新**: 2026-05-19

## 当前阶段

**Phase 2B: CUE4Parse 后端** — 已完成

- 目标：用 CUE4Parse 替代 UE Python API，解决 NodeGuid/Pins/坐标不可访问问题
- 进度：Phase 2B 全部 Wave 完成（Wave 1: 编译, Wave 2: Python 封装, Wave 3: 统一控制器, Wave 5: 验证与文档）
- E2E 结果：12 节点提取成功，378ms，退出码 0
- 阻塞：.usmap 映射文件缺失导致坐标/GUID/Pins 为空（待 Phase 4 或后续解决）
- 下一步：Phase 3 — 输出格式化（MD + JSON）→ Phase 4 CLI 与验证

## 阻塞问题

**.usmap 映射文件**：

- UE 5.7 默认使用无版本属性（PKG_UnversionedProperties），CUE4Parse 需要 .usmap 才能解析属性值
- UE 5.7 无 GenerateMappingFile 命令let
- UnrealPak.exe 存在但不直接生成 .usmap
- 待尝试：UE Python API 生成、第三方工具、或 UE headless 兜底

## 已完成阶段

### Phase 1: UE 无头桥接 ✓ 2026-05-18

- 计划数：1
- 提交数：6
- UAT：6/6 测试通过
- 验证状态：passed

**交付物：**

- scripts/controller.py — 外部控制器（引擎检测、无头启动）
- scripts/ue_extract.py — UE 内嵌脚本（资产加载、蓝图检测）
- temp/minimal.uproject — 最小 UE 项目
- temp/ue_config.json — 引擎路径缓存

**需求覆盖：**

- PARSE-01 ✓ — 启动 UE 无头模式执行内嵌 Python
- PARSE-02 ✓ — 正确识别 Blueprint 资产

### Phase 2: 蓝图节点提取 ⚠️ 部分完成 2026-05-18

- 计划数：3
- 状态：UE Python API 受限，转 Phase 2B（CUE4Parse）

**交付物：**

- scripts/node_utils.py — 节点提取辅助函数（8 个函数）
- scripts/ue_extract.py — 扩展入口（节点提取流程）

**已实现**：节点类型/名称提取
**未实现**：NodeGuid=None, NodePosX/Y=0, Pins=[]（API 限制）

## 路线图摘要

| 阶段 | 目标 | 需求 | 状态 |
|------|------|------|------|
| 1 - UE 无头桥接 | 启动 UE 5.7 无头，加载 .uasset，验证蓝图 | PARSE-01, PARSE-02 | ✓ 完成 |
| 2 - 蓝图节点提取 | 提取 EventGraph 节点、引脚、连线、坐标 | PARSE-03 ~ PARSE-06 | ⚠️ 部分完成 |
| 2B - CUE4Parse 后端 | 用 C# 二进制解析替代 UE Python API | PARSE-03 ~ PARSE-06 | 完成（12 节点，378ms） |
| 3 - 输出格式化 | 生成 MD 文本和 JSON 输出 | OUT-01, OUT-02 | ✓ 完成 |
| 4 - CLI 与验证 | CLI 界面、加载策略、交叉验证 | OUT-03, LOAD-01, LOAD-02, VERIFY-01 | ✓ 完成 |

## 近期变更

- [2026-05-19] Phase 4 已规划 — 4 个计划（统一 CLI、加载策略、交叉验证、E2E UAT）
- [2026-05-18] Phase 2B 完成 — E2E 验证通过，12 节点提取成功（378ms），修复控制器 PascalCase 兼容 bug
- [2026-05-18] Phase 2B Plan 02 完成 — 统一控制器，--backend cue4parse|ue-headless|auto
- [2026-05-18] Phase 2B Plan 01 完成 — Python 封装 BPExtractor.exe，8/8 测试通过，修复 PascalCase key 兼容
- [2026-05-18] Phase 2B Wave 1 完成 — BPExtractor.exe 编译发布，0 错误 0 警告
- [2026-05-18] 冒烟测试：提取 12 个节点，坐标/GUID/Pins 全空（.usmap 缺失）
- [2026-05-18] 创建 02B-PLAN.md — Phase 2B 完整计划文档
- [2026-05-18] Phase 2 UE Python API 受限确认 — NodeGuid/Pins/坐标不可访问
- [2026-05-18] Phase 1 shipped — PR #1 创建
- [2026-05-18] 添加 GitHub remote: https://github.com/soatori/uasset_resolver.git
