# ACMI Maid — Code Wiki

> **Pure-Python ACMI 2.2 Toolset for Tacview Flight Recordings**
>
> 版本: 0.1.0 | 许可证: MIT | Python ≥ 3.10 | 零外部依赖

---

## 目录

1. [项目概述](#1-项目概述)
2. [项目架构](#2-项目架构)
3. [目录结构](#3-目录结构)
4. [模块详解](#4-模块详解)
   - 4.1 [enums — 枚举定义](#41-enums--枚举定义)
   - 4.2 [models — 数据模型](#42-models--数据模型)
   - 4.3 [utils — 工具函数](#43-utils--工具函数)
   - 4.4 [parser — 解析器](#44-parser--解析器)
   - 4.5 [writer — 写入器](#45-writer--写入器)
   - 4.6 [streamer — 流式写入器](#46-streamer--流式写入器)
5. [模块依赖关系](#5-模块依赖关系)
6. [数据流与核心流程](#6-数据流与核心流程)
7. [ACMI 文件格式说明](#7-acmi-文件格式说明)
8. [自定义数据接口](#8-自定义数据接口)
9. [测试体系](#9-测试体系)
10. [项目运行方式](#10-项目运行方式)
11. [设计决策与约定](#11-设计决策与约定)

---

## 1. 项目概述

**acmi-maid** 是一个纯 Python 实现的 ACMI（Air Combat Maneuvering Instrumentation）2.1/2.2 格式工具集，用于处理 [Tacview](https://www.tacview.net/) 飞行记录文件。项目提供完整的解析、序列化和流式写入能力，支持：

- **解析** ACMI 文本文件（含 ZIP 压缩格式）为结构化 Python 对象
- **序列化** Python 对象回 ACMI 文本格式（含 ZIP 压缩输出）
- **流式写入** 实时遥测数据，无需在内存中缓存完整录制
- **自定义数据** 通过 `CustomDataMixin` 机制读写用户扩展属性
- **零外部依赖**，仅使用 Python 标准库

### 技术栈

| 项目 | 技术 |
|------|------|
| 语言 | Python 3.13（最低 3.10） |
| 构建工具 | uv (uv_build) |
| 包管理 | uv + pyproject.toml |
| 测试框架 | pytest ≥ 9.0.2 |
| 类型标记 | py.typed (PEP 561) |
| 运行时依赖 | 无（零外部依赖） |

---

## 2. 项目架构

```
┌─────────────────────────────────────────────────────────┐
│                     acmi_maid (包)                       │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │  enums   │  │  models  │  │        utils          │  │
│  │ (枚举定义)│  │(数据模型) │  │  (Transform/DateTime │  │
│  │          │  │          │  │   /Escape 工具函数)    │  │
│  └────┬─────┘  └────┬─────┘  └──────────┬───────────┘  │
│       │             │                    │              │
│       │    ┌────────┴────────┐           │              │
│       │    │                 │           │              │
│  ┌────┴────┴──┐   ┌─────────┴──┐  ┌────┴─────────┐    │
│  │   parser   │   │   writer    │  │   streamer   │    │
│  │ (ACMI解析) │   │ (ACMI序列化)│  │ (流式写入)   │    │
│  └────────────┘   └────────────┘  └──────────────┘    │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │              __init__.py (公共 API 导出)           │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**架构分层**：

- **底层**：`enums`（枚举常量）+ `models`（数据结构）+ `utils`（纯函数工具）
- **中层**：`parser`（解析）+ `writer`（序列化）+ `streamer`（流式写入）
- **顶层**：`__init__.py`（统一公共 API 导出）

---

## 3. 目录结构

```
acmi-maid/
├── src/
│   └── acmi_maid/              # 核心源码包
│       ├── __init__.py         # 公共 API 导出
│       ├── enums.py            # ACMI 枚举类型定义
│       ├── models.py           # 数据模型（dataclass）
│       ├── utils.py            # 工具函数
│       ├── parser.py           # ACMI 文件解析器
│       ├── writer.py           # ACMI 文件写入器
│       ├── streamer.py         # 流式 ACMI 写入器
│       └── py.typed            # PEP 561 类型标记
├── tests/
│   ├── fixtures/               # ACMI 测试固件文件
│   │   ├── minimal.acmi        # 最小化 ACMI 文件
│   │   ├── basic_mission.acmi  # 基础任务（含对象/事件/移除）
│   │   ├── all_transforms.acmi # 所有 Transform 格式
│   │   ├── escaped_commas.acmi # 逗号转义测试
│   │   ├── version21.acmi      # ACMI 2.1 版本测试
│   │   └── with_bom.acmi       # BOM 头测试
│   ├── test_enums.py           # 枚举测试
│   ├── test_models.py          # 模型测试
│   ├── test_utils.py           # 工具函数测试
│   ├── test_parser.py          # 解析器测试
│   ├── test_writer.py          # 写入器测试
│   ├── test_streamer.py        # 流式写入器测试
│   └── test_integration.py     # 集成测试
├── docs/                       # 文档
│   └── todos/todo.md           # TODO 列表
├── pyproject.toml              # 项目配置
├── uv.lock                     # 依赖锁定
├── .python-version             # Python 版本 (3.13)
├── .gitignore
└── LICENSE                     # MIT 许可证
```

---

## 4. 模块详解

### 4.1 enums — 枚举定义

**文件**: [enums.py](file:///c:/Users/bytimes/lxj/projects/acmi-maid/src/acmi_maid/enums.py)

所有枚举均继承自 `str` 和 `Enum`，可直接与字符串比较，用于 ACMI 格式中的标签值分类。

| 枚举类 | 用途 | 值示例 |
|--------|------|--------|
| `ObjectClass` | 对象主分类 | `Air`, `Ground`, `Sea`, `Weapon`, `Sensor`, `Navaid`, `Misc` |
| `ObjectAttribute` | 对象属性修饰 | `Static`, `Heavy`, `Medium`, `Light`, `Minor` |
| `BasicType` | 基础类型标签 | `FixedWing`, `Rotorcraft`, `Missile`, `Bomb`, `Beam` 等 |
| `SpecificType` | 具体类型标签 | `Tank`, `Warship`, `AircraftCarrier`, `Submarine`, `Infantry` 等 |
| `EventType` | ACMI 事件类型 | `Message`, `Bookmark`, `Debug`, `LeftArea`, `Destroyed`, `TakenOff`, `Landed`, `Timeout` |
| `ObjectColor` | 预定义颜色 | `Red`, `Orange`, `Yellow`, `Green`, `Cyan`, `Blue`, `Violet` |

**设计要点**：
- 使用 `str, Enum` 双重继承，枚举值可直接与字符串比较（如 `ObjectClass.AIR == "Air"`）
- 对应 ACMI 格式中 `Type=` 属性值的标签部分（如 `Type=Air+FixedWing` 中的 `Air` 和 `FixedWing`）

---

### 4.2 models — 数据模型

**文件**: [models.py](file:///c:/Users/bytimes/lxj/projects/acmi-maid/src/acmi_maid/models.py)

核心数据模型，全部使用 `@dataclass` 定义，构成 ACMI 数据的内存表示。

#### CustomDataMixin

```python
class CustomDataMixin:
    extra: dict[str, str]
    def set_custom(self, key: str, value: str) -> None: ...
    def get_custom(self, key: str) -> str | None: ...
    def delete_custom(self, key: str) -> bool: ...
    def get_all_custom(self) -> dict[str, str]: ...
```

Mixin 类，为 `GlobalProperties` 和 `ObjectProperties` 提供自定义数据存取能力。自定义数据以 `__custom_` 前缀存储在 `extra` 字典中，与 ACMI 标准属性隔离。

#### Transform

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

WGS-84 大地坐标系下的位置与姿态。`None` 表示"与上一帧相同"（ACMI 增量语义）。

#### GlobalProperties

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

ACMI 全局属性（对应 object ID 0），包含录制元数据、参考时间/坐标等。

#### ObjectProperties

```python
@dataclass
class ObjectProperties(CustomDataMixin):
    # 身份标识 (name, type, call_sign, registration, squawk, icao24, pilot, country, coalition, color, group, label, shape, short_name, long_name, full_name, debug)
    # 对象引用 (parent, next, focused_target, locked_targets)
    # 飞行动力学 (ias, cas, tas, mach, aoa, aos, agl, hdg, hdm)
    # 状态 (importance, health, on_ground, disabled, visible)
    # 控制与系统 (throttle, throttle2, afterburner, landing_gear, flaps, air_brakes, tailhook, parachute, drag_chute)
    # 燃油 (fuel_weights: list[float | None])  — 最多 10 个油箱
    # 雷达 (radar_mode, radar_range, radar_azimuth, radar_elevation, engagement_range)
    # G 力 (vertical_g, longitudinal_g, lateral_g)
    # 尺寸 (length, width, height, radius)
    # 飞行员头部追踪 (pilot_head_roll, pilot_head_pitch, pilot_head_yaw)
    # 控制输入 (roll_control_input, pitch_control_input, yaw_control_input, trigger_pressed)
    # 生物特征 (heart_rate, spo2)
    # 通用 (extra: dict[str, str])
```

所有已知 ACMI 对象属性的完整类型化表示。`None` 表示属性未设置/未知，`extra` 捕获未覆盖的属性。

#### Frame

```python
@dataclass
class Frame:
    timestamp: float
    transform: Transform | None = None
    properties: dict[str, str] = field(default_factory=dict)
```

对象在特定时间戳的状态增量快照，仅包含该时刻变化的属性。

#### AcmiObject

```python
@dataclass
class AcmiObject:
    id: int
    properties: ObjectProperties = field(default_factory=ObjectProperties)
    timeline: list[Frame] = field(default_factory=list)
    removed: bool = False
    removed_at: float | None = None
```

ACMI 录制中的一个被追踪对象。`timeline` 记录其状态变化历史，`removed` 标记是否已被移除。

提供自定义数据便捷方法：`set_custom_data()`, `get_custom_data()`, `delete_custom_data()`, `get_all_custom_data()`。

#### Event

```python
@dataclass
class Event:
    timestamp: float
    type: EventType
    object_ids: list[int] = field(default_factory=list)
    text: str = ""
```

ACMI 事件记录（如起飞、摧毁、消息等）。

#### AcmiFile

```python
@dataclass
class AcmiFile:
    file_type: str = "text/acmi/tacview"
    file_version: str = "2.2"
    globals: GlobalProperties = field(default_factory=GlobalProperties)
    objects: dict[int, AcmiObject] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)
```

完整 ACMI 录制的根容器。提供全局自定义数据便捷方法：`set_global_custom_data()`, `get_global_custom_data()`, `delete_global_custom_data()`, `get_all_global_custom_data()`。

#### 原始记录类型（用于 iter_records）

| 类型 | 用途 |
|------|------|
| `TimeRecord` | 时间戳标记（`#<seconds>`） |
| `PropertyRecord` | 对象属性更新行 |
| `RemovalRecord` | 对象移除行（`-<hex_id>`） |
| `EventRecord` | 事件记录（从 object ID 0 的 `Event=` 属性解析） |

`Record = TimeRecord | PropertyRecord | RemovalRecord | EventRecord` — 四种原始记录的联合类型。

---

### 4.3 utils — 工具函数

**文件**: [utils.py](file:///c:/Users/bytimes/lxj/projects/acmi-maid/src/acmi_maid/utils.py)

纯函数工具模块，提供 ACMI 格式相关的序列化/反序列化辅助。

| 函数 | 签名 | 说明 |
|------|------|------|
| `parse_transform` | `(value: str) -> Transform` | 解析 `T=` 值字符串为 Transform。支持 3/5/6/9 分量格式，空分量设为 None |
| `format_transform` | `(t: Transform) -> str` | 格式化 Transform 为 `T=` 值字符串。省略尾部 None 分量，内部 None 用空字段表示 |
| `parse_acmi_datetime` | `(value: str) -> datetime` | 解析 ACMI ISO 8601 日期时间字符串（支持毫秒），返回 UTC 时区 datetime |
| `format_acmi_datetime` | `(dt: datetime) -> str` | 格式化 datetime 为 ACMI ISO 8601 字符串（有毫秒时包含，否则省略） |
| `split_escaped` | `(line: str, delimiter: str = ",") -> list[str]` | 按分隔符分割字符串，尊重反斜杠转义（`\,` → `,`） |
| `escape_value` | `(value: str) -> str` | 转义属性值中的逗号为 `\,` |
| `to_snake_case` | `(name: str) -> str` | PascalCase → snake_case 转换 |
| `to_pascal_case` | `(name: str) -> str` | snake_case → PascalCase 转换 |

**Transform 格式说明**：

| 分量数 | 字段 | 示例 |
|--------|------|------|
| 3 | lon\|lat\|alt | `-118.5\|34.0\|3000` |
| 5 | lon\|lat\|alt\|u\|v | `-118.5\|34.0\|3000\|100\|200` |
| 6 | lon\|lat\|alt\|roll\|pitch\|yaw | `-118.5\|34.0\|3000\|10\|5\|270` |
| 9 | lon\|lat\|alt\|roll\|pitch\|yaw\|u\|v\|heading | `-118.5\|34.0\|3000\|10\|5\|270\|100\|200\|90` |

---

### 4.4 parser — 解析器

**文件**: [parser.py](file:///c:/Users/bytimes/lxj/projects/acmi-maid/src/acmi_maid/parser.py)

ACMI 文件解析器，将 ACMI 文本格式转换为结构化 Python 对象。

#### AcmiParseError

```python
class AcmiParseError(Exception):
    line_number: int
```

解析错误异常，包含行号信息用于错误定位。

#### AcmiParser

```python
class AcmiParser:
    @staticmethod
    def parse(source: str | Path | IO[str]) -> AcmiFile: ...

    @staticmethod
    def iter_records(source: str | Path | IO[str]) -> Iterator[Record]: ...
```

| 方法 | 说明 |
|------|------|
| `parse(source)` | 完整解析 ACMI 文件为 `AcmiFile` 对象。支持文件路径、字符串路径和 IO 流输入。自动检测 ZIP 压缩格式并解压。 |
| `iter_records(source)` | 惰性迭代器，逐条产出原始记录（`TimeRecord`/`PropertyRecord`/`RemovalRecord`/`EventRecord`），不构建完整状态，适用于大文件流式处理。 |

**输入源支持**：
- 文件路径（`str` / `Path`）：自动检测 ZIP 压缩格式
- IO 流（`IO[str]`）：直接读取，支持 BOM 头自动去除

#### 内部函数

| 函数 | 说明 |
|------|------|
| `_open_source(source)` | 打开 ACMI 源，返回 `(lines, line_offset)`。处理 ZIP 解压、BOM 去除 |
| `_validate_header(lines, acmi, line_offset)` | 验证 ACMI 文件头（FileType + FileVersion 两行） |
| `_parse_property_line(line, line_num, current_time, acmi)` | 解析属性行（`<hex_id>,<Key=Value>,...`）并更新 AcmiFile |
| `_parse_event(value, timestamp, line_num, acmi)` | 解析 Event= 值并添加到 acmi.events |
| `_set_global_property(globals_, key, value)` | 设置 GlobalProperties 上的属性（自动类型转换） |
| `_set_object_property(props, key, value)` | 设置 ObjectProperties 上的属性（处理索引属性、类型转换） |

#### 属性映射

- `_PROPERTY_MAP`: ACMI PascalCase → ObjectProperties snake_case 字段名（70+ 映射）
- `_REVERSE_PROPERTY_MAP`: 反向映射（snake_case → PascalCase）
- `_GLOBAL_MAP`: ACMI PascalCase → GlobalProperties 字段名（13 个映射）
- `_REVERSE_GLOBAL_MAP`: 反向映射

**属性类型自动转换**：
- `_BOOL_FIELDS`: `on_ground`, `disabled`, `trigger_pressed` → `bool`（`"1"` → `True`）
- `_INT_FIELDS`: `parent`, `next`, `focused_target` → `int`（十六进制）
- `_INT_DECIMAL_FIELDS`: `radar_mode` → `int`（十进制）
- 索引属性：`LockedTarget0`~`LockedTargetN` → `locked_targets` 列表；`FuelWeight0`~`FuelWeight9` → `fuel_weights` 列表

---

### 4.5 writer — 写入器

**文件**: [writer.py](file:///c:/Users/bytimes/lxj/projects/acmi-maid/src/acmi_maid/writer.py)

将 `AcmiFile` 对象序列化为 ACMI 文本格式。

#### AcmiWriter

```python
class AcmiWriter:
    @staticmethod
    def write(acmi: AcmiFile, dest: str | Path | IO[str], compress: bool = False) -> None: ...

    @staticmethod
    def to_string(acmi: AcmiFile) -> str: ...
```

| 方法 | 说明 |
|------|------|
| `write(acmi, dest, compress=False)` | 将 AcmiFile 写入文件路径或 IO 流。`compress=True` 时输出 ZIP 压缩格式。文件输出自动添加 UTF-8 BOM。 |
| `to_string(acmi)` | 将 AcmiFile 序列化为字符串（无 BOM 前缀）。 |

**序列化逻辑**：
1. 写入文件头（`FileType=` + `FileVersion=`）
2. 写入全局属性（object ID 0 的属性行）
3. 收集所有对象时间线条目和事件，按时间戳排序
4. 按时间戳分组输出，每组前缀 `#<timestamp>` 行

#### 内部函数

| 函数 | 说明 |
|------|------|
| `_format_event(event)` | 格式化 Event 为 ACMI 行（`0,Event=Type\|hex_ids\|text`） |
| `_format_timestamp(ts)` | 格式化时间戳（整数值去掉小数点） |
| `_write_compressed(text, path)` | 将文本内容写入 ZIP 压缩 ACMI 文件 |

---

### 4.6 streamer — 流式写入器

**文件**: [streamer.py](file:///c:/Users/bytimes/lxj/projects/acmi-maid/src/acmi_maid/streamer.py)

追加式流式 ACMI 写入器，用于实时遥测场景，无需在内存中缓存完整录制。

#### AcmiStreamer

```python
class AcmiStreamer:
    def __init__(self, dest: str | Path | IO[str], globals: GlobalProperties | None = None, compress: bool = False) -> None: ...
    def write_frame(self, timestamp: float, object_id: int, transform: Transform | None = None, **properties: str) -> None: ...
    def write_event(self, event: Event) -> None: ...
    def remove_object(self, timestamp: float, object_id: int) -> None: ...
    def close(self) -> None: ...
    def __enter__(self) -> AcmiStreamer: ...
    def __exit__(self, *args) -> None: ...
```

| 方法 | 说明 |
|------|------|
| `__init__(dest, globals, compress)` | 初始化写入器，自动写入文件头和全局属性。`compress=True` 时先写临时文件，close 时压缩。 |
| `write_frame(timestamp, object_id, transform, **properties)` | 写入单条对象更新。属性使用 ACMI 原生 PascalCase 名称。自动去重时间戳。 |
| `write_event(event)` | 写入事件记录。 |
| `remove_object(timestamp, object_id)` | 写入对象移除行。 |
| `close()` | 刷新并关闭底层流。压缩模式下自动将临时文件打包为 ZIP。 |

**上下文管理器**：支持 `with` 语句自动关闭。

**线程安全**：非线程安全。

**时间戳去重**：`_write_timestamp()` 方法仅在时间戳变化时写入 `#<timestamp>` 行。

---

## 5. 模块依赖关系

```
                    ┌───────┐
                    │ enums │
                    └───┬───┘
                        │
            ┌───────────┴───────────┐
            │                       │
        ┌───┴────┐            ┌─────┴────┐
        │ models │◄───────────┤  utils   │
        └───┬────┘            └─────┬────┘
            │                       │
    ┌───────┼───────────────────────┤
    │       │                       │
┌───┴───┐ ┌─┴────┐          ┌──────┴──────┐
│parser │ │writer│          │  streamer   │
└───────┘ └──────┘          └─────────────┘
```

**依赖详情**：

| 模块 | 依赖 |
|------|------|
| `enums` | 无（纯枚举定义） |
| `models` | `enums`（EventType） |
| `utils` | `models`（Transform） |
| `parser` | `enums`, `models`, `utils` |
| `writer` | `models`, `parser`（`_REVERSE_GLOBAL_MAP`）, `utils` |
| `streamer` | `models`, `parser`（`_REVERSE_GLOBAL_MAP`）, `utils` |

**注意**：`writer` 和 `streamer` 依赖 `parser` 中的 `_REVERSE_GLOBAL_MAP` 反向映射表，这是一个设计上的耦合点（解析器模块同时承担了属性映射的职责）。

---

## 6. 数据流与核心流程

### 解析流程（Parse）

```
ACMI 文件 (文本/ZIP)
    │
    ▼
_open_source() ─── 自动检测 ZIP / BOM
    │
    ▼
_validate_header() ─── 校验 FileType + FileVersion
    │
    ▼
逐行解析 ─────────────────────────────┐
    │                                  │
    ├─ #<timestamp>  → 更新 current_time
    ├─ -<hex_id>     → 标记对象移除
    ├─ <hex_id>,<props> → _parse_property_line()
    │       │
    │       ├─ T=...      → parse_transform() → Transform
    │       ├─ Event=...  → _parse_event() → Event
    │       ├─ obj_id==0  → _set_global_property()
    │       └─ obj_id!=0  → _set_object_property() + Frame
    │
    ▼
AcmiFile (内存结构)
```

### 序列化流程（Write）

```
AcmiFile (内存结构)
    │
    ▼
写入文件头 (FileType + FileVersion)
    │
    ▼
写入全局属性 (object ID 0)
    │
    ▼
收集所有时间线条目 + 事件 + 移除
    │
    ▼
按 (timestamp, sort_key) 排序
    │
    ▼
按时间戳分组输出:
    ├─ #<timestamp>
    ├─ <hex_id>,T=<transform>,<Key=Value>,...
    ├─ 0,Event=<Type>|<hex_ids>|<text>
    └─ -<hex_id>
    │
    ▼
ACMI 文本 / ZIP 压缩输出
```

### 流式写入流程（Stream）

```
AcmiStreamer(dest, globals)
    │
    ├─ 写入文件头
    ├─ 写入全局属性
    │
    ▼
循环调用:
    ├─ write_frame() ─── 写入对象更新（自动去重时间戳）
    ├─ write_event() ─── 写入事件
    └─ remove_object() ─ 写入对象移除
    │
    ▼
close() / __exit__()
    ├─ flush 流
    └─ compress=True 时打包为 ZIP
```

### 往返一致性（Round-trip）

```
ACMI 文件 → AcmiParser.parse() → AcmiFile → AcmiWriter.to_string() → ACMI 文本 → AcmiParser.parse() → AcmiFile
```

项目保证 **Parse → Write → Parse** 往返一致性，即解析后重新序列化再解析，数据保持等价。

---

## 7. ACMI 文件格式说明

ACMI（Air Combat Maneuvering Instrumentation）是 Tacview 使用的飞行数据录制格式。acmi-maid 支持 2.1 和 2.2 版本。

### 文件结构

```
FileType=text/acmi/tacview          ← 第1行：文件类型
FileVersion=2.2                     ← 第2行：文件版本
0,ReferenceTime=...,DataSource=...  ← 全局属性（object ID 0）
#0                                  ← 时间戳（秒，从参考时间起的偏移量）
3001,T=-118.5|34.0|3000|0|5|270,Name=F-16C,Type=Air+FixedWing  ← 对象属性
#1.0
3001,T=-118.501|34.001|3050||5|270  ← 增量更新（空字段=未变化）
0,Event=TakenOff|3001|Viper 1 airborne  ← 事件
#10.0
-3002                               ← 对象移除
```

### 关键格式规则

| 规则 | 说明 |
|------|------|
| 对象 ID | 十六进制表示（如 `3001` = 0x3001） |
| 全局属性 | object ID 为 `0` |
| 时间戳 | `#` 前缀，从参考时间起的秒数偏移 |
| 增量语义 | 属性值 `None`/空 表示与上一帧相同 |
| 逗号转义 | 属性值中的逗号用 `\,` 转义 |
| 注释 | `//` 开头的行被忽略 |
| BOM | 支持 UTF-8 BOM 头 |
| 压缩 | 支持 ZIP 压缩格式（`.zip.acmi`） |

---

## 8. 自定义数据接口

acmi-maid 通过 `CustomDataMixin` 提供用户自定义数据读写能力，设计原则为：

1. **不影响原有 ACMI 功能**：自定义数据以 `__custom_` 前缀存储在 `extra` 字典中
2. **嵌入 ACMI 原始设计**：利用已有的 `extra` 字典机制，Writer/Parser 自动处理序列化/反序列化
3. **优雅的接口设计**：通过 Mixin 模式提供统一的 CRUD 接口

### API 使用

```python
from acmi_maid import AcmiFile, AcmiObject, Frame, Transform

# 全局自定义数据
acmi = AcmiFile()
acmi.set_global_custom_data("missionId", "M001")
acmi.set_global_custom_data("missionType", "training")
value = acmi.get_global_custom_data("missionId")        # "M001"
all_custom = acmi.get_all_global_custom_data()           # {"missionId": "M001", "missionType": "training"}
acmi.delete_global_custom_data("missionId")

# 对象自定义数据
obj = AcmiObject(id=0x3001)
obj.timeline.append(Frame(timestamp=0.0, properties={"Name": "F-16C"}))
obj.set_custom_data("squadron", "VFA-41")
obj.set_custom_data("tailNumber", "FF-212")
value = obj.get_custom_data("squadron")                  # "VFA-41"
all_custom = obj.get_all_custom_data()                   # {"squadron": "VFA-41", "tailNumber": "FF-212"}
obj.delete_custom_data("squadron")
```

### 存储机制

- 自定义键 `key` 在 `extra` 字典中存储为 `__custom_key`
- `CustomDataMixin` 的 `set_custom`/`get_custom`/`delete_custom`/`get_all_custom` 方法操作带前缀的键
- `AcmiObject` 的自定义数据同时写入 `properties.extra` 和最新 `timeline[-1].properties`
- 序列化时 `extra` 字典中的 `__custom_*` 条目作为普通属性输出，解析时自动还原

---

## 9. 测试体系

### 测试文件

| 文件 | 测试内容 | 测试数量 |
|------|---------|---------|
| `test_enums.py` | 枚举值正确性、str(Enum) 行为 | 6 |
| `test_models.py` | 数据模型默认值、CustomDataMixin CRUD、AcmiObject 自定义数据 | 15 |
| `test_utils.py` | Transform 解析/格式化、日期时间、转义、大小写转换 | 20 |
| `test_parser.py` | 文件头验证、固件解析、错误路径、索引属性、iter_records | 16 |
| `test_writer.py` | 序列化输出、文件/流/压缩输出、往返一致性 | 13 |
| `test_streamer.py` | 流式写入、时间戳去重、事件/移除、压缩、可解析性 | 7 |
| `test_integration.py` | 完整工作流、公共 API 导出、自定义数据往返 | 7 |

### 测试固件

| 文件 | 用途 |
|------|------|
| `minimal.acmi` | 最小化 ACMI 文件（仅全局属性） |
| `basic_mission.acmi` | 完整任务（2个对象、时间线、事件、对象移除） |
| `all_transforms.acmi` | 3/5/6/9 分量 Transform 格式 + 增量更新 |
| `escaped_commas.acmi` | 逗号转义（`\,`）测试 |
| `version21.acmi` | ACMI 2.1 版本兼容性 |
| `with_bom.acmi` | UTF-8 BOM 头处理 |

---

## 10. 项目运行方式

### 环境准备

```bash
# 安装 uv（如未安装）
# Windows:
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 使用 uv 创建虚拟环境并安装项目
uv sync
```

### 运行测试

```bash
# 运行全部测试
uv run pytest

# 运行指定测试文件
uv run pytest tests/test_parser.py

# 运行指定测试函数
uv run pytest tests/test_integration.py::test_full_workflow

# 显示详细输出
uv run pytest -v
```

### 作为库使用

```bash
# 安装到当前环境
uv add acmi-maid

# 或 pip 安装
pip install acmi-maid
```

```python
from acmi_maid import AcmiParser, AcmiWriter, AcmiStreamer, AcmiFile, Transform, GlobalProperties
from datetime import datetime, timezone

# 解析 ACMI 文件
acmi = AcmiParser.parse("recording.acmi")
print(f"对象数量: {len(acmi.objects)}")
print(f"事件数量: {len(acmi.events)}")

# 流式写入
globals_ = GlobalProperties(
    data_source="MySim",
    reference_time=datetime(2025, 1, 15, 8, 0, 0, tzinfo=timezone.utc),
)
with AcmiStreamer("output.acmi", globals=globals_) as s:
    s.write_frame(0.0, 0x3001, Transform(longitude=-118.5, latitude=34.0, altitude=3000.0), Name="F-16C")
    s.write_frame(1.0, 0x3001, Transform(longitude=-118.501, latitude=34.001, altitude=3050.0))

# 完整写入
AcmiWriter.write(acmi, "output.acmi")
AcmiWriter.write(acmi, "output.zip.acmi", compress=True)

# 惰性迭代大文件
for record in AcmiParser.iter_records("large_recording.acmi"):
    # 处理每条记录，不加载完整文件到内存
    pass
```

### 构建发布

```bash
uv build
```

---

## 11. 设计决策与约定

### 编码约定

| 约定 | 说明 |
|------|------|
| 数据类 | 全部使用 `@dataclass`，无 `__init__` 自定义 |
| 可变默认值 | 使用 `field(default_factory=list)` / `field(default_factory=dict)` 避免共享可变状态 |
| 类型注解 | 全面使用 Python 3.10+ 语法（`X \| None`，`dict[str, str]`） |
| 前向引用 | 模块顶部使用 `from __future__ import annotations` |
| 枚举 | `str, Enum` 双重继承，值直接等于对应字符串 |
| 无注释 | 代码中不添加注释（项目约定） |

### 架构决策

| 决策 | 理由 |
|------|------|
| 零外部依赖 | 最大化可移植性，降低安装门槛 |
| dataclass 而非 Pydantic | 无需运行时验证开销，保持轻量 |
| CustomDataMixin 而非子类化 | 组合优于继承，避免类爆炸 |
| `__custom_` 前缀隔离 | 与 ACMI 标准属性完全隔离，无冲突风险 |
| iter_records 惰性迭代 | 支持大文件流式处理，不占用大量内存 |
| 属性映射表集中管理 | `_PROPERTY_MAP` / `_GLOBAL_MAP` 集中在 parser.py，便于维护 |
| writer/streamer 复用 parser 映射 | `_REVERSE_PROPERTY_MAP` / `_REVERSE_GLOBAL_MAP` 确保序列化与解析一致 |

### 已知限制

| 限制 | 说明 |
|------|------|
| 非线程安全 | `AcmiStreamer` 不保证线程安全 |
| 属性映射耦合 | writer/streamer 依赖 parser 模块的反向映射表 |
| 无 ACMI 2.0 支持 | 仅支持 2.1 和 2.2 版本 |
| 无二进制 ACMI 支持 | 仅支持文本格式（text/acmi/tacview） |
