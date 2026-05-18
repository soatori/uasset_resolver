---
title: "项目结构"
date: 2026-05-18
focus: arch
---

# 结构

## 目录布局

```
E:/Develop/uasset_resolver/
├── .git/                          # Git 仓库（新初始化）
├── .planning/                     # GSD 规划文档
│   └── codebase/                  # 代码库映射（本目录）
├── BP_FirstPersonCharacter.uasset # 测试资产（56KB）
├── CLAUDE.md                      # 项目说明
├── UnrealEditor_uasset加载流程.md   # UE 加载管线文档
├── 蓝图节点文本参考.md              # 蓝图节点文本格式参考
├── 测试对照C++类/                  # 参考 C++ 类
│   ├── BP_FirstPersonCharacter.uasset  # 重复的测试资产
│   ├── FirstPersonCCharacter.cpp     # C++ 实现
│   └── FirstPersonCCharacter.h       # C++ 头文件
└── temp/                          # 缓存/临时目录（gitignore）
```

## 关键路径

| 路径 | 用途 |
|------|------|
| `BP_FirstPersonCharacter.uasset` | 解析器开发的主要测试文件 |
| `测试对照C++类/` | C++ 参考实现，展示蓝图映射到的目标 |
| `UnrealEditor_uasset加载流程.md` | UE 的 .uasset 加载管线文档 |
| `蓝图节点文本参考.md` | 蓝图节点序列化格式示例 |
| `CLAUDE.md` | 项目上下文和 GSD 工作流配置 |

## 命名约定

- **中文文件名** 用于参考文档
- **C++ 命名**: `AFirstPersonCCharacter` — UE 风格 `A` 前缀表示 Actor 类
- **蓝图命名**: `BP_` 前缀表示蓝图资产
