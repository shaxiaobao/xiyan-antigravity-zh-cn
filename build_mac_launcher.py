#!/usr/bin/env python3
"""Build a native macOS launcher; keep it beside the language-pack sources."""
import subprocess
import plistlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = ROOT / "希言 Antigravity 中文启动器.app"
SCRIPT = r'''
on run
    set bundlePath to POSIX path of (path to me)
    set packagePath to do shell script "/usr/bin/dirname " & quoted form of bundlePath
    set installerPath to packagePath & "/patch_asar.py"
    set logPath to packagePath & "/launcher.log"
    try
        do shell script "PATH=/opt/homebrew/bin:/usr/local/bin:/Library/Frameworks/Python.framework/Versions/Current/bin:/usr/bin:/bin /usr/bin/env python3 " & quoted form of installerPath & " launch > " & quoted form of logPath & " 2>&1"
    on error errorMessage
        try
            set errorMessage to do shell script "/usr/bin/tail -c 3000 " & quoted form of logPath
        end try
        display dialog "中文启动未完成：" & return & errorMessage & return & return & "详情见语言包目录中的 launcher.log。请确认 Python 3 已安装，且启动器与语言包文件放在同一文件夹。" with title "希言 Antigravity 中文语言包" buttons {"好"} default button "好"
    end try
end run
'''

if __name__ == "__main__":
    subprocess.run(["/usr/bin/osacompile", "-o", str(APP), "-e", SCRIPT], check=True)
    plist_path = APP / "Contents/Info.plist"
    with plist_path.open("rb") as stream:
        metadata = plistlib.load(stream)
    metadata.update({"CFBundleIdentifier": "cn.xiyan.antigravity.zh-cn.launcher", "CFBundleShortVersionString": "0.2.0", "CFBundleVersion": "2", "CFBundleDevelopmentRegion": "zh_CN"})
    # osacompile adds descriptions for many unrelated permissions; none are used.
    metadata = {key: value for key, value in metadata.items() if not key.endswith("UsageDescription")}
    with plist_path.open("wb") as stream:
        plistlib.dump(metadata, stream)
    subprocess.run(["/usr/bin/codesign", "--force", "--sign", "-", str(APP)], check=True)
    print(APP)
