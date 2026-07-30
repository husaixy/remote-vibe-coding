import threading
import unittest

from ovb_rc003 import legacy_key_suppressor_windows as suppressor


class LegacyKeySuppressorDecisionTests(unittest.TestCase):
    def test_right_alt_transform_event_has_one_physical_identity(self):
        target = suppressor.PhysicalKeyTarget(
            vk_code=0xA5,
            scan_code=0x38,
            extended=True,
            system_key=True,
        )

        down, down_message = suppressor.build_physical_key_event(target, True, 123)
        up, up_message = suppressor.build_physical_key_event(target, False, 124)

        self.assertEqual((down.vkCode, down.scanCode, down.flags, down.time), (0xA5, 0x38, suppressor.LLKHF_EXTENDED, 123))
        self.assertEqual((up.vkCode, up.scanCode, up.flags, up.time), (0xA5, 0x38, suppressor.LLKHF_EXTENDED | suppressor.LLKHF_UP, 124))
        self.assertEqual(down_message, suppressor.WM_SYSKEYDOWN)
        self.assertEqual(up_message, suppressor.WM_SYSKEYUP)

    def test_suppresses_configured_non_injected_vk(self):
        gate = suppressor.LegacyKeySuppressor({0x74})
        self.assertTrue(gate.should_suppress(0x74, 0))

    def test_does_not_suppress_sendinput_injected_vk(self):
        gate = suppressor.LegacyKeySuppressor({0x74})
        self.assertFalse(gate.should_suppress(0x74, suppressor.LLKHF_INJECTED))

    def test_physicalizes_only_marked_right_alt_event(self):
        gate = suppressor.LegacyKeySuppressor({0x74})
        event = suppressor.KBDLLHOOKSTRUCT(
            vkCode=0xA5,
            scanCode=0x38,
            flags=(
                suppressor.LLKHF_EXTENDED
                | suppressor.LLKHF_INJECTED
                | suppressor.LLKHF_LOWER_IL_INJECTED
            ),
            time=123,
            dwExtraInfo=suppressor.VOICE_EVENT_EXTRA_INFO,
        )

        self.assertTrue(gate.physicalize_injected_event(event))
        self.assertEqual(event.flags, suppressor.LLKHF_EXTENDED)
        self.assertEqual(event.dwExtraInfo, 0)

    def test_does_not_physicalize_unmarked_or_other_injected_events(self):
        gate = suppressor.LegacyKeySuppressor({0x74})
        for vk_code, extra_info in (
            (0xA5, 0),
            (0xA4, suppressor.VOICE_EVENT_EXTRA_INFO),
        ):
            event = suppressor.KBDLLHOOKSTRUCT(
                vkCode=vk_code,
                scanCode=0x38,
                flags=suppressor.LLKHF_EXTENDED | suppressor.LLKHF_INJECTED,
                time=123,
                dwExtraInfo=extra_info,
            )
            original = (int(event.flags), int(event.dwExtraInfo))
            self.assertFalse(gate.physicalize_injected_event(event))
            self.assertEqual((int(event.flags), int(event.dwExtraInfo)), original)

    def test_does_not_suppress_unconfigured_vk_codes(self):
        gate = suppressor.LegacyKeySuppressor({0x74})
        self.assertFalse(gate.should_suppress(0x5B, 0))  # VK_LWIN
        self.assertFalse(gate.should_suppress(0x48, 0))  # H

    def test_suppressed_physical_edge_is_forwarded_without_forwarding_injected_input(self):
        events = []
        gate = suppressor.LegacyKeySuppressor(
            {0x74}, on_key_event=lambda vk_code, is_pressed: events.append(
                (vk_code, is_pressed)
            )
        )

        self.assertTrue(gate.handle_key_event(0x74, 0, True))
        self.assertTrue(gate.handle_key_event(0x74, 0, False))
        self.assertFalse(gate.handle_key_event(0x74, suppressor.LLKHF_INJECTED, True))
        self.assertEqual(events, [(0x74, True), (0x74, False)])

    def test_armed_raw_input_edge_is_consumed_once_and_only_with_exact_identity(self):
        gate = suppressor.LegacyKeySuppressor({0x74})
        gate.arm_key_event(0x26, 0x48, True, True)

        self.assertFalse(gate.consume_armed_key_event(0x26, 0x48, False, True))
        self.assertTrue(gate.consume_armed_key_event(0x26, 0x48, True, True))
        self.assertFalse(gate.consume_armed_key_event(0x26, 0x48, True, True))

    def test_armed_five_is_left_to_the_dedicated_voice_suppressor(self):
        gate = suppressor.LegacyKeySuppressor({0x74})
        gate.arm_key_event(0x74, 0x3F, False, True)
        self.assertFalse(gate.consume_armed_key_event(0x74, 0x3F, False, True))


class LegacyKeySuppressorLifecycleTests(unittest.TestCase):
    def test_empty_suppressor_is_a_noop(self):
        gate = suppressor.LegacyKeySuppressor(set())
        gate.start(_run_target=lambda: None)
        self.assertFalse(gate.is_running)

    def test_rejects_second_start_while_thread_is_running(self):
        gate = suppressor.LegacyKeySuppressor({0x74})
        release = threading.Event()

        def fake_run():
            gate._ready_event.set()
            release.wait()

        try:
            gate.start(_run_target=fake_run)
            with self.assertRaises(suppressor.LegacyKeySuppressorUnavailableError):
                gate.start(_run_target=fake_run)
        finally:
            release.set()
            gate.stop()


if __name__ == "__main__":
    unittest.main()
