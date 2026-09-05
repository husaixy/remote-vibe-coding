import unittest

from ovb_rc003 import codex_window


class _FakeBackend:
    def __init__(
        self,
        *,
        windows=None,
        foreground=0,
        minimized=None,
        activation_succeeds=True,
    ):
        self.windows = list(windows or [])
        self.foreground = foreground
        self.minimized = set(minimized or [])
        self.activation_succeeds = activation_succeeds
        self.restored = []
        self.minimized_calls = []
        self.activated = []

    def codex_windows(self):
        return list(self.windows)

    def foreground_window(self):
        return self.foreground

    def is_minimized(self, hwnd):
        return hwnd in self.minimized

    def restore(self, hwnd):
        self.restored.append(hwnd)
        self.minimized.discard(hwnd)

    def minimize(self, hwnd):
        self.minimized_calls.append(hwnd)

    def activate(self, hwnd):
        self.activated.append(hwnd)
        if self.activation_succeeds:
            self.foreground = hwnd
        return self.activation_succeeds


class _Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class CodexWindowTests(unittest.TestCase):
    def test_matches_only_the_packaged_codex_gui(self):
        self.assertTrue(
            codex_window._is_codex_gui_path(
                "C:/Program Files/WindowsApps/OpenAI.Codex_1_x64__/app/ChatGPT.exe"
            )
        )
        self.assertFalse(
            codex_window._is_codex_gui_path(
                "C:/Program Files/WindowsApps/OpenAI.ChatGPT_1/app/ChatGPT.exe"
            )
        )
        self.assertFalse(
            codex_window._is_codex_gui_path("C:/OpenAI/Codex/bin/codex.exe")
        )

    def test_short_press_minimizes_only_foreground_codex(self):
        backend = _FakeBackend(windows=[10], foreground=10)
        self.assertTrue(codex_window.minimize_if_foreground(_backend=backend))
        self.assertEqual(backend.minimized_calls, [10])

        background = _FakeBackend(windows=[10], foreground=20)
        self.assertFalse(codex_window.minimize_if_foreground(_backend=background))
        self.assertEqual(background.minimized_calls, [])

    def test_focus_restores_minimized_window_then_sends_complete_chord(self):
        backend = _FakeBackend(windows=[10], foreground=20, minimized=[10])
        sent = []
        clock = _Clock()

        result = codex_window.focus_main_chat(
            _backend=backend,
            _hotkey_sender=lambda keys: sent.append(tuple(keys)),
            _clock=clock,
            _sleep=clock.sleep,
        )

        self.assertTrue(result)
        self.assertEqual(backend.restored, [10])
        self.assertEqual(backend.activated, [10])
        self.assertEqual(sent, [codex_window.CODEX_FOCUS_HOTKEY])

    def test_focus_preserves_non_minimized_window_state(self):
        backend = _FakeBackend(windows=[10], foreground=10)
        sent = []
        clock = _Clock()
        self.assertTrue(
            codex_window.focus_main_chat(
                _backend=backend,
                _hotkey_sender=lambda keys: sent.append(tuple(keys)),
                _clock=clock,
                _sleep=clock.sleep,
            )
        )
        self.assertEqual(backend.restored, [])
        self.assertEqual(sent, [codex_window.CODEX_FOCUS_HOTKEY])

    def test_closed_codex_is_launched_and_waited_for(self):
        backend = _FakeBackend()
        launched = []
        sent = []
        clock = _Clock()

        def sleep(seconds):
            clock.sleep(seconds)
            backend.windows = [10]

        result = codex_window.focus_main_chat(
            _backend=backend,
            _launcher=lambda: launched.append(True) or True,
            _hotkey_sender=lambda keys: sent.append(tuple(keys)),
            _clock=clock,
            _sleep=sleep,
        )

        self.assertTrue(result)
        self.assertEqual(launched, [True])
        self.assertEqual(sent, [codex_window.CODEX_FOCUS_HOTKEY])

    def test_launch_timeout_never_sends_shortcut(self):
        backend = _FakeBackend()
        sent = []
        clock = _Clock()
        self.assertFalse(
            codex_window.focus_main_chat(
                _backend=backend,
                _launcher=lambda: True,
                _hotkey_sender=lambda keys: sent.append(tuple(keys)),
                _clock=clock,
                _sleep=clock.sleep,
            )
        )
        self.assertEqual(sent, [])

    def test_activation_failure_never_sends_shortcut(self):
        backend = _FakeBackend(
            windows=[10], foreground=20, activation_succeeds=False
        )
        sent = []
        clock = _Clock()
        self.assertFalse(
            codex_window.focus_main_chat(
                _backend=backend,
                _hotkey_sender=lambda keys: sent.append(tuple(keys)),
                _clock=clock,
                _sleep=clock.sleep,
            )
        )
        self.assertEqual(sent, [])


if __name__ == "__main__":
    unittest.main()
