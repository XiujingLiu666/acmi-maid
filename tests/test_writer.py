"""Tests for acmi_maid.writer."""

import io
import zipfile

import pytest

from acmi_maid.models import AcmiFile, AcmiObject, ObjectRecord, Transform
from acmi_maid.parser import parse_string
from acmi_maid.writer import write_file, write_stream, write_string


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_simple_acmi() -> AcmiFile:
    acmi = AcmiFile(file_type="text/acmi/tacview", file_version="2.2")
    acmi.global_properties["ReferenceTime"] = "2021-01-01T00:00:00Z"

    obj = AcmiObject(id=0x100)
    obj.records.append(
        ObjectRecord(
            timestamp=0.0,
            transform=Transform(longitude=10.0, latitude=20.0, altitude=1000.0),
            properties={"Name": "F-16C", "Color": "Red"},
        )
    )
    obj.records.append(
        ObjectRecord(
            timestamp=1.0,
            transform=Transform(longitude=10.1, latitude=20.1, altitude=1050.0),
        )
    )
    acmi.objects[0x100] = obj
    return acmi


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------


def test_write_file_type():
    text = write_string(_make_simple_acmi())
    assert "FileType=text/acmi/tacview" in text


def test_write_file_version():
    text = write_string(_make_simple_acmi())
    assert "FileVersion=2.2" in text


def test_write_default_file_type_when_empty():
    acmi = AcmiFile()
    text = write_string(acmi)
    assert "FileType=text/acmi/tacview" in text


def test_write_default_file_version_when_empty():
    acmi = AcmiFile()
    text = write_string(acmi)
    assert "FileVersion=2.2" in text


# ---------------------------------------------------------------------------
# Global properties
# ---------------------------------------------------------------------------


def test_write_global_properties():
    text = write_string(_make_simple_acmi())
    assert "ReferenceTime=2021-01-01T00:00:00Z" in text


def test_write_no_global_line_when_empty():
    acmi = AcmiFile(file_type="text/acmi/tacview", file_version="2.2")
    text = write_string(acmi)
    assert "0," not in text


# ---------------------------------------------------------------------------
# Object lines
# ---------------------------------------------------------------------------


def test_write_object_hex_id():
    text = write_string(_make_simple_acmi())
    # 0x100 = 256, displayed as uppercase hex "100"
    assert "100," in text


def test_write_object_properties():
    text = write_string(_make_simple_acmi())
    assert "Name=F-16C" in text
    assert "Color=Red" in text


def test_write_transform():
    text = write_string(_make_simple_acmi())
    assert "T=10.0|20.0|1000.0" in text


def test_write_transform_partial_fields():
    """None fields at the end of a transform should be omitted."""
    acmi = AcmiFile(file_type="text/acmi/tacview", file_version="2.2")
    obj = AcmiObject(id=1)
    obj.records.append(
        ObjectRecord(
            timestamp=0.0,
            transform=Transform(longitude=1.0, latitude=2.0, altitude=100.0),
        )
    )
    acmi.objects[1] = obj
    text = write_string(acmi)
    assert "T=1.0|2.0|100.0" in text
    # No trailing pipes
    assert "T=1.0|2.0|100.0|" not in text


def test_write_transform_inner_none_preserved():
    """A None latitude between a longitude and altitude must emit empty field."""
    acmi = AcmiFile(file_type="text/acmi/tacview", file_version="2.2")
    obj = AcmiObject(id=1)
    obj.records.append(
        ObjectRecord(
            timestamp=0.0,
            transform=Transform(longitude=10.0, latitude=None, altitude=500.0),
        )
    )
    acmi.objects[1] = obj
    text = write_string(acmi)
    # latitude is None → empty field between lon and alt
    assert "T=10.0||500.0" in text


# ---------------------------------------------------------------------------
# Timestamps
# ---------------------------------------------------------------------------


def test_write_frame_markers():
    text = write_string(_make_simple_acmi())
    assert "#0" in text
    assert "#1" in text


def test_write_frame_order():
    """Earlier timestamps must appear before later ones."""
    text = write_string(_make_simple_acmi())
    idx0 = text.index("#0")
    idx1 = text.index("#1")
    assert idx0 < idx1


# ---------------------------------------------------------------------------
# Object removal
# ---------------------------------------------------------------------------


def test_write_object_removal():
    acmi = AcmiFile(file_type="text/acmi/tacview", file_version="2.2")
    obj = AcmiObject(id=0xAB, removed_at=3.0)
    obj.records.append(
        ObjectRecord(
            timestamp=0.0,
            transform=Transform(longitude=0.0, latitude=0.0, altitude=0.0),
        )
    )
    acmi.objects[0xAB] = obj
    text = write_string(acmi)
    assert "-AB" in text
    # The removal marker must appear after the #3 frame header
    assert text.index("#3") < text.index("-AB")


def test_write_removal_after_updates_at_same_timestamp():
    """Object updates at t=3 must come before the removal at t=3."""
    acmi = AcmiFile(file_type="text/acmi/tacview", file_version="2.2")
    obj1 = AcmiObject(id=1, removed_at=3.0)
    obj1.records.append(ObjectRecord(timestamp=0.0, transform=Transform(longitude=0.0, latitude=0.0, altitude=0.0)))
    obj2 = AcmiObject(id=2)
    obj2.records.append(ObjectRecord(timestamp=3.0, transform=Transform(longitude=1.0, latitude=1.0, altitude=0.0)))
    acmi.objects[1] = obj1
    acmi.objects[2] = obj2
    text = write_string(acmi)
    assert text.index("2,") < text.index("-1")


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------


def test_write_roundtrip_header():
    original = """\
FileType=text/acmi/tacview
FileVersion=2.2
0,ReferenceTime=2021-01-01T00:00:00Z
#0
A,T=10.0|20.0|1000.0,Name=TestAircraft,Color=Blue
#1.0
A,T=10.1|20.1|1050.0
"""
    acmi = parse_string(original)
    reparsed = parse_string(write_string(acmi))
    assert reparsed.file_type == acmi.file_type
    assert reparsed.file_version == acmi.file_version


def test_write_roundtrip_global_properties():
    original = """\
FileType=text/acmi/tacview
FileVersion=2.2
0,ReferenceTime=2021-01-01T00:00:00Z
#0
A,T=0.0|0.0|0.0
"""
    acmi = parse_string(original)
    reparsed = parse_string(write_string(acmi))
    assert reparsed.reference_time == acmi.reference_time


def test_write_roundtrip_object_properties():
    original = """\
FileType=text/acmi/tacview
FileVersion=2.2
#0
A,T=10.0|20.0|1000.0,Name=TestAircraft,Color=Blue
#1.0
A,T=10.1|20.1|1050.0
"""
    acmi = parse_string(original)
    reparsed = parse_string(write_string(acmi))
    assert reparsed.objects[0xA].name == acmi.objects[0xA].name
    assert len(reparsed.objects[0xA].records) == len(acmi.objects[0xA].records)


def test_write_roundtrip_removal():
    original = """\
FileType=text/acmi/tacview
FileVersion=2.2
#0
1,T=0.0|0.0|0.0
#5.0
-1
"""
    acmi = parse_string(original)
    reparsed = parse_string(write_string(acmi))
    assert reparsed.objects[1].removed_at == 5.0


# ---------------------------------------------------------------------------
# File and stream I/O
# ---------------------------------------------------------------------------


def test_write_file_creates_file(tmp_path):
    path = tmp_path / "output.acmi"
    write_file(_make_simple_acmi(), path)
    assert path.exists()


def test_write_file_content(tmp_path):
    path = tmp_path / "output.acmi"
    write_file(_make_simple_acmi(), path)
    content = path.read_text("utf-8")
    assert "FileType=text/acmi/tacview" in content


def test_write_file_accepts_string_path(tmp_path):
    path = tmp_path / "output.acmi"
    write_file(_make_simple_acmi(), str(path))
    assert path.exists()


def test_write_file_compressed(tmp_path):
    path = tmp_path / "output.zip.acmi"
    write_file(_make_simple_acmi(), path, compressed=True)
    assert zipfile.is_zipfile(path)


def test_write_stream_plain():
    buf = io.BytesIO()
    write_stream(_make_simple_acmi(), buf)
    buf.seek(0)
    content = buf.read().decode("utf-8")
    assert "FileType=text/acmi/tacview" in content


def test_write_stream_compressed():
    buf = io.BytesIO()
    write_stream(_make_simple_acmi(), buf, compressed=True)
    buf.seek(0)
    assert zipfile.is_zipfile(buf)
