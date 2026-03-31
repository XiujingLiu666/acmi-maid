"""Serialiser for ACMI flight-recording files.

Converts an :class:`~acmi_maid.models.AcmiFile` back to the plain-text ACMI
format (or a ZIP-compressed variant).
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import IO, Union

from .models import AcmiFile, AcmiObject, ObjectRecord, Transform

_TRANSFORM_FIELDS = [
    "longitude",
    "latitude",
    "altitude",
    "roll",
    "pitch",
    "yaw",
    "u",
    "v",
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _transform_to_str(transform: Transform) -> str:
    """Serialise a :class:`~acmi_maid.models.Transform` to the ``T=…`` value.

    Format: ``Longitude|Latitude|Altitude[|Roll|Pitch|Yaw[|U|V]]``

    Trailing empty (``None``) fields are omitted.
    """
    parts: list[str] = []
    for field_name in _TRANSFORM_FIELDS:
        val = getattr(transform, field_name)
        parts.append("" if val is None else str(val))

    # Trim trailing empty fields
    while parts and parts[-1] == "":
        parts.pop()

    return "|".join(parts)


def _props_to_str(props: dict[str, str]) -> str:
    return ",".join(f"{k}={v}" for k, v in props.items())


def _serialize(acmi: AcmiFile) -> list[str]:
    """Return the lines of the ACMI text representation (without newlines)."""
    lines: list[str] = []

    # --- Header -----------------------------------------------------------
    lines.append(f"FileType={acmi.file_type or 'text/acmi/tacview'}")
    lines.append(f"FileVersion={acmi.file_version or '2.2'}")

    # --- Global properties ------------------------------------------------
    if acmi.global_properties:
        lines.append(f"0,{_props_to_str(acmi.global_properties)}")

    # --- Collect all timed events -----------------------------------------
    # Each event is (timestamp, sort_key, line_text)
    # sort_key 0 = object update, 1 = object removal (removals after updates
    # at the same timestamp)
    events: list[tuple[float, int, str]] = []

    for obj in acmi.objects.values():
        for record in obj.records:
            parts: list[str] = [f"{obj.id:X}"]
            if record.transform is not None:
                parts.append(f"T={_transform_to_str(record.transform)}")
            for key, val in record.properties.items():
                parts.append(f"{key}={val}")
            events.append((record.timestamp, 0, ",".join(parts)))

        if obj.removed_at is not None:
            events.append((obj.removed_at, 1, f"-{obj.id:X}"))

    # Sort chronologically; within the same timestamp updates precede removals
    events.sort(key=lambda e: (e[0], e[1]))

    # --- Emit frames -------------------------------------------------------
    current_ts: float | None = None
    for ts, _, line_text in events:
        if ts != current_ts:
            lines.append(f"#{ts:g}")
            current_ts = ts
        lines.append(line_text)

    return lines


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def write_string(acmi: AcmiFile) -> str:
    """Serialise *acmi* to a plain-text ACMI string.

    Parameters
    ----------
    acmi:
        The recording to serialise.

    Returns
    -------
    str
        The ACMI text content.
    """
    return "\n".join(_serialize(acmi)) + "\n"


def write_stream(
    acmi: AcmiFile,
    stream: IO[bytes],
    *,
    compressed: bool = False,
) -> None:
    """Write *acmi* to a binary file-like stream.

    Parameters
    ----------
    acmi:
        The recording to serialise.
    stream:
        A writable binary file-like object.
    compressed:
        When ``True`` the output is ZIP-compressed (suitable for
        ``.zip.acmi`` files).
    """
    text = write_string(acmi)
    data = text.encode("utf-8")

    if compressed:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("tacview.acmi.txt", data)
        stream.write(buf.getvalue())
    else:
        stream.write(data)


def write_file(
    acmi: AcmiFile,
    path: Union[str, Path],
    *,
    compressed: bool = False,
) -> None:
    """Write *acmi* to a file.

    Parameters
    ----------
    acmi:
        The recording to serialise.
    path:
        Destination file path.
    compressed:
        When ``True`` the output is ZIP-compressed (suitable for
        ``.zip.acmi`` files).
    """
    path = Path(path)
    with path.open("wb") as fh:
        write_stream(acmi, fh, compressed=compressed)
