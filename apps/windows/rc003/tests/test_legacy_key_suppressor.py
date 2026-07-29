import threading
import unittest

from ovb_rc003 import legacy_key_suppressor_windows as suppressor


class LegacyKeySuppressorDecisionTests(unittest.TestCase):
    def test_suppresses_configured_non_injected_vk(self):
        gate = suppressor.LegacyKeySuppressor({0x74})
        self.assertTrue(gate.should_suppress(0x74, 0))

    def test_does_not_suppress_sendinput_injected_vk(self):
        gate = suppressor.LegacyKeySuppressor({0x74})
        self.assertFalse(gate.should_suppress(0x74, suppressor.LLKHF_INJECTED))

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
