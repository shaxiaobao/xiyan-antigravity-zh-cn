#!/usr/bin/env python3
"""Package only distributable sources and the compiled macOS launcher."""
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def build():
    version = json.loads((ROOT / "manifest.json").read_text())["version"]
    bundle = ROOT / "希言 Antigravity 中文启动器.app"
    if not (bundle / "Contents/Resources/Scripts/main.scpt").is_file():
        raise SystemExit("请先运行 python3 build_mac_launcher.py")
    filenames = ["README.md", "CHANGELOG.md", "manifest.json", "translations.json", "translator.js", "patch_asar.py", "test_patch_asar.py", "build_mac_launcher.py", "build_release.py", "启动 Antigravity 中文版.command"]
    paths = [ROOT / name for name in filenames] + sorted(path for path in bundle.rglob("*") if path.is_file())
    output = ROOT / "release" / f"xiyan-antigravity-zh-cn-v{version}.zip"
    output.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            archive.write(path, "xiyan-antigravity-zh-cn/" + path.relative_to(ROOT).as_posix())
    print(output)


if __name__ == "__main__":
    build()
