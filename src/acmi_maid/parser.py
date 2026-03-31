from __future__ import annotations

import io
import logging
import re
import zipfile
from dataclasses import fields
from pathlib import Path
from typing import IO, Iterator

from acmi_maid.enums import EventType
from acmi_maid.models import (
    AcmiFile, AcmiObject, Event, Frame, GlobalProperties,
    ObjectProperties, Transform,
    EventRecord, PropertyRecord, RemovalRecord, TimeRecord, Record,
)
from acmi_maid.utils import (
    parse_acmi_datetime, parse_transform, split_escaped,
)

log = logging.getLogger("acmi_maid")

# Property name mapping: ACMI PascalCase -> ObjectProperties snake_case field
_PROPERTY_MAP: dict[str, str] = {
    "Name": "name", "Type": "type", "CallSign": "call_sign",
    "Registration": "registration", "Squawk": "squawk", "ICAO24": "icao24",
    "Pilot": "pilot", "Country": "country", "Coalition": "coalition",
    "Color": "color", "Group": "group", "Label": "label", "Shape": "shape",
    "ShortName": "short_name", "LongName": "long_name",
    "FullName": "full_name", "Debug": "debug",
    "Parent": "parent", "Next": "next", "FocusedTarget": "focused_target",
    "IAS": "ias", "CAS": "cas", "TAS": "tas", "Mach": "mach",
    "AOA": "aoa", "AOS": "aos", "AGL": "agl", "HDG": "hdg", "HDM": "hdm",
    "Importance": "importance", "Health": "health",
    "OnGround": "on_ground", "Disabled": "disabled", "Visible": "visible",
    "Throttle": "throttle", "Throttle2": "throttle2",
    "Afterburner": "afterburner", "LandingGear": "landing_gear",
    "Flaps": "flaps", "AirBrakes": "air_brakes", "Tailhook": "tailhook",
    "Parachute": "parachute", "DragChute": "drag_chute",
    "RadarMode": "radar_mode", "RadarRange": "radar_range",
    "RadarAzimuth": "radar_azimuth", "RadarElevation": "radar_elevation",
    "EngagementRange": "engagement_range",
    "VerticalGForce": "vertical_g", "LongitudinalGForce": "longitudinal_g",
    "LateralGForce": "lateral_g",
    "Length": "length", "Width": "width", "Height": "height",
    "Radius": "radius",
    "PilotHeadRoll": "pilot_head_roll", "PilotHeadPitch": "pilot_head_pitch",
    "PilotHeadYaw": "pilot_head_yaw",
    "RollControlInput": "roll_control_input",
    "PitchControlInput": "pitch_control_input",
    "YawControlInput": "yaw_control_input",
    "TriggerPressed": "trigger_pressed",
    "HeartRate": "heart_rate", "SpO2": "spo2",
}

_REVERSE_PROPERTY_MAP: dict[str, str] = {v: k for k, v in _PROPERTY_MAP.items()}

# Global properties mapping
_GLOBAL_MAP: dict[str, str] = {
    "DataSource": "data_source", "DataRecorder": "data_recorder",
    "ReferenceTime": "reference_time", "RecordingTime": "recording_time",
    "ReferenceLongitude": "reference_longitude",
    "ReferenceLatitude": "reference_latitude",
    "Author": "author", "Title": "title", "Category": "category",
    "Briefing": "briefing", "Debriefing": "debriefing",
    "Comments": "comments", "MapId": "map_id",
}

# Indexed property patterns
_RE_LOCKED_TARGET = re.compile(r"^LockedTarget(\d)$")
_RE_FUEL_WEIGHT = re.compile(r"^FuelWeight(\d)$")

# Build a set of bool/int/float field names for type coercion
_OBJ_FIELDS = {f.name: f.type for f in fields(ObjectProperties)}
_BOOL_FIELDS = {
    name for name, t in _OBJ_FIELDS.items()
    if t in ("bool | None",)
}
_INT_FIELDS = {
    name for name, t in _OBJ_FIELDS.items()
    if t in ("int | None",)
}
_FLOAT_FIELDS = {
    name for name, t in _OBJ_FIELDS.items()
    if t in ("float | None",)
}


class AcmiParseError(Exception):
    """Raised when an ACMI file contains invalid or malformed content."""
    def __init__(self, message: str, line_number: int) -> None:
        self.line_number = line_number
        super().__init__(f"Line {line_number}: {message}")


def _open_source(source: str | Path | IO[str]) -> tuple[IO[str], bool]:
    """Open the source, detecting zip compression.
    Returns (text_stream, should_close).
    """
    if isinstance(source, (str, Path)):
        path = Path(source)
        # Check for zip via magic bytes
        try:
            with open(path, "rb") as f:
                magic = f.read(4)
            if magic[:2] == b"PK":
                zf = zipfile.ZipFile(path, "r")
                name = zf.namelist()[0]
                raw = zf.read(name)
                zf.close()
                return io.StringIO(raw.decode("utf-8-sig")), False
        except (zipfile.BadZipFile, IndexError, OSError):
            pass
        return open(path, "r", encoding="utf-8-sig"), True
    else:
        return source, False


def _strip_bom(line: str) -> str:
    if line.startswith("\ufeff"):
        return line[1:]
    return line


def _coerce_value(field_name: str, raw: str) -> object:
    """Coerce a raw string value to the appropriate Python type."""
    if field_name in _BOOL_FIELDS:
        return raw.strip() in ("1", "true", "True")
    if field_name in _INT_FIELDS:
        return int(raw)
    if field_name in _FLOAT_FIELDS:
        return float(raw)
    return raw


def _set_global_prop(gp: GlobalProperties, key: str, value: str) -> None:
    field_name = _GLOBAL_MAP.get(key)
    if field_name is None:
        gp.extra[key] = value
        return
    if field_name in ("reference_time", "recording_time"):
        setattr(gp, field_name, parse_acmi_datetime(value))
    elif field_name in ("reference_longitude", "reference_latitude"):
        setattr(gp, field_name, float(value))
    else:
        setattr(gp, field_name, value)


def _set_object_prop(props: ObjectProperties, key: str, value: str) -> None:
    field_name = _PROPERTY_MAP.get(key)
    if field_name:
        setattr(props, field_name, _coerce_value(field_name, value))
        return
    # Check indexed properties
    m = _RE_LOCKED_TARGET.match(key)
    if m:
        idx = int(m.group(1))
        while len(props.locked_targets) <= idx:
            props.locked_targets.append(0)
        props.locked_targets[idx] = int(value, 16) if not value.isdigit() else int(value)
        return
    m = _RE_FUEL_WEIGHT.match(key)
    if m:
        idx = int(m.group(1))
        while len(props.fuel_weights) <= idx:
            props.fuel_weights.append(None)
        props.fuel_weights[idx] = float(value)
        return
    # Overflow to extra
    props.extra[key] = value


def _parse_property_line(line: str) -> tuple[int, dict[str, str], Transform | None]:
    """Parse a property line: '<hex_id>,Key=Val,Key=Val,...'
    Returns (object_id, properties_dict, transform_or_none).
    """
    parts = split_escaped(line)
    obj_id_str = parts[0]
    obj_id = int(obj_id_str, 16)
    props: dict[str, str] = {}
    transform: Transform | None = None
    for part in parts[1:]:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        if key == "T":
            transform = parse_transform(value)
        else:
            props[key] = value
    return obj_id, props, transform


def _parse_event(value: str, timestamp: float) -> Event | None:
    """Parse an Event= value: 'EventType|ObjId1|ObjId2|...|Text'"""
    parts = value.split("|")
    if not parts:
        return None
    event_type_str = parts[0]
    try:
        event_type = EventType(event_type_str)
    except ValueError:
        log.warning("Unknown event type: %s", event_type_str)
        return None
    # Remaining parts: object IDs until non-hex, then text
    object_ids: list[int] = []
    text = ""
    for i, p in enumerate(parts[1:], start=1):
        try:
            object_ids.append(int(p, 16))
        except ValueError:
            text = "|".join(parts[i:])
            break
    return Event(timestamp=timestamp, type=event_type,
                 object_ids=object_ids, text=text)


class AcmiParser:
    """Parses ACMI files into structured AcmiFile objects.

    Supports plain text (.txt.acmi) and zip-compressed (.zip.acmi, .acmi) files.
    Auto-detects compression format. Handles UTF-8 BOM transparently.
    Accepts FileVersion 2.1 and 2.2.
    """

    @staticmethod
    def parse(source: str | Path | IO[str]) -> AcmiFile:
        """Parse an ACMI file into a fully populated AcmiFile.

        Args:
            source: file path (str/Path) or readable text stream

        Returns:
            AcmiFile with merged object states and complete timelines

        Raises:
            AcmiParseError: on invalid header, malformed lines, etc.
        """
        stream, should_close = _open_source(source)
        try:
            return _parse_stream(stream)
        finally:
            if should_close:
                stream.close()

    @staticmethod
    def iter_records(source: str | Path | IO[str]) -> Iterator[Record]:
        """Lazy iterator over raw records without building full state.

        Yields one of: TimeRecord, PropertyRecord, RemovalRecord, EventRecord.
        Useful for large files or when full state materialization is not needed.
        """
        stream, should_close = _open_source(source)
        try:
            yield from _iter_records_stream(stream)
        finally:
            if should_close:
                stream.close()


def _parse_stream(stream: IO[str]) -> AcmiFile:
    acmi = AcmiFile()
    lines = stream.read().splitlines()
    if not lines:
        raise AcmiParseError("Empty file", 1)

    # Validate header
    line1 = _strip_bom(lines[0]).strip()
    if line1 != "FileType=text/acmi/tacview":
        raise AcmiParseError(
            f"Expected 'FileType=text/acmi/tacview', got '{line1}'", 1
        )
    acmi.file_type = "text/acmi/tacview"

    if len(lines) < 2:
        raise AcmiParseError("Missing FileVersion", 2)
    line2 = lines[1].strip()
    if line2 not in ("FileVersion=2.1", "FileVersion=2.2"):
        raise AcmiParseError(
            f"Expected FileVersion 2.1 or 2.2, got '{line2}'", 2
        )
    acmi.file_version = line2.split("=", 1)[1]

    current_time = 0.0
    for line_num, raw_line in enumerate(lines[2:], start=3):
        line = raw_line.strip()
        if not line or line.startswith("//"):
            continue
        if line.startswith("#"):
            current_time = float(line[1:])
            continue
        if line.startswith("-"):
            obj_id = int(line[1:], 16)
            if obj_id not in acmi.objects:
                acmi.objects[obj_id] = AcmiObject(id=obj_id)
            acmi.objects[obj_id].removed = True
            acmi.objects[obj_id].removed_at = current_time
            continue

        # Property line
        try:
            obj_id, props, transform = _parse_property_line(line)
        except (ValueError, IndexError) as e:
            raise AcmiParseError(str(e), line_num) from e

        if obj_id == 0:
            # Global properties
            for key, value in props.items():
                if key == "Event":
                    event = _parse_event(value, current_time)
                    if event:
                        acmi.events.append(event)
                else:
                    _set_global_prop(acmi.globals, key, value)
        else:
            if obj_id not in acmi.objects:
                acmi.objects[obj_id] = AcmiObject(id=obj_id)
            obj = acmi.objects[obj_id]
            frame = Frame(
                timestamp=current_time,
                transform=transform,
                properties=props,
            )
            obj.timeline.append(frame)
            # Merge into ObjectProperties
            for key, value in props.items():
                _set_object_prop(obj.properties, key, value)

    return acmi


def _iter_records_stream(stream: IO[str]) -> Iterator[Record]:
    lines = stream.read().splitlines()
    if not lines:
        return

    line1 = _strip_bom(lines[0]).strip()
    if line1 != "FileType=text/acmi/tacview":
        raise AcmiParseError(
            f"Expected 'FileType=text/acmi/tacview', got '{line1}'", 1
        )
    if len(lines) < 2 or lines[1].strip() not in (
        "FileVersion=2.1", "FileVersion=2.2"
    ):
        raise AcmiParseError("Invalid FileVersion", 2)

    current_time = 0.0
    for raw_line in lines[2:]:
        line = raw_line.strip()
        if not line or line.startswith("//"):
            continue
        if line.startswith("#"):
            current_time = float(line[1:])
            yield TimeRecord(timestamp=current_time)
            continue
        if line.startswith("-"):
            obj_id = int(line[1:], 16)
            yield RemovalRecord(object_id=obj_id, timestamp=current_time)
            continue

        obj_id, props, transform = _parse_property_line(line)
        if obj_id == 0:
            for key, value in props.items():
                if key == "Event":
                    parsed = _parse_event(value, current_time)
                    if parsed:
                        yield EventRecord(
                            event_type=parsed.type,
                            object_ids=parsed.object_ids,
                            text=parsed.text,
                            timestamp=current_time,
                        )
            # Also yield global as PropertyRecord
            remaining = {k: v for k, v in props.items() if k != "Event"}
            if remaining or transform:
                yield PropertyRecord(
                    object_id=0, properties=remaining, transform=transform
                )
        else:
            yield PropertyRecord(
                object_id=obj_id, properties=props, transform=transform
            )
