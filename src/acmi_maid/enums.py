from enum import Enum


class ObjectClass(str, Enum):
    """Primary class tags for ACMI objects."""

    AIR = "Air"
    GROUND = "Ground"
    SEA = "Sea"
    WEAPON = "Weapon"
    SENSOR = "Sensor"
    NAVAID = "Navaid"
    MISC = "Misc"


class ObjectAttribute(str, Enum):
    """Attribute tags (size/role modifiers)."""

    STATIC = "Static"
    HEAVY = "Heavy"
    MEDIUM = "Medium"
    LIGHT = "Light"
    MINOR = "Minor"


class BasicType(str, Enum):
    """Basic type tags."""

    FIXED_WING = "FixedWing"
    ROTORCRAFT = "Rotorcraft"
    ARMOR = "Armor"
    ANTI_AIRCRAFT = "AntiAircraft"
    VEHICLE = "Vehicle"
    WATERCRAFT = "Watercraft"
    HUMAN = "Human"
    BIOLOGIC = "Biologic"
    MISSILE = "Missile"
    ROCKET = "Rocket"
    BOMB = "Bomb"
    TORPEDO = "Torpedo"
    PROJECTILE = "Projectile"
    BEAM = "Beam"
    DECOY = "Decoy"
    BUILDING = "Building"
    BULLSEYE = "Bullseye"
    WAYPOINT = "Waypoint"


class SpecificType(str, Enum):
    """Specific type tags."""

    TANK = "Tank"
    WARSHIP = "Warship"
    AIRCRAFT_CARRIER = "AircraftCarrier"
    SUBMARINE = "Submarine"
    INFANTRY = "Infantry"
    PARACHUTIST = "Parachutist"
    SHELL = "Shell"
    BULLET = "Bullet"
    GRENADE = "Grenade"
    FLARE = "Flare"
    CHAFF = "Chaff"
    SMOKE_GRENADE = "SmokeGrenade"
    AERODROME = "Aerodrome"
    CONTAINER = "Container"
    SHRAPNEL = "Shrapnel"
    EXPLOSION = "Explosion"


class EventType(str, Enum):
    """ACMI event types."""

    MESSAGE = "Message"
    BOOKMARK = "Bookmark"
    DEBUG = "Debug"
    LEFT_AREA = "LeftArea"
    DESTROYED = "Destroyed"
    TAKEN_OFF = "TakenOff"
    LANDED = "Landed"
    TIMEOUT = "Timeout"


class ObjectColor(str, Enum):
    """Predefined ACMI object colors."""

    RED = "Red"
    ORANGE = "Orange"
    YELLOW = "Yellow"
    GREEN = "Green"
    CYAN = "Cyan"
    BLUE = "Blue"
    VIOLET = "Violet"
