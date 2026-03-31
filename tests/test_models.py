from datetime import datetime, timezone
from acmi_maid.models import (
    Transform, GlobalProperties, ObjectProperties, Frame,
    AcmiObject, Event, AcmiFile,
    TimeRecord, PropertyRecord, RemovalRecord, EventRecord,
)
from acmi_maid.enums import EventType


def test_transform_defaults():
    t = Transform()
    assert t.longitude is None
    assert t.latitude is None
    assert t.altitude is None
    assert t.roll is None
    assert t.yaw is None
    assert t.u is None


def test_transform_with_values():
    t = Transform(longitude=41.6, latitude=41.5, altitude=2000.0,
                  roll=10.0, pitch=5.0, yaw=270.0)
    assert t.longitude == 41.6
    assert t.pitch == 5.0


def test_global_properties_defaults():
    g = GlobalProperties()
    assert g.reference_longitude == 0.0
    assert g.reference_latitude == 0.0
    assert g.data_source is None
    assert g.extra == {}


def test_object_properties_defaults():
    p = ObjectProperties()
    assert p.name is None
    assert p.locked_targets == []
    assert p.fuel_weights == []
    assert p.extra == {}


def test_object_properties_independent_defaults():
    """Each instance should get its own mutable defaults."""
    p1 = ObjectProperties()
    p2 = ObjectProperties()
    p1.locked_targets.append(1)
    assert p2.locked_targets == []


def test_frame():
    f = Frame(timestamp=10.5)
    assert f.timestamp == 10.5
    assert f.transform is None
    assert f.properties == {}


def test_acmi_object():
    obj = AcmiObject(id=0x3001)
    assert obj.id == 0x3001
    assert obj.removed is False
    assert obj.removed_at is None
    assert obj.timeline == []


def test_event():
    e = Event(timestamp=8.0, type=EventType.TAKEN_OFF,
              object_ids=[0x2723], text="Takeoff")
    assert e.type == EventType.TAKEN_OFF
    assert e.object_ids == [0x2723]


def test_acmi_file_defaults():
    f = AcmiFile()
    assert f.file_type == "text/acmi/tacview"
    assert f.file_version == "2.2"
    assert f.objects == {}
    assert f.events == []


def test_record_types():
    tr = TimeRecord(timestamp=47.13)
    assert tr.timestamp == 47.13

    pr = PropertyRecord(object_id=0x3001, properties={"Name": "F-16C"})
    assert pr.transform is None

    rr = RemovalRecord(object_id=0x6A56, timestamp=100.0)
    assert rr.object_id == 0x6A56

    er = EventRecord(event_type=EventType.DESTROYED,
                     object_ids=[0x6A56], text="", timestamp=100.0)
    assert er.event_type == EventType.DESTROYED
