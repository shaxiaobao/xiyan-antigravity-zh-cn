#!/usr/bin/env python3
"""Install, inspect, and restore the external Antigravity Simplified Chinese patch."""

from __future__ import annotations

import argparse
import csv
import sys
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path


PLATFORM = sys.platform
PACKAGE_DIR = Path(__file__).resolve().parent
APP_ASAR = Path("/Applications/Antigravity.app/Contents/Resources/app.asar")
BACKUP_DIR = PACKAGE_DIR / "backups"
STATE_PATH = PACKAGE_DIR / "patch-state.json"
TARGET_PATH = "/dist/utils.js"
MARKER = "__ANTIGRAVITY_ZH_CN_EXTERNAL_PATCH__"


def configure_output():
    # Redirected consoles on non-Chinese Windows can otherwise fail after a successful install.
    if PLATFORM == "win32":
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="replace")


def normalize_app_path(value):
    path = Path(value).expanduser().resolve()
    if path.name.lower() == "app.asar":
        return path
    if path.suffix.lower() == ".exe":
        path = path.parent
    if path.suffix.lower() == ".app":
        return path / "Contents/Resources/app.asar"
    return path / "resources/app.asar"


def locate_app(explicit=None):
    value = explicit or os.environ.get("ANTIGRAVITY_PATH")
    if value:
        candidate = normalize_app_path(value)
        if not candidate.is_file():
            raise RuntimeError(f"指定位置未找到 app.asar：{candidate}")
        return candidate
    if PLATFORM == "darwin":
        candidates = [Path("/Applications/Antigravity.app/Contents/Resources/app.asar"),
                      Path.home() / "Applications/Antigravity.app/Contents/Resources/app.asar"]
    elif PLATFORM == "win32":
        candidates = []
        for variable, suffixes in {
            "LOCALAPPDATA": ["Programs/Antigravity", "Antigravity"],
            "ProgramFiles": ["Antigravity"],
            "ProgramFiles(x86)": ["Antigravity"],
        }.items():
            if os.environ.get(variable):
                candidates.extend(Path(os.environ[variable]) / suffix / "resources/app.asar" for suffix in suffixes)
    else:
        raise RuntimeError("目前支持 macOS 和 Windows。")
    found = list(dict.fromkeys(p.resolve() for p in candidates if p.is_file()))
    if len(found) == 1:
        return found[0]
    if len(found) > 1:
        raise RuntimeError("发现多个安装位置，请用 --app 指定其中一个：" + ", ".join(map(str, found)))
    raise RuntimeError("未找到 Antigravity，请用 --app 指定安装目录、可执行文件或 app.asar。")


def app_running():
    if PLATFORM == "win32":
        # Conservatively treat any Antigravity.exe as running, including other installs.
        tasklist = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32/tasklist.exe"
        result = subprocess.run([str(tasklist), "/FO", "CSV", "/NH"], capture_output=True, timeout=30)
        if result.returncode != 0:
            raise RuntimeError("无法检查应用进程，已停止操作。")
        rows = list(csv.reader(result.stdout.decode("utf-8", errors="replace").splitlines()))
        if not any(len(row) >= 2 and row[1].isdigit() for row in rows):
            raise RuntimeError("无法解析 Windows 进程列表，已停止操作。")
        return any(row and row[0].lower() == "antigravity.exe" for row in rows)
    result = subprocess.run(["/usr/bin/pgrep", "-f", "^" + re.escape(str(APP_ASAR.parents[1] / "MacOS/Antigravity")) + "( |$)"], capture_output=True)
    if result.returncode not in (0, 1):
        raise RuntimeError("无法检查应用进程，已停止操作。")
    return result.returncode == 0


def require_stopped():
    if app_running():
        raise RuntimeError("请完全退出 Antigravity 后重试；不会中断正在运行的任务。")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_archive(path: Path):
    with path.open("rb") as stream:
        header = struct.unpack("<4I", stream.read(16))
        json_bytes = stream.read(header[3])
        tree = json.loads(json_bytes)
        data_start = 8 + header[1]
        stream.seek(0)
        raw = stream.read()
    return header, tree, data_start, raw


def walk_files(node, prefix=""):
    if "files" in node:
        for name, child in node["files"].items():
            yield from walk_files(child, f"{prefix}/{name}")
    else:
        yield prefix, node


def set_file_metadata(tree, target_path, content):
    for path, metadata in walk_files(tree):
        if path == target_path:
            metadata["size"] = len(content)
            return metadata
    raise RuntimeError(f"ASAR file not found: {target_path}")


def build_integrity(content):
    block_size = 4 * 1024 * 1024
    blocks = [
        hashlib.sha256(content[index : index + block_size]).hexdigest()
        for index in range(0, len(content), block_size)
    ]
    if not blocks:
        blocks = [hashlib.sha256(b"").hexdigest()]
    return {
        "algorithm": "SHA256",
        "hash": hashlib.sha256(content).hexdigest(),
        "blockSize": block_size,
        "blocks": blocks,
    }


def patch_utils_source(source: bytes, injector: str) -> bytes:
    text = source.decode("utf-8")
    if MARKER in text:
        raise RuntimeError("The installed ASAR already contains the Chinese patch.")
    marker = "    void win.loadURL(url);"
    if marker not in text:
        raise RuntimeError("The installed Antigravity build has no supported loadURL marker.")
    injector_literal = json.dumps(injector, ensure_ascii=False)
    block = f'''    // {MARKER}\n    const zhCnInjector = {injector_literal};\n    const applyZhCn = () => {{\n        if (!win.isDestroyed?.() && !hubContents.isDestroyed?.()) {{\n            void hubContents.executeJavaScript(zhCnInjector).catch(() => undefined);\n        }}\n    }};\n    hubContents.on('did-finish-load', applyZhCn);\n    win.on('closed', () => hubContents.off?.('did-finish-load', applyZhCn));\n'''
    return text.replace(marker, block + marker, 1).encode("utf-8")


def repack_archive(original_path: Path, output_path: Path, patched_content: bytes):
    _, tree, data_start, raw = read_archive(original_path)
    target_meta = set_file_metadata(tree, TARGET_PATH, patched_content)
    payloads = {}
    for path, metadata in walk_files(tree):
        if metadata.get("unpacked"):
            continue
        if path == TARGET_PATH:
            payload = patched_content
        else:
            offset = data_start + int(metadata["offset"])
            size = int(metadata["size"])
            payload = raw[offset : offset + size]
        payloads[path] = payload
        metadata["size"] = len(payload)
        metadata["integrity"] = build_integrity(payload)

    data = bytearray()
    for path, metadata in walk_files(tree):
        if metadata.get("unpacked"):
            continue
        metadata["offset"] = str(len(data))
        data.extend(payloads[path])

    json_bytes = json.dumps(tree, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    header = struct.pack("<4I", 4, len(json_bytes) + 10, len(json_bytes) + 6, len(json_bytes))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as stream:
        stream.write(header)
        stream.write(json_bytes)
        stream.write(b"\0\0")
        stream.write(data)
    return target_meta


def load_injector() -> str:
    dictionary = json.loads((PACKAGE_DIR / "translations.json").read_text(encoding="utf-8"))
    return "window.__antigravityZhCnDictionary = " + json.dumps(dictionary, ensure_ascii=False) + ";\n" + (PACKAGE_DIR / "translator.js").read_text(encoding="utf-8")


def read_state():
    if not STATE_PATH.exists():
        return None
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def inspect_app(path=None):
    _, tree, data_start, raw = read_archive(path or APP_ASAR)
    files = dict(walk_files(tree))
    def content(path):
        meta = files[path]
        start = data_start + int(meta["offset"])
        return raw[start : start + int(meta["size"])]
    version = json.loads(content("/package.json")).get("version", "unknown")
    return version, content(TARGET_PATH)


def status():
    if not APP_ASAR.exists():
        print(f"未找到 Antigravity: {APP_ASAR}")
        return 1
    current = sha256(APP_ASAR)
    state = read_state()
    if state and current == state.get("patchedSha256"):
        print(f"已安装简体中文补丁：Antigravity {state['version']}")
        if state.get("injectorSha256") != hashlib.sha256(load_injector().encode()).hexdigest():
            print("本地词库已更新，完全退出后运行 apply 可更新翻译。")
        print(f"当前 app.asar: {current}")
        return 0
    if state and current == state.get("originalSha256"):
        print("未安装补丁（当前是原始 app.asar）。")
        return 0
    version, source = inspect_app()
    if MARKER.encode() not in source:
        if not state or version != state.get("version"):
            print(f"Antigravity {version} 尚未安装汉化补丁（应用更新会覆盖补丁）。")
            print("完全退出应用后运行 apply；工具将备份当前版本，不会恢复旧版应用。")
            return 2
    print(f"当前 app.asar 未匹配已记录版本：{current}")
    print("检测到同版本外部修改或未知补丁，请先运行 build 检查。")
    return 2


def apply_patch():
    if not APP_ASAR.exists():
        raise RuntimeError(f"未找到 Antigravity: {APP_ASAR}")
    original_hash = sha256(APP_ASAR)
    source_archive = APP_ASAR
    current_hash = original_hash
    injector = load_injector()
    injector_hash = hashlib.sha256(injector.encode()).hexdigest()
    previous = read_state()
    if previous and original_hash == previous.get("patchedSha256"):
        if previous.get("injectorSha256") == injector_hash:
            print("补丁和词库已是当前版本，无需重复操作。")
            return
        source_archive = Path(previous["backup"])
        if not source_archive.exists() or sha256(source_archive) != previous["originalSha256"]:
            raise RuntimeError("更新词库需要有效的原始备份；校验失败，已停止。")
        original_hash = previous["originalSha256"]
        print("正在基于已校验的原始备份更新词库。")
    version, old_utils = inspect_app(source_archive)
    # Validate compatibility before changing backups, state, or the application.
    patched_utils = patch_utils_source(old_utils, injector)
    if previous and original_hash != previous.get("originalSha256"):
        if version == "unknown" or version == previous.get("version"):
            raise RuntimeError("检测到同版本 app.asar 被外部修改，已停止安装。不会覆盖未知修改。")
        print(f"检测到应用更新：{previous['version']} → {version}，将为当前版本单独备份并安装。")

    backup_name = f"app.asar.{original_hash[:12]}.original"
    backup_path = BACKUP_DIR / backup_name
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if not backup_path.exists():
        shutil.copy2(source_archive, backup_path)
    if sha256(backup_path) != original_hash:
        raise RuntimeError("原始备份校验失败，已停止安装。")
    if previous:
        history = BACKUP_DIR / f"patch-state.{previous['patchedSha256'][:12]}.json"
        history.write_text(json.dumps(previous, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with tempfile.NamedTemporaryFile(prefix="antigravity-zh-cn-", suffix=".asar", dir=APP_ASAR.parent, delete=False) as temp:
        temp_path = Path(temp.name)
    try:
        repack_archive(source_archive, temp_path, patched_utils)
        os.chmod(temp_path, APP_ASAR.stat().st_mode & 0o777)
        patched_hash = sha256(temp_path)
        if sha256(APP_ASAR) != current_hash:
            raise RuntimeError("安装期间应用文件发生变化，已停止。请待应用更新结束后重试。")
        os.replace(temp_path, APP_ASAR)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    state = {
        "version": version,
        "originalSha256": original_hash,
        "patchedSha256": patched_hash,
        "backup": str(backup_path),
        "target": str(APP_ASAR),
        "marker": MARKER,
        "injectorSha256": injector_hash,
    }
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已安装 Antigravity {version} 简体中文补丁。")
    print(f"原始备份：{backup_path}")
    print("请完全退出并重新打开 Antigravity 后查看效果。")


def restore_patch():
    state = read_state()
    if not state:
        raise RuntimeError("没有找到补丁状态文件。")
    current = sha256(APP_ASAR)
    if current != state.get("patchedSha256"):
        raise RuntimeError("当前 app.asar 不是本补丁生成的版本，已停止恢复以避免覆盖应用更新。")
    backup = Path(state["backup"])
    if not backup.exists():
        raise RuntimeError(f"找不到原始备份：{backup}")
    if sha256(backup) != state.get("originalSha256"):
        raise RuntimeError("原始备份校验失败，已停止恢复。")
    shutil.copy2(backup, APP_ASAR)
    STATE_PATH.unlink(missing_ok=True)
    print("已恢复 Antigravity 原始 app.asar。请重新启动应用。")


def build_copy(output: Path):
    if not APP_ASAR.exists():
        raise RuntimeError(f"未找到 Antigravity: {APP_ASAR}")
    source = APP_ASAR
    state = read_state()
    if state and sha256(APP_ASAR) == state.get("patchedSha256"):
        source = Path(state["backup"])
        if sha256(source) != state["originalSha256"]:
            raise RuntimeError("原始备份校验失败。")
    if output.resolve() == APP_ASAR.resolve() or output.resolve() == source.resolve():
        raise RuntimeError("build 输出不能覆盖应用或原始备份。")
    _, old_utils = inspect_app(source)
    patched_utils = patch_utils_source(old_utils, load_injector())
    repack_archive(source, output, patched_utils)
    print(f"已生成测试补丁：{output}")


def launch():
    if PLATFORM == "win32":
        executable = APP_ASAR.parent.parent / "Antigravity.exe"
        if not executable.is_file():
            raise RuntimeError(f"未找到应用程序：{executable}")
    if app_running():
        print("Antigravity 已在运行，不会中断后台任务。若刚更新，请完全退出后再次使用中文启动入口。")
    else:
        apply_patch()
    if PLATFORM == "win32":
        subprocess.Popen([str(executable)], cwd=str(executable.parent))
    else:
        subprocess.run(["/usr/bin/open", "-a", str(APP_ASAR.parents[2])], check=True)


def main():
    global APP_ASAR
    configure_output()
    parser = argparse.ArgumentParser(description="Antigravity 简体中文外置汉化包")
    parser.add_argument("--app", help="Antigravity 安装目录、可执行文件或 app.asar 路径")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="查看补丁状态")
    sub.add_parser("apply", help="备份并安装补丁")
    sub.add_parser("restore", help="恢复原始 app.asar")
    sub.add_parser("launch", help="检查并重装兼容补丁，然后启动应用；不中断运行中的任务")
    build = sub.add_parser("build", help="只生成补丁文件，不修改已安装应用")
    build.add_argument("output", type=Path)
    args = parser.parse_args()
    APP_ASAR = locate_app(args.app)
    if args.command in ("apply", "restore"):
        require_stopped()
    if args.command == "status":
        raise SystemExit(status())
    if args.command == "apply":
        apply_patch()
    elif args.command == "restore":
        restore_patch()
    elif args.command == "build":
        build_copy(args.output)
    elif args.command == "launch":
        launch()


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError, subprocess.SubprocessError, struct.error) as error:
        raise SystemExit(f"汉化操作未完成：{error}")
