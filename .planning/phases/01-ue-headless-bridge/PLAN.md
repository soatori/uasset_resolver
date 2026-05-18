---
phase: 01-ue-headless-bridge
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - .gitignore
  - minimal.uproject
  - Content/
  - temp/
  - scripts/ue_extract.py
  - scripts/controller.py
autonomous: false
requirements: [PARSE-01, PARSE-02]
user_setup:
  - service: UE 5.7
    why: "无头资产加载需要安装 UE 5.7 编辑器"
    env_vars:
      - name: UE_PATH（可选）
        source: "自动检测失败时的手动覆盖"
    dashboard_config:
      - task: "验证 UE 5.7 已安装在 D:\\Program Files\\Epic Games\\Engine\\UE_5.7"
        location: "Epic Games Launcher 或文件系统"

must_haves:
  truths:
    - "运行 controller.py 以 -unattended -NullRHI 参数启动 UE 5.7"
    - "UE 通过 -ExecutePythonScript 参数执行 scripts/ue_extract.py"
    - "scripts/ue_extract.py 加载测试资产并将 JSON 写入 temp/output"
    - "JSON 结果正确识别 BP_FirstPersonCharacter 为蓝图"
    - "UE 进程在 120 秒超时内退出（无残留编辑器窗口）"
  artifacts:
    - path: "minimal.uproject"
      provides: "最小 UE 项目，启用 PythonScriptPlugin + EditorScriptingUtilities"
      contains: '"PythonScriptPlugin"'
    - path: "Content/BP_FirstPersonCharacter.uasset"
      provides: "UE Content/ 目录中的测试资产，用于虚拟路径加载"
    - path: "scripts/ue_extract.py"
      provides: "UE 内嵌脚本：资产加载、类型检测、JSON 输出"
      exports: ["main"]
    - path: "scripts/controller.py"
      provides: "外部控制器：引擎检测、subprocess 启动、结果读取"
      exports: ["main"]
    - path: "temp/result.json"
      provides: "UE 脚本执行的 JSON 输出"
    - path: ".gitignore"
      provides: "从版本控制中排除 temp/"
  key_links:
    - from: "scripts/controller.py"
      to: "UnrealEditor.exe"
      via: "subprocess.run 使用 -NullRHI -unattended -ExecutePythonScript"
      pattern: "subprocess\\.run.*UnrealEditor"
    - from: "scripts/controller.py"
      to: "scripts/ue_extract.py"
      via: "命令行参数 -ExecutePythonScript=path"
      pattern: "ExecutePythonScript.*ue_extract"
    - from: "scripts/ue_extract.py"
      to: "Content/BP_FirstPersonCharacter.uasset"
      via: "EditorAssetLibrary.load_asset('/Game/...')"
      pattern: "load_asset.*Game"
    - from: "scripts/ue_extract.py"
      to: "temp/result.json"
      via: "json.dump 到 output_path"
      pattern: "json\\.dump.*output_path"
---

<objective>
构建一个 Python 控制的 UE 5.7 无头桥接工具，加载 .uasset 文件，检测是否为蓝图资产，返回结构化 JSON 输出。建立最小执行循环：外部脚本 → 启动 UE → 内嵌脚本运行 → 结果采集 → UE 退出。

目的：为所有后续阶段（节点提取、输出格式化、CLI）奠定基础。必须正确区分蓝图与非蓝图资产。
输出：2 个 Python 脚本、1 个 .uproject 文件、Content 目录含测试资产、JSON 结果文件
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/01-ue-headless-bridge/01-CONTEXT.md
@.planning/phases/01-ue-headless-bridge/01-RESEARCH.md
@E:\Develop\uasset_resolver\CLAUDE.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: 创建项目脚手架 — .uproject、Content、temp、.gitignore</name>
  <files>.gitignore, minimal.uproject, Content/, temp/</files>
  <action>
创建无头执行所需的最小 UE 项目结构：

1. **`.gitignore`** — 从版本控制中排除 `temp/` 目录。添加 `temp/` 和 `temp/**` 条目。

2. **`minimal.uproject`** — 最小 UE 项目文件（参见 RESEARCH.md 代码示例）。必须包含：
   - `"FileVersion": 3`
   - `"EngineAssociation": "5.7"`（匹配已安装的 UE 5.7）
   - `"Plugins"` 数组，两个插件均启用：
     - `{"Name": "PythonScriptPlugin", "Enabled": true}`（D-01：Python 执行需要此插件）
     - `{"Name": "EditorScriptingUtilities", "Enabled": true}`（EditorAssetLibrary 需要）
   - 空的 `Category` 和 `Description` 字符串
   - 不需要关卡 — 资产加载可在空项目中进行

3. **`Content/` 目录** — 创建空目录。然后将 `BP_FirstPersonCharacter.uasset` 从项目根目录复制到 `Content/`。虚拟路径将为 `/Game/BP_FirstPersonCharacter`。

4. **`temp/` 目录** — 创建空目录。运行时将在此写入 `result.json` 和 `ue_config.json`。

关键：UE 5.7 中两个插件的 `EnabledByDefault: false`（已从 `.uplugin` 源码验证）。若 `.uproject` 中未列出它们，`-ExecutePythonScript` 将静默失败。

**为何无需手动编辑器操作即可工作：**
- `.uproject` 中显式声明 `"Enabled": true` 会覆盖插件 `.uplugin` 的 `EnabledByDefault: false`（源码：`FProjectManager::LoadModulesForProject`）
- `-ExecutePythonScript` 参数触发回退机制：`EditorPythonExecuter.cpp:192` 调用 `ForceEnablePythonAtRuntime()`，即使插件未完全加载也会强制启用 Python
- `-unattended` 模式下 `FApp::IsUnattended()` 返回 true，编辑器不会弹出任何确认对话框（源码：`App.cpp:288`）
- 结论：整个过程零手动操作，纯命令行可完成
  </action>
  <verify>
    <automated>
      python -c "import json; d=json.load(open('minimal.uproject')); assert d['EngineAssociation']=='5.7'; plugins={p['Name']:p['Enabled'] for p in d['Plugins']}; assert plugins.get('PythonScriptPlugin')==True; assert plugins.get('EditorScriptingUtilities')==True; print('OK')"
    </automated>
  </verify>
  <done>
    - `.gitignore` 排除 `temp/`
    - `minimal.uproject` 是有效 JSON，EngineAssociation 为 "5.7"，两个插件均启用
    - `Content/BP_FirstPersonCharacter.uasset` 存在（56KB）
    - `temp/` 目录存在
  </done>
</task>

<task type="auto">
  <name>Task 2: 创建 UE 内嵌脚本 — scripts/ue_extract.py</name>
  <files>scripts/ue_extract.py</files>
  <action>
创建在 UE 内嵌 Python 解释器中运行的脚本，执行实际的资产加载和蓝图检测。

**文件**: `scripts/ue_extract.py`

**核心逻辑**:
1. 从 `sys.argv` 解析 `--output`（默认：`temp/result.json`）— 实现 D-03
2. 定义资产虚拟路径：`/Game/BP_FirstPersonCharacter`（映射到 `Content/BP_FirstPersonCharacter.uasset`）
3. 使用 `unreal.EditorAssetLibrary.load_asset(asset_path)` 加载资产
4. 通过 `isinstance` 检测类型（D-04 + D-05 可扩展性）：
   - `isinstance(asset, unreal.Blueprint)` — 主要检查。在 UE Python 中，`unreal.Blueprint` 封装了 C++ 的 `UBlueprint` 类，其生成类为 `UBlueprintGeneratedClass`。加载后的蓝图资产本身就是 `UBlueprint` 实例，等价于"包中包含 UBlueprintGeneratedClass"。
   - 同时检查 `unreal.Material`、`unreal.StaticMesh`、`unreal.SkeletalMesh` 以备未来扩展
   - 记录 `asset.get_class().get_name()` — 捕获原始 C++ 类名用于交叉引用
5. 若是蓝图，提取：`generated_class`、`parent_class`、通过 `unreal.BlueprintEditorLibrary.find_event_graph(bp)` 检查 EventGraph 是否存在
6. 使用 `json.dump(result, f, indent=2, ensure_ascii=False)` 写入 JSON 到输出路径
7. 调用 `unreal.SystemLibrary.quit_editor()`（参见 RESEARCH.md 陷阱 3）

**JSON 输出结构**（由实现者决定，参见 CONTEXT.md）：
```json
{
  "asset_path": "/Game/BP_FirstPersonCharacter",
  "asset_class": "BlueprintGeneratedClass",
  "is_blueprint": true,
  "generated_class": "...",
  "parent_class": "...",
  "has_event_graph": true,
  "event_graph_name": "...",
  "node_count": 0
}
```

**错误处理**: 若 `load_asset()` 返回 `None`，写入 `{"asset_path": "...", "error": "Asset not found or failed to load", "is_blueprint": false}` 并仍然调用 `quit_editor()`。

**重要**: 此脚本在 UE 的 Python 3.11 环境中运行。`unreal` 模块无需额外安装即可使用。请勿使用任何第三方包。
  </action>
  <verify>
    <automated>python -c "import ast; ast.parse(open('scripts/ue_extract.py').read()); print('语法 OK')"</automated>
  </verify>
  <done>
    - 脚本无语法错误
    - 包含 `unreal.EditorAssetLibrary.load_asset` 调用
    - 包含 `isinstance(asset, unreal.Blueprint)` 检查（D-04）
    - 包含 `unreal.SystemLibrary.quit_editor()` 调用
    - 从 sys.argv 解析 `--output`（D-03）
    - 写入包含 `is_blueprint` 布尔字段的 JSON（D-02）
    - 可扩展的类型检测结构（D-05）：以结构化方式检查多种资产类型
  </done>
</task>

<task type="auto">
  <name>Task 3: 创建外部控制器 — scripts/controller.py</name>
  <files>scripts/controller.py</files>
  <action>
创建管理整个 UE 启动生命周期的外部 Python 脚本。运行在用户的系统 Python（3.9+）中，而非 UE 内部。

**文件**: `scripts/controller.py`

**CLI 接口**:
```
python scripts/controller.py [选项]
  --uasset PATH     .uasset 文件路径（默认：BP_FirstPersonCharacter.uasset）
  --ue-path PATH    覆盖引擎路径（D-08 回退）
  --output PATH     输出 JSON 路径（默认：temp/result.json）
  --timeout SECS    超时秒数（默认：120）
```

**核心逻辑**（顺序步骤）：

1. **引擎检测**（D-08）：
   - 首先检查 `temp/ue_config.json` 是否有缓存路径（D-09：若已缓存则跳过检测）
   - 若未缓存，扫描 Windows 注册表：`HKLM\SOFTWARE\EpicGames\Unreal Engine` → 遍历版本子键 → 读取 `InstalledDirectory` 值 → 构造 `UnrealEditor.exe` 路径
   - 回退到已知路径：`D:\Program Files\Epic Games\Engine\UE_5.7`、`C:\Program Files\Epic Games\UE_5.7`
   - 若全部失败且未提供 `--ue-path`：打印错误并以退出码 1 退出
   - 首次成功检测后：写入 `temp/ue_config.json`，格式为 `{"engine_path": "..."}`（D-09）

2. **资产准备**:
   - 解析输入 `.uasset` 路径（默认：项目根目录 `BP_FirstPersonCharacter.uasset`）
   - 将文件复制到 `Content/` 目录（若存在则覆盖）
   - 派生虚拟路径：去除 `.uasset` 扩展名，反斜杠替换为正斜杠，前缀 `/Game/`

3. **通过 subprocess 启动 UE**（PARSE-01）：
   - 构建命令：
     ```
     "{ue_exe}" "{project_root}/minimal.uproject"
       -NullRHI -unattended -NoLoadingScreen -NoScreenMessages
       -ExecutePythonScript="{project_root}/scripts/ue_extract.py --output {abs_output_path}"
     ```
   - 注意：`--output` 参数必须**包含在** `-ExecutePythonScript=` 的值内部，作为单独参数传递给 UE 编辑器会导致丢失。
   - 使用 `subprocess.run()` 配合 `timeout=120`（D-06：固定超时）
   - 捕获 stdout/stderr 用于调试（不用于结果提取）
   - 若 `subprocess.TimeoutExpired`：调用 `proc.kill()`，报告超时错误

4. **结果读取**（D-02）：
   - subprocess 退出后，从输出路径读取 `result.json`
   - 解析 JSON 并打印人类可读摘要
   - 若文件缺失：报告 UE 脚本未能写入输出

5. **退出**: 成功返回退出码 0，任何失败返回 1

**Windows 路径处理**: 对传给 UE 的所有路径使用 `os.path.abspath()`。UE 命令行中尽量使用正斜杠以避免引号转义问题（参见 RESEARCH.md 陷阱 4）。

**可扩展性提示**（D-05）：将资产准备和结果读取设计为独立函数 — 未来资产类型可能需要不同的准备步骤。
  </action>
  <verify>
    <automated>python -c "import ast; ast.parse(open('scripts/controller.py').read()); print('语法 OK')"</automated>
  </verify>
  <done>
    - 脚本无语法错误
    - 实现 `argparse` CLI，含 `--uasset`、`--ue-path`、`--output`、`--timeout`
    - 引擎检测顺序：缓存 → 注册表 → 已知路径 → --ue-path 回退（D-08, D-09）
    - 首次成功后缓存引擎路径到 `temp/ue_config.json`（D-09）
    - 复制 .uasset 到 `Content/` 并派生虚拟路径
    - 以 `-NullRHI -unattended -ExecutePythonScript` 参数启动 UE（PARSE-01）
    - 使用 `subprocess.run` 配合 timeout=120，超时则 kill（D-06）
    - UE 退出后读取并解析结果 JSON（D-02）
    - 返回适当的退出码
  </done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <name>Task 4: 端到端冒烟测试 — 启动 UE，验证蓝图检测</name>
  <action>
运行完整流水线并验证所有三项成功标准。

**运行命令**:
```
python scripts/controller.py
```

预期行为：
1. 检测 UE 5.7 引擎路径（或使用缓存的 `temp/ue_config.json`）
2. 复制 `BP_FirstPersonCharacter.uasset` 到 `Content/`
3. 以 `-NullRHI -unattended` 参数启动 `UnrealEditor.exe`
4. 在 UE 内执行 `scripts/ue_extract.py`
5. UE 写入 `temp/result.json` 并调用 `quit_editor()`
6. 控制器读取结果并打印摘要

**验证步骤**（命令完成后运行）：

1. 检查 `temp/result.json` 存在且包含有效 JSON：
   ```
   python -c "import json; print(json.dumps(json.load(open('temp/result.json')), indent=2))"
   ```

2. 验证 `BP_FirstPersonCharacter.uasset` 的 `is_blueprint` 为 `true`

3. 验证无 UE 编辑器窗口残留（在任务管理器中检查 `UnrealEditor.exe` 进程）

4. 若任何步骤失败：
   - 检查 `temp/` 目录中是否有任何日志文件
   - 尝试手动运行 UE 命令以查看 stderr 输出
   - 验证 `minimal.uproject` 中两个插件已启用
   - 验证 `Content/BP_FirstPersonCharacter.uasset` 存在

**恢复信号**: 若所有检查通过，输入 "approved"；否则描述观察到的失败。
  </action>
  <verify>
    <human-check>
      1. `temp/result.json` 存在且包含 `"is_blueprint": true`
      2. `asset_class` 字段显示 "BlueprintGeneratedClass" 或类似值
      3. 完成后无 `UnrealEditor.exe` 进程残留
      4. 控制器退出码为 0
    </human-check>
  </verify>
  <done>
    - UE 以正确参数无头启动（PARSE-01）
    - `temp/result.json` 报告 `BP_FirstPersonCharacter` 为蓝图（PARSE-02）
    - UE 进程在超时内干净退出（无残留）
    - 引擎路径已缓存到 `temp/ue_config.json`
  </done>
</task>

</tasks>

<threat_model>
## 信任边界

| 边界 | 描述 |
|------|------|
| controller.py → UnrealEditor.exe | 外部进程以命令行参数启动 UE 编辑器 |
| controller.py → .uasset 文件 | 用户提供的文件路径作为输入 |
| ue_extract.py → temp/result.json | UE 脚本写入项目 temp 目录 |

## STRIDE 威胁登记

| 威胁 ID | 类别 | 组件 | 处置 | 缓解计划 |
|---------|------|------|------|----------|
| T-01-01 | 篡改 | .uasset 文件输入 | 缓解 | 控制器在复制到 Content/ 前验证文件存在且有 `.uasset` 扩展名 |
| T-01-02 | 篡改 | --output 路径参数 | 缓解 | 控制器限制输出路径到项目 `temp/` 目录；拒绝含 `..` 的路径穿越 |
| T-01-03 | 拒绝服务 | UE subprocess 挂起 | 缓解 | 固定 120 秒超时配合 `subprocess.kill()`（D-06）；UE 脚本中 `quit_editor()` 作为安全措施 |
| T-01-04 | 篡改 | 引擎路径检测 | 缓解 | 注册表读取为只读；已知路径通过 `os.path.exists` 验证 UnrealEditor.exe 后再使用 |
| T-01-05 | 欺骗 | UE 进程身份 | 接受 | 工具本地运行；无网络或认证边界。低价值目标。 |
| T-01-SC | 篡改 | npm/pip/cargo 安装 | N/A | 无外部包安装 — 全部 Python 标准库 + UE 内置模块 |
</threat_model>

<verification>
## Phase 级别验证

1. **PARSE-01**: `python scripts/controller.py` 以 `-NullRHI -unattended` 启动 UE 并执行 `scripts/ue_extract.py`
   - 验证方式：subprocess 退出码 0，无残留 UE 进程，生成 `temp/result.json`

2. **PARSE-02**: `BP_FirstPersonCharacter.uasset` 正确识别为蓝图
   - 验证方式：`temp/result.json` 包含 `"is_blueprint": true`

3. **干净退出**: 完成后无残留 `UnrealEditor.exe` 进程
   - 验证方式：任务管理器检查或 `tasklist | findstr UnrealEditor` 返回空

4. **引擎路径缓存**: 首次运行后 `temp/ue_config.json` 存在
   - 验证方式：文件包含有效 JSON，`"engine_path"` 键指向 UnrealEditor.exe
</verification>

<success_criteria>
## 可度量的完成标准

- [ ] `minimal.uproject` 是有效 JSON，两个插件均启用
- [ ] `Content/BP_FirstPersonCharacter.uasset` 存在
- [ ] `scripts/ue_extract.py` 语法有效，使用 EditorAssetLibrary.load_asset + isinstance + quit_editor
- [ ] `scripts/controller.py` 语法有效，实现引擎检测（注册表 + 回退）、subprocess 超时、结果读取
- [ ] 首次成功运行后创建 `temp/ue_config.json`
- [ ] 为测试资产创建 `temp/result.json`，含 `is_blueprint: true`
- [ ] 执行后无 UE 编辑器窗口残留
- [ ] `.gitignore` 排除 `temp/`
</success_criteria>

<output>
完成后创建 `.planning/phases/01-ue-headless-bridge/01-01-SUMMARY.md`
</output>
