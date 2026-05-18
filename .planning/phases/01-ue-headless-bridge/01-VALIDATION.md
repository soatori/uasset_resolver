# Phase 1 验证映射 — UE 无头桥接

## 需求 → 测试

| 需求 | 验证 | 方法 | 预期结果 |
|------|------|------|----------|
| PARSE-01: 启动 UE 5.7 无头模式 + 执行 Python 脚本 | V-01: 进程以正确参数启动 | 运行 `controller.py`，检查 subprocess 参数包含 `-unattended -NullRHI -ExecutePythonScript` | UE 进程以这些参数启动 |
| PARSE-01 | V-02: 脚本执行并产生输出 | 检查 `temp/result.json` 在 controller.py 完成后存在 | 包含有效结构的 JSON 文件 |
| PARSE-02: 加载 .uasset + 检测蓝图 | V-03: 蓝图检测正确 | 检查 `temp/result.json` 对 `BP_FirstPersonCharacter.uasset` 包含 `is_blueprint: true` | `is_blueprint` 为布尔值 `true` |
| PARSE-02 | V-04: 非蓝图检测 | （未来）使用非蓝图 .uasset（如纹理）测试 | `is_blueprint` 为布尔值 `false` |

## 成功标准 → 观察方法

| 标准 | 验证方式 |
|------|----------|
| SC1: 以 `-unattended -NullRHI` 启动 UE + 执行脚本 | Windows 任务管理器 / `Get-Process` 显示 UnrealEditor.exe；生成 result.json |
| SC2: 正确报告是否为蓝图 | `temp/result.json` 中 `is_blueprint == true`（已知蓝图资产） |
| SC3: UE 干净退出，无残留窗口 | controller.py 返回后进程列表中无 UnrealEditor.exe |

## 冒烟测试命令

```bash
python scripts/controller.py BP_FirstPersonCharacter.uasset --output temp/result.json
python -c "import json; d=json.load(open('temp/result.json')); assert d.get('is_blueprint')==True, '蓝图检测失败'; print('PARSE-02: 通过')"
tasklist | findstr UnrealEditor && echo 'SC3: 失败 - 进程仍在运行' || echo 'SC3: 通过 - 干净退出'
```

## 退出码文档（来自 Task 4）

_首次成功运行后填写:_
- 成功时观察到的退出码: 待定
- 失败时观察到的退出码: 待定
- 超时时观察到的退出码: 待定
