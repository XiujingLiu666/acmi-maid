from __future__ import annotations

import io
import tempfile
import zipfile
from pathlib import Path
from typing import IO

from acmi_maid.models import Event, GlobalProperties, Transform
from acmi_maid.parser import _REVERSE_GLOBAL_MAP
from acmi_maid.utils import (
    escape_value,
    format_acmi_datetime,
    format_transform,
)


class AcmiStreamer:
    """Append-only streaming ACMI writer for real-time telemetry.

    Writes ACMI lines incrementally without buffering the full recording
    in memory. Property kwargs use ACMI-native PascalCase names.

    Thread safety: NOT thread-safe.
    """

    def __init__(
        self,
        dest: str | Path | IO[str],
        globals: GlobalProperties | None = None,
        compress: bool = False,
    ) -> None:
        self._compress = compress
        self._dest_path: Path | None = None
        self._owns_stream = False
        self._last_timestamp: float | None = None

        if isinstance(dest, (str, Path)):
            self._dest_path = Path(dest)
            if compress:
                # Write to temp file, zip on close
                self._tmp = tempfile.NamedTemporaryFile(
                    mode="w", suffix=".acmi", delete=False, encoding="utf-8"
                )
                self._stream: IO[str] = self._tmp
                self._owns_stream = True
            else:
                self._stream = open(self._dest_path, "w", encoding="utf-8-sig")
                self._owns_stream = True
        else:
            self._stream = dest

        # Write header
        self._write_line("FileType=text/acmi/tacview")
        self._write_line("FileVersion=2.2")

        # Write global properties
        if globals is not None:
            parts = ["0"]
            for field_name, acmi_key in _REVERSE_GLOBAL_MAP.items():
                val = getattr(globals, field_name)
                if val is None:
                    continue
                if field_name in ("reference_time", "recording_time"):
                    parts.append(f"{acmi_key}={format_acmi_datetime(val)}")
                elif field_name in ("reference_longitude", "reference_latitude"):
                    if val != 0.0:
                        parts.append(f"{acmi_key}={val}")
                else:
                    parts.append(f"{acmi_key}={escape_value(str(val))}")
            for key, val in globals.extra.items():
                parts.append(f"{key}={escape_value(val)}")
            if len(parts) > 1:
                self._write_line(",".join(parts))

    def write_frame(
        self,
        timestamp: float,
        object_id: int,
        transform: Transform | None = None,
        **properties: str,
    ) -> None:
        """Write a single object update at the given timestamp."""
        self._write_timestamp(timestamp)
        hex_id = format(object_id, "x")
        parts = [hex_id]
        if transform is not None:
            parts.append(f"T={format_transform(transform)}")
        for key, value in properties.items():
            parts.append(f"{key}={escape_value(str(value))}")
        self._write_line(",".join(parts))

    def write_event(self, event: Event) -> None:
        """Write an event record."""
        self._write_timestamp(event.timestamp)
        hex_ids = "|".join(format(oid, "x") for oid in event.object_ids)
        evt_parts = [event.type.value]
        if hex_ids:
            evt_parts.append(hex_ids)
        if event.text:
            evt_parts.append(event.text)
        self._write_line(f"0,Event={'|'.join(evt_parts)}")

    def remove_object(self, timestamp: float, object_id: int) -> None:
        """Write an object removal line."""
        self._write_timestamp(timestamp)
        self._write_line(f"-{format(object_id, 'x')}")

    def close(self) -> None:
        """Flush and close the underlying stream."""
        self._stream.flush()
        if self._compress and self._dest_path is not None:
            # Close temp file, then zip it
            tmp_path = self._tmp.name
            self._stream.close()
            inner_name = self._dest_path.stem
            if not inner_name.endswith(".acmi"):
                inner_name += ".acmi"
            data = Path(tmp_path).read_bytes()
            with zipfile.ZipFile(self._dest_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(inner_name, data)
            Path(tmp_path).unlink(missing_ok=True)
        elif self._owns_stream:
            self._stream.close()

    def __enter__(self) -> AcmiStreamer:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _write_timestamp(self, timestamp: float) -> None:
        if timestamp != self._last_timestamp:
            ts_str = str(int(timestamp)) if timestamp == int(timestamp) else str(timestamp)
            self._write_line(f"#{ts_str}")
            self._last_timestamp = timestamp

    def _write_line(self, line: str) -> None:
        self._stream.write(line + "\n")
