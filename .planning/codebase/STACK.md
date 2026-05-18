---
title: "Tech Stack"
date: 2026-05-18
focus: tech
---

# Tech Stack

## Languages & Runtime

- **C++** — Unreal Engine native code (UE 5.x, template-based character class)
- **Blueprint Visual Scripting** — `.uasset` binary assets contain serialized Blueprint graphs

## Frameworks & Engines

- **Unreal Engine 5** — Game engine and asset pipeline
  - `ACharacter` base class — pawn/character framework
  - `USkeletalMeshComponent` — first-person arm mesh
  - `UCameraComponent` — first-person camera
  - Enhanced Input system (`UInputAction`, `FInputActionValue`)

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `CoreMinimal.h` | UE built-in | Core types and macros |
| `GameFramework/Character.h` | UE built-in | Character base class |
| `Logging/LogMacros.h` | UE built-in | Logging utilities |

## Configuration

- No build configuration files present in repo (`.Build.cs`, `.Target.cs` missing — likely part of a larger UE project)
- `.gitignore` excludes `temp/` directory for cache/temporary files

## Key Observations

- The `.uasset` file is a **binary serialized format** — not human-readable
- Blueprint nodes serialize as `Begin Object ... End Object` blocks with pins, positions, and function references
- Reference docs exist in Chinese (`UnrealEditor_uasset加载流程.md`, `蓝图节点文本参考.md`)
