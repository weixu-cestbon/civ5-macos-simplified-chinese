import contextlib
import io
import json
import os
from pathlib import Path
import plistlib
import subprocess
import tempfile
import unittest
from unittest import mock

import launch_game as launch


class LaunchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.app = self.root / "Sid Meier's Civilization V" / "Civilization V.app"
        self.executable = self.app / "Contents/MacOS/Civilization V"
        self.executable.parent.mkdir(parents=True)
        with (self.app / "Contents/Info.plist").open("wb") as stream:
            plistlib.dump({"CFBundleIdentifier": launch.BUNDLE_ID}, stream)
        self.executable.write_text("#!/bin/sh\nexit 0\n")
        self.executable.chmod(0o755)

    def test_validate_path_with_spaces_and_apostrophe(self):
        self.assertEqual(launch.validate_app(self.app), self.executable.resolve())

    def test_reject_wrong_edition(self):
        with (self.app / "Contents/Info.plist").open("wb") as stream:
            plistlib.dump({"CFBundleIdentifier": "com.aspyr.civ5campaign"}, stream)
        with self.assertRaisesRegex(ValueError, "Steam macOS"):
            launch.validate_app(self.app)

    def test_reject_missing_executable(self):
        self.executable.unlink()
        with self.assertRaisesRegex(ValueError, "执行文件"):
            launch.validate_app(self.app)

    def test_reject_malformed_plist(self):
        (self.app / "Contents/Info.plist").write_text("not a plist")
        with self.assertRaisesRegex(ValueError, "有效"):
            launch.validate_app(self.app)

    def test_environment_is_scoped_to_child(self):
        source = {"DYLD_INSERT_LIBRARIES": "custom", "SteamAppId": "1", "PATH": "/usr/bin"}
        result = launch.launch_environment(source)
        self.assertEqual(source["DYLD_INSERT_LIBRARIES"], "custom")
        self.assertNotIn("DYLD_INSERT_LIBRARIES", result)
        self.assertEqual(result["SteamAppId"], "8930")
        self.assertEqual(result["SteamGameId"], "8930")
        self.assertEqual(result["PATH"], source["PATH"])

    def test_logs_are_unique_and_private(self):
        first, handle = launch.create_log(self.root / "logs")
        handle.close()
        second, handle = launch.create_log(self.root / "logs")
        handle.close()
        self.assertNotEqual(first, second)
        self.assertEqual(first.stat().st_mode & 0o777, 0o600)

    def test_real_fake_child_receives_environment_cwd_and_logs_exit_code(self):
        # This fixture replaces the game. No Steam or game process is started.
        self.executable.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os, sys\n"
            "print(json.dumps({'cwd': os.getcwd(), 'app': os.environ.get('SteamAppId'), "
            "'game': os.environ.get('SteamGameId'), 'injected': os.environ.get('DYLD_INSERT_LIBRARIES')}))\n"
            "print('fixture stderr', file=sys.stderr)\n"
            "sys.exit(7)\n"
        )
        environment = launch.launch_environment(dict(os.environ, DYLD_INSERT_LIBRARIES="not-loaded"))
        path, log = launch.create_log(self.root / "logs")
        with log:
            result = launch.run_game(self.executable, environment, log)
        self.assertEqual(result, 7)
        lines = path.read_text().splitlines()
        record = next(json.loads(line) for line in lines if line.startswith("{"))
        self.assertEqual(record["cwd"], str(self.executable.parent.resolve()))
        self.assertEqual(record["app"], "8930")
        self.assertEqual(record["game"], "8930")
        self.assertIsNone(record["injected"])
        self.assertIn("fixture stderr", lines)
        self.assertIn("Exit code: 7", lines)

    def test_dry_run_does_not_start_process_or_create_log(self):
        logs = self.root / "never-created"
        with mock.patch.object(launch.sys, "platform", "darwin"), \
                mock.patch.object(launch, "game_is_running") as running, \
                mock.patch.object(launch, "run_game") as start, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(launch.main(["--game", str(self.app), "--logs-dir", str(logs), "--dry-run"]), 0)
            running.assert_not_called()
            start.assert_not_called()
        self.assertFalse(logs.exists())

    def test_running_game_is_not_launched_twice(self):
        with mock.patch.object(launch.sys, "platform", "darwin"), \
                mock.patch.object(launch, "game_is_running", return_value=True), \
                mock.patch.object(launch, "run_game") as start, \
                contextlib.redirect_stderr(io.StringIO()), \
                self.assertRaises(SystemExit) as raised:
            launch.main(["--game", str(self.app)])
        self.assertEqual(raised.exception.code, 1)
        start.assert_not_called()

    def test_process_check_error_is_not_mistaken_for_no_game(self):
        with mock.patch.object(launch.subprocess, "run", return_value=subprocess.CompletedProcess([], 2)):
            with self.assertRaises(RuntimeError):
                launch.game_is_running()

    def test_reject_other_platform(self):
        with mock.patch.object(launch.sys, "platform", "linux"), \
                contextlib.redirect_stderr(io.StringIO()), \
                self.assertRaises(SystemExit) as raised:
            launch.main(["--dry-run"])
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
