# 流式写入器 (Streamer)

> 源文件: `src/acmi_maid/streamer.py`

追加式流式 ACMI 写入器，用于实时遥测场景，无需在内存中缓存完整录制。

## AcmiStreamer

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

### 构造函数

| 参数 | 类型 | 说明 |
|------|------|------|
| `dest` | `str \| Path \| IO[str]` | 输出目标 |
| `globals` | `GlobalProperties \| None` | 全局属性（可选） |
| `compress` | `bool` | 是否压缩输出（默认 `False`） |

**行为**：
- 自动写入文件头（`FileType=` + `FileVersion=`）
- 自动写入全局属性
- `compress=True` 时先写临时文件，`close()` 时压缩为 ZIP
- 文件输出自动添加 UTF-8 BOM

### write_frame(timestamp, object_id, transform, **properties)

写入单条对象更新。

| 参数 | 类型 | 说明 |
|------|------|------|
| `timestamp` | `float` | 时间戳（秒） |
| `object_id` | `int` | 对象 ID（十六进制值） |
| `transform` | `Transform \| None` | 位置/姿态（可选） |
| `**properties` | `str` | 属性键值对，使用 **ACMI 原生 PascalCase** 名称 |

**特性**：
- 自动去重时间戳（仅在时间戳变化时写入 `#<timestamp>` 行）

### write_event(event)

写入事件记录。

### remove_object(timestamp, object_id)

写入对象移除行。

### close()

刷新并关闭底层流。压缩模式下自动将临时文件打包为 ZIP。

## 上下文管理器

支持 `with` 语句自动关闭：

```python
with AcmiStreamer("output.acmi", globals=globals_) as s:
    s.write_frame(0.0, 0x3001, Name="F-16C")
```

## 线程安全

**非线程安全**。如需多线程使用，请自行加锁。

## 使用示例

```python
from acmi_maid import AcmiStreamer, Transform, Event, GlobalProperties, EventType
from datetime import datetime, timezone

# 基本流式写入
globals_ = GlobalProperties(
    data_source="MySim",
    reference_time=datetime(2025, 1, 15, 8, 0, 0, tzinfo=timezone.utc),
)

with AcmiStreamer("output.acmi", globals=globals_) as s:
    # 创建对象
    s.write_frame(0.0, 0x3001,
        Transform(longitude=-118.5, latitude=34.0, altitude=3000.0),
        Name="F-16C", Type="Air+FixedWing", Coalition="Red"
    )

    # 更新位置
    s.write_frame(1.0, 0x3001,
        Transform(longitude=-118.501, latitude=34.001, altitude=3050.0)
    )

    # 写入事件
    s.write_event(Event(
        timestamp=2.0,
        type=EventType.TAKEN_OFF,
        object_ids=[0x3001],
        text="Viper 1 airborne"
    ))

    # 移除对象
    s.remove_object(100.0, 0x3001)

# 压缩输出
with AcmiStreamer("output.zip.acmi", globals=globals_, compress=True) as s:
    s.write_frame(0.0, 0x3001, Name="F-16C")
```
