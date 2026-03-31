"""Utility functions for working with ACMI recordings."""

from __future__ import annotations

import math
from typing import List, Optional

from .models import AcmiFile, AcmiObject, Transform

_EARTH_RADIUS_M = 6_371_000.0  # mean Earth radius in metres


def haversine_distance(
    lon1: float,
    lat1: float,
    lon2: float,
    lat2: float,
) -> float:
    """Return the great-circle distance in metres between two WGS-84 points.

    Parameters
    ----------
    lon1, lat1:
        Longitude and latitude of the first point in decimal degrees.
    lon2, lat2:
        Longitude and latitude of the second point in decimal degrees.

    Returns
    -------
    float
        Distance in metres.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * _EARTH_RADIUS_M * math.asin(math.sqrt(a))


def filter_objects_by_type(acmi: AcmiFile, type_pattern: str) -> List[AcmiObject]:
    """Return all objects whose ``Type`` property contains *type_pattern*.

    The comparison is **case-insensitive**.

    Parameters
    ----------
    acmi:
        The recording to search.
    type_pattern:
        Substring to look for in the ``Type`` property, e.g.
        ``"Air+FixedWing"`` for fixed-wing aircraft.

    Returns
    -------
    list[AcmiObject]
        Objects matching the pattern.
    """
    pattern = type_pattern.lower()
    return [
        obj
        for obj in acmi.iter_objects()
        if obj.type is not None and pattern in obj.type.lower()
    ]


def get_active_objects_at(acmi: AcmiFile, time: float) -> List[AcmiObject]:
    """Return objects that were alive at the given *time*.

    An object is considered *active* when:

    * it has at least one record with ``timestamp <= time``, **and**
    * it either has no ``removed_at`` time, or its ``removed_at > time``.

    Parameters
    ----------
    acmi:
        The recording to query.
    time:
        The query timestamp in seconds (relative to the recording start).

    Returns
    -------
    list[AcmiObject]
        Objects active at *time*.
    """
    result: List[AcmiObject] = []
    for obj in acmi.iter_objects():
        if not obj.records:
            continue
        if obj.records[0].timestamp > time:
            continue
        if obj.removed_at is not None and obj.removed_at <= time:
            continue
        result.append(obj)
    return result


def interpolate_transform(obj: AcmiObject, time: float) -> Optional[Transform]:
    """Return a linearly interpolated :class:`~acmi_maid.models.Transform` for
    *obj* at *time*.

    The function merges all transform frames up to each record timestamp to
    produce fully-resolved transforms, then linearly interpolates between the
    two surrounding frames.

    * If *time* is before the first transform frame the first frame's transform
      is returned unchanged.
    * If *time* is after the last frame the last frame's transform is returned
      unchanged.
    * Returns ``None`` when the object has no records with transform data.

    Parameters
    ----------
    obj:
        The object whose position should be estimated.
    time:
        The query timestamp in seconds.

    Returns
    -------
    Transform or None
        The interpolated (or boundary) transform, or ``None`` if no transform
        data is available.
    """
    # Build a list of (timestamp, fully-resolved Transform) pairs
    resolved: list[tuple[float, Transform]] = []
    running: Optional[Transform] = None

    for record in obj.records:
        if record.transform is not None:
            running = (
                record.transform
                if running is None
                else running.merge(record.transform)
            )
        if running is not None:
            resolved.append((record.timestamp, running))

    if not resolved:
        return None

    if time <= resolved[0][0]:
        return resolved[0][1]

    if time >= resolved[-1][0]:
        return resolved[-1][1]

    # Find the two surrounding resolved frames and interpolate
    for i in range(len(resolved) - 1):
        t0, xfm0 = resolved[i]
        t1, xfm1 = resolved[i + 1]
        if t0 <= time <= t1:
            alpha = (time - t0) / (t1 - t0)
            return _lerp_transform(xfm0, xfm1, alpha)

    return resolved[-1][1]  # unreachable, but safe


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _lerp(a: Optional[float], b: Optional[float], alpha: float) -> Optional[float]:
    """Linearly interpolate between two optional floats."""
    if a is None or b is None:
        return b if a is None else a
    return a + (b - a) * alpha


def _lerp_transform(a: Transform, b: Transform, alpha: float) -> Transform:
    """Return a Transform linearly interpolated between *a* and *b*."""
    return Transform(
        longitude=_lerp(a.longitude, b.longitude, alpha),
        latitude=_lerp(a.latitude, b.latitude, alpha),
        altitude=_lerp(a.altitude, b.altitude, alpha),
        roll=_lerp(a.roll, b.roll, alpha),
        pitch=_lerp(a.pitch, b.pitch, alpha),
        yaw=_lerp(a.yaw, b.yaw, alpha),
        u=_lerp(a.u, b.u, alpha),
        v=_lerp(a.v, b.v, alpha),
    )
