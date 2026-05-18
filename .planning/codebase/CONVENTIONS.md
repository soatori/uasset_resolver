---
title: "约定"
date: 2026-05-18
focus: quality
---

# 约定

## 语言

- **文档**: 中文（CLAUDE.md 中指定）
- **代码**: 英文（标准 UE C++ 约定）

## C++ 约定（来自参考类）

- **UE 命名**: `A` 前缀用于 Actor 类，`U` 前缀用于 UObject 类，`F` 前缀用于结构体
- **UPROPERTY 宏**: `VisibleAnywhere`、`BlueprintReadOnly`、`EditAnywhere`，带 category 元数据
- **UFUNCTION 宏**: `BlueprintCallable`，带 category
- **头文件保护**: `#pragma once`
- **Include 顺序**: `CoreMinimal.h` → 框架头 → 生成的头文件

## 蓝图约定（来自参考文档）

- **节点格式**: `Begin Object ... End Object` 块
- **字段**: Class、Name、ExportPath、FunctionReference、NodeGuid
- **引脚**: `CustomProperties Pin`，包含 PinId/PinName/PinType/LinkedTo/Direction
- **坐标**: NodePosX/NodePosY 用于画布位置

## 文件组织

- 参考文档使用中文文件名
- 测试资产使用 `BP_` 前缀
- `temp/` 目录用于缓存和临时文件（gitignore）

## Git

- 新初始化的仓库
- 尚无提交历史
