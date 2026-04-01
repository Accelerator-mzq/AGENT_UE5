# 待办与卡点

> 文档版本：L1-Phase6-v2

## 当前 P0 待办

- 清理本轮 Phase 6 本地产生的临时 handoff / report / runtime config 产物
- 继续观察真实 UE5 runtime smoke 的稳定性，确认多次重复执行无漂移
- 为 runtime actor 增加更稳的人工点击验证说明

## 当前 P1 待办

- 为 runtime actor 增加更丰富的 UI 反馈
- 为 Brownfield runtime / turn/ui patch 增加更细的 contract 与 reviewer 规则
- 视后续进展决定是否扩展更通用的 boardgame runtime 骨架

## 当前门禁项

- Python / simulated / UBT 编译 已通过
- 真实 UE5 `bridge_rc_api` playable runtime smoke 已通过
- Phase 6 截图证据已落盘到 `ProjectState/Evidence/Phase6/`
- 当前已无 Phase 6 P0 阻塞门禁

## 当前策略

- Phase 6 测试用例先写在根目录 `task.md`
- `SystemTestCases.md` 不提前追加 Phase 6 用例正文，待本阶段归档时统一补录
- `ProjectState/Snapshots/` 与 `ProjectState/Evidence/Phase6/` 严格分责
