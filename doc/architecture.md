# 项目架构

## 架构总览

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

## 分层设计

| 层级 | 模块 | 职责 |
|------|------|------|
| **底层** | `enums` | 枚举常量定义（ObjectClass, EventType 等） |
| **底层** | `models` | 数据结构定义（dataclass） |
| **底层** | `utils` | 纯函数工具（Transform 解析/格式化、日期时间、转义） |
| **中层** | `parser` | ACMI 文本 → Python 对象（解析） |
| **中层** | `writer` | Python 对象 → ACMI 文本（序列化） |
| **中层** | `streamer` | 追加式流式 ACMI 写入（实时遥测） |
| **顶层** | `__init__.py` | 统一公共 API 导出 |

## 目录结构

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
│   ├── test_enums.py
│   ├── test_models.py
│   ├── test_utils.py
│   ├── test_parser.py
│   ├── test_writer.py
│   ├── test_streamer.py
│   └── test_integration.py
├── pyproject.toml
├── uv.lock
└── LICENSE
```

## 模块依赖关系

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

| 模块 | 依赖 |
|------|------|
| `enums` | 无（纯枚举定义） |
| `models` | `enums`（EventType） |
| `utils` | `models`（Transform） |
| `parser` | `enums`, `models`, `utils` |
| `writer` | `models`, `parser`（`_REVERSE_GLOBAL_MAP`）, `utils` |
| `streamer` | `models`, `parser`（`_REVERSE_GLOBAL_MAP`）, `utils` |

> **注意**：`writer` 和 `streamer` 依赖 `parser` 中的 `_REVERSE_GLOBAL_MAP` 反向映射表，这是一个设计上的耦合点。

## 数据流

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
