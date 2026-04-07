# acmi-maid Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a pure-Python ACMI 2.2 toolset with parser, writer, streamer, and structured dataclass models.

**Architecture:** Flat data model with `@dataclass` types in `models.py`, enums in `enums.py`, utility functions in `utils.py`, and three consumer modules (`parser.py`, `writer.py`, `streamer.py`). The parser builds full in-memory state; the streamer is append-only. TDD throughout.

**Tech Stack:** Python 3.10+, stdlib only, uv for package management, pytest for testing.

**Spec:** `docs/superpowers/specs/2026-03-31-acmi-maid-design.md`

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/acmi_maid/__init__.py` (empty placeholder)
- Create: `tests/__init__.py` (empty)
- Create: `tests/fixtures/` (directory)
- Create: `.gitignore`

- [ ] **Step 1: Initialize uv project with src layout**

```bash
cd c:/Users/bytimes/lxj/projects/acmi_maid
uv init --lib --python ">=3.10"
```

If uv creates a flat layout, restructure to `src/acmi_maid/`. Ensure `pyproject.toml` has:

```toml
[project]
name = "acmi-maid"
version = "0.1.0"
description = "General-purpose ACMI 2.2 parser, writer, and streamer for Tacview flight recordings"
requires-python = ">=3.10"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/acmi_maid"]
```

- [ ] **Step 2: Add pytest as dev dependency**

```bash
uv add --dev pytest
```

- [ ] **Step 3: Create directory structure**

```bash
mkdir -p src/acmi_maid tests/fixtures
```

Create empty `tests/__init__.py`. Ensure `src/acmi_maid/__init__.py` exists (can be empty for now).

- [ ] **Step 4: Update .gitignore**

Ensure `.gitignore` includes at minimum:

```
__pycache__/
*.pyc
.venv/
dist/
*.egg-info/
.pytest_cache/
```

- [ ] **Step 5: Verify setup**

```bash
uv run pytest --co -q
```

Expected: `no tests ran` (or similar — no errors).

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src/ tests/ .gitignore .python-version uv.lock
git commit -m "feat: scaffold acmi-maid project with uv, src layout, pytest"
```

---

### Task 2: Enums (`enums.py`)

**Files:**
- Create: `src/acmi_maid/enums.py`
- Create: `tests/test_enums.py`

- [ ] **Step 1: Write tests for enums**

Create `tests/test_enums.py`:

```python
from acmi_maid.enums import (
    ObjectClass, ObjectAttribute, BasicType, SpecificType,
    EventType, ObjectColor,
)


def test_object_class_values():
    assert ObjectClass.AIR == "Air"
    assert ObjectClass.GROUND == "Ground"
    assert ObjectClass("Sea") == ObjectClass.SEA


def test_event_type_values():
    assert EventType.DESTROYED == "Destroyed"
    assert EventType.TAKEN_OFF == "TakenOff"
    assert EventType("Landed") == EventType.LANDED


def test_basic_type_values():
    assert BasicType.FIXED_WING == "FixedWing"
    assert BasicType.ROTORCRAFT == "Rotorcraft"
    assert BasicType.MISSILE == "Missile"


def test_specific_type_values():
    assert SpecificType.TANK == "Tank"
    assert SpecificType.FLARE == "Flare"


def test_object_color_values():
    assert ObjectColor.RED == "Red"
    assert ObjectColor.VIOLET == "Violet"


def test_enums_are_str_subclass():
    assert isinstance(ObjectClass.AIR, str)
    assert isinstance(EventType.DESTROYED, str)
    assert isinstance(BasicType.FIXED_WING, str)
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
uv run pytest tests/test_enums.py -v
```
Expected: `ModuleNotFoundError: No module named 'acmi_maid.enums'`

- [ ] **Step 3: Implement enums**

Create `src/acmi_maid/enums.py` with all enums exactly as defined in the spec (lines 49-129):

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

- [ ] **Step 4: Run tests — expect PASS**

```bash
uv run pytest tests/test_enums.py -v
```
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/acmi_maid/enums.py tests/test_enums.py
git commit -m "feat: add ACMI enum types (ObjectClass, EventType, BasicType, etc.)"
```

---

### Task 3: Data Models (`models.py`)

**Files:**
- Create: `src/acmi_maid/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write tests for models**

Create `tests/test_models.py`:

```python
from datetime import datetime, timezone
from acmi_maid.models import (
    Transform, GlobalProperties, ObjectProperties, Frame,
    AcmiObject, Event, AcmiFile,
    TimeRecord, PropertyRecord, RemovalRecord, EventRecord,
)
from acmi_maid.enums import EventType


def test_transform_defaults():
    t = Transform()
    assert t.longitude is None
    assert t.latitude is None
    assert t.altitude is None
    assert t.roll is None
    assert t.yaw is None
    assert t.u is None


def test_transform_with_values():
    t = Transform(longitude=41.6, latitude=41.5, altitude=2000.0,
                  roll=10.0, pitch=5.0, yaw=270.0)
    assert t.longitude == 41.6
    assert t.pitch == 5.0


def test_global_properties_defaults():
    g = GlobalProperties()
    assert g.reference_longitude == 0.0
    assert g.reference_latitude == 0.0
    assert g.data_source is None
    assert g.extra == {}


def test_object_properties_defaults():
    p = ObjectProperties()
    assert p.name is None
    assert p.locked_targets == []
    assert p.fuel_weights == []
    assert p.extra == {}


def test_object_properties_independent_defaults():
    """Each instance should get its own mutable defaults."""
    p1 = ObjectProperties()
    p2 = ObjectProperties()
    p1.locked_targets.append(1)
    assert p2.locked_targets == []


def test_frame():
    f = Frame(timestamp=10.5)
    assert f.timestamp == 10.5
    assert f.transform is None
    assert f.properties == {}


def test_acmi_object():
    obj = AcmiObject(id=0x3001)
    assert obj.id == 0x3001
    assert obj.removed is False
    assert obj.removed_at is None
    assert obj.timeline == []


def test_event():
    e = Event(timestamp=8.0, type=EventType.TAKEN_OFF,
              object_ids=[0x2723], text="Takeoff")
    assert e.type == EventType.TAKEN_OFF
    assert e.object_ids == [0x2723]


def test_acmi_file_defaults():
    f = AcmiFile()
    assert f.file_type == "text/acmi/tacview"
    assert f.file_version == "2.2"
    assert f.objects == {}
    assert f.events == []


def test_record_types():
    tr = TimeRecord(timestamp=47.13)
    assert tr.timestamp == 47.13

    pr = PropertyRecord(object_id=0x3001, properties={"Name": "F-16C"})
    assert pr.transform is None

    rr = RemovalRecord(object_id=0x6A56, timestamp=100.0)
    assert rr.object_id == 0x6A56

    er = EventRecord(event_type=EventType.DESTROYED,
                     object_ids=[0x6A56], text="", timestamp=100.0)
    assert er.event_type == EventType.DESTROYED
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
uv run pytest tests/test_models.py -v
```
Expected: `ModuleNotFoundError: No module named 'acmi_maid.models'`

- [ ] **Step 3: Implement models**

Create `src/acmi_maid/models.py` with all dataclasses exactly as defined in the spec (lines 134-367). This includes: `Transform`, `GlobalProperties`, `ObjectProperties`, `Frame`, `AcmiObject`, `Event`, `AcmiFile`, `TimeRecord`, `PropertyRecord`, `RemovalRecord`, `EventRecord`, and the `Record` type alias.

```python
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from acmi_maid.enums import EventType


@dataclass
class Transform:
    """Position and orientation in WGS-84 geodetic coordinates.

    Longitude/Latitude in degrees, Altitude in meters MSL.
    Roll/Pitch/Yaw in degrees. U/V in meters (flat-world native coords).
    None means "unchanged from previous frame" (ACMI delta semantics).
    """
    longitude: float | None = None
    latitude: float | None = None
    altitude: float | None = None
    roll: float | None = None
    pitch: float | None = None
    yaw: float | None = None
    u: float | None = None
    v: float | None = None
    heading: float | None = None


@dataclass
class GlobalProperties:
    """ACMI global properties (object ID 0)."""
    data_source: str | None = None
    data_recorder: str | None = None
    reference_time: datetime | None = None
    recording_time: datetime | None = None
    reference_longitude: float = 0.0
    reference_latitude: float = 0.0
    author: str | None = None
    title: str | None = None
    category: str | None = None
    briefing: str | None = None
    debriefing: str | None = None
    comments: str | None = None
    map_id: str | None = None
    extra: dict[str, str] = field(default_factory=dict)


@dataclass
class ObjectProperties:
    """All known ACMI object properties with typed fields."""
    # Identity
    name: str | None = None
    type: str | None = None
    call_sign: str | None = None
    registration: str | None = None
    squawk: str | None = None
    icao24: str | None = None
    pilot: str | None = None
    country: str | None = None
    coalition: str | None = None
    color: str | None = None
    group: str | None = None
    label: str | None = None
    shape: str | None = None
    short_name: str | None = None
    long_name: str | None = None
    full_name: str | None = None
    debug: str | None = None
    # References
    parent: int | None = None
    next: int | None = None
    focused_target: int | None = None
    locked_targets: list[int] = field(default_factory=list)
    # Flight dynamics
    ias: float | None = None
    cas: float | None = None
    tas: float | None = None
    mach: float | None = None
    aoa: float | None = None
    aos: float | None = None
    agl: float | None = None
    hdg: float | None = None
    hdm: float | None = None
    # State
    importance: float | None = None
    health: float | None = None
    on_ground: bool | None = None
    disabled: bool | None = None
    visible: float | None = None
    # Controls
    throttle: float | None = None
    throttle2: float | None = None
    afterburner: float | None = None
    landing_gear: float | None = None
    flaps: float | None = None
    air_brakes: float | None = None
    tailhook: float | None = None
    parachute: float | None = None
    drag_chute: float | None = None
    # Fuel
    fuel_weights: list[float | None] = field(default_factory=list)
    # Radar
    radar_mode: int | None = None
    radar_range: float | None = None
    radar_azimuth: float | None = None
    radar_elevation: float | None = None
    engagement_range: float | None = None
    # G-forces
    vertical_g: float | None = None
    longitudinal_g: float | None = None
    lateral_g: float | None = None
    # Dimensions
    length: float | None = None
    width: float | None = None
    height: float | None = None
    radius: float | None = None
    # Pilot head
    pilot_head_roll: float | None = None
    pilot_head_pitch: float | None = None
    pilot_head_yaw: float | None = None
    # Control inputs
    roll_control_input: float | None = None
    pitch_control_input: float | None = None
    yaw_control_input: float | None = None
    trigger_pressed: bool | None = None
    # Biometrics
    heart_rate: float | None = None
    spo2: float | None = None
    # Catch-all
    extra: dict[str, str] = field(default_factory=dict)


@dataclass
class Frame:
    """A snapshot delta of an object's state at a specific time.

    Keys in `properties` use ACMI-native PascalCase.
    The T= transform is in `transform`, NOT in `properties`.
    """
    timestamp: float
    transform: Transform | None = None
    properties: dict[str, str] = field(default_factory=dict)


@dataclass
class AcmiObject:
    """A tracked object in the ACMI recording."""
    id: int
    properties: ObjectProperties = field(default_factory=ObjectProperties)
    timeline: list[Frame] = field(default_factory=list)
    removed: bool = False
    removed_at: float | None = None


@dataclass
class Event:
    """An ACMI event record."""
    timestamp: float
    type: EventType
    object_ids: list[int] = field(default_factory=list)
    text: str = ""


@dataclass
class AcmiFile:
    """Root container for a complete ACMI recording."""
    file_type: str = "text/acmi/tacview"
    file_version: str = "2.2"
    globals: GlobalProperties = field(default_factory=GlobalProperties)
    objects: dict[int, AcmiObject] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)


# --- Raw Record Types (for iter_records) ---

@dataclass
class TimeRecord:
    """A timestamp marker (#<seconds>)."""
    timestamp: float


@dataclass
class PropertyRecord:
    """An object property update line.
    Timestamp is provided by the preceding TimeRecord."""
    object_id: int
    properties: dict[str, str]
    transform: Transform | None = None


@dataclass
class RemovalRecord:
    """An object removal line (-<hex_id>)."""
    object_id: int
    timestamp: float


@dataclass
class EventRecord:
    """An event parsed from an Event= property on object ID 0."""
    event_type: EventType
    object_ids: list[int]
    text: str
    timestamp: float


Record = TimeRecord | PropertyRecord | RemovalRecord | EventRecord
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
uv run pytest tests/test_models.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/acmi_maid/models.py tests/test_models.py
git commit -m "feat: add ACMI dataclass models (AcmiFile, Transform, ObjectProperties, etc.)"
```

---

### Task 4: Utilities (`utils.py`)

**Files:**
- Create: `src/acmi_maid/utils.py`
- Create: `tests/test_utils.py`

- [ ] **Step 1: Write tests for utils**

Create `tests/test_utils.py`:

```python
from datetime import datetime, timezone
from acmi_maid.utils import (
    parse_transform, format_transform,
    parse_acmi_datetime, format_acmi_datetime,
    split_escaped, escape_value,
)
from acmi_maid.models import Transform


class TestParseTransform:
    def test_3_component(self):
        t = parse_transform("41.6251307|41.5910417|2000.14")
        assert t.longitude == 41.6251307
        assert t.latitude == 41.5910417
        assert t.altitude == 2000.14
        assert t.roll is None

    def test_6_component(self):
        t = parse_transform("41.6|41.5|2000|10.5|5.0|270.0")
        assert t.roll == 10.5
        assert t.pitch == 5.0
        assert t.yaw == 270.0

    def test_5_component(self):
        t = parse_transform("41.6|41.5|2000|100.0|200.0")
        assert t.u == 100.0
        assert t.v == 200.0

    def test_9_component(self):
        t = parse_transform("41.6|41.5|2000|10|5|270|100|200|275")
        assert t.u == 100.0
        assert t.v == 200.0
        assert t.heading == 275.0

    def test_empty_components(self):
        t = parse_transform("41.6||2000")
        assert t.longitude == 41.6
        assert t.latitude is None
        assert t.altitude == 2000.0

    def test_all_empty_3(self):
        t = parse_transform("||")
        assert t.longitude is None
        assert t.latitude is None
        assert t.altitude is None

    def test_empty_components_6(self):
        t = parse_transform("41.6||2000|||270")
        assert t.longitude == 41.6
        assert t.latitude is None
        assert t.yaw == 270.0


class TestFormatTransform:
    def test_3_component(self):
        t = Transform(longitude=41.6, latitude=41.5, altitude=2000.0)
        result = format_transform(t)
        assert result == "41.6|41.5|2000.0"

    def test_6_component(self):
        t = Transform(longitude=41.6, latitude=41.5, altitude=2000.0,
                      roll=10.0, pitch=5.0, yaw=270.0)
        result = format_transform(t)
        assert result == "41.6|41.5|2000.0|10.0|5.0|270.0"

    def test_with_interior_nones(self):
        t = Transform(longitude=41.6, altitude=2000.0)
        result = format_transform(t)
        assert result == "41.6||2000.0"

    def test_9_component(self):
        t = Transform(longitude=41.6, latitude=41.5, altitude=2000.0,
                      roll=10.0, pitch=5.0, yaw=270.0,
                      u=100.0, v=200.0, heading=275.0)
        result = format_transform(t)
        assert result == "41.6|41.5|2000.0|10.0|5.0|270.0|100.0|200.0|275.0"

    def test_5_component(self):
        t = Transform(longitude=41.6, latitude=41.5, altitude=2000.0,
                      u=100.0, v=200.0)
        result = format_transform(t)
        assert result == "41.6|41.5|2000.0|100.0|200.0"


class TestAcmiDatetime:
    def test_parse(self):
        dt = parse_acmi_datetime("2011-06-02T05:00:00Z")
        assert dt.year == 2011
        assert dt.month == 6
        assert dt.day == 2
        assert dt.hour == 5
        assert dt.tzinfo == timezone.utc

    def test_format(self):
        dt = datetime(2011, 6, 2, 5, 0, 0, tzinfo=timezone.utc)
        result = format_acmi_datetime(dt)
        assert result == "2011-06-02T05:00:00Z"

    def test_roundtrip(self):
        original = "2023-12-25T14:30:00Z"
        dt = parse_acmi_datetime(original)
        assert format_acmi_datetime(dt) == original


class TestSplitEscaped:
    def test_simple(self):
        assert split_escaped("a,b,c") == ["a", "b", "c"]

    def test_escaped_comma(self):
        assert split_escaped(r"a\,b,c") == ["a,b", "c"]

    def test_no_delimiter(self):
        assert split_escaped("abc") == ["abc"]

    def test_multiple_escapes(self):
        assert split_escaped(r"a\,b\,c,d") == ["a,b,c", "d"]


class TestEscapeValue:
    def test_no_commas(self):
        assert escape_value("hello") == "hello"

    def test_with_comma(self):
        assert escape_value("hello,world") == r"hello\,world"

    def test_roundtrip(self):
        original = "value,with,commas"
        escaped = escape_value(original)
        parts = split_escaped(escaped)
        assert parts == [original]


class TestToSnakeCase:
    def test_pascal(self):
        from acmi_maid.utils import to_snake_case
        assert to_snake_case("CallSign") == "call_sign"
        assert to_snake_case("OnGround") == "on_ground"
        assert to_snake_case("LandingGear") == "landing_gear"

    def test_abbreviation(self):
        from acmi_maid.utils import to_snake_case
        assert to_snake_case("IAS") == "ias"
        assert to_snake_case("ICAO24") == "icao24"


class TestToPascalCase:
    def test_snake(self):
        from acmi_maid.utils import to_pascal_case
        assert to_pascal_case("call_sign") == "CallSign"
        assert to_pascal_case("on_ground") == "OnGround"

    def test_single_word(self):
        from acmi_maid.utils import to_pascal_case
        assert to_pascal_case("name") == "Name"
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
uv run pytest tests/test_utils.py -v
```

- [ ] **Step 3: Implement utils**

Create `src/acmi_maid/utils.py`:

```python
from __future__ import annotations

import re
from datetime import datetime, timezone

from acmi_maid.models import Transform


def parse_transform(value: str) -> Transform:
    """Parse a T= value string into a Transform dataclass.
    Handles 3, 5, 6, and 9 component forms.
    Empty components between | are set to None.
    """
    parts = value.split("|")
    count = len(parts)

    def _float_or_none(s: str) -> float | None:
        s = s.strip()
        return float(s) if s else None

    if count == 3:
        return Transform(
            longitude=_float_or_none(parts[0]),
            latitude=_float_or_none(parts[1]),
            altitude=_float_or_none(parts[2]),
        )
    elif count == 5:
        return Transform(
            longitude=_float_or_none(parts[0]),
            latitude=_float_or_none(parts[1]),
            altitude=_float_or_none(parts[2]),
            u=_float_or_none(parts[3]),
            v=_float_or_none(parts[4]),
        )
    elif count == 6:
        return Transform(
            longitude=_float_or_none(parts[0]),
            latitude=_float_or_none(parts[1]),
            altitude=_float_or_none(parts[2]),
            roll=_float_or_none(parts[3]),
            pitch=_float_or_none(parts[4]),
            yaw=_float_or_none(parts[5]),
        )
    elif count == 9:
        return Transform(
            longitude=_float_or_none(parts[0]),
            latitude=_float_or_none(parts[1]),
            altitude=_float_or_none(parts[2]),
            roll=_float_or_none(parts[3]),
            pitch=_float_or_none(parts[4]),
            yaw=_float_or_none(parts[5]),
            u=_float_or_none(parts[6]),
            v=_float_or_none(parts[7]),
            heading=_float_or_none(parts[8]),
        )
    else:
        raise ValueError(f"Invalid transform component count: {count}")


def format_transform(t: Transform) -> str:
    """Format a Transform into a T= value string.
    Determines the form (3/5/6/9) based on which fields are set,
    then omits trailing Nones but preserves interior Nones as empty.
    """
    # Determine form: 9 > 6 > 5 > 3
    if t.heading is not None or (t.u is not None and t.roll is not None):
        vals = [t.longitude, t.latitude, t.altitude,
                t.roll, t.pitch, t.yaw,
                t.u, t.v, t.heading]
    elif t.roll is not None or t.pitch is not None or t.yaw is not None:
        vals = [t.longitude, t.latitude, t.altitude,
                t.roll, t.pitch, t.yaw]
    elif t.u is not None or t.v is not None:
        vals = [t.longitude, t.latitude, t.altitude,
                t.u, t.v]
    else:
        vals = [t.longitude, t.latitude, t.altitude]

    # Strip trailing Nones
    while vals and vals[-1] is None:
        vals.pop()

    def _fmt(v: float | None) -> str:
        if v is None:
            return ""
        # Use repr-free formatting: strip unnecessary trailing zeros
        if v == int(v):
            return str(float(v))
        return str(v)

    return "|".join(_fmt(v) for v in vals)


def parse_acmi_datetime(value: str) -> datetime:
    """Parse an ACMI datetime string (ISO 8601) into a Python datetime."""
    # Handle the Z suffix (UTC)
    value = value.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def format_acmi_datetime(dt: datetime) -> str:
    """Format a Python datetime into ACMI ISO 8601 string."""
    s = dt.isoformat()
    # Replace +00:00 with Z for UTC
    if s.endswith("+00:00"):
        s = s[:-6] + "Z"
    return s


def split_escaped(line: str, delimiter: str = ",") -> list[str]:
    """Split a string on delimiter, respecting backslash escaping.
    Unescapes \\, -> , in the resulting values.
    """
    result: list[str] = []
    current: list[str] = []
    i = 0
    while i < len(line):
        if line[i] == "\\" and i + 1 < len(line) and line[i + 1] == delimiter:
            current.append(delimiter)
            i += 2
        elif line[i] == delimiter:
            result.append("".join(current))
            current = []
            i += 1
        else:
            current.append(line[i])
            i += 1
    result.append("".join(current))
    return result


def escape_value(value: str) -> str:
    """Escape commas in a property value for ACMI output."""
    return value.replace(",", "\\,")


def to_snake_case(name: str) -> str:
    """Convert PascalCase ACMI property name to snake_case."""
    result = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    result = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", result)
    return result.lower()


def to_pascal_case(name: str) -> str:
    """Convert snake_case Python field name to PascalCase ACMI property name."""
    return "".join(word.capitalize() for word in name.split("_"))


# Shared reverse mapping: GlobalProperties field -> ACMI key
GLOBAL_REVERSE_MAP: dict[str, str] = {
    "data_source": "DataSource", "data_recorder": "DataRecorder",
    "reference_time": "ReferenceTime", "recording_time": "RecordingTime",
    "reference_longitude": "ReferenceLongitude",
    "reference_latitude": "ReferenceLatitude",
    "author": "Author", "title": "Title", "category": "Category",
    "briefing": "Briefing", "debriefing": "Debriefing",
    "comments": "Comments", "map_id": "MapId",
}
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
uv run pytest tests/test_utils.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/acmi_maid/utils.py tests/test_utils.py
git commit -m "feat: add ACMI utility functions (transform parsing, datetime, escaping)"
```

---

### Task 5: Parser (`parser.py`)

**Files:**
- Create: `src/acmi_maid/parser.py`
- Create: `tests/test_parser.py`
- Create: `tests/fixtures/minimal.acmi`
- Create: `tests/fixtures/full_mission.acmi`
- Create: `tests/fixtures/v21.acmi`

- [ ] **Step 1: Create test fixture files**

Create `tests/fixtures/minimal.acmi` (UTF-8 with BOM):

```
FileType=text/acmi/tacview
FileVersion=2.2
```

Create `tests/fixtures/full_mission.acmi`:

```
FileType=text/acmi/tacview
FileVersion=2.2
0,ReferenceTime=2023-12-25T10:00:00Z,Title=Test Mission,DataSource=TestSim,ReferenceLongitude=0,ReferenceLatitude=0
#0
3001,T=41.6|41.5|2000|10|5|270,Name=F-16C,Type=Air+FixedWing,Pilot=Viper 1,Country=us,Coalition=Blue
3002,T=42.0|42.0|3000|0|0|90,Name=MiG-29,Type=Air+FixedWing,Pilot=Bandit 1,Coalition=Red
#10.5
3001,T=41.7||2100|||275
3002,T=42.1||3100
#20.0
3001,T=41.8||2200,IAS=150.5,Throttle=0.8
0,Event=TakenOff|3001|Viper 1 airborne
#30.0
-3002
0,Event=Destroyed|3002|MiG-29 shot down
```

Create `tests/fixtures/v21.acmi`:

```
FileType=text/acmi/tacview
FileVersion=2.1
0,ReferenceTime=2023-01-01T00:00:00Z
```

- [ ] **Step 2: Write parser tests**

Create `tests/test_parser.py`:

```python
import io
import os
import zipfile
from pathlib import Path

from acmi_maid.parser import AcmiParser, AcmiParseError
from acmi_maid.models import (
    AcmiFile, TimeRecord, PropertyRecord, RemovalRecord, EventRecord,
)
from acmi_maid.enums import EventType

FIXTURES = Path(__file__).parent / "fixtures"


class TestParseMinimal:
    def test_parse_minimal(self):
        acmi = AcmiParser.parse(FIXTURES / "minimal.acmi")
        assert acmi.file_type == "text/acmi/tacview"
        assert acmi.file_version == "2.2"
        assert acmi.objects == {}

    def test_parse_v21(self):
        acmi = AcmiParser.parse(FIXTURES / "v21.acmi")
        assert acmi.file_version == "2.1"


class TestParseFullMission:
    def test_globals(self):
        acmi = AcmiParser.parse(FIXTURES / "full_mission.acmi")
        assert acmi.globals.title == "Test Mission"
        assert acmi.globals.data_source == "TestSim"
        assert acmi.globals.reference_time is not None
        assert acmi.globals.reference_time.year == 2023

    def test_objects(self):
        acmi = AcmiParser.parse(FIXTURES / "full_mission.acmi")
        assert 0x3001 in acmi.objects
        assert 0x3002 in acmi.objects
        obj1 = acmi.objects[0x3001]
        assert obj1.properties.name == "F-16C"
        assert obj1.properties.pilot == "Viper 1"
        assert obj1.properties.country == "us"

    def test_timeline(self):
        acmi = AcmiParser.parse(FIXTURES / "full_mission.acmi")
        obj1 = acmi.objects[0x3001]
        assert len(obj1.timeline) == 3  # at t=0, t=10.5, t=20.0
        assert obj1.timeline[0].timestamp == 0.0
        assert obj1.timeline[0].transform is not None
        assert obj1.timeline[0].transform.longitude == 41.6

    def test_delta_transform(self):
        acmi = AcmiParser.parse(FIXTURES / "full_mission.acmi")
        obj1 = acmi.objects[0x3001]
        frame1 = obj1.timeline[1]  # t=10.5
        assert frame1.transform.longitude == 41.7
        assert frame1.transform.latitude is None  # unchanged
        assert frame1.transform.altitude == 2100.0

    def test_removal(self):
        acmi = AcmiParser.parse(FIXTURES / "full_mission.acmi")
        obj2 = acmi.objects[0x3002]
        assert obj2.removed is True
        assert obj2.removed_at == 30.0

    def test_events(self):
        acmi = AcmiParser.parse(FIXTURES / "full_mission.acmi")
        assert len(acmi.events) == 2
        assert acmi.events[0].type == EventType.TAKEN_OFF
        assert 0x3001 in acmi.events[0].object_ids
        assert acmi.events[1].type == EventType.DESTROYED

    def test_numeric_properties(self):
        acmi = AcmiParser.parse(FIXTURES / "full_mission.acmi")
        obj1 = acmi.objects[0x3001]
        assert obj1.properties.ias == 150.5
        assert obj1.properties.throttle == 0.8


class TestParseFromStream:
    def test_parse_from_string_io(self):
        content = "FileType=text/acmi/tacview\nFileVersion=2.2\n"
        acmi = AcmiParser.parse(io.StringIO(content))
        assert acmi.file_version == "2.2"

    def test_parse_with_bom_stream(self):
        content = "\ufeffFileType=text/acmi/tacview\nFileVersion=2.2\n"
        acmi = AcmiParser.parse(io.StringIO(content))
        assert acmi.file_version == "2.2"

    def test_parse_with_comments(self):
        content = (
            "FileType=text/acmi/tacview\n"
            "FileVersion=2.2\n"
            "// This is a comment\n"
            "0,Title=Test\n"
        )
        acmi = AcmiParser.parse(io.StringIO(content))
        assert acmi.globals.title == "Test"


class TestParseZip:
    def test_parse_zip(self, tmp_path):
        text = "FileType=text/acmi/tacview\nFileVersion=2.2\n0,Title=Zipped\n"
        zip_path = tmp_path / "test.zip.acmi"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("mission.acmi", text)
        acmi = AcmiParser.parse(zip_path)
        assert acmi.globals.title == "Zipped"


class TestParseErrors:
    def test_invalid_header(self):
        try:
            AcmiParser.parse(io.StringIO("not a valid header\n"))
            assert False, "Should have raised AcmiParseError"
        except AcmiParseError as e:
            assert e.line_number == 1

    def test_bad_version(self):
        try:
            AcmiParser.parse(io.StringIO(
                "FileType=text/acmi/tacview\nFileVersion=3.0\n"
            ))
            assert False, "Should have raised AcmiParseError"
        except AcmiParseError as e:
            assert e.line_number == 2


class TestParseEscapedCommas:
    def test_escaped_comma_in_value(self):
        content = (
            "FileType=text/acmi/tacview\n"
            "FileVersion=2.2\n"
            r"0,Title=Hello\, World" + "\n"
        )
        acmi = AcmiParser.parse(io.StringIO(content))
        assert acmi.globals.title == "Hello, World"


class TestParseIndexedProperties:
    def test_locked_targets(self):
        content = (
            "FileType=text/acmi/tacview\n"
            "FileVersion=2.2\n"
            "#0\n"
            "3001,Name=F-16C,LockedTarget0=4001,LockedTarget1=4002\n"
        )
        acmi = AcmiParser.parse(io.StringIO(content))
        obj = acmi.objects[0x3001]
        assert len(obj.properties.locked_targets) == 2
        assert obj.properties.locked_targets[0] == 0x4001
        assert obj.properties.locked_targets[1] == 0x4002

    def test_fuel_weights(self):
        content = (
            "FileType=text/acmi/tacview\n"
            "FileVersion=2.2\n"
            "#0\n"
            "3001,Name=F-16C,FuelWeight0=2500.0,FuelWeight1=1200.5\n"
        )
        acmi = AcmiParser.parse(io.StringIO(content))
        obj = acmi.objects[0x3001]
        assert len(obj.properties.fuel_weights) == 2
        assert obj.properties.fuel_weights[0] == 2500.0
        assert obj.properties.fuel_weights[1] == 1200.5


class TestParseUnicode:
    def test_unicode_pilot_name(self):
        content = (
            "FileType=text/acmi/tacview\n"
            "FileVersion=2.2\n"
            "#0\n"
            "3001,Name=Su-27,Pilot=\u041f\u0435\u0442\u0440\u043e\u0432\n"
        )
        acmi = AcmiParser.parse(io.StringIO(content))
        assert acmi.objects[0x3001].properties.pilot == "\u041f\u0435\u0442\u0440\u043e\u0432"

    def test_unicode_title(self):
        content = (
            "FileType=text/acmi/tacview\n"
            "FileVersion=2.2\n"
            "0,Title=\u4efb\u52a1\u6d4b\u8bd5\n"
        )
        acmi = AcmiParser.parse(io.StringIO(content))
        assert acmi.globals.title == "\u4efb\u52a1\u6d4b\u8bd5"


class TestIterRecords:
    def test_iter_records(self):
        content = (
            "FileType=text/acmi/tacview\n"
            "FileVersion=2.2\n"
            "#0\n"
            "3001,T=41.6|41.5|2000,Name=F-16\n"
            "#10\n"
            "-3001\n"
        )
        records = list(AcmiParser.iter_records(io.StringIO(content)))
        assert isinstance(records[0], TimeRecord)
        assert records[0].timestamp == 0.0
        assert isinstance(records[1], PropertyRecord)
        assert records[1].object_id == 0x3001
        assert isinstance(records[2], TimeRecord)
        assert isinstance(records[3], RemovalRecord)
```

- [ ] **Step 3: Run tests — expect FAIL**

```bash
uv run pytest tests/test_parser.py -v
```

- [ ] **Step 4: Implement the parser**

Create `src/acmi_maid/parser.py`. The implementation must follow the parsing flow in the spec (lines 416-433). Key details:

- Use `encoding='utf-8-sig'` when opening file paths
- Strip BOM from `IO[str]` streams
- Accept FileVersion 2.1 and 2.2
- Use `split_escaped()` for comma handling
- Use `parse_transform()` for T= values
- Use `_PROPERTY_MAP` (defined in this file) for property name mapping
- Handle indexed properties (`LockedTarget<N>`, `FuelWeight<N>`) via regex
- Map boolean properties (`OnGround`, `Disabled`, `TriggerPressed`) converting "1"→True, "0"→False
- Map numeric properties (float/int) via field type introspection
- Store unmapped properties in `ObjectProperties.extra`

```python
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
    # (full mapping as in spec lines 449-524)
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
        # Check for zip
        if path.suffix == ".acmi" or str(path).endswith(".zip.acmi"):
            try:
                with open(path, "rb") as f:
                    magic = f.read(4)
                if magic[:2] == b"PK":
                    zf = zipfile.ZipFile(path, "r")
                    name = zf.namelist()[0]
                    raw = zf.read(name)
                    zf.close()
                    return io.StringIO(raw.decode("utf-8-sig")), False
            except (zipfile.BadZipFile, IndexError):
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
        props.locked_targets[idx] = int(value, 16)
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
    """Parses ACMI files into structured AcmiFile objects."""

    @staticmethod
    def parse(source: str | Path | IO[str]) -> AcmiFile:
        stream, should_close = _open_source(source)
        try:
            return _parse_stream(stream)
        finally:
            if should_close:
                stream.close()

    @staticmethod
    def iter_records(source: str | Path | IO[str]) -> Iterator[Record]:
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
```

- [ ] **Step 5: Run tests — expect PASS**

```bash
uv run pytest tests/test_parser.py -v
```

- [ ] **Step 6: Commit**

```bash
git add src/acmi_maid/parser.py tests/test_parser.py tests/fixtures/
git commit -m "feat: implement ACMI parser with full property mapping and iter_records"
```

---

### Task 6: Writer (`writer.py`)

**Files:**
- Create: `src/acmi_maid/writer.py`
- Create: `tests/test_writer.py`

- [ ] **Step 1: Write writer tests**

Create `tests/test_writer.py`:

```python
import io
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from acmi_maid.models import (
    AcmiFile, AcmiObject, GlobalProperties, ObjectProperties,
    Transform, Frame, Event,
)
from acmi_maid.enums import EventType
from acmi_maid.parser import AcmiParser
from acmi_maid.writer import AcmiWriter


def _make_acmi() -> AcmiFile:
    """Build a test AcmiFile with known data."""
    acmi = AcmiFile()
    acmi.globals = GlobalProperties(
        data_source="TestSim",
        reference_time=datetime(2023, 12, 25, 10, 0, 0, tzinfo=timezone.utc),
        title="Test Mission",
    )
    obj = AcmiObject(id=0x3001)
    obj.properties = ObjectProperties(
        name="F-16C", type="Air+FixedWing", pilot="Viper 1",
    )
    obj.timeline = [
        Frame(
            timestamp=0.0,
            transform=Transform(longitude=41.6, latitude=41.5, altitude=2000.0,
                                roll=10.0, pitch=5.0, yaw=270.0),
            properties={"Name": "F-16C", "Type": "Air+FixedWing", "Pilot": "Viper 1"},
        ),
        Frame(
            timestamp=10.0,
            transform=Transform(longitude=41.7, altitude=2100.0),
            properties={},
        ),
    ]
    acmi.objects[0x3001] = obj

    obj2 = AcmiObject(id=0x3002)
    obj2.properties = ObjectProperties(name="MiG-29")
    obj2.timeline = [
        Frame(
            timestamp=0.0,
            transform=Transform(longitude=42.0, latitude=42.0, altitude=3000.0),
            properties={"Name": "MiG-29"},
        ),
    ]
    obj2.removed = True
    obj2.removed_at = 30.0
    acmi.objects[0x3002] = obj2

    acmi.events = [
        Event(timestamp=20.0, type=EventType.TAKEN_OFF,
              object_ids=[0x3001], text="Viper 1 airborne"),
    ]
    return acmi


class TestWriterToString:
    def test_header(self):
        acmi = AcmiFile()
        text = AcmiWriter.to_string(acmi)
        lines = text.split("\n")
        assert lines[0] == "FileType=text/acmi/tacview"
        assert lines[1] == "FileVersion=2.2"

    def test_globals(self):
        acmi = _make_acmi()
        text = AcmiWriter.to_string(acmi)
        assert "Title=Test Mission" in text
        assert "DataSource=TestSim" in text
        assert "ReferenceTime=2023-12-25T10:00:00Z" in text

    def test_objects(self):
        acmi = _make_acmi()
        text = AcmiWriter.to_string(acmi)
        assert "3001," in text
        assert "Name=F-16C" in text

    def test_removal(self):
        acmi = _make_acmi()
        text = AcmiWriter.to_string(acmi)
        assert "-3002" in text

    def test_events(self):
        acmi = _make_acmi()
        text = AcmiWriter.to_string(acmi)
        assert "Event=TakenOff|3001|Viper 1 airborne" in text

    def test_escape_commas(self):
        acmi = AcmiFile()
        acmi.globals.title = "Hello, World"
        text = AcmiWriter.to_string(acmi)
        assert r"Title=Hello\, World" in text


class TestRoundTrip:
    def test_roundtrip(self):
        acmi = _make_acmi()
        text = AcmiWriter.to_string(acmi)
        parsed = AcmiParser.parse(io.StringIO(text))

        assert parsed.globals.title == acmi.globals.title
        assert parsed.globals.data_source == acmi.globals.data_source
        assert 0x3001 in parsed.objects
        assert parsed.objects[0x3001].properties.name == "F-16C"
        assert parsed.objects[0x3002].removed is True
        assert len(parsed.events) == 1
        assert parsed.events[0].type == EventType.TAKEN_OFF

    def test_roundtrip_fixture(self):
        fixtures = Path(__file__).parent / "fixtures"
        original = AcmiParser.parse(fixtures / "full_mission.acmi")
        text = AcmiWriter.to_string(original)
        reparsed = AcmiParser.parse(io.StringIO(text))

        assert reparsed.globals.title == original.globals.title
        assert len(reparsed.objects) == len(original.objects)
        for oid in original.objects:
            assert oid in reparsed.objects
            assert (reparsed.objects[oid].properties.name
                    == original.objects[oid].properties.name)


class TestWriteFile:
    def test_write_to_file(self, tmp_path):
        acmi = _make_acmi()
        out = tmp_path / "output.acmi"
        AcmiWriter.write(acmi, out)
        assert out.exists()
        parsed = AcmiParser.parse(out)
        assert parsed.globals.title == "Test Mission"

    def test_write_compressed(self, tmp_path):
        acmi = _make_acmi()
        out = tmp_path / "output.zip.acmi"
        AcmiWriter.write(acmi, out, compress=True)
        assert out.exists()
        # Verify it's a valid zip
        assert zipfile.is_zipfile(out)
        parsed = AcmiParser.parse(out)
        assert parsed.globals.title == "Test Mission"

    def test_write_to_stream(self):
        acmi = _make_acmi()
        buf = io.StringIO()
        AcmiWriter.write(acmi, buf)
        text = buf.getvalue()
        assert "FileType=text/acmi/tacview" in text
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
uv run pytest tests/test_writer.py -v
```

- [ ] **Step 3: Implement writer**

Create `src/acmi_maid/writer.py`:

```python
from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import IO

from acmi_maid.models import AcmiFile, AcmiObject, Event, Frame, GlobalProperties
from acmi_maid.utils import escape_value, format_acmi_datetime, format_transform, GLOBAL_REVERSE_MAP


def _format_global_props(gp: GlobalProperties) -> list[str]:
    """Format global properties as Key=Value pairs."""
    parts: list[str] = []
    for field_name, acmi_key in GLOBAL_REVERSE_MAP.items():
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
    """Writes AcmiFile objects to ACMI text format."""

    @staticmethod
    def write(acmi: AcmiFile, dest: str | Path | IO[str],
              compress: bool = False) -> None:
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
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
uv run pytest tests/test_writer.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/acmi_maid/writer.py tests/test_writer.py
git commit -m "feat: implement ACMI writer with round-trip support and zip compression"
```

---

### Task 7: Streamer (`streamer.py`)

**Files:**
- Create: `src/acmi_maid/streamer.py`
- Create: `tests/test_streamer.py`

- [ ] **Step 1: Write streamer tests**

Create `tests/test_streamer.py`:

```python
import io
import zipfile
from datetime import datetime, timezone

from acmi_maid.models import GlobalProperties, Transform, Event
from acmi_maid.enums import EventType
from acmi_maid.parser import AcmiParser
from acmi_maid.streamer import AcmiStreamer


def test_basic_stream():
    buf = io.StringIO()
    gp = GlobalProperties(
        data_source="TestSim",
        reference_time=datetime(2023, 1, 1, tzinfo=timezone.utc),
    )
    with AcmiStreamer(buf, globals=gp) as s:
        s.write_frame(0.0, 0x3001,
                      transform=Transform(longitude=41.6, latitude=41.5, altitude=2000.0),
                      Name="F-16C", Type="Air+FixedWing")
        s.write_frame(10.0, 0x3001,
                      transform=Transform(longitude=41.7))

    text = buf.getvalue()
    assert "FileType=text/acmi/tacview" in text
    assert "FileVersion=2.2" in text
    assert "DataSource=TestSim" in text
    assert "Name=F-16C" in text
    assert "#0" in text or "#0.0" in text
    assert "#10" in text or "#10.0" in text


def test_no_duplicate_timestamps():
    buf = io.StringIO()
    with AcmiStreamer(buf) as s:
        s.write_frame(0.0, 0x3001,
                      transform=Transform(longitude=1.0, latitude=2.0, altitude=3.0))
        s.write_frame(0.0, 0x3002,
                      transform=Transform(longitude=4.0, latitude=5.0, altitude=6.0))

    text = buf.getvalue()
    # Should only have one #0 line
    lines = text.split("\n")
    time_lines = [l for l in lines if l.startswith("#0")]
    assert len(time_lines) == 1


def test_event_writing():
    buf = io.StringIO()
    with AcmiStreamer(buf) as s:
        s.write_event(Event(
            timestamp=5.0, type=EventType.TAKEN_OFF,
            object_ids=[0x3001], text="Airborne"))

    text = buf.getvalue()
    assert "Event=TakenOff|3001|Airborne" in text


def test_remove_object():
    buf = io.StringIO()
    with AcmiStreamer(buf) as s:
        s.write_frame(0.0, 0x3001,
                      transform=Transform(longitude=1.0, latitude=2.0, altitude=3.0))
        s.remove_object(10.0, 0x3001)

    text = buf.getvalue()
    assert "-3001" in text


def test_streamer_roundtrip():
    buf = io.StringIO()
    gp = GlobalProperties(
        data_source="TestSim",
        reference_time=datetime(2023, 1, 1, tzinfo=timezone.utc),
        title="Stream Test",
    )
    with AcmiStreamer(buf, globals=gp) as s:
        s.write_frame(0.0, 0x3001,
                      transform=Transform(longitude=41.6, latitude=41.5, altitude=2000.0,
                                          roll=10.0, pitch=5.0, yaw=270.0),
                      Name="F-16C", Type="Air+FixedWing")

    text = buf.getvalue()
    acmi = AcmiParser.parse(io.StringIO(text))
    assert acmi.globals.title == "Stream Test"
    assert 0x3001 in acmi.objects
    assert acmi.objects[0x3001].properties.name == "F-16C"


def test_streamer_to_file(tmp_path):
    out = tmp_path / "stream.acmi"
    with AcmiStreamer(out) as s:
        s.write_frame(0.0, 0x3001,
                      transform=Transform(longitude=1.0, latitude=2.0, altitude=3.0),
                      Name="Test")
    acmi = AcmiParser.parse(out)
    assert 0x3001 in acmi.objects


def test_streamer_compressed(tmp_path):
    out = tmp_path / "stream.zip.acmi"
    with AcmiStreamer(out, compress=True) as s:
        s.write_frame(0.0, 0x3001,
                      transform=Transform(longitude=1.0, latitude=2.0, altitude=3.0),
                      Name="Test")
    assert zipfile.is_zipfile(out)
    acmi = AcmiParser.parse(out)
    assert 0x3001 in acmi.objects
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
uv run pytest tests/test_streamer.py -v
```

- [ ] **Step 3: Implement streamer**

Create `src/acmi_maid/streamer.py`:

```python
from __future__ import annotations

import io
import tempfile
import zipfile
from pathlib import Path
from typing import IO

from acmi_maid.models import Event, GlobalProperties, Transform
from acmi_maid.utils import escape_value, format_acmi_datetime, format_transform, GLOBAL_REVERSE_MAP


class AcmiStreamer:
    """Append-only streaming ACMI writer for real-time telemetry."""

    def __init__(
        self,
        dest: str | Path | IO[str],
        globals: GlobalProperties | None = None,
        compress: bool = False,
    ) -> None:
        self._compress = compress
        self._dest_path: Path | None = None
        self._owns_stream = False

        if isinstance(dest, (str, Path)):
            self._dest_path = Path(dest)
            if compress:
                self._tmp = tempfile.NamedTemporaryFile(
                    mode="w", suffix=".acmi", delete=False, encoding="utf-8",
                    newline="",
                )
                self._stream: IO[str] = self._tmp
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
            for field_name, acmi_key in GLOBAL_REVERSE_MAP.items():
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
        self._ensure_timestamp(timestamp)
        parts: list[str] = [f"{object_id:x}"]
        if transform is not None:
            parts.append(f"T={format_transform(transform)}")
        for key, value in properties.items():
            parts.append(f"{key}={escape_value(str(value))}")
        self._stream.write(",".join(parts) + "\n")

    def write_event(self, event: Event) -> None:
        self._ensure_timestamp(event.timestamp)
        parts = [event.type.value]
        parts.extend(format(oid, "x") for oid in event.object_ids)
        if event.text:
            parts.append(event.text)
        self._stream.write(f"0,Event={'|'.join(parts)}\n")

    def remove_object(self, timestamp: float, object_id: int) -> None:
        self._ensure_timestamp(timestamp)
        self._stream.write(f"-{object_id:x}\n")

    def close(self) -> None:
        if self._compress and self._dest_path and self._owns_stream:
            self._stream.flush()
            tmp_path = self._tmp.name
            self._tmp.close()
            with open(tmp_path, "r", encoding="utf-8") as f:
                content = f.read()
            with zipfile.ZipFile(
                self._dest_path, "w", zipfile.ZIP_DEFLATED
            ) as zf:
                zf.writestr("mission.acmi", content)
            import os
            os.unlink(tmp_path)
        elif self._owns_stream:
            self._stream.close()

    def __enter__(self) -> AcmiStreamer:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
uv run pytest tests/test_streamer.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/acmi_maid/streamer.py tests/test_streamer.py
git commit -m "feat: implement ACMI streamer for real-time append-only writing"
```

---

### Task 8: Public API (`__init__.py`) and Full Test Suite

**Files:**
- Modify: `src/acmi_maid/__init__.py`

- [ ] **Step 1: Write `__init__.py` with all re-exports**

Update `src/acmi_maid/__init__.py`:

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
    "AcmiFile", "AcmiObject", "GlobalProperties", "ObjectProperties",
    "Transform", "Frame", "Event",
    "TimeRecord", "PropertyRecord", "RemovalRecord", "EventRecord", "Record",
    "EventType", "ObjectClass", "ObjectAttribute", "BasicType",
    "SpecificType", "ObjectColor",
    "AcmiParser", "AcmiParseError",
    "AcmiWriter",
    "AcmiStreamer",
]
```

- [ ] **Step 2: Run full test suite**

```bash
uv run pytest -v
```

Expected: ALL tests pass across test_enums, test_models, test_utils, test_parser, test_writer, test_streamer.

- [ ] **Step 3: Commit**

```bash
git add src/acmi_maid/__init__.py
git commit -m "feat: add public API with __all__ re-exports"
```

---

### Task 9: Integration Test & Final Verification

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test**

Create `tests/test_integration.py`:

```python
"""End-to-end integration tests for acmi-maid."""
import io
from datetime import datetime, timezone

from acmi_maid import (
    AcmiFile, AcmiObject, AcmiParser, AcmiWriter, AcmiStreamer,
    GlobalProperties, ObjectProperties, Transform, Frame, Event,
    EventType,
)


def test_full_workflow():
    """Build -> write -> parse -> verify -> edit -> write -> parse again."""
    # Build
    acmi = AcmiFile()
    acmi.globals = GlobalProperties(
        data_source="IntegrationTest",
        data_recorder="acmi-maid",
        reference_time=datetime(2023, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        title="Integration Test Mission",
    )

    f16 = AcmiObject(id=0x1001)
    f16.properties = ObjectProperties(
        name="F-16C", type="Air+FixedWing", pilot="Viper 1",
        country="us", coalition="Blue",
    )
    f16.timeline = [
        Frame(timestamp=0.0,
              transform=Transform(longitude=-118.5, latitude=34.0, altitude=3000.0,
                                  roll=0.0, pitch=5.0, yaw=270.0),
              properties={"Name": "F-16C", "Type": "Air+FixedWing",
                          "Pilot": "Viper 1", "Country": "us", "Coalition": "Blue"}),
        Frame(timestamp=5.0,
              transform=Transform(longitude=-118.501, altitude=3050.0),
              properties={"IAS": "155.0"}),
    ]
    acmi.objects[0x1001] = f16

    sam = AcmiObject(id=0x2001)
    sam.properties = ObjectProperties(name="SA-6", type="Ground+AntiAircraft")
    sam.timeline = [
        Frame(timestamp=0.0,
              transform=Transform(longitude=-118.4, latitude=33.9, altitude=100.0),
              properties={"Name": "SA-6", "Type": "Ground+AntiAircraft"}),
    ]
    acmi.objects[0x2001] = sam

    acmi.events = [
        Event(timestamp=5.0, type=EventType.TAKEN_OFF,
              object_ids=[0x1001], text="Viper 1 airborne"),
    ]

    # Write
    text = AcmiWriter.to_string(acmi)

    # Parse
    parsed = AcmiParser.parse(io.StringIO(text))
    assert parsed.globals.title == "Integration Test Mission"
    assert len(parsed.objects) == 2
    assert parsed.objects[0x1001].properties.pilot == "Viper 1"
    assert parsed.objects[0x2001].properties.name == "SA-6"
    assert len(parsed.events) == 1

    # Edit
    parsed.globals.title = "Modified Mission"
    parsed.objects[0x2001].removed = True
    parsed.objects[0x2001].removed_at = 25.0

    # Write again
    text2 = AcmiWriter.to_string(parsed)

    # Parse again
    final = AcmiParser.parse(io.StringIO(text2))
    assert final.globals.title == "Modified Mission"
    assert final.objects[0x2001].removed is True
    assert final.objects[0x2001].removed_at == 25.0


def test_streamer_to_parser():
    """Stream data, then parse the result."""
    buf = io.StringIO()
    gp = GlobalProperties(
        data_source="StreamTest",
        reference_time=datetime(2023, 1, 1, tzinfo=timezone.utc),
        title="Streamer Integration",
    )
    with AcmiStreamer(buf, globals=gp) as s:
        s.write_frame(0.0, 0x5001,
                      transform=Transform(longitude=10.0, latitude=20.0, altitude=500.0),
                      Name="C172", Type="Air+FixedWing")
        s.write_frame(5.0, 0x5001,
                      transform=Transform(longitude=10.001))
        s.write_event(Event(timestamp=10.0, type=EventType.LANDED,
                            object_ids=[0x5001], text="C172 landed"))
        s.remove_object(15.0, 0x5001)

    acmi = AcmiParser.parse(io.StringIO(buf.getvalue()))
    assert acmi.globals.title == "Streamer Integration"
    assert acmi.objects[0x5001].properties.name == "C172"
    assert acmi.objects[0x5001].removed is True
    assert len(acmi.events) == 1
    assert acmi.events[0].type == EventType.LANDED
```

- [ ] **Step 2: Run full test suite**

```bash
uv run pytest -v
```

Expected: ALL tests pass.

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "feat: add end-to-end integration tests for full acmi-maid workflow"
```

---

### Task 10: Final Cleanup

- [ ] **Step 1: Run full test suite one final time**

```bash
uv run pytest -v --tb=short
```

Expected: all tests pass, no warnings.

- [ ] **Step 2: Verify imports work from top-level**

```bash
uv run python -c "from acmi_maid import AcmiParser, AcmiWriter, AcmiStreamer, AcmiFile, Transform; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit all remaining changes and tag**

```bash
git add -A
git status
git commit -m "chore: final cleanup for acmi-maid v0.1.0"
```
