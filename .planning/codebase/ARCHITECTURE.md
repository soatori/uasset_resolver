---
title: "Architecture"
date: 2026-05-18
focus: arch
---

# Architecture

## Pattern

**Reference tool / parser** — No application code exists yet. The codebase currently consists of:

1. A test asset (`BP_FirstPersonCharacter.uasset`)
2. A reference C++ class (`测试对照C++类/`)
3. Domain research documents in Chinese

## Layers (Target Architecture)

Based on project goals in `CLAUDE.md`, the intended architecture is:

```
.uasset binary file
    ↓
FLinkerLoad-style parser (to be implemented)
    ↓
Structured document output (JSON/Markdown)
    ↓
Blueprint EventGraph node representation
```

## Data Flow

1. Input: `.uasset` binary file on disk
2. Parse: Binary deserialization following UE's `FLinkerLoad` pattern
3. Extract: Export table, import table, object serialization data
4. Output: Human-readable blueprint node structure with:
   - Node types and function references
   - Pin definitions and connections
   - Canvas positions and GUIDs

## Abstractions

None implemented yet. Target abstractions based on UE source:

- **Package** — `.uasset` file container
- **Export Table Entry** — Serializable objects within the package
- **Blueprint Node** — Individual graph element (events, functions, variables)
- **Pin** — Connection point on a node (input/output with type info)

## Entry Points

No executable entry points exist yet.
