# acmi-maid

A Python tool-set for reading, writing, and processing `*.acmi` flight-recording
files as produced by [Tacview](https://www.tacview.net/).

## Features

* **Parse** plain-text and ZIP-compressed `.acmi` files.
* **Write** recordings back to plain-text or ZIP-compressed files.
* **Data model** with full property accumulation and timestamped state tracking.
* **Utilities**: haversine distance, object filtering by type, active-object
  queries, and linear position interpolation.

## Installation

```bash
pip install .
```

## Quick Start

```python
import acmi_maid

# Parse a recording
acmi = acmi_maid.parse_file("mission.acmi")

print(acmi.reference_time)   # e.g. "2011-06-01T00:00:00Z"
print(len(acmi.objects))     # number of tracked entities

# Get all fixed-wing aircraft
aircraft = acmi_maid.filter_objects_by_type(acmi, "Air+FixedWing")
for ac in aircraft:
    print(ac.name, ac.pilot, ac.coalition)

# Get the position of an aircraft at t=30 s
pos = acmi_maid.interpolate_transform(aircraft[0], 30.0)
print(pos.longitude, pos.latitude, pos.altitude)

# Compute distance between two lat/lon points
dist_m = acmi_maid.haversine_distance(pos.longitude, pos.latitude, 0.0, 0.0)

# Write a modified recording
acmi_maid.write_file(acmi, "output.acmi")
```

## ACMI File Format

ACMI is a text-based telemetry format used by Tacview.  Files begin with:

```
FileType=text/acmi/tacview
FileVersion=2.2
```

Each subsequent line is one of:

| Pattern | Meaning |
|---------|---------|
| `#<seconds>` | Start of a new time frame |
| `0,Key=Value,...` | Global property update |
| `<hex_id>,Key=Value,...` | Object property update |
| `-<hex_id>` | Object removal |
| `// text` | Comment (ignored) |

Object transforms use the `T` key:

```
T=Longitude|Latitude|Altitude[|Roll|Pitch|Yaw[|U|V]]
```

Empty fields (`||`) mean the value is unchanged from the previous frame.
Files may optionally be ZIP-compressed (`.zip.acmi`); both formats are
handled automatically.

## API Reference

### Parsing

| Function | Description |
|----------|-------------|
| `parse_file(path)` | Parse from a file path (auto-detects ZIP) |
| `parse_stream(stream)` | Parse from a binary stream (auto-detects ZIP) |
| `parse_string(text)` | Parse from a plain-text string |

### Writing

| Function | Description |
|----------|-------------|
| `write_file(acmi, path, *, compressed=False)` | Write to a file |
| `write_stream(acmi, stream, *, compressed=False)` | Write to a binary stream |
| `write_string(acmi)` | Serialise to a string |

### Utilities

| Function | Description |
|----------|-------------|
| `haversine_distance(lon1, lat1, lon2, lat2)` | Great-circle distance in metres |
| `filter_objects_by_type(acmi, type_pattern)` | Filter objects by `Type` property |
| `get_active_objects_at(acmi, time)` | Objects alive at a given timestamp |
| `interpolate_transform(obj, time)` | Linearly interpolate object position |

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
