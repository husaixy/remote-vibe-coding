import asyncio
import unittest

from ovb_rc003 import app, bridge_control


class _FakeKernel32:
    def __init__(self, *, wait_result=0):
        self.wait_result = wait_result
        self.set_calls = []
        self.closed = []

    def OpenEventW(self, access, inherit, name):
        return 10 if name == bridge_control.STOPPED_EVENT_NAME else 11

    def SetEvent(self, handle):
        self.set_calls.append(handle)
        return True

    def WaitForSingleObject(self, handle, timeout):
        return self.wait_result

    def CloseHandle(self, handle):
        self.closed.append(handle)
        return True


class RequestBridgeStopTests(unittest.TestCase):
    def test_signals_stop_and_waits_for_cleanup_confirmation(self):
        fake = _FakeKernel32(wait_result=bridge_control._WAIT_OBJECT_0)
        original = bridge_control._kernel32
        bridge_control._kernel32 = lambda: fake
        try:
            result = bridge_control.request_bridge_stop(2.0)
        finally:
            bridge_control._kernel32 = original

        self.assertEqual(result.outcome, bridge_control.StopOutcome.STOPPED)
        self.assertEqual(fake.set_calls, [11])
        self.assertEqual(fake.closed, [11, 10])

    def test_timeout_is_reported_without_claiming_stopped(self):
        fake = _FakeKernel32(wait_result=bridge_control._WAIT_TIMEOUT)
        original = bridge_control._kernel32
        bridge_control._kernel32 = lambda: fake
        try:
            result = bridge_control.request_bridge_stop(0.1)
        finally:
            bridge_control._kernel32 = original

        self.assertEqual(result.outcome, bridge_control.StopOutcome.TIMED_OUT)


class AppStopPollingTests(unittest.IsolatedAsyncioTestCase):
    async def test_stop_request_uses_normal_app_cleanup_path(self):
        class FakeApp:
            def __init__(self):
                self.stopped = asyncio.Event()
                self.stop_calls = 0

            async def run_forever(self):
                await self.stopped.wait()

            async def stop(self):
                self.stop_calls += 1
                self.stopped.set()

        fake = FakeApp()
        original = app.RC003App
        app.RC003App = lambda: fake
        try:
            await app._run(lambda: True)
        finally:
            app.RC003App = original

        self.assertGreaterEqual(fake.stop_calls, 1)


if __name__ == "__main__":
    unittest.main()
