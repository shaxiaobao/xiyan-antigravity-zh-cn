#!/usr/bin/env python3
"""Install, inspect, and restore the external Antigravity Simplified Chinese patch."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import struct
import tempfile
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
APP_ASAR = Path("/Applications/Antigravity.app/Contents/Resources/app.asar")
BACKUP_DIR = PACKAGE_DIR / "backups"
STATE_PATH = PACKAGE_DIR / "patch-state.json"
TARGET_PATH = "/dist/utils.js"
MARKER = "__ANTIGRAVITY_ZH_CN_EXTERNAL_PATCH__"


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
        "hash": blocks[0],
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
    return (PACKAGE_DIR / "translator.js").read_text(encoding="utf-8")


def read_state():
    if not STATE_PATH.exists():
        return None
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def status():
    if not APP_ASAR.exists():
        print(f"未找到 Antigravity: {APP_ASAR}")
        return 1
    current = sha256(APP_ASAR)
    state = read_state()
    if state and current == state.get("patchedSha256"):
        print(f"已安装简体中文补丁：Antigravity {state['version']}")
        print(f"当前 app.asar: {current}")
        return 0
    if state and current == state.get("originalSha256"):
        print("未安装补丁（当前是原始 app.asar）。")
        return 0
    print(f"当前 app.asar 未匹配已记录版本：{current}")
    print("可能是应用更新或外部修改，请先运行 build 检查。")
    return 2


def apply_patch():
    if not APP_ASAR.exists():
        raise RuntimeError(f"未找到 Antigravity: {APP_ASAR}")
    original_hash = sha256(APP_ASAR)
    previous = read_state()
    if previous and original_hash == previous.get("patchedSha256"):
        print("补丁已经安装，无需重复操作。")
        return
    if previous and original_hash != previous.get("originalSha256"):
        raise RuntimeError("检测到 app.asar 与上次记录不一致。请先运行 restore，或删除旧状态后重新检查版本。")

    version = "unknown"
    package_json = PACKAGE_DIR / "detected-version.json"
    backup_name = f"app.asar.{original_hash[:12]}.original"
    backup_path = BACKUP_DIR / backup_name
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if not backup_path.exists():
        shutil.copy2(APP_ASAR, backup_path)

    _, tree, data_start, raw = read_archive(APP_ASAR)
    for path, metadata in walk_files(tree):
        if path == "/package.json":
            package_data = raw[data_start + int(metadata["offset"]) : data_start + int(metadata["offset"]) + int(metadata["size"])]
            version = json.loads(package_data.decode("utf-8")).get("version", version)
            break

    target = next(metadata for path, metadata in walk_files(tree) if path == TARGET_PATH)
    old_utils = raw[data_start + int(target["offset"]) : data_start + int(target["offset"]) + int(target["size"])]
    patched_utils = patch_utils_source(old_utils, load_injector())
    with tempfile.NamedTemporaryFile(prefix="antigravity-zh-cn-", suffix=".asar", dir=APP_ASAR.parent, delete=False) as temp:
        temp_path = Path(temp.name)
    try:
        repack_archive(APP_ASAR, temp_path, patched_utils)
        patched_hash = sha256(temp_path)
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
    shutil.copy2(backup, APP_ASAR)
    STATE_PATH.unlink(missing_ok=True)
    print("已恢复 Antigravity 原始 app.asar。请重新启动应用。")


def build_copy(output: Path):
    if not APP_ASAR.exists():
        raise RuntimeError(f"未找到 Antigravity: {APP_ASAR}")
    _, tree, data_start, raw = read_archive(APP_ASAR)
    target = next(metadata for path, metadata in walk_files(tree) if path == TARGET_PATH)
    old_utils = raw[data_start + int(target["offset"]) : data_start + int(target["offset"]) + int(target["size"])]
    patched_utils = patch_utils_source(old_utils, load_injector())
    repack_archive(APP_ASAR, output, patched_utils)
    print(f"已生成测试补丁：{output}")


def main():
    parser = argparse.ArgumentParser(description="Antigravity 简体中文外置汉化包")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="查看补丁状态")
    sub.add_parser("apply", help="备份并安装补丁")
    sub.add_parser("restore", help="恢复原始 app.asar")
    build = sub.add_parser("build", help="只生成补丁文件，不修改已安装应用")
    build.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.command == "status":
        raise SystemExit(status())
    if args.command == "apply":
        apply_patch()
    elif args.command == "restore":
        restore_patch()
    elif args.command == "build":
        build_copy(args.output)


if __name__ == "__main__":
    main()
