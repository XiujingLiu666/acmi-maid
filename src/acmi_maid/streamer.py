from __future__ import annotations

import io
import os
import tempfile
import zipfile
from pathlib import Path
from typing import IO

from acmi_maid.models import Event, GlobalProperties, Transform
from acmi_maid.utils import escape_value, format_acmi_datetime, format_transform

_GLOBAL_REVERSE: dict[str, str] = {
    "data_source": "DataSource", "data_recorder": "DataRecorder",
    "reference_time": "ReferenceTime", "recording_time": "RecordingTime",
    "reference_longitude": "ReferenceLongitude",
    "reference_latitude": "ReferenceLatitude",
    "author": "Author", "title": "Title", "category": "Category",
    "briefing": "Briefing", "debriefing": "Debriefing",
    "comments": "Comments", "map_id": "MapId",
}


class AcmiStreamer:
    """Append-only streaming ACMI writer for real-time telemetry.

    Writes ACMI lines incrementally without buffering the full recording
    in memory. Suitable for live data feeds.

    Property kwargs use ACMI-native PascalCase names (e.g. Name="F-16C")
    to match the wire format directly, since the streamer has no
    ObjectProperties layer to map through.

    Thread safety: NOT thread-safe. Callers must synchronize externally
    if multiple threads write concurrently.
    """

    def __init__(
        self,
        dest: str | Path | IO[str],
        globals: GlobalProperties | None = None,
        compress: bool = False,
    ) -> None:
        """Open a stream and write the header + global properties."""
        self._compress = compress
        self._dest_path: Path | None = None
        self._owns_stream = False
        self._tmp_path: str | None = None

        if isinstance(dest, (str, Path)):
            self._dest_path = Path(dest)
            if compress:
                fd, self._tmp_path = tempfile.mkstemp(
                    suffix=".acmi", text=True,
                )
                self._stream: IO[str] = os.fdopen(
                    fd, "w", encoding="utf-8", newline="",
                )
            else:
                self._stream = open(
                    self._dest_path, "w", encoding="utf-8-sig", newline=""
                )
            self._owns_stream = True
        else:
            self._stream = dest

        self._last_time: float | None = None
        self._write_header(globals)

    def _write_header(self, gp: GlobalProperties | None) -> None:
        self._stream.write("FileType=text/acmi/tacview\n")
        self._stream.write("FileVersion=2.2\n")
        if gp:
            parts: list[str] = []
            for field_name, acmi_key in _GLOBAL_REVERSE.items():
                value = getattr(gp, field_name)
                if value is None:
                    continue
                if field_name in ("reference_longitude", "reference_latitude"):
                    if value == 0.0:
                        continue
                    parts.append(f"{acmi_key}={value}")
                elif field_name in ("reference_time", "recording_time"):
                    parts.append(f"{acmi_key}={format_acmi_datetime(value)}")
                else:
                    parts.append(f"{acmi_key}={escape_value(str(value))}")
            for key, value in gp.extra.items():
                parts.append(f"{key}={escape_value(value)}")
            if parts:
                self._stream.write("0," + ",".join(parts) + "\n")

    def _ensure_timestamp(self, timestamp: float) -> None:
        if self._last_time is None or timestamp != self._last_time:
            self._stream.write(f"#{timestamp}\n")
            self._last_time = timestamp

    def write_frame(
        self,
        timestamp: float,
        object_id: int,
        transform: Transform | None = None,
        **properties: str,
    ) -> None:
        """Write a single object update at the given timestamp.

        Args:
            timestamp: seconds since reference_time
            object_id: hex object ID as int
            transform: optional position/orientation update
            **properties: ACMI PascalCase property key-value pairs
        """
        self._ensure_timestamp(timestamp)
        parts: list[str] = [f"{object_id:x}"]
        if transform is not None:
            parts.append(f"T={format_transform(transform)}")
        for key, value in properties.items():
            parts.append(f"{key}={escape_value(str(value))}")
        self._stream.write(",".join(parts) + "\n")

    def write_event(self, event: Event) -> None:
        """Write an event record. Uses event.timestamp for timing."""
        self._ensure_timestamp(event.timestamp)
        parts = [event.type.value]
        parts.extend(format(oid, "x") for oid in event.object_ids)
        if event.text:
            parts.append(event.text)
        self._stream.write(f"0,Event={'|'.join(parts)}\n")

    def remove_object(self, timestamp: float, object_id: int) -> None:
        """Write an object removal line (-ID)."""
        self._ensure_timestamp(timestamp)
        self._stream.write(f"-{object_id:x}\n")

    def close(self) -> None:
        """Flush and close the underlying stream."""
        if self._compress and self._dest_path and self._owns_stream:
            self._stream.flush()
            self._stream.close()
            with open(self._tmp_path, "r", encoding="utf-8") as f:
                content = f.read()
            with zipfile.ZipFile(
                self._dest_path, "w", zipfile.ZIP_DEFLATED
            ) as zf:
                zf.writestr("mission.acmi", content)
            os.unlink(self._tmp_path)
        elif self._owns_stream:
            self._stream.close()

    def __enter__(self) -> AcmiStreamer:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
