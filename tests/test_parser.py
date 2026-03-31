"""Tests for acmi_maid.parser."""

import io
import zipfile

import pytest

from acmi_maid.parser import parse_file, parse_stream, parse_string


# ---------------------------------------------------------------------------
# Shared sample ACMI text used across multiple tests
# ---------------------------------------------------------------------------

SAMPLE = """\
FileType=text/acmi/tacview
FileVersion=2.2
0,ReferenceTime=2011-06-01T00:00:00Z,ReferenceLongitude=0,ReferenceLatitude=0
// A comment line – should be ignored
#0
3000102,T=41.6251|41.5915|2000,Name=F-16C,Color=Red,Type=Air+FixedWing
3000201,T=41.8|41.7|5000,Name=F-15C,Color=Blue,Type=Air+FixedWing
#1.0
3000102,T=41.628|41.593|2050
#2.0
-3000102
"""


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------


def test_parse_file_type():
    acmi = parse_string(SAMPLE)
    assert acmi.file_type == "text/acmi/tacview"


def test_parse_file_version():
    acmi = parse_string(SAMPLE)
    assert acmi.file_version == "2.2"


# ---------------------------------------------------------------------------
# Global properties
# ---------------------------------------------------------------------------


def test_parse_reference_time():
    acmi = parse_string(SAMPLE)
    assert acmi.reference_time == "2011-06-01T00:00:00Z"


def test_parse_reference_longitude():
    acmi = parse_string(SAMPLE)
    assert acmi.reference_longitude == 0.0


def test_parse_reference_latitude():
    acmi = parse_string(SAMPLE)
    assert acmi.reference_latitude == 0.0


def test_global_object_not_in_objects_dict():
    acmi = parse_string(SAMPLE)
    # Object 0 (global) must never appear in the objects dict
    assert 0 not in acmi.objects


# ---------------------------------------------------------------------------
# Object count and identity
# ---------------------------------------------------------------------------


def test_parse_object_count():
    acmi = parse_string(SAMPLE)
    assert len(acmi.objects) == 2


def test_parse_object_ids():
    acmi = parse_string(SAMPLE)
    assert 0x3000102 in acmi.objects
    assert 0x3000201 in acmi.objects


# ---------------------------------------------------------------------------
# Object properties
# ---------------------------------------------------------------------------


def test_parse_object_name():
    acmi = parse_string(SAMPLE)
    assert acmi.objects[0x3000102].name == "F-16C"
    assert acmi.objects[0x3000201].name == "F-15C"


def test_parse_object_type():
    acmi = parse_string(SAMPLE)
    assert acmi.objects[0x3000102].type == "Air+FixedWing"


def test_parse_object_color():
    acmi = parse_string(SAMPLE)
    assert acmi.objects[0x3000102].color == "Red"
    assert acmi.objects[0x3000201].color == "Blue"


# ---------------------------------------------------------------------------
# Transform parsing
# ---------------------------------------------------------------------------


def test_parse_transform_values():
    acmi = parse_string(SAMPLE)
    t = acmi.objects[0x3000102].records[0].transform
    assert t is not None
    assert abs(t.longitude - 41.6251) < 1e-6
    assert abs(t.latitude - 41.5915) < 1e-6
    assert t.altitude == 2000.0


def test_parse_transform_partial_fields_are_none():
    text = """\
FileType=text/acmi/tacview
FileVersion=2.2
#0
1,T=10.0|20.0|1000.0|5.0
"""
    acmi = parse_string(text)
    t = acmi.objects[1].records[0].transform
    assert t is not None
    assert t.longitude == 10.0
    assert t.latitude == 20.0
    assert t.altitude == 1000.0
    assert t.roll == 5.0
    assert t.pitch is None
    assert t.yaw is None


def test_parse_transform_empty_field_is_none():
    text = """\
FileType=text/acmi/tacview
FileVersion=2.2
#0
1,T=10.0||1000.0
"""
    acmi = parse_string(text)
    t = acmi.objects[1].records[0].transform
    assert t is not None
    assert t.longitude == 10.0
    assert t.latitude is None
    assert t.altitude == 1000.0


# ---------------------------------------------------------------------------
# Timestamps and record ordering
# ---------------------------------------------------------------------------


def test_parse_timestamps():
    acmi = parse_string(SAMPLE)
    obj = acmi.objects[0x3000102]
    assert obj.records[0].timestamp == 0.0
    assert obj.records[1].timestamp == 1.0


def test_parse_multiple_records():
    acmi = parse_string(SAMPLE)
    obj = acmi.objects[0x3000102]
    assert len(obj.records) == 2


# ---------------------------------------------------------------------------
# Object removal
# ---------------------------------------------------------------------------


def test_parse_object_removal():
    acmi = parse_string(SAMPLE)
    obj = acmi.objects[0x3000102]
    assert obj.removed_at == 2.0


def test_parse_object_not_removed():
    acmi = parse_string(SAMPLE)
    obj = acmi.objects[0x3000201]
    assert obj.removed_at is None


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------


def test_parse_comment_lines_ignored():
    text = """\
FileType=text/acmi/tacview
FileVersion=2.2
// This is a comment
#0
1,T=0.0|0.0|0.0
// Another comment
"""
    acmi = parse_string(text)
    assert len(acmi.objects) == 1


# ---------------------------------------------------------------------------
# Stream / file I/O
# ---------------------------------------------------------------------------


def test_parse_stream_plain_text():
    data = SAMPLE.encode("utf-8")
    acmi = parse_stream(io.BytesIO(data))
    assert acmi.file_version == "2.2"
    assert len(acmi.objects) == 2


def test_parse_stream_with_bom():
    data = b"\xef\xbb\xbf" + SAMPLE.encode("utf-8")  # UTF-8 BOM
    acmi = parse_stream(io.BytesIO(data))
    assert acmi.file_type == "text/acmi/tacview"


def test_parse_stream_zip_compressed():
    data = SAMPLE.encode("utf-8")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("tacview.acmi.txt", data)
    buf.seek(0)
    acmi = parse_stream(buf)
    assert acmi.file_version == "2.2"
    assert len(acmi.objects) == 2


def test_parse_file_plain(tmp_path):
    path = tmp_path / "test.acmi"
    path.write_text(SAMPLE, encoding="utf-8")
    acmi = parse_file(path)
    assert acmi.file_type == "text/acmi/tacview"
    assert len(acmi.objects) == 2


def test_parse_file_zip(tmp_path):
    data = SAMPLE.encode("utf-8")
    path = tmp_path / "test.zip.acmi"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("tacview.acmi.txt", data)
    acmi = parse_file(path)
    assert acmi.file_version == "2.2"
    assert acmi.objects[0x3000102].name == "F-16C"


def test_parse_file_accepts_string_path(tmp_path):
    path = tmp_path / "test.acmi"
    path.write_text(SAMPLE, encoding="utf-8")
    acmi = parse_file(str(path))
    assert acmi.file_type == "text/acmi/tacview"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_parse_empty_string():
    acmi = parse_string("")
    assert acmi.file_type == ""
    assert acmi.file_version == ""
    assert len(acmi.objects) == 0


def test_parse_global_properties_update_multiple_times():
    text = """\
FileType=text/acmi/tacview
FileVersion=2.2
0,Title=First
0,Title=Second
"""
    acmi = parse_string(text)
    assert acmi.title == "Second"


def test_parse_value_with_equals_sign():
    """A property value that itself contains '=' must not be truncated."""
    text = """\
FileType=text/acmi/tacview
FileVersion=2.2
#0
1,Name=A=B
"""
    acmi = parse_string(text)
    assert acmi.objects[1].name == "A=B"
