import io
import zipfile
from pathlib import Path

from acmi_maid.parser import AcmiParser, AcmiParseError
from acmi_maid.models import (
    AcmiFile, TimeRecord, PropertyRecord, RemovalRecord, EventRecord,
)
from acmi_maid.enums import EventType

FIXTURES = Path(__file__).parent / "fixtures"


class TestParseMinimal:
    def test_parse_minimal(self):
        acmi = AcmiParser.parse(FIXTURES / "minimal.acmi")
        assert acmi.file_type == "text/acmi/tacview"
        assert acmi.file_version == "2.2"
        assert acmi.objects == {}

    def test_parse_v21(self):
        acmi = AcmiParser.parse(FIXTURES / "v21.acmi")
        assert acmi.file_version == "2.1"


class TestParseFullMission:
    def test_globals(self):
        acmi = AcmiParser.parse(FIXTURES / "full_mission.acmi")
        assert acmi.globals.title == "Test Mission"
        assert acmi.globals.data_source == "TestSim"
        assert acmi.globals.reference_time is not None
        assert acmi.globals.reference_time.year == 2023

    def test_objects(self):
        acmi = AcmiParser.parse(FIXTURES / "full_mission.acmi")
        assert 0x3001 in acmi.objects
        assert 0x3002 in acmi.objects
        obj1 = acmi.objects[0x3001]
        assert obj1.properties.name == "F-16C"
        assert obj1.properties.pilot == "Viper 1"
        assert obj1.properties.country == "us"

    def test_timeline(self):
        acmi = AcmiParser.parse(FIXTURES / "full_mission.acmi")
        obj1 = acmi.objects[0x3001]
        assert len(obj1.timeline) == 3  # at t=0, t=10.5, t=20.0
        assert obj1.timeline[0].timestamp == 0.0
        assert obj1.timeline[0].transform is not None
        assert obj1.timeline[0].transform.longitude == 41.6

    def test_delta_transform(self):
        acmi = AcmiParser.parse(FIXTURES / "full_mission.acmi")
        obj1 = acmi.objects[0x3001]
        frame1 = obj1.timeline[1]  # t=10.5
        assert frame1.transform.longitude == 41.7
        assert frame1.transform.latitude is None  # unchanged
        assert frame1.transform.altitude == 2100.0

    def test_removal(self):
        acmi = AcmiParser.parse(FIXTURES / "full_mission.acmi")
        obj2 = acmi.objects[0x3002]
        assert obj2.removed is True
        assert obj2.removed_at == 30.0

    def test_events(self):
        acmi = AcmiParser.parse(FIXTURES / "full_mission.acmi")
        assert len(acmi.events) == 2
        assert acmi.events[0].type == EventType.TAKEN_OFF
        assert 0x3001 in acmi.events[0].object_ids
        assert acmi.events[1].type == EventType.DESTROYED

    def test_numeric_properties(self):
        acmi = AcmiParser.parse(FIXTURES / "full_mission.acmi")
        obj1 = acmi.objects[0x3001]
        assert obj1.properties.ias == 150.5
        assert obj1.properties.throttle == 0.8


class TestParseFromStream:
    def test_parse_from_string_io(self):
        content = "FileType=text/acmi/tacview\nFileVersion=2.2\n"
        acmi = AcmiParser.parse(io.StringIO(content))
        assert acmi.file_version == "2.2"

    def test_parse_with_bom_stream(self):
        content = "\ufeffFileType=text/acmi/tacview\nFileVersion=2.2\n"
        acmi = AcmiParser.parse(io.StringIO(content))
        assert acmi.file_version == "2.2"

    def test_parse_with_comments(self):
        content = (
            "FileType=text/acmi/tacview\n"
            "FileVersion=2.2\n"
            "// This is a comment\n"
            "0,Title=Test\n"
        )
        acmi = AcmiParser.parse(io.StringIO(content))
        assert acmi.globals.title == "Test"


class TestParseZip:
    def test_parse_zip(self, tmp_path):
        text = "FileType=text/acmi/tacview\nFileVersion=2.2\n0,Title=Zipped\n"
        zip_path = tmp_path / "test.zip.acmi"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("mission.acmi", text)
        acmi = AcmiParser.parse(zip_path)
        assert acmi.globals.title == "Zipped"


class TestParseErrors:
    def test_invalid_header(self):
        try:
            AcmiParser.parse(io.StringIO("not a valid header\n"))
            assert False, "Should have raised AcmiParseError"
        except AcmiParseError as e:
            assert e.line_number == 1

    def test_bad_version(self):
        try:
            AcmiParser.parse(io.StringIO(
                "FileType=text/acmi/tacview\nFileVersion=3.0\n"
            ))
            assert False, "Should have raised AcmiParseError"
        except AcmiParseError as e:
            assert e.line_number == 2


class TestParseEscapedCommas:
    def test_escaped_comma_in_value(self):
        content = (
            "FileType=text/acmi/tacview\n"
            "FileVersion=2.2\n"
            r"0,Title=Hello\, World" + "\n"
        )
        acmi = AcmiParser.parse(io.StringIO(content))
        assert acmi.globals.title == "Hello, World"


class TestIterRecords:
    def test_iter_records(self):
        content = (
            "FileType=text/acmi/tacview\n"
            "FileVersion=2.2\n"
            "#0\n"
            "3001,T=41.6|41.5|2000,Name=F-16\n"
            "#10\n"
            "-3001\n"
        )
        records = list(AcmiParser.iter_records(io.StringIO(content)))
        assert isinstance(records[0], TimeRecord)
        assert records[0].timestamp == 0.0
        assert isinstance(records[1], PropertyRecord)
        assert records[1].object_id == 0x3001
        assert isinstance(records[2], TimeRecord)
        assert isinstance(records[3], RemovalRecord)
