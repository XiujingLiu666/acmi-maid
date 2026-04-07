import io
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from acmi_maid.enums import EventType
from acmi_maid.models import Event, GlobalProperties, Transform
from acmi_maid.parser import AcmiParser
from acmi_maid.streamer import AcmiStreamer


def _make_globals() -> GlobalProperties:
    return GlobalProperties(
        data_source="TestSim",
        reference_time=datetime(2025, 1, 15, 8, 0, 0, tzinfo=timezone.utc),
    )


def test_streamer_basic():
    buf = io.StringIO()
    with AcmiStreamer(buf, globals=_make_globals()) as s:
        s.write_frame(
            0.0, 0x3001,
            transform=Transform(longitude=-118.5, latitude=34.0, altitude=3000.0),
            Name="F-16C", Type="Air+FixedWing",
        )
        s.write_frame(
            1.0, 0x3001,
            transform=Transform(longitude=-118.501, latitude=34.001, altitude=3050.0),
        )
    text = buf.getvalue()
    assert "FileType=text/acmi/tacview" in text
    assert "ReferenceTime=" in text
    assert "#0" in text
    assert "3001,T=" in text
    assert "Name=F-16C" in text
    assert "#1" in text


def test_streamer_no_duplicate_timestamps():
    buf = io.StringIO()
    with AcmiStreamer(buf, globals=_make_globals()) as s:
        s.write_frame(
            0.0, 0x3001,
            transform=Transform(longitude=-118.5, latitude=34.0, altitude=3000.0),
            Name="F-16C",
        )
        s.write_frame(
            0.0, 0x3002,
            transform=Transform(longitude=-118.6, latitude=34.1, altitude=2500.0),
            Name="MiG-29",
        )
    text = buf.getvalue()
    assert text.count("#0") == 1


def test_streamer_events():
    buf = io.StringIO()
    with AcmiStreamer(buf, globals=_make_globals()) as s:
        s.write_frame(
            0.0, 0x3001,
            transform=Transform(longitude=-118.5, latitude=34.0, altitude=3000.0),
            Name="F-16C",
        )
        s.write_event(
            Event(timestamp=5.0, type=EventType.TAKEN_OFF, object_ids=[0x3001], text="Airborne")
        )
    text = buf.getvalue()
    assert "Event=TakenOff|3001|Airborne" in text


def test_streamer_remove_object():
    buf = io.StringIO()
    with AcmiStreamer(buf, globals=_make_globals()) as s:
        s.write_frame(
            0.0, 0x3001,
            transform=Transform(longitude=-118.5, latitude=34.0, altitude=3000.0),
            Name="F-16C",
        )
        s.remove_object(5.0, 0x3001)
    text = buf.getvalue()
    assert "-3001" in text


def test_streamer_write_to_file(tmp_path):
    path = tmp_path / "stream.acmi"
    with AcmiStreamer(path, globals=_make_globals()) as s:
        s.write_frame(
            0.0, 0x3001,
            transform=Transform(longitude=-118.5, latitude=34.0, altitude=3000.0),
            Name="F-16C",
        )
    content = path.read_bytes()
    assert content[:3] == b"\xef\xbb\xbf"


def test_streamer_compressed(tmp_path):
    path = tmp_path / "stream.zip.acmi"
    with AcmiStreamer(path, globals=_make_globals(), compress=True) as s:
        s.write_frame(
            0.0, 0x3001,
            transform=Transform(longitude=-118.5, latitude=34.0, altitude=3000.0),
            Name="F-16C",
        )
    assert zipfile.is_zipfile(path)


def test_streamer_output_parseable():
    buf = io.StringIO()
    with AcmiStreamer(buf, globals=_make_globals()) as s:
        s.write_frame(
            0.0, 0x3001,
            transform=Transform(longitude=-118.5, latitude=34.0, altitude=3000.0),
            Name="F-16C", Type="Air+FixedWing",
        )
    buf.seek(0)
    acmi = AcmiParser.parse(buf)
    assert 0x3001 in acmi.objects
    assert acmi.objects[0x3001].properties.name == "F-16C"
