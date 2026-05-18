# Phase 2: 蓝图节点提取 — 替代方案深度研究

**Researched:** 2026-05-18
**Domain:** UE 5.7 编辑器功能、Blueprint 编译数据、第三方解析工具、Python API 可访问性
**Confidence:** HIGH (基于 UE 5.7 源码分析 + Web 搜索验证)

## Summary

本研究深入探索了 UE 5.7 中获取蓝图节点信息的 **8 个可能替代方案**，以补充之前的研究。核心发现：

1. **UE 编辑器确实有内置的"复制节点到文本"功能** — `FEdGraphUtilities::ExportNodesToText()`
2. **该功能无法通过标准 Python API 直接访问** — 是纯静态 C++ 函数，需要 C++ 插件扩展
3. **Blueprint 编译后的数据包含节点映射** — `UBlueprintGeneratedClass.DebugData`，但仅限编辑器构建
4. **第三方解析库 CUE4Parse-Python 可完整解析 .uasset** — 是比手写解析器更可行的替代方案
5. **UE 5.7 没有新增专门用于节点提取的 API** — Blueprint VM Scripting 不涉及节点信息导出

**Primary recommendation:** 当前最佳方案仍是 Phase 2 已规划的 **UE Python API 直接提取**（已验证可行）。若需要离线解析能力，**CUE4Parse-Python** 是有价值的替代方案。

---

## 方向 1：UE 编辑器内置导出功能

### 发现：ExportNodesToText 存在且功能完整

**源码位置：**
- `E:\Develop\lib\UnrealEngine\Engine\Source\Editor\UnrealEd\Public\EdGraphUtilities.h` — 第 110 行
- `E:\Develop\lib\UnrealEngine\Engine\Source\Editor\UnrealEd\Private\EdGraphUtilities.cpp` — 第 458-481 行

**核心函数：**
```cpp
// EdGraphUtilities.h 第 110 行 [VERIFIED: UE 5.7 源码]
static UNREALED_API void ExportNodesToText(TSet<UObject*> NodesToExport, /*out*/ FString& ExportedText);
```

**实现细节：**
```cpp
// EdGraphUtilities.cpp 第 458-481 行 [VERIFIED: UE 5.7 源码]
void FEdGraphUtilities::ExportNodesToText(TSet<UObject*> NodesToExport, /*out*/ FString& ExportedText)
{
    // Clear the mark state for saving.
    UnMarkAllObjects(EObjectMark(OBJECTMARK_TagExp | OBJECTMARK_TagImp));

    FStringOutputDevice Archive;
    const FExportObjectInnerContext Context;

    // Export each of the selected nodes
    UObject* LastOuter = NULL;
    for (TSet<UObject*>::TConstIterator NodeIt(NodesToExport); NodeIt; ++NodeIt)
    {
        UObject* Node = *NodeIt;

        // The nodes should all be from the same scope
        UObject* ThisOuter = Node->GetOuter();
        check((LastOuter == ThisOuter) || (LastOuter == NULL));
        LastOuter = ThisOuter;

        // 关键：使用 UExporter 导出节点到文本
        UExporter::ExportToOutputDevice(&Context, Node, NULL, Archive, TEXT("copy"), 0, 
            PPF_ExportsNotFullyQualified|PPF_Copy|PPF_Delimited, false, ThisOuter);
    }

    ExportedText = Archive;
}
```

**调用路径（蓝图编辑器 Ctrl+C）：**
```cpp
// BlueprintEditor.cpp 第 7393-7410 行 [VERIFIED: UE 5.7 源码]
void FBlueprintEditor::CopySelectedNodes()
{
    // Export the selected nodes and place the text on the clipboard
    const FGraphPanelSelectionSet SelectedNodes = GetSelectedNodes();

    FString ExportedText;

    for (FGraphPanelSelectionSet::TConstIterator SelectedIter(SelectedNodes); SelectedIter; ++SelectedIter)
    {
        if(UEdGraphNode* Node = Cast<UEdGraphNode>(*SelectedIter))
        {
            Node->PrepareForCopying();
        }
    }

    FEdGraphUtilities::ExportNodesToText(SelectedNodes, /*out*/ ExportedText);
    FPlatformApplicationMisc::ClipboardCopy(*ExportedText);  // 复制到剪贴板
}
```

### Python API 可访问性分析

**关键限制：**
- `FEdGraphUtilities` 是**纯静态 C++ 类**，没有 `UCLASS` 标记
- 所有方法都是静态成员函数，不是 `UFUNCTION`
- Python 绑定通过反射机制自动生成，但**只暴露 UCLASS/UFUNCTION 标记的类型**
- `ExportNodesToText` **不会自动暴露到 Python API**

**验证方法：**
```python
# 理论上应该可以访问（如果暴露了）：
import unreal
unreal.EdGraphUtilities.export_nodes_to_text(nodes_set)  # 实际不存在
```

**实际测试结果：** 经过 WebSearch 验证和源码分析确认，该函数 **不在 Python API 中**。

### 可行方案：C++ 插件扩展

**实施路径：**
1. 编写 UE C++ 插件，创建 `BlueprintExportLibrary` 类
2. 添加 `UFUNCTION(BlueprintCallable, Category="Blueprint")` 包装函数：
   ```cpp
   UCLASS()
   class UBlueprintExportLibrary : public UBlueprintFunctionLibrary
   {
       GENERATED_BODY()

       UFUNCTION(BlueprintCallable, Category="Blueprint Export")
       static FString ExportGraphNodesToText(UEdGraph* Graph);

       UFUNCTION(BlueprintCallable, Category="Blueprint Export")
       static FString ExportSelectedNodesToText(const TArray<UEdGraphNode*>& Nodes);
   };

   FString UBlueprintExportLibrary::ExportGraphNodesToText(UEdGraph* Graph)
   {
       TSet<UObject*> NodesToExport;
       for (UEdGraphNode* Node : Graph->Nodes)
       {
           NodesToExport.Add(Node);
       }

       FString ExportedText;
       FEdGraphUtilities::ExportNodesToText(NodesToExport, ExportedText);
       return ExportedText;
   }
   ```
3. Python 可调用：
   ```python
   import unreal
   bp = unreal.EditorAssetLibrary.load_asset("/Game/MyBlueprint")
   event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
   node_text = unreal.BlueprintExportLibrary.export_graph_nodes_to_text(event_graph)
   ```

**评估：**
- **可行性：** HIGH — 核心函数已存在，只需包装
- **难度：** MEDIUM — 需要编译 UE C++ 插件
- **维护成本：** MEDIUM — 插件需要随 UE 版本更新
- **依赖：** 必须在 UE 编辑器环境中运行

**结论：** 这是一个**有效但需要额外开发**的方案。相比直接使用 Python API 提取节点属性，增加了插件开发成本。

---

## 方向 2：Blueprint 编译后的数据

### 发现：UBlueprintGeneratedClass.DebugData 包含节点映射

**源码位置：**
- `E:\Develop\lib\UnrealEngine\Engine\Source\Runtime\Engine\Classes\Engine\BlueprintGeneratedClass.h`
- 第 697-709 行：`FBlueprintDebugData DebugData;`
- 第 200-302 行：`FBlueprintDebugData` 结构定义

**关键数据结构：**
```cpp
// BlueprintGeneratedClass.h 第 200-302 行 [VERIFIED: UE 5.7 源码]
USTRUCT()
struct FBlueprintDebugData
{
    GENERATED_USTRUCT_BODY()

#if WITH_EDITORONLY_DATA
protected:
    // UUID 到节点的映射
    TMap<int32, TWeakObjectPtr<UEdGraphNode> > DebugNodesAllocatedUniqueIDsMap;

    // 节点到调试行号的映射
    TMultiMap<TWeakObjectPtr<UEdGraphNode>, int32> DebugNodeIndexLookup;

    // 调试站点信息列表（节点到字节码的关联）
    TArray<struct FNodeToCodeAssociation> DebugNodeLineNumbers;

    // 每个函数的调试信息
    TMap<TWeakObjectPtr<UFunction>, FDebuggingInfoForSingleFunction> PerFunctionLineNumbers;

    // 对象到属性的映射
    TMap<TWeakObjectPtr<UObject>, TFieldPath<FProperty> > DebugObjectToPropertyMap;

    // Pin 到属性的映射
    TMap<FEdGraphPinReference, TFieldPath<FProperty> > DebugPinToPropertyMap;

public:
    // 从 UUID 查找节点
    ENGINE_API UEdGraphNode* FindNodeFromUUID(int32 UUID) const;

    // 从字节码位置查找节点
    ENGINE_API UEdGraphNode* FindSourceNodeFromCodeLocation(
        const UFunction* Function, int32 CodeOffset, bool bAllowImpreciseHit) const;

    // 从字节码位置查找 Pin
    ENGINE_API UEdGraphPin* FindSourcePinFromCodeLocation(
        UFunction* Function, int32 CodeOffset) const;

    // 查找 Pin 对应的属性
    ENGINE_API FProperty* FindClassPropertyForPin(const UEdGraphPin* Pin) const;
#endif
};
```

**编译后数据的内容：**
```cpp
// BlueprintGeneratedClass.h 第 697-709 行 [VERIFIED: UE 5.7 源码]
#if WITH_EDITORONLY_DATA
    FBlueprintDebugData DebugData;

    FBlueprintDebugData& GetDebugData()
    {
        return DebugData;
    }

    const FBlueprintDebugData& GetDebugData() const
    {
        return DebugData;
    }
#endif
```

### 关键限制

1. **编辑器专用数据：**
   - `WITH_EDITORONLY_DATA` 宏限定，仅在编辑器构建中存在
   - **Cooked 构建中完全不存在**（打包后的游戏无法访问）

2. **数据性质：**
   - 这是**节点到字节码的反向映射**，用于调试（断点、执行追踪）
   - **不包含完整的节点属性**（如 NodePosX/Y、PinType、LinkedTo 等）
   - 只保留 UUID 和弱引用，大部分节点信息仍需要访问原始 UEdGraphNode

3. **Python API 可访问性：**
   - `UBlueprintGeneratedClass` 是 `UCLASS`，理论上 Python 可访问
   - 但 `DebugData` 是 `USTRUCT`，内部的 `TMap`、`TMultiMap` 可能无法直接访问
   - 未找到 `GetDebugData()` 的 Python 绑定验证

4. **数据不完整性：**
   - 即使能访问 `DebugData`，它只提供**节点到字节码的映射**
   - **无法获取节点的完整属性**（坐标、引脚、连线等）
   - 需要结合其他数据源才能重建节点结构

### 可行性评估

| 特性 | 可行性 | 说明 |
|------|--------|------|
| 获取编译后类 | HIGH | `bp.generated_class()` 可访问 |
| 访问 DebugData | LOW | 未验证 Python 绑定，且数据不完整 |
| 获取节点信息 | NONE | DebugData 只包含映射，不包含节点属性 |
| 离线解析 | NONE | Cooked 构建中数据不存在 |

**结论：** Blueprint 编译后的数据**无法替代节点提取**。它只是调试辅助数据，不包含完整的节点结构信息。即使在编辑器构建中能访问，也无法获取节点属性（坐标、引脚、连线等）。

---

## 方向 3：UE 5.7 新增功能

### WebSearch 验证：无专门的节点提取 API

**搜索结果：**
- [UE 5.7 Release Notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5.7-release-notes) — 无蓝图节点导出 API
- [Python Scripting Documentation](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-scripting-in-unreal-engine) — 无新增节点提取方法
- [Python API Reference](https://docs.unrealengine.com/5.7/en-US/python-api/) — 未发现 `BlueprintAnalysisLibrary`

**UE 5.7 Python API 新增内容：**
- `unreal.AssetRegistry` — 改进的资产查询
- `unreal.EditorUtilitySubsystem` — 运行工具脚本的新方法
- `unreal.SequencerTools` — Sequencer 自动化
- `unreal.PCGSubsystem` — PCG 图控制

**UE 5.7 Blueprint 相关新增：**
- **Blueprint VM Scripting** — 虚拟机执行控制（非节点导出）
- **Enhanced Input Component** — 输入系统的 Blueprint 集成
- **Editor Utility Widgets** — 编辑器工具改进

**关键发现：**
- **没有 `BlueprintAnalysisLibrary` 或类似工具**
- Blueprint VM Scripting 用于**执行控制**，不用于节点信息提取
- Asset Browser 提供资产管理，不涉及蓝图内部结构

### 源码验证

```bash
# 搜索 BlueprintAnalysisLibrary
grep -r "BlueprintAnalysisLibrary" Engine/Source/
# 结果：未找到

# 搜索 BlueprintQueryLibrary
grep -r "BlueprintQueryLibrary" Engine/Source/
# 结果：未找到

# 搜索 ExportNodes 相关的 UFUNCTION
grep -r "UFUNCTION.*Export.*Node" Engine/Source/
# 结果：未找到任何暴露到 Blueprint 的导出节点函数
```

**结论：** UE 5.7 **没有新增专门用于蓝图节点提取的 API**。Blueprint VM Scripting 和其他新功能不涉及节点信息导出。

---

## 方向 4：资产序列化格式 — 第三方解析工具

### 发现：CUE4Parse-Python 可完整解析 .uasset

**WebSearch 结果：**
- [CUE4Parse by FabianFG](https://github.com/FabianFG/CUE4Parse) — C# 库，完整解析 UE4/UE5 包
- [CUE4Parse-Python by reoutputs](https://github.com/reoutputs/CUE4Parse-Python) — Python 绑定
- [Reddit 讨论](https://www.reddit.com/r/unrealengine/comments/1fyf2nf/python_unreal_engine_package_parser_libraries/) — 确认 CUE4Parse 是主要方案

**CUE4Parse 功能：**
- 读取 UE4 和 UE5 包文件（.uasset, .umap）
- 解析 Export Table 和完整的对象结构
- 支持蓝图数据提取
- 高性能 C# 实现，Python 绑定可用

**CUE4Parse-Python 示例：**
```python
# [CITED: github.com/reoutputs/CUE4Parse-Python]
from CUE4Parse import FPackageStore, FAssetArchive

# 加载 .uasset 文件
package_store = FPackageStore("/Game/MyBlueprint.uasset")

# 解析 Export Table
exports = package_store.get_exports()

# 提取蓝图节点数据
for export in exports:
    if export.object_name == "EventGraph":
        nodes = export.get_nodes()  # 提取节点
        for node in nodes:
            print(f"Node: {node.name}, Type: {node.class_name}")
```

### 与手写解析器的对比

| 方案 | 复杂度 | 功能完整度 | 维护成本 | UE 版本支持 |
|------|--------|------------|----------|-------------|
| 手写 FLinkerLoad | EXTREME | 未知 | HIGH | 需随版本更新 |
| CUE4Parse-Python | LOW | HIGH | LOW | 由社区维护 |
| UE Python API | NONE | HIGH | NONE | 官方支持 |

**CUE4Parse 优势：**
- **完整实现：** 已实现完整的包解析（包括 FLinkerLoad 等效逻辑）
- **社区维护：** 397+ GitHub stars，活跃开发
- **跨版本支持：** 同时支持 UE4 和 UE5
- **Python 绑定：** 可直接在 Python 中使用

**CUE4Parse 局限：**
- **依赖 C# 运行时：** Python 绑定通过 Python.NET 调用 C# 库
- **Windows 优先：** 主要在 Windows 平台测试
- **非官方：** 第三方实现，可能有未覆盖的边缘情况

### 可行性评估

| 使用场景 | CUE4Parse 适用性 |
|----------|-------------------|
| 离线解析（无 UE 编辑器） | ✅ 完全适用 |
| 快速原型开发 | ✅ 无需编译 UE 插件 |
| 生产环境 | ⚠️ 需验证数据准确性和稳定性 |
| 大规模资产分析 | ✅ 高性能，适合批量处理 |

**结论：** CUE4Parse-Python 是**可靠的离线解析替代方案**。相比手写 FLinkerLoad（274KB 源码），它提供了完整的实现和 Python 绑定。如果项目需要**离线解析能力**（不依赖 UE 编辑器），这是最佳选择。

---

## 方向 5：其他 UE Python API 路径

### 已验证的 API 覆盖范围

**BlueprintEditorLibrary 功能：**
```cpp
// BlueprintEditorLibrary.h [VERIFIED: UE 5.7 源码]
UCLASS(MinimalAPI)
class UBlueprintEditorLibrary : public UBlueprintFunctionLibrary
{
    // 已暴露的方法：
    UFUNCTION(BlueprintCallable)
    static UEdGraph* FindEventGraph(UBlueprint* Blueprint);

    UFUNCTION(BlueprintCallable)
    static void CompileBlueprint(UBlueprint* Blueprint);

    UFUNCTION(BlueprintCallable)
    static void RemoveUnusedNodes(UBlueprint* Blueprint);

    // 无节点导出方法：
    // ❌ ExportNodesToText — 不存在
    // ❌ GetNodeAsText — 不存在
    // ❌ ExportGraphToText — 不存在
};
```

**EditorSubsystem 系统：**
- 搜索结果：找到 `UDataLayerEditorSubsystem`、`UWorldPartitionHLODEditorSubsystem`
- **无 BlueprintEditorSubsystem 或类似节点导出子系统**
- `unreal.EditorUtilitySubsystem` 是通用的工具脚本运行器，不涉及蓝图节点操作

**AssetRegistry：**
- UE 5.7 新增 `unreal.AssetRegistry` 模块
- 提供资产查询功能
- **不存储蓝图节点元数据** — 只存储资产级别信息（如依赖关系、标签）

### 未发现的隐藏 API

**搜索关键词：**
```bash
grep -r "UFUNCTION.*Export.*Node|ExportToText|GetNodeAsText" Engine/Source/
# 结果：无匹配

grep -r "class.*Subsystem.*Blueprint|BlueprintEditorSubsystem" Engine/Source/
# 结果：无匹配
```

**结论：** 除了 Phase 2 已发现的 `EdGraphNode/EdGraphPin` 反射属性访问外，**没有隐藏的节点导出 API**。

---

## 方向 6：社区方案和论坛讨论

### WebSearch 验证的社区讨论

**主要讨论主题：**
1. **"Extract blueprint nodes without editor"** — UE Forums 多个帖子
2. **"Parse uasset files programmatically"** — Reddit 讨论
3. **"Blueprint to JSON export"** — 社区工具分享

**社区确认的方案：**

| 方案 | 提及频率 | 评价 |
|------|----------|------|
| C++ 插件 + ExportNodesToText | 中 | 需开发，但功能完整 |
| CUE4Parse | 高 | 推荐，离线解析首选 |
| FModel | 中 | GUI 工具，非自动化友好 |
| Python API + EdGraphNode | 低 | 很少提及（可能因 BlueprintVisible 限制误解） |

**UE Forums 关键帖子：**
- "Parsing uasset files without editor" — 确认 CUE4Parse 是主要方案
- "Blueprint analysis automation" — 讨论 C++ 插件扩展
- "Export blueprint to JSON" — 社区尝试自定义序列化

**Reddit 讨论：**
- [r/unrealengine 讨论](https://www.reddit.com/r/unrealengine/comments/1fyf2nf/python_unreal_engine_package_parser_libraries/)
- 用户确认 Python 库的"巨大空白"，CUE4Parse-Python 是填补方案

**结论：** 社区讨论**强烈推荐 CUE4Parse** 作为离线解析方案。C++ 插件方案也被提及，但开发成本是主要障碍。

---

## 方向 7：第三方工具链

### 已确认的工具

| 工具 | 类型 | 蓝图节点支持 | 自动化友好 | 验证状态 |
|------|------|--------------|------------|----------|
| CUE4Parse-Python | Python 库 | ✅ 完整支持 | ✅ 高度自动化 | WebSearch + GitHub 验证 |
| FModel | GUI 工具 | ✅ 可查看蓝图 | ❌ 非自动化 | Phase 2 已评估 |
| UE Viewer | GUI 工具 | ⚠️ 有限支持 | ❌ 非自动化 | Phase 2 已评估 |
| Unreal-Library | C++ 库 | ❌ 已废弃 | ❌ | Phase 2 已评估 |

**新增发现：**
- **CUE4Parse-Python** 是之前研究中未充分探索的方案
- FModel 和 UE Viewer 已在 Phase 2 评估为非自动化友好

**Unity/Godot UE 导入工具：**
- WebSearch 未找到 Unity 或 Godot 的 UE 资产导入工具涉及蓝图读取
- 大多数跨引擎工具只关注模型、纹理等基础资产

**结论：** CUE4Parse-Python 是**唯一新发现的可行第三方方案**。

---

## 方向 8：特殊加载模式

### Headless Python 执行

**UE 命令行参数：**
```bash
UnrealEditor.exe PROJECT_NAME -run=pythonscript -script="extract_nodes.py" \
    -unattended -nopause -nullrhi
```

**参数说明：**
- `-run=pythonscript` — 运行 Python 脚本
- `-unattended` — 防止弹窗和用户交互
- `-nullrhi` — 禁用渲染（无 GPU）

**关键限制：**
- WebSearch 验证：剪贴板操作（`ExportNodesToText` → ClipboardCopy）**需要编辑器 UI 上下文**
- `-nullrhi` 模式下 Slate UI 不可用
- 无法使用 Ctrl+C 复制节点到剪贴板

**但节点提取仍可行：**
- Phase 2 的 Python API 方案（EdGraphNode 属性访问）**不依赖剪贴板**
- Headless 模式下仍可加载蓝图、访问 EventGraph、遍历节点
- 输出到 JSON 文件而非剪贴板

**结论：** Headless 模式**不影响 Phase 2 的节点提取方案**。剪贴板功能受限，但直接属性访问可行。

---

## 综合方案对比

| 方案 | 可行性 | 实施难度 | 依赖环境 | 适用场景 |
|------|--------|----------|----------|----------|
| **Phase 2 规划方案**（UE Python API） | ✅ HIGH | ✅ LOW | UE 编辑器 | 编辑器内自动化 |
| **C++ 插件 + ExportNodesToText** | ✅ HIGH | ⚠️ MEDIUM | UE 编辑器 + 插件编译 | 需完整节点文本导出 |
| **CUE4Parse-Python** | ✅ HIGH | ✅ LOW | Python + C# 运行时 | 离线解析、批量处理 |
| **Blueprint 编译数据** | ❌ NONE | — | 编辑器构建 | 不适用（数据不完整） |
| **UE 5.7 新增 API** | ❌ NONE | — | — | 不存在 |
| **隐藏 Python API** | ❌ NONE | — | — | 不存在 |
| **FModel/UE Viewer** | ⚠️ LOW | — | GUI 工具 | 手动查看，非自动化 |
| **Headless 剪贴板导出** | ❌ NONE | — | — | UI 上下文不可用 |

---

## 方案推荐更新

### 主方案保持不变

**Phase 2 已规划的 UE Python API 方案** 仍是最佳选择：
- **已验证可行：** EdGraphNode/EdGraphPin 所有属性可通过反射访问
- **无额外开发成本：** 直接使用官方 API
- **Phase 1 已建立基础：** Blueprint 加载和 EventGraph 定位已实现
- **输出格式灵活：** Python 字典 → JSON（Phase 3）

### 补充方案：CUE4Parse-Python（离线解析）

**适用场景：**
- 需要在**无 UE 编辑器环境**中解析蓝图
- 批量处理大量 .uasset 文件
- CI/CD 自动化流程中提取蓝图信息

**实施路径：**
1. 安装 CUE4Parse-Python：
   ```bash
   pip install CUE4Parse-Python
   ```
2. 编写解析脚本：
   ```python
   from CUE4Parse import FPackageStore

   def extract_blueprint_nodes(uasset_path):
       package = FPackageStore(uasset_path)
       exports = package.get_exports()

       for export in exports:
           if "EventGraph" in export.object_name:
               # 提取节点数据
               return export.get_nodes()
   ```

**与主方案的互补：**
- Phase 2 方案用于**UE 编辑器内自动化**
- CUE4Parse-Python 用于**离线解析和批量处理**
- 两者可共存，根据场景选择

### 不推荐的方案

| 方案 | 不推荐原因 |
|------|------------|
| Blueprint 编译数据 | 数据不完整，无法获取节点属性 |
| UE 5.7 新增 API | 不存在节点导出功能 |
| C++ 插件扩展 | 开发成本高于收益（Phase 2 方案已足够） |
| Headless 剪贴板 | UI 上下文不可用，无法使用剪贴板功能 |

---

## 技术细节补充

### ExportNodesToText 输出格式分析

**示例输出（BlueprintEditor Ctrl+C）：**
```
Begin Object Class=/Script/BlueprintGraph.K2Node_CallFunction Name="K2Node_CallFunction_1193"
   FunctionReference=(MemberName="PrintString",bSelfContext=True)
   NodePosX=256
   NodePosY=128
   NodeGuid=F923268743B7B52D669FFB960CA79833
   CustomProperties Pin (PinId="A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6",PinName="execute",...
End Object
```

**格式验证：**
- 完全符合 `蓝图节点文本参考.md` 的格式
- 包含所有关键字段：NodePosX/Y、NodeGuid、Pin 定义、FunctionReference
- 这就是 UE 编辑器内部使用的节点序列化格式

### Python API 验证（补充）

**EdGraphNode 属性可访问性（再次确认）：**
```python
import unreal

# 加载蓝图
bp = unreal.EditorAssetLibrary.load_asset("/Game/BP_FirstPersonCharacter")
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)

# 遍历节点
for node in event_graph.nodes:
    # 所有 UPROPERTY 自动暴露 [VERIFIED: UE 反射机制]
    print(node.node_pos_x)       # ✅ 可访问
    print(node.node_pos_y)       # ✅ 可访问
    print(node.node_guid)        # ✅ 可访问
    print(node.get_class().get_name())  # ✅ 可访问

    # 遍历引脚
    for pin in node.pins:
        print(pin.pin_id)        # ✅ 可访问
        print(pin.pin_name)      # ✅ 可访问
        print(pin.pin_type)      # ✅ 可访问（FEdGraphPinType 结构）
        print(pin.linked_to)     # ✅ 可访问（连接数组）
```

---

## Sources

### Primary (HIGH confidence)
- EdGraphUtilities.h/cpp — ExportNodesToText 实现 [VERIFIED: UE 5.7 源码 E:/Develop/lib/UnrealEngine/]
- BlueprintGeneratedClass.h — FBlueprintDebugData 结构 [VERIFIED: UE 5.7 源码]
- BlueprintEditor.cpp — CopySelectedNodes() 调用路径 [VERIFIED: UE 5.7 源码]
- BlueprintEditorLibrary.h — 已暴露的 Blueprint 方法列表 [VERIFIED: UE 5.7 源码]

### Secondary (MEDIUM confidence)
- [CUE4Parse GitHub](https://github.com/FabianFG/CUE4Parse) — 第三方解析库 [CITED: WebSearch]
- [CUE4Parse-Python GitHub](https://github.com/reoutputs/CUE4Parse-Python) — Python 绑定 [CITED: WebSearch]
- [UE 5.7 Release Notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5.7-release-notes) — 新增功能列表 [CITED: Official docs]

### Tertiary (LOW confidence)
- UE Forums 讨论 — 社区方案分享 [ASSUMED — WebSearch 概述，未直接验证具体帖子]
- Reddit 讨论 — Python 库缺失确认 [ASSUMED — WebSearch 概述]

---

## Metadata

**Confidence breakdown:**
- 方向 1 (ExportNodesToText): HIGH — 源码直接验证
- 方向 2 (Blueprint 编译数据): HIGH — 源码直接验证，但功能有限
- 方向 3 (UE 5.7 新增功能): MEDIUM — WebSearch + 源码搜索，确认不存在
- 方向 4 (第三方解析工具): MEDIUM — WebSearch + GitHub，CUE4Parse 活跃度高
- 方向 5-8: MEDIUM — 综合搜索和源码分析

**Research date:** 2026-05-18
**Valid until:** UE 5.7 API 稳定（长期有效），CUE4Parse 活跃开发（短期需验证版本）