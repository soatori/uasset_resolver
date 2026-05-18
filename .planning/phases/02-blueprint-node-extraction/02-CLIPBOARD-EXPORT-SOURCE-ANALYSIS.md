# Phase 2: 蓝图节点提取 — 剪贴板文本导出源码分析

**Created:** 2026-05-18
**Scope:** UE 编辑器中 Ctrl+C 复制蓝图节点的完整源码链路

---

## 完整调用链路

```
用户按下 Ctrl+C
  ↓
FBlueprintEditor::CopySelectedNodes()          (BlueprintEditor.cpp:7393)
  ↓
FEdGraphUtilities::ExportNodesToText()         (EdGraphUtilities.cpp:458)
  ↓
UExporter::ExportToOutputDevice()              (每节点调用)
  ↓
UObjectExporterT3D::ExportText()              (EditorExporters.cpp:331)
  ↓
EmitBeginObject() → ExportObjectInner() → EmitEndObject()
  ↓
FStringOutputDevice 累积文本
  ↓
FPlatformApplicationMisc::ClipboardCopy()      (写入系统剪贴板)
```

---

## 逐层源码分析

### 1. 入口：FBlueprintEditor::CopySelectedNodes()

**文件:** `Engine/Source/Editor/Kismet/Private/BlueprintEditor.cpp` 第 7393-7410 行

```cpp
void FBlueprintEditor::CopySelectedNodes()
{
    // 获取选中的节点集合
    const FGraphPanelSelectionSet SelectedNodes = GetSelectedNodes();

    FString ExportedText;

    // 准备每个节点（清理临时状态）
    for (FGraphPanelSelectionSet::TConstIterator SelectedIter(SelectedNodes); SelectedIter; ++SelectedIter)
    {
        if(UEdGraphNode* Node = Cast<UEdGraphNode>(*SelectedIter))
        {
            Node->PrepareForCopying();
        }
    }

    // 核心导出：将节点集合导出为文本
    FEdGraphUtilities::ExportNodesToText(SelectedNodes, /*out*/ ExportedText);

    // 写入系统剪贴板
    FPlatformApplicationMisc::ClipboardCopy(*ExportedText);
}
```

**关键点:**
- 命令绑定：`GraphEditorCommands->MapAction(FGenericCommands::Get().Copy, ...)` (第 1638 行)
- Cut（剪切）复用此方法：`CutSelectedNodes()` 调用 `CopySelectedNodes()` 后再删除
- Duplicate（复制+粘贴）也复用此方法

---

### 2. 核心导出：FEdGraphUtilities::ExportNodesToText()

**文件:** `Engine/Source/Editor/UnrealEd/Private/EdGraphUtilities.cpp` 第 458-481 行

```cpp
void FEdGraphUtilities::ExportNodesToText(TSet<UObject*> NodesToExport, /*out*/ FString& ExportedText)
{
    // 清除标记状态（用于保存/加载标记系统）
    UnMarkAllObjects(EObjectMark(OBJECTMARK_TagExp | OBJECTMARK_TagImp));

    // 使用 FStringOutputDevice 作为文本累积缓冲区
    FStringOutputDevice Archive;
    const FExportObjectInnerContext Context;

    // 遍历每个节点导出
    UObject* LastOuter = NULL;
    for (TSet<UObject*>::TConstIterator NodeIt(NodesToExport); NodeIt; ++NodeIt)
    {
        UObject* Node = *NodeIt;

        // 所有节点必须来自同一个 Outer（同一个 Graph）
        UObject* ThisOuter = Node->GetOuter();
        check((LastOuter == ThisOuter) || (LastOuter == NULL));
        LastOuter = ThisOuter;

        // 核心导出调用
        UExporter::ExportToOutputDevice(&Context, Node, NULL, Archive, TEXT("copy"), 0,
            PPF_ExportsNotFullyQualified | PPF_Copy | PPF_Delimited,
            false, ThisOuter);
    }

    ExportedText = Archive;
}
```

**关键参数解析:**
- `TEXT("copy")` — 导出格式类型，匹配 `FormatExtension.Add(TEXT("COPY"))`
- `PPF_ExportsNotFullyQualified` — 不导出完全限定路径
- `PPF_Copy` — 剪贴板模式（影响哪些属性被导出）
- `PPF_Delimited` — 使用 Begin/End Object 分隔符
- `ThisOuter` — 指定导出上下文（确保 ExportPath 正确）

---

### 3. 分发器：UExporter::ExportToOutputDevice()

UE 的导出器工厂系统，根据对象类型查找匹配的 `UExporter` 子类。

调用签名:
```cpp
UExporter::ExportToOutputDevice(
    &Context,              // FExportObjectInnerContext
    Node,                  // 要导出的 UObject
    NULL,                  // 指定 Exporter（NULL=自动查找）
    Archive,               // 输出设备
    TEXT("copy"),          // 导出类型
    0,                     // 缩进级别
    PPF_ExportsNotFullyQualified | PPF_Copy | PPF_Delimited,
    false,                 // bNoReplaceFromCombo
    ThisOuter              // 外部对象
);
```

**自动匹配:** 由于 `UObjectExporterT3D` 的 `SupportedClass = UObject::StaticClass()`，所有 EdGraphNode 都匹配此导出器。

---

### 4. 实际导出：UObjectExporterT3D::ExportText()

**文件:** `Engine/Source/Editor/UnrealEd/Private/EditorExporters.cpp` 第 331-338 行

```cpp
bool UObjectExporterT3D::ExportText(
    const FExportObjectInnerContext* Context,
    UObject* Object,
    const TCHAR* Type,
    FOutputDevice& Ar,          // 输出设备（累积文本）
    FFeedbackContext* Warn,
    uint32 PortFlags )
{
    EmitBeginObject(Ar, Object, PortFlags);      // 输出 "Begin Object Class=... Name=..."
    ExportObjectInner(Context, Object, Ar, PortFlags);  // 输出所有属性和子对象
    EmitEndObject(Ar);                           // 输出 "End Object"

    return true;
}
```

---

### 5. Begin Object 行格式

`EmitBeginObject()` 生成的格式:

```
Begin Object Class=/Script/BlueprintGraph.K2Node_CallFunction Name="K2Node_CallFunction_1193" ExportPath="/Script/BlueprintGraph.K2Node_CallFunction'/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter.BP_FirstPersonCharacter:EventGraph.K2Node_CallFunction_1193'"
```

包含三个字段:
- `Class=` — 对象的完整类路径
- `Name=` — 对象名称
- `ExportPath=` — 在资源层次结构中的完整路径

---

### 6. 属性导出：ExportObjectInner()

这是生成所有属性行的核心函数，包括:

**直接属性 (Node 的 UPROPERTY):**
- `FunctionReference=(MemberName="Jump",bSelfContext=True)`
- `NodePosX=3136`
- `NodePosY=-1040`
- `NodeGuid=F923268743B7B52D669FFB960CA79833`

**引脚导出为 CustomProperties:**
```
CustomProperties Pin (PinId=13FD260E...,PinName="execute",PinType.PinCategory="exec",...,LinkedTo=(K2Node_EnhancedInputAction_5 6412140B...,),...)
```

引脚通过 `EdGraphPin` 的 `ExportText` 导出（非 UObject，作为 Inner 对象处理）。

---

### 7. 导入反向链路：ImportNodesFromText()

**文件:** `Engine/Source/Editor/UnrealEd/Private/EdGraphUtilities.cpp` 第 484-497 行

```cpp
void FEdGraphUtilities::ImportNodesFromText(UEdGraph* DestinationGraph, const FString& TextToImport, /*out*/ TSet<UEdGraphNode*>& ImportedNodeSet)
{
    // 将文本缓冲区解析为对象
    FGraphObjectTextFactory Factory(DestinationGraph);
    Factory.ProcessBuffer(DestinationGraph, RF_Transactional, TextToImport);

    // 修复引脚交叉链接等
    FEdGraphUtilities::PostProcessPastedNodes(Factory.SpawnedNodes);

    // 解析所有引脚引用
    UEdGraphPin::ResolveAllPinReferences();

    ImportedNodeSet.Append(Factory.SpawnedNodes);
}
```

**`FGraphObjectTextFactory`** (第 108-222 行):
- 继承 `FCustomizableTextObjectFactory`
- `CanCreateClass()` — 验证节点能否在目标图中创建
- `ProcessConstructedObject()` — 处理每个解析出的节点
- `PostProcessConstructedObjects()` — 后处理：修复引脚链接、替换不兼容节点

---

## 为什么这个方案强大

### 文本格式 = UE 原生序列化格式

剪贴板文本格式与 `.uasset` 反序列化后的文本表示**完全一致**，因为:
1. 都使用 `UExporter` 导出系统
2. 都通过 `FProperty::ExportText()` 序列化属性
3. `PPF_Copy` 标志确保相同的属性子集

### 可跨蓝图粘贴

虚幻盒子 (ue5box.com) 和 UE 编辑器都利用了这个特性:
- 导出的文本包含完整的 `ExportPath`
- 粘贴时 `FGraphObjectTextFactory` 自动重命名冲突的节点
- 引脚链接通过 PinId 解析，跨节点也能正确重建

---

## 对我们的意义

### 优势
1. **格式标准化** — 输出就是 UE 原生格式，无需自定义解析器
2. **双向可逆** — Export → Import 完全可逆，数据不丢失
3. **包含全部数据** — 坐标/引脚/连线/GUID 全部在内

### 挑战
1. **只能在 UE 编辑器内执行** — `FEdGraphUtilities` 在 `UnrealEd` 模块中
2. **`UnrealEd` 构建守卫** — 无法编译独立工具调用此函数
3. **C++ 插件方案** — 需要 UE 插件，用户明确不倾向

### 替代方案映射

| 方案 | 能否利用此导出链路 | 可行性 |
|------|-------------------|--------|
| 现有 Python API | ❌ 不能（API 不暴露） | 已验证 |
| C++ 插件 | ✅ 直接调用 | 用户不倾向 |
| CUE4Parse CLI | ❌ 独立实现 | 已编译验证 |
| UE 源码抽取 | ✅ 但需引擎编译环境 | 不可行 |
| **离线解析 .uasset 二进制** | ❌ 不走此链路 | CUE4Parse 方案 |

---

**分析日期:** 2026-05-18
**状态:** 源码分析完成
