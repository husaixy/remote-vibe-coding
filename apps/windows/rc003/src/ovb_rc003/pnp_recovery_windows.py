"""Recover a disabled paired RC001/RC003 Bluetooth device on Windows."""

from __future__ import annotations

import enum
import ctypes
import subprocess
import sys
from ctypes import wintypes
from pathlib import Path
from typing import Callable


class RecoveryStatus(enum.Enum):
    ENABLED = "enabled"
    NOT_DISABLED = "not_disabled"
    AMBIGUOUS = "ambiguous"
    FAILED = "failed"
    NEEDS_ELEVATION = "needs_elevation"
    UNAVAILABLE = "unavailable"


_ENABLE_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
$names = @(
    'mi rc',
    'xiaomi bluetooth remote 2',
    'xiaomi bluetooth remote 2 pro',
    '小米蓝牙语音遥控器'
)
$devices = @(
    Get-PnpDevice -PresentOnly -Class Bluetooth -ErrorAction Stop |
        Where-Object {
            $_.FriendlyName -and
            $names -contains $_.FriendlyName.ToLowerInvariant()
        }
)
if ($devices.Count -gt 1) { exit 3 }
if ($devices.Count -ne 1) { exit 2 }
$problem = (Get-PnpDeviceProperty -InstanceId $devices[0].InstanceId `
    -KeyName 'DEVPKEY_Device_ProblemCode' -ErrorAction Stop).Data
if ($problem -ne 22) { exit 2 }
try {
    Enable-PnpDevice -InstanceId $devices[0].InstanceId `
        -Confirm:$false -ErrorAction Stop
} catch {
    exit 4
}
exit 0
"""

SW_HIDE = 0
SHELL_SUCCESS_MINIMUM = 32


def enable_single_disabled_remote(
    *,
    _run: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> RecoveryStatus:
    """Enable the sole present matching remote, but only for problem code 22."""

    if sys.platform != "win32":
        return RecoveryStatus.UNAVAILABLE
    try:
        completed = _run(
            [
                "powershell.exe",
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                _ENABLE_SCRIPT,
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10.0,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.SubprocessError):
        return RecoveryStatus.FAILED
    if completed.returncode == 0:
        return RecoveryStatus.ENABLED
    if completed.returncode == 2:
        return RecoveryStatus.NOT_DISABLED
    if completed.returncode == 3:
        return RecoveryStatus.AMBIGUOUS
    if completed.returncode == 4:
        return RecoveryStatus.NEEDS_ELEVATION
    return RecoveryStatus.FAILED


def _shell_execute_elevated(executable: str, parameters: str, directory: str) -> int:
    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    shell32.ShellExecuteW.argtypes = (
        wintypes.HWND,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        ctypes.c_int,
    )
    shell32.ShellExecuteW.restype = wintypes.HINSTANCE
    result = shell32.ShellExecuteW(
        None, "runas", executable, parameters, directory, SW_HIDE
    )
    return int(ctypes.cast(result, ctypes.c_void_p).value or 0)


def request_elevated_recovery(
    *,
    frozen: bool | None = None,
    executable: str | None = None,
    _launch: Callable[[str, str, str], int] = _shell_execute_elevated,
) -> bool:
    """Start the same application as a short-lived, explicit UAC helper."""

    if sys.platform != "win32":
        return False
    if frozen is None:
        frozen = bool(getattr(sys, "frozen", False))
    if executable is None:
        executable = sys.executable
    if not executable:
        return False
    arguments = ["--repair-disabled-remote"]
    if not frozen:
        arguments = ["-m", "ovb_rc003", *arguments]
    result = _launch(
        executable,
        subprocess.list2cmdline(arguments),
        str(Path(executable).parent),
    )
    return result > SHELL_SUCCESS_MINIMUM


def prepare_explicit_restart_recovery() -> RecoveryStatus:
    """Repair directly when allowed, otherwise request the narrow UAC helper."""

    status = enable_single_disabled_remote()
    if status is RecoveryStatus.NEEDS_ELEVATION:
        if request_elevated_recovery():
            return RecoveryStatus.ENABLED
        return RecoveryStatus.FAILED
    return status


def elevated_recovery_main() -> int:
    """Hidden helper entry point; the parent already requested UAC explicitly."""

    status = enable_single_disabled_remote()
    return 0 if status in {RecoveryStatus.ENABLED, RecoveryStatus.NOT_DISABLED} else 1
