# 工具函数

> 源文件: `src/acmi_maid/utils.py`

纯函数工具模块，提供 ACMI 格式相关的序列化/反序列化辅助。

## 函数列表

### Transform 解析/格式化

#### parse_transform(value: str) -> Transform

解析 `T=` 值字符串为 Transform。支持 3/5/6/9 分量格式，空分量设为 None。

```python
from acmi_maid.utils import parse_transform

# 3 分量: lon|lat|alt
t = parse_transform("-118.5|34.0|3000")

# 6 分量: lon|lat|alt|roll|pitch|yaw
t = parse_transform("-118.5|34.0|3000|10|5|270")

# 9 分量: lon|lat|alt|roll|pitch|yaw|u|v|heading
t = parse_transform("-118.5|34.0|3000|10|5|270|100|200|90")

# 增量更新（空字段 = 未变化）
t = parse_transform("-118.501|34.001|3050||5|270")  # roll=None
```

#### format_transform(t: Transform) -> str

格式化 Transform 为 `T=` 值字符串。省略尾部 None 分量，内部 None 用空字段表示。

```python
from acmi_maid.utils import format_transform
from acmi_maid import Transform

t = Transform(longitude=-118.5, latitude=34.0, altitude=3000.0)
format_transform(t)  # "-118.5|34.0|3000"
```

### Transform 格式说明

| 分量数 | 字段 | 示例 |
|--------|------|------|
| 3 | lon\|lat\|alt | `-118.5\|34.0\|3000` |
| 5 | lon\|lat\|alt\|u\|v | `-118.5\|34.0\|3000\|100\|200` |
| 6 | lon\|lat\|alt\|roll\|pitch\|yaw | `-118.5\|34.0\|3000\|10\|5\|270` |
| 9 | lon\|lat\|alt\|roll\|pitch\|yaw\|u\|v\|heading | `-118.5\|34.0\|3000\|10\|5\|270\|100\|200\|90` |

### 日期时间

#### parse_acmi_datetime(value: str) -> datetime

解析 ACMI ISO 8601 日期时间字符串（支持毫秒），返回 UTC 时区 datetime。

```python
parse_acmi_datetime("2025-01-15T08:00:00Z")
parse_acmi_datetime("2025-01-15T08:00:00.123Z")
```

#### format_acmi_datetime(dt: datetime) -> str

格式化 datetime 为 ACMI ISO 8601 字符串（有毫秒时包含，否则省略）。

```python
format_acmi_datetime(datetime(2025, 1, 15, 8, 0, 0, tzinfo=timezone.utc))
# "2025-01-15T08:00:00Z"
```

### 转义

#### split_escaped(line: str, delimiter: str = ",") -> list[str]

按分隔符分割字符串，尊重反斜杠转义（`\,` → `,`）。

```python
split_escaped("Name=F-16C,Type=Air+FixedWing,Notes=Hello\\, World")
# ["Name=F-16C", "Type=Air+FixedWing", "Notes=Hello, World"]
```

#### escape_value(value: str) -> str

转义属性值中的逗号为 `\,`。

```python
escape_value("Hello, World")  # "Hello\\, World"
```

### 大小写转换

#### to_snake_case(name: str) -> str

PascalCase → snake_case 转换。

```python
to_snake_case("LockedTarget")  # "locked_target"
to_snake_case("IAS")           # "ias"
```

#### to_pascal_case(name: str) -> str

snake_case → PascalCase 转换。

```python
to_pascal_case("locked_target")  # "LockedTarget"
to_pascal_case("ias")            # "Ias"
```
