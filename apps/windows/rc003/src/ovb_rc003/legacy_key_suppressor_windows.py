"""Suppress legacy keyboard events that leak from RC003 HID buttons.

Raw Input lets this app identify RC003 button presses, but Windows may also
deliver the same translated HID Keyboard-page usage to the foreground app as a
normal legacy keyboard event. The real RC003 microphone key does this as F5.

This module installs a narrow low-level keyboard hook that swallows only the
configured non-injected virtual-key codes. SendInput-generated keys carry the
LLKHF_INJECTED flag, so the app's own Win+H voice hotkey is allowed through.
"""

from __future__ import annotations

import ctypes
import sys
import threading
from ctypes import wintypes
from typing import Callable, FrozenSet, Optional


WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
LLKHF_INJECTED = 0x00000010


class LegacyKeySuppressorUnavailableError(Exception):
    """Raised when the Windows low-level keyboard hook cannot be started."""


def _require_windows() -> None:
    if sys.platform != "win32":
        raise LegacyKeySuppressorUnavailableError(
            "legacy key suppression is only available on Windows"
        )


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class LegacyKeySuppressor:
    def __init__(self, suppress_vk_codes) -> None:
        self._suppress_vk_codes: FrozenSet[int] = frozenset(int(vk) for vk in suppress_vk_codes)
        self._thread: Optional[threading.Thread] = None
        self._ready_event = threading.Event()
        self._stop_event = threading.Event()
        self._start_error: Optional[BaseException] = None
        self._thread_id = wintypes.DWORD(0)
        self._hook = None
        self._hookproc_keepalive = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def should_suppress(self, vk_code: int, flags: int) -> bool:
        if flags & LLKHF_INJECTED:
            return False
        return int(vk_code) in self._suppress_vk_codes

    def start(
        self,
        *,
        start_timeout: float = 5.0,
        _run_target: Optional[Callable[[], None]] = None,
    ) -> None:
        if self.is_running:
            raise LegacyKeySuppressorUnavailableError(
                "legacy key suppressor is already running; call stop() first"
            )
        if not self._suppress_vk_codes:
            return
        if _run_target is None:
            _require_windows()
        self._ready_event.clear()
        self._stop_event.clear()
        self._start_error = None
        self._thread = threading.Thread(target=_run_target or self._run, daemon=True)
        self._thread.start()
        if not self._ready_event.wait(timeout=start_timeout):
            self._stop_event.set()
            self._thread.join(timeout=2.0)
            raise LegacyKeySuppressorUnavailableError(
                f"legacy key suppressor did not become ready within {start_timeout}s"
            )
        if self._start_error is not None:
            error = self._start_error
            self._thread = None
            raise error

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is None:
            return
        if sys.platform == "win32" and self._thread_id.value:
            user32 = ctypes.windll.user32  # type: ignore[attr-defined]
            user32.PostThreadMessageW.argtypes = (
                wintypes.DWORD,
                wintypes.UINT,
                wintypes.WPARAM,
                wintypes.LPARAM,
            )
            user32.PostThreadMessageW.restype = wintypes.BOOL
            user32.PostThreadMessageW(self._thread_id.value, 0x0012, 0, 0)  # WM_QUIT
        self._thread.join(timeout=2.0)
        if self._thread.is_alive():
            raise LegacyKeySuppressorUnavailableError(
                "legacy key suppressor thread did not stop within 2.0s"
            )
        self._thread = None
        self._thread_id = wintypes.DWORD(0)

    def _run(self) -> None:
        try:
            user32 = ctypes.windll.user32  # type: ignore[attr-defined]
            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]

            LRESULT = ctypes.c_ssize_t
            HOOKPROC = ctypes.WINFUNCTYPE(
                LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM
            )
            hookproc = HOOKPROC(self._hookproc)
            self._hookproc_keepalive = hookproc

            kernel32.GetCurrentThreadId.argtypes = ()
            kernel32.GetCurrentThreadId.restype = wintypes.DWORD
            self._thread_id = wintypes.DWORD(kernel32.GetCurrentThreadId())

            kernel32.GetModuleHandleW.argtypes = (wintypes.LPCWSTR,)
            kernel32.GetModuleHandleW.restype = wintypes.HMODULE

            user32.SetWindowsHookExW.argtypes = (
                ctypes.c_int,
                HOOKPROC,
                wintypes.HINSTANCE,
                wintypes.DWORD,
            )
            user32.SetWindowsHookExW.restype = wintypes.HHOOK

            user32.UnhookWindowsHookEx.argtypes = (wintypes.HHOOK,)
            user32.UnhookWindowsHookEx.restype = wintypes.BOOL

            self._hook = user32.SetWindowsHookExW(
                WH_KEYBOARD_LL, hookproc, kernel32.GetModuleHandleW(None), 0
            )
            if not self._hook:
                raise LegacyKeySuppressorUnavailableError("SetWindowsHookExW failed")

            self._ready_event.set()

            msg = wintypes.MSG()
            user32.GetMessageW.argtypes = (
                ctypes.POINTER(wintypes.MSG),
                wintypes.HWND,
                wintypes.UINT,
                wintypes.UINT,
            )
            user32.GetMessageW.restype = ctypes.c_int
            while not self._stop_event.is_set():
                result = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if result <= 0:
                    break
        except BaseException as exc:  # noqa: BLE001 - surfaced to start()
            self._start_error = exc
            self._ready_event.set()
        finally:
            if self._hook:
                try:
                    ctypes.windll.user32.UnhookWindowsHookEx(self._hook)  # type: ignore[attr-defined]
                except Exception:
                    pass
                self._hook = None

    def _hookproc(self, n_code, w_param, l_param):
        user32 = ctypes.windll.user32  # type: ignore[attr-defined]
        user32.CallNextHookEx.argtypes = (
            wintypes.HHOOK,
            ctypes.c_int,
            wintypes.WPARAM,
            wintypes.LPARAM,
        )
        user32.CallNextHookEx.restype = ctypes.c_ssize_t
        if n_code >= 0 and int(w_param) in (
            WM_KEYDOWN,
            WM_KEYUP,
            WM_SYSKEYDOWN,
            WM_SYSKEYUP,
        ):
            event = KBDLLHOOKSTRUCT.from_address(int(l_param))
            if self.should_suppress(event.vkCode, event.flags):
                return 1
        return user32.CallNextHookEx(self._hook, n_code, w_param, l_param)
