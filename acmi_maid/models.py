"""Data models for ACMI flight-recording files."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Transform:
    """Position and orientation of an object at a point in time.

    All fields are optional; ``None`` means the value was not present in
    the corresponding ACMI frame and should be inherited from a previous
    frame.

    Coordinates follow the ACMI / Tacview convention:
    - *longitude* / *latitude* in decimal degrees (WGS-84)
    - *altitude* in metres above mean sea level
    - *roll* / *pitch* / *yaw* in degrees
    - *u* / *v* are optional native coordinates used by some data sources
    """

    longitude: Optional[float] = None
    latitude: Optional[float] = None
    altitude: Optional[float] = None
    roll: Optional[float] = None
    pitch: Optional[float] = None
    yaw: Optional[float] = None
    u: Optional[float] = None
    v: Optional[float] = None

    def merge(self, other: "Transform") -> "Transform":
        """Return a new :class:`Transform` with non-``None`` fields from *other*
        overwriting the corresponding fields from *self*.

        This mirrors the ACMI rule that properties are *persistent* – an empty
        field in a later frame keeps the value from the previous frame.
        """
        return Transform(
            longitude=other.longitude if other.longitude is not None else self.longitude,
            latitude=other.latitude if other.latitude is not None else self.latitude,
            altitude=other.altitude if other.altitude is not None else self.altitude,
            roll=other.roll if other.roll is not None else self.roll,
            pitch=other.pitch if other.pitch is not None else self.pitch,
            yaw=other.yaw if other.yaw is not None else self.yaw,
            u=other.u if other.u is not None else self.u,
            v=other.v if other.v is not None else self.v,
        )


@dataclass
class ObjectRecord:
    """A single timestamped update for a tracked object.

    Each record corresponds to one line of ACMI data within a ``#<time>``
    frame.  Properties in a record override any previously set values for
    the same key on the parent :class:`AcmiObject`.
    """

    timestamp: float
    transform: Optional[Transform] = None
    properties: Dict[str, str] = field(default_factory=dict)


@dataclass
class AcmiObject:
    """A tracked entity (aircraft, missile, ground unit, …) in the recording.

    Attributes
    ----------
    id:
        The object's numeric identifier (decoded from the hexadecimal ID in
        the ACMI file).
    records:
        All timestamped update records for this object, in chronological order.
    removed_at:
        The timestamp at which the object was removed (``-<id>`` line), or
        ``None`` if the object was never explicitly removed.
    """

    id: int
    records: List[ObjectRecord] = field(default_factory=list)
    removed_at: Optional[float] = None

    # ------------------------------------------------------------------
    # Property helpers
    # ------------------------------------------------------------------

    def get_property(self, name: str, at_time: Optional[float] = None) -> Optional[str]:
        """Return the most recent value of property *name*.

        If *at_time* is given only records with ``timestamp <= at_time`` are
        considered.  If *at_time* is ``None`` the last known value is returned.
        """
        result: Optional[str] = None
        for record in self.records:
            if at_time is not None and record.timestamp > at_time:
                break
            if name in record.properties:
                result = record.properties[name]
        return result

    def get_transform(self, at_time: Optional[float] = None) -> Optional[Transform]:
        """Return the accumulated :class:`Transform` up to and including *at_time*.

        ACMI transforms are persistent – a ``None`` field in a later frame
        means the value from the previous frame is kept.  This method merges
        all frames up to *at_time* to produce the effective transform.
        """
        result: Optional[Transform] = None
        for record in self.records:
            if at_time is not None and record.timestamp > at_time:
                break
            if record.transform is not None:
                result = (
                    record.transform
                    if result is None
                    else result.merge(record.transform)
                )
        return result

    # ------------------------------------------------------------------
    # Convenience properties for frequently used ACMI attributes
    # ------------------------------------------------------------------

    @property
    def name(self) -> Optional[str]:
        """Object display name (``Name`` property)."""
        return self.get_property("Name")

    @property
    def pilot(self) -> Optional[str]:
        """Pilot name (``Pilot`` property)."""
        return self.get_property("Pilot")

    @property
    def type(self) -> Optional[str]:
        """Object type string, e.g. ``"Air+FixedWing"`` (``Type`` property)."""
        return self.get_property("Type")

    @property
    def color(self) -> Optional[str]:
        """Display colour (``Color`` property)."""
        return self.get_property("Color")

    @property
    def coalition(self) -> Optional[str]:
        """Coalition name (``Coalition`` property)."""
        return self.get_property("Coalition")

    @property
    def country(self) -> Optional[str]:
        """Country code (``Country`` property)."""
        return self.get_property("Country")

    @property
    def callsign(self) -> Optional[str]:
        """Callsign (``CallSign`` property)."""
        return self.get_property("CallSign")

    @property
    def first_seen(self) -> Optional[float]:
        """Timestamp of the first record for this object."""
        return self.records[0].timestamp if self.records else None

    @property
    def last_seen(self) -> Optional[float]:
        """Timestamp of the last record for this object."""
        return self.records[-1].timestamp if self.records else None


@dataclass
class AcmiFile:
    """In-memory representation of a parsed ACMI recording.

    Attributes
    ----------
    file_type:
        The ``FileType`` header value (typically ``"text/acmi/tacview"``).
    file_version:
        The ``FileVersion`` header value (e.g. ``"2.2"``).
    global_properties:
        Key/value properties associated with global object ``0``, such as
        ``ReferenceTime``, ``DataSource``, ``Title``, etc.
    objects:
        All tracked objects keyed by their numeric ID.  Object ``0`` is never
        present here; its properties are stored in *global_properties*.
    """

    file_type: str = ""
    file_version: str = ""
    global_properties: Dict[str, str] = field(default_factory=dict)
    objects: Dict[int, AcmiObject] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Global property helpers
    # ------------------------------------------------------------------

    @property
    def reference_time(self) -> Optional[str]:
        """ISO 8601 reference time string, or ``None``."""
        return self.global_properties.get("ReferenceTime")

    @property
    def reference_longitude(self) -> Optional[float]:
        """Reference longitude in decimal degrees, or ``None``."""
        val = self.global_properties.get("ReferenceLongitude")
        return float(val) if val is not None else None

    @property
    def reference_latitude(self) -> Optional[float]:
        """Reference latitude in decimal degrees, or ``None``."""
        val = self.global_properties.get("ReferenceLatitude")
        return float(val) if val is not None else None

    @property
    def reference_altitude(self) -> Optional[float]:
        """Reference altitude in metres, or ``None``."""
        val = self.global_properties.get("ReferenceAltitude")
        return float(val) if val is not None else None

    @property
    def data_source(self) -> Optional[str]:
        """Data source identifier, or ``None``."""
        return self.global_properties.get("DataSource")

    @property
    def data_recorder(self) -> Optional[str]:
        """Data recorder identifier, or ``None``."""
        return self.global_properties.get("DataRecorder")

    @property
    def title(self) -> Optional[str]:
        """Mission title, or ``None``."""
        return self.global_properties.get("Title")

    @property
    def author(self) -> Optional[str]:
        """Author name, or ``None``."""
        return self.global_properties.get("Author")

    # ------------------------------------------------------------------
    # Object helpers
    # ------------------------------------------------------------------

    def get_object(self, obj_id: int) -> Optional[AcmiObject]:
        """Return the :class:`AcmiObject` with the given *obj_id*, or ``None``."""
        return self.objects.get(obj_id)

    def iter_objects(self):
        """Iterate over all tracked objects (global object 0 is excluded)."""
        yield from self.objects.values()

    @property
    def duration(self) -> Optional[float]:
        """Total recording length in seconds, or ``None`` if the file is empty."""
        times = [
            record.timestamp
            for obj in self.objects.values()
            for record in obj.records
        ]
        if not times:
            return None
        return max(times) - min(times)
