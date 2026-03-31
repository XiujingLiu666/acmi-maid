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
