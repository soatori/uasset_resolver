"""
外部 Python 控制器：启动 UE 5.7 无头模式，执行资产加载脚本，
采集结果并报告。

用法：
  python scripts/controller.py [选项]
    --uasset PATH     .uasset 文件路径（默认：BP_FirstPersonCharacter.uasset）
    --ue-path PATH    覆盖引擎路径（D-08 回退）
    --output PATH     输出 JSON 路径（默认：temp/result.json）
    --timeout SECS    超时秒数（默认：120）
"""
import argparse
import os
import sys
import subprocess
import json
import shutil


def find_ue_via_registry():
    """扫描 Windows 注册表查找 UE 安装路径（D-08）。"""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r"SOFTWARE\EpicGames\Unreal Engine")
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
    return None


def find_ue_via_known_paths():
    """检查已知安装路径（D-08 回退）。"""
    known_paths = [
        r"D:\Program Files\Epic Games\Engine\UE_5.7",
        r"C:\Program Files\Epic Games\UE_5.7",
        r"C:\Program Files\Epic Games\Engine\UE_5.7",
    ]
    for base in known_paths:
        exe = os.path.join(base, "Engine", "Binaries", "Win64", "UnrealEditor.exe")
        if os.path.exists(exe):
            return exe
    return None


def find_ue_editor(cache_path="temp/ue_config.json", override_path=None):
    """
    引擎路径检测顺序（D-08 + D-09）：
    1. 缓存文件
    2. Windows 注册表
    3. 已知路径
    4. --ue-path 参数覆盖
    """
    # 1. 检查缓存
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                cached = config.get("engine_path")
                if cached and os.path.exists(cached):
                    print(f"[controller] 使用缓存的引擎路径：{cached}")
                    return cached
        except (json.JSONDecodeError, KeyError):
            pass

    # 2. 注册表扫描
    editor_exe = find_ue_via_registry()
    if editor_exe:
        print(f"[controller] 注册表发现引擎：{editor_exe}")
        return editor_exe

    # 3. 已知路径
    editor_exe = find_ue_via_known_paths()
    if editor_exe:
        print(f"[controller] 已知路径发现引擎：{editor_exe}")
        return editor_exe

    # 4. 用户指定
    if override_path:
        if os.path.exists(override_path):
            print(f"[controller] 使用用户指定的引擎路径：{override_path}")
            return override_path
        else:
            print(f"[controller] 错误：指定的引擎路径不存在：{override_path}")
            return None

    return None


def cache_ue_path(path, cache_path="temp/ue_config.json"):
    """首次成功后缓存引擎路径（D-09）。"""
    config = {"engine_path": path}
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    print(f"[controller] 引擎路径已缓存到 {cache_path}")


def derive_virtual_path(filename):
    """从文件名派生 UE 虚拟路径。"""
    # 去除 .uasset 扩展名
    name = os.path.splitext(filename)[0]
    # 反斜杠替换为正斜杠
    name = name.replace("\\", "/")
    # 前缀 /Game/
    return f"/Game/{name}"


def prepare_asset(uasset_path, content_dir="temp/Content"):
    """
    准备资产：复制到 Content 目录（PARSE-01）。
    返回虚拟路径。
    """
    if not os.path.exists(uasset_path):
        print(f"[controller] 错误：资产文件不存在：{uasset_path}")
        return None

    # 验证扩展名
    if not uasset_path.lower().endswith(".uasset"):
        print(f"[controller] 错误：文件不是 .uasset 格式：{uasset_path}")
        return None

    # 复制到 Content 目录
    filename = os.path.basename(uasset_path)
    dest_path = os.path.join(content_dir, filename)
    os.makedirs(content_dir, exist_ok=True)
    shutil.copy2(uasset_path, dest_path)
    print(f"[controller] 资产已复制到 {dest_path}")

    return derive_virtual_path(filename)


def run_ue_headless(ue_exe, project_path, script_path, output_path, timeout=300):
    """
    以无头模式启动 UE（PARSE-01 + D-06）。
    返回 subprocess 退出码。
    """
    # 构建命令
    # 注意：--output 参数嵌入在 -ExecutePythonScript 的值内
    script_arg = f"{script_path} --output {output_path}"

    # 使用正斜杠避免路径引号问题
    project_path = project_path.replace("\\", "/")
    script_arg = script_arg.replace("\\", "/")
    output_path = output_path.replace("\\", "/")
    ue_exe = ue_exe.replace("\\", "/")

    # 禁用启动画面和 splash screen（完全静默启动）
    cmd = [
        ue_exe,
        project_path,
        "-NoSplash",         # 禁用启动画面
        "-NullRHI",          # 无头渲染
        "-unattended",       # 无需用户交互
        "-NoLoadingScreen",  # 禁用加载画面
        "-NoScreenMessages", # 禁用屏幕消息
        "-stdout",           # 输出日志到 stdout
        f"-ExecutePythonScript={script_arg}",
    ]

    print(f"[controller] 启动 UE 无头模式（超时 {timeout} 秒）...")
    print(f"[controller] 命令：{cmd[0]} {cmd[1]} -NullRHI -unattended -ExecutePythonScript=...")

    # 使用 Popen 以便在超时时能正确终止进程
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        stdout, stderr = process.communicate(timeout=timeout)
        if stdout:
            print(f"[controller] UE stdout ({len(stdout)} chars):")
            print(stdout)
        if stderr:
            print(f"[controller] UE stderr ({len(stderr)} chars):")
            print(stderr)
        return process.returncode
    except subprocess.TimeoutExpired:
        print(f"[controller] 警告：UE 进程超时（{timeout}秒），强制终止")
        process.kill()
        stdout, stderr = process.communicate()
        if stdout:
            print(f"[controller] UE stdout (超时, {len(stdout)} chars):")
            print(stdout)
        if stderr:
            print(f"[controller] UE stderr (超时, {len(stderr)} chars):")
            print(stderr)
        return -1


def read_result(output_path):
    """读取并解析结果 JSON（D-02）。"""
    if not os.path.exists(output_path):
        print(f"[controller] 错误：结果文件不存在：{output_path}")
        return None

    try:
        with open(output_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"[controller] 错误：JSON 解析失败：{e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="UE 5.7 无头资产加载控制器")
    parser.add_argument("--uasset", default="BP_FirstPersonCharacter.uasset",
                        help=".uasset 文件路径")
    parser.add_argument("--ue-path", default=None,
                        help="覆盖 UE 引擎路径")
    parser.add_argument("--output", default="temp/result.json",
                        help="输出 JSON 路径")
    parser.add_argument("--timeout", type=int, default=300,
                        help="UE 进程超时秒数（默认 300，首次启动可能需要更长时间）")
    args = parser.parse_args()

    # 获取项目根目录（查找 temp/minimal.uproject）
    project_root = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(project_root, "temp", "minimal.uproject")):
        parent = os.path.dirname(project_root)
        if parent == project_root:
            print("[controller] 错误：找不到 temp/minimal.uproject")
            sys.exit(1)
        project_root = parent

    print(f"[controller] 项目根目录：{project_root}")

    # 1. 引擎检测
    cache_path = os.path.join(project_root, "temp", "ue_config.json")
    ue_exe = find_ue_editor(cache_path, args.ue_path)
    if not ue_exe:
        print("[controller] 错误：无法找到 UE 5.7 引擎")
        print("[controller] 请通过 --ue-path 参数指定引擎路径")
        sys.exit(1)

    # 首次成功后缓存
    if not os.path.exists(cache_path):
        cache_ue_path(ue_exe, cache_path)

    # 2. 资产准备
    uasset_path = os.path.abspath(args.uasset)
    content_dir = os.path.join(project_root, "temp", "Content")
    virtual_path = prepare_asset(uasset_path, content_dir)
    if not virtual_path:
        sys.exit(1)

    # 3. 启动 UE
    project_path = os.path.join(project_root, "temp", "minimal.uproject")
    script_path = os.path.join(project_root, "scripts", "ue_extract.py")
    output_path = os.path.join(project_root, args.output)

    exit_code = run_ue_headless(ue_exe, project_path, script_path, output_path, args.timeout)

    # 4. 读取结果
    result = read_result(output_path)
    if result:
        print("\n[controller] === 结果摘要 ===")
        print(f"  资产路径：{result.get('asset_path', 'N/A')}")
        print(f"  资产类型：{result.get('asset_class', 'N/A')}")
        print(f"  是否蓝图：{result.get('is_blueprint', False)}")
        if result.get('is_blueprint'):
            print(f"  生成类：{result.get('generated_class', 'N/A')}")
            print(f"  父类：{result.get('parent_class', 'N/A')}")
            print(f"  有 EventGraph：{result.get('has_event_graph', False)}")
        if result.get('error'):
            print(f"  错误：{result.get('error')}")
        print("[controller] === 完成 ===")

    # 5. 退出
    if exit_code == 0 and result and result.get('is_blueprint'):
        print("[controller] 成功")
        sys.exit(0)
    else:
        print(f"[controller] 失败（退出码={exit_code}）")
        sys.exit(1)


if __name__ == "__main__":
    main()