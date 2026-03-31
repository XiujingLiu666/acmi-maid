import io
import zipfile
from datetime import datetime, timezone

from acmi_maid.models import GlobalProperties, Transform, Event
from acmi_maid.enums import EventType
from acmi_maid.parser import AcmiParser
from acmi_maid.streamer import AcmiStreamer


def test_basic_stream():
    buf = io.StringIO()
    gp = GlobalProperties(
        data_source="TestSim",
        reference_time=datetime(2023, 1, 1, tzinfo=timezone.utc),
    )
    with AcmiStreamer(buf, globals=gp) as s:
        s.write_frame(0.0, 0x3001,
                      transform=Transform(longitude=41.6, latitude=41.5, altitude=2000.0),
                      Name="F-16C", Type="Air+FixedWing")
        s.write_frame(10.0, 0x3001,
                      transform=Transform(longitude=41.7))

    text = buf.getvalue()
    assert "FileType=text/acmi/tacview" in text
    assert "FileVersion=2.2" in text
    assert "DataSource=TestSim" in text
    assert "Name=F-16C" in text
    assert "#0" in text or "#0.0" in text
    assert "#10" in text or "#10.0" in text


def test_no_duplicate_timestamps():
    buf = io.StringIO()
    with AcmiStreamer(buf) as s:
        s.write_frame(0.0, 0x3001,
                      transform=Transform(longitude=1.0, latitude=2.0, altitude=3.0))
        s.write_frame(0.0, 0x3002,
                      transform=Transform(longitude=4.0, latitude=5.0, altitude=6.0))

    text = buf.getvalue()
    # Should only have one #0 line
    lines = text.split("\n")
    time_lines = [l for l in lines if l.startswith("#0")]
    assert len(time_lines) == 1


def test_event_writing():
    buf = io.StringIO()
    with AcmiStreamer(buf) as s:
        s.write_event(Event(
            timestamp=5.0, type=EventType.TAKEN_OFF,
            object_ids=[0x3001], text="Airborne"))

    text = buf.getvalue()
    assert "Event=TakenOff|3001|Airborne" in text


def test_remove_object():
    buf = io.StringIO()
    with AcmiStreamer(buf) as s:
        s.write_frame(0.0, 0x3001,
                      transform=Transform(longitude=1.0, latitude=2.0, altitude=3.0))
        s.remove_object(10.0, 0x3001)

    text = buf.getvalue()
    assert "-3001" in text


def test_streamer_roundtrip():
    buf = io.StringIO()
    gp = GlobalProperties(
        data_source="TestSim",
        reference_time=datetime(2023, 1, 1, tzinfo=timezone.utc),
        title="Stream Test",
    )
    with AcmiStreamer(buf, globals=gp) as s:
        s.write_frame(0.0, 0x3001,
                      transform=Transform(longitude=41.6, latitude=41.5, altitude=2000.0,
                                          roll=10.0, pitch=5.0, yaw=270.0),
                      Name="F-16C", Type="Air+FixedWing")

    text = buf.getvalue()
    acmi = AcmiParser.parse(io.StringIO(text))
    assert acmi.globals.title == "Stream Test"
    assert 0x3001 in acmi.objects
    assert acmi.objects[0x3001].properties.name == "F-16C"


def test_streamer_to_file(tmp_path):
    out = tmp_path / "stream.acmi"
    with AcmiStreamer(out) as s:
        s.write_frame(0.0, 0x3001,
                      transform=Transform(longitude=1.0, latitude=2.0, altitude=3.0),
                      Name="Test")
    acmi = AcmiParser.parse(out)
    assert 0x3001 in acmi.objects


def test_streamer_compressed(tmp_path):
    out = tmp_path / "stream.zip.acmi"
    with AcmiStreamer(out, compress=True) as s:
        s.write_frame(0.0, 0x3001,
                      transform=Transform(longitude=1.0, latitude=2.0, altitude=3.0),
                      Name="Test")
    assert zipfile.is_zipfile(out)
    acmi = AcmiParser.parse(out)
    assert 0x3001 in acmi.objects
