# 证据与产物

> 文档版本：L1-ArchiveBridge-v1

## 1. 报告目录

- 项目级报告：`ProjectState/Reports/YYYY-MM-DD/`
- 插件级报告：`Plugins/AgentBridge/reports/YYYY-MM-DD/`

所有新生成的报告默认按日期分层，不再平铺到根目录。

## 2. Evidence 目录

- 项目级真实截图与验收证据放在 `ProjectState/Evidence/`
- 历史阶段证据副本放在 `Docs/History/reports/AgentBridgeEvidence/`

## 3. Snapshot 目录

- Snapshot 默认写入 `ProjectState/Snapshots/YYYY-MM-DD/`
- Snapshot manifest 至少包含：
  - `baseline_ref`
  - `digest`
  - `source_report`
  - `created_at`

## 4. 归档后沿用规则

- 运行时证据与 snapshot 默认保留在项目内本地目录，不作为源码常规提交物。
- 历史归档只复制“可审计副本”，不搬整份 `ProjectState`。
- 下一阶段开始前，不新增新的 evidence 命名体系，继续复用当前目录规则。
