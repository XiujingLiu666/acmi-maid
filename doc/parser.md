# 解析器 (Parser)

> 源文件: `src/acmi_maid/parser.py`

ACMI 文件解析器，将 ACMI 文本格式转换为结构化 Python 对象。

## AcmiParseError

解析错误异常，包含行号信息用于错误定位。

```python
class AcmiParseError(Exception):
    line_number: int
```

## AcmiParser

```python
class AcmiParser:
    @staticmethod
    def parse(source: str | Path | IO[str]) -> AcmiFile: ...

    @staticmethod
    def iter_records(source: str | Path | IO[str]) -> Iterator[Record]: ...
```

### parse(source)

完整解析 ACMI 文件为 `AcmiFile` 对象。

| 参数 | 类型 | 说明 |
|------|------|------|
| `source` | `str \| Path \| IO[str]` | 文件路径、字符串路径或 IO 流 |

**输入源支持**：
- 文件路径（`str` / `Path`）：自动检测 ZIP 压缩格式
- IO 流（`IO[str]`）：直接读取，支持 BOM 头自动去除

**返回**: `AcmiFile`

**异常**: `AcmiParseError`（文件格式错误时抛出）

### iter_records(source)

惰性迭代器，逐条产出原始记录，不构建完整状态，适用于大文件流式处理。

**产出类型**: `TimeRecord | PropertyRecord | RemovalRecord | EventRecord`

## 内部函数

| 函数 | 说明 |
|------|------|
| `_open_source(source)` | 打开 ACMI 源，返回 `(lines, line_offset)`。处理 ZIP 解压、BOM 去除 |
| `_validate_header(lines, acmi, line_offset)` | 验证 ACMI 文件头（FileType + FileVersion 两行） |
| `_parse_property_line(line, line_num, current_time, acmi)` | 解析属性行并更新 AcmiFile |
| `_parse_event(value, timestamp, line_num, acmi)` | 解析 Event= 值并添加到 acmi.events |
| `_set_global_property(globals_, key, value)` | 设置 GlobalProperties 上的属性（自动类型转换） |
| `_set_object_property(props, key, value)` | 设置 ObjectProperties 上的属性（处理索引属性、类型转换） |

## 属性映射

### _PROPERTY_MAP

ACMI PascalCase → ObjectProperties snake_case 字段名（70+ 映射）。

示例:
```python
"Name" -> "name"
"Type" -> "type"
"IAS" -> "ias"
"OnGround" -> "on_ground"
"LockedTarget0" -> 索引属性 -> locked_targets[0]
"FuelWeight0" -> 索引属性 -> fuel_weights[0]
```

### _GLOBAL_MAP

ACMI PascalCase → GlobalProperties 字段名（13 个映射）。

```python
"DataSource" -> "data_source"
"ReferenceTime" -> "reference_time"
"ReferenceLongitude" -> "reference_longitude"
# ...
```

### _REVERSE_PROPERTY_MAP / _REVERSE_GLOBAL_MAP

反向映射（snake_case → PascalCase），供 writer 和 streamer 使用。

## 属性类型自动转换

| 类别 | 字段 | 转换规则 |
|------|------|---------|
| 布尔 | `on_ground`, `disabled`, `trigger_pressed` | `"1"` → `True`, 其他 → `False` |
| 整数（十六进制） | `parent`, `next`, `focused_target` | `int(value, 16)` |
| 整数（十进制） | `radar_mode` | `int(value)` |
| 索引属性 | `LockedTarget0`~`LockedTargetN` | → `locked_targets` 列表 |
| 索引属性 | `FuelWeight0`~`FuelWeight9` | → `fuel_weights` 列表 |
| 浮点 | 其余数值字段 | `float(value)` |
| 字符串 | 身份标识字段 | 直接赋值 |

## 使用示例

```python
from acmi_maid import AcmiParser

# 解析文件
acmi = AcmiParser.parse("recording.acmi")

# 访问全局属性
print(acmi.globals.reference_time)
print(acmi.globals.data_source)

# 遍历对象
for obj_id, obj in acmi.objects.items():
    print(f"对象 {obj_id:#x}: {obj.properties.name}")

# 遍历事件
for event in acmi.events:
    print(f"[{event.timestamp}s] {event.type.value}: {event.text}")

# 惰性迭代大文件
for record in AcmiParser.iter_records("large_recording.acmi"):
    match record:
        case TimeRecord(timestamp=ts):
            print(f"时间戳: {ts}")
        case PropertyRecord(object_id=oid, properties=props):
            print(f"对象 {oid:#x} 属性更新")
        case RemovalRecord(object_id=oid):
            print(f"对象 {oid:#x} 已移除")
        case EventRecord(event_type=et):
            print(f"事件: {et.value}")
```
