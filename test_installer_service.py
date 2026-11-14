import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import json

import patch_asar as core
import installer_service as service
from test_patch_asar import archive


class InstallerStorage(unittest.TestCase):
    def setUp(self):
        core.configure_output()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.app = self.root / 'Antigravity.app/Contents/Resources/app.asar'
        self.app.parent.mkdir(parents=True)
        archive(self.app, '2.32.1')
        self.original = self.app.read_bytes()
        for name in ('APP_ASAR', 'STATE_PATH', 'BACKUP_DIR'):
            p = patch.object(core, name, getattr(core, name))
            p.start()
            self.addCleanup(p.stop)
        p = patch.object(core, 'app_running', return_value=False)
        self.running = p.start()
        self.addCleanup(p.stop)
        service.configure(self.app, self.root / 'user-data')

    def test_install_restore_and_storage_independent_of_download(self):
        service.operate('install')
        self.assertIn('已安装汉化', service.describe())
        self.assertTrue(str(core.STATE_PATH).startswith(str(self.root / 'user-data')))
        service.operate('restore')
        self.assertEqual(self.original, self.app.read_bytes())

    def test_running_app_and_concurrent_installer_are_rejected(self):
        self.running.return_value = True
        with self.assertRaises(RuntimeError):
            service.operate('install')
        self.assertEqual(self.original, self.app.read_bytes())
        self.running.return_value = False
        with service.exclusive():
            with self.assertRaises(RuntimeError):
                service.operate('install')

    def test_state_write_failure_rolls_back_app(self):
        real_write = Path.write_text
        def fail(path, *args, **kwargs):
            if path == core.STATE_PATH:
                raise OSError('disk full')
            return real_write(path, *args, **kwargs)
        with patch.object(Path, 'write_text', fail):
            with self.assertRaises(OSError):
                service.operate('install')
        self.assertEqual(self.original, self.app.read_bytes())
        self.assertFalse(core.STATE_PATH.exists())

    def test_legacy_import_copies_verified_backup(self):
        service.operate('install')
        old_folder = core.STATE_PATH.parent
        old_state = json.loads(core.STATE_PATH.read_text(encoding='utf-8'))
        service.configure(self.app, self.root / 'new-storage')
        with service.exclusive():
            self.assertTrue(service.import_legacy(old_folder))
        new_state = core.read_state()
        self.assertNotEqual(old_state['backup'], new_state['backup'])
        service.operate('restore')
        self.assertEqual(self.original, self.app.read_bytes())
        self.assertTrue(Path(old_state['backup']).exists())

    def test_corrupted_legacy_backup_is_not_imported(self):
        service.operate('install')
        old_folder = core.STATE_PATH.parent
        Path(core.read_state()['backup']).write_bytes(b'corrupted')
        service.configure(self.app, self.root / 'new-storage')
        with self.assertRaises(RuntimeError):
            service.import_legacy(old_folder)
        self.assertFalse(core.STATE_PATH.exists())

    def test_pending_operation_is_preserved(self):
        core.STATE_PATH.parent.mkdir(parents=True)
        pending = core.STATE_PATH.parent / 'pending-app.asar'
        pending.write_bytes(b'recovery')
        with self.assertRaises(RuntimeError):
            service.operate('install')
        self.assertEqual(pending.read_bytes(), b'recovery')
        self.assertEqual(self.original, self.app.read_bytes())

if __name__ == '__main__':
    core.configure_output()
    unittest.main()
