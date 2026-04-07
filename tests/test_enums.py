from acmi_maid.enums import (
    BasicType,
    EventType,
    ObjectAttribute,
    ObjectClass,
    ObjectColor,
    SpecificType,
)


def test_object_class_values():
    assert ObjectClass.AIR == "Air"
    assert ObjectClass.GROUND == "Ground"
    assert ObjectClass.SEA == "Sea"
    assert ObjectClass.WEAPON == "Weapon"
    assert ObjectClass.SENSOR == "Sensor"
    assert ObjectClass.NAVAID == "Navaid"
    assert ObjectClass.MISC == "Misc"


def test_event_type_values():
    assert EventType.MESSAGE == "Message"
    assert EventType.DESTROYED == "Destroyed"
    assert EventType.TAKEN_OFF == "TakenOff"
    assert EventType.LANDED == "Landed"


def test_object_color_values():
    assert ObjectColor.RED == "Red"
    assert ObjectColor.BLUE == "Blue"


def test_str_enum_behavior():
    # str(Enum) value depends on Python version; value access is reliable
    assert ObjectClass.AIR.value == "Air"
    assert EventType.DESTROYED.value == "Destroyed"
    # As str subclass, direct comparison with str works
    assert ObjectClass.AIR == "Air"


def test_basic_type_values():
    assert BasicType.FIXED_WING == "FixedWing"
    assert BasicType.ROTORCRAFT == "Rotorcraft"
    assert BasicType.MISSILE == "Missile"


def test_specific_type_values():
    assert SpecificType.TANK == "Tank"
    assert SpecificType.AIRCRAFT_CARRIER == "AircraftCarrier"


def test_object_attribute_values():
    assert ObjectAttribute.STATIC == "Static"
    assert ObjectAttribute.HEAVY == "Heavy"
