# ACMI Maid

> **Pure-Python ACMI 2.2 Toolset for Tacview Flight Recordings**
>
> 版本: 0.1.0 | 许可证: MIT | Python >= 3.10 | 零外部依赖

## 项目简介

**acmi-maid** 是一个纯 Python 实现的 ACMI（Air Combat Maneuvering Instrumentation）2.1/2.2 格式工具集，用于处理 [Tacview](https://www.tacview.net/) 飞行记录文件。

### 核心能力

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
| 测试框架 | pytest >= 9.0.2 |
| 类型标记 | py.typed (PEP 561) |
| 运行时依赖 | 无（零外部依赖） |

## 快速开始

```bash
# 安装
uv sync

# 运行测试
uv run pytest

# 作为库使用
uv add acmi-maid
```

```python
from acmi_maid import AcmiParser, AcmiWriter, AcmiStreamer, Transform, GlobalProperties
from datetime import datetime, timezone

# 解析 ACMI 文件
acmi = AcmiParser.parse("recording.acmi")
print(f"对象数量: {len(acmi.objects)}")

# 流式写入
globals_ = GlobalProperties(
    data_source="MySim",
    reference_time=datetime(2025, 1, 15, 8, 0, 0, tzinfo=timezone.utc),
)
with AcmiStreamer("output.acmi", globals=globals_) as s:
    s.write_frame(0.0, 0x3001, Transform(longitude=-118.5, latitude=34.0, altitude=3000.0), Name="F-16C")
    s.write_frame(1.0, 0x3001, Transform(longitude=-118.501, latitude=34.001, altitude=3050.0))
```

## 文档导航

| 文档 | 说明 |
|------|------|
| [项目架构](architecture.md) | 整体架构、模块依赖关系、分层设计 |
| [数据模型](models.md) | 所有 dataclass 数据结构详解 |
| [解析器](parser.md) | ACMI 文件解析器 API 与内部实现 |
| [写入器](writer.md) | ACMI 序列化写入器 API |
| [流式写入器](streamer.md) | 实时遥测流式写入 API |
| [枚举类型](enums.md) | ACMI 格式枚举定义 |
| [工具函数](utils.md) | Transform 解析/格式化、日期时间、转义等工具函数 |
| [ACMI 格式说明](acmi-format.md) | ACMI 2.1/2.2 文件格式规范 |
| [自定义数据接口](custom-data.md) | CustomDataMixin 使用指南 |
| [测试体系](testing.md) | 测试文件、固件、运行方式 |
| [设计决策](design-decisions.md) | 编码约定、架构决策、已知限制 |
