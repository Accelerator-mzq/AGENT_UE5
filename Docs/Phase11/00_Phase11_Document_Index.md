# AGENT_UE5 Phase 11 最终文档包总索引

> 本套文档是 Phase 11 的最终正式交付包。
> 它综合了独立架构方案与 v1.3 文档包的交叉评审结果，形成统一口径。
> 所有后续实施以本套文档为准。

---

## 1. 正式术语表

本套文档统一使用以下术语：

| 术语 | 定义 |
|------|------|
| **Root Skill Contract** | GDD 进入编译主链后的第一份强实体；能力骨架 + 约束容器 + 启用边界 |
| **Domain Skill** | 设计与编译单元；同时承担约束识别、Design Space Discovery、Realization Generation、Cross-domain Coupling Awareness |
| **Gameplay Domain Skill** | 负责玩法、系统、规则相关域的 Domain Skill |
| **Baseline Domain Skill** | 负责壳层、菜单、设置、HUD、结果页等通用基础域的 Domain Skill |
| **Skill Graph** | 从 Root Skill Contract 派生的 Domain Skill 图结构，含依赖/耦合/收敛顺序 |
| **Skill Instance** | Skill Graph 中的具体实例节点 |
| **Constraint Field** | 已确认边界的字段，不可违背 |
| **Variant Field** | 在 Constraint 不变前提下可发生 realization-level 变化的字段 |
| **Clarification Gate** | 对 GDD 缺失/含糊/冲突项的分类处置阶段 |
| **Design Space Discovery** | Domain Skill 发现自身可设计维度的过程 |
| **Realization Candidates** | 每个可设计维度生成的 1~N 个候选实现方向 |
| **Converged Realization Pack** | 经过收敛后最终选中的 realization 组合 |
| **design_decision_log** | Skill Fragment 中记录非平凡实现决策的追溯日志 |
| **naming_resolution_log** | Build IR step 中记录命名解析过程的追溯日志 |
| **Static Spec** | 结构骨架（字段、合约、模板、默认值） |
| **Dynamic Spec Fragment** | 当次项目实际生成的 Spec 片段（结构受 Static Spec 约束，内容由 Agent 填充） |
| **Reviewed Dynamic Spec Tree** | 经过 Cross-Domain Convergence Review 后的统一 Spec 树 |
| **Reviewed Handoff** | Compiler 到 Execution 的正式交付物 |
| **Build IR** | Spec 到执行指令的中间表示 |
| **Run** | 一次完整的管线运行，有独立 run_id，产物独立存储 |
| **Batch** | 一组 Run 的集合，用于比较和 promote |
| **Promote** | 将某次 Run 的结果正式吸收到主项目 |

禁止使用以下旧术语作为正式名词：

- Parent Skill / Child Skill / Child Skill Tree
- design_comprehension / capability_architecture / design_directions
- creative_space_map / constraint_map (C1/C2/C3/C4)
- generation（用 run 替代）

---

## 2. 文档清单与阅读顺序

### 第一组：总架构与主约束
1. `01_Phase11_Unified_Architecture.md` — 最终统一架构
2. `02_Root_Skill_Contract_Standard.md` — Root Skill Contract 标准
3. `03_Universal_Baseline_Standard.md` — 通用基础能力标准
4. `04_Baseline_Realization_Policy.md` — Baseline 发散创造策略

### 第二组：发散创造与收口规则
5. `05_Clarification_Gate_Rules.md` — 缺失项分类处置规则
6. `06_Constraint_vs_Variant_Policy.md` — 约束与变化字段策略
7. `07_Design_Space_Discovery_and_Realization.md` — 设计空间发现与 Realization
8. `08_Skill_Graph_and_Domain_Skill.md` — Skill Graph 与 Domain Skill

### 第三组：工程落地与运行治理
9. `09_Run_Isolation_Compare_Promote.md` — Run 隔离 / 比较 / 吸收
10. `10_Naming_and_Path_Convention.md` — 命名与路径规范
11. `11_Schema_and_Artifact_Reference.md` — Schema 与产物参考

### 第四组：实施与交接
12. `12_Implementation_Taskbook.md` — 实施任务书
13. `13_Claude_Handoff_and_Reading_Order.md` — Claude 交接文档

---

## 3. 文档之间的关系

### 3.1 主链
```
GDD
  -> Root Skill Contract (02) + Universal Baseline Merge (03, 04)
  -> Clarification Gate (05)
  -> Skill Graph Planning (08)
  -> Domain Skill Runtime: Design Space Discovery (07) + Realization (07)
  -> Cross-Domain Convergence Review
  -> Dynamic Spec Fragments
  -> Reviewed Dynamic Spec Tree
  -> Build IR (含 naming_resolution_log, 10)
  -> Reviewed Handoff v3
  -> Execution
```

### 3.2 发散创造发生的位置
- Domain Skill 的 Design Space Discovery (07)
- Realization Candidate Generation (07)
- Cross-Domain Convergence (07)
- Baseline Realization-Eligible 域 (04)

### 3.3 不发生发散创造的位置
- Root Skill Contract 的 Constraint Field 层
- Static Spec 的骨架层
- Build IR / Handoff 的执行边界层
- Baseline Presence-Only 域

---

## 4. 本套文档解决的问题

1. 同一份 GDD 下如何在已确认边界内发生发散创造
2. 发散创造不能依赖死板枚举库，而要由 Agent 发现设计空间
3. Universal Baseline 也要具备 realization-level 的创造能力
4. 同一项目路径多轮测试覆盖问题
5. 多轮 run 之间如何对比"是否存在创造性差异"
6. GDD 已命名和未命名文件如何统一命名、落盘
7. 除 C++ 代码之外的所有新增项目文件如何规范放置与命名
8. 如何把当前 SkillTemplates/ 与 Skills/ 的职责重新分层
9. 旧 Phase 10 产物如何在 Phase 11 过渡期兼容
10. fast_mode 的适用范围与安全边界
