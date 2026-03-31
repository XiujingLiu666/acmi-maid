"""Parser for ACMI flight-recording files.

Supports both plain-text ``.acmi`` files and ZIP-compressed ``.zip.acmi``
archives.

ACMI format overview
--------------------
* ``FileType=text/acmi/tacview`` — file-type declaration (first line)
* ``FileVersion=2.2`` — format version (second line)
* ``0,Key=Value,...`` — global property update (object 0)
* ``#<seconds>`` — start of a new time frame
* ``<hex_id>,Key=Value,...`` — object property update
* ``-<hex_id>`` — object removal
* ``// ...`` — comment (ignored)

Object IDs are **hexadecimal** integers.  The special ID ``0`` holds global
(mission-level) properties and is never stored as an :class:`~acmi_maid.models.AcmiObject`.

The ``T=`` property encodes position/orientation as
``Longitude|Latitude|Altitude[|Roll|Pitch|Yaw[|U|V]]``.  Empty fields
(``||``) mean *no change* and are stored as ``None``.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import IO, Union

from .models import AcmiFile, AcmiObject, ObjectRecord, Transform


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_transform(value: str) -> Transform:
    """Parse a ``T=`` property value into a :class:`~acmi_maid.models.Transform`.

    Format: ``Longitude|Latitude|Altitude[|Roll|Pitch|Yaw[|U|V]]``

    An empty field (e.g. ``||``) means *no change* and is represented as
    ``None``.
    """
    parts = value.split("|")
    field_names = ["longitude", "latitude", "altitude", "roll", "pitch", "yaw", "u", "v"]
    kwargs: dict = {}
    for i, name in enumerate(field_names):
        if i < len(parts):
            raw = parts[i].strip()
            kwargs[name] = float(raw) if raw else None
    return Transform(**kwargs)


def _parse_kv_pairs(text: str) -> dict[str, str]:
    """Parse a comma-separated sequence of ``Key=Value`` pairs.

    Only the *first* ``=`` in each token is used as the delimiter, so values
    that themselves contain ``=`` are preserved intact.
    """
    props: dict[str, str] = {}
    for token in text.split(","):
        token = token.strip()
        if "=" in token:
            key, _, val = token.partition("=")
            props[key.strip()] = val
    return props


def _process_lines(lines: list[str], acmi: AcmiFile) -> None:
    """Process a sequence of text lines and populate *acmi* in place."""
    current_time: float = 0.0

    for raw_line in lines:
        line = raw_line.strip()

        # Blank lines and comments
        if not line or line.startswith("//"):
            continue

        # File-type declaration (appears before the first frame)
        if line.startswith("FileType="):
            acmi.file_type = line[len("FileType="):]
            continue

        # File-version declaration
        if line.startswith("FileVersion="):
            acmi.file_version = line[len("FileVersion="):]
            continue

        # Timestamp frame marker: ``#<seconds>``
        if line.startswith("#"):
            try:
                current_time = float(line[1:])
            except ValueError:
                pass
            continue

        # Object removal: ``-<hex_id>``
        if line.startswith("-"):
            try:
                obj_id = int(line[1:].strip(), 16)
            except ValueError:
                continue
            if obj_id in acmi.objects:
                acmi.objects[obj_id].removed_at = current_time
            continue

        # Object update: ``<hex_id>,Key=Value,...``
        comma_idx = line.find(",")
        if comma_idx == -1:
            continue

        id_part = line[:comma_idx].strip()
        props_part = line[comma_idx + 1:]

        try:
            obj_id = int(id_part, 16)
        except ValueError:
            continue

        props = _parse_kv_pairs(props_part)

        transform: Transform | None = None
        if "T" in props:
            transform = _parse_transform(props.pop("T"))

        if obj_id == 0:
            # Global properties – accumulate into the global dict
            acmi.global_properties.update(props)
        else:
            if obj_id not in acmi.objects:
                acmi.objects[obj_id] = AcmiObject(id=obj_id)
            record = ObjectRecord(
                timestamp=current_time,
                transform=transform,
                properties=props,
            )
            acmi.objects[obj_id].records.append(record)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_string(text: str) -> AcmiFile:
    """Parse an ACMI recording from a plain-text string.

    Parameters
    ----------
    text:
        The full text content of an ``.acmi`` file.

    Returns
    -------
    AcmiFile
        The parsed recording.
    """
    acmi = AcmiFile()
    _process_lines(text.splitlines(), acmi)
    return acmi


def parse_stream(stream: IO[bytes]) -> AcmiFile:
    """Parse an ACMI recording from a binary file-like object.

    Automatically detects and decompresses ZIP-compressed archives.

    Parameters
    ----------
    stream:
        A readable binary stream.  May be a plain-text ``.acmi`` or a
        ZIP-compressed ``.zip.acmi``.

    Returns
    -------
    AcmiFile
        The parsed recording.
    """
    data = stream.read()

    if zipfile.is_zipfile(io.BytesIO(data)):
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            # The archive typically contains a single entry
            entry_name = next(
                (n for n in zf.namelist() if not n.endswith("/")),
                zf.namelist()[0],
            )
            data = zf.read(entry_name)

    # Strip UTF-8 BOM if present
    text = data.decode("utf-8-sig")
    return parse_string(text)


def parse_file(path: Union[str, Path]) -> AcmiFile:
    """Parse an ACMI recording from a file path.

    Automatically detects and decompresses ZIP-compressed archives.

    Parameters
    ----------
    path:
        Path to a plain-text ``.acmi`` or ZIP-compressed ``.zip.acmi`` file.

    Returns
    -------
    AcmiFile
        The parsed recording.
    """
    path = Path(path)
    with path.open("rb") as fh:
        return parse_stream(fh)
