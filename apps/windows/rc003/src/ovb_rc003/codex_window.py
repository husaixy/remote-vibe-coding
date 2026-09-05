"""Public Win32 integration for the installed Codex desktop window."""

from __future__ import annotations

import ctypes
import logging
import sys
import time
from ctypes import wintypes
from typing import Callable, List, Optional, Protocol, Sequence

from . import action_executor, key_mapping, win32_input


CODEX_FOCUS_HOTKEY = ("lctrl", "lalt", "lshift", "f12")
WINDOW_START_TIMEOUT_SECONDS = 8.0
FOREGROUND_TIMEOUT_SECONDS = 1.0
POLL_SECONDS = 0.05

_LOGGER = logging.getLogger(__name__)
_WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


class WindowBackend(Protocol):
    def codex_windows(self) -> List[int]: ...

    def foreground_window(self) -> int: ...

    def is_minimized(self, hwnd: int) -> bool: ...

    def restore(self, hwnd: int) -> None: ...

    def minimize(self, hwnd: int) -> None: ...

    def activate(self, hwnd: int) -> bool: ...


def _is_codex_gui_path(path: str) -> bool:
    normalized = str(path).replace("/", "\\").casefold()
    return normalized.endswith("\\app\\chatgpt.exe") and (
        "\\windowsapps\\openai.codex_" in normalized
    )


class _Win32Backend:
    GW_OWNER = 4
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    SW_MINIMIZE = 6
    SW_RESTORE = 9

    def __init__(self) -> None:
        if sys.platform != "win32":
            raise OSError("Codex window control is only available on Windows")
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._configure_signatures()

    def _configure_signatures(self) -> None:
        self.user32.EnumWindows.argtypes = (_WNDENUMPROC, wintypes.LPARAM)
        self.user32.EnumWindows.restype = wintypes.BOOL
        self.user32.GetWindow.argtypes = (wintypes.HWND, wintypes.UINT)
        self.user32.GetWindow.restype = wintypes.HWND
        self.user32.GetWindowThreadProcessId.argtypes = (
            wintypes.HWND,
            ctypes.POINTER(wintypes.DWORD),
        )
        self.user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        self.user32.GetForegroundWindow.restype = wintypes.HWND
        self.user32.IsWindowVisible.argtypes = (wintypes.HWND,)
        self.user32.IsWindowVisible.restype = wintypes.BOOL
        self.user32.IsIconic.argtypes = (wintypes.HWND,)
        self.user32.IsIconic.restype = wintypes.BOOL
        self.user32.ShowWindowAsync.argtypes = (wintypes.HWND, ctypes.c_int)
        self.user32.ShowWindowAsync.restype = wintypes.BOOL
        self.user32.BringWindowToTop.argtypes = (wintypes.HWND,)
        self.user32.BringWindowToTop.restype = wintypes.BOOL
        self.user32.SetForegroundWindow.argtypes = (wintypes.HWND,)
        self.user32.SetForegroundWindow.restype = wintypes.BOOL
        self.user32.AttachThreadInput.argtypes = (
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.BOOL,
        )
        self.user32.AttachThreadInput.restype = wintypes.BOOL
        self.kernel32.OpenProcess.argtypes = (
            wintypes.DWORD,
            wintypes.BOOL,
            wintypes.DWORD,
        )
        self.kernel32.OpenProcess.restype = wintypes.HANDLE
        self.kernel32.QueryFullProcessImageNameW.argtypes = (
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
        )
        self.kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
        self.kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
        self.kernel32.CloseHandle.restype = wintypes.BOOL
        self.kernel32.GetCurrentThreadId.restype = wintypes.DWORD

    def _process_path(self, hwnd: int) -> str:
        process_id = wintypes.DWORD()
        self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
        if not process_id.value:
            return ""
        handle = self.kernel32.OpenProcess(
            self.PROCESS_QUERY_LIMITED_INFORMATION, False, process_id.value
        )
        if not handle:
            return ""
        try:
            size = wintypes.DWORD(32768)
            buffer = ctypes.create_unicode_buffer(size.value)
            if not self.kernel32.QueryFullProcessImageNameW(
                handle, 0, buffer, ctypes.byref(size)
            ):
                return ""
            return buffer.value
        finally:
            self.kernel32.CloseHandle(handle)

    def codex_windows(self) -> List[int]:
        windows: List[int] = []

        @_WNDENUMPROC
        def callback(hwnd: int, _lparam: int) -> bool:
            if (
                self.user32.IsWindowVisible(hwnd)
                and not self.user32.GetWindow(hwnd, self.GW_OWNER)
                and _is_codex_gui_path(self._process_path(hwnd))
            ):
                windows.append(int(hwnd))
            return True

        if not self.user32.EnumWindows(callback, 0):
            raise ctypes.WinError(ctypes.get_last_error())
        return windows

    def foreground_window(self) -> int:
        return int(self.user32.GetForegroundWindow() or 0)

    def is_minimized(self, hwnd: int) -> bool:
        return bool(self.user32.IsIconic(hwnd))

    def restore(self, hwnd: int) -> None:
        self.user32.ShowWindowAsync(hwnd, self.SW_RESTORE)

    def minimize(self, hwnd: int) -> None:
        self.user32.ShowWindowAsync(hwnd, self.SW_MINIMIZE)

    def activate(self, hwnd: int) -> bool:
        foreground = self.foreground_window()
        if foreground == hwnd:
            return True

        current_thread = int(self.kernel32.GetCurrentThreadId())
        target_thread = int(self.user32.GetWindowThreadProcessId(hwnd, None))
        foreground_thread = (
            int(self.user32.GetWindowThreadProcessId(foreground, None))
            if foreground
            else 0
        )
        attached: List[int] = []
        try:
            for thread_id in (foreground_thread, target_thread):
                if thread_id and thread_id != current_thread and thread_id not in attached:
                    if self.user32.AttachThreadInput(current_thread, thread_id, True):
                        attached.append(thread_id)
            self.user32.BringWindowToTop(hwnd)
            self.user32.SetForegroundWindow(hwnd)
        finally:
            for thread_id in reversed(attached):
                self.user32.AttachThreadInput(current_thread, thread_id, False)
        return self.foreground_window() == hwnd


def _backend_or_none(backend: Optional[WindowBackend]) -> Optional[WindowBackend]:
    if backend is not None:
        return backend
    try:
        return _Win32Backend()
    except OSError as exc:
        _LOGGER.warning("Codex window integration unavailable: %s", exc)
        return None


def minimize_if_foreground(*, _backend: Optional[WindowBackend] = None) -> bool:
    """Minimize Codex only when its own top-level window is foreground."""

    backend = _backend_or_none(_backend)
    if backend is None:
        return False
    foreground = backend.foreground_window()
    if not foreground or foreground not in backend.codex_windows():
        _LOGGER.info("Codex minimize ignored: Codex is not foreground")
        return False
    backend.minimize(foreground)
    _LOGGER.info("Codex foreground window minimized")
    return True


def focus_main_chat(
    *,
    _backend: Optional[WindowBackend] = None,
    _launcher: Optional[Callable[[], bool]] = None,
    _hotkey_sender: Optional[Callable[[Sequence[str]], None]] = None,
    _clock: Callable[[], float] = time.monotonic,
    _sleep: Callable[[float], None] = time.sleep,
) -> bool:
    """Restore or start Codex, then send its configured composer shortcut."""

    backend = _backend_or_none(_backend)
    if backend is None:
        return False
    windows = backend.codex_windows()
    if not windows:
        launcher = _launcher or (
            lambda: action_executor.open_configured_application(
                key_mapping.ButtonAction(key_mapping.ActionKind.OPEN_CODEX)
            )
        )
        try:
            started = launcher()
        except OSError:
            _LOGGER.exception("Codex launch failed")
            return False
        if not started:
            _LOGGER.warning("Codex launch failed: desktop application not installed")
            return False
        deadline = _clock() + WINDOW_START_TIMEOUT_SECONDS
        while _clock() < deadline:
            windows = backend.codex_windows()
            if windows:
                break
            _sleep(POLL_SECONDS)
        if not windows:
            _LOGGER.warning("Codex launch timed out before a desktop window appeared")
            return False

    hwnd = windows[0]
    if backend.is_minimized(hwnd):
        backend.restore(hwnd)
    if backend.foreground_window() != hwnd and not backend.activate(hwnd):
        _LOGGER.warning("Codex foreground activation was rejected by Windows")
        return False

    deadline = _clock() + FOREGROUND_TIMEOUT_SECONDS
    while backend.foreground_window() != hwnd and _clock() < deadline:
        _sleep(POLL_SECONDS)
    if backend.foreground_window() != hwnd:
        _LOGGER.warning("Codex focus shortcut withheld: another app is foreground")
        return False

    _sleep(0.1)
    sender = _hotkey_sender or win32_input.send_key_combo_tap
    sender(CODEX_FOCUS_HOTKEY)
    _LOGGER.info(
        "Codex focus shortcut sent; Codex must bind Ctrl+Alt+Shift+F12 "
        "to Focus main chat"
    )
    return True
