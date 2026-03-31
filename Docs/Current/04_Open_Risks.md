# 当前风险

> 文档版本：L1-Phase5-v1

## 风险清单

### 活跃风险

1. Brownfield 基线理解如果读取不全，后续 delta 分析会把“已有内容”误当成“待新建内容”。
2. Contract 体系若定义过宽，会放大误修改风险；若定义过窄，又会阻塞合法增量开发。
3. `project_state_intake.py` 从 mock 切到真实 Bridge 后，容易受到当前关卡状态、Editor 会话和 RC 通道稳定性的影响。
4. Brownfield Handoff 需要同时满足 `baseline_context`、`delta_context` 和现有执行兼容性，若设计不慎，会造成“编译能过、执行不可落地”。
5. 真实 UE5 Editor / RC API 虽已在 2026-03-31 完成 Phase 4 闭环，但换机或更换引擎安装后仍可能因为 BuildId 不匹配重新触发启动层问题。

### 已缓解风险

- Phase 4 的 Static Base 已落地，Phase 5 不再需要补 Phase 4 的基础表达地基
- Phase 4 的 generation / review / handoff / simulated E2E 已通过
- `python Scripts/run_greenfield_demo.py bridge_rc_api` 已在 2026-03-31 本机验证通过
- `start_ue_editor_project.ps1` 已修复为优先匹配项目 BuildId

## 已验证假设

1. Greenfield 主链已经具备继续复用的稳定基础。
2. Static Spec Base 可以在现有仓库中被 registry + loader 正常消费。
3. `Scripts/run_greenfield_demo.py` 作为项目层入口适合承接 GDD → Handoff → Runner 的端到端验证。

## 待验证假设

1. 真实项目状态采集能稳定支持 Brownfield 基线构建。
2. 最小 Contract 体系足以约束 Brownfield 样例，不会只停留在占位表达。
3. Delta Scope Analyzer 能输出足够细的差量范围，而不只是笼统标记“需要修改”。
