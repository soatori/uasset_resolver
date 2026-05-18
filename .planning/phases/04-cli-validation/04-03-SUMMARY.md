---
plan_id: "04-03"
phase: "04-cli-validation"
status: "complete"
objective: "交叉验证 — verify.py 模块 + --verify 参数集成"
---

# Plan 04-03 Summary: 交叉验证

**What was built:** `scripts/verify.py` verification module and `--verify`/`--verify-ref` CLI flags.

**Key changes:**
- Created `scripts/verify.py` with `verify_output(output_data, reference_path) -> VerificationReport`
- Parses `蓝图节点文本参考.md` Begin Object/End Object blocks via regex
- 4 validation dimensions: node count (>=30%), name match (>=10%), function refs, pin structure
- Graceful degradation for .usmap missing: functions/pins/coords skipped when empty
- Added `--verify` and `--verify-ref` args to main.py
- main.py calls verify after successful extraction, exit code 3 on failure
