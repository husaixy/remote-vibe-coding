import unittest

from ovb_rc003 import wechat_input_method as wetype


class _FakeNative:
    def __init__(self):
        self.toolbar = 10
        self.voice = 20
        self.toolbar_visible = True
        self.voice_visible = False
        self.owner = wetype.EXPECTED_PROCESS_NAME
        self.clicks = []
        self.shows = []
        self.hides = []
        self.click_succeeds = True

    def find_window(self, class_name, title):
        if (class_name, title) == (wetype.TOOLBAR_CLASS, wetype.TOOLBAR_TITLE):
            return self.toolbar
        if (class_name, title) == (
            wetype.VOICE_WINDOW_CLASS,
            wetype.VOICE_WINDOW_TITLE,
        ):
            return self.voice
        return 0

    def is_visible(self, hwnd):
        return self.toolbar_visible if hwnd == self.toolbar else self.voice_visible

    def process_name(self, hwnd):
        return self.owner

    def client_size(self, hwnd):
        return (160, 40)

    def show_hidden_toolbar(self, hwnd):
        self.shows.append(hwnd)
        self.toolbar_visible = True
        return True

    def hide_toolbar(self, hwnd):
        self.hides.append(hwnd)
        self.toolbar_visible = False

    def post_left_click(self, hwnd, x, y):
        self.clicks.append((hwnd, x, y))
        if not self.click_succeeds:
            return False
        self.voice_visible = not self.voice_visible
        return True

    def sleep(self, seconds):
        pass


class WeChatInputMethodVoiceToolbarTests(unittest.TestCase):
    def test_voice_button_is_second_of_five_status_bar_items(self):
        self.assertEqual(wetype.voice_button_point(160, 40), (48, 20))

    def test_opens_and_closes_without_duplicate_clicks(self):
        native = _FakeNative()
        self.assertTrue(wetype.set_voice_panel_active(True, _native=native))
        self.assertTrue(native.voice_visible)
        self.assertEqual(native.clicks, [(10, 48, 20)])

        self.assertTrue(wetype.set_voice_panel_active(True, _native=native))
        self.assertEqual(len(native.clicks), 1)

        self.assertTrue(wetype.set_voice_panel_active(False, _native=native))
        self.assertFalse(native.voice_visible)
        self.assertEqual(len(native.clicks), 2)

    def test_rejects_spoofed_owner(self):
        native = _FakeNative()
        native.owner = "not-wetype.exe"
        self.assertFalse(wetype.set_voice_panel_active(True, _native=native))
        self.assertEqual(native.clicks, [])

    def test_hidden_toolbar_is_shown_in_place_then_hidden_again(self):
        native = _FakeNative()
        native.toolbar_visible = False
        self.assertTrue(wetype.set_voice_panel_active(True, _native=native))
        self.assertTrue(native.voice_visible)
        self.assertFalse(native.toolbar_visible)
        self.assertEqual(native.shows, [10])
        self.assertEqual(native.hides, [10])

    def test_hidden_toolbar_is_restored_when_click_fails(self):
        native = _FakeNative()
        native.toolbar_visible = False
        native.click_succeeds = False
        self.assertFalse(wetype.set_voice_panel_active(True, _native=native))
        self.assertFalse(native.toolbar_visible)
        self.assertEqual(native.hides, [10])

    def test_wait_reports_the_observed_voice_panel_state(self):
        native = _FakeNative()
        self.assertTrue(
            wetype.wait_voice_panel_active(
                False, _native=native, timeout_seconds=0
            )
        )
        native.voice_visible = True
        self.assertTrue(
            wetype.wait_voice_panel_active(
                True, _native=native, timeout_seconds=0
            )
        )


if __name__ == "__main__":
    unittest.main()
