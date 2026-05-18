---
title: "Concerns"
date: 2026-05-18
focus: concerns
---

# Concerns

## High Risk

### Binary Format Complexity

UE's `.uasset` format is **not publicly documented**. The format is an internal UE implementation detail that can change between engine versions. Parsing requires reverse-engineering from UE source code (`LinkerLoad.cpp` — 274KB in the reference UE installation at `E:\Develop\lib\UnrealEngine\`).

**Mitigation**: Study `FLinkerLoad` implementation in UE source thoroughly before writing parser code.

### Version Compatibility

Different UE versions may have different `.uasset` binary layouts. A parser built for one version may fail on assets from another.

**Mitigation**: Target a specific UE version initially; document version compatibility.

## Medium Risk

### Scope Creep

The full .uasset format includes many subsystems (textures, materials, animations). This project should focus only on **Blueprint EventGraph** parsing.

**Mitigation**: Clear scope boundary in PROJECT.md — only Blueprint node extraction.

### Reference Document Quality

The reference docs (`UnrealEditor_uasset加载流程.md`, `蓝图节点文本参考.md`) are research notes, not formal specifications. They may contain gaps or inaccuracies.

**Mitigation**: Cross-reference with actual UE source code.

## Low Risk

### Small Codebase

The current codebase has no application code — everything needs to be built from scratch. This is expected for a new project.
