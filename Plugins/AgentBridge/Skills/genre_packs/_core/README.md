# Genre Skill Packs - Core

## 当前状态
📦 **占位目录** - 第一阶段暂未实现

## 职责

Genre Skill Packs Core 提供类型包机制的核心框架。

### 计划包含的能力

1. **Manifest Loader**
   - 加载类型包清单
   - 解析依赖关系
   - 验证完整性

2. **Router Base**
   - 类型路由基类
   - 路由规则引擎
   - 优先级管理

3. **Policy Base**
   - 策略基类
   - Delta Policy 接口
   - Review Policy 接口

4. **Registry**
   - 类型包注册表
   - 动态加载机制
   - 版本管理

## 第一阶段实现

第一阶段只实现了最小的 Mode Routing，位于：
- `Scripts/compiler/routing/mode_router.py`

完整的 Genre Pack 机制将在后续阶段补充。

## 使用方式（未来）

```python
from genre_packs._core import load_genre_pack

# 加载 boardgame 类型包
pack = load_genre_pack("boardgame")

# 激活类型包
pack.activate()

# 使用类型包的 Skill
pack.skills["board_layout"].execute(...)
```
