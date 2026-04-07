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

    Omits trailing None components; uses empty fields for interior Nones.
    """

    def _fmt(val: float | None) -> str:
        if val is None:
            return ""
        # Drop trailing .0 for cleaner output
        return str(val) if val != int(val) else str(val)

    # Determine which form to use based on which fields are set
    has_uv_heading = t.u is not None or t.v is not None or t.heading is not None
    has_rpy = t.roll is not None or t.pitch is not None or t.yaw is not None
    has_uv = t.u is not None or t.v is not None

    if has_rpy and has_uv_heading:
        # 9-component form
        parts = [t.longitude, t.latitude, t.altitude,
                 t.roll, t.pitch, t.yaw,
                 t.u, t.v, t.heading]
    elif has_rpy:
        # 6-component form
        parts = [t.longitude, t.latitude, t.altitude,
                 t.roll, t.pitch, t.yaw]
    elif has_uv:
        # 5-component form
        parts = [t.longitude, t.latitude, t.altitude,
                 t.u, t.v]
    else:
        # 3-component form
        parts = [t.longitude, t.latitude, t.altitude]

    return "|".join(_fmt(p) for p in parts)


def parse_acmi_datetime(value: str) -> datetime:
    """Parse an ACMI datetime string (ISO 8601) into a Python datetime."""
    # Handle fractional seconds
    if "." in value:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
            tzinfo=timezone.utc
        )
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )


def format_acmi_datetime(dt: datetime) -> str:
    """Format a Python datetime into ACMI ISO 8601 string."""
    if dt.microsecond:
        # Include fractional seconds
        frac = f".{dt.microsecond:06d}".rstrip("0")
        return dt.strftime(f"%Y-%m-%dT%H:%M:%S{frac}Z")
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def split_escaped(line: str, delimiter: str = ",") -> list[str]:
    r"""Split a string on delimiter, respecting backslash escaping.

    Unescapes \, -> , in the resulting values.
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
    r"""Escape commas in a property value for ACMI output (\,)."""
    return value.replace(",", "\\,")


_SNAKE_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def to_snake_case(name: str) -> str:
    """Convert PascalCase ACMI property name to snake_case."""
    return _SNAKE_RE.sub("_", name).lower()


def to_pascal_case(name: str) -> str:
    """Convert snake_case Python field name to PascalCase ACMI property name."""
    return "".join(word.capitalize() for word in name.split("_"))
