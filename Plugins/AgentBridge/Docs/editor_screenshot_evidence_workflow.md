# UE5 Editor 截图取证工作流

> 目标引擎版本：UE5.5.4 | 文档版本：v0.6.0 | 适用范围：AgentBridge 框架在真实 UE5 Editor 中的截图取证

## 1. 文档目的

本文档归档 **“在真实 UE5 Editor 中，为执行结果生成截图证据”** 的可复用方法。

它回答 3 个问题：

- 为什么要截图，以及截图不等于什么
- 在 UE5.5.4 + AgentBridge 当前实现下，哪条截图链路稳定
- 截图生成后应该放到哪里、阶段结束后如何归档

## 2. 分层归属

本能力涉及 3 层信息，必须分开放置：

- **插件层 Canonical 文档**
  位置：`Plugins/AgentBridge/Docs/editor_screenshot_evidence_workflow.md`
  作用：记录“怎么截图”的稳定方法，供后续阶段和其他项目复用
- **项目层当前规则**
  位置：`Docs/Current/07_Evidence_And_Artifacts.md`
  作用：定义“当前阶段截图放哪里、命名规则是什么、何时归档”
- **阶段执行证据**
  位置：`ProjectState/Evidence/PhaseX/`
  作用：保存某次真实执行对应的截图、日志与说明，不承担通用规范职责

结论：

- **方法归插件层**
- **当前阶段放置规则归项目层**
- **本次运行产物归 `ProjectState/Evidence/PhaseX/`**

## 3. 当前稳定做法

### 3.1 推荐链路

在 UE5.5.4 当前工程环境下，推荐截图链路为：

1. 在真实 Editor 会话中完成目标 Actor 的生成或修改
2. 使用 `CameraActor` 固定取证角度
3. 通过 `AutomationBlueprintFunctionLibrary.TakeHighResScreenshot` 出图
4. 将原始截图复制到 `ProjectState/Evidence/PhaseX/screenshots/`
5. 在 `notes/` 中记录截图说明、相机角度、对应 handoff / report

### 3.2 为什么不只用 `CaptureViewportScreenshot`

`CaptureViewportScreenshot` 仍然是有效能力，但它抓取的是**当前激活视口**。在真实 Editor 中，如果“截图视口”和“相机被设置的视口”不同步，就可能出现：

- 画面没有更新到预期角度
- 两张不同角度的截图哈希完全一致
- 自动化链路显示成功，但证据角度不可信

因此，当前更稳的证据路径是：

`CameraActor + TakeHighResScreenshot`

### 3.3 当前脚本入口

当前项目用于截图取证的默认脚本入口是：

- `Scripts/validation/capture_editor_evidence.py`

该脚本已按“高分截图 + 分阶段证据目录 + 元数据说明文件”口径调整，供后续阶段复用。Phase 5 的旧命名脚本保留为历史兼容入口，不再作为当前默认入口。

## 4. 证据目录规则

### 4.1 当前阶段工作目录

截图与证据放在：

- `ProjectState/Evidence/PhaseX/screenshots/`
- `ProjectState/Evidence/PhaseX/logs/`
- `ProjectState/Evidence/PhaseX/notes/`

### 4.2 不应放入的位置

以下目录不应直接存放截图证据：

- `ProjectState/Snapshots/`
  原因：这里保留 baseline / state snapshot，不是截图证据目录
- `Plugins/AgentBridge/Docs/`
  原因：这里只放方法文档，不放运行产物
- `Docs/History/`
  原因：这里是阶段结束后的归档目标，不是当前工作目录

## 5. 命名规则

推荐命名保持与当前项目规则一致：

- 截图：
  `phaseX_<taskid>_<scenario>_<view>.png`
- 说明：
  `phaseX_<taskid>_<scenario>_evidence.md`

推荐至少保留两类视图：

- `overview_oblique`
  3/4 俯视总览，目标 Actor 尽量同时入镜
- `topdown_alignment`
  顶视或近顶视，用于核对布局、相对位置和对齐关系

## 6. 证据说明文件必须包含的信息

每次截图取证都应配套一份 `notes/*.md`，最少记录：

- 生成时间
- RC 启动信息或运行环境说明
- 对应的 Handoff 路径
- 对应的执行报告路径
- 画面中应可见的 Actor 名称
- 原始截图路径
- 最终证据路径
- 截图后端
- CameraActor 路径
- 相机位置和旋转

## 7. 归档规则

阶段结束后：

1. 保留当期 `ProjectState/Evidence/PhaseX/` 作为阶段证据源
2. 按当前项目规则，将其整体归档到  
   `Docs/History/reports/AgentBridgeEvidence/phaseX_evidence_<date>/`
3. 归档后，`Docs/History/Tasks/taskN_phaseX.md` 中只引用证据目录和关键报告，不复制图片内容

## 8. 当前结论

这次新增的“UE5 Editor 内截图取证”能力，后续应这样记忆：

- **它不是一次性排查记录，而是框架能力**
- **通用方法归档在插件层 Docs**
- **阶段放置规则归档在 `Docs/Current/07_Evidence_And_Artifacts.md`**
- **实际图片和说明继续放在 `ProjectState/Evidence/PhaseX/`**

这样下次复用时，Agent 只需要：

1. 读插件层工作流文档
2. 读当前阶段 Evidence 规则
3. 在当前 `PhaseX` 目录写出新的截图证据
