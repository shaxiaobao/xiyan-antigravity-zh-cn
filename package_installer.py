"""Package installers while preserving macOS framework symlinks."""
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent
if __name__ == '__main__':
    version = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))['version']
    system = 'windows' if sys.platform == 'win32' else 'macos'
    arch = 'arm64' if platform.machine().lower() in ('arm64', 'aarch64') else 'x64'
    output = ROOT / 'release' / f'xiyan-installer-v{version}-{system}-{arch}.zip'
    output.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        stage = Path(temp) / 'Xiyan-Antigravity-Chinese'
        stage.mkdir()
        for name in ('LICENSE', 'README.md', 'CHANGELOG.md'):
            shutil.copy2(ROOT / name, stage / name)
        if system == 'macos':
            bundle = 'XiyanAntigravityChinese.app'
            shutil.copytree(ROOT / 'dist' / bundle, stage / bundle, symlinks=True)
            subprocess.run(['/usr/bin/ditto', '-c', '-k', '--keepParent', str(stage), str(output)], check=True)
        else:
            shutil.copy2(ROOT / 'dist/XiyanAntigravityChinese.exe', stage)
            with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
                for path in stage.rglob('*'):
                    if path.is_file():
                        archive.write(path, path.relative_to(stage.parent))
    print(output)
