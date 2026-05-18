# Phase 1: UE Headless Bridge - Research

**Researched:** 2026-05-18
**Domain:** Unreal Engine 5.7 headless execution, Python scripting, asset loading
**Confidence:** HIGH (verified via UE source code + official docs + web search)

## Summary

This phase requires launching UE 5.7 editor in headless mode from an external Python process, executing an embedded Python script to load a `.uasset` file, determine if it's a Blueprint, and write results to JSON. The research confirms this is feasible but requires several non-obvious setup steps.

**Critical findings:**
1. The `-ExecutePythonScript=` flag requires the **full editor** (not a commandlet), which means a `.uproject` file is mandatory — even a minimal one.
2. Both the **PythonScriptPlugin** and **EditorScriptingUtilities** plugins ship with UE 5.7 but are **disabled by default** (`EnabledByDefault: false`). They must be enabled via the `.uproject` file.
3. UE's Python `load_asset()` API works with **virtual paths** (`/Game/...`), not filesystem paths. The `.uasset` file must be placed in the project's `Content/` directory.
4. The editor auto-exits after script execution via `QUIT_EDITOR` deferred command, but the script should also call `unreal.SystemLibrary.quit_editor()` as a safety measure.
5. UE 5.7 bundles **Python 3.11** at `Engine/Binaries/ThirdParty/Python3/Win64/python.exe`.

**Primary recommendation:** Create a minimal `.uproject` with both plugins enabled, copy the test `.uasset` into `Content/`, launch headless with `-NullRHI -unattended -ExecutePythonScript=`, and use `unreal.EditorAssetLibrary.load_asset()` with `isinstance()` checks for Blueprint detection.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** 使用外部 .py 文件，通过 UE 命令行参数 `-ExecutePythonScript=path/to/script.py` 传入。脚本放在项目 `scripts/ue_extract.py`，便于迭代调试。
- **D-02:** UE 内嵌脚本将结果写入 `temp/` 目录下的 JSON 文件，外部 Python 控制脚本读取该文件。不依赖 stdout 管道（UE 日志系统不可靠）。
- **D-03:** 临时文件路径由外部脚本传入参数指定，格式：`--output temp/result.json`。
- **D-04:** 检查加载后的包中是否包含 `UBlueprintGeneratedClass` 类型的对象来判定 Blueprint。
- **D-05:** 架构需保留可扩展性——未来支持其他资产类型（材质、动画等）时，类型检测逻辑应可插拔。
- **D-06:** Phase 1 使用固定超时（60-120 秒），超时后 `subprocess.kill()`。只需报告成功/失败，不做详细诊断。
- **D-07:** 后续 Phase 可演进为智能超时 + 重试（监控输出关键词判断状态）。
- **D-08:** 混合模式：自动扫描 Windows 注册表（`HKLM\SOFTWARE\EpicGames\Unreal Engine`）和已知安装路径 → 失败后提示用户通过 CLI 参数 `--ue-path` 手动指定。
- **D-09:** 首次检测成功后，将引擎路径缓存到项目配置文件中，避免重复扫描。

### Claude's Discretion
- 临时文件的 JSON 结构由实现者决定，只要能被外部脚本正确读取即可。
- UE 内嵌脚本中的 `print` 输出格式无特殊要求，主要用于调试日志。

### Deferred Ideas (OUT OF SCOPE)
- 智能超时 + 重试（D-07）——后续 Phase 实现
- 非 Blueprint 资产类型支持（D-05 扩展性）—— v2 需求，已列在 REQUIREMENTS.md v2 中

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| UE headless process management | External Python (subprocess) | — | External process spawns and monitors UE |
| UE Python script execution | UE Embedded Python | — | `-ExecutePythonScript` runs inside UE editor |
| Asset loading (.uasset → UObject) | UE Editor (Python API) | — | `EditorAssetLibrary.load_asset()` requires editor context |
| Blueprint type detection | UE Embedded Python | — | `isinstance()` checks on loaded asset |
| JSON output writing | UE Embedded Python | External Python reads | Script writes to `temp/`, external process reads |
| Engine path auto-detection | External Python | — | Registry scan and filesystem probing before UE launch |
| Timeout & process kill | External Python | — | `subprocess` timeout with `kill()` |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `unreal` (built-in UE module) | UE 5.7 bundled | Asset loading, Blueprint inspection, editor control | UE's official Python integration — no third-party install needed |
| `unreal.EditorAssetLibrary` | UE 5.7 bundled | `load_asset()`, `save_loaded_asset()`, `does_asset_exist()` | Primary asset manipulation API in UE Python |
| `unreal.EditorFilterLibrary` | UE 5.7 bundled | Asset type filtering and classification | Utility for extensible type detection (D-05) |
| `unreal.BlueprintEditorLibrary` | UE 5.7 bundled | `find_event_graph()`, graph node access | Blueprint graph inspection |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `json` (Python stdlib) | Python 3.11 | JSON output serialization | Writing results to `temp/result.json` |
| `sys` (Python stdlib) | Python 3.11 | `sys.argv` parsing | Reading `--output` parameter in UE script |
| `subprocess` (Python stdlib) | Python 3.11 | Process spawning, timeout management | External controller script |
| `winreg` (Python stdlib) | Python 3.11 | Windows registry reading | Engine path auto-detection (D-08) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Full editor + `-ExecutePythonScript` | Commandlet `-run=PythonScript` | Commandlet has NO asset loading — `EditorPythonExecuter.cpp` explicitly forbids it (line 187: "-ExecutePythonScript cannot be used by a commandlet") |
| `EditorAssetLibrary.load_asset()` | `FLinkerLoad` via custom C++ plugin | Requires recompiling engine — far too complex for Phase 1 |
| `-NullRHI` | `-windowed -ResX=1 -ResY=1` | Windowed still creates a GPU window; `-NullRHI` is true headless |

**Installation:**
No external packages needed. UE 5.7 bundles Python 3.11 with the `unreal` module built-in. Both required plugins ship with the engine — just need to enable them in the project.

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| `unreal` (UE built-in module) | N/A (bundled with UE) | — | — | Epic Games UE source | N/A | Approved — official UE module |
| `json` (stdlib) | N/A | — | — | Python stdlib | N/A | Approved |
| `subprocess` (stdlib) | N/A | — | — | Python stdlib | N/A | Approved |
| `winreg` (stdlib) | N/A | — | — | Python stdlib | N/A | Approved |

**No external packages installed.** All dependencies are either UE built-in modules or Python stdlib.

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    External Python                       │
│  (E:\Develop\uasset_resolver\scripts\controller.py)      │
│                                                          │
│  1. Detect/cache UE path (registry scan)                 │
│  2. Build command: UnrealEditor.exe + flags              │
│  3. subprocess.run(timeout=120s)                         │
│  4. Read temp/result.json                                │
└──────────────────────┬──────────────────────────────────┘
                       │ subprocess call
                       ▼
┌─────────────────────────────────────────────────────────┐
│               UE 5.7 Editor (headless)                   │
│  UnrealEditor.exe "minimal.uproject"                     │
│  -NullRHI -unattended -NoLoadingScreen                   │
│  -ExecutePythonScript="scripts/ue_extract.py"            │
│  --output "temp/result.json"                             │
│                                                          │
│  1. Editor boots (null RHI, no window)                   │
│  2. PythonScriptPlugin initializes (Python 3.11)         │
│  3. ue_extract.py runs after asset registry ready        │
│  4. EditorAssetLibrary.load_asset("/Game/...")           │
│  5. isinstance(asset, unreal.Blueprint) → type check     │
│  6. json.dump(results, open(output_path, "w"))           │
│  7. unreal.SystemLibrary.quit_editor()                   │
└─────────────────────────────────────────────────────────┘
                       │ exit code 0
                       ▼
┌─────────────────────────────────────────────────────────┐
│                    External Python                       │
│  1. Check subprocess return code                         │
│  2. Read & parse temp/result.json                        │
│  3. Report success/failure                               │
└─────────────────────────────────────────────────────────┘
```

### Recommended Project Structure
```
E:\Develop\uasset_resolver\
├── minimal.uproject          # Minimal UE project for headless execution
├── Content/                  # UE Content directory (uasset files go here)
│   └── BP_FirstPersonCharacter.uasset   # Test asset (copied or symlinked)
├── scripts/
│   ├── controller.py         # External Python: launch UE, monitor, collect
│   └── ue_extract.py         # Internal UE Python: load asset, detect type, output JSON
├── temp/                     # Output directory (gitignored)
│   └── result.json           # Script output
└── temp/
    └── ue_config.json        # Cached engine path (D-09)
```

### Pattern 1: Headless Editor Execution
**What:** Launch UE editor with no GUI, run Python script, auto-exit
**When to use:** Asset inspection, batch processing, CI/CD pipelines
**Example:**
```bash
# Source: Verified from EditorPythonExecuter.cpp lines 142-211 + WebSearch community patterns
"D:\Program Files\Epic Games\Engine\UE_5.7\Engine\Binaries\Win64\UnrealEditor.exe" ^
  "E:\Develop\uasset_resolver\minimal.uproject" ^
  -NullRHI ^
  -unattended ^
  -NoLoadingScreen ^
  -NoScreenMessages ^
  -stdout ^
  -ExecutePythonScript="E:\Develop\uasset_resolver\scripts\ue_extract.py --output E:\Develop\uasset_resolver\temp\result.json"
```

### Pattern 2: Blueprint Detection via type checking
**What:** Load asset with `EditorAssetLibrary.load_asset()`, check `isinstance(asset, unreal.Blueprint)`
**When to use:** Asset type identification pipelines
**Example:**
```python
# Source: Verified from UE Python API docs + WebSearch community patterns
import unreal
import json
import sys

# Parse output path from args
output_path = "temp/result.json"  # default
for i, arg in enumerate(sys.argv):
    if arg == "--output" and i + 1 < len(sys.argv):
        output_path = sys.argv[i + 1]

# Load asset using virtual path (NOT filesystem path)
asset_path = "/Game/BP_FirstPersonCharacter"
asset = unreal.EditorAssetLibrary.load_asset(asset_path)

result = {
    "asset_path": asset_path,
    "is_blueprint": isinstance(asset, unreal.Blueprint),
    "asset_class": asset.get_class().get_name(),
}

if isinstance(asset, unreal.Blueprint):
    bp = asset
    generated_class = bp.generated_class
    result["generated_class"] = str(generated_class) if generated_class else None
    # Check for EventGraph (D-05 extensibility)
    event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    result["has_event_graph"] = event_graph is not None

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"Result written to {output_path}")

# Safety exit
unreal.SystemLibrary.quit_editor()
```

### Pattern 3: Engine Path Auto-Detection (Windows)
**What:** Scan registry + known paths, cache result
**When to use:** Phase 1 engine discovery (D-08)
**Example:**
```python
import winreg
import os
import json

def find_ue_install():
    # Try registry: HKLM\SOFTWARE\EpicGames\Unreal Engine
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\EpicGames\Unreal Engine")
        # Iterate subkeys (version numbers like "5.7")
        i = 0
        while True:
            try:
                version = winreg.EnumKey(key, i)
                subkey = winreg.OpenKey(key, version)
                path, _ = winreg.QueryValueEx(subkey, "InstalledDirectory")
                editor_exe = os.path.join(path, "Engine", "Binaries", "Win64", "UnrealEditor.exe")
                if os.path.exists(editor_exe):
                    return editor_exe
            except OSError:
                break
            i += 1
    except OSError:
        pass

    # Fallback: known install paths
    known_paths = [
        r"D:\Program Files\Epic Games\Engine\UE_5.7",
        r"C:\Program Files\Epic Games\UE_5.7",
    ]
    for base in known_paths:
        exe = os.path.join(base, "Engine", "Binaries", "Win64", "UnrealEditor.exe")
        if os.path.exists(exe):
            return exe

    return None
```

### Anti-Patterns to Avoid
- **Using `UnrealEditor-Cmd.exe` with `-ExecutePythonScript`**: The source code (`EditorPythonExecuter.cpp:186-188`) explicitly rejects this combination. Use `-run=PythonScript` with Cmd instead, but note commandlets cannot load assets.
- **Passing filesystem paths to `load_asset()`**: `EditorAssetLibrary.load_asset()` expects virtual paths (`/Game/...`), not `C:\path\to\file.uasset`. The asset must be in the project's `Content/` directory.
- **Relying on stdout for results**: UE's logging system captures Python `print()` output but formatting is unreliable in headless mode (D-02 decision confirms file-based output).
- **Forgetting to enable plugins**: Both `PythonScriptPlugin` and `EditorScriptingUtilities` are `EnabledByDefault: false`. The `.uproject` must list them.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Asset loading from `.uasset` binary | Custom binary parser for .uasset format | `unreal.EditorAssetLibrary.load_asset()` | UE's `FLinkerLoad` handles serialization, versioning, and object references — reimplementing would be thousands of lines |
| Blueprint type detection | Manual class name string comparison | `isinstance(asset, unreal.Blueprint)` | UE's Python wrapper handles inheritance correctly; string matching breaks on BlueprintGeneratedClass vs Blueprint |
| JSON serialization | Manual string formatting | Python `json.dump()` | Edge cases with escaping, encoding, and nested structures |
| Engine path detection | Hardcoded paths only | Registry scan + fallback | User may have installed to custom location; registry is the authoritative source |

**Key insight:** The `.uasset` binary format is complex (FLinkerLoad serialization, name tables, import/export tables, bulk data). The whole point of this phase is to leverage UE's own loader instead of reverse-engineering the format.

## Runtime State Inventory

N/A — This is a greenfield phase (no existing application code to refactor). No runtime state categories apply.

## Common Pitfalls

### Pitfall 1: Plugins Not Enabled
**What goes wrong:** `-ExecutePythonScript` silently does nothing, or errors "Python support is disabled"
**Why it happens:** Both `PythonScriptPlugin` (Experimental) and `EditorScriptingUtilities` (Editor) have `EnabledByDefault: false` in their `.uplugin` files
**How to avoid:** Add both plugins to `.uproject` with `"Enabled": true`. Also set `"EnablePython"` to `true` in editor settings or use `-EnablePython` flag.
**Warning signs:** UE log shows "Python disabled via CVar" or "PythonScriptPlugin cannot be used when Python support is disabled"

### Pitfall 2: Asset Not Found by Virtual Path
**What goes wrong:** `load_asset("/Game/BP_FirstPersonCharacter")` returns `None`
**Why it happens:** The `.uasset` file is not in the project's `Content/` directory, or the virtual path doesn't match the file's location
**How to avoid:** Copy/symlink the `.uasset` into `Content/` before launching UE. Virtual path = `/Game/` + relative path within Content dir (without `.uasset` extension).
**Warning signs:** UE log shows "Asset not found" or `load_asset` returns `None`

### Pitfall 3: Editor Hangs After Script
**What goes wrong:** UE process doesn't exit after Python script completes
**Why it happens:** The `QUIT_EDITOR` deferred command runs after a full tick cycle; if the script ends before the editor fully initializes, timing issues can occur
**How to avoid:** Always call `unreal.SystemLibrary.quit_editor()` at the end of the script. Use the external subprocess timeout (D-06) as a safety net.
**Warning signs:** `subprocess.run(timeout=120)` triggers timeout, process must be killed

### Pitfall 4: Spaces in Paths Break Command Line Parsing
**What goes wrong:** `-ExecutePythonScript="C:\My Scripts\script.py"` fails to parse correctly
**Why it happens:** The command line parser in `EditorPythonExecuter.cpp` handles quotes specially; nested quotes require escaping
**How to avoid:** Use forward slashes, avoid spaces in paths, or use proper quote escaping: `-ExecutePythonScript="\"C:/My Scripts/script.py\""`
**Warning signs:** UE log shows "Could not load Python file" or script path appears truncated

### Pitfall 5: Asset Registry Not Ready When Script Runs
**What goes wrong:** Script runs but assets are not available in the registry
**Why it happens:** `EditorPythonExecuter` waits for `IAssetRegistry::GetChecked().IsLoadingAssets()` to return false before running (line 86), but if the project has never been opened, the asset registry may need to scan
**How to avoid:** For a minimal project, this is typically fast. If issues arise, use `-ForceRescan` flag or open the project in the editor once to build the registry.
**Warning signs:** `load_asset()` returns `None` even though the file exists in `Content/`

### Pitfall 6: No .uproject File
**What goes wrong:** UE editor refuses to start without a project file
**Why it happens:** `-ExecutePythonScript` is an editor feature (not a commandlet feature) and the editor requires a `.uproject` context
**How to avoid:** Create a minimal `.uproject` file (see Standard Stack section). The project doesn't need any content or levels — just the file must exist.
**Warning signs:** UE shows project browser or error dialog

## Code Examples

### Minimal .uproject File
```json
{
    "FileVersion": 3,
    "EngineAssociation": "5.7",
    "Category": "",
    "Description": "",
    "Plugins": [
        {
            "Name": "PythonScriptPlugin",
            "Enabled": true
        },
        {
            "Name": "EditorScriptingUtilities",
            "Enabled": true
        }
    ]
}
```

### Complete ue_extract.py (UE Embedded Script)
```python
"""
UE embedded Python script: Load a .uasset asset, detect if it's a Blueprint,
and write results to a JSON file.

Usage (via -ExecutePythonScript):
  -ExecutePythonScript="scripts/ue_extract.py --output temp/result.json"
"""
import unreal
import json
import sys

def parse_args():
    """Parse --output argument from command line."""
    output_path = "temp/result.json"
    for i, arg in enumerate(sys.argv):
        if arg == "--output" and i + 1 < len(sys.argv):
            output_path = sys.argv[i + 1]
    return output_path

def detect_asset_type(asset):
    """Determine asset type using isinstance checks (extensible per D-05)."""
    if asset is None:
        return {"error": "Asset not found or failed to load"}

    asset_class = asset.get_class().get_name()
    result = {
        "asset_class": asset_class,
        "is_blueprint": isinstance(asset, unreal.Blueprint),
        "is_material": isinstance(asset, unreal.Material),
        "is_static_mesh": isinstance(asset, unreal.StaticMesh),
        "is_skeletal_mesh": isinstance(asset, unreal.SkeletalMesh),
    }

    if isinstance(asset, unreal.Blueprint):
        bp = asset
        generated_class = bp.generated_class
        result["generated_class"] = str(generated_class) if generated_class else None
        result["parent_class"] = str(bp.parent_class) if bp.parent_class else None

        # EventGraph detection
        event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
        result["has_event_graph"] = event_graph is not None
        if event_graph:
            result["event_graph_name"] = event_graph.get_fname()
            result["node_count"] = len(event_graph.nodes) if event_graph.nodes else 0

    return result

def main():
    output_path = parse_args()
    print(f"[ue_extract] Output path: {output_path}")

    # Virtual path of the asset (must be in Content/ directory)
    asset_path = "/Game/BP_FirstPersonCharacter"
    print(f"[ue_extract] Loading asset: {asset_path}")

    asset = unreal.EditorAssetLibrary.load_asset(asset_path)
    result = detect_asset_type(asset)
    result["asset_path"] = asset_path

    # Write JSON
    print(f"[ue_extract] Writing result...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"[ue_extract] Done. Blueprint={result.get('is_blueprint', False)}")

    # Exit the editor
    unreal.SystemLibrary.quit_editor()

if __name__ == "__main__":
    main()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| UE4 Python 2.7 support | UE5 Python 3.11 bundled | UE 5.0 | Modern Python syntax, type hints available |
| Manual C++ plugin for asset loading | `unreal.EditorAssetLibrary` Python API | UE 4.25+ | No compilation needed, pure Python scripting |
| `EditorUtilityWidget` for automation | `-ExecutePythonScript` headless | UE 5.0+ | No UI needed, CI/CD friendly |
| `-game` flag for batch processing | `-NullRHI -unattended` | UE 5.x | True headless, no GPU context required |

**Deprecated/outdated:**
- **`UnrealPak` for asset extraction**: Only works for `.pak` files, not individual `.uasset` files
- **UE4 Python 2.x**: UE 5.x uses Python 3.11; Python 2 syntax will fail
- **`EditorAssetLibrary.does_asset_exist()` before `load_asset()`**: Not needed — `load_asset()` returns `None` if not found

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `unreal.BlueprintEditorLibrary.find_event_graph()` exists in UE 5.7 | Code Examples | MEDIUM — API name may differ; needs runtime verification |
| A2 | UE 5.7 bundled Python is 3.11 | Standard Stack | LOW — confirmed by `python311.dll` in UE installation |
| A3 | `-ExecutePythonScript` works with `-NullRHI` simultaneously | Architecture Patterns | LOW — both are standard flags, widely documented together |
| A4 | `EditorScriptingUtilities` provides `EditorAssetLibrary` to Python | Standard Stack | LOW — confirmed by C++ API docs linking `UEditorAssetLibrary` to this plugin |
| A5 | Minimal `.uproject` without a level/map can still load assets | Architecture Patterns | MEDIUM — asset loading requires the asset registry, which may need a level; needs runtime verification |

## Open Questions

1. **Does a minimal .uproject without any levels still load the asset registry?**
   - What we know: `EditorPythonExecuter` waits for `IsLoadingAssets()` to return false before running the script
   - What's unclear: If no levels exist, does the registry scan still happen? The asset registry scans the Content directory on first open
   - Recommendation: Create the minimal project and test — if registry scan fails, add an empty map

2. **Can `EditorAssetLibrary.load_asset()` load assets from outside the Content directory?**
   - What we know: Virtual paths map to `Content/` directory
   - What's unclear: Whether `ImportAsset` or other methods can load from arbitrary filesystem paths
   - Recommendation: For Phase 1, copy the asset into `Content/` — keep it simple. Phase 2 can explore external loading

3. **What is the exact exit code of UnrealEditor.exe after `-ExecutePythonScript` completes?**
   - What we know: `PythonScriptCommandlet::Main` returns 0 on success, -1 on error
   - What's unclear: The editor path (not commandlet) may return different exit codes
   - Recommendation: Test and document; use timeout-based detection as fallback (D-06)

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| UnrealEditor.exe | Headless asset loading | Verified | UE 5.7 | `D:\Program Files\Epic Games\Engine\UE_5.7\Engine\Binaries\Win64\UnrealEditor.exe` |
| UnrealEditor-Cmd.exe | Alternative (not needed for D-01) | Verified | UE 5.7 | Not used — D-01 requires full editor |
| Python 3.11 (bundled) | UE Python execution | Verified | 3.11.x | Bundled with UE at `Engine/Binaries/ThirdParty/Python3/Win64/` |
| PythonScriptPlugin | `-ExecutePythonScript` support | Verified (in installed UE) | 1.0 (beta) | Must be enabled via `.uproject` |
| EditorScriptingUtilities | `EditorAssetLibrary` API | Verified (in installed UE) | 1.0 (beta) | Must be enabled via `.uproject` |
| `.uproject` file | Editor context | Not yet created | — | Must create minimal project file |
| `BP_FirstPersonCharacter.uasset` in Content/ | Asset loading | File exists at project root | 56KB | Must be copied to `Content/` |
| `winreg` (Python stdlib) | Registry path detection | Available | Python 3.11 | Fallback to known paths |
| `subprocess` (Python stdlib) | Process management | Available | Python 3.11 | — |

**Missing dependencies requiring setup:**
- `minimal.uproject` — must create (see Code Examples)
- `Content/BP_FirstPersonCharacter.uasset` — must copy from project root
- Both plugins must be enabled in `.uproject`

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Python `unittest` (stdlib) or manual execution |
| Config file | None — Phase 1 is a spike |
| Quick run command | `python scripts/controller.py --test` (manual) |
| Full suite command | N/A |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PARSE-01 | Launch UE headless, load asset, detect Blueprint | Manual E2E | Run controller.py | No — will be created in plan |
| PARSE-02 | Output JSON to temp/ with correct structure | Manual E2E | Check temp/result.json | No — will be created in plan |

### Wave 0 Gaps
- [ ] Basic smoke test script to verify UE launch + script execution
- [ ] No test framework configured yet — Phase 1 is a proof-of-concept spike

## Security Domain

`security_enforcement` is not configured in `.planning/config.json`, so this section is included.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No user authentication — local tool only |
| V3 Session Management | No | No sessions |
| V4 Access Control | No | No access control needed |
| V5 Input Validation | Yes | Validate asset path parameters, JSON output sanitization |
| V6 Cryptography | No | No cryptographic operations |

### Known Threat Patterns for UE Headless Automation

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malicious .uasset file causing UE crash | Tampering | Use subprocess timeout (D-06); validate exit code |
| Path injection via --output parameter | Tampering | Sanitize output path, restrict to project temp/ directory |
| UE process hanging after script | Denial of Service | Subprocess timeout with `kill()` (D-06) |

## Sources

### Primary (HIGH confidence)
- UE Source: `E:\Develop\lib\UnrealEngine\Engine\Plugins\Experimental\PythonScriptPlugin\PythonScriptPlugin.uplugin` — Plugin config (EnabledByDefault: false, IsBetaVersion)
- UE Source: `E:\Develop\lib\UnrealEngine\Engine\Plugins\Experimental\PythonScriptPlugin\Source\PythonScriptPlugin\Private\PythonScriptPlugin.cpp` — Python initialization, `unreal` module setup, `IsPythonEnabled()` logic
- UE Source: `E:\Develop\lib\UnrealEngine\Engine\Plugins\Experimental\PythonScriptPlugin\Source\PythonScriptPlugin\Private\EditorUtilities\EditorPythonExecuter.cpp` — `-ExecutePythonScript` handling, exit behavior, commandlet rejection
- UE Source: `E:\Develop\lib\UnrealEngine\Engine\Plugins\Experimental\PythonScriptPlugin\Source\PythonScriptPlugin\Private\PythonScriptCommandlet.cpp` — Commandlet execution (not used for D-01)
- UE Source: `E:\Develop\lib\UnrealEngine\Engine\Plugins\Editor\EditorScriptingUtilities\EditorScriptingUtilities.uplugin` — Plugin config
- UE Installed: `D:\Program Files\Epic Games\Engine\UE_5.7\Engine\Binaries\ThirdParty/Python3/Win64/python.exe` — Python 3.11 confirmed
- UE Installed: `D:\Program Files\Epic Games\Engine\UE_5.7\Engine\Binaries\Win64\UnrealEditor.exe` — Editor binary confirmed
- UE Installed: `D:\Program Files\Epic Games\Engine\UE_5.7\Engine\Binaries\Win64\UnrealEditor-Cmd.exe` — Commandlet binary confirmed

### Secondary (MEDIUM confidence)
- [Unreal Engine Command-Line Arguments Reference](https://dev.epic<think>.com/documentation/unreal-engine/unreal-engine-command-line-arguments-reference) - Flag documentation
- [Scripting the Unreal Editor Using Python](https://dev.epicgames.com/documentation/unreal-engine/scripting-the-unreal-editor-using-python) - Official Python docs
- [UEditorAssetLibrary::LoadAsset | UE 5.7](https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/EditorScriptingUtilities/UEditorAssetLibrary/LoadAsset) - API reference
- [unreal.BlueprintEditorLibrary | UE 5.2](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/BlueprintEditorLibrary?application_version=5.2) - Blueprint graph API
- Web search: Community patterns for headless UE execution with `-NullRHI -unattended -ExecutePythonScript`
- Web search: Windows registry UE install path at `HKLM\SOFTWARE\EpicGames\Unreal Engine`

### Tertiary (LOW confidence)
- API method name `find_event_graph()` — needs runtime verification in UE 5.7
- Exit code behavior of full editor after script — needs runtime testing

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified via UE source code and installed binaries
- Architecture: HIGH — EditorPythonExecuter.cpp confirms all architectural assumptions
- Pitfalls: MEDIUM — based on source code analysis + community reports, needs runtime verification
- Plugin configuration: HIGH — directly read from `.uplugin` files
- API availability: MEDIUM — `EditorAssetLibrary` confirmed, `BlueprintEditorLibrary.find_event_graph()` needs verification

**Research date:** 2026-05-18
**Valid until:** 30 days (UE 5.7 APIs are stable; plugin configuration unlikely to change)
