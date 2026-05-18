# Milestones — uasset_resolver

项目里程碑索引。每个里程碑完整归档保存在 `milestones/` 目录。

| Version | Name | Date | Phases | Plans | Status | Archive |
|---------|------|------|--------|-------|--------|--------|
| v0.1.0 | Initial Blueprint Parser | 2026-05-19 | 5 | 12 | ✅ Shipped | [v0.1.0-ROADMAP.md](milestones/v0.1.0-ROADMAP.md) |

## v0.1.0 Initial Blueprint Parser

**Summary:**
- 搭建基础架构，验证 CUE4Parse 路径可行
- 实现双格式输出（MD + JSON）
- 统一 CLI 界面，支持交叉验证
- 提取速度：~400ms 对比 UE 无头 >60s（150x 提升）

**Known gaps:** 4 个需求部分完成（坐标/GUID/Pins），都因 .usmap 映射文件缺失阻塞。计划下一里程碑解决。

**Audit:** [0.1.0-MILESTONE-AUDIT.md](milestones/0.1.0-MILESTONE-AUDIT.md)
