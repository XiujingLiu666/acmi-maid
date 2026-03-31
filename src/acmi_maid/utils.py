from __future__ import annotations

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

    # Strip trailing Nones, but always keep at least 3 components
    while len(vals) > 3 and vals[-1] is None:
        vals.pop()

    def _fmt(v: float | None) -> str:
        if v is None:
            return ""
        if v == int(v):
            return str(float(v))
        return str(v)

    return "|".join(_fmt(v) for v in vals)


def parse_acmi_datetime(value: str) -> datetime:
    """Parse an ACMI datetime string (ISO 8601) into a Python datetime."""
    value = value.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def format_acmi_datetime(dt: datetime) -> str:
    """Format a Python datetime into ACMI ISO 8601 string."""
    s = dt.isoformat()
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
