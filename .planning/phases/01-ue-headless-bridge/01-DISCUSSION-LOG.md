# Phase 1: UE Headless Bridge - Discussion Log

**Date:** 2026-05-18
**Mode:** Default interactive

## Areas Discussed

### 1. Python 脚本传递方式
- **Options:** 外部 .py 文件 / 内联 -exec 命令 / 预装 UE Python 插件
- **Selected:** 外部 .py 文件（`-ExecutePythonScript=path`）
- **Reason:** 调试方便，脚本可迭代修改

### 2. UE 进程通信 & 输出采集
- **Options:** 写临时文件 / stdout 管道重定向 / 退出码 + stderr
- **Selected:** 写临时文件
- **Reason:** 简单可靠，不怕 stdout 截断

### 3. Blueprint 识别策略
- **Options:** 检查 UBlueprintGeneratedClass / 查找 EventGraph 成员 / 双重检查
- **Selected:** 检查 UBlueprintGeneratedClass
- **Note:** 需要保留架构可扩展性，未来支持其他资产类型

### 4. 错误处理 & 超时策略
- **Options:** 固定超时 + kill / 智能超时 + 重试 / 宽松超时（5 分钟）
- **Selected:** 固定超时（60-120s）+ kill
- **Note:** 后续搭建智能超时机制

### 5. 引擎安装路径检测（用户追加）
- **Options:** 用户指定 + 配置文件 / 自动扫描 / 混合模式
- **Selected:** 混合模式
- **Reason:** 覆盖大多数情况，自动失败后 fallback 到手动

## Deferred Ideas
- 智能超时 + 重试（Phase 4 CLI & Validation）
- 非 Blueprint 资产类型支持（v2 需求）

---

*Discussion completed: 2026-05-18*
