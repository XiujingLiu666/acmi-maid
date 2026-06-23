# 数据模型

> 源文件: `src/acmi_maid/models.py`

所有数据模型使用 `@dataclass` 定义，构成 ACMI 数据的内存表示。

## 模型关系图

```
AcmiFile (根容器)
├── globals: GlobalProperties (CustomDataMixin)
├── objects: dict[int, AcmiObject]
│   └── AcmiObject
│       ├── properties: ObjectProperties (CustomDataMixin)
│       └── timeline: list[Frame]
│           └── Frame
│               ├── transform: Transform | None
│               └── properties: dict[str, str]
└── events: list[Event]
```

---

## CustomDataMixin

为 `GlobalProperties` 和 `ObjectProperties` 提供自定义数据存取能力的 Mixin 类。

自定义数据以 `__custom_` 前缀存储在 `extra` 字典中，与 ACMI 标准属性隔离。

```python
class CustomDataMixin:
    extra: dict[str, str]

    def set_custom(self, key: str, value: str) -> None: ...
    def get_custom(self, key: str) -> str | None: ...
    def delete_custom(self, key: str) -> bool: ...
    def get_all_custom(self) -> dict[str, str]: ...
```

---

## Transform

WGS-84 大地坐标系下的位置与姿态。`None` 表示"与上一帧相同"（ACMI 增量语义）。

```python
@dataclass
class Transform:
    longitude: float | None = None   # 经度（度）
    latitude: float | None = None    # 纬度（度）
    altitude: float | None = None    # 海拔高度（米 MSL）
    roll: float | None = None        # 横滚角（度）
    pitch: float | None = None       # 俯仰角（度）
    yaw: float | None = None         # 偏航角（度）
    u: float | None = None           # 平面坐标 U（米）
    v: float | None = None           # 平面坐标 V（米）
    heading: float | None = None     # 航向角（度）
```

---

## GlobalProperties

ACMI 全局属性（对应 object ID 0），包含录制元数据、参考时间/坐标等。

```python
@dataclass
class GlobalProperties(CustomDataMixin):
    data_source: str | None = None
    data_recorder: str | None = None
    reference_time: datetime | None = None
    recording_time: datetime | None = None
    reference_longitude: float = 0.0
    reference_latitude: float = 0.0
    author: str | None = None
    title: str | None = None
    category: str | None = None
    briefing: str | None = None
    debriefing: str | None = None
    comments: str | None = None
    map_id: str | None = None
    extra: dict[str, str] = field(default_factory=dict)
```

---

## ObjectProperties

所有已知 ACMI 对象属性的完整类型化表示。`None` 表示属性未设置/未知，`extra` 捕获未覆盖的属性。

### 属性分组

| 分组 | 字段 | 类型 |
|------|------|------|
| **身份标识** | `name`, `type`, `call_sign`, `registration`, `squawk`, `icao24`, `pilot`, `country`, `coalition`, `color`, `group`, `label`, `shape`, `short_name`, `long_name`, `full_name`, `debug` | `str \| None` |
| **对象引用** | `parent`, `next`, `focused_target` | `int \| None`（十六进制） |
| **对象引用** | `locked_targets` | `list[int]`（索引属性 LockedTarget0~N） |
| **飞行动力学** | `ias`, `cas`, `tas`, `mach`, `aoa`, `aos`, `agl`, `hdg`, `hdm` | `float \| None` |
| **状态** | `importance`, `health`, `visible` | `float \| None` |
| **状态** | `on_ground`, `disabled` | `bool \| None` |
| **控制与系统** | `throttle`, `throttle2`, `afterburner`, `landing_gear`, `flaps`, `air_brakes`, `tailhook`, `parachute`, `drag_chute` | `float \| None` |
| **燃油** | `fuel_weights` | `list[float \| None]`（最多 10 个油箱，索引属性 FuelWeight0~9） |
| **雷达** | `radar_mode` | `int \| None`（十进制） |
| **雷达** | `radar_range`, `radar_azimuth`, `radar_elevation`, `engagement_range` | `float \| None` |
| **G 力** | `vertical_g`, `longitudinal_g`, `lateral_g` | `float \| None` |
| **尺寸** | `length`, `width`, `height`, `radius` | `float \| None` |
| **飞行员头部追踪** | `pilot_head_roll`, `pilot_head_pitch`, `pilot_head_yaw` | `float \| None` |
| **控制输入** | `roll_control_input`, `pitch_control_input`, `yaw_control_input` | `float \| None` |
| **控制输入** | `trigger_pressed` | `bool \| None` |
| **生物特征** | `heart_rate`, `spo2` | `float \| None` |
| **通用** | `extra` | `dict[str, str]` |

---

## Frame

对象在特定时间戳的状态增量快照，仅包含该时刻变化的属性。

```python
@dataclass
class Frame:
    timestamp: float
    transform: Transform | None = None
    properties: dict[str, str] = field(default_factory=dict)
```

---

## AcmiObject

ACMI 录制中的一个被追踪对象。`timeline` 记录其状态变化历史，`removed` 标记是否已被移除。

```python
@dataclass
class AcmiObject:
    id: int
    properties: ObjectProperties = field(default_factory=ObjectProperties)
    timeline: list[Frame] = field(default_factory=list)
    removed: bool = False
    removed_at: float | None = None
```

### 自定义数据便捷方法

| 方法 | 说明 |
|------|------|
| `set_custom_data(key, value)` | 设置自定义数据（同步写入 properties.extra 和最新 timeline frame） |
| `get_custom_data(key)` | 获取自定义数据（优先从最新 timeline frame 读取） |
| `delete_custom_data(key)` | 删除自定义数据（同时清理 properties.extra 和最新 frame） |
| `get_all_custom_data()` | 获取所有自定义数据（合并 properties.extra 和最新 frame） |

---

## Event

ACMI 事件记录（如起飞、摧毁、消息等）。

```python
@dataclass
class Event:
    timestamp: float
    type: EventType
    object_ids: list[int] = field(default_factory=list)
    text: str = ""
```

---

## AcmiFile

完整 ACMI 录制的根容器。

```python
@dataclass
class AcmiFile:
    file_type: str = "text/acmi/tacview"
    file_version: str = "2.2"
    globals: GlobalProperties = field(default_factory=GlobalProperties)
    objects: dict[int, AcmiObject] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)
```

### 全局自定义数据便捷方法

| 方法 | 说明 |
|------|------|
| `set_global_custom_data(key, value)` | 设置全局自定义数据 |
| `get_global_custom_data(key)` | 获取全局自定义数据 |
| `delete_global_custom_data(key)` | 删除全局自定义数据 |
| `get_all_global_custom_data()` | 获取所有全局自定义数据 |

---

## 原始记录类型（用于 iter_records）

| 类型 | 用途 | 字段 |
|------|------|------|
| `TimeRecord` | 时间戳标记（`#<seconds>`） | `timestamp: float` |
| `PropertyRecord` | 对象属性更新行 | `object_id: int`, `properties: dict[str, str]`, `transform: Transform \| None` |
| `RemovalRecord` | 对象移除行（`-<hex_id>`） | `object_id: int`, `timestamp: float` |
| `EventRecord` | 事件记录 | `event_type: EventType`, `object_ids: list[int]`, `text: str`, `timestamp: float` |

```python
Record = TimeRecord | PropertyRecord | RemovalRecord | EventRecord
```
