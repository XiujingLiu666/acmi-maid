from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import IO

from acmi_maid.models import AcmiFile, AcmiObject, Event, Frame, GlobalProperties
from acmi_maid.utils import escape_value, format_acmi_datetime, format_transform

# Reverse mapping: GlobalProperties field -> ACMI key
_GLOBAL_REVERSE: dict[str, str] = {
    "data_source": "DataSource", "data_recorder": "DataRecorder",
    "reference_time": "ReferenceTime", "recording_time": "RecordingTime",
    "reference_longitude": "ReferenceLongitude",
    "reference_latitude": "ReferenceLatitude",
    "author": "Author", "title": "Title", "category": "Category",
    "briefing": "Briefing", "debriefing": "Debriefing",
    "comments": "Comments", "map_id": "MapId",
}


def _format_global_props(gp: GlobalProperties) -> list[str]:
    """Format global properties as Key=Value pairs."""
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
    return parts


def _format_frame_props(frame: Frame) -> list[str]:
    """Format a frame's properties as Key=Value pairs."""
    parts: list[str] = []
    if frame.transform is not None:
        parts.append(f"T={format_transform(frame.transform)}")
    for key, value in frame.properties.items():
        parts.append(f"{key}={escape_value(str(value))}")
    return parts


def _format_event(event: Event) -> str:
    """Format an Event as an Event= value string."""
    parts = [event.type.value]
    parts.extend(format(oid, "x") for oid in event.object_ids)
    if event.text:
        parts.append(event.text)
    return "Event=" + "|".join(parts)


class AcmiWriter:
    """Writes AcmiFile objects to ACMI text format.

    Produces spec-compliant ACMI 2.2 output with LF line endings.
    When writing to a file path, includes a UTF-8 BOM.
    When writing to a caller-provided IO[str] stream, no BOM is written.
    """

    @staticmethod
    def write(acmi: AcmiFile, dest: str | Path | IO[str],
              compress: bool = False) -> None:
        """Write a complete AcmiFile to disk or stream.

        Args:
            acmi: the recording data to serialize
            dest: file path or writable text stream
            compress: if True, wrap output in a zip container
        """
        if isinstance(dest, (str, Path)):
            path = Path(dest)
            text = AcmiWriter.to_string(acmi)
            if compress:
                with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
                    zf.writestr("mission.acmi", text)
            else:
                with open(path, "w", encoding="utf-8-sig", newline="") as f:
                    f.write(text)
        else:
            # Writing to stream — no BOM
            dest.write(AcmiWriter.to_string(acmi))

    @staticmethod
    def to_string(acmi: AcmiFile) -> str:
        """Serialize an AcmiFile to a string (no BOM prefix)."""
        lines: list[str] = []
        # Header
        lines.append(f"FileType={acmi.file_type}")
        lines.append(f"FileVersion={acmi.file_version}")

        # Collect all timeline entries: (timestamp, content_line)
        timeline: list[tuple[float, str]] = []

        # Global properties at t=0
        gp_parts = _format_global_props(acmi.globals)
        if gp_parts:
            timeline.append((0.0, "0," + ",".join(gp_parts)))

        # Object frames
        for obj in acmi.objects.values():
            for frame in obj.timeline:
                parts = _format_frame_props(frame)
                if parts:
                    line = f"{obj.id:x},{','.join(parts)}"
                    timeline.append((frame.timestamp, line))

        # Events (written as global object properties)
        for event in acmi.events:
            line = f"0,{_format_event(event)}"
            timeline.append((event.timestamp, line))

        # Object removals
        for obj in acmi.objects.values():
            if obj.removed and obj.removed_at is not None:
                timeline.append((obj.removed_at, f"-{obj.id:x}"))

        # Sort by timestamp, then write with #timestamp markers
        timeline.sort(key=lambda x: x[0])
        last_time: float | None = None
        for ts, content in timeline:
            if last_time is None or ts != last_time:
                lines.append(f"#{ts}")
                last_time = ts
            lines.append(content)

        return "\n".join(lines) + "\n"
