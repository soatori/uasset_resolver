# Phase 2B Plan 01: CUE4Parse Python 封装 Summary

> Python 封装 BPExtractor.exe，提供类型化数据接口（dataclasses + subprocess 调用）。

---

phase: 2b
plan: "01"
type: auto
tags: [python, cue4parse, wrapper, bpextractor]
status: complete
dependency_graph:
  requires: ["Phase 2B Wave 1 (BPExtractor.exe 已编译发布)"]
  provides: ["scripts/cue4parse_extractor 可被 import", "extract_to_dict() 返回 dict", "extract() 返回 BlueprintGraph"]
  affects: ["scripts/"]
tech-stack:
  added: [Python 3.14, unittest]
  patterns: [dataclass, subprocess, JSON parsing]
key-files:
  created:
    - scripts/cue4parse_extractor.py
    - scripts/test_cue4parse_extractor.py
    - scripts/__init__.py
  modified: []
decisions:
  - "兼容 PascalCase 和 snake_case JSON key（BPExtractor 输出使用 PascalCase）"
  - "使用 unittest 而非 pytest（无额外依赖）"
metrics:
  duration: ~5min
  completed: 2026-05-18
  tasks_completed: 2
  tests: 8 passed

---

## Objective

Create `scripts/cue4parse_extractor.py` and `scripts/test_cue4parse_extractor.py` to wrap BPExtractor.exe with typed Python interfaces.

## Verification Results

- `python -c "from scripts.cue4parse_extractor import BPExtractor; print('OK')"` — OK
- `python -m unittest scripts.test_cue4parse_extractor -v` — 8/8 passed

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] JSON key format mismatch**
- **Found during:** Task 2 (test execution)
- **Issue:** BPExtractor.exe outputs JSON with PascalCase keys (`PackageName`, `Nodes`, `Graphs`) instead of the snake_case keys assumed by the plan (`package_name`, `nodes`, `graphs`). This caused `_graph_from_dict` to return empty nodes list and `extract_to_dict` tests to fail on `assertIn("package_name")`.
- **Fix:** Added `_get()` helper that tries multiple key names (snake_case, PascalCase, camelCase) in order. Updated all `_from_dict` functions to use it. Updated test assertions to check for either key format.
- **Files modified:** `scripts/cue4parse_extractor.py`, `scripts/test_cue4parse_extractor.py`
- **Commit:** de61d02

## Known Limitations (Plan-acknowledged)

- `.usmap` 文件缺失，导致坐标/GUID/Pins 为空 — 这是 BPExtractor 层面的限制，非本 Wave 解决范围。

## Known Stubs

None — all dataclasses have proper defaults; BPExtractor output is fully mapped.

## Self-Check: PASSED

- [x] `scripts/cue4parse_extractor.py` exists
- [x] `scripts/test_cue4parse_extractor.py` exists
- [x] `scripts/__init__.py` exists
- [x] Commit de61d02 verified in git log
