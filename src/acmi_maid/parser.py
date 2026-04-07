from __future__ import annotations

import io
import logging
import re
import zipfile
from pathlib import Path
from typing import IO, Iterator

from acmi_maid.enums import EventType
from acmi_maid.models import (
    AcmiFile,
    AcmiObject,
    Event,
    EventRecord,
    Frame,
    GlobalProperties,
    ObjectProperties,
    PropertyRecord,
    Record,
    RemovalRecord,
    TimeRecord,
    Transform,
)
from acmi_maid.utils import (
    format_acmi_datetime,
    parse_acmi_datetime,
    parse_transform,
    split_escaped,
)

log = logging.getLogger("acmi_maid")

_VALID_VERSIONS = {"2.1", "2.2"}

# Maps ACMI PascalCase property names to ObjectProperties field names.
_PROPERTY_MAP: dict[str, str] = {
    # Identity
    "Name": "name",
    "Type": "type",
    "CallSign": "call_sign",
    "Registration": "registration",
    "Squawk": "squawk",
    "ICAO24": "icao24",
    "Pilot": "pilot",
    "Country": "country",
    "Coalition": "coalition",
    "Color": "color",
    "Group": "group",
    "Label": "label",
    "Shape": "shape",
    "ShortName": "short_name",
    "LongName": "long_name",
    "FullName": "full_name",
    "Debug": "debug",
    # References
    "Parent": "parent",
    "Next": "next",
    "FocusedTarget": "focused_target",
    # Flight dynamics
    "IAS": "ias",
    "CAS": "cas",
    "TAS": "tas",
    "Mach": "mach",
    "AOA": "aoa",
    "AOS": "aos",
    "AGL": "agl",
    "HDG": "hdg",
    "HDM": "hdm",
    # State
    "Importance": "importance",
    "Health": "health",
    "OnGround": "on_ground",
    "Disabled": "disabled",
    "Visible": "visible",
    # Controls
    "Throttle": "throttle",
    "Throttle2": "throttle2",
    "Afterburner": "afterburner",
    "LandingGear": "landing_gear",
    "Flaps": "flaps",
    "AirBrakes": "air_brakes",
    "Tailhook": "tailhook",
    "Parachute": "parachute",
    "DragChute": "drag_chute",
    # Radar
    "RadarMode": "radar_mode",
    "RadarRange": "radar_range",
    "RadarAzimuth": "radar_azimuth",
    "RadarElevation": "radar_elevation",
    "EngagementRange": "engagement_range",
    # G-forces
    "VerticalGForce": "vertical_g",
    "LongitudinalGForce": "longitudinal_g",
    "LateralGForce": "lateral_g",
    # Dimensions
    "Length": "length",
    "Width": "width",
    "Height": "height",
    "Radius": "radius",
    # Pilot head
    "PilotHeadRoll": "pilot_head_roll",
    "PilotHeadPitch": "pilot_head_pitch",
    "PilotHeadYaw": "pilot_head_yaw",
    # Control inputs
    "RollControlInput": "roll_control_input",
    "PitchControlInput": "pitch_control_input",
    "YawControlInput": "yaw_control_input",
    "TriggerPressed": "trigger_pressed",
    # Biometrics
    "HeartRate": "heart_rate",
    "SpO2": "spo2",
}

_REVERSE_PROPERTY_MAP: dict[str, str] = {v: k for k, v in _PROPERTY_MAP.items()}

# Global property name mapping (ACMI PascalCase -> GlobalProperties field)
_GLOBAL_MAP: dict[str, str] = {
    "DataSource": "data_source",
    "DataRecorder": "data_recorder",
    "ReferenceTime": "reference_time",
    "RecordingTime": "recording_time",
    "ReferenceLongitude": "reference_longitude",
    "ReferenceLatitude": "reference_latitude",
    "Author": "author",
    "Title": "title",
    "Category": "category",
    "Briefing": "briefing",
    "Debriefing": "debriefing",
    "Comments": "comments",
    "MapId": "map_id",
}

_REVERSE_GLOBAL_MAP: dict[str, str] = {v: k for k, v in _GLOBAL_MAP.items()}

# Fields that should be parsed as booleans
_BOOL_FIELDS = {"on_ground", "disabled", "trigger_pressed"}

# Fields that should be parsed as int (hex object references)
_INT_FIELDS = {"parent", "next", "focused_target"}

# Fields that should be parsed as int (decimal)
_INT_DECIMAL_FIELDS = {"radar_mode"}

# Float global fields
_FLOAT_GLOBAL_FIELDS = {"reference_longitude", "reference_latitude"}

# Datetime global fields
_DATETIME_GLOBAL_FIELDS = {"reference_time", "recording_time"}

# Regex for indexed properties
_LOCKED_TARGET_RE = re.compile(r"^LockedTarget(\d+)$")
_FUEL_WEIGHT_RE = re.compile(r"^FuelWeight(\d+)$")

# Event type lookup
_EVENT_TYPE_MAP: dict[str, EventType] = {e.value: e for e in EventType}


class AcmiParseError(Exception):
    """Raised when an ACMI file contains invalid or malformed content."""

    def __init__(self, message: str, line_number: int) -> None:
        self.line_number = line_number
        super().__init__(f"Line {line_number}: {message}")


class AcmiParser:
    """Parses ACMI files into structured AcmiFile objects."""

    @staticmethod
    def parse(source: str | Path | IO[str]) -> AcmiFile:
        """Parse an ACMI file into a fully populated AcmiFile."""
        lines, line_offset = _open_source(source)
        acmi = AcmiFile()
        current_time = 0.0

        # Validate header
        _validate_header(lines, acmi, line_offset)

        # Process body
        for line_idx in range(2, len(lines)):
            line_num = line_idx + 1 + line_offset
            line = lines[line_idx].strip()
            if not line or line.startswith("//"):
                continue

            if line.startswith("#"):
                # Timestamp
                try:
                    current_time = float(line[1:])
                except ValueError:
                    raise AcmiParseError(f"Invalid timestamp: {line}", line_num)
                continue

            if line.startswith("-"):
                # Object removal
                hex_id = line[1:].strip()
                try:
                    obj_id = int(hex_id, 16)
                except ValueError:
                    raise AcmiParseError(f"Invalid object ID in removal: {hex_id}", line_num)
                if obj_id in acmi.objects:
                    acmi.objects[obj_id].removed = True
                    acmi.objects[obj_id].removed_at = current_time
                continue

            # Property line: <hex_id>,<props>
            _parse_property_line(line, line_num, current_time, acmi)

        return acmi

    @staticmethod
    def iter_records(source: str | Path | IO[str]) -> Iterator[Record]:
        """Lazy iterator over raw records without building full state."""
        lines, line_offset = _open_source(source)

        # Validate header
        acmi = AcmiFile()
        _validate_header(lines, acmi, line_offset)

        current_time = 0.0

        for line_idx in range(2, len(lines)):
            line_num = line_idx + 1 + line_offset
            line = lines[line_idx].strip()
            if not line or line.startswith("//"):
                continue

            if line.startswith("#"):
                try:
                    current_time = float(line[1:])
                except ValueError:
                    raise AcmiParseError(f"Invalid timestamp: {line}", line_num)
                yield TimeRecord(timestamp=current_time)
                continue

            if line.startswith("-"):
                hex_id = line[1:].strip()
                try:
                    obj_id = int(hex_id, 16)
                except ValueError:
                    raise AcmiParseError(f"Invalid object ID in removal: {hex_id}", line_num)
                yield RemovalRecord(object_id=obj_id, timestamp=current_time)
                continue

            # Property line
            parts = split_escaped(line)
            if len(parts) < 2:
                raise AcmiParseError(f"Malformed property line: {line}", line_num)

            hex_id = parts[0]
            try:
                obj_id = int(hex_id, 16)
            except ValueError:
                raise AcmiParseError(f"Invalid object ID: {hex_id}", line_num)

            transform = None
            props: dict[str, str] = {}

            for part in parts[1:]:
                if "=" not in part:
                    raise AcmiParseError(f"Malformed property (no '='): {part}", line_num)
                key, _, value = part.partition("=")

                if key == "T":
                    try:
                        transform = parse_transform(value)
                    except ValueError as e:
                        raise AcmiParseError(str(e), line_num)
                elif key == "Event" and obj_id == 0:
                    # Parse event
                    event_parts = value.split("|")
                    event_type_str = event_parts[0] if event_parts else ""
                    if event_type_str in _EVENT_TYPE_MAP:
                        evt_type = _EVENT_TYPE_MAP[event_type_str]
                        evt_ids: list[int] = []
                        evt_text = ""
                        # Parse object IDs and text from remaining parts
                        remaining = event_parts[1:]
                        for i, ep in enumerate(remaining):
                            try:
                                evt_ids.append(int(ep, 16))
                            except ValueError:
                                # Rest is text
                                evt_text = "|".join(remaining[i:])
                                break
                        yield EventRecord(
                            event_type=evt_type,
                            object_ids=evt_ids,
                            text=evt_text,
                            timestamp=current_time,
                        )
                    else:
                        log.warning("Unknown event type: %s (line %d)", event_type_str, line_num)
                        props[key] = value
                else:
                    props[key] = value

            if obj_id != 0 or props:
                yield PropertyRecord(
                    object_id=obj_id,
                    properties=props,
                    transform=transform,
                )


def _open_source(source: str | Path | IO[str]) -> tuple[list[str], int]:
    """Open an ACMI source and return lines + line offset.

    Returns (lines, line_offset) where line_offset is used for error reporting.
    """
    if isinstance(source, (str, Path)):
        path = Path(source)
        # Check for zip
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as zf:
                # Find first .acmi or .txt.acmi entry
                acmi_entries = [
                    n for n in zf.namelist()
                    if n.endswith(".acmi") or n.endswith(".txt.acmi")
                ]
                if not acmi_entries:
                    acmi_entries = zf.namelist()
                entry = acmi_entries[0]
                data = zf.read(entry)
                text = data.decode("utf-8-sig")
                return text.splitlines(), 0
        else:
            text = path.read_text(encoding="utf-8-sig")
            return text.splitlines(), 0
    else:
        # IO[str] stream
        text = source.read()
        # Strip BOM if present
        if text.startswith("\ufeff"):
            text = text[1:]
        return text.splitlines(), 0


def _validate_header(lines: list[str], acmi: AcmiFile, line_offset: int) -> None:
    """Validate ACMI file header (first two lines)."""
    if len(lines) < 2:
        raise AcmiParseError("File too short: missing header", 1 + line_offset)

    # First line: FileType
    first = lines[0].strip()
    if not first.startswith("FileType="):
        raise AcmiParseError(f"Expected FileType header, got: {first}", 1 + line_offset)
    acmi.file_type = first.split("=", 1)[1]

    # Second line: FileVersion
    second = lines[1].strip()
    if not second.startswith("FileVersion="):
        raise AcmiParseError(f"Expected FileVersion header, got: {second}", 2 + line_offset)
    version = second.split("=", 1)[1]
    if version not in _VALID_VERSIONS:
        raise AcmiParseError(f"Unsupported FileVersion: {version}", 2 + line_offset)
    acmi.file_version = version


def _parse_property_line(
    line: str, line_num: int, current_time: float, acmi: AcmiFile
) -> None:
    """Parse a property line (<hex_id>,<Key=Value>,...) and update acmi."""
    parts = split_escaped(line)
    if len(parts) < 2:
        raise AcmiParseError(f"Malformed property line: {line}", line_num)

    hex_id = parts[0]
    try:
        obj_id = int(hex_id, 16)
    except ValueError:
        raise AcmiParseError(f"Invalid object ID: {hex_id}", line_num)

    transform = None
    raw_props: dict[str, str] = {}

    for part in parts[1:]:
        if "=" not in part:
            raise AcmiParseError(f"Malformed property (no '='): {part}", line_num)
        key, _, value = part.partition("=")

        if key == "T":
            try:
                transform = parse_transform(value)
            except ValueError as e:
                raise AcmiParseError(str(e), line_num)
        elif key == "Event" and obj_id == 0:
            _parse_event(value, current_time, line_num, acmi)
        elif obj_id == 0:
            _set_global_property(acmi.globals, key, value)
            raw_props[key] = value
        else:
            raw_props[key] = value

    if obj_id == 0:
        return

    # Handle object property line
    if obj_id not in acmi.objects:
        acmi.objects[obj_id] = AcmiObject(id=obj_id)
    obj = acmi.objects[obj_id]

    # Build frame (store raw props for round-trip)
    frame = Frame(timestamp=current_time, transform=transform, properties=raw_props)
    obj.timeline.append(frame)

    # Merge properties into ObjectProperties
    for key, value in raw_props.items():
        _set_object_property(obj.properties, key, value)


def _parse_event(value: str, timestamp: float, line_num: int, acmi: AcmiFile) -> None:
    """Parse an Event= value and add to acmi.events."""
    event_parts = value.split("|")
    if not event_parts:
        return

    event_type_str = event_parts[0]
    if event_type_str not in _EVENT_TYPE_MAP:
        log.warning("Unknown event type: %s (line %d)", event_type_str, line_num)
        acmi.globals.extra[f"Event_{event_type_str}"] = value
        return

    evt_type = _EVENT_TYPE_MAP[event_type_str]
    evt_ids: list[int] = []
    evt_text = ""

    remaining = event_parts[1:]
    for i, ep in enumerate(remaining):
        try:
            evt_ids.append(int(ep, 16))
        except ValueError:
            evt_text = "|".join(remaining[i:])
            break

    acmi.events.append(Event(
        timestamp=timestamp,
        type=evt_type,
        object_ids=evt_ids,
        text=evt_text,
    ))


def _set_global_property(globals_: GlobalProperties, key: str, value: str) -> None:
    """Set a property on GlobalProperties."""
    field_name = _GLOBAL_MAP.get(key)
    if field_name is None:
        globals_.extra[key] = value
        return

    if field_name in _DATETIME_GLOBAL_FIELDS:
        setattr(globals_, field_name, parse_acmi_datetime(value))
    elif field_name in _FLOAT_GLOBAL_FIELDS:
        setattr(globals_, field_name, float(value))
    else:
        setattr(globals_, field_name, value)


def _set_object_property(props: ObjectProperties, key: str, value: str) -> None:
    """Set a property on ObjectProperties."""
    # Check indexed properties first
    m = _LOCKED_TARGET_RE.match(key)
    if m:
        idx = int(m.group(1))
        # Extend list if needed
        while len(props.locked_targets) <= idx:
            props.locked_targets.append(0)
        props.locked_targets[idx] = int(value, 16)
        return

    m = _FUEL_WEIGHT_RE.match(key)
    if m:
        idx = int(m.group(1))
        while len(props.fuel_weights) <= idx:
            props.fuel_weights.append(None)
        props.fuel_weights[idx] = float(value)
        return

    field_name = _PROPERTY_MAP.get(key)
    if field_name is None:
        props.extra[key] = value
        return

    if field_name in _BOOL_FIELDS:
        setattr(props, field_name, value == "1")
    elif field_name in _INT_FIELDS:
        setattr(props, field_name, int(value, 16))
    elif field_name in _INT_DECIMAL_FIELDS:
        setattr(props, field_name, int(value))
    elif field_name in {"name", "type", "call_sign", "registration", "squawk",
                        "icao24", "pilot", "country", "coalition", "color",
                        "group", "label", "shape", "short_name", "long_name",
                        "full_name", "debug"}:
        setattr(props, field_name, value)
    else:
        # Float fields
        try:
            setattr(props, field_name, float(value))
        except ValueError:
            setattr(props, field_name, value)
