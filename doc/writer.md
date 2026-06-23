# 写入器 (Writer)

> 源文件: `src/acmi_maid/writer.py`

将 `AcmiFile` 对象序列化为 ACMI 文本格式。

## AcmiWriter

```python
class AcmiWriter:
    @staticmethod
    def write(acmi: AcmiFile, dest: str | Path | IO[str], compress: bool = False) -> None: ...

    @staticmethod
    def to_string(acmi: AcmiFile) -> str: ...
```

### write(acmi, dest, compress=False)

将 AcmiFile 写入文件路径或 IO 流。

| 参数 | 类型 | 说明 |
|------|------|------|
| `acmi` | `AcmiFile` | 要序列化的 ACMI 数据 |
| `dest` | `str \| Path \| IO[str]` | 输出目标（文件路径或 IO 流） |
| `compress` | `bool` | 是否输出 ZIP 压缩格式（默认 `False`） |

**行为**：
- 文件输出自动添加 UTF-8 BOM
- `compress=True` 时输出 ZIP 压缩格式（`.zip.acmi`）
- IO 流输出不含 BOM

### to_string(acmi)

将 AcmiFile 序列化为字符串（无 BOM 前缀）。

**返回**: `str`

## 序列化逻辑

1. 写入文件头（`FileType=` + `FileVersion=`）
2. 写入全局属性（object ID 0 的属性行）
3. 收集所有对象时间线条目和事件
4. 按时间戳排序（sort_key: 全局属性 → 对象帧 → 事件 → 移除）
5. 按时间戳分组输出，每组前缀 `#<timestamp>` 行

## 内部函数

| 函数 | 说明 |
|------|------|
| `_format_event(event)` | 格式化 Event 为 ACMI 行（`0,Event=Type\|hex_ids\|text`） |
| `_format_timestamp(ts)` | 格式化时间戳（整数值去掉小数点） |
| `_write_compressed(text, path)` | 将文本内容写入 ZIP 压缩 ACMI 文件 |

## 使用示例

```python
from acmi_maid import AcmiParser, AcmiWriter

# 解析 → 修改 → 写入
acmi = AcmiParser.parse("input.acmi")
acmi.globals.title = "Modified Recording"
AcmiWriter.write(acmi, "output.acmi")

# 压缩输出
AcmiWriter.write(acmi, "output.zip.acmi", compress=True)

# 写入 IO 流
with open("output.acmi", "w", encoding="utf-8") as f:
    AcmiWriter.write(acmi, f)

# 序列化为字符串
text = AcmiWriter.to_string(acmi)
print(text)
```
