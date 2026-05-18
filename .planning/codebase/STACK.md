---
title: "技术栈"
date: 2026-05-18
focus: tech
---

# 技术栈

## 语言与运行时

- **C++** — Unreal Engine 原生代码（UE 5.x，基于模板的角色类）
- **蓝图可视化脚本** — `.uasset` 二进制资产包含序列化的蓝图图

## 框架与引擎

- **Unreal Engine 5** — 游戏引擎和资产管线
  - `ACharacter` 基类 — pawn/角色框架
  - `USkeletalMeshComponent` — 第一人称手臂网格
  - `UCameraComponent` — 第一人称相机
  - 增强输入系统（`UInputAction`、`FInputActionValue`）

## 依赖

| 包 | 版本 | 用途 |
|----|------|------|
| `CoreMinimal.h` | UE 内置 | 核心类型和宏 |
| `GameFramework/Character.h` | UE 内置 | 角色基类 |
| `Logging/LogMacros.h` | UE 内置 | 日志工具 |

## 配置

- 仓库中无构建配置文件（`.Build.cs`、`.Target.cs` 缺失 — 可能属于更大的 UE 项目）
- `.gitignore` 排除 `temp/` 目录用于缓存/临时文件

## 关键观察

- `.uasset` 文件是**二进制序列化格式** — 不可直接阅读
- 蓝图节点序列化为 `Begin Object ... End Object` 块，包含引脚、坐标和函数引用
- 参考文档以中文编写（`UnrealEditor_uasset加载流程.md`、`蓝图节点文本参考.md`）
