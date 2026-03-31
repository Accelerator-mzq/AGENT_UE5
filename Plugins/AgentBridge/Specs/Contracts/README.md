# Patch / Migration / Regression Contracts

## 当前状态
📦 **占位目录** - 第一阶段暂未实现

## 职责

Contracts 定义 Brownfield 模式下的核心受控边界：
- Patch Contract（如何安全地修改现有 Spec）
- Migration Contract（如何迁移旧版本 Spec）
- Regression Contract（如何验证修改不破坏现有功能）

### 计划目录结构

```
Contracts/
├── Common/
│   ├── SpecPatchContractModel/
│   │   ├── schema.json
│   │   ├── template.yaml
│   │   └── examples/
│   ├── MigrationContractModel/
│   └── RegressionValidationContractModel/
└── Genres/
    └── Boardgame/
        ├── DecisionUIPatchContract/
        ├── TurnFlowPatchContract/
        └── BoardgameRegressionContractModel/
```

## 为什么必须在插件层

这些 Contract 是框架级约束，是 Skill / Planner / Workflow / Validator 的共同语言。
如果留给项目层临时决定，Brownfield 会退化成"项目自己 patch，插件只执行"。

## 第一阶段

第一阶段只支持 Greenfield 模式，不需要 Patch / Migration Contract。
这些能力将在 Brownfield 实装阶段补充。

## 最小示例（未来）

```yaml
# SpecPatchContractModel 示例
patch_type: "add_actor"
target_spec: "scene_spec"
operation:
  type: "add"
  path: "/actors/-"
  value:
    actor_name: "NewActor"
    actor_class: "/Script/Engine.StaticMeshActor"
    transform: {...}
validation:
  - no_name_conflict
  - no_position_overlap
```
