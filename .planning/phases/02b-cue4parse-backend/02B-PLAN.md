# PLAN: Phase 2B — CUE4Parse Backend

> 用 CUE4Parse 替代 UE Python API 作为主要 .uasset 解析后端，解决 NodeGuid/Pins/坐标不可访问的 API 限制。

## Context

Phase 2 通过 UE Python API 发现：NodeGuid=None, NodePosX/Y=0, Pins=[]。CUE4Parse 是 C# 二进制解析库，直接从 .uasset 读取，不需要 UE 编辑器。

**目标**：构建 AI 可用的 skill — 输入 .uasset 路径，输出结构化 JSON。

**关键约束**：.usmap 映射文件暂时跳过（Wave 4  deferred）。BPExtractor 在无 .usmap 时，UE5 PKG_UnversionedProperties 资产属性值将为空。Plan 接受这一限制，先完成封装和集成层。

## 已完成

### Wave 1: 克隆、编译、发布 ✅

| 任务 | 状态 | 备注 |
|------|------|------|
| 克隆 CUE4Parse | ✅ | `E:\Develop\CUE4Parse\` — git clone --recursive |
| 创建 BPExtractor 项目 | ✅ | 4 个 C# 文件 |
| 编译 | ✅ | 0 错误 0 警告, .NET 8.0 |
| 发布 | ✅ | `engines/bp_extractor/BPExtractor.exe` + 依赖 DLLs |
| 冒烟测试 | ✅ | 提取 12 个节点（类型/名称），坐标/GUID/Pins 全空 — .usmap 缺失 |

## 待完成任务

### Wave 2: Python 封装模块

**目标**：创建 `scripts/cue4parse_extractor.py` 封装 BPExtractor.exe

1. **创建 `scripts/cue4parse_extractor.py`**
   - Dataclasses：`Pin`、`BlueprintNode`、`BlueprintGraph`
   - `BPExtractorError` 异常
   - `BPExtractor` 类：
     - `__init__(exe_path=None, ue_version="UE5_7", usmap_path=None, timeout=30)`
     - 自动发现 `engines/bp_extractor/BPExtractor.exe`
     - `extract(path) -> BlueprintGraph` — 返回类型化对象
     - `extract_to_dict(path) -> dict` — 返回原始 JSON
   - subprocess 调用 BPExtractor.exe，解析 JSON 输出
   - 错误处理：exe 不存在、非零退出码、JSON 解析失败、超时

2. **创建 `scripts/test_cue4parse_extractor.py`**
   - 测试 extract_to_dict 对 BP_FirstPersonCharacter.uasset
   - 验证 ≥5 节点（.usmap 缺失下坐标/GUID/Pins 可能为空 — 这是已知限制）
   - 测试不存在文件的错误处理
   - 测试 subprocess 非零退出码

### Wave 3: 统一控制器

1. **创建 `scripts/cue4parse_controller.py`**
   - 支持 `--backend cue4parse | ue-headless | auto`
   - `auto` 模式：优先 CUE4Parse，找不到 exe 则回退 UE headless
   - 输出标准化 JSON（含 backend 字段）
   - 接受 `--uasset`、`--output`、`--usmap`、`--timeout` 参数

2. **更新 `scripts/controller.py`**
   - 添加 `--backend` 参数
   - `--backend cue4parse` 时委托给 cue4parse_controller
   - 保持现有 ue-headless 流程不变

### Wave 4: .usmap 风险应对 ⏸️ SKIPPED

**状态**：用户决定暂时不解决 .usmap 问题。

**已知**：
- CUE4Parse 在 UE5 PKG_UnversionedProperties 资产下需要 .usmap 才能解析属性值
- 无 .usmap 时，NodeGuid/Pins/坐标等属性将为空/默认值
- 潜在解决方案：UE4SS、Dumper-7、手动映射

**影响**：在 .usmap 缺失状态下，PARSE-04/05/06 需求只能部分满足（节点类型/名称可提取，但坐标/GUID/引脚为空）。

### Wave 5: 验证与文档

1. 端到端测试：`python scripts/cue4parse_controller.py --uasset BP_FirstPersonCharacter.uasset --backend cue4parse`
2. 验证 JSON 输出包含 ≥9 节点（已知限制：坐标/GUID/Pins 为空）
3. 执行时间测量（预期 < 10 秒 vs UE headless > 60s）
4. 更新 ROADMAP.md Phase 2B 状态
5. 更新 .gitignore（确保 engines/bp_extractor/ 被排除或确认已在）
6. 在 PLAN.md 中标注已知限制

## 依赖关系

```
Wave 1 ✅
  |
Wave 2 (Python 封装) ← 独立，可立即开始
  |
Wave 3 (控制器) ← 依赖 Wave 2
  |
Wave 4 (.usmap) ⏸️ SKIPPED — 不阻塞 Wave 2-3
  |
Wave 5 (验证) ← 依赖 Wave 3，接受 .usmap 缺失限制
```

## 成功标准（调整后）

1. BPExtractor.exe 能从 .uasset 提取 ≥9 个节点（类型/名称）✅ 已验证
2. Python 封装正确调用 BPExtractor.exe，返回结构化数据 ✅ Wave 2
3. 统一控制器支持 --backend 切换 ✅ Wave 3
4. 执行时间 < 10 秒 ✅ Wave 5 验证
5. ⚠️ 坐标/GUID/Pins 数据 — 需 .usmap（Wave 4 暂挂，已知限制）

## 文件清单

### 已存在
| 文件 | 状态 |
|------|------|
| `engines/bp_extractor/BPExtractor.exe` + DLLs | ✅ 已编译发布 |
| `E:\Develop\CUE4Parse\BPExtractor\*.cs` | ✅ 源代码 |
| `scripts/controller.py` | ✅ 现有（需更新） |
| `scripts/ue_extract.py` | ✅ 现有 |
| `scripts/node_utils.py` | ✅ 现有 |

### 待创建
| 文件 | Wave |
|------|------|
| `scripts/cue4parse_extractor.py` | Wave 2 |
| `scripts/test_cue4parse_extractor.py` | Wave 2 |
| `scripts/cue4parse_controller.py` | Wave 3 |

### 待修改
| 文件 | Wave | 变更 |
|------|------|------|
| `scripts/controller.py` | Wave 3 | 加 `--backend` 参数 |
| `.planning/ROADMAP.md` | Wave 5 | Phase 2B 状态更新 |
