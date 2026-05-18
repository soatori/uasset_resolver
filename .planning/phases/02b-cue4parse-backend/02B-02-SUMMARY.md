# Phase 2B Plan 02: 统一控制器 Summary

> 合并 CUE4Parse 和 UE headless 为统一 CLI 入口，支持 --backend 切换。

## Frontmatter

```yaml
phase: 02b
plan: 02
subsystem: controller
tags: [cli, backend, cue4parse]
dependency:
  requires: [PARSE-03, Phase 2B-01]
  provides: ["--backend parameter on unified controller"]
  affects: [scripts/controller.py]
tech-stack:
  added: [argparse, subprocess, time.monotonic]
  patterns: [strategy pattern via backend branching]
key-files:
  created: [scripts/cue4parse_controller.py]
  modified: [scripts/controller.py]
decisions:
  - "Extracted ue-headless flow into _run_ue_headless_backend() for symmetry with cue4parse backend"
  - "auto mode checks BPExtractor.exe existence before attempting CUE4Parse"
  - "Output JSON uses PascalCase keys (NodeCount) matching BPExtractor native format"
metrics:
  duration: ~5min
  completed: "2026-05-18"
```

## One-liner

Unified CLI controller with `--backend` flag supporting cue4parse, ue-headless, and auto modes.

## Tasks Completed

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | 创建 cue4parse_controller.py | `5542d02` | `scripts/cue4parse_controller.py` (new) |
| 2 | 更新 controller.py 添加 --backend | `b5054da` | `scripts/controller.py` (modified) |

## Verification Results

1. `python scripts/cue4parse_controller.py --uasset BP_FirstPersonCharacter.uasset` → **exit 0**, JSON has `"backend": "cue4parse"` and `"extraction_time_ms"`
2. `python scripts/controller.py --backend cue4parse --uasset BP_FirstPersonCharacter.uasset` → **exit 0**, 12 nodes extracted, JSON has `"backend": "cue4parse"`
3. `python scripts/controller.py --backend auto --uasset BP_FirstPersonCharacter.uasset` → **exit 0**, CUE4Parse selected automatically
4. `python scripts/controller.py --help` → shows `--backend {cue4parse,ue-headless,auto}` option
5. Error handling: missing file → **exit 1**

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Threat Flags

None.

## Self-Check: PASSED

- [x] `scripts/cue4parse_controller.py` exists
- [x] `scripts/controller.py` modified with --backend
- [x] Commit `5542d02` exists
- [x] Commit `b5054da` exists
- [x] JSON output verified with backend field
- [x] Error exit codes verified
