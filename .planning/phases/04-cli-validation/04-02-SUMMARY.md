---
plan_id: "04-02"
phase: "04-cli-validation"
status: "complete"
objective: "加载策略 — CUE4Parse 裸文件直接加载 + UE headless 回退提示"
---

# Plan 04-02 Summary: 加载策略

**What was built:** `--content-dir` parameter for main.py and structured fallback error messages.

**Key changes:**
- Added `--content-dir PATH` to main.py backend params — allows custom UE Content directory
- `_run_ue_headless_backend()` now accepts `content_dir` param, validates it exists
- `_select_backend_auto()` passes `content_dir` through to ue-headless fallback
- When all backends fail: prints structured error with 3 options:
  1. 编译 CUE4Parse 后端（推荐）
  2. 指定 UE 项目目录：--content-dir
  3. 指定引擎路径：--ue-path

**Note:** Task 2.1 (CUE4Parse 裸文件直接加载) was already satisfied — `BPExtractor.extract_to_dict()` already accepts absolute paths and main.py passes them directly.
