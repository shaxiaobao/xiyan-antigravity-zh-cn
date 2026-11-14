"""Persistent, per-installation storage for the standalone installer."""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

import patch_asar as patch


def data_root():
    if sys.platform == 'win32':
        return Path(os.environ['LOCALAPPDATA']) / 'XiyanAntigravityChinese'
    return Path.home() / 'Library/Application Support/XiyanAntigravityChinese'


def configure(target, root=None):
    patch.APP_ASAR = patch.normalize_app_path(target)
    identity = hashlib.sha256(os.path.normcase(str(patch.APP_ASAR)).encode()).hexdigest()[:20]
    folder = (root or data_root()) / identity
    patch.STATE_PATH = folder / 'patch-state.json'
    patch.BACKUP_DIR = folder / 'backups'
    return folder


@contextlib.contextmanager
def exclusive():
    folder = patch.STATE_PATH.parent
    folder.mkdir(parents=True, exist_ok=True)
    lock = folder / 'operation.lock'
    try:
        lock.mkdir()
    except FileExistsError:
        raise RuntimeError(f'另一个安装操作正在进行，或上次操作异常中断。请关闭其他安装器后检查：{lock}')
    try:
        yield
    finally:
        lock.rmdir()


def import_legacy(folder):
    """Copy verified original bytes, never import arbitrary paths as active state."""
    if patch.STATE_PATH.exists():
        return False
    source = Path(folder) / 'patch-state.json'
    if not source.is_file():
        return False
    state = json.loads(source.read_text(encoding='utf-8'))
    if patch.sha256(patch.APP_ASAR) != state.get('patchedSha256'):
        raise RuntimeError('旧版记录与当前应用不一致，请选择当时实际安装的语言包目录。')
    backup = Path(state['backup'])
    if not backup.is_file():
        backup = Path(folder) / 'backups' / backup.name
    if not backup.is_file() or patch.sha256(backup) != state.get('originalSha256'):
        raise RuntimeError('旧版原始备份缺失或校验失败，未导入。')
    patch.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    destination = patch.BACKUP_DIR / f"app.asar.{state['originalSha256'][:12]}.original"
    shutil.copy2(backup, destination)
    state.update(backup=str(destination), target=str(patch.APP_ASAR))
    patch.STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    return True


def describe():
    version, source = patch.inspect_app()
    state = patch.read_state()
    current = patch.sha256(patch.APP_ASAR)
    if state and current == state.get('patchedSha256'):
        return f'Antigravity {version} · 已安装汉化'
    if patch.MARKER.encode() in source:
        return f'Antigravity {version} · 需要导入旧版备份'
    return f'Antigravity {version} · 可安装或修复汉化'


def operate(action):
    if action not in ('install', 'restore'):
        raise ValueError(action)
    with exclusive():
        patch.require_stopped()
        # Keep the current bytes until application AND state writes have succeeded.
        folder = patch.STATE_PATH.parent
        rollback = folder / 'pending-app.asar'
        pending_state = folder / 'pending-state.json'
        if rollback.exists():
            raise RuntimeError(f'发现未完成操作的恢复文件，请先排查，未覆盖应用：{rollback}')
        previous_state = patch.STATE_PATH.read_bytes() if patch.STATE_PATH.exists() else None
        shutil.copy2(patch.APP_ASAR, rollback)
        if previous_state is not None:
            pending_state.write_bytes(previous_state)
        try:
            if action == 'install':
                patch.apply_patch()
            else:
                patch.restore_patch()
        except Exception:
            # Restore by atomic replace in the application's own filesystem.
            fd, name = tempfile.mkstemp(prefix='xiyan-rollback-', dir=patch.APP_ASAR.parent)
            os.close(fd)
            temporary = Path(name)
            try:
                shutil.copy2(rollback, temporary)
                os.replace(temporary, patch.APP_ASAR)
                if previous_state is None:
                    patch.STATE_PATH.unlink(missing_ok=True)
                else:
                    patch.STATE_PATH.write_bytes(previous_state)
            finally:
                temporary.unlink(missing_ok=True)
            rollback.unlink()
            pending_state.unlink(missing_ok=True)
            raise
        rollback.unlink()
        pending_state.unlink(missing_ok=True)


def open_app():
    # Opening the original application never installs or repairs anything.
    if patch.PLATFORM == 'win32':
        exe = patch.APP_ASAR.parent.parent / 'Antigravity.exe'
        if not exe.is_file():
            raise RuntimeError(f'找不到应用：{exe}')
        patch.subprocess.Popen([str(exe)], cwd=str(exe.parent))
    else:
        patch.subprocess.run(['/usr/bin/open', '-a', str(patch.APP_ASAR.parents[2])], check=True)
