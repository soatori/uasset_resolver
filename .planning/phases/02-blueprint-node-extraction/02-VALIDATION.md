# Phase 2: 蓝图节点提取 — 验证结果

**Phase:** 02-蓝图节点提取
**Created:** 2026-05-18
**Updated:** 2026-05-18 (Wave 3 验证完成)

## Wave 3 验证结果

**执行时间:** 2026-05-18
**状态:** ⚠️ 部分通过 — 发现 UE 5.7 Python API 限制

### 验证通过项

| Req ID | 验证内容 | 结果 | 备注 |
|--------|----------|------|------|
| PARSE-03 | 提取节点列表（类型、名称） | ✅ PASS | 使用 ObjectIterator 遍历，成功提取 9 个节点 |

**提取结果示例:**
```json
{
  "nodes": [
    {"node_class": "EdGraphNode_Comment", "node_name": "EdGraphNode_Comment_0"},
    {"node_class": "K2Node_CallFunction", "node_name": "K2Node_CallFunction_10"},
    {"node_class": "K2Node_Event", "node_name": "K2Node_Event_12"}
  ],
  "extracted_node_count": 9
}
```

### 验证失败项（API 限制）

| Req ID | 验证内容 | 结果 | 原因 |
|--------|----------|------|------|
| PARSE-03 | 提取节点坐标（NodePosX/Y） | ❌ FAIL | API 未暴露（无 BlueprintVisible 标记） |
| PARSE-03 | 提取节点 GUID（NodeGuid） | ❌ FAIL | API 未暴露（无 BlueprintVisible 标记） |
| PARSE-04 | 提取引脚定义（PinId、PinName、PinType） | ❌ FAIL | EdGraphPin 不是 UObject，完全不暴露 |
| PARSE-05 | 提取连线关系（LinkedTo） | ❌ FAIL | EdGraphPin 不暴露 → LinkedTo 不可访问 |
| PARSE-06 | 提取画布坐标（NodePosX/NodePosY） | ❌ FAIL | API 未暴露 |

### 根本原因

**源码验证（UE 5.7）:**
- PyGenUtil.cpp 第 1608-1612 行：`IsScriptExposedProperty()` 要求 `CPF_BlueprintVisible` 标记
- EdGraphNode.h：NodePosX/NodePosY/NodeGuid 有 `UPROPERTY()` 但无 BlueprintVisible
- EdGraphPin.h 第 293 行：EdGraphPin 不是 UObject（无 UCLASS 标记）

**详见:** `02-API-LIMITATIONS-RESEARCH.md`

---

## Test Framework

| Property | Value |
|----------|-------|
| Framework | UE 内嵌 Python (无外部测试框架) |
| Config file | 无 — 使用 ue_extract.py 内嵌验证 |
| Quick run command | 无独立测试 — 验证通过结果文件检查 |
| Full suite command | 运行 ue_extract.py + 手动对比 蓝图节点文本参考.md |

## Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | Status |
|--------|----------|-----------|-------------------|--------|
| PARSE-03 | 提取节点列表 | Smoke | 检查 result.json["nodes"] 非空 | Wave 0 |
| PARSE-04 | 提取引脚定义 | Smoke | 检查每个 node["pins"] 非空 | Wave 0 |
| PARSE-05 | 提取连线关系 | Smoke | 检查 pin["linked_to"] 结构正确 | Wave 0 |
| PARSE-06 | 提取画布坐标 | Smoke | 检查 node["node_pos_x/y"] 数值 | Wave 0 |

## Sampling Rate

- **Per task commit:** 运行 ue_extract.py，检查输出 JSON 结构
- **Per wave merge:** 对比输出节点数量与 Phase 1 检测的 node_count
- **Phase gate:** 输出 JSON 与 蓝图节点文本参考.md 关键字段匹配验证

## Wave 0 Gaps

- [x] `scripts/node_utils.py` — 节点/引脚提取辅助函数 ✓ Wave 1 完成
- [x] `scripts/ue_extract.py` 扩展 — 添加节点提取逻辑 ✓ Wave 2 完成
- [x] 验证逻辑 — 输出与参考文本对比脚本 ✓ Wave 3 完成（发现 API 限制）

## 后续研究待办

- [x] 研究编辑器复制蓝图文本功能（`FEdGraphUtilities::ExportNodesToText`） ✓ 2026-05-18 — 需 C++ 插件包装，用户不倾向
- [x] 评估 C++ 插件扩展 Python API 的可行性 ✓ 2026-05-18 — 用户明确不希望在引擎中添加插件
- [x] 测试 CUE4Parse-Python 离线解析方案 ✓ 2026-05-18 — 已编译验证（.NET 8.0），支持 UE 5.7/5.8
- [x] 分析 uasset_read 项目 ✓ 2026-05-18 — 复杂度过高，可借鉴模块设计
- [x] 虚幻盒子 (ue5box.com) 分析 ✓ 2026-05-18 — 商业产品，具体实现未公开
- [x] C++ 独立工具可行性 ✓ 2026-05-18 — UnrealEd 构建守卫阻止，不可行
- [x] UE 5.7/5.8 版本兼容性验证 ✓ 2026-05-18 — CUE4Parse 完整支持
- [x] UnrealBridge Skill 分析 ✓ 2026-05-18 — 编辑器内自动化工具，互补但非替代

## 推荐方案

**混合方案：现有 Python API + CUE4Parse CLI**

```
Phase 2 Wave 4 计划：
1. 节点类型/名称 ✅ (ObjectIterator - 已完成)
2. 坐标/引脚/连线 → CUE4Parse CLI 补全 (2-4 天)
3. Python subprocess 管道集成
```

详见：`02-ALTERNATIVE-PATHWAYS-RESEARCH.md` 方向 9-15

---

**Source:** 从 RESEARCH.md Validation Architecture 部分提取 + Wave 3 实际验证结果