"""Writes decoded ATVV PCM to the one user-selected Windows output endpoint.

Windows-only (``sounddevice``/PortAudio). Never touches the system default
device: it always opens the specific endpoint the user picked by name, and
raises immediately if that endpoint can't be opened - callers must treat
that as "voice fails closed, buttons keep working" (see audio_output.py).
"""

from __future__ import annotations

from typing import List, Optional

from . import audio_output

SOURCE_SAMPLE_RATE_HZ = 16000
CHANNELS = 1


class PlaybackUnavailableError(Exception):
    pass


class EndpointPlaybackSink:
    """Opens one output stream bound to a specific, already-resolved endpoint
    and accepts decoded int16 PCM sample batches to play.

    Endpoint identity is (name, host_api) - matching audio_output.py's
    disambiguation contract - since a bare display name is not always unique
    across PortAudio host APIs (e.g. the same physical device can appear
    once under WASAPI and once under MME).
    """

    def __init__(self, endpoint_name: str, host_api: str = "") -> None:
        self._endpoint_name = endpoint_name
        self._host_api = host_api
        self._stream = None
        self._output_sample_rate_hz = SOURCE_SAMPLE_RATE_HZ

    def open(self) -> None:
        try:
            import sounddevice as sd  # type: ignore
        except ImportError as exc:  # pragma: no cover - exercised only on Windows
            raise PlaybackUnavailableError(
                "the 'sounddevice' package is not installed"
            ) from exc

        device_index = self._resolve_device_index(sd)
        self._output_sample_rate_hz = self._select_output_sample_rate(sd, device_index)

        self._stream = sd.OutputStream(
            device=device_index,
            channels=CHANNELS,
            dtype="int16",
            samplerate=self._output_sample_rate_hz,
            latency="low",
        )
        self._stream.start()

    def _select_output_sample_rate(self, sd, device_index: int) -> int:
        device = sd.query_devices()[device_index]
        preferred = int(device.get("default_samplerate") or 0)
        candidates = []
        if preferred > 0:
            candidates.append(preferred)
        candidates.extend([SOURCE_SAMPLE_RATE_HZ, 48000, 44100])

        seen = set()
        errors = []
        for sample_rate in candidates:
            if sample_rate in seen:
                continue
            seen.add(sample_rate)
            try:
                sd.check_output_settings(
                    device=device_index,
                    channels=CHANNELS,
                    dtype="int16",
                    samplerate=sample_rate,
                )
                return sample_rate
            except Exception as exc:  # pragma: no cover - exercised only on Windows
                errors.append(f"{sample_rate} Hz: {exc}")

        detail = "; ".join(errors) if errors else "no candidate sample rates available"
        raise audio_output.AudioOutputUnavailableError(
            "selected output endpoint cannot play mono int16 PCM at any supported "
            f"sample rate ({detail})"
        )

    def _resolve_device_index(self, sd) -> int:
        host_apis = sd.query_hostapis()
        candidates = []
        for index, device in enumerate(sd.query_devices()):
            if device.get("max_output_channels", 0) <= 0:
                continue
            if device["name"] != self._endpoint_name:
                continue
            host_api_name = host_apis[device["hostapi"]]["name"] if host_apis else ""
            candidates.append((index, host_api_name))

        if not candidates:
            raise audio_output.AudioOutputUnavailableError(
                f"selected output endpoint is not currently present: {self._endpoint_name!r}"
            )

        if self._host_api:
            for index, host_api_name in candidates:
                if host_api_name == self._host_api:
                    return index
            raise audio_output.AudioOutputUnavailableError(
                f"selected output endpoint {self._endpoint_name!r} is no longer present "
                f"under host API {self._host_api!r}"
            )

        if len(candidates) > 1:
            raise audio_output.AudioOutputUnavailableError(
                f"{len(candidates)} output endpoints are named {self._endpoint_name!r} "
                "across different host APIs; open settings and re-select one to disambiguate"
            )

        return candidates[0][0]

    def write(self, samples: List[int]) -> None:
        if self._stream is None:
            raise PlaybackUnavailableError("open() must be called before write()")
        import numpy as np  # type: ignore

        array = np.asarray(samples, dtype="int16").reshape(-1, 1)
        if self._output_sample_rate_hz != SOURCE_SAMPLE_RATE_HZ and len(array) > 1:
            ratio = self._output_sample_rate_hz / SOURCE_SAMPLE_RATE_HZ
            output_length = max(1, int(round(len(array) * ratio)))
            source_positions = np.arange(len(array), dtype=np.float64)
            target_positions = np.linspace(0, len(array) - 1, output_length)
            resampled = np.interp(target_positions, source_positions, array[:, 0])
            array = np.rint(resampled).clip(-32768, 32767).astype("int16").reshape(-1, 1)
        self._stream.write(array)

    def close(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
