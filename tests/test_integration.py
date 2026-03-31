"""End-to-end integration tests for acmi-maid."""
import io
from datetime import datetime, timezone

from acmi_maid import (
    AcmiFile, AcmiObject, AcmiParser, AcmiWriter, AcmiStreamer,
    GlobalProperties, ObjectProperties, Transform, Frame, Event,
    EventType,
)


def test_full_workflow():
    """Build -> write -> parse -> verify -> edit -> write -> parse again."""
    # Build
    acmi = AcmiFile()
    acmi.globals = GlobalProperties(
        data_source="IntegrationTest",
        data_recorder="acmi-maid",
        reference_time=datetime(2023, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        title="Integration Test Mission",
    )

    f16 = AcmiObject(id=0x1001)
    f16.properties = ObjectProperties(
        name="F-16C", type="Air+FixedWing", pilot="Viper 1",
        country="us", coalition="Blue",
    )
    f16.timeline = [
        Frame(timestamp=0.0,
              transform=Transform(longitude=-118.5, latitude=34.0, altitude=3000.0,
                                  roll=0.0, pitch=5.0, yaw=270.0),
              properties={"Name": "F-16C", "Type": "Air+FixedWing",
                          "Pilot": "Viper 1", "Country": "us", "Coalition": "Blue"}),
        Frame(timestamp=5.0,
              transform=Transform(longitude=-118.501, altitude=3050.0),
              properties={"IAS": "155.0"}),
    ]
    acmi.objects[0x1001] = f16

    sam = AcmiObject(id=0x2001)
    sam.properties = ObjectProperties(name="SA-6", type="Ground+AntiAircraft")
    sam.timeline = [
        Frame(timestamp=0.0,
              transform=Transform(longitude=-118.4, latitude=33.9, altitude=100.0),
              properties={"Name": "SA-6", "Type": "Ground+AntiAircraft"}),
    ]
    acmi.objects[0x2001] = sam

    acmi.events = [
        Event(timestamp=5.0, type=EventType.TAKEN_OFF,
              object_ids=[0x1001], text="Viper 1 airborne"),
    ]

    # Write
    text = AcmiWriter.to_string(acmi)

    # Parse
    parsed = AcmiParser.parse(io.StringIO(text))
    assert parsed.globals.title == "Integration Test Mission"
    assert len(parsed.objects) == 2
    assert parsed.objects[0x1001].properties.pilot == "Viper 1"
    assert parsed.objects[0x2001].properties.name == "SA-6"
    assert len(parsed.events) == 1

    # Edit
    parsed.globals.title = "Modified Mission"
    parsed.objects[0x2001].removed = True
    parsed.objects[0x2001].removed_at = 25.0

    # Write again
    text2 = AcmiWriter.to_string(parsed)

    # Parse again
    final = AcmiParser.parse(io.StringIO(text2))
    assert final.globals.title == "Modified Mission"
    assert final.objects[0x2001].removed is True
    assert final.objects[0x2001].removed_at == 25.0


def test_streamer_to_parser():
    """Stream data, then parse the result."""
    buf = io.StringIO()
    gp = GlobalProperties(
        data_source="StreamTest",
        reference_time=datetime(2023, 1, 1, tzinfo=timezone.utc),
        title="Streamer Integration",
    )
    with AcmiStreamer(buf, globals=gp) as s:
        s.write_frame(0.0, 0x5001,
                      transform=Transform(longitude=10.0, latitude=20.0, altitude=500.0),
                      Name="C172", Type="Air+FixedWing")
        s.write_frame(5.0, 0x5001,
                      transform=Transform(longitude=10.001))
        s.write_event(Event(timestamp=10.0, type=EventType.LANDED,
                            object_ids=[0x5001], text="C172 landed"))
        s.remove_object(15.0, 0x5001)

    acmi = AcmiParser.parse(io.StringIO(buf.getvalue()))
    assert acmi.globals.title == "Streamer Integration"
    assert acmi.objects[0x5001].properties.name == "C172"
    assert acmi.objects[0x5001].removed is True
    assert len(acmi.events) == 1
    assert acmi.events[0].type == EventType.LANDED
