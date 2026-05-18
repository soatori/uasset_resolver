# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作时提供指导。

## 语言

请使用中文回复以及编写文档

## 项目概述

Unreal Engine .uasset 文件解析 tool — 让 AI 代理在不依赖 UE 编辑器的情况下读取蓝图内容。参考 UE 编辑器源码制作的小工具。

目标是从二进制 `.uasset` 文件中反序列化出蓝图事件图（EventGraph）的节点结构，包括节点类型、函数引用、引脚定义和连线关系。先研究源码输出索引文档，再编写计划执行

## 文件组织

```
'E:\Develop\lib\UnrealEngine/'  # UE 编辑器源码（参考用，非本项目构建）
'D:\Program Files\Epic Games\Engine\UE_5.7' #本地引擎编辑器安装路径
'BP_FirstPersonCharacter.uasset' # 真实测试文件（56KB）
'测试对照C++类'                 # 测试文件对应的 C++ 类参考
'UnrealEditor_uasset加载流程.md' # UE 加载管线文档
'蓝图节点文本参考.md'            # 蓝图节点文本序列化格式参考
```

> 所有缓存、临时性生成文件统一放在 `temp/` 目录，已在 `.gitignore` 中排除。

## 技术参考

### UE .uasset 加载管线

核心路径：`LoadPackage() → FLinkerLoad → ProcessPackageSummary → 导入表/导出表 → 对象序列化 → PostLoad()`

关键类：
- `FLinkerLoad` — 从磁盘反序列化 .uasset 包文件的核心机制
- `UPackage` — 资产容器，对应一个 .uasset 文件
- `UBlueprintGeneratedClass` — 蓝图加载后生成的 UClass

详细流程请参考 `UnrealEditor_uasset加载流程.md`。

### 蓝图节点文本格式

反序列化后的节点以 `Begin Object ... End Object` 块表示，标准字段包括：
- Class / Name / ExportPath
- FunctionReference（函数节点）
- NodePosX / NodePosY（画布坐标）
- NodeGuid（唯一标识符）
- CustomProperties Pin（引脚定义：PinId/PinName/PinType/LinkedTo/Direction）

完整示例请参考 `蓝图节点文本参考.md`。

### UE 源码参考位置

UE 编辑器源码位于 `E:\Develop\lib\UnrealEngine/`，重点目录：
- `Engine/Source/Runtime/CoreUObject/Private/UObject/LinkerLoad.cpp` — FLinkerLoad 核心实现（274KB）
- `Engine/Source/Developer/AssetTools/` — 资产操作中枢
- `Engine/Source/Editor/UnrealEd/Classes/Factories/` — 工厂系统

## gsd-sdk 使用

仅支持 3 个命令：`run "<prompt>"` / `auto` / `init [input]`

**不支持** `query`、`list`、`get` 等子命令（会报错）。查 phase 信息请直接读 `.planning/` 文件或用 GSD slash commands。

## 上下文与效率

- 上下文 >70% 时执行 `compact`
- 独立任务优先并行 subagent，主线程只看结构化摘要
- **GSD：** wave 或 PLAN 之间互补不干扰时均可并行执行
- 有依赖或共享状态的任务不可并行；写冲突风险可通过 git 分支管理规避
