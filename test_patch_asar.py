"""Offline regression checks. Never writes to the installed Antigravity app."""
import contextlib
import io
import hashlib
import json
import struct
import sys
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import patch_asar as tool


def archive(path, version, extra=""):
    payloads = {
        "package.json": json.dumps({"version": version}).encode(),
        "dist/utils.js": ("function demo(){\n    void win.loadURL(url);\n}" + extra).encode(),
        "unchanged.txt": b"untouched payload",
    }
    tree = {"files": {}}
    data = bytearray()
    for name, payload in payloads.items():
        branch = tree
        parts = name.split("/")
        for part in parts[:-1]:
            branch = branch["files"].setdefault(part, {"files": {}})
        branch["files"][parts[-1]] = {"size": len(payload), "offset": str(len(data))}
        data.extend(payload)
    header = json.dumps(tree).encode()
    path.write_bytes(struct.pack("<4I", 4, len(header) + 10, len(header) + 6, len(header)) + header + b"\0\0" + data)


class PatchLifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.app = self.root / "Antigravity.app/Contents/Resources/app.asar"
        self.app.parent.mkdir(parents=True)
        archive(self.app, "2.31.2")
        self.injector = "window.testDictionary = 1;"
        for name, value in {"PLATFORM": "darwin", "APP_ASAR": self.app, "BACKUP_DIR": self.root / "backups", "STATE_PATH": self.root / "state.json"}.items():
            patcher = patch.object(tool, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(tool, "load_injector", side_effect=lambda: self.injector)
        patcher.start()
        self.addCleanup(patcher.stop)
        redirect = contextlib.redirect_stdout(io.StringIO())
        redirect.__enter__()
        self.addCleanup(redirect.__exit__, None, None, None)

    def test_install_idempotent_and_restore_exact_bytes(self):
        original = self.app.read_bytes()
        tool.apply_patch()
        installed = self.app.read_bytes()
        tool.apply_patch()
        self.assertEqual(installed, self.app.read_bytes())
        tool.restore_patch()
        self.assertEqual(original, self.app.read_bytes())

    def test_app_update_backs_up_current_version(self):
        tool.apply_patch()
        old_backup = Path(tool.read_state()["backup"])
        archive(self.app, "2.32.1")
        upgraded = self.app.read_bytes()
        tool.apply_patch()
        state = tool.read_state()
        self.assertEqual(state["version"], "2.32.1")
        self.assertTrue(old_backup.exists())
        self.assertNotEqual(old_backup, Path(state["backup"]))
        tool.restore_patch()
        self.assertEqual(self.app.read_bytes(), upgraded)

    def test_dictionary_update_rebuilds_without_nested_injection(self):
        tool.apply_patch()
        self.injector = "window.testDictionary = 2;"
        tool.apply_patch()
        _, source = tool.inspect_app()
        self.assertEqual(source.count(tool.MARKER.encode()), 1)
        self.assertIn(self.injector.encode(), source)

    def test_same_version_unknown_changes_are_preserved(self):
        tool.apply_patch()
        archive(self.app, "2.31.2", "\n// third-party modification")
        modified = self.app.read_bytes()
        with self.assertRaises(RuntimeError):
            tool.apply_patch()
        self.assertEqual(self.app.read_bytes(), modified)

    def test_restore_never_downgrades_an_updated_app(self):
        tool.apply_patch()
        archive(self.app, "2.32.1")
        updated = self.app.read_bytes()
        with self.assertRaises(RuntimeError):
            tool.restore_patch()
        self.assertEqual(self.app.read_bytes(), updated)

    def test_corrupt_backup_is_rejected(self):
        tool.apply_patch()
        Path(tool.read_state()["backup"]).write_bytes(b"corrupt")
        with self.assertRaises(RuntimeError):
            tool.restore_patch()

    def test_build_after_install_and_preserve_other_payloads(self):
        tool.apply_patch()
        installed = self.app.read_bytes()
        output = self.root / "preview.asar"
        tool.build_copy(output)
        self.assertEqual(self.app.read_bytes(), installed)
        _, tree, start, raw = tool.read_archive(output)
        meta = dict(tool.walk_files(tree))["/unchanged.txt"]
        offset = start + int(meta["offset"])
        self.assertEqual(raw[offset:offset + meta["size"]], b"untouched payload")
        with self.assertRaises(RuntimeError):
            tool.build_copy(self.app)

    def test_large_file_integrity_hashes_entire_payload(self):
        payload = b'a' * (4 * 1024 * 1024) + b'second block'
        integrity = tool.build_integrity(payload)
        self.assertEqual(integrity['hash'], hashlib.sha256(payload).hexdigest())
        self.assertEqual(len(integrity['blocks']), 2)
        self.assertNotEqual(integrity['hash'], integrity['blocks'][0])

    def test_launcher_does_not_patch_or_quit_running_app(self):
        with patch.object(tool.subprocess, "run") as run, patch.object(tool, "apply_patch") as apply:
            run.return_value.returncode = 0
            tool.launch()
            apply.assert_not_called()
            self.assertEqual(run.call_args_list[-1].args[0], ["/usr/bin/open", "-a", str(self.app.parents[2])])

    def test_launcher_patches_before_start(self):
        events = []
        with patch.object(tool.subprocess, "run") as run, patch.object(tool, "apply_patch", side_effect=lambda: events.append("patch")):
            def result(args, **kwargs):
                events.append(args[0])
                return type("Result", (), {"returncode": 1})()
            run.side_effect = result
            tool.launch()
            self.assertEqual(events, ["/usr/bin/pgrep", "patch", "/usr/bin/open"])


class WindowsSupport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="中文 language pack ")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.install = self.root / "Programs/Antigravity"
        self.asar = self.install / "resources/app.asar"
        self.asar.parent.mkdir(parents=True)
        archive(self.asar, "2.32.1")
        (self.install / "Antigravity.exe").touch()
        for name, value in {"PLATFORM": "win32", "APP_ASAR": self.asar,
                            "STATE_PATH": self.root / "state.json", "BACKUP_DIR": self.root / "backups"}.items():
            context = patch.object(tool, name, value)
            context.start()
            self.addCleanup(context.stop)

    @unittest.skipUnless(sys.platform == "win32", "Windows CMD integration")
    def test_native_cmd_entry_with_unicode_and_spaces(self):
        launcher = self.root / "启动 中文版.cmd"
        launcher.write_bytes((Path(__file__).parent / "启动 Antigravity 中文版.cmd").read_bytes())
        for name in ("patch_asar.py", "translator.js", "translations.json"):
            (self.root / name).write_bytes((Path(__file__).parent / name).read_bytes())
        environment = dict(os.environ, ANTIGRAVITY_PATH=str(self.install))
        original = self.asar.read_bytes()
        result = subprocess.run(f'call "{launcher}" status', shell=True, stdin=subprocess.DEVNULL,
                                capture_output=True, env=environment, timeout=60)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("尚未安装汉化补丁".encode(), result.stdout)
        self.assertEqual(original, self.asar.read_bytes())

    def test_discovery_and_explicit_paths(self):
        with patch.dict(tool.os.environ, {"LOCALAPPDATA": str(self.root)}, clear=True):
            self.assertEqual(tool.locate_app(), self.asar.resolve())
            for path in [self.install, self.install / "Antigravity.exe", self.asar]:
                self.assertEqual(tool.locate_app(str(path)), self.asar.resolve())
            with patch.dict(tool.os.environ, {"ANTIGRAVITY_PATH": str(self.install)}):
                self.assertEqual(tool.locate_app(), self.asar.resolve())

    def test_ambiguous_installation_is_rejected(self):
        other = self.root / "system/Antigravity/resources/app.asar"
        other.parent.mkdir(parents=True)
        other.write_bytes(self.asar.read_bytes())
        with patch.dict(tool.os.environ, {"LOCALAPPDATA": str(self.root), "ProgramFiles": str(self.root / "system")}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "多个"):
                tool.locate_app()

    def test_process_detection_and_fail_closed(self):
        with patch.object(tool.subprocess, "run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = b'"Antigravity.exe","123","Console","1","1 K"\r\n'
            self.assertTrue(tool.app_running())
            with self.assertRaises(RuntimeError):
                tool.require_stopped()
            run.return_value.stdout = b'"System","4","Services","0","1 K"\r\n'
            self.assertFalse(tool.app_running())
            run.return_value.stdout = b'ERROR'
            with self.assertRaises(RuntimeError):
                tool.app_running()
            run.return_value.returncode = 1
            with self.assertRaises(RuntimeError):
                tool.app_running()

    def test_windows_install_launch_and_restore(self):
        original = self.asar.read_bytes()
        with patch.object(tool, "app_running", return_value=False), patch.object(tool.subprocess, "Popen") as start:
            tool.launch()
            self.assertIn(tool.MARKER.encode(), tool.inspect_app()[1])
            start.assert_called_once_with([str(self.install / "Antigravity.exe")], cwd=str(self.install))
        tool.restore_patch()
        self.assertEqual(self.asar.read_bytes(), original)

    def test_running_windows_app_is_not_modified(self):
        with patch.object(tool, "app_running", return_value=True), patch.object(tool, "apply_patch") as apply, patch.object(tool.subprocess, "Popen"):
            tool.launch()
            apply.assert_not_called()

    def test_missing_windows_executable_is_rejected_before_patch(self):
        (self.install / "Antigravity.exe").unlink()
        with patch.object(tool, "apply_patch") as apply:
            with self.assertRaises(RuntimeError):
                tool.launch()
            apply.assert_not_called()


if __name__ == "__main__":
    unittest.main()
