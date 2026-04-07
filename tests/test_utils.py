from datetime import datetime, timezone

from acmi_maid.models import Transform
from acmi_maid.utils import (
    escape_value,
    format_acmi_datetime,
    format_transform,
    parse_acmi_datetime,
    parse_transform,
    split_escaped,
    to_pascal_case,
    to_snake_case,
)


# --- Transform parsing ---


def test_parse_transform_3_components():
    t = parse_transform("-118.5|34.0|3000")
    assert t.longitude == -118.5
    assert t.latitude == 34.0
    assert t.altitude == 3000.0


def test_parse_transform_5_components():
    t = parse_transform("-118.5|34.0|3000|100|200")
    assert t.longitude == -118.5
    assert t.u == 100.0
    assert t.v == 200.0


def test_parse_transform_6_components():
    t = parse_transform("-118.5|34.0|3000|10|5|270")
    assert t.roll == 10.0
    assert t.pitch == 5.0
    assert t.yaw == 270.0


def test_parse_transform_9_components():
    t = parse_transform("-118.5|34.0|3000|10|5|270|100|200|90")
    assert t.longitude == -118.5
    assert t.u == 100.0
    assert t.heading == 90.0


def test_parse_transform_empty_components():
    t = parse_transform("||3000")
    assert t.longitude is None
    assert t.latitude is None
    assert t.altitude == 3000.0


def test_parse_transform_all_empty_3():
    t = parse_transform("||")
    assert t.longitude is None
    assert t.latitude is None
    assert t.altitude is None


def test_format_transform_basic():
    t = Transform(longitude=-118.5, latitude=34.0, altitude=3000.0)
    assert format_transform(t) == "-118.5|34.0|3000.0"


def test_format_transform_5_components():
    t = Transform(longitude=-118.5, latitude=34.0, altitude=3000.0,
                  u=100.0, v=200.0)
    assert format_transform(t) == "-118.5|34.0|3000.0|100.0|200.0"


def test_format_transform_6_components():
    t = Transform(longitude=-118.5, latitude=34.0, altitude=3000.0,
                  roll=10.0, pitch=5.0, yaw=270.0)
    assert format_transform(t) == "-118.5|34.0|3000.0|10.0|5.0|270.0"


def test_format_transform_9_components():
    t = Transform(longitude=-118.5, latitude=34.0, altitude=3000.0,
                  roll=10.0, pitch=5.0, yaw=270.0,
                  u=100.0, v=200.0, heading=90.0)
    assert format_transform(t) == "-118.5|34.0|3000.0|10.0|5.0|270.0|100.0|200.0|90.0"


def test_format_transform_with_nones():
    t = Transform(altitude=3000.0)
    assert format_transform(t) == "||3000.0"


def test_format_transform_all_none():
    t = Transform()
    assert format_transform(t) == "||"


# --- Datetime ---


def test_parse_acmi_datetime():
    dt = parse_acmi_datetime("2025-01-15T08:30:00Z")
    assert dt.year == 2025
    assert dt.month == 1
    assert dt.hour == 8
    assert dt.tzinfo == timezone.utc


def test_parse_acmi_datetime_with_fractional():
    dt = parse_acmi_datetime("2025-01-15T08:30:00.500Z")
    assert dt.microsecond == 500000


def test_format_acmi_datetime():
    dt = datetime(2025, 1, 15, 8, 30, 0, tzinfo=timezone.utc)
    assert format_acmi_datetime(dt) == "2025-01-15T08:30:00Z"


def test_format_acmi_datetime_with_fractional():
    dt = datetime(2025, 1, 15, 8, 30, 0, 500000, tzinfo=timezone.utc)
    assert format_acmi_datetime(dt) == "2025-01-15T08:30:00.5Z"


# --- Escape handling ---


def test_split_escaped_no_escapes():
    assert split_escaped("a,b,c") == ["a", "b", "c"]


def test_split_escaped_with_escape():
    assert split_escaped(r"a\,b,c") == ["a,b", "c"]


def test_split_escaped_multiple():
    assert split_escaped(r"a\,b\,c,d") == ["a,b,c", "d"]


def test_escape_value():
    assert escape_value("hello, world") == r"hello\, world"


def test_escape_value_no_commas():
    assert escape_value("hello") == "hello"


# --- Case conversion ---


def test_to_snake_case():
    assert to_snake_case("CallSign") == "call_sign"
    assert to_snake_case("IAS") == "ias"
    assert to_snake_case("LandingGear") == "landing_gear"
    assert to_snake_case("Name") == "name"


def test_to_pascal_case():
    assert to_pascal_case("call_sign") == "CallSign"
    assert to_pascal_case("name") == "Name"
    assert to_pascal_case("landing_gear") == "LandingGear"
