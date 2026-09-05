import subprocess
import sys
import unittest
from unittest import mock

from ovb_rc003 import pnp_recovery_windows


class PnpRecoveryTests(unittest.TestCase):
    def _run_with_exit(self, exit_code):
        calls = []

        def fake_run(command, **kwargs):
            calls.append((command, kwargs))
            return subprocess.CompletedProcess(command, exit_code)

        with mock.patch.object(sys, "platform", "win32"):
            result = pnp_recovery_windows.enable_single_disabled_remote(_run=fake_run)
        self.assertEqual(len(calls), 1)
        command, kwargs = calls[0]
        self.assertEqual(command[0], "powershell.exe")
        self.assertNotIn("shell", kwargs)
        return result

    def test_enables_exactly_one_disabled_remote(self):
        self.assertIs(
            self._run_with_exit(0), pnp_recovery_windows.RecoveryStatus.ENABLED
        )

    def test_reports_no_disabled_remote(self):
        self.assertIs(
            self._run_with_exit(2), pnp_recovery_windows.RecoveryStatus.NOT_DISABLED
        )

    def test_refuses_ambiguous_remote_devices(self):
        self.assertIs(
            self._run_with_exit(3), pnp_recovery_windows.RecoveryStatus.AMBIGUOUS
        )

    def test_reports_when_enable_requires_elevation(self):
        self.assertIs(
            self._run_with_exit(4),
            pnp_recovery_windows.RecoveryStatus.NEEDS_ELEVATION,
        )

    def test_process_failure_is_nonfatal(self):
        def fail(*_args, **_kwargs):
            raise OSError("unavailable")

        with mock.patch.object(sys, "platform", "win32"):
            result = pnp_recovery_windows.enable_single_disabled_remote(_run=fail)
        self.assertIs(result, pnp_recovery_windows.RecoveryStatus.FAILED)

    def test_non_windows_does_not_start_a_process(self):
        with mock.patch.object(sys, "platform", "linux"):
            result = pnp_recovery_windows.enable_single_disabled_remote(
                _run=lambda *_args, **_kwargs: self.fail("must not run")
            )
        self.assertIs(result, pnp_recovery_windows.RecoveryStatus.UNAVAILABLE)

    def test_elevated_command_uses_hidden_repair_entrypoint(self):
        calls = []
        with mock.patch.object(sys, "platform", "win32"):
            started = pnp_recovery_windows.request_elevated_recovery(
                frozen=True,
                executable=r"C:\Apps\RemoteMicRC003.exe",
                _launch=lambda executable, parameters, directory: (
                    calls.append((executable, parameters, directory)) or 33
                ),
            )
        self.assertTrue(started)
        self.assertEqual(calls[0][0], r"C:\Apps\RemoteMicRC003.exe")
        self.assertIn("--repair-disabled-remote", calls[0][1])
