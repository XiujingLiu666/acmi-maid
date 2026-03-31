# acmi-maid Design Specification

**Date:** 2026-03-31
**Status:** Draft

## Overview

acmi-maid is a general-purpose, pure-Python ACMI 2.2 toolset for parsing, writing, editing, and streaming Tacview-compatible ACMI flight recording files. It fills a gap in the Python ecosystem where no well-maintained, feature-complete ACMI library exists.

## Requirements

- **Parse** `.acmi` files (plain text and zip-compressed) into structured Python dataclasses
- **Write** complete `AcmiFile` objects back to `.acmi` format (text or zip)
- **Edit** loaded recordings (modify properties, add/remove objects/events, re-export)
- **Stream** real-time telemetry data via an append-only writer
- **Pure Python** with no required external dependencies (stdlib only: `dataclasses`, `zipfile`, `datetime`, `enum`, etc.)
- **uv** for project/dependency management
- **ACMI 2.1/2.2** spec compliance (Tacview documentation reference). The parser accepts both `FileVersion=2.1` and `FileVersion=2.2` since 2.2 is a superset of 2.1.
- **Python 3.10+** required (uses `X | Y` union syntax at runtime)

## Project Structure

```
acmi_maid/
├── pyproject.toml              # uv-managed package metadata
├── docs/                       # Documentation
│   └── superpowers/specs/      # Design specs
├── src/
│   └── acmi_maid/
│       ├── __init__.py         # Public API re-exports with __all__
│       ├── models.py           # @dataclass definitions (data layer)
│       ├── enums.py            # Enums for types, events, colors
│       ├── parser.py           # AcmiParser: file/stream -> AcmiFile
│       ├── writer.py           # AcmiWriter: AcmiFile -> file/stream
│       ├── streamer.py         # AcmiStreamer: real-time append-only writer
│       └── utils.py            # Coordinate helpers, time conversion
└── tests/
    ├── test_models.py
    ├── test_parser.py
    ├── test_writer.py
    ├── test_streamer.py
    └── fixtures/               # Sample .acmi files for round-trip testing
```

## Data Model (`models.py` + `enums.py`)

### Enums (`enums.py`)

```python
from enum import Enum

class ObjectClass(str, Enum):
    """Primary class tags for ACMI objects."""
    AIR = "Air"
    GROUND = "Ground"
    SEA = "Sea"
    WEAPON = "Weapon"
    SENSOR = "Sensor"
    NAVAID = "Navaid"
    MISC = "Misc"

class ObjectAttribute(str, Enum):
    """Attribute tags (size/role modifiers)."""
    STATIC = "Static"
    HEAVY = "Heavy"
    MEDIUM = "Medium"
    LIGHT = "Light"
    MINOR = "Minor"

class BasicType(str, Enum):
    """Basic type tags."""
    FIXED_WING = "FixedWing"
    ROTORCRAFT = "Rotorcraft"
    ARMOR = "Armor"
    ANTI_AIRCRAFT = "AntiAircraft"
    VEHICLE = "Vehicle"
    WATERCRAFT = "Watercraft"
    HUMAN = "Human"
    BIOLOGIC = "Biologic"
    MISSILE = "Missile"
    ROCKET = "Rocket"
    BOMB = "Bomb"
    TORPEDO = "Torpedo"
    PROJECTILE = "Projectile"
    BEAM = "Beam"
    DECOY = "Decoy"
    BUILDING = "Building"
    BULLSEYE = "Bullseye"
    WAYPOINT = "Waypoint"

class SpecificType(str, Enum):
    """Specific type tags."""
    TANK = "Tank"
    WARSHIP = "Warship"
    AIRCRAFT_CARRIER = "AircraftCarrier"
    SUBMARINE = "Submarine"
    INFANTRY = "Infantry"
    PARACHUTIST = "Parachutist"
    SHELL = "Shell"
    BULLET = "Bullet"
    GRENADE = "Grenade"
    FLARE = "Flare"
    CHAFF = "Chaff"
    SMOKE_GRENADE = "SmokeGrenade"
    AERODROME = "Aerodrome"
    CONTAINER = "Container"
    SHRAPNEL = "Shrapnel"
    EXPLOSION = "Explosion"

class EventType(str, Enum):
    """ACMI event types."""
    MESSAGE = "Message"
    BOOKMARK = "Bookmark"
    DEBUG = "Debug"
    LEFT_AREA = "LeftArea"
    DESTROYED = "Destroyed"
    TAKEN_OFF = "TakenOff"
    LANDED = "Landed"
    TIMEOUT = "Timeout"

class ObjectColor(str, Enum):
    """Predefined ACMI object colors."""
    RED = "Red"
    ORANGE = "Orange"
    YELLOW = "Yellow"
    GREEN = "Green"
    CYAN = "Cyan"
    BLUE = "Blue"
    VIOLET = "Violet"
```

### Dataclasses (`models.py`)

```python
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Transform:
    """Position and orientation in WGS-84 geodetic coordinates.

    Longitude/Latitude in degrees, Altitude in meters MSL.
    Roll/Pitch/Yaw in degrees. U/V in meters (flat-world native coords).
    None means "unchanged from previous frame" (ACMI delta semantics).
    """
    longitude: float | None = None   # degrees, positive = east
    latitude: float | None = None    # degrees, positive = north
    altitude: float | None = None    # meters MSL
    roll: float | None = None        # degrees, positive = right roll
    pitch: float | None = None       # degrees, positive = nose up
    yaw: float | None = None         # degrees, clockwise from true north
    u: float | None = None           # meters, flat-world native X
    v: float | None = None           # meters, flat-world native Y
    heading: float | None = None     # degrees, flat-world heading


@dataclass
class GlobalProperties:
    """ACMI global properties (object ID 0).

    These apply to the entire recording session.
    """
    data_source: str | None = None          # simulator name/version
    data_recorder: str | None = None        # recording software
    reference_time: datetime | None = None  # base UTC time for all timestamps
    recording_time: datetime | None = None  # file creation UTC time
    reference_longitude: float = 0.0        # degrees, added to all object longitudes
    reference_latitude: float = 0.0         # degrees, added to all object latitudes
    author: str | None = None
    title: str | None = None
    category: str | None = None
    briefing: str | None = None
    debriefing: str | None = None
    comments: str | None = None
    map_id: str | None = None               # terrain/location identifier
    extra: dict[str, str] = field(default_factory=dict)


@dataclass
class ObjectProperties:
    """All known ACMI object properties with typed fields.

    None means the property has not been set / is unknown.
    The `extra` dict captures any properties not covered by typed fields,
    ensuring no data is lost during parsing.
    """
    # Identity
    name: str | None = None              # ICAO/NATO designation (e.g. "F/A-18C")
    type: str | None = None              # tag string (e.g. "Air+FixedWing")
    call_sign: str | None = None         # display priority over name
    registration: str | None = None      # tail number
    squawk: str | None = None            # transponder code
    icao24: str | None = None            # Mode S 24-bit address
    pilot: str | None = None             # pilot in command
    country: str | None = None           # ISO 3166-1 alpha-2
    coalition: str | None = None
    color: str | None = None             # ObjectColor value or arbitrary hex (e.g. "0xFF0000")
    group: str | None = None             # formation/group name
    label: str | None = None             # free text displayed in 3D view
    shape: str | None = None             # .obj 3D model filename
    short_name: str | None = None
    long_name: str | None = None
    full_name: str | None = None
    debug: str | None = None

    # Object references (stored as int, displayed as hex)
    parent: int | None = None            # parent object ID
    next: int | None = None              # next linked object ID
    focused_target: int | None = None
    locked_targets: list[int] = field(default_factory=list)  # up to 10

    # Flight dynamics
    ias: float | None = None             # m/s indicated airspeed
    cas: float | None = None             # m/s calibrated airspeed
    tas: float | None = None             # m/s true airspeed
    mach: float | None = None            # Mach number
    aoa: float | None = None             # degrees, angle of attack
    aos: float | None = None             # degrees, angle of sideslip
    agl: float | None = None             # meters above ground level
    hdg: float | None = None             # degrees, true heading
    hdm: float | None = None             # degrees, magnetic heading

    # State
    importance: float | None = None      # object importance factor
    health: float | None = None          # 0.0 = destroyed, 1.0 = pristine
    on_ground: bool | None = None
    disabled: bool | None = None         # out of combat but not destroyed
    visible: float | None = None         # 0.0 = invisible, 1.0 = fully visible

    # Controls & systems
    throttle: float | None = None        # 0.0-1.0
    throttle2: float | None = None       # second engine
    afterburner: float | None = None     # 0.0-1.0
    landing_gear: float | None = None    # 0.0-1.0
    flaps: float | None = None           # 0.0-1.0
    air_brakes: float | None = None      # 0.0-1.0
    tailhook: float | None = None        # 0.0-1.0
    parachute: float | None = None       # 0.0-1.0
    drag_chute: float | None = None      # 0.0-1.0

    # Fuel (up to 10 tanks)
    fuel_weights: list[float | None] = field(default_factory=list)

    # Radar
    radar_mode: int | None = None        # 0 = off
    radar_range: float | None = None     # meters
    radar_azimuth: float | None = None   # degrees
    radar_elevation: float | None = None # degrees
    engagement_range: float | None = None  # meters (SAM/AAA)

    # G-forces
    vertical_g: float | None = None
    longitudinal_g: float | None = None
    lateral_g: float | None = None

    # Dimensions
    length: float | None = None          # meters
    width: float | None = None           # meters
    height: float | None = None          # meters
    radius: float | None = None          # meters

    # Pilot head tracking
    pilot_head_roll: float | None = None   # degrees
    pilot_head_pitch: float | None = None  # degrees
    pilot_head_yaw: float | None = None    # degrees

    # Control inputs
    roll_control_input: float | None = None    # -1.0 to 1.0
    pitch_control_input: float | None = None   # -1.0 to 1.0
    yaw_control_input: float | None = None     # -1.0 to 1.0
    trigger_pressed: bool | None = None

    # Biometrics
    heart_rate: float | None = None      # bpm
    spo2: float | None = None            # ratio

    # Catch-all for unlisted properties
    extra: dict[str, str] = field(default_factory=dict)


@dataclass
class Frame:
    """A snapshot delta of an object's state at a specific time.

    Contains only the properties that changed at this timestamp.
    Keys in `properties` use ACMI-native PascalCase (e.g. "CallSign", "IAS")
    to enable lossless round-trip serialization. The `T=` transform is stored
    exclusively in `transform`, NOT duplicated in `properties`.
    """
    timestamp: float                     # seconds since ReferenceTime
    transform: Transform | None = None   # position/orientation update
    properties: dict[str, str] = field(default_factory=dict)  # PascalCase key=value deltas


@dataclass
class AcmiObject:
    """A tracked object in the ACMI recording.

    `properties` holds the latest merged state (accumulated from all frames).
    `timeline` holds the per-frame deltas in chronological order.
    """
    id: int                              # 64-bit object ID (from hex)
    properties: ObjectProperties = field(default_factory=ObjectProperties)
    timeline: list[Frame] = field(default_factory=list)
    removed: bool = False                # True if object was removed via "-ID"
    removed_at: float | None = None      # timestamp of removal


@dataclass
class Event:
    """An ACMI event record (declared on global object ID 0)."""
    timestamp: float                     # seconds since ReferenceTime
    type: EventType                      # event type enum
    object_ids: list[int] = field(default_factory=list)  # referenced object IDs
    text: str = ""                       # event description


@dataclass
class AcmiFile:
    """Root container for a complete ACMI recording.

    This is the primary data structure returned by the parser
    and accepted by the writer.
    """
    file_type: str = "text/acmi/tacview"
    file_version: str = "2.2"
    globals: GlobalProperties = field(default_factory=GlobalProperties)
    objects: dict[int, AcmiObject] = field(default_factory=dict)  # keyed by object ID
    events: list[Event] = field(default_factory=list)
```

### Raw Record Types (for `iter_records`)

These lightweight types are used by the lazy `iter_records()` iterator, which yields raw parsed lines without building full object state:

```python
from dataclasses import dataclass

@dataclass
class TimeRecord:
    """A timestamp marker (#<seconds>)."""
    timestamp: float

@dataclass
class PropertyRecord:
    """An object property update line (<hex_id>,<props>).
    Timestamp is provided by the preceding TimeRecord in the stream."""
    object_id: int
    properties: dict[str, str]   # PascalCase keys, raw string values
    transform: Transform | None = None

@dataclass
class RemovalRecord:
    """An object removal line (-<hex_id>)."""
    object_id: int
    timestamp: float             # current timestamp when removal was encountered

@dataclass
class EventRecord:
    """An event parsed from an Event= property on object ID 0."""
    event_type: EventType
    object_ids: list[int]
    text: str
    timestamp: float

Record = TimeRecord | PropertyRecord | RemovalRecord | EventRecord
```

## Parser (`parser.py`)

### Exception

```python
class AcmiParseError(Exception):
    """Raised when an ACMI file contains invalid or malformed content."""
    def __init__(self, message: str, line_number: int) -> None:
        self.line_number = line_number
        super().__init__(f"Line {line_number}: {message}")
```

### Public API

```python
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

    @staticmethod
    def iter_records(source: str | Path | IO[str]) -> Iterator[Record]:
        """Lazy iterator over raw records without building full state.

        Yields one of: TimeRecord, PropertyRecord, RemovalRecord, EventRecord.
        Useful for large files or when full state materialization is not needed.
        """
```

### Internal Parsing Flow

1. **Open source**: detect zip vs plain text via magic bytes or extension. When opening file paths, use `encoding='utf-8-sig'` to transparently strip UTF-8 BOM. When receiving an `IO[str]` stream, strip a leading BOM character (`\ufeff`) from the first line if present.
2. **Validate header**: first two lines must be `FileType=text/acmi/tacview` and `FileVersion=2.1` or `FileVersion=2.2`
3. **Escape handling**: ACMI uses backslash-escaped commas (`\,`) within property values. Before splitting a property line on commas, the parser must handle escaped commas by:
   - Splitting on `,` that are NOT preceded by `\`
   - Unescaping `\,` → `,` in the resulting values
   - The writer must re-escape commas in values as `\,` on output
4. **Line-by-line processing**:
   - Comment lines starting with `//` → skip
   - `#<float>` → update current timestamp
   - `-<hex_id>` → mark object as removed at current timestamp
   - `<hex_id>,<props>` → parse comma-separated `Key=Value` pairs (respecting escape rules)
     - Object ID `0`: update `GlobalProperties` fields; collect `Event` entries
     - Other IDs: create `AcmiObject` if new, append `Frame`, merge into `ObjectProperties`
5. **Transform parsing**: detect 3/5/6/9 component forms based on pipe-delimited field count. Empty components between `|` delimiters are set to `None` (unchanged).
6. **Property mapping**: map ACMI property names (PascalCase) to Python field names (snake_case) via a lookup table. Properties in `Frame.properties` retain their original PascalCase keys.
7. **Return**: fully populated `AcmiFile`

### Error Handling

`AcmiParseError` is raised for:
- Missing or invalid header
- Malformed property lines (no `=` separator)
- Invalid object IDs (non-hex)
- Invalid transform format (wrong component count)
- Unrecognized event types (logged as warning, stored in `extra` rather than raising)

### Property Name Mapping

A constant dict maps ACMI PascalCase names to `ObjectProperties` field names. The general rule is `to_snake_case()` conversion, with explicit overrides for abbreviations:

```python
_PROPERTY_MAP = {
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
    # Flight dynamics (abbreviations kept as-is in snake_case)
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

# Reverse mapping for writer output
_REVERSE_PROPERTY_MAP = {v: k for k, v in _PROPERTY_MAP.items()}
```

Properties not found in `_PROPERTY_MAP` go into `ObjectProperties.extra` with their original PascalCase keys preserved.

**Indexed properties:** Properties matching `LockedTarget<N>` (N=0-9) and `FuelWeight<N>` (N=0-9) are parsed into the `locked_targets` and `fuel_weights` list fields by index. The parser recognizes these via regex (`LockedTarget\d+`, `FuelWeight\d+`). The writer serializes list elements back to their indexed ACMI keys (e.g., `fuel_weights[2]` → `FuelWeight2`).

## Writer (`writer.py`)

### Public API

```python
class AcmiWriter:
    """Writes AcmiFile objects to ACMI text format.

    Produces spec-compliant ACMI 2.2 output with LF line endings.
    When writing to a file path, includes a UTF-8 BOM.
    When writing to a caller-provided IO[str] stream, no BOM is written
    (the caller controls encoding, avoiding double-BOM issues).
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

    @staticmethod
    def to_string(acmi: AcmiFile) -> str:
        """Serialize an AcmiFile to a string (no BOM prefix)."""
```

### Writing Flow

1. Write header lines (`FileType`, `FileVersion`)
2. Write global properties at timestamp `#0`
3. Collect all frames from all objects, plus removal events, into a unified timeline sorted by timestamp
4. For each timestamp: write `#<time>`, then each object's property deltas for that time
5. Removal lines (`-<hex_id>`) are written at the timestamp specified by `AcmiObject.removed_at`
6. Property values containing commas are escaped as `\,` on output
7. If `compress=True`, wrap the text content in a zip archive

### Round-Trip Guarantee

`AcmiParser.parse(AcmiWriter.to_string(acmi))` must produce a semantically equivalent `AcmiFile`. This is validated in tests. Note: exact byte-level identity is not guaranteed (e.g., property ordering within a line may differ).

## Streamer (`streamer.py`)

### Public API

```python
class AcmiStreamer:
    """Append-only streaming ACMI writer for real-time telemetry.

    Writes ACMI lines incrementally without buffering the full recording
    in memory. Suitable for live data feeds.

    Property kwargs use ACMI-native PascalCase names (e.g. Name="F-16C")
    to match the wire format directly, since the streamer has no
    ObjectProperties layer to map through.

    Thread safety: NOT thread-safe. Callers must synchronize externally
    if multiple threads write concurrently.

    Compression caveat: When compress=True, output is buffered to a
    temporary file and zipped on close(). This is intended for
    post-session archival; real-time consumers should use compress=False.
    """

    def __init__(self, dest: str | Path | IO[str],
                 globals: GlobalProperties | None = None,
                 compress: bool = False) -> None:
        """Open a stream and write the header + global properties."""

    def write_frame(self, timestamp: float, object_id: int,
                    transform: Transform | None = None,
                    **properties: str) -> None:
        """Write a single object update at the given timestamp.

        Args:
            timestamp: seconds since reference_time
            object_id: hex object ID as int
            transform: optional position/orientation update
            **properties: ACMI PascalCase property key-value pairs
                          (e.g. Name="F-16C", Type="Air+FixedWing")

        Only writes a new #timestamp line if the timestamp has changed
        since the last write.
        """

    def write_event(self, event: Event) -> None:
        """Write an event record. Uses event.timestamp for timing."""

    def remove_object(self, timestamp: float, object_id: int) -> None:
        """Write an object removal line (-ID)."""

    def close(self) -> None:
        """Flush and close the underlying stream."""

    def __enter__(self) -> AcmiStreamer: ...
    def __exit__(self, *args) -> None: ...
```

### Streamer Behavior

- Writes header + globals immediately on construction
- Tracks the last written timestamp to avoid duplicate `#` lines
- Does NOT track object state (append-only, no merging)
- Supports context manager protocol for automatic cleanup
- When `compress=True`, buffers to a temporary file and zips on `close()`. This defeats real-time streaming semantics and is intended only for post-session archival.
- NOT thread-safe; callers must synchronize externally for concurrent writes

## Utilities (`utils.py`)

```python
def parse_transform(value: str) -> Transform:
    """Parse a T= value string into a Transform dataclass.
    Handles 3, 5, 6, and 9 component forms.
    Empty components between | are set to None."""

def format_transform(t: Transform) -> str:
    """Format a Transform into a T= value string.
    Omits trailing None components; uses empty fields for interior Nones."""

def parse_acmi_datetime(value: str) -> datetime:
    """Parse an ACMI datetime string (ISO 8601) into a Python datetime."""

def format_acmi_datetime(dt: datetime) -> str:
    """Format a Python datetime into ACMI ISO 8601 string."""

def to_snake_case(name: str) -> str:
    """Convert PascalCase ACMI property name to snake_case."""

def to_pascal_case(name: str) -> str:
    """Convert snake_case Python field name to PascalCase ACMI property name."""

def split_escaped(line: str, delimiter: str = ",") -> list[str]:
    """Split a string on delimiter, respecting backslash escaping.
    Unescapes \\, -> , in the resulting values."""

def escape_value(value: str) -> str:
    """Escape commas in a property value for ACMI output (\\,)."""
```

## Public API (`__init__.py`)

All user-facing types and classes are re-exported from the package root:

```python
from acmi_maid.models import (
    AcmiFile, AcmiObject, GlobalProperties, ObjectProperties,
    Transform, Frame, Event,
    TimeRecord, PropertyRecord, RemovalRecord, EventRecord, Record,
)
from acmi_maid.enums import (
    EventType, ObjectClass, ObjectAttribute, BasicType,
    SpecificType, ObjectColor,
)
from acmi_maid.parser import AcmiParser, AcmiParseError
from acmi_maid.writer import AcmiWriter
from acmi_maid.streamer import AcmiStreamer

__all__ = [
    # Models
    "AcmiFile", "AcmiObject", "GlobalProperties", "ObjectProperties",
    "Transform", "Frame", "Event",
    "TimeRecord", "PropertyRecord", "RemovalRecord", "EventRecord", "Record",
    # Enums
    "EventType", "ObjectClass", "ObjectAttribute", "BasicType",
    "SpecificType", "ObjectColor",
    # Parser
    "AcmiParser", "AcmiParseError",
    # Writer
    "AcmiWriter",
    # Streamer
    "AcmiStreamer",
]
```

## Usage Examples

### Parsing and Analysis

```python
from acmi_maid import AcmiParser

acmi = AcmiParser.parse("mission.acmi")
print(f"Mission: {acmi.globals.title}")
print(f"Reference time: {acmi.globals.reference_time}")

for obj in acmi.objects.values():
    if obj.properties.type and "FixedWing" in obj.properties.type:
        print(f"  Aircraft: {obj.properties.name} ({obj.properties.pilot})")
        print(f"    Frames: {len(obj.timeline)}")
        if obj.removed:
            print(f"    Destroyed at T+{obj.removed_at:.1f}s")
```

### Writing / Editing

```python
from acmi_maid import AcmiParser, AcmiWriter

acmi = AcmiParser.parse("original.acmi")
acmi.globals.title = "Edited Mission"
acmi.globals.author = "acmi-maid"

# Mark an object as removed (produces a -ID line in output at the specified time)
obj = acmi.objects[0x3001]
obj.removed = True
obj.removed_at = 120.5

# Completely omit an object from output (no trace in the file)
del acmi.objects[0x3002]

AcmiWriter.write(acmi, "edited.acmi", compress=True)
```

### Real-Time Streaming

```python
from acmi_maid import AcmiStreamer, GlobalProperties, Transform, Event, EventType
from datetime import datetime, timezone

globals = GlobalProperties(
    data_source="MySim 1.0",
    data_recorder="acmi-maid",
    reference_time=datetime.now(timezone.utc),
)

# Streamer uses PascalCase kwargs to match ACMI wire format directly
with AcmiStreamer("live.acmi", globals=globals) as stream:
    stream.write_frame(0.0, 0x3001,
        transform=Transform(longitude=-118.5, latitude=34.0, altitude=3000,
                            roll=0, pitch=5, yaw=270),
        Name="F-16C", Type="Air+FixedWing", Pilot="Viper 1")

    stream.write_frame(1.0, 0x3001,
        transform=Transform(longitude=-118.501, latitude=34.001, altitude=3050))

    stream.write_event(Event(
        timestamp=8.0, type=EventType.TAKEN_OFF,
        object_ids=[0x3001], text="Viper 1 airborne"))
```

### Lazy Record Iteration (Large Files)

```python
from acmi_maid import AcmiParser, TimeRecord, PropertyRecord

for record in AcmiParser.iter_records("huge_mission.acmi"):
    if isinstance(record, TimeRecord):
        current_time = record.timestamp
    elif isinstance(record, PropertyRecord):
        if record.object_id == 0x3001 and record.transform:
            print(f"t={current_time}: alt={record.transform.altitude}")
```

## Testing Strategy

- **Unit tests** for each module (`test_models.py`, `test_parser.py`, `test_writer.py`, `test_streamer.py`)
- **Round-trip tests**: parse a fixture file, write it back, parse again, assert semantic equivalence
- **Fixture files** in `tests/fixtures/`: hand-crafted `.acmi` files covering edge cases:
  - Minimal valid file (header only)
  - FileVersion 2.1 compatibility
  - All transform formats (3, 5, 6, 9 components)
  - Delta properties (omitted fields between `|`)
  - Events of each type
  - Object removal
  - Zip-compressed files
  - Unicode content (pilot names, comments)
  - Escaped commas in values (`\,`)
  - UTF-8 BOM handling
  - Comment lines (`//`)

## Error Handling

- `AcmiParseError(message, line_number)` — custom exception raised during parsing for malformed input, includes the offending line number
- `ValueError` — raised by writer/streamer for invalid data (e.g., missing required fields)
- Logging via `logging.getLogger("acmi_maid")` throughout — no `print()` statements

## Non-Goals (Explicit Exclusions)

- 7z compression support (would require external dependency)
- 3D visualization or replay
- Network protocol support (Tacview real-time telemetry protocol)
- Database storage or ORM integration
- pandas/numpy integration in core (users can convert AcmiFile to DataFrames themselves)
