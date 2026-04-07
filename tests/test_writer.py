import io
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from acmi_maid.enums import EventType
from acmi_maid.models import (
    AcmiFile,
    AcmiObject,
    Event,
    Frame,
    GlobalProperties,
    Transform,
)
from acmi_maid.parser import AcmiParser
from acmi_maid.writer import AcmiWriter

FIXTURES = Path(__file__).parent / "fixtures"


def _make_simple_acmi() -> AcmiFile:
    acmi = AcmiFile()
    acmi.globals.reference_time = datetime(2025, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
    acmi.globals.data_source = "TestSim"
    obj = AcmiObject(id=0x3001)
    obj.properties.name = "F-16C"
    obj.properties.type = "Air+FixedWing"
    obj.timeline.append(
        Frame(
            timestamp=0.0,
            transform=Transform(
                longitude=-118.5, latitude=34.0, altitude=3000.0,
                roll=0.0, pitch=5.0, yaw=270.0,
            ),
            properties={"Name": "F-16C", "Type": "Air+FixedWing"},
        )
    )
    obj.timeline.append(
        Frame(
            timestamp=1.0,
            transform=Transform(longitude=-118.501, latitude=34.001, altitude=3050.0),
        )
    )
    acmi.objects[0x3001] = obj
    return acmi


def test_to_string_header():
    acmi = _make_simple_acmi()
    text = AcmiWriter.to_string(acmi)
    lines = text.split("\n")
    assert lines[0] == "FileType=text/acmi/tacview"
    assert lines[1] == "FileVersion=2.2"


def test_to_string_globals():
    acmi = _make_simple_acmi()
    text = AcmiWriter.to_string(acmi)
    assert "ReferenceTime=2025-01-15T08:00:00Z" in text
    assert "DataSource=TestSim" in text


def test_to_string_object_frames():
    acmi = _make_simple_acmi()
    text = AcmiWriter.to_string(acmi)
    assert "#0" in text
    assert "3001,T=" in text
    assert "#1" in text


def test_to_string_removal():
    acmi = _make_simple_acmi()
    acmi.objects[0x3001].removed = True
    acmi.objects[0x3001].removed_at = 5.0
    text = AcmiWriter.to_string(acmi)
    assert "-3001" in text


def test_to_string_events():
    acmi = _make_simple_acmi()
    acmi.events.append(
        Event(timestamp=2.0, type=EventType.DESTROYED, object_ids=[0x3001], text="boom")
    )
    text = AcmiWriter.to_string(acmi)
    assert "Event=Destroyed|3001|boom" in text


def test_to_string_escaped_commas():
    acmi = _make_simple_acmi()
    acmi.objects[0x3001].timeline[0].properties["Label"] = "Hello, World"
    text = AcmiWriter.to_string(acmi)
    assert r"Hello\, World" in text


def test_write_to_stream():
    acmi = _make_simple_acmi()
    buf = io.StringIO()
    AcmiWriter.write(acmi, buf)
    text = buf.getvalue()
    assert text.startswith("FileType=")


def test_write_to_file(tmp_path):
    acmi = _make_simple_acmi()
    path = tmp_path / "test.acmi"
    AcmiWriter.write(acmi, path)
    content = path.read_bytes()
    assert content[:3] == b"\xef\xbb\xbf"
    text = content.decode("utf-8-sig")
    assert "FileType=" in text


def test_write_compressed(tmp_path):
    acmi = _make_simple_acmi()
    path = tmp_path / "test.zip.acmi"
    AcmiWriter.write(acmi, path, compress=True)
    assert zipfile.is_zipfile(path)
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        assert len(names) == 1


def test_round_trip_basic_mission():
    original = AcmiParser.parse(FIXTURES / "basic_mission.acmi")
    text = AcmiWriter.to_string(original)
    reparsed = AcmiParser.parse(io.StringIO(text))
    assert reparsed.globals.title == original.globals.title
    assert reparsed.globals.data_source == original.globals.data_source
    assert set(reparsed.objects.keys()) == set(original.objects.keys())
    for oid in original.objects:
        assert reparsed.objects[oid].properties.name == original.objects[oid].properties.name
        assert len(reparsed.objects[oid].timeline) == len(original.objects[oid].timeline)
    assert len(reparsed.events) == len(original.events)


def test_round_trip_escaped_commas():
    original = AcmiParser.parse(FIXTURES / "escaped_commas.acmi")
    text = AcmiWriter.to_string(original)
    reparsed = AcmiParser.parse(io.StringIO(text))
    assert reparsed.globals.title == "Test, with comma"
    obj = reparsed.objects[0xB001]
    assert obj.properties.name == "Test, Aircraft"


def test_round_trip_compressed(tmp_path):
    original = AcmiParser.parse(FIXTURES / "basic_mission.acmi")
    path = tmp_path / "roundtrip.zip.acmi"
    AcmiWriter.write(original, path, compress=True)
    reparsed = AcmiParser.parse(path)
    assert reparsed.globals.title == original.globals.title
    assert set(reparsed.objects.keys()) == set(original.objects.keys())
