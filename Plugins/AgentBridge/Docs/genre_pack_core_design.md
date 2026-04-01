# Genre Pack Core 设计

> 文档版本：v0.5.0（Phase 6 口径）

## 1. 文档目的

本文档说明 `Skills/genre_packs/_core/` 在 Phase 6 的最小职责边界。

目标不是建立一个过重的插件系统，而是让 Genre Pack 从“只有 manifest 的目录”升级为 Compiler 能真正消费的编译驱动力。

## 2. 当前目录

```text
Skills/genre_packs/_core/
├── __init__.py
├── manifest_loader.py
├── registry.py
├── router_base.py
└── module_loader.py
```

## 3. 四个核心模块

### 3.1 `manifest_loader.py`

职责：

- 读取单个 `pack_manifest.yaml`
- 补齐默认字段
- 做最小结构校验
- 返回 normalized pack bundle

当前要求的关键字段包括：

- `pack_id`
- `version`
- `title`
- `status`
- `router`
- `activation`
- `required_skills`
- `review_extensions`
- `validation_extensions`
- `delta_policy`
- `dependencies`
- `outputs`

### 3.2 `registry.py`

职责：

- 扫描 `Skills/genre_packs/*/pack_manifest.yaml`
- 建立 `pack_id -> pack_bundle` 映射
- 提供按 `game_type / feature_tags` 的激活选择

当前 Phase 6 只要求正确发现并激活 `genre-boardgame`。

### 3.3 `router_base.py`

职责：

- 定义统一的 router 输出结构
- 让具体类型包的激活结果可追踪、可审计

当前统一输出字段：

- `matched`
- `confidence`
- `matched_feature_tags`
- `reasons`
- `activated_pack_ids`

### 3.4 `module_loader.py`

职责：

- 根据 manifest 的短 ID 加载 pack 目录中的真实 Python 模块
- 返回 `required_skills / review_extensions / validation_extensions / delta_policy`

当前加载规则是“目录约定优先”，而不是把 manifest 设计成一门新的 DSL。

## 4. 当前编译接入方式

```text
design_input / project_state
→ _core.registry 发现 pack
→ _core.router_base 返回激活结果
→ _core.module_loader 装载 required skills / review / validation / delta policy
→ generation / review / brownfield analysis
→ Reviewed Handoff
```

## 5. 当前边界

- `_core` 只负责 pack 发现、标准化与装载，不负责执行运行时逻辑
- Base Skill Domains 仍未在 Phase 6 完整实装
- 当前只有 `boardgame` 一个 pack
- 当前不做热加载、远程安装或复杂版本协商
