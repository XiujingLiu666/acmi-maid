from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import IO

from acmi_maid.models import AcmiFile, Event
from acmi_maid.parser import _REVERSE_GLOBAL_MAP, _REVERSE_PROPERTY_MAP
from acmi_maid.utils import (
    escape_value,
    format_acmi_datetime,
    format_transform,
)


class AcmiWriter:
    """Writes AcmiFile objects to ACMI text format."""

    @staticmethod
    def write(
        acmi: AcmiFile,
        dest: str | Path | IO[str],
        compress: bool = False,
    ) -> None:
        """Write a complete AcmiFile to disk or stream."""
        text = AcmiWriter.to_string(acmi)

        if isinstance(dest, (str, Path)):
            path = Path(dest)
            if compress:
                _write_compressed(text, path)
            else:
                path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))
        else:
            # IO[str] stream — no BOM
            dest.write(text)

    @staticmethod
    def to_string(acmi: AcmiFile) -> str:
        """Serialize an AcmiFile to a string (no BOM prefix)."""
        lines: list[str] = []

        # Header
        lines.append(f"FileType={acmi.file_type}")
        lines.append(f"FileVersion={acmi.file_version}")

        # Global properties
        global_parts = ["0"]
        g = acmi.globals
        for field_name, acmi_key in _REVERSE_GLOBAL_MAP.items():
            val = getattr(g, field_name)
            if val is None:
                continue
            if field_name in ("reference_time", "recording_time"):
                global_parts.append(f"{acmi_key}={format_acmi_datetime(val)}")
            elif field_name in ("reference_longitude", "reference_latitude"):
                if val != 0.0:
                    global_parts.append(f"{acmi_key}={val}")
            else:
                global_parts.append(f"{acmi_key}={escape_value(str(val))}")
        for key, val in g.extra.items():
            global_parts.append(f"{key}={escape_value(val)}")
        if len(global_parts) > 1:
            lines.append(",".join(global_parts))

        # Collect all timeline entries into a unified sorted list
        # Each entry: (timestamp, sort_key, line_str)
        # sort_key ensures stable ordering: globals first, then objects, then events, then removals
        entries: list[tuple[float, int, str]] = []

        for obj_id, obj in acmi.objects.items():
            hex_id = format(obj_id, "x")
            for frame in obj.timeline:
                parts = [hex_id]
                if frame.transform is not None:
                    parts.append(f"T={format_transform(frame.transform)}")
                for key, value in frame.properties.items():
                    parts.append(f"{key}={escape_value(str(value))}")
                entries.append((frame.timestamp, 1, ",".join(parts)))

            if obj.removed and obj.removed_at is not None:
                entries.append((obj.removed_at, 3, f"-{hex_id}"))

        # Events
        for event in acmi.events:
            entries.append((event.timestamp, 2, _format_event(event)))

        # Sort by timestamp, then sort_key
        entries.sort(key=lambda e: (e[0], e[1]))

        # Write grouped by timestamp
        last_time: float | None = None
        for timestamp, _, line_str in entries:
            if timestamp != last_time:
                lines.append(f"#{_format_timestamp(timestamp)}")
                last_time = timestamp
            lines.append(line_str)

        return "\n".join(lines) + "\n"


def _format_event(event: Event) -> str:
    """Format an Event into an ACMI line."""
    hex_ids = "|".join(format(oid, "x") for oid in event.object_ids)
    parts = [event.type.value]
    if hex_ids:
        parts.append(hex_ids)
    if event.text:
        parts.append(event.text)
    return f"0,Event={'|'.join(parts)}"


def _format_timestamp(ts: float) -> str:
    """Format a timestamp for output."""
    if ts == int(ts):
        return str(int(ts))
    return str(ts)


def _write_compressed(text: str, path: Path) -> None:
    """Write text content as a zip-compressed ACMI file."""
    # Use the stem as the inner filename
    inner_name = path.stem
    if not inner_name.endswith(".acmi"):
        inner_name += ".acmi"
    data = b"\xef\xbb\xbf" + text.encode("utf-8")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(inner_name, data)
