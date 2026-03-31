"""Tests for acmi_maid.models."""

import pytest

from acmi_maid.models import AcmiFile, AcmiObject, ObjectRecord, Transform


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------


def test_transform_default_all_none():
    t = Transform()
    assert t.longitude is None
    assert t.latitude is None
    assert t.altitude is None
    assert t.roll is None
    assert t.pitch is None
    assert t.yaw is None
    assert t.u is None
    assert t.v is None


def test_transform_merge_updates_non_none():
    base = Transform(longitude=10.0, latitude=20.0, altitude=1000.0)
    update = Transform(altitude=1500.0)
    merged = base.merge(update)
    assert merged.longitude == 10.0
    assert merged.latitude == 20.0
    assert merged.altitude == 1500.0


def test_transform_merge_keeps_base_when_update_is_none():
    base = Transform(longitude=10.0, latitude=20.0)
    update = Transform(longitude=None, latitude=21.0)
    merged = base.merge(update)
    assert merged.longitude == 10.0
    assert merged.latitude == 21.0


def test_transform_merge_full_override():
    base = Transform(longitude=1.0, latitude=2.0, altitude=100.0, roll=5.0)
    update = Transform(longitude=3.0, latitude=4.0, altitude=200.0, roll=10.0)
    merged = base.merge(update)
    assert merged.longitude == 3.0
    assert merged.latitude == 4.0
    assert merged.altitude == 200.0
    assert merged.roll == 10.0


# ---------------------------------------------------------------------------
# AcmiObject
# ---------------------------------------------------------------------------


def test_acmi_object_get_property_latest():
    obj = AcmiObject(id=1)
    obj.records.append(ObjectRecord(timestamp=0.0, properties={"Name": "F-16C", "Color": "Red"}))
    obj.records.append(ObjectRecord(timestamp=1.0, properties={"Color": "Blue"}))
    assert obj.get_property("Name") == "F-16C"
    assert obj.get_property("Color") == "Blue"


def test_acmi_object_get_property_at_time():
    obj = AcmiObject(id=1)
    obj.records.append(ObjectRecord(timestamp=0.0, properties={"Color": "Red"}))
    obj.records.append(ObjectRecord(timestamp=2.0, properties={"Color": "Blue"}))
    assert obj.get_property("Color", at_time=1.0) == "Red"
    assert obj.get_property("Color", at_time=2.0) == "Blue"


def test_acmi_object_get_property_missing():
    obj = AcmiObject(id=1)
    obj.records.append(ObjectRecord(timestamp=0.0, properties={"Name": "F-16C"}))
    assert obj.get_property("Pilot") is None


def test_acmi_object_convenience_properties():
    obj = AcmiObject(id=1)
    obj.records.append(
        ObjectRecord(
            timestamp=0.0,
            properties={
                "Name": "F-16C",
                "Pilot": "Viper",
                "Type": "Air+FixedWing",
                "Color": "Red",
                "Coalition": "Enemies",
                "Country": "US",
                "CallSign": "Viper11",
            },
        )
    )
    assert obj.name == "F-16C"
    assert obj.pilot == "Viper"
    assert obj.type == "Air+FixedWing"
    assert obj.color == "Red"
    assert obj.coalition == "Enemies"
    assert obj.country == "US"
    assert obj.callsign == "Viper11"


def test_acmi_object_first_last_seen():
    obj = AcmiObject(id=1)
    obj.records.append(ObjectRecord(timestamp=0.0))
    obj.records.append(ObjectRecord(timestamp=5.0))
    assert obj.first_seen == 0.0
    assert obj.last_seen == 5.0


def test_acmi_object_first_last_seen_empty():
    obj = AcmiObject(id=1)
    assert obj.first_seen is None
    assert obj.last_seen is None


def test_acmi_object_get_transform_accumulates():
    obj = AcmiObject(id=1)
    obj.records.append(
        ObjectRecord(
            timestamp=0.0,
            transform=Transform(longitude=10.0, latitude=20.0, altitude=1000.0),
        )
    )
    obj.records.append(
        ObjectRecord(
            timestamp=1.0,
            transform=Transform(altitude=1500.0),  # only altitude changes
        )
    )
    t = obj.get_transform()
    assert t is not None
    assert t.longitude == 10.0
    assert t.latitude == 20.0
    assert t.altitude == 1500.0


def test_acmi_object_get_transform_at_time():
    obj = AcmiObject(id=1)
    obj.records.append(
        ObjectRecord(
            timestamp=0.0,
            transform=Transform(longitude=10.0),
        )
    )
    obj.records.append(
        ObjectRecord(
            timestamp=2.0,
            transform=Transform(longitude=20.0),
        )
    )
    t0 = obj.get_transform(at_time=0.0)
    assert t0 is not None
    assert t0.longitude == 10.0

    t1 = obj.get_transform(at_time=1.0)
    assert t1 is not None
    assert t1.longitude == 10.0  # still previous value


def test_acmi_object_get_transform_none():
    obj = AcmiObject(id=1)
    obj.records.append(ObjectRecord(timestamp=0.0, properties={"Name": "test"}))
    assert obj.get_transform() is None


# ---------------------------------------------------------------------------
# AcmiFile
# ---------------------------------------------------------------------------


def test_acmi_file_global_property_helpers():
    acmi = AcmiFile()
    acmi.global_properties["ReferenceTime"] = "2011-06-01T00:00:00Z"
    acmi.global_properties["ReferenceLongitude"] = "41.5"
    acmi.global_properties["ReferenceLatitude"] = "42.0"
    acmi.global_properties["ReferenceAltitude"] = "100.0"
    acmi.global_properties["DataSource"] = "DCS"
    acmi.global_properties["DataRecorder"] = "Tacview"
    acmi.global_properties["Title"] = "Test Mission"
    acmi.global_properties["Author"] = "Pilot"

    assert acmi.reference_time == "2011-06-01T00:00:00Z"
    assert acmi.reference_longitude == 41.5
    assert acmi.reference_latitude == 42.0
    assert acmi.reference_altitude == 100.0
    assert acmi.data_source == "DCS"
    assert acmi.data_recorder == "Tacview"
    assert acmi.title == "Test Mission"
    assert acmi.author == "Pilot"


def test_acmi_file_global_properties_none_when_absent():
    acmi = AcmiFile()
    assert acmi.reference_time is None
    assert acmi.reference_longitude is None
    assert acmi.reference_latitude is None
    assert acmi.reference_altitude is None
    assert acmi.data_source is None
    assert acmi.title is None
    assert acmi.author is None


def test_acmi_file_duration():
    acmi = AcmiFile()
    obj = AcmiObject(id=1)
    obj.records.append(ObjectRecord(timestamp=0.0))
    obj.records.append(ObjectRecord(timestamp=10.0))
    acmi.objects[1] = obj
    assert acmi.duration == 10.0


def test_acmi_file_duration_empty():
    acmi = AcmiFile()
    assert acmi.duration is None


def test_acmi_file_get_object():
    acmi = AcmiFile()
    obj = AcmiObject(id=5)
    acmi.objects[5] = obj
    assert acmi.get_object(5) is obj
    assert acmi.get_object(99) is None


def test_acmi_file_iter_objects():
    acmi = AcmiFile()
    acmi.objects[1] = AcmiObject(id=1)
    acmi.objects[2] = AcmiObject(id=2)
    ids = {obj.id for obj in acmi.iter_objects()}
    assert ids == {1, 2}
