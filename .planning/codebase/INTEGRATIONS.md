---
title: "集成"
date: 2026-05-18
focus: tech
---

# 集成

## 外部 API

无。这是一个本地资产解析工具，不是网络应用。

## 数据库

无。

## 认证提供者

无。

## 引擎集成

- **Unreal Engine 资产管线** — 工具对接 UE 的 `.uasset` 二进制格式
  - `FLinkerLoad` — UE 内部加载器，用于加载 .uasset 包
  - `UPackage` — 资产容器，对应一个 .uasset 文件
  - `UBlueprintGeneratedClass` — 从蓝图资产生成的 UClass

## 文件 I/O

- 从磁盘读取 `.uasset` 二进制文件
- 测试文件：`BP_FirstPersonCharacter.uasset`（56KB）
