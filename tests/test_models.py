from acmi_maid.enums import EventType
from acmi_maid.models import (
    AcmiFile,
    AcmiObject,
    Event,
    EventRecord,
    Frame,
    GlobalProperties,
    ObjectProperties,
    PropertyRecord,
    RemovalRecord,
    TimeRecord,
    Transform,
)


def test_transform_defaults():
    t = Transform()
    assert t.longitude is None
    assert t.latitude is None
    assert t.altitude is None
    assert t.roll is None
    assert t.pitch is None
    assert t.yaw is None
    assert t.u is None
    assert t.v is None
    assert t.heading is None


def test_transform_with_values():
    t = Transform(longitude=1.0, latitude=2.0, altitude=3.0)
    assert t.longitude == 1.0
    assert t.latitude == 2.0
    assert t.altitude == 3.0


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


def test_object_properties_no_shared_mutable_defaults():
    p1 = ObjectProperties()
    p2 = ObjectProperties()
    p1.locked_targets.append(1)
    assert p2.locked_targets == []


def test_frame():
    f = Frame(timestamp=1.5)
    assert f.timestamp == 1.5
    assert f.transform is None
    assert f.properties == {}


def test_acmi_object():
    obj = AcmiObject(id=0x3001)
    assert obj.id == 0x3001
    assert obj.removed is False
    assert obj.removed_at is None
    assert obj.timeline == []


def test_event():
    e = Event(timestamp=5.0, type=EventType.DESTROYED, object_ids=[0x3001], text="boom")
    assert e.timestamp == 5.0
    assert e.type == EventType.DESTROYED
    assert e.text == "boom"


def test_acmi_file_defaults():
    f = AcmiFile()
    assert f.file_type == "text/acmi/tacview"
    assert f.file_version == "2.2"
    assert f.objects == {}
    assert f.events == []


def test_record_types():
    tr = TimeRecord(timestamp=1.0)
    assert tr.timestamp == 1.0
    pr = PropertyRecord(object_id=1, properties={"Name": "F-16"})
    assert pr.transform is None
    rr = RemovalRecord(object_id=1, timestamp=2.0)
    assert rr.object_id == 1
    er = EventRecord(event_type=EventType.MESSAGE, object_ids=[], text="hi", timestamp=0.0)
    assert er.text == "hi"


def test_global_properties_custom_data():
    g = GlobalProperties()
    g.set_custom("myKey", "myValue")
    assert g.get_custom("myKey") == "myValue"
    assert g.get_all_custom() == {"myKey": "myValue"}

    g.set_custom("anotherKey", "anotherValue")
    assert g.get_all_custom() == {"myKey": "myValue", "anotherKey": "anotherValue"}

    assert g.delete_custom("myKey") is True
    assert g.get_custom("myKey") is None
    assert g.get_all_custom() == {"anotherKey": "anotherValue"}

    assert g.delete_custom("nonexistent") is False


def test_global_properties_custom_data_in_extra():
    g = GlobalProperties()
    g.set_custom("key1", "value1")
    assert "__custom_key1" in g.extra
    assert g.extra["__custom_key1"] == "value1"


def test_object_properties_custom_data():
    p = ObjectProperties()
    p.set_custom("pilotName", "John")
    assert p.get_custom("pilotName") == "John"
    assert p.get_all_custom() == {"pilotName": "John"}

    p.delete_custom("pilotName")
    assert p.get_custom("pilotName") is None
    assert p.get_all_custom() == {}


def test_object_properties_custom_data_isolation_from_extra():
    p = ObjectProperties()
    p.extra["someOtherKey"] = "otherValue"
    p.set_custom("customKey", "customValue")
    assert p.extra["someOtherKey"] == "otherValue"
    assert p.extra["__custom_customKey"] == "customValue"


def test_acmi_object_custom_data():
    obj = AcmiObject(id=0x3001)
    obj.set_custom_data("aircraftType", "F-16")
    assert obj.get_custom_data("aircraftType") == "F-16"

    obj.set_custom_data("pilot", "Jane")
    assert obj.get_all_custom_data() == {"aircraftType": "F-16", "pilot": "Jane"}

    assert obj.delete_custom_data("aircraftType") is True
    assert obj.get_custom_data("aircraftType") is None
    assert obj.get_all_custom_data() == {"pilot": "Jane"}


def test_acmi_file_global_custom_data():
    acmi = AcmiFile()
    acmi.set_global_custom_data("missionName", "Operation X")
    assert acmi.get_global_custom_data("missionName") == "Operation X"

    acmi.set_global_custom_data("difficulty", "hard")
    assert acmi.get_all_global_custom_data() == {"missionName": "Operation X", "difficulty": "hard"}

    assert acmi.delete_global_custom_data("missionName") is True
    assert acmi.get_global_custom_data("missionName") is None
    assert acmi.get_all_global_custom_data() == {"difficulty": "hard"}


def test_acmi_object_custom_data_via_properties():
    obj = AcmiObject(id=0x3001)
    obj.properties.set_custom("testKey", "testValue")
    assert obj.properties.get_custom("testKey") == "testValue"
    assert obj.get_custom_data("testKey") == "testValue"
