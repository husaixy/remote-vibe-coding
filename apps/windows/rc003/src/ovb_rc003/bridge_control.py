"""Graceful cross-process stop control for the Windows bridge.

The settings and bridge modes share one executable, so process-name based
termination would also close the settings window. Two per-session named
events provide a narrow control channel instead: settings asks the bridge to
stop, and the bridge confirms only after normal cleanup and mutex release.
"""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from dataclasses import dataclass
from enum import Enum
from typing import Optional

STOP_REQUEST_EVENT_NAME = r"Local\RemoteMicRC003_BridgeStopRequested"
STOPPED_EVENT_NAME = r"Local\RemoteMicRC003_BridgeStopped"
DEFAULT_STOP_TIMEOUT_SECONDS = 10.0

_EVENT_MODIFY_STATE = 0x0002
_SYNCHRONIZE = 0x00100000
_WAIT_OBJECT_0 = 0x00000000
_WAIT_TIMEOUT = 0x00000102
_ERROR_FILE_NOT_FOUND = 2


class BridgeControlUnavailableError(RuntimeError):
    """Raised when the Windows event channel cannot be created or used."""


class StopOutcome(Enum):
    NO_RUNNING_BRIDGE = "no_running_bridge"
    STOPPED = "stopped"
    TIMED_OUT = "timed_out"
    FAILED = "failed"


@dataclass(frozen=True)
class StopResult:
    outcome: StopOutcome
    error: Optional[str] = None


def _kernel32():
    if sys.platform != "win32":
        raise BridgeControlUnavailableError("bridge control is only available on Windows")
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateEventW.argtypes = (
        wintypes.LPVOID,
        wintypes.BOOL,
        wintypes.BOOL,
        wintypes.LPCWSTR,
    )
    kernel32.CreateEventW.restype = wintypes.HANDLE
    kernel32.OpenEventW.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR)
    kernel32.OpenEventW.restype = wintypes.HANDLE
    kernel32.SetEvent.argtypes = (wintypes.HANDLE,)
    kernel32.SetEvent.restype = wintypes.BOOL
    kernel32.ResetEvent.argtypes = (wintypes.HANDLE,)
    kernel32.ResetEvent.restype = wintypes.BOOL
    kernel32.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
    kernel32.WaitForSingleObject.restype = wintypes.DWORD
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL
    return kernel32


def _close_handle(kernel32, handle: int) -> None:
    if handle:
        kernel32.CloseHandle(handle)


class BridgeControlOwner:
    """Owns the stop-request and stopped events for one bridge lifetime."""

    def __init__(self) -> None:
        self._kernel32 = _kernel32()
        self._stop_handle = self._create_event(STOP_REQUEST_EVENT_NAME)
        self._stopped_handle = 0
        try:
            self._stopped_handle = self._create_event(STOPPED_EVENT_NAME)
            if not self._kernel32.ResetEvent(self._stop_handle):
                raise BridgeControlUnavailableError("could not reset bridge stop request")
            if not self._kernel32.ResetEvent(self._stopped_handle):
                raise BridgeControlUnavailableError("could not reset bridge stopped state")
        except Exception:
            self.close()
            raise

    def _create_event(self, name: str) -> int:
        handle = self._kernel32.CreateEventW(None, True, False, name)
        if not handle:
            raise BridgeControlUnavailableError(
                f"CreateEventW failed (GetLastError={ctypes.get_last_error()})"
            )
        return int(handle)

    def stop_requested(self) -> bool:
        return self._kernel32.WaitForSingleObject(self._stop_handle, 0) == _WAIT_OBJECT_0

    def mark_stopped(self) -> None:
        if not self._kernel32.SetEvent(self._stopped_handle):
            raise BridgeControlUnavailableError("could not signal bridge stopped state")

    def close(self) -> None:
        stop_handle = self._stop_handle
        stopped_handle = self._stopped_handle
        self._stop_handle = 0
        self._stopped_handle = 0
        _close_handle(self._kernel32, stopped_handle)
        _close_handle(self._kernel32, stop_handle)


def request_bridge_stop(timeout_seconds: float = DEFAULT_STOP_TIMEOUT_SECONDS) -> StopResult:
    """Request graceful shutdown and wait for its completion signal."""

    try:
        kernel32 = _kernel32()
    except BridgeControlUnavailableError as exc:
        return StopResult(StopOutcome.FAILED, str(exc))

    stopped_handle = kernel32.OpenEventW(_SYNCHRONIZE, False, STOPPED_EVENT_NAME)
    if not stopped_handle:
        error = ctypes.get_last_error()
        if error == _ERROR_FILE_NOT_FOUND:
            return StopResult(StopOutcome.NO_RUNNING_BRIDGE)
        return StopResult(StopOutcome.FAILED, f"OpenEventW failed (GetLastError={error})")

    stop_handle = kernel32.OpenEventW(_EVENT_MODIFY_STATE, False, STOP_REQUEST_EVENT_NAME)
    if not stop_handle:
        error = ctypes.get_last_error()
        _close_handle(kernel32, int(stopped_handle))
        if error == _ERROR_FILE_NOT_FOUND:
            return StopResult(StopOutcome.NO_RUNNING_BRIDGE)
        return StopResult(StopOutcome.FAILED, f"OpenEventW failed (GetLastError={error})")

    try:
        if not kernel32.SetEvent(stop_handle):
            return StopResult(StopOutcome.FAILED, "could not signal the running bridge")
        timeout_ms = max(0, min(int(timeout_seconds * 1000), 0xFFFFFFFE))
        wait_result = kernel32.WaitForSingleObject(stopped_handle, timeout_ms)
        if wait_result == _WAIT_OBJECT_0:
            return StopResult(StopOutcome.STOPPED)
        if wait_result == _WAIT_TIMEOUT:
            return StopResult(StopOutcome.TIMED_OUT)
        return StopResult(StopOutcome.FAILED, f"wait failed (result={wait_result})")
    finally:
        _close_handle(kernel32, int(stop_handle))
        _close_handle(kernel32, int(stopped_handle))
