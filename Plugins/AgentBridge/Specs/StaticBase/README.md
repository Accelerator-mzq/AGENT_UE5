# Static Spec Base

## 当前状态
📦 **占位目录** - 第一阶段暂未实现完整体系

## 职责

Static Spec Base 是框架级能力地基，定义：
- Schema（哪些字段合法）
- Contract（哪些结构可被 Workflow 消费）
- Template（统一表达模板）
- UE5 能力映射（图纸表达到 UE5 原生能力的映射）
- Workflow 边界（哪些 patch / expand / replace 是合法操作）

### 计划目录结构

```
StaticBase/
├── Core/
│   ├── GameplayFrameworkStaticSpec/
│   ├── UIModelStaticSpec/
│   ├── AudioEventStaticSpec/
│   ├── WorldBuildStaticSpec/
│   ├── ConfigStaticSpec/
│   └── ValidationStaticSpec/
├── Genres/
│   └── Boardgame/
│       ├── BoardgameStaticSpec/
│       ├── BoardgameUIStaticSpec/
│       └── BoardgameValidationStaticSpec/
└── Registry/
    └── spec_type_registry.yaml
```

## 与现有仓库的关系

当前 `Schemas/` 中已有的 16 个 JSON Schema 是 Static Spec Base 的雏形。
后续阶段将把 Static Spec Base 体系化为更完整的结构。

## 第一阶段

第一阶段只使用现有的 `Specs/Templates/` 和 `Schemas/`，不做完整 StaticBase 实装。
