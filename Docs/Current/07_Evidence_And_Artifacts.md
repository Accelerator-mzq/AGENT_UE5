# Evidence 与 Artifacts 规则

> 文档版本：L1-Phase7Prep-v2

## 目录分责

### `ProjectState/Snapshots/`

用途：

- baseline snapshot
- state snapshot
- Brownfield 分析链可复用的项目状态固化产物

不应存放：

- UE5 场景截图
- 当前阶段验收说明
- 临时人工备注

### `ProjectState/Reports/`

用途：

- 编译报告
- 执行报告
- 验收报告
- smoke 记录
- 阶段归档记录

当前规则：

- 当天新生成的报告默认写入 `ProjectState/Reports/YYYY-MM-DD/`
- 如需引用具体报告，应优先链接到日期子目录中的实际文件

### `Plugins/AgentBridge/reports/`

用途：

- 系统测试汇总报告
- 插件层结构化 JSON 报告

当前规则：

- 当天新生成的报告默认写入 `Plugins/AgentBridge/reports/YYYY-MM-DD/`
- 不再直接平铺写入 `Plugins/AgentBridge/reports/` 根目录

## 历史证据归档

### `Phase 5`

- 历史证据归档路径：
  `Docs/History/reports/AgentBridgeEvidence/phase5_evidence_2026-04-01/`

### `Phase 6`

- 项目内工作副本：
  `ProjectState/Evidence/Phase6/`
- 历史归档副本：
  `Docs/History/reports/AgentBridgeEvidence/phase6_evidence_2026-04-02/`

当前默认以历史归档副本作为正式归档引用；  
项目内工作副本继续保留，便于本地复查与后续回归。

## 当前阶段规则

- 当前处于准备期，不新增新的阶段证据目录
- 如下一阶段需要新的证据目录，再随阶段任务一并定义
- 通用截图取证方法仍参考：
  [editor_screenshot_evidence_workflow.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Docs/editor_screenshot_evidence_workflow.md)
