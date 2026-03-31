"""Tests for acmi_maid.utils."""

import pytest

from acmi_maid.models import AcmiFile, AcmiObject, ObjectRecord, Transform
from acmi_maid.utils import (
    filter_objects_by_type,
    get_active_objects_at,
    haversine_distance,
    interpolate_transform,
)


# ---------------------------------------------------------------------------
# haversine_distance
# ---------------------------------------------------------------------------


def test_haversine_same_point():
    assert haversine_distance(10.0, 20.0, 10.0, 20.0) == 0.0


def test_haversine_one_degree_latitude():
    # One degree of latitude ≈ 111 km
    dist = haversine_distance(0.0, 0.0, 0.0, 1.0)
    assert 111_000 < dist < 112_000


def test_haversine_one_degree_longitude_at_equator():
    # At the equator one degree of longitude ≈ 111 km as well
    dist = haversine_distance(0.0, 0.0, 1.0, 0.0)
    assert 111_000 < dist < 112_000


def test_haversine_symmetry():
    d1 = haversine_distance(0.0, 0.0, 10.0, 20.0)
    d2 = haversine_distance(10.0, 20.0, 0.0, 0.0)
    assert abs(d1 - d2) < 1e-6


def test_haversine_known_value():
    # London (51.5074° N, 0.1278° W) to Paris (48.8566° N, 2.3522° E)
    # Approximately 340 km
    dist = haversine_distance(-0.1278, 51.5074, 2.3522, 48.8566)
    assert 335_000 < dist < 345_000


# ---------------------------------------------------------------------------
# filter_objects_by_type
# ---------------------------------------------------------------------------


def _make_acmi_with_objects(*types) -> AcmiFile:
    """Create an AcmiFile with objects having the given Type property values."""
    acmi = AcmiFile()
    for i, type_str in enumerate(types, start=1):
        obj = AcmiObject(id=i)
        obj.records.append(ObjectRecord(timestamp=0.0, properties={"Type": type_str}))
        acmi.objects[i] = obj
    return acmi


def test_filter_by_type_matches():
    acmi = _make_acmi_with_objects("Air+FixedWing", "Ground+Light+Armor", "Air+FixedWing")
    result = filter_objects_by_type(acmi, "Air+FixedWing")
    assert len(result) == 2


def test_filter_by_type_case_insensitive():
    acmi = _make_acmi_with_objects("Air+FixedWing")
    assert len(filter_objects_by_type(acmi, "air+fixedwing")) == 1
    assert len(filter_objects_by_type(acmi, "AIR+FIXEDWING")) == 1


def test_filter_by_type_partial_match():
    acmi = _make_acmi_with_objects("Air+FixedWing+Military")
    result = filter_objects_by_type(acmi, "Air")
    assert len(result) == 1


def test_filter_by_type_no_match():
    acmi = _make_acmi_with_objects("Ground+Light+Armor")
    result = filter_objects_by_type(acmi, "Air+FixedWing")
    assert result == []


def test_filter_by_type_excludes_objects_without_type():
    acmi = AcmiFile()
    obj = AcmiObject(id=1)
    obj.records.append(ObjectRecord(timestamp=0.0, properties={"Name": "Unknown"}))
    acmi.objects[1] = obj
    assert filter_objects_by_type(acmi, "Air") == []


# ---------------------------------------------------------------------------
# get_active_objects_at
# ---------------------------------------------------------------------------


def test_get_active_at_includes_spawned_object():
    acmi = AcmiFile()
    obj = AcmiObject(id=1)
    obj.records.append(ObjectRecord(timestamp=0.0))
    acmi.objects[1] = obj
    assert any(o.id == 1 for o in get_active_objects_at(acmi, 5.0))


def test_get_active_at_excludes_future_spawn():
    acmi = AcmiFile()
    obj = AcmiObject(id=1)
    obj.records.append(ObjectRecord(timestamp=10.0))
    acmi.objects[1] = obj
    assert get_active_objects_at(acmi, 5.0) == []


def test_get_active_at_excludes_removed_object():
    acmi = AcmiFile()
    obj = AcmiObject(id=1, removed_at=3.0)
    obj.records.append(ObjectRecord(timestamp=0.0))
    acmi.objects[1] = obj
    # Removed at t=3, so not active at t=3
    assert get_active_objects_at(acmi, 3.0) == []
    # But was active at t=2.9
    assert any(o.id == 1 for o in get_active_objects_at(acmi, 2.9))


def test_get_active_at_mixes_correctly():
    acmi = AcmiFile()
    obj1 = AcmiObject(id=1)
    obj1.records.append(ObjectRecord(timestamp=0.0))

    obj2 = AcmiObject(id=2)
    obj2.records.append(ObjectRecord(timestamp=5.0))  # spawns at t=5

    obj3 = AcmiObject(id=3, removed_at=3.0)
    obj3.records.append(ObjectRecord(timestamp=0.0))

    acmi.objects = {1: obj1, 2: obj2, 3: obj3}
    active = get_active_objects_at(acmi, 4.0)
    ids = {o.id for o in active}
    assert 1 in ids
    assert 2 not in ids
    assert 3 not in ids


def test_get_active_excludes_object_without_records():
    acmi = AcmiFile()
    obj = AcmiObject(id=1)  # no records at all
    acmi.objects[1] = obj
    assert get_active_objects_at(acmi, 0.0) == []


# ---------------------------------------------------------------------------
# interpolate_transform
# ---------------------------------------------------------------------------


def test_interpolate_midpoint():
    obj = AcmiObject(id=1)
    obj.records.append(
        ObjectRecord(timestamp=0.0, transform=Transform(longitude=0.0, latitude=0.0, altitude=1000.0))
    )
    obj.records.append(
        ObjectRecord(timestamp=2.0, transform=Transform(longitude=2.0, latitude=2.0, altitude=2000.0))
    )
    result = interpolate_transform(obj, 1.0)
    assert result is not None
    assert abs(result.longitude - 1.0) < 1e-9
    assert abs(result.latitude - 1.0) < 1e-9
    assert abs(result.altitude - 1500.0) < 1e-9


def test_interpolate_at_exact_timestamps():
    obj = AcmiObject(id=1)
    obj.records.append(
        ObjectRecord(timestamp=0.0, transform=Transform(longitude=0.0, latitude=0.0, altitude=1000.0))
    )
    obj.records.append(
        ObjectRecord(timestamp=4.0, transform=Transform(longitude=4.0, latitude=4.0, altitude=2000.0))
    )
    r0 = interpolate_transform(obj, 0.0)
    assert r0 is not None
    assert r0.longitude == 0.0

    r4 = interpolate_transform(obj, 4.0)
    assert r4 is not None
    assert r4.longitude == 4.0


def test_interpolate_before_first_record():
    obj = AcmiObject(id=1)
    obj.records.append(
        ObjectRecord(timestamp=5.0, transform=Transform(longitude=10.0, latitude=20.0, altitude=1000.0))
    )
    result = interpolate_transform(obj, 0.0)
    assert result is not None
    assert result.longitude == 10.0


def test_interpolate_after_last_record():
    obj = AcmiObject(id=1)
    obj.records.append(
        ObjectRecord(timestamp=0.0, transform=Transform(longitude=10.0, latitude=20.0, altitude=1000.0))
    )
    result = interpolate_transform(obj, 100.0)
    assert result is not None
    assert result.longitude == 10.0


def test_interpolate_no_transform_data_returns_none():
    obj = AcmiObject(id=1)
    obj.records.append(ObjectRecord(timestamp=0.0, properties={"Name": "test"}))
    assert interpolate_transform(obj, 0.0) is None


def test_interpolate_empty_object_returns_none():
    obj = AcmiObject(id=1)
    assert interpolate_transform(obj, 0.0) is None


def test_interpolate_accumulated_transform():
    """Partial transform updates should accumulate before interpolation."""
    obj = AcmiObject(id=1)
    obj.records.append(
        ObjectRecord(timestamp=0.0, transform=Transform(longitude=0.0, latitude=0.0, altitude=1000.0))
    )
    # Only altitude changes at t=2
    obj.records.append(
        ObjectRecord(timestamp=2.0, transform=Transform(altitude=2000.0))
    )
    result = interpolate_transform(obj, 1.0)
    assert result is not None
    # Interpolating between (lon=0, lat=0, alt=1000) and (lon=0, lat=0, alt=2000)
    assert result.longitude == 0.0
    assert abs(result.altitude - 1500.0) < 1e-9


def test_interpolate_with_none_fields_uses_available_value():
    """If one endpoint has None for a field, the available value is used."""
    obj = AcmiObject(id=1)
    obj.records.append(
        ObjectRecord(timestamp=0.0, transform=Transform(longitude=0.0, latitude=0.0, altitude=None))
    )
    obj.records.append(
        ObjectRecord(timestamp=2.0, transform=Transform(longitude=2.0, latitude=2.0, altitude=None))
    )
    result = interpolate_transform(obj, 1.0)
    assert result is not None
    assert result.altitude is None
