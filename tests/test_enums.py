from acmi_maid.enums import (
    ObjectClass, ObjectAttribute, BasicType, SpecificType,
    EventType, ObjectColor,
)


def test_object_class_values():
    assert ObjectClass.AIR == "Air"
    assert ObjectClass.GROUND == "Ground"
    assert ObjectClass("Sea") == ObjectClass.SEA


def test_event_type_values():
    assert EventType.DESTROYED == "Destroyed"
    assert EventType.TAKEN_OFF == "TakenOff"
    assert EventType("Landed") == EventType.LANDED


def test_basic_type_values():
    assert BasicType.FIXED_WING == "FixedWing"
    assert BasicType.ROTORCRAFT == "Rotorcraft"
    assert BasicType.MISSILE == "Missile"


def test_specific_type_values():
    assert SpecificType.TANK == "Tank"
    assert SpecificType.FLARE == "Flare"


def test_object_color_values():
    assert ObjectColor.RED == "Red"
    assert ObjectColor.VIOLET == "Violet"


def test_enums_are_str_subclass():
    assert isinstance(ObjectClass.AIR, str)
    assert isinstance(EventType.DESTROYED, str)
    assert isinstance(BasicType.FIXED_WING, str)
