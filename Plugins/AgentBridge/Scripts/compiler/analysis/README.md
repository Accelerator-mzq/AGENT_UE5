# Compiler Analysis Module

## 当前状态
📦 **占位目录** - 第一阶段暂未实现

## 职责

Analysis 模块负责 Brownfield 模式的核心分析能力：

### 1. Baseline Understanding
- 构建当前项目模型（Current Project Model）
- 构建当前 Spec 基线（Current Spec Baseline）
- 构建当前能力地图（Current Capability Map）

### 2. Delta Scope Analysis
- 分析增量意图（Delta Intent）
- 检测受影响的域（Affected Domains）
- 检测受影响的 Spec（Affected Specs）
- 检测需要的回归测试（Required Regression Checks）

### 计划文件结构

```
analysis/
├── __init__.py
├── baseline_builder.py
│   ├── project_model_builder.py
│   ├── spec_baseline_builder.py
│   └── capability_map_builder.py
└── delta_scope_analyzer.py
    ├── delta_intent_analyzer.py
    ├── affected_domain_detector.py
    └── regression_detector.py
```

## 第一阶段

第一阶段只支持 Greenfield 模式，不需要 Baseline Understanding 和 Delta Scope Analysis。

当前只实现了最小的 Project State Intake：
- `intake/project_state_intake.py`（获取项目现状快照）

完整的 Analysis 能力将在 Brownfield 实装阶段补充。

## 与 Intake 的区别

- **Intake**：读取原始输入（GDD / 项目状态）
- **Analysis**：深度分析和理解（构建模型 / 检测差量）

Intake 是浅层读取，Analysis 是深层理解。
