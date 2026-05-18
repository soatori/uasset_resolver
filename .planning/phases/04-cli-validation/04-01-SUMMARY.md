---
plan_id: "04-01"
phase: "04-cli-validation"
status: "complete"
objective: "创建 scripts/main.py 统一 CLI 入口，合并 controller.py 和 cue4parse_controller.py 功能"
---

# Plan 04-01 Summary: 统一 CLI 入口

**What was built:** `scripts/main.py` — unified CLI entry point with argparse parameter grouping, version info, standard exit codes, and all backend logic (CUE4Parse, UE headless, auto).

**Key changes:**
- Created `scripts/main.py` with `run(argv=None)` function for testability
- Parameter groups: 基本参数 (uasset, --version), 后端参数 (--backend, --ue-path, --usmap, --timeout), 输出参数 (--format, --output)
- Exit codes: 0=success, 1=file/param error, 2=extraction failure
- Updated `scripts/controller.py` main() to deprecation warning + redirect to main.py
- Updated `scripts/__init__.py` to export all public functions

**Verification:**
- `python scripts/main.py --help` → exit 0, shows all grouped params
- `python scripts/main.py --version` → "uasset_resolver 0.1.0"
- `python scripts/main.py nonexistent.uasset` → exit 1, clear error message
