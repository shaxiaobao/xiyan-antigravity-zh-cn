"""Build a self-contained desktop installer on its target OS."""
import os
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
NAME = 'XiyanAntigravityChinese'

if __name__ == '__main__':
    command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--windowed',
               '--name', NAME, '--osx-bundle-identifier', 'cn.xiyan.antigravity.installer']
    command += ['--onefile'] if sys.platform == 'win32' else ['--onedir']
    for name in ('translations.json', 'translator.js', 'LICENSE', 'manifest.json'):
        command += ['--add-data', f'{ROOT / name}:.']
    command += [str(ROOT / 'installer.py')]
    environment = dict(os.environ, PYINSTALLER_CONFIG_DIR=str(ROOT / "build/pyinstaller-cache"))
    subprocess.run(command, cwd=ROOT, check=True, env=environment)
    print(ROOT / 'dist' / (NAME + ('.exe' if sys.platform == 'win32' else '.app')))
