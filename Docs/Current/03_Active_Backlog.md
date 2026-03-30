# 待办与卡点

> 文档版本：L1-Phase3-v1

## 已知卡点

- Bridge 真实调用联调需要 UE5 Editor 运行 + RC API 端口开放
- project_state_intake.py 当前返回模拟数据，需要桥接到真实查询接口
- Handoff 审批当前是手工移动文件，后续需要自动化

## 待办事项

### P0（必须先做）
- 将 input/ 目录下的交付件部署到正式位置（项目层 + 插件层）
- 验证 Schema 校验通过
- 验证 simulated 模式端到端跑通
- 验证现有 validate_examples.py 不受影响

### P1（接着做）
- 将 bridge_mode 从 simulated 切换到 bridge_rc_api
- 在 UE5 中验证 Actor 生成
- 验证现有 Automation Test 不受影响

### P2（只做占位）
- Brownfield 能力占位（analysis/ 目录 README）
- Patch / Migration Contract 占位（Specs/Contracts/ 目录 README）
- 完整 Orchestrator 能力占位
