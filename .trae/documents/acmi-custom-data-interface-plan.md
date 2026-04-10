# ACMI Maid 用户自定义数据接口设计方案

## 1. 需求分析

### 用户需求
为 acmi-maid 添加用户自定义信息写入、读取接口，满足以下要求：
1. 不影响原有的 ACMI 功能
2. 尽量嵌入到 ACMI 的原始设计中，减少改动
3. 优雅的接口设计，高可维护性

### 现有架构分析
- **GlobalProperties** (object ID 0): 包含 `extra: dict[str, str]` 用于存储未知全局属性
- **ObjectProperties** (其他 object): 包含 `extra: dict[str, str]` 用于存储未知对象属性
- **AcmiFile**: 根容器，包含 `globals` 和 `objects`
- **AcmiObject**: 追踪对象，包含 `properties` 和 `timeline`
- **Writer/Streamer**: 已支持自动序列化 `extra` 字典中的数据
- **Parser**: 已支持将未知属性解析到 `extra` 字典中

### 关键发现
现有设计已经通过 `extra` 字段为扩展数据提供了基础设施：
- `extra` 中的数据会被 **Writer** 自动序列化输出
- **Parser** 会将未知属性自动解析到 `extra` 中
- **Streamer** 也支持 `extra` 属性

## 2. 设计方案

### 核心设计：CustomDataMixin

利用 Python 的 mixin 模式，为 `GlobalProperties` 和 `ObjectProperties` 添加用户自定义数据接口。

### API 设计

```python
# 全局自定义数据 (通过 AcmiFile 或 GlobalProperties)
acmi_file.set_global_custom_data("myKey", "myValue")
value = acmi_file.get_global_custom_data("myKey")
acmi_file.delete_global_custom_data("myKey")
all_custom = acmi_file.get_all_global_custom_data()

# 对象自定义数据 (通过 AcmiObject)
obj.set_custom_data("pilotName", "John")
value = obj.get_custom_data("pilotName")
obj.delete_custom_data("pilotName")
all_custom = obj.get_all_custom_data()
```

### 内部实现
- 使用 `CustomDataMixin` 类实现公共逻辑
- 自定义数据以 `"__custom_"` 前缀存储在 `extra` 字典中，避免与 ACMI 标准属性冲突
- 保留 `extra["__custom_"]` 为子字典，结构更清晰

## 3. 实现步骤

### Step 1: 创建 CustomDataMixin 类
- 文件：`src/acmi_maid/models.py`
- 实现 `set_custom`, `get_custom`, `delete_custom`, `get_all_custom` 方法
- 利用 `extra["__custom_"]` 子字典存储

### Step 2: 修改 GlobalProperties 类
- 添加 `CustomDataMixin` 作为基类

### Step 3: 修改 ObjectProperties 类
- 添加 `CustomDataMixin` 作为基类

### Step 4: 在 GlobalProperties 上添加全局便捷方法
- 通过 `acmi.globals.set_custom(...)` 调用（继承自 mixin）

### Step 5: 在 AcmiObject 上添加对象便捷方法
- `AcmiObject.set_custom_data()` → 调用 `self.properties.set_custom()`
- `AcmiObject.get_custom_data()` → 调用 `self.properties.get_custom()`
- `AcmiObject.delete_custom_data()` → 调用 `self.properties.delete_custom()`
- `AcmiObject.get_all_custom_data()` → 调用 `self.properties.get_all_custom()`

### Step 6: 在 AcmiFile 上添加全局便捷类方法
- `AcmiFile.set_global_custom_data()` → 调用 `self.globals.set_custom()`
- `AcmiFile.get_global_custom_data()` → 调用 `self.globals.get_custom()`
- `AcmiFile.delete_global_custom_data()` → 调用 `self.globals.delete_custom()`
- `AcmiFile.get_all_global_custom_data()` → 调用 `self.globals.get_all_custom()`

### Step 7: 更新 `__init__.py`
- 导出 `CustomDataMixin`（如需要）

### Step 8: 编写单元测试
- 文件：`tests/test_models.py`
- 测试 GlobalProperties 的自定义数据接口
- 测试 ObjectProperties 的自定义数据接口
- 测试 AcmiObject 的自定义数据接口
- 测试 AcmiFile 的全局自定义数据接口

### Step 9: 编写集成测试
- 文件：`tests/test_integration.py`
- 测试自定义数据经过 parse → write 循环后数据完整性

## 4. 文件修改清单

| 文件 | 修改类型 |
|------|---------|
| `src/acmi_maid/models.py` | 添加 CustomDataMixin，修改 GlobalProperties, ObjectProperties, AcmiObject, AcmiFile |
| `tests/test_models.py` | 添加自定义数据相关测试 |
| `tests/test_integration.py` | 添加 parse-write 循环测试 |

## 5. 命名空间隔离

使用 `"__custom_"` 前缀存储自定义数据：
- 存储位置：`extra["__custom_"][key] = value`
- 优点：完全隔离，不与任何 ACMI 标准属性冲突
- ACMI 标准属性名称不含双下划线前缀

## 6. 兼容性保证

1. **向后兼容**：`extra` 字典的处理逻辑不变
2. **无损序列化**：Writer/Streamer 已经支持 `extra` 字典的序列化
3. **增量修改**：不修改已有的解析逻辑，新增接口独立运作
