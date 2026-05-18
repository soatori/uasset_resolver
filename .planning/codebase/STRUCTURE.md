---
title: "Project Structure"
date: 2026-05-18
focus: arch
---

# Structure

## Directory Layout

```
E:/Develop/uasset_resolver/
├── .git/                          # Git repository (newly initialized)
├── .planning/                     # GSD planning documents
│   └── codebase/                  # Codebase mapping (this directory)
├── BP_FirstPersonCharacter.uasset # Test asset (56KB)
├── CLAUDE.md                      # Project instructions
├── UnrealEditor_uasset加载流程.md   # UE loading pipeline documentation
├── 蓝图节点文本参考.md              # Blueprint node text format reference
├── 测试对照C++类/                  # Reference C++ class
│   ├── BP_FirstPersonCharacter.uasset  # Duplicate test asset
│   ├── FirstPersonCCharacter.cpp     # C++ implementation
│   └── FirstPersonCCharacter.h       # C++ header
└── temp/                          # Cache/temp directory (gitignored)
```

## Key Locations

| Path | Purpose |
|------|---------|
| `BP_FirstPersonCharacter.uasset` | Primary test file for parser development |
| `测试对照C++类/` | C++ reference implementation showing what the Blueprint maps to |
| `UnrealEditor_uasset加载流程.md` | Documentation of UE's .uasset loading pipeline |
| `蓝图节点文本参考.md` | Blueprint node serialization format examples |
| `CLAUDE.md` | Project context and GSD workflow configuration |

## Naming Conventions

- **Chinese filenames** for reference documentation
- **C++ naming**: `AFirstPersonCCharacter` — UE-style `A` prefix for Actor classes
- **Blueprint naming**: `BP_` prefix for Blueprint assets
