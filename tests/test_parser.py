import io
from pathlib import Path

import pytest

from acmi_maid.models import EventRecord, PropertyRecord, RemovalRecord, TimeRecord
from acmi_maid.parser import AcmiParseError, AcmiParser

FIXTURES = Path(__file__).parent / "fixtures"


# --- Header validation ---


def test_parse_error_includes_line_number():
    err = AcmiParseError("bad line", 42)
    assert err.line_number == 42
    assert "Line 42" in str(err)


def test_parse_invalid_header():
    bad = io.StringIO("NotAcmi\nFileVersion=2.2\n")
    with pytest.raises(AcmiParseError):
        AcmiParser.parse(bad)


def test_parse_invalid_version():
    bad = io.StringIO("FileType=text/acmi/tacview\nFileVersion=9.9\n")
    with pytest.raises(AcmiParseError):
        AcmiParser.parse(bad)


# --- Fixture parsing ---


def test_parse_minimal_fixture():
    acmi = AcmiParser.parse(FIXTURES / "minimal.acmi")
    assert acmi.file_version == "2.2"
    assert acmi.globals.reference_time is not None
    assert len(acmi.objects) == 0


def test_parse_basic_mission():
    acmi = AcmiParser.parse(FIXTURES / "basic_mission.acmi")
    assert acmi.globals.title == "Basic Mission"
    assert acmi.globals.data_source == "TestSim"
    # Two objects
    assert 0x3001 in acmi.objects
    assert 0x3002 in acmi.objects
    # Object properties
    viper = acmi.objects[0x3001]
    assert viper.properties.name == "F-16C"
    assert viper.properties.pilot == "Viper 1"
    assert viper.properties.coalition == "Blue"
    # Timeline
    assert len(viper.timeline) >= 3
    assert viper.timeline[0].transform is not None
    assert viper.timeline[0].transform.longitude == -118.5
    # Removal
    red1 = acmi.objects[0x3002]
    assert red1.removed is True
    assert red1.removed_at == 10.0
    # Events
    assert len(acmi.events) == 2
    assert acmi.events[0].type.value == "TakenOff"
    assert 0x3001 in acmi.events[0].object_ids


def test_parse_version21():
    acmi = AcmiParser.parse(FIXTURES / "version21.acmi")
    assert acmi.file_version == "2.1"
    assert 0xC001 in acmi.objects


def test_parse_bom_file():
    acmi = AcmiParser.parse(FIXTURES / "with_bom.acmi")
    assert acmi.file_version == "2.2"
    assert 0xD001 in acmi.objects


def test_parse_escaped_commas():
    acmi = AcmiParser.parse(FIXTURES / "escaped_commas.acmi")
    assert acmi.globals.title == "Test, with comma"
    obj = acmi.objects[0xB001]
    assert obj.properties.name == "Test, Aircraft"
    assert obj.properties.label == "Hello, World"


def test_parse_all_transform_formats():
    acmi = AcmiParser.parse(FIXTURES / "all_transforms.acmi")
    three = acmi.objects[0xA001]
    assert three.timeline[0].transform.altitude == 3000.0
    assert three.timeline[0].transform.roll is None
    five = acmi.objects[0xA002]
    assert five.timeline[0].transform.u == 100.0
    six = acmi.objects[0xA003]
    assert six.timeline[0].transform.yaw == 270.0
    nine = acmi.objects[0xA004]
    assert nine.timeline[0].transform.heading == 90.0
    # Delta with empty components
    assert three.timeline[1].transform.altitude == 3100.0
    assert three.timeline[1].transform.longitude is None
    # 6-component delta with interior empties (A003 at t=1.0): |||10||
    assert six.timeline[1].transform.roll == 10.0
    assert six.timeline[1].transform.longitude is None
    assert six.timeline[1].transform.yaw is None


def test_parse_from_string_io():
    text = "FileType=text/acmi/tacview\nFileVersion=2.2\n0,ReferenceTime=2025-01-15T08:00:00Z\n"
    acmi = AcmiParser.parse(io.StringIO(text))
    assert acmi.globals.reference_time is not None


def test_parse_from_string_io_with_bom():
    text = "\ufeffFileType=text/acmi/tacview\nFileVersion=2.2\n0,ReferenceTime=2025-01-15T08:00:00Z\n"
    acmi = AcmiParser.parse(io.StringIO(text))
    assert acmi.globals.reference_time is not None


def test_parse_comments_ignored():
    text = "FileType=text/acmi/tacview\nFileVersion=2.2\n// This is a comment\n0,ReferenceTime=2025-01-15T08:00:00Z\n"
    acmi = AcmiParser.parse(io.StringIO(text))
    assert acmi.globals.reference_time is not None


# --- Error paths ---


def test_parse_malformed_property_no_equals():
    text = "FileType=text/acmi/tacview\nFileVersion=2.2\n#0\n3001,NameF-16C\n"
    with pytest.raises(AcmiParseError, match="no '='"):
        AcmiParser.parse(io.StringIO(text))


def test_parse_invalid_object_id():
    text = "FileType=text/acmi/tacview\nFileVersion=2.2\n#0\nZZZZ,Name=Test\n"
    with pytest.raises(AcmiParseError, match="Invalid object ID"):
        AcmiParser.parse(io.StringIO(text))


def test_parse_invalid_transform_component_count():
    text = "FileType=text/acmi/tacview\nFileVersion=2.2\n#0\n3001,T=1|2|3|4\n"
    with pytest.raises(AcmiParseError, match="Invalid transform"):
        AcmiParser.parse(io.StringIO(text))


# --- Indexed properties ---


def test_parse_indexed_properties():
    text = (
        "FileType=text/acmi/tacview\nFileVersion=2.2\n#0\n"
        "3001,T=0|0|0,Name=Test,LockedTarget0=A001,LockedTarget1=A002,"
        "FuelWeight0=5000,FuelWeight2=3000\n"
    )
    acmi = AcmiParser.parse(io.StringIO(text))
    obj = acmi.objects[0x3001]
    assert obj.properties.locked_targets[0] == 0xA001
    assert obj.properties.locked_targets[1] == 0xA002
    assert obj.properties.fuel_weights[0] == 5000.0
    assert obj.properties.fuel_weights[2] == 3000.0


# --- iter_records ---


def test_iter_records_basic():
    records = list(AcmiParser.iter_records(FIXTURES / "basic_mission.acmi"))
    time_records = [r for r in records if isinstance(r, TimeRecord)]
    prop_records = [r for r in records if isinstance(r, PropertyRecord)]
    removal_records = [r for r in records if isinstance(r, RemovalRecord)]
    event_records = [r for r in records if isinstance(r, EventRecord)]
    assert len(time_records) >= 4
    assert len(prop_records) >= 4
    assert len(removal_records) == 1
    assert removal_records[0].object_id == 0x3002
    assert len(event_records) == 2


def test_iter_records_from_stream():
    text = "FileType=text/acmi/tacview\nFileVersion=2.2\n#0\nA001,T=-118.5|34.0|3000,Name=Test\n#1.0\nA001,T=||3100\n"
    records = list(AcmiParser.iter_records(io.StringIO(text)))
    time_recs = [r for r in records if isinstance(r, TimeRecord)]
    prop_recs = [r for r in records if isinstance(r, PropertyRecord)]
    assert len(time_recs) == 2
    assert len(prop_recs) == 2
    assert prop_recs[0].transform.longitude == -118.5
    assert prop_recs[1].transform.altitude == 3100.0
