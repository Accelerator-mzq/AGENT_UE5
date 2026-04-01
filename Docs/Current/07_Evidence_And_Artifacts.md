# Evidence 与 Artifacts 规则

> 文档版本：L1-Phase6-v1

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

### `ProjectState/Evidence/Phase6/`

用途：

- `screenshots/`：UE5 场景截图
- `logs/`：命令输出、抓取日志、证据采集日志
- `notes/`：人工核验说明、截图清单、相机角度说明

命名规则：

- 截图：`phase6_<taskid>_<scenario>_<view>.png`
- 说明：`phase6_<taskid>_<scenario>_evidence.md`

## 报告目录

### `ProjectState/Reports/`

用途：

- 编译报告
- 执行报告
- 验收报告
- smoke 记录

## 阶段归档规则

- 当前阶段工作目录：`ProjectState/Evidence/Phase6/`
- Phase 5 证据已归档到：
  `Docs/History/reports/AgentBridgeEvidence/phase5_evidence_2026-04-01/`
- Phase 6 结束后，将当前期证据目录整期归档到：
  `Docs/History/reports/AgentBridgeEvidence/phase6_evidence_<date>/`
- 归档完成后，再把根目录 `task.md` 归档到 `Docs/History/Tasks/task4_phase6.md`

## 可复用方法入口

- 通用截图取证方法已归档到插件层 Canonical 文档：
  `Plugins/AgentBridge/Docs/editor_screenshot_evidence_workflow.md`
- `Scripts/validation/capture_phase5_evidence.py` 作为 Phase 5 的历史脚本样板继续保留
- 当前项目只在本文件定义“放哪里、怎么归档”，不重复定义完整截图实现细节
