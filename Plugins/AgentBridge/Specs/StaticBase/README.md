# Static Spec Base

## 当前状态

Phase 4 已将本目录从“纯占位”升级为“最小可加载 Static Base 体系”。

当前实现包含：

- `Registry/spec_type_registry.yaml`：统一入口
- `Core/`：6 个通用静态基座
- `Genres/Boardgame/`：4 个 boardgame 类型静态基座

## 职责

Static Spec Base 是框架级能力地基，定义：

- Schema：哪些字段合法
- Contract：哪些结构可被 Workflow 消费
- Template：统一表达模板
- UE5 能力映射：图纸表达到 UE5 原生能力的映射
- Workflow 边界：哪些 patch / expand / replace 是合法操作

## 目录结构

```
StaticBase/
├── Registry/
│   └── spec_type_registry.yaml
├── Core/
│   ├── GameplayFrameworkStaticSpec/
│   ├── UIModelStaticSpec/
│   ├── AudioEventStaticSpec/
│   ├── WorldBuildStaticSpec/
│   ├── ConfigStaticSpec/
│   └── ValidationStaticSpec/
└── Genres/
    └── Boardgame/
        ├── BoardgameStaticSpec/
        ├── BoardgameUIStaticSpec/
        ├── BoardgameAudioStaticSpec/
        └── BoardgameValidationStaticSpec/
```

## Phase 4 的使用方式

Phase 4 中，Compiler 通过 `generation/static_base_loader.py` 读取 registry，再按 registry 中的条目发现静态基座。

当前只让以下基座直接进入主生成链：

- `WorldBuildStaticSpec`
- `ValidationStaticSpec`
- `BoardgameStaticSpec`
- `BoardgameValidationStaticSpec`

其余基座在 Phase 4 先提供真实 `manifest/template/schema`，作为类型边界和后续阶段的地基。

## 与现有仓库的关系

- `Schemas/` 中已有的稳定 JSON Schema 仍是返回值契约
- `Specs/StaticBase/` 负责 Phase 4 的“编译前端地基”
- `Skills/` 仍保留最终架构主轴，但完整 Skill 机制延后到 Phase 6 / Phase 7
