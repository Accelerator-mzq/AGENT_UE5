# ADR-001：文档治理结构

> 日期：2026-03-28 | 状态：accepted

## 背景

Phase 1 结束后，task.md（3852 行）同时承载任务指引、执行记录、架构知识三重职责。状态信息散落在 AGENTS.md、README.md、task.md、Roadmap/ 四处。阶段切换时没有标准流程，AI 无法区分当前依据与历史记录。

## 选项

1. 按版本号建立 docs/v1、docs/v2、docs/v3 — 拒绝，因为文档不是整体换代
2. 所有文档持续叠加修改 — 拒绝，因为历史决策会被覆盖
3. 按职责分层（Current / Canonical / History / Decisions / Proposals） — 采纳

## 决策

采用五层文档治理结构：
- L0 入口层（AGENTS.md / README.md / task.md）
- L1 当前生效层（Docs/Current/）
- L2 插件 Canonical 层（Plugins/AgentBridge/）
- L3 历史归档层（Docs/History/）
- L4 决策记录 + L5 草案（Docs/Decisions/ + Docs/Proposals/）

task.md 定位为一次性消耗品，每期清除重写，不归档。

## 影响

- AGENTS.md 不再承载进度状态，只承载规则
- AI 默认只读 L0 + L1 + L2，History 按需读取
- 每次阶段切换执行"文档结算"流程
