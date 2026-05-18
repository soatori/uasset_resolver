---
title: "Testing"
date: 2026-05-18
focus: quality
---

# Testing

## Current State

No test infrastructure exists.

## Test Assets Available

- `BP_FirstPersonCharacter.uasset` (56KB) — Real Blueprint asset for parser validation
- `测试对照C++类/` — Reference C++ class showing expected Blueprint-to-C++ mapping

## Recommended Testing Strategy

Once parser implementation begins:

1. **Unit tests**: Verify individual parsing functions (header parsing, export table extraction)
2. **Fixture tests**: Parse `BP_FirstPersonCharacter.uasset` and verify output matches expected node structure
3. **Regression tests**: Compare parser output against UE editor's Blueprint text export format (see `蓝图节点文本参考.md`)
