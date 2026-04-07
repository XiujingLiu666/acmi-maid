"""Integration tests for the acmi-maid public API."""

import io
from datetime import datetime, timezone

from acmi_maid import (
    AcmiFile,
    AcmiObject,
    AcmiParseError,
    AcmiParser,
    AcmiStreamer,
    AcmiWriter,
    BasicType,
    Event,
    EventRecord,
    EventType,
    Frame,
    GlobalProperties,
    ObjectAttribute,
    ObjectClass,
    ObjectColor,
    ObjectProperties,
    PropertyRecord,
    RemovalRecord,
    SpecificType,
    TimeRecord,
    Transform,
)


def test_full_workflow():
    """Create -> write -> parse -> verify."""
    acmi = AcmiFile()
    acmi.globals = GlobalProperties(
        data_source="IntegrationTest",
        reference_time=datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
        title="Integration Test Mission",
    )
    obj = AcmiObject(id=0x4001)
    obj.properties.name = "F/A-18C"
    obj.properties.type = "Air+FixedWing"
    obj.properties.pilot = "Maverick"
    obj.timeline.append(
        Frame(
            timestamp=0.0,
            transform=Transform(
                longitude=-120.0, latitude=35.0, altitude=5000.0,
                roll=0.0, pitch=2.0, yaw=180.0,
            ),
            properties={"Name": "F/A-18C", "Type": "Air+FixedWing", "Pilot": "Maverick"},
        )
    )
    obj.timeline.append(
        Frame(
            timestamp=5.0,
            transform=Transform(longitude=-120.01, latitude=35.01, altitude=5100.0),
        )
    )
    acmi.objects[0x4001] = obj
    acmi.events.append(
        Event(timestamp=5.0, type=EventType.TAKEN_OFF, object_ids=[0x4001], text="Maverick airborne")
    )

    # Write and re-parse
    text = AcmiWriter.to_string(acmi)
    reparsed = AcmiParser.parse(io.StringIO(text))
    assert reparsed.globals.title == "Integration Test Mission"
    assert reparsed.objects[0x4001].properties.pilot == "Maverick"
    assert len(reparsed.events) == 1


def test_streamer_workflow():
    """Streamer -> parse -> verify."""
    buf = io.StringIO()
    globals_ = GlobalProperties(
        data_source="StreamTest",
        reference_time=datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
    )
    with AcmiStreamer(buf, globals=globals_) as s:
        s.write_frame(
            0.0, 0x5001,
            transform=Transform(longitude=-120.0, latitude=35.0, altitude=5000.0),
            Name="F-16C", Type="Air+FixedWing",
        )
        s.write_event(
            Event(timestamp=1.0, type=EventType.MESSAGE, text="Hello world")
        )
        s.remove_object(2.0, 0x5001)

    buf.seek(0)
    acmi = AcmiParser.parse(buf)
    assert acmi.objects[0x5001].properties.name == "F-16C"
    assert len(acmi.events) == 1


def test_all_public_symbols_importable():
    import acmi_maid
    for name in acmi_maid.__all__:
        assert hasattr(acmi_maid, name), f"{name} not found in acmi_maid"
