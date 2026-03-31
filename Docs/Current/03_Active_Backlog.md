# 待办与卡点

> 文档版本：L1-Phase3-v2（Phase 3 结束更新）

## 已知卡点

- ~~Bridge 真实调用联调需要 UE5 Editor 运行 + RC API 端口开放~~ → Phase 3 遗留，Phase 4 前置解决
- ~~project_state_intake.py 当前返回模拟数据~~ → Phase 5 桥接真实查询接口
- Handoff 审批当前是手工移动文件，后续需要自动化（Phase 7）

## 已完成事项（Phase 3）

### P0（已完成 ✅）
- ✅ 将 input/ 目录下的交付件部署到正式位置（项目层 + 插件层）
- ✅ 验证 Schema 校验通过（12/12）
- ✅ 验证 simulated 模式端到端跑通（run_greenfield_demo.py）
- ✅ 验证现有 validate_examples.py 不受影响

### P1（部分完成）
- ⬜ 将 bridge_mode 从 simulated 切换到 bridge_rc_api（Phase 3 遗留）
- ⬜ 在 UE5 中验证 Actor 生成（Phase 3 遗留）
- ✅ 验证现有 Automation Test 不受影响

### P2（已完成 ✅）
- ✅ Brownfield 能力占位（analysis/ 目录 README）
- ✅ Patch / Migration Contract 占位（Specs/Contracts/ 目录 README）
- ✅ 完整 Orchestrator 能力占位

## Phase 4 前瞻待办

### P0
- 实装 Prototype 最小 Static Spec Base（Layer A：6 个通用基础 + Layer B：4 个 boardgame 类型）
- 实装 Spec Generation Dispatcher（从 design_input + Static Base 生成 Dynamic Spec Tree）
- 实装最小 Cross-Spec Review（引用完整性 + 字段类型检查）

### P1
- 增强 Handoff Builder（从自动生成的 Spec Tree 组装 Handoff）
- 增强 Design Input Intake（从 GDD 提取场景需求，不只是 game_type）
- 端到端验证：GDD → 自动生成 Spec → Handoff → 执行 → UE5 中看到结果

### P1（Phase 3 遗留前置）
- Bridge 真实调用联调（bridge_rc_api 模式）
- UE5 中验证 Actor 生成
