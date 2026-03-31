import io
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from acmi_maid.models import (
    AcmiFile, AcmiObject, GlobalProperties, ObjectProperties,
    Transform, Frame, Event,
)
from acmi_maid.enums import EventType
from acmi_maid.parser import AcmiParser
from acmi_maid.writer import AcmiWriter


def _make_acmi() -> AcmiFile:
    """Build a test AcmiFile with known data."""
    acmi = AcmiFile()
    acmi.globals = GlobalProperties(
        data_source="TestSim",
        reference_time=datetime(2023, 12, 25, 10, 0, 0, tzinfo=timezone.utc),
        title="Test Mission",
    )
    obj = AcmiObject(id=0x3001)
    obj.properties = ObjectProperties(
        name="F-16C", type="Air+FixedWing", pilot="Viper 1",
    )
    obj.timeline = [
        Frame(
            timestamp=0.0,
            transform=Transform(longitude=41.6, latitude=41.5, altitude=2000.0,
                                roll=10.0, pitch=5.0, yaw=270.0),
            properties={"Name": "F-16C", "Type": "Air+FixedWing", "Pilot": "Viper 1"},
        ),
        Frame(
            timestamp=10.0,
            transform=Transform(longitude=41.7, altitude=2100.0),
            properties={},
        ),
    ]
    acmi.objects[0x3001] = obj

    obj2 = AcmiObject(id=0x3002)
    obj2.properties = ObjectProperties(name="MiG-29")
    obj2.timeline = [
        Frame(
            timestamp=0.0,
            transform=Transform(longitude=42.0, latitude=42.0, altitude=3000.0),
            properties={"Name": "MiG-29"},
        ),
    ]
    obj2.removed = True
    obj2.removed_at = 30.0
    acmi.objects[0x3002] = obj2

    acmi.events = [
        Event(timestamp=20.0, type=EventType.TAKEN_OFF,
              object_ids=[0x3001], text="Viper 1 airborne"),
    ]
    return acmi


class TestWriterToString:
    def test_header(self):
        acmi = AcmiFile()
        text = AcmiWriter.to_string(acmi)
        lines = text.split("\n")
        assert lines[0] == "FileType=text/acmi/tacview"
        assert lines[1] == "FileVersion=2.2"

    def test_globals(self):
        acmi = _make_acmi()
        text = AcmiWriter.to_string(acmi)
        assert "Title=Test Mission" in text
        assert "DataSource=TestSim" in text
        assert "ReferenceTime=2023-12-25T10:00:00Z" in text

    def test_objects(self):
        acmi = _make_acmi()
        text = AcmiWriter.to_string(acmi)
        assert "3001," in text
        assert "Name=F-16C" in text

    def test_removal(self):
        acmi = _make_acmi()
        text = AcmiWriter.to_string(acmi)
        assert "-3002" in text

    def test_events(self):
        acmi = _make_acmi()
        text = AcmiWriter.to_string(acmi)
        assert "Event=TakenOff|3001|Viper 1 airborne" in text

    def test_escape_commas(self):
        acmi = AcmiFile()
        acmi.globals.title = "Hello, World"
        text = AcmiWriter.to_string(acmi)
        assert r"Title=Hello\, World" in text


class TestRoundTrip:
    def test_roundtrip(self):
        acmi = _make_acmi()
        text = AcmiWriter.to_string(acmi)
        parsed = AcmiParser.parse(io.StringIO(text))

        assert parsed.globals.title == acmi.globals.title
        assert parsed.globals.data_source == acmi.globals.data_source
        assert 0x3001 in parsed.objects
        assert parsed.objects[0x3001].properties.name == "F-16C"
        assert parsed.objects[0x3002].removed is True
        assert len(parsed.events) == 1
        assert parsed.events[0].type == EventType.TAKEN_OFF

    def test_roundtrip_fixture(self):
        fixtures = Path(__file__).parent / "fixtures"
        original = AcmiParser.parse(fixtures / "full_mission.acmi")
        text = AcmiWriter.to_string(original)
        reparsed = AcmiParser.parse(io.StringIO(text))

        assert reparsed.globals.title == original.globals.title
        assert len(reparsed.objects) == len(original.objects)
        for oid in original.objects:
            assert oid in reparsed.objects
            assert (reparsed.objects[oid].properties.name
                    == original.objects[oid].properties.name)


class TestWriteFile:
    def test_write_to_file(self, tmp_path):
        acmi = _make_acmi()
        out = tmp_path / "output.acmi"
        AcmiWriter.write(acmi, out)
        assert out.exists()
        parsed = AcmiParser.parse(out)
        assert parsed.globals.title == "Test Mission"

    def test_write_compressed(self, tmp_path):
        acmi = _make_acmi()
        out = tmp_path / "output.zip.acmi"
        AcmiWriter.write(acmi, out, compress=True)
        assert out.exists()
        # Verify it's a valid zip
        assert zipfile.is_zipfile(out)
        parsed = AcmiParser.parse(out)
        assert parsed.globals.title == "Test Mission"

    def test_write_to_stream(self):
        acmi = _make_acmi()
        buf = io.StringIO()
        AcmiWriter.write(acmi, buf)
        text = buf.getvalue()
        assert "FileType=text/acmi/tacview" in text
