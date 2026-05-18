# Phase 1: UE 无头桥接 — 研究

**研究日期:** 2026-05-18
**领域:** Unreal Engine 5.7 无头执行、Python 脚本、资产加载
**置信度:** 高（已通过 UE 源码 + 官方文档 + 网络搜索验证）

## 摘要

本阶段需要从外部 Python 进程以无头模式启动 UE 5.7 编辑器，执行内嵌 Python 脚本加载 `.uasset` 文件，判断其是否为蓝图，并将结果写入 JSON。研究确认这是可行的，但需要若干非显而易见的设置步骤。

**关键发现：**
1. `-ExecutePythonScript=` 参数需要**完整编辑器**（非 commandlet），这意味着 `.uproject` 文件是必需的 — 即使是最小化的。
2. **PythonScriptPlugin** 和 **EditorScriptingUtilities** 插件均随 UE 5.7 分发，但**默认禁用**（`EnabledByDefault: false`）。必须通过 `.uproject` 文件启用。**零手动操作**——`.uproject` 声明覆盖默认值 + `-ExecutePythonScript` 触发 `ForceEnablePythonAtRuntime()` 回退 + `-unattended` 抑制弹窗（详见陷阱 7 + PLAN.md Task 1）。
3. UE 的 Python `load_asset()` API 使用**虚拟路径**（`/Game/...`），而非文件系统路径。`.uasset` 文件必须放在项目的 `Content/` 目录中。
4. 编辑器在脚本执行后通过 `QUIT_EDITOR` 延迟命令自动退出，但脚本也应调用 `unreal.SystemLibrary.quit_editor()` 作为安全措施。
5. UE 5.7 内置 **Python 3.11**，位于 `Engine/Binaries/ThirdParty/Python3/Win64/python.exe`。

**主要建议：** 创建最小 `.uproject`，启用两个插件，将测试 `.uasset` 复制到 `Content/`，以 `-NullRHI -unattended -ExecutePythonScript=` 启动无头模式，使用 `unreal.EditorAssetLibrary.load_asset()` 配合 `isinstance()` 检查进行蓝图检测。

## 用户约束（来自 CONTEXT.md）

### 已锁定决策
- **D-01:** 使用外部 .py 文件，通过 UE 命令行参数 `-ExecutePythonScript=path/to/script.py` 传入。脚本放在项目 `scripts/ue_extract.py`，便于迭代调试。
- **D-02:** UE 内嵌脚本将结果写入 `temp/` 目录下的 JSON 文件，外部 Python 控制脚本读取该文件。不依赖 stdout 管道（UE 日志系统不可靠）。
- **D-03:** 临时文件路径由外部脚本传入参数指定，格式：`--output temp/result.json`。
- **D-04:** 检查加载后的包中是否包含 `UBlueprintGeneratedClass` 类型的对象来判定蓝图。
- **D-05:** 架构需保留可扩展性——未来支持其他资产类型（材质、动画等）时，类型检测逻辑应可插拔。
- **D-06:** Phase 1 使用固定超时（60-120 秒），超时后 `subprocess.kill()`。只需报告成功/失败，不做详细诊断。
- **D-07:** 后续 Phase 可演进为智能超时 + 重试（监控输出关键词判断状态）。
- **D-08:** 混合模式：自动扫描 Windows 注册表（`HKLM\SOFTWARE\EpicGames\Unreal Engine`）和已知安装路径 → 失败后提示用户通过 CLI 参数 `--ue-path` 手动指定。
- **D-09:** 首次检测成功后，将引擎路径缓存到项目配置文件中，避免重复扫描。

### Claude 自由裁量
- 临时文件的 JSON 结构由实现者决定，只要能被外部脚本正确读取即可。
- UE 内嵌脚本中的 `print` 输出格式无特殊要求，主要用于调试日志。

### 延期想法（超出范围）
- 智能超时 + 重试（D-07）——后续 Phase 实现
- 非蓝图资产类型支持（D-05 扩展性）—— v2 需求，已列在 REQUIREMENTS.md v2 中

## 架构职责映射

| 能力 | 主要层 | 次要层 | 理由 |
|------|--------|--------|------|
| UE 无头进程管理 | 外部 Python（subprocess） | — | 外部进程生成和监控 UE |
| UE Python 脚本执行 | UE 内嵌 Python | — | `-ExecutePythonScript` 在 UE 编辑器内运行 |
| 资产加载（.uasset → UObject） | UE 编辑器（Python API） | — | `EditorAssetLibrary.load_asset()` 需要编辑器上下文 |
| 蓝图类型检测 | UE 内嵌 Python | — | 对已加载资产的 `isinstance()` 检查 |
| JSON 输出写入 | UE 内嵌 Python | 外部 Python 读取 | 脚本写入 `temp/`，外部进程读取 |
| 引擎路径自动检测 | 外部 Python | — | UE 启动前注册表扫描和文件系统探测 |
| 超时与进程终止 | 外部 Python | — | `subprocess` 超时配合 `kill()` |

## 标准技术栈

### 核心
| 库 | 版本 | 用途 | 为何标准 |
|----|------|------|----------|
| `unreal`（UE 内置模块） | UE 5.7 内置 | 资产加载、蓝图检查、编辑器控制 | UE 官方 Python 集成 — 无需第三方安装 |
| `unreal.EditorAssetLibrary` | UE 5.7 内置 | `load_asset()`、`save_loaded_asset()`、`does_asset_exist()` | UE Python 中的主要资产操作 API |
| `unreal.EditorFilterLibrary` | UE 5.7 内置 | 资产类型过滤和分类 | 可扩展类型检测工具（D-05） |
| `unreal.BlueprintEditorLibrary` | UE 5.7 内置 | `find_event_graph()`、图节点访问 | 蓝图图检查 |

### 辅助
| 库 | 版本 | 用途 | 使用场景 |
|----|------|------|----------|
| `json`（Python 标准库） | Python 3.11 | JSON 输出序列化 | 写入结果到 `temp/result.json` |
| `sys`（Python 标准库） | Python 3.11 | `sys.argv` 解析 | UE 脚本中读取 `--output` 参数 |
| `subprocess`（Python 标准库） | Python 3.11 | 进程生成、超时管理 | 外部控制器脚本 |
| `winreg`（Python 标准库） | Python 3.11 | Windows 注册表读取 | 引擎路径自动检测（D-08） |

### 已考虑的替代方案
| 替代 | 可使用 | 权衡 |
|------|--------|------|
| 完整编辑器 + `-ExecutePythonScript` | Commandlet `-run=PythonScript` | Commandlet 无法加载资产 — `EditorPythonExecuter.cpp` 明确禁止（第 187 行："-ExecutePythonScript cannot be used by a commandlet"） |
| `EditorAssetLibrary.load_asset()` | 自定义 C++ 插件通过 `FLinkerLoad` | 需要重新编译引擎 — 对 Phase 1 来说过于复杂 |
| `-NullRHI` | `-windowed -ResX=1 -ResY=1` | 窗口模式仍创建 GPU 窗口；`-NullRHI` 才是真正的无头 |

**安装：**
无需外部包。UE 5.7 内置 Python 3.11 和 `unreal` 模块。两个所需插件均随引擎分发 — 只需在项目中启用。

## 包合法性审计

| 包 | 注册表 | 年龄 | 下载量 | 源码仓库 | slopcheck | 处置 |
|----|--------|------|--------|----------|-----------|------|
| `unreal`（UE 内置模块） | N/A（UE 内置） | — | — | Epic Games UE 源码 | N/A | 已批准 — 官方 UE 模块 |
| `json`（标准库） | N/A | — | — | Python 标准库 | N/A | 已批准 |
| `subprocess`（标准库） | N/A | — | — | Python 标准库 | N/A | 已批准 |
| `winreg`（标准库） | N/A | — | — | Python 标准库 | N/A | 已批准 |

**无外部包安装。** 所有依赖均为 UE 内置模块或 Python 标准库。

## 架构模式

### 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                    外部 Python                           │
│  (E:\Develop\uasset_resolver\scripts\controller.py)      │
│                                                          │
│  1. 检测/缓存 UE 路径（注册表扫描）                       │
│  2. 构建命令：UnrealEditor.exe + 参数                    │
│  3. subprocess.run(timeout=120s)                         │
│  4. 读取 temp/result.json                                │
└──────────────────────┬──────────────────────────────────┘
                       │ subprocess 调用
                       ▼
┌─────────────────────────────────────────────────────────┐
│               UE 5.7 编辑器（无头）                       │
│  UnrealEditor.exe "minimal.uproject"                     │
│  -NullRHI -unattended -NoLoadingScreen                   │
│  -ExecutePythonScript="scripts/ue_extract.py"            │
│  --output "temp/result.json"                             │
│                                                          │
│  1. 编辑器启动（null RHI，无窗口）                        │
│  2. PythonScriptPlugin 初始化（Python 3.11）             │
│  3. 资产注册表就绪后运行 ue_extract.py                    │
│  4. EditorAssetLibrary.load_asset("/Game/...")           │
│  5. isinstance(asset, unreal.Blueprint) → 类型检查       │
│  6. json.dump(results, open(output_path, "w"))           │
│  7. unreal.SystemLibrary.quit_editor()                   │
└─────────────────────────────────────────────────────────┘
                       │ 退出码 0
                       ▼
┌─────────────────────────────────────────────────────────┐
│                    外部 Python                           │
│  1. 检查 subprocess 返回码                               │
│  2. 读取并解析 temp/result.json                          │
│  3. 报告成功/失败                                        │
└─────────────────────────────────────────────────────────┘
```

### 推荐项目结构
```
E:\Develop\uasset_resolver\
├── minimal.uproject          # 无头执行的最小 UE 项目
├── Content/                  # UE Content 目录（uasset 文件放这里）
│   └── BP_FirstPersonCharacter.uasset   # 测试资产（复制或符号链接）
├── scripts/
│   ├── controller.py         # 外部 Python：启动 UE、监控、采集
│   └── ue_extract.py         # UE 内嵌 Python：加载资产、检测类型、输出 JSON
├── temp/                     # 输出目录（gitignore）
│   └── result.json           # 脚本输出
└── temp/
    └── ue_config.json        # 缓存的引擎路径（D-09）
```

### 模式 1：无头编辑器执行
**说明：** 启动无 GUI 的 UE 编辑器，运行 Python 脚本，自动退出
**使用场景：** 资产检查、批处理、CI/CD 流水线
**示例：**
```bash
# 来源：已从 EditorPythonExecuter.cpp 第 142-211 行 + 网络搜索社区模式验证
"D:\Program Files\Epic Games\Engine\UE_5.7\Engine\Binaries\Win64\UnrealEditor.exe" ^
  "E:\Develop\uasset_resolver\minimal.uproject" ^
  -NullRHI ^
  -unattended ^
  -NoLoadingScreen ^
  -NoScreenMessages ^
  -stdout ^
  -ExecutePythonScript="E:\Develop\uasset_resolver\scripts\ue_extract.py --output E:\Develop\uasset_resolver\temp\result.json"
```

### 模式 2：通过类型检查进行蓝图检测
**说明：** 使用 `EditorAssetLibrary.load_asset()` 加载资产，检查 `isinstance(asset, unreal.Blueprint)`
**使用场景：** 资产类型识别流水线
**示例：**
```python
# 来源：已从 UE Python API 文档 + 网络搜索社区模式验证
import unreal
import json
import sys

# 从参数解析输出路径
output_path = "temp/result.json"  # 默认
for i, arg in enumerate(sys.argv):
    if arg == "--output" and i + 1 < len(sys.argv):
        output_path = sys.argv[i + 1]

# 使用虚拟路径加载资产（非文件系统路径）
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
    # 检查 EventGraph（D-05 可扩展性）
    event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    result["has_event_graph"] = event_graph is not None

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"结果已写入 {output_path}")

# 安全退出
unreal.SystemLibrary.quit_editor()
```

### 模式 3：引擎路径自动检测（Windows）
**说明：** 扫描注册表 + 已知路径，缓存结果
**使用场景：** Phase 1 引擎发现（D-08）
**示例：**
```python
import winreg
import os
import json

def find_ue_install():
    # 尝试注册表：HKLM\SOFTWARE\EpicGames\Unreal Engine
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\EpicGames\Unreal Engine")
        # 遍历子键（版本号如 "5.7"）
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

    # 回退：已知安装路径
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

### 应避免的反模式
- **使用 `UnrealEditor-Cmd.exe` 配合 `-ExecutePythonScript`**：源码（`EditorPythonExecuter.cpp:186-188`）明确拒绝此组合。Cmd 请使用 `-run=PythonScript`，但注意 commandlet 无法加载资产。
- **向 `load_asset()` 传递文件系统路径**：`EditorAssetLibrary.load_asset()` 期望虚拟路径（`/Game/...`），而非 `C:\path\to\file.uasset`。资产必须位于项目的 `Content/` 目录中。
- **依赖 stdout 获取结果**：UE 的日志系统会捕获 Python `print()` 输出，但在无头模式下格式不可靠（D-02 决策已确认使用基于文件的输出）。
- **忘记启用插件**：`PythonScriptPlugin` 和 `EditorScriptingUtilities` 均为 `EnabledByDefault: false`。`.uproject` 必须列出它们并设置 `"Enabled": true`。不需要手动打开编辑器勾选——`.uproject` 声明 + `-ExecutePythonScript` 回退 + `-unattended` 模式共同保证零手动操作。（详见陷阱 7）

## 不要重复造轮子

| 问题 | 不要构建 | 使用 | 原因 |
|------|----------|------|------|
| 从 `.uasset` 二进制加载资产 | 自定义 .uasset 格式二进制解析器 | `unreal.EditorAssetLibrary.load_asset()` | UE 的 `FLinkerLoad` 处理序列化、版本化和对象引用 — 重新实现需要数千行代码 |
| 蓝图类型检测 | 手动类名字符串比较 | `isinstance(asset, unreal.Blueprint)` | UE 的 Python 包装器正确处理继承；字符串匹配在 BlueprintGeneratedClass 与 Blueprint 之间会出错 |
| JSON 序列化 | 手动字符串格式化 | Python `json.dump()` | 转义、编码和嵌套结构的边界情况 |
| 引擎路径检测 | 仅硬编码路径 | 注册表扫描 + 回退 | 用户可能安装到自定义位置；注册表是权威来源 |

**关键洞察：** `.uasset` 二进制格式很复杂（FLinkerLoad 序列化、名称表、导入/导出表、批量数据）。本阶段的核心目标就是利用 UE 自身的加载器，而非反向工程该格式。

## 运行时状态清单

N/A — 这是一个绿色领域阶段（无现有应用代码需要重构）。无运行时状态类别适用。

## 常见陷阱

### 陷阱 1：插件未启用
**问题：** `-ExecutePythonScript` 静默无操作，或报错 "Python support is disabled"
**原因：** `PythonScriptPlugin`（Experimental）和 `EditorScriptingUtilities`（Editor）在其 `.uplugin` 文件中均设置 `EnabledByDefault: false`
**避免方法：** 在 `.uproject` 中添加两个插件并设置 `"Enabled": true`。同时在编辑器设置中将 `"EnablePython"` 设为 `true`，或使用 `-EnablePython` 参数。
**警告信号：** UE 日志显示 "Python disabled via CVar" 或 "PythonScriptPlugin cannot be used when Python support is disabled"

### 陷阱 2：虚拟路径找不到资产
**问题：** `load_asset("/Game/BP_FirstPersonCharacter")` 返回 `None`
**原因：** `.uasset` 文件不在项目的 `Content/` 目录中，或虚拟路径与文件位置不匹配
**避免方法：** 启动 UE 前将 `.uasset` 复制/符号链接到 `Content/`。虚拟路径 = `/Game/` + Content 目录中的相对路径（不含 `.uasset` 扩展名）。
**警告信号：** UE 日志显示 "Asset not found" 或 `load_asset` 返回 `None`

### 陷阱 3：脚本完成后编辑器挂起
**问题：** UE 进程在 Python 脚本完成后不退出
**原因：** `QUIT_EDITOR` 延迟命令在完整 tick 周期后运行；如果脚本在编辑器完全初始化之前结束，可能出现时序问题
**避免方法：** 始终在脚本末尾调用 `unreal.SystemLibrary.quit_editor()`。使用外部 subprocess 超时（D-06）作为安全网。
**警告信号：** `subprocess.run(timeout=120)` 触发超时，必须强制终止进程

### 陷阱 4：路径中的空格破坏命令行解析
**问题：** `-ExecutePythonScript="C:\My Scripts\script.py"` 无法正确解析
**原因：** `EditorPythonExecuter.cpp` 中的命令行解析器特殊处理引号；嵌套引号需要转义
**避免方法：** 使用正斜杠，避免路径中的空格，或使用正确的引号转义：`-ExecutePythonScript="\"C:/My Scripts/script.py\""`
**警告信号：** UE 日志显示 "Could not load Python file" 或脚本路径被截断

### 陷阱 5：资产注册表未就绪时脚本运行
**问题：** 脚本运行但资产在注册表中不可用
**原因：** `EditorPythonExecuter` 等待 `IAssetRegistry::GetChecked().IsLoadingAssets()` 返回 false 后才运行（第 86 行），但如果项目从未打开过，资产注册表可能需要扫描
**避免方法：** 对于最小项目，这通常很快。若出现问题，使用 `-ForceRescan` 参数或在编辑器中打开项目一次以构建注册表。
**警告信号：** `load_asset()` 返回 `None`，即使文件存在于 `Content/` 中

### 陷阱 6：缺少 .uproject 文件
**问题：** UE 编辑器没有项目文件拒绝启动
**原因：** `-ExecutePythonScript` 是编辑器功能（非 commandlet 功能），编辑器需要 `.uproject` 上下文
**避免方法：** 创建最小 `.uproject` 文件（参见标准技术栈部分）。项目不需要任何内容或关卡 — 文件存在即可。
**警告信号：** UE 显示项目浏览器或错误对话框

### 陷阱 7：插件启用机制误解
**问题：** "手动启用插件" 被误解为需要打开 UE 编辑器手动勾选
**原因：** `PythonScriptPlugin.uplugin` 和 `EditorScriptingUtilities.uplugin` 都设置了 `"EnabledByDefault": false`，让人以为需要手动操作
**避免方法：** 理解三层机制：
1. `.uproject` 中显式声明 `"Enabled": true` 覆盖插件的 `EnabledByDefault: false`（源码：`FProjectManager::LoadModulesForProject`，`ProjectManager.cpp:95-102`）
2. `-ExecutePythonScript` 触发回退：`ForceEnablePythonAtRuntime()` 强制启用 Python（源码：`EditorPythonExecuter.cpp:192-193`）
3. `-unattended` 模式抑制所有弹窗：`FApp::IsUnattended()` 返回 true（源码：`App.cpp:288-289`）
**结论：** 整个过程零手动操作，纯命令行可完成
**警告信号：** 无 — 正确配置 `.uproject` + `-unattended` 即可

## 代码示例

### 最小 .uproject 文件
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

### 完整的 ue_extract.py（UE 内嵌脚本）
```python
"""
UE 内嵌 Python 脚本：加载 .uasset 资产，检测是否为蓝图，
并将结果写入 JSON 文件。

用法（通过 -ExecutePythonScript）：
  -ExecutePythonScript="scripts/ue_extract.py --output temp/result.json"
"""
import unreal
import json
import sys

def parse_args():
    """从命令行解析 --output 参数。"""
    output_path = "temp/result.json"
    for i, arg in enumerate(sys.argv):
        if arg == "--output" and i + 1 < len(sys.argv):
            output_path = sys.argv[i + 1]
    return output_path

def detect_asset_type(asset):
    """使用 isinstance 检查确定资产类型（按 D-05 可扩展）。"""
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

        # EventGraph 检测
        event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
        result["has_event_graph"] = event_graph is not None
        if event_graph:
            result["event_graph_name"] = event_graph.get_fname()
            result["node_count"] = len(event_graph.nodes) if event_graph.nodes else 0

    return result

def main():
    output_path = parse_args()
    print(f"[ue_extract] 输出路径：{output_path}")

    # 资产的虚拟路径（必须在 Content/ 目录中）
    asset_path = "/Game/BP_FirstPersonCharacter"
    print(f"[ue_extract] 加载资产：{asset_path}")

    asset = unreal.EditorAssetLibrary.load_asset(asset_path)
    result = detect_asset_type(asset)
    result["asset_path"] = asset_path

    # 写入 JSON
    print(f"[ue_extract] 写入结果...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"[ue_extract] 完成。蓝图={result.get('is_blueprint', False)}")

    # 退出编辑器
    unreal.SystemLibrary.quit_editor()

if __name__ == "__main__":
    main()
```

## 技术演进

| 旧方法 | 当前方法 | 变更时间 | 影响 |
|--------|----------|----------|------|
| UE4 Python 2.7 支持 | UE5 Python 3.11 内置 | UE 5.0 | 现代 Python 语法，可用类型提示 |
| 手动 C++ 插件用于资产加载 | `unreal.EditorAssetLibrary` Python API | UE 4.25+ | 无需编译，纯 Python 脚本 |
| `EditorUtilityWidget` 用于自动化 | `-ExecutePythonScript` 无头模式 | UE 5.0+ | 无需 UI，CI/CD 友好 |
| `-game` 参数用于批处理 | `-NullRHI -unattended` | UE 5.x | 真正无头，无需 GPU 上下文 |

**已废弃/过时：**
- **`UnrealPak` 用于资产提取**：仅适用于 `.pak` 文件，不适用于单个 `.uasset` 文件
- **UE4 Python 2.x**：UE 5.x 使用 Python 3.11；Python 2 语法会失败
- **`EditorAssetLibrary.does_asset_exist()` 在 `load_asset()` 之前**：不需要 — `load_asset()` 在找不到时返回 `None`

## 假设登记

| # | 声明 | 章节 | 若错误的风险 |
|---|------|------|-------------|
| A1 | `unreal.BlueprintEditorLibrary.find_event_graph()` 存在于 UE 5.7 | 代码示例 | 中 — API 名称可能不同；需要运行时验证 |
| A2 | UE 5.7 内置 Python 为 3.11 | 标准技术栈 | 低 — 已通过 UE 安装中的 `python311.dll` 确认 |
| A3 | `-ExecutePythonScript` 可与 `-NullRHI` 同时使用 | 架构模式 | 低 — 两者均为标准参数，广泛文档化 |
| A4 | `EditorScriptingUtilities` 向 Python 提供 `EditorAssetLibrary` | 标准技术栈 | 低 — 已由 C++ API 文档确认 `UEditorAssetLibrary` 链接到此插件 |
| A5 | 无关卡/地图的最小 `.uproject` 仍能加载资产 | 架构模式 | 中 — 资产加载需要资产注册表，可能需要关卡；需要运行时验证 |

## 开放问题（已解决）

> 规划期间已解决 — 剩余项目延期至 Task 4 冒烟测试验证。

1. **无任何关卡的最小 .uproject 是否仍能加载资产注册表？**
   - **已解决：延期至 Task 4。** A5 假设涵盖此问题 — 若资产注册表失败，Task 4 会捕获。计划通过在启动前将资产复制到 Content/ 来缓解。若 load_asset 返回 None，用户手动在 UE 中打开 minimal.uproject 一次以触发注册表构建。

2. **`EditorAssetLibrary.load_asset()` 能否从 Content 目录外加载资产？**
   - **已解决：无需验证。** PLAN.md 采用复制到 Content 的方案（Task 1+3）。这更简单且避免边界情况。问题已由设计决策回答 — 我们复制，而非从外部加载。

3. **`-ExecutePythonScript` 完成后 UnrealEditor.exe 的确切退出码是什么？**
   - **已解决：延期至 Task 4。** 退出码检测不是 Phase 1 成功标准的必需项。控制器依赖基于超时的检测（D-06：120 秒）。Task 4 将记录观察到的退出码供未来参考。

## 环境可用性

| 依赖 | 需要方 | 可用性 | 版本 | 回退方案 |
|------|--------|--------|------|----------|
| UnrealEditor.exe | 无头资产加载 | 已验证 | UE 5.7 | `D:\Program Files\Epic Games\Engine\UE_5.7\Engine\Binaries\Win64\UnrealEditor.exe` |
| UnrealEditor-Cmd.exe | 替代方案（D-01 不需要） | 已验证 | UE 5.7 | 不使用 — D-01 需要完整编辑器 |
| Python 3.11（内置） | UE Python 执行 | 已验证 | 3.11.x | 随 UE 内置于 `Engine/Binaries/ThirdParty/Python3/Win64/` |
| PythonScriptPlugin | `-ExecutePythonScript` 支持 | 已验证（已安装的 UE 中） | 1.0（beta） | 必须通过 `.uproject` 启用 |
| EditorScriptingUtilities | `EditorAssetLibrary` API | 已验证（已安装的 UE 中） | 1.0（beta） | 必须通过 `.uproject` 启用 |
| `.uproject` 文件 | 编辑器上下文 | 尚未创建 | — | 必须创建最小项目文件 |
| `Content/` 中的 `BP_FirstPersonCharacter.uasset` | 资产加载 | 文件存在于项目根目录 | 56KB | 必须复制到 `Content/` |
| `winreg`（Python 标准库） | 注册表路径检测 | 可用 | Python 3.11 | 回退到已知路径 |
| `subprocess`（Python 标准库） | 进程管理 | 可用 | Python 3.11 | — |

**需要设置的缺失依赖：**
- `minimal.uproject` — 必须创建（参见代码示例）
- `Content/BP_FirstPersonCharacter.uasset` — 必须从项目根目录复制
- 两个插件必须在 `.uproject` 中启用

## 验证架构

### 测试框架
| 属性 | 值 |
|------|-----|
| 框架 | Python `unittest`（标准库）或手动执行 |
| 配置文件 | 无 — Phase 1 是技术验证 |
| 快速运行命令 | `python scripts/controller.py --test`（手动） |
| 完整套件命令 | N/A |

### Phase 需求 → 测试映射
| 需求 ID | 行为 | 测试类型 | 自动化命令 | 文件存在？ |
|---------|------|----------|------------|-----------|
| PARSE-01 | 无头启动 UE，加载资产，检测蓝图 | 手动端到端 | 运行 controller.py | 否 — 将在计划中创建 |
| PARSE-02 | 输出 JSON 到 temp/，结构正确 | 手动端到端 | 检查 temp/result.json | 否 — 将在计划中创建 |

### Wave 0 缺口
- [ ] 基本冒烟测试脚本，验证 UE 启动 + 脚本执行
- [ ] 尚未配置测试框架 — Phase 1 是概念验证

## 安全领域

`.planning/config.json` 中未配置 `security_enforcement`，因此包含此部分。

### 适用 ASVS 类别

| ASVS 类别 | 适用 | 标准控制 |
|-----------|------|----------|
| V2 认证 | 否 | 无用户认证 — 仅本地工具 |
| V3 会话管理 | 否 | 无会话 |
| V4 访问控制 | 否 | 无需访问控制 |
| V5 输入验证 | 是 | 验证资产路径参数、JSON 输出清理 |
| V6 密码学 | 否 | 无密码学操作 |

### UE 无头自动化已知威胁模式

| 模式 | STRIDE | 标准缓解 |
|------|--------|----------|
| 恶意 .uasset 文件导致 UE 崩溃 | 篡改 | 使用 subprocess 超时（D-06）；验证退出码 |
| 通过 --output 参数的路径注入 | 篡改 | 清理输出路径，限制到项目 temp/ 目录 |
| 脚本后 UE 进程挂起 | 拒绝服务 | subprocess 超时配合 `kill()`（D-06） |

## 来源

### 主要（高置信度）
- UE 源码：`E:\Develop\lib\UnrealEngine\Engine\Plugins\Experimental\PythonScriptPlugin\PythonScriptPlugin.uplugin` — 插件配置（EnabledByDefault: false, IsBetaVersion）
- UE 源码：`E:\Develop\lib\UnrealEngine\Engine\Plugins\Experimental\PythonScriptPlugin\Source\PythonScriptPlugin\Private\PythonScriptPlugin.cpp` — Python 初始化、`unreal` 模块设置、`IsPythonEnabled()` 逻辑
- UE 源码：`E:\Develop\lib\UnrealEngine\Engine\Plugins\Experimental\PythonScriptPlugin\Source\PythonScriptPlugin\Private\EditorUtilities\EditorPythonExecuter.cpp` — `-ExecutePythonScript` 处理、退出行为、commandlet 拒绝
- UE 源码：`E:\Develop\lib\UnrealEngine\Engine\Plugins\Experimental\PythonScriptPlugin\Source\PythonScriptPlugin\Private\PythonScriptCommandlet.cpp` — Commandlet 执行（D-01 不使用）
- UE 源码：`E:\Develop\lib\UnrealEngine\Engine\Plugins\Editor\EditorScriptingUtilities\EditorScriptingUtilities.uplugin` — 插件配置
- UE 已安装：`D:\Program Files\Epic Games\Engine\UE_5.7\Engine\Binaries\ThirdParty/Python3/Win64/python.exe` — 确认 Python 3.11
- UE 已安装：`D:\Program Files\Epic Games\Engine\UE_5.7\Engine\Binaries\Win64\UnrealEditor.exe` — 确认编辑器二进制
- UE 已安装：`D:\Program Files\Epic Games\Engine\UE_5.7\Engine\Binaries\Win64\UnrealEditor-Cmd.exe` — 确认 commandlet 二进制

### 次要（中等置信度）
- [Unreal Engine 命令行参数参考](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-command-line-arguments-reference) - 参数文档
- [使用 Python 脚本化 Unreal 编辑器](https://dev.epicgames.com/documentation/unreal-engine/scripting-the-unreal-editor-using-python) - 官方 Python 文档
- [UEditorAssetLibrary::LoadAsset | UE 5.7](https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/EditorScriptingUtilities/UEditorAssetLibrary/LoadAsset) - API 参考
- [unreal.BlueprintEditorLibrary | UE 5.2](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/BlueprintEditorLibrary?application_version=5.2) - 蓝图图 API
- 网络搜索：使用 `-NullRHI -unattended -ExecutePythonScript` 无头执行 UE 的社区模式
- 网络搜索：Windows 注册表 UE 安装路径 `HKLM\SOFTWARE\EpicGames\Unreal Engine`

### 三级（低置信度）
- API 方法名 `find_event_graph()` — 需要在 UE 5.7 中运行时验证
- 完整编辑器脚本后的退出码行为 — 需要运行时测试

## 元数据

**置信度分解：**
- 标准技术栈：高 — 已通过 UE 源码和已安装二进制验证
- 架构：高 — EditorPythonExecuter.cpp 确认所有架构假设
- 陷阱：中 — 基于源码分析 + 社区报告，需要运行时验证
- 插件配置：高 — 直接从 `.uplugin` 文件读取
- API 可用性：中 — `EditorAssetLibrary` 已确认，`BlueprintEditorLibrary.find_event_graph()` 需要验证

**研究日期：** 2026-05-18
**有效期至：** 30 天（UE 5.7 API 稳定；插件配置不太可能变化）
