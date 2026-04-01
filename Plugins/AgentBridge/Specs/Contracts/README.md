# Patch / Migration / Regression Contracts

> 状态：Phase 5 已启用最小 Contract 体系

## 目录职责

`Specs/Contracts/` 负责承载 Brownfield 模式下的受控修改边界：

- `SpecPatchContractModel`：约束允许的 patch 范围
- `MigrationContractModel`：表达结构迁移或升级要求
- `RegressionValidationContractModel`：表达 Brownfield 回归验证要求

## 当前目录结构

```text
Contracts/
├── Registry/
│   └── contract_type_registry.yaml
└── Common/
    ├── SpecPatchContractModel/
    │   ├── manifest.yaml
    │   ├── template.yaml
    │   └── schema.json
    ├── MigrationContractModel/
    └── RegressionValidationContractModel/
```

## Phase 5 实施边界

- 当前只真正支持 `append/new-actor` 的最小 Brownfield 执行闭环
- `patch / migration` 在 Phase 5 只做到“可表达、可校验、可阻断”
- Genre 级 Contract 延后到 Phase 6+

## Registry 约定

`Registry/contract_type_registry.yaml` 统一登记：

- `contract_id`
- `contract_kind`
- `target_spec_family`
- `required_fields`
- `template_ref`
- `schema_ref`

Contract registry 由编译期加载，不应由项目层临时改写为一次性规则。
