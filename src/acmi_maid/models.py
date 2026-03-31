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
