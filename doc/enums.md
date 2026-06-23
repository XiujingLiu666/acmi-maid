# 枚举类型

> 源文件: `src/acmi_maid/enums.py`

所有枚举均继承自 `str` 和 `Enum`，可直接与字符串比较，用于 ACMI 格式中的标签值分类。

## ObjectClass — 对象主分类

| 枚举值 | ACMI 标签 | 说明 |
|--------|-----------|------|
| `ObjectClass.AIR` | `Air` | 空中 |
| `ObjectClass.GROUND` | `Ground` | 地面 |
| `ObjectClass.SEA` | `Sea` | 海上 |
| `ObjectClass.WEAPON` | `Weapon` | 武器 |
| `ObjectClass.SENSOR` | `Sensor` | 传感器 |
| `ObjectClass.NAVAID` | `Navaid` | 导航设施 |
| `ObjectClass.MISC` | `Misc` | 其他 |

## ObjectAttribute — 对象属性修饰

| 枚举值 | ACMI 标签 | 说明 |
|--------|-----------|------|
| `ObjectAttribute.STATIC` | `Static` | 静态 |
| `ObjectAttribute.HEAVY` | `Heavy` | 重型 |
| `ObjectAttribute.MEDIUM` | `Medium` | 中型 |
| `ObjectAttribute.LIGHT` | `Light` | 轻型 |
| `ObjectAttribute.MINOR` | `Minor` | 微型 |

## BasicType — 基础类型标签

| 枚举值 | ACMI 标签 | 说明 |
|--------|-----------|------|
| `BasicType.FIXED_WING` | `FixedWing` | 固定翼 |
| `BasicType.ROTORCRAFT` | `Rotorcraft` | 旋翼机 |
| `BasicType.ARMOR` | `Armor` | 装甲 |
| `BasicType.ANTI_AIRCRAFT` | `AntiAircraft` | 防空 |
| `BasicType.VEHICLE` | `Vehicle` | 车辆 |
| `BasicType.WATERCRAFT` | `Watercraft` | 水面舰艇 |
| `BasicType.HUMAN` | `Human` | 人员 |
| `BasicType.BIOLOGIC` | `Biologic` | 生物 |
| `BasicType.MISSILE` | `Missile` | 导弹 |
| `BasicType.ROCKET` | `Rocket` | 火箭 |
| `BasicType.BOMB` | `Bomb` | 炸弹 |
| `BasicType.TORPEDO` | `Torpedo` | 鱼雷 |
| `BasicType.PROJECTILE` | `Projectile` | 弹丸 |
| `BasicType.BEAM` | `Beam` | 光束 |
| `BasicType.DECOY` | `Decoy` | 诱饵 |
| `BasicType.BUILDING` | `Building` | 建筑 |
| `BasicType.BULLSEYE` | `Bullseye` | 标靶 |
| `BasicType.WAYPOINT` | `Waypoint` | 航路点 |

## SpecificType — 具体类型标签

| 枚举值 | ACMI 标签 | 说明 |
|--------|-----------|------|
| `SpecificType.TANK` | `Tank` | 坦克 |
| `SpecificType.WARSHIP` | `Warship` | 军舰 |
| `SpecificType.AIRCRAFT_CARRIER` | `AircraftCarrier` | 航空母舰 |
| `SpecificType.SUBMARINE` | `Submarine` | 潜艇 |
| `SpecificType.INFANTRY` | `Infantry` | 步兵 |
| `SpecificType.PARACHUTIST` | `Parachutist` | 伞兵 |
| `SpecificType.SHELL` | `Shell` | 炮弹 |
| `SpecificType.BULLET` | `Bullet` | 子弹 |
| `SpecificType.GRENADE` | `Grenade` | 手榴弹 |
| `SpecificType.FLARE` | `Flare` | 曳光弹 |
| `SpecificType.CHAFF` | `Chaff` | 箔条 |
| `SpecificType.SMOKE_GRENADE` | `SmokeGrenade` | 烟雾弹 |
| `SpecificType.AERODROME` | `Aerodrome` | 机场 |
| `SpecificType.CONTAINER` | `Container` | 容器 |
| `SpecificType.SHRAPNEL` | `Shrapnel` | 破片 |
| `SpecificType.EXPLOSION` | `Explosion` | 爆炸 |

## EventType — ACMI 事件类型

| 枚举值 | ACMI 标签 | 说明 |
|--------|-----------|------|
| `EventType.MESSAGE` | `Message` | 消息 |
| `EventType.BOOKMARK` | `Bookmark` | 书签 |
| `EventType.DEBUG` | `Debug` | 调试 |
| `EventType.LEFT_AREA` | `LeftArea` | 离开区域 |
| `EventType.DESTROYED` | `Destroyed` | 被摧毁 |
| `EventType.TAKEN_OFF` | `TakenOff` | 起飞 |
| `EventType.LANDED` | `Landed` | 降落 |
| `EventType.TIMEOUT` | `Timeout` | 超时 |

## ObjectColor — 预定义颜色

| 枚举值 | ACMI 标签 |
|--------|-----------|
| `ObjectColor.RED` | `Red` |
| `ObjectColor.ORANGE` | `Orange` |
| `ObjectColor.YELLOW` | `Yellow` |
| `ObjectColor.GREEN` | `Green` |
| `ObjectColor.CYAN` | `Cyan` |
| `ObjectColor.BLUE` | `Blue` |
| `ObjectColor.VIOLET` | `Violet` |

## 设计要点

- 使用 `str, Enum` 双重继承，枚举值可直接与字符串比较
- 对应 ACMI 格式中 `Type=` 属性值的标签部分
- 示例: `Type=Air+FixedWing` 中的 `Air` 对应 `ObjectClass.AIR`，`FixedWing` 对应 `BasicType.FIXED_WING`
