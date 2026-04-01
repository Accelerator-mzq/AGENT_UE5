# AgentBridge 系统测试用例总表

> 来源：`Docs/History/Phase1_MVP/task.md` + `Docs/History/Tasks/task1_phase3.md` + `Docs/History/Tasks/task2_phase4.md` + `Docs/History/Tasks/task3_phase5.md` + `Docs/History/Tasks/task4_phase6.md` 中的验收标准与验证步骤  
> 最后更新：2026-04-02
> 维护者：msc

---

## 目录

- [1. 测试分类说明](#1-测试分类说明)
- [2. Schema 验证（SV）](#2-schema-验证sv)
- [3. 编译与加载（BL）](#3-编译与加载bl)
- [3.1 通用执行约束（适用于 Q/W/CL/UI）](#31-通用执行约束适用于-qwclui)
- [4. L1 查询接口（Q）](#4-l1-查询接口q)
- [5. L1 写接口（W）](#5-l1-写接口w)
- [6. L2 闭环验证（CL）](#6-l2-闭环验证cl)
- [7. L3 UI 工具（UI）](#7-l3-ui-工具ui)
- [8. Commandlet 无头执行（CMD）](#8-commandlet-无头执行cmd)
- [9. Python 客户端（PY）](#9-python-客户端py)
- [10. Orchestrator 编排（ORC）](#10-orchestrator-编排orc)
- [11. Compiler Plane（CP）](#11-compiler-planecp)
- [12. Skills & Specs（SS）](#12-skills--specsss)
- [13. Gauntlet CI/CD（GA）](#13-gauntlet-cicdga)
- [14. 端到端集成（E2E）](#14-端到端集成e2e)
- [附录 A：UE5 Automation Test ID 速查表](#附录-aue5-automation-test-id-速查表)
- [附录 B：统计摘要](#附录-b统计摘要)
- [附录 C：自动化工具链](#附录-c自动化工具链)

---

## 1. 测试分类说明

| 前缀 | 分类 | 环境要求 | 自动化方式 |
|------|------|----------|-----------|
| SV | Schema 验证 | Python | `python validate_examples.py --strict` / pytest |
| BL | 编译与加载 | UE5 + VS2022 | `Build.bat` + `Scripts/validation/start_ue_editor_project.ps1` + HTTP 探测 |
| Q | L1 查询接口 | UE5 Editor + RC API | `-run=AgentBridge -RunTests=Project.AgentBridge.L1.Query` |
| W | L1 写接口 | UE5 Editor + RC API | `-run=AgentBridge -RunTests=Project.AgentBridge.L1.Write` |
| CL | L2 闭环验证 | UE5 Editor | `-run=AgentBridge -RunTests=Project.AgentBridge.L2` |
| UI | L3 UI 工具 | UE5 Editor + Automation Driver | `-run=AgentBridge -RunTests=Project.AgentBridge.L1.UITool` + `Project.AgentBridge.L2.UITool` |
| CMD | Commandlet | UE5 命令行（无头） | `UnrealEditor-Cmd.exe -run=AgentBridge` + `Scripts/validation/start_ue_editor_cmd_project.ps1` |
| PY | Python 客户端 | Python | pytest / `ast.parse` / Mock 模式调用 |
| ORC | Orchestrator | Python + UE5 | pytest / `orchestrator.py --channel mock` |
| CP | Compiler Plane | Python | pytest / `compiler_main.py` |
| SS | Skills & Specs | Python | pytest / `yaml.safe_load` |
| GA | Gauntlet CI/CD | UE5 + UAT | `RunUAT.bat RunUnreal -test=SmokeTests/AllTests` |
| E2E | 端到端集成 | 全栈 | 多步流水线（Schema→Cmd→Gauntlet→三通道脚本） |

> 全部 206 条用例均已登记到当前测试总表。证据目录分层为：`ProjectState/Reports/`（当期执行）+ `Docs/History/reports/AgentBridgeEvidence/`（历史归档）。

---

## 2. Schema 验证（SV）

> 来源：TASK 02, TASK 18, task1.md TASK 03

| 编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 自动化命令 |
|------|---------|---------|---------|---------|-----------|
| SV-01 | 全部 example 通过 Schema 校验 | 文件就位 | `python validate_examples.py --strict` | exit code 0, Passed=8(或10) | `python Scripts/validation/validate_examples.py --strict` |
| SV-02 | 全部 JSON 文件语法合法 | 文件就位 | 遍历 Schemas/**/*.json 做 json.load | 全部 OK，无 FAIL | `pytest Tests/scripts/test_schema_validation.py::TestSchemaValidation::test_sv02` |
| SV-03 | Schema 文件数量一致性 | TASK 01 完成 | 统计 Schemas/ 下文件数 | 初始 24 个，扩展后 28 个 | `pytest Tests/scripts/test_schema_validation.py::TestSchemaValidation::test_sv03` |
| SV-04 | example→Schema 映射完整 | 文件就位 | 检查每个 example 有对应 Schema | 全部 example 有映射 | `pytest Tests/scripts/test_schema_validation.py::TestSchemaValidation::test_sv04` |
| SV-05 | 新增 example 不破坏旧 example | TASK 18 扩展后 | 运行 validate_examples.py | 原 8 个仍通过，新增也通过 | `python Scripts/validation/validate_examples.py --strict` |
| SV-06 | reviewed_handoff.schema.json 格式正确 | task1 TASK 03 | `json.load` + 检查 required 字段 | required 含 5 个必填字段 | `python -c "import json; s=json.load(open('Schemas/reviewed_handoff.schema.json')); assert len(s['required'])==5"` |
| SV-07 | run_plan.schema.json 格式正确 | task1 TASK 03 | `json.load` + 检查 required 字段 | required 含 5 个必填字段 | `python -c "import json; s=json.load(open('Schemas/run_plan.schema.json')); assert len(s['required'])==5"` |
| SV-08 | reviewed_handoff example 通过 Schema 校验 | SV-06 | `jsonschema.validate` | 无异常 | `python -c "import json,jsonschema; jsonschema.validate(json.load(open('Schemas/examples/reviewed_handoff_greenfield.example.json')), json.load(open('Schemas/reviewed_handoff.schema.json')))"` |
| SV-09 | run_plan example 通过 Schema 校验 | SV-07 | `jsonschema.validate` | 无异常 | `python -c "import json,jsonschema; jsonschema.validate(json.load(open('Schemas/examples/run_plan_greenfield.example.json')), json.load(open('Schemas/run_plan.schema.json')))"` |
| SV-10 | 新增 Schema 不影响现有 validate_examples.py | SV-08, SV-09 | `validate_examples.py --strict` | 原有 10 个 + 新增 2 个全部通过 | `python Scripts/validation/validate_examples.py --strict` |

---

## 3. 编译与加载（BL）

> 来源：TASK 03
> 自动化基础设施：`Build.bat`（UBT）+ `Scripts/validation/start_ue_editor_project.ps1`

| 编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 自动化命令 |
|------|---------|---------|---------|---------|-----------|
| BL-01 | Plugin 编译零 error | VS2022 / UE5.5.4 | UBT 编译 | 零 error（允许引擎自身 warning） | `Build.bat Mvpv4TestCodexEditor Win64 Development -Project=...uproject` |
| BL-02 | Plugin 加载日志 | Editor 启动 | grep Editor log | 出现 `[AgentBridge] Plugin loaded, version 0.3.0` | `Scripts/validation/start_ue_editor_project.ps1` → 检查 `Saved/Logs/*.log` |
| BL-03 | BridgeTypes.h 可被外部引用 | BL-01 通过 | 编译含 `#include "BridgeTypes.h"` 的模块 | 编译通过 | BL-01 的 UBT 编译隐含验证（AgentBridgeTests 引用 BridgeTypes.h） |
| BL-04 | EBridgeStatus 枚举完整 | BL-01 通过 | UE5 Automation Test 检查枚举值 | 5 个值：Success/Warning/Failed/Mismatch/ValidationError | `UnrealEditor-Cmd.exe ... -run=AgentBridge -RunTests=Project.AgentBridge.L1 -NullRHI` |
| BL-05 | EBridgeErrorCode 枚举完整 | BL-01 通过 | UE5 Automation Test 检查枚举值 | 12 个值（含 3 个 L3 专用） | `UnrealEditor-Cmd.exe ... -run=AgentBridge -RunTests=Project.AgentBridge.L1 -NullRHI` |
| BL-06 | Remote Control API 可用 | Editor 运行 | HTTP GET 探测 | 返回有效 JSON | `Scripts/validation/start_ue_editor_project.ps1` → `curl http://localhost:30010/remote/info` |

---

### 3.1 通用执行约束（适用于 Q/W/CL/UI）

| 约束编号 | 常见阻塞现象 | 约束说明 | 统一处理 |
|------|------|------|------|
| C1 | 日志出现 `Unable to load plugin 'AgentBridgeTests'`，测试未真正开始 | `AgentBridgeTests` 位于嵌套路径 `Plugins/AgentBridge/AgentBridgeTests/`，仅写 `-EnablePlugins=AgentBridgeTests` 无法稳定定位 | 显式传 `-PLUGIN=<绝对路径>/AgentBridgeTests.uplugin` |
| C2 | 日志出现 `Unknown Automation command 'Automation RunTests ...'` | 在无头/Commandlet 场景混用了 Editor Console 指令 | 统一使用 `-run=AgentBridge -RunTests=<Filter>` |
| C3 | 启动脚本参数被误绑定，出现 `Resolve-Path ... -PLUGIN=...` | 未显式传 `-ProjectPath`，剩余参数可能被 PowerShell 绑定到位置参数 | 显式传 `-ProjectPath=<uproject>`，其后再传运行参数 |

推荐无头基线命令（适用于 4~7 分类）：
`Scripts/validation/start_ue_editor_cmd_project.ps1 -EngineRoot "<UE_ROOT>" -ProjectPath "<UPROJECT>" -PLUGIN="<UPLUGIN>" -run=AgentBridge -RunTests=Project.AgentBridge.L1.Query -NullRHI -Unattended -NoPause -stdout -FullStdOutLogOutput`

---

## 4. L1 查询接口（Q）

> 来源：TASK 04, TASK 07
> UE5 Automation Test 编号：T1-01 ~ T1-07
> 自动化命令（推荐无头）：`UnrealEditor-Cmd.exe ... -run=AgentBridge -RunTests=Project.AgentBridge.L1.Query -NullRHI`
> 已打开 Editor 的交互会话可使用：`Automation RunTests Project.AgentBridge.L1.Query`

| 编号 | 用例名称 | UE5 Test ID | 测试步骤 | 预期结果 |
|------|---------|------------|---------|---------|
| Q-01 | GetCurrentProjectState 正常返回 | T1-01 | 调用接口 | status=success, project_name 非空, engine_version 含 "5.5" |
| Q-02 | ListLevelActors 正常返回 | T1-02 | 调用接口 | status=success, actors 数组, 每项含 actor_name/actor_path/class |
| Q-03 | GetActorState 正常路径 | T1-03 | 传入有效 ActorPath | data 含 transform/collision/tags |
| Q-04 | GetActorState 空参数 | T1-03 | ActorPath="" | status=validation_error, error code=INVALID_ARGS |
| Q-05 | GetActorState 不存在路径 | T1-03 | ActorPath="/Non/Existent" | status=failed, error code=ACTOR_NOT_FOUND |
| Q-06 | GetActorBounds 正常返回 | T1-04 | 传入有效 ActorPath | world_bounds_origin[3] + world_bounds_extent[3] |
| Q-07 | GetActorBounds 空参数 | T1-04 | ActorPath="" | status=validation_error |
| Q-08 | GetAssetMetadata 存在资产 | T1-05 | 传入存在的 AssetPath | exists=true, class 非空 |
| Q-09 | GetAssetMetadata 不存在资产 | T1-05 | 传入不存在路径 | status=success, exists=false（不是 error） |
| Q-10 | GetAssetMetadata 空参数 | T1-05 | AssetPath="" | status=validation_error |
| Q-11 | GetDirtyAssets 正常返回 | T1-06 | 调用接口 | status=success, dirty_assets 为数组 |
| Q-12 | RunMapCheck 正常返回 | T1-07 | 调用接口 | status=success, map_errors(int), map_warnings(int) |

---

## 5. L1 写接口（W）

> 来源：TASK 05, TASK 07, TASK 17
> UE5 Automation Test 编号：T1-08 ~ T1-11
> 自动化命令（推荐无头）：`UnrealEditor-Cmd.exe ... -run=AgentBridge -RunTests=Project.AgentBridge.L1.Write -NullRHI`
> 已打开 Editor 的交互会话可使用：`Automation RunTests Project.AgentBridge.L1.Write`

| 编号 | 用例名称 | UE5 Test ID | 测试步骤 | 预期结果 |
|------|---------|------------|---------|---------|
| W-01 | SpawnActor 参数校验 | T1-08 | ActorClass="" 等 3 种空参数 | validation_error + INVALID_ARGS |
| W-02 | SpawnActor dry_run | T1-08 | bDryRun=true | status=success, Actor 不出现在关卡中 |
| W-03 | SpawnActor 实际执行 | T1-08 | 正常参数 | Actor 出现, created_objects 非空 |
| W-04 | SpawnActor 写后读回容差 | T1-08 | 比较 actual_transform 与输入 | location ≤0.01cm, scale ≤0.001 |
| W-05 | SpawnActor dirty_assets | T1-08 | 执行后检查 | dirty_assets 非空 |
| W-06 | SpawnActor Undo 回滚 | T1-08 | FScopedTransaction + GEditor->UndoTransaction | Actor 消失, bTransaction=true |
| W-07 | SetActorTransform 参数校验 | T1-09 | 空 ActorPath | validation_error |
| W-08 | SetActorTransform 不存在 Actor | T1-09 | 不存在路径 | ACTOR_NOT_FOUND |
| W-09 | SetActorTransform dry_run | T1-09 | bDryRun=true | 返回 old_transform 预览, 不修改 |
| W-10 | SetActorTransform 实际执行 | T1-09 | 正常参数 | old_transform ≠ actual_transform |
| W-11 | SetActorTransform Undo | T1-09 | GEditor->UndoTransaction | Transform 恢复原值 |
| W-12 | ImportAssets 参数校验 | T1-10 | 空 SourceDir/DestPath | validation_error |
| W-13 | ImportAssets dry_run | T1-10 | bDryRun=true | 不实际导入 |
| W-14 | CreateBlueprintChild 参数校验 | T1-11 | 空参数 | validation_error |
| W-15 | CreateBlueprintChild 不存在父类 | T1-11 | 不存在 ParentClass | CLASS_NOT_FOUND |
| W-16 | CreateBlueprintChild dry_run | T1-11 | bDryRun=true | 不实际创建 |
| W-17 | CreateBlueprintChild 实际创建+Undo | T1-11 | 正常参数后 Undo | 创建成功然后撤销 |
| W-18 | SetActorCollision 写+读回+Undo | T1-08 扩展 | 修改碰撞配置 | GetActorState 确认修改, Undo 恢复 |
| W-19 | AssignMaterial 写+读回+Undo | T1-08 扩展 | 设置材质 | 读回确认, Undo 恢复 |
| W-20 | 全部写接口返回 bTransaction:true | T1-08~11 | 检查返回值 | bTransaction=true |

---

## 6. L2 闭环验证（CL）

> 来源：TASK 08
> UE5 Automation Spec 编号：LT-01 ~ LT-03
> 自动化命令（推荐无头）：`UnrealEditor-Cmd.exe ... -run=AgentBridge -RunTests=Project.AgentBridge.L2 -NullRHI`
> 已打开 Editor 的交互会话可使用：`Automation RunTests Project.AgentBridge.L2`

### Spec 1: SpawnReadbackLoop (LT-01, 5 个 It)

| 编号 | 用例名称 | It 描述 | 预期结果 |
|------|---------|---------|---------|
| CL-01 | Spawn 后 location 读回一致 | should return matching location on readback | 容差 ≤0.01 |
| CL-02 | Spawn 后 rotation 读回一致 | should return matching rotation on readback | 容差 ≤0.01 |
| CL-03 | Spawn 后 scale 读回一致 | should return matching scale on readback | 容差 ≤0.001 |
| CL-04 | Spawn 后可通过 GetActorBounds 查到 | should be visible in GetActorBounds | 跨接口验证 |
| CL-05 | Spawn 后关卡标记为 dirty | should mark level as dirty | 副作用检查 |
| CL-06 | AfterEach Undo 无残留 Actor | — | Undo 后 Actor 消失 |

### Spec 2: TransformModifyLoop (LT-02, 3 个 It)

| 编号 | 用例名称 | It 描述 | 预期结果 |
|------|---------|---------|---------|
| CL-07 | old_transform 是修改前值 | should return old_transform matching original | old_transform ≠ actual_transform |
| CL-08 | 修改后 GetActorState 读回新值 | should readback modified values via GetActorState | 新值一致 |
| CL-09 | Undo 恢复原值 | should be undoable via Transaction | old values 恢复正确 |

### Spec 3: ImportMetadataLoop (LT-03, 2 个 It)

| 编号 | 用例名称 | It 描述 | 预期结果 |
|------|---------|---------|---------|
| CL-10 | 导入后 GetAssetMetadata 可查到 | should find imported asset via GetAssetMetadata | exists=true |
| CL-11 | 导入后资产在 dirty 列表中 | should list imported assets as dirty | dirty_assets 含该资产 |
| CL-12 | 无测试资产时 SKIP 不 FAIL | — | graceful degradation |

---

## 7. L3 UI 工具（UI）

> 来源：TASK 20
> UE5 Automation Test 编号：T1-12 ~ T1-15, Spec: LT-04 ~ LT-05
> 自动化命令（推荐无头）：`UnrealEditor-Cmd.exe ... -run=AgentBridge -RunTests=Project.AgentBridge.L1.UITool -NullRHI` 与 `Project.AgentBridge.L2.UITool`
> 已打开 Editor 的交互会话可使用：`Automation RunTests Project.AgentBridge.L1.UITool` / `Project.AgentBridge.L2.UITool`
> Gauntlet AllTests 模式（需 GPU）自动覆盖

### L1 UITool 测试

| 编号 | 用例名称 | UE5 Test ID | 预期结果 |
|------|---------|------------|---------|
| UI-01 | IsAutomationDriverAvailable | T1-12 | 与 FAutomationDriverAdapter::IsAvailable() 一致 |
| UI-02 | ClickDetailPanelButton 空 ActorPath | T1-13 | validation_error |
| UI-03 | ClickDetailPanelButton 空 ButtonLabel | T1-13 | validation_error |
| UI-04 | ClickDetailPanelButton 不存在 Actor | T1-13 | ACTOR_NOT_FOUND |
| UI-05 | ClickDetailPanelButton dry_run | T1-13 | tool_layer=L3_UITool |
| UI-06 | TypeInDetailPanelField 空参数（3 种） | T1-14 | validation_error each |
| UI-07 | TypeInDetailPanelField dry_run | T1-14 | tool_layer=L3_UITool |
| UI-08 | DragAssetToViewport 参数校验+dry_run | T1-15 | data.drop_location 存在 |
| UI-09 | DragAssetToViewport 执行+L3→L1 交叉比对 | T1-15 | consistent=true |
| UI-10 | DragAssetToViewport Undo 清理 | T1-15 | Actor 消失 |
| UI-11 | Driver 不可用时优雅降级 | T1-12~15 | 全部 SKIP 不 FAIL |

### L2 UITool Spec

| 编号 | 用例名称 | UE5 Spec ID | It 数 | 预期结果 |
|------|---------|------------|------|---------|
| UI-12 | DragAssetToViewportLoop | LT-04 | 5 | L3 执行→L1 Actor 数增加→交叉比对→position 容差 100cm→Undo 恢复 |
| UI-13 | TypeInFieldLoop | LT-05 | 3 | L1 Spawn 准备→baseline 读回→L3 TypeIn→L1 仍可用 |

---

## 8. Commandlet 无头执行（CMD）

> 来源：TASK 06
> 自动化基础设施：`UnrealEditor-Cmd.exe -run=AgentBridge` + `Scripts/validation/start_ue_editor_cmd_project.ps1`
> 全部使用 `-NullRHI`（无 GPU）无头执行

| 编号 | 用例名称 | 测试命令 | 预期结果 |
|------|---------|---------|---------|
| CMD-01 | 模式 3 单工具执行 | `UnrealEditor-Cmd.exe ...uproject -run=AgentBridge -Tool=GetCurrentProjectState -Report=report.json -NullRHI` | JSON 输出 + exit code 0 |
| CMD-02 | 模式 3 ListLevelActors | 同上，`-Tool=ListLevelActors` | JSON 含 actors 数组 + exit code 0 |
| CMD-03 | 不存在工具名 | 同上，`-Tool=NonExistentTool` | exit code 2 |
| CMD-04 | 无参数启动 | `-run=AgentBridge`（不传 -Tool/-RunTests） | exit code 2 + log "No mode specified" |
| CMD-05 | Report 输出 | `-Report=xxx.json` | 生成有效 JSON 报告文件 |
| CMD-06 | 模式 2 运行测试 | `-run=AgentBridge -RunTests=Project.AgentBridge.L1 -Report=report.json` | 测试执行 + exit code 0 |
| CMD-07 | UATRunner 可用性 | `IsUATAvailable()` 通过 Commandlet 调用 | 返回 true |
| CMD-08 | FUATRunResult.IsSuccess() | bLaunched+bCompleted+ExitCode==0 | 返回 true |

> 证据：`Docs/History/reports/AgentBridgeEvidence/task06_evidence_2026-03-28/` 下含每个用例的 `.log` + `_report.json`

---

## 9. Python 客户端（PY）

> 来源：TASK 09
> 自动化方式：`pytest` + `ast.parse` 语法检查 + Mock 模式调用

| 编号 | 用例名称 | 测试方式 | 预期结果 |
|------|---------|---------|---------|
| PY-01 | 7 个 Python 文件无语法错误 | `ast.parse` 遍历 `Scripts/bridge/*.py` | 无 SyntaxError |
| PY-02 | BridgeChannel 枚举完整 | `from bridge_core import BridgeChannel` | 4 值：PYTHON_EDITOR/REMOTE_CONTROL/CPP_PLUGIN/MOCK |
| PY-03 | Mock 模式 7 个 L1 查询 | `set_channel(MOCK)` 后调用全部查询接口 | 全部 status=success |
| PY-04 | Mock 模式 4 个 L1 写接口 | `set_channel(MOCK)` 后调用全部写接口 | 全部 status=success |
| PY-05 | Mock 模式 3 个 L3 UI 接口 | `set_channel(MOCK)` 后调用 | status=success + tool_layer=L3_UITool |
| PY-06 | validate_required_string 空串 | `validate_required_string("")` | 返回 validation_error |
| PY-07 | validate_required_string 有效值 | `validate_required_string("valid")` | 返回 None |
| PY-08 | call_cpp_plugin 函数签名 | `inspect.signature(call_cpp_plugin)` | function_name + parameters 参数 |
| PY-09 | _CPP_QUERY_MAP 映射数 | `len(_CPP_QUERY_MAP)` | 7 个映射 |
| PY-10 | _CPP_WRITE_MAP 映射数 | `len(_CPP_WRITE_MAP)` | 4 个映射 |

> 证据：`Docs/History/reports/AgentBridgeEvidence/task09_evidence_2026-03-28/`

---

## 10. Orchestrator 编排（ORC）

> 来源：TASK 10 ~ TASK 14
> 自动化方式：`pytest` + `orchestrator.py --channel mock` + Channel C（UE5 Editor + RC API）

### Spec Reader (TASK 10)

| 编号 | 用例名称 | 测试方式 | 预期结果 |
|------|---------|---------|---------|
| ORC-01 | read_spec 解析模板 Spec | `read_spec("templates/scene_spec.yaml")` | 返回 7 个顶层字段 |
| ORC-02 | validate_spec 模板通过 | `validate_spec(spec)` | (True, []) |
| ORC-03 | validate_spec 缺必填字段 | 删除 required 字段后校验 | (False, [具体错误]) |
| ORC-04 | execution_method 默认值 | 未指定 execution_method 的 actor | 默认 "semantic" |
| ORC-05 | get_actors_by_execution_method 分组 | 4 actor spec | semantic 2 / ui_tool 2 |
| ORC-06 | 重复 actor_id 校验 | 两个相同 actor_id | validate_spec 返回 False |

> 证据：`Docs/History/reports/AgentBridgeEvidence/task10_evidence_2026-03-28/`

### Plan Generator (TASK 11)

| 编号 | 用例名称 | 测试方式 | 预期结果 |
|------|---------|---------|---------|
| ORC-07 | 全新场景→全部 CREATE | `generate_plan(spec, existing_actors=[])` | semantic=CREATE, ui_tool=UI_TOOL |
| ORC-08 | 已存在 Actor→UPDATE | `generate_plan(spec, existing_actors=[...])` | existing_actor_path 正确 |
| ORC-09 | ui_tool Actor 不受 existing 影响 | existing 中含 ui_tool actor | 始终 UI_TOOL |
| ORC-10 | plan entry 字段完整 | 检查返回结构 | 含 actor_spec/action/execution_method/existing_actor_path/reason |

> 证据：`Docs/History/reports/AgentBridgeEvidence/task11_evidence_2026-03-28/`

### Verifier (TASK 12)

| 编号 | 用例名称 | 测试方式 | 预期结果 |
|------|---------|---------|---------|
| ORC-11 | verify_transform 精确匹配 | 输入完全相同的 transform | status=success, mismatches=[] |
| ORC-12 | verify_transform 超出容差 | location 偏差 > 0.01 | status=mismatch, mismatches 含字段名和值 |
| ORC-13 | L3 宽容差（50cm 偏差） | L3_TOLERANCES 下 50cm 偏差 | 在 100cm 容差内→success |
| ORC-14 | checks 列表字段完整 | 检查返回的 checks 数组 | field/expected/actual/delta/tolerance/pass |
| ORC-15 | verify_actor_state 自动选择容差 | 分别传 semantic 和 ui_tool | semantic→DEFAULT, ui_tool→L3 |

> 证据：`Docs/History/reports/AgentBridgeEvidence/task12_evidence_2026-03-28/`

### Report Generator (TASK 13)

| 编号 | 用例名称 | 测试方式 | 预期结果 |
|------|---------|---------|---------|
| ORC-16 | 全部 success→overall success | 全部 actor status=success | overall_status=success |
| ORC-17 | 有 mismatch 无 failed→mismatch | 混合 success+mismatch | overall_status=mismatch |
| ORC-18 | 有 failed→failed（最高优先级） | 混合 success+mismatch+failed | overall_status=failed |
| ORC-19 | summary 计数正确 | 4 actors 不同状态 | passed+mismatched+failed+skipped=total |
| ORC-20 | actors entry 字段完整 | 检查报告结构 | actor_id/action/execution_method/exec_status/verify_status/mismatches |
| ORC-21 | save_report 写文件 | `save_report(report, path)` | 输出有效 JSON 文件 |
| ORC-22 | 报告含时间戳 | 检查 timestamp 字段 | ISO 8601 格式 |
| ORC-23 | L3 操作含 cross_verification | L3 actor entry | actors entry 含 cross_verification 字段 |

> 证据：`Docs/History/reports/AgentBridgeEvidence/task13_evidence_2026-03-28/`

### Orchestrator 主编排 (TASK 14)

| 编号 | 用例名称 | 测试命令 | 预期结果 |
|------|---------|---------|---------|
| ORC-24 | Mock 模式 E2E（4 actors） | `python orchestrator.py --channel mock --spec scene_spec.yaml --report report.json` | 报告含 overall_status + 4 actor entries |
| ORC-25 | Channel C E2E | `python orchestrator.py --channel cpp_plugin --spec scene_spec.yaml` (需 Editor 运行) | semantic actors 通过 L1 创建+验证通过 |
| ORC-26 | L3 操作分发 | Channel C + ui_tool actor | UI_TOOL action 分发到 _UI_TOOL_DISPATCH |
| ORC-27 | L3 操作后交叉比对 | Channel C + ui_tool actor | cross_verify_ui_operation 被调用 |
| ORC-28 | 单 Actor 失败不中断后续 | 故意让第 1 个 actor 失败 | 后续 Actor 继续执行 |
| ORC-29 | execution_methods 计数 | 报告 summary | 正确统计 semantic/ui_tool 数量 |
| ORC-30 | CLI 参数 | `--channel mock --report path` | 正常工作 |
| ORC-31 | 退出码 | 检查 exit code | success→0, failed→1 |

> 证据：`Docs/History/reports/AgentBridgeEvidence/task14_evidence_2026-03-28/`

### Run Plan Builder (task1.md TASK 06)

| 编号 | 用例名称 | 测试方式 | 预期结果 |
|------|---------|---------|---------|
| ORC-32 | run_plan_builder 可导入 | `from orchestrator.run_plan_builder import build_run_plan_from_handoff` | 无 ImportError |
| ORC-33 | handoff_runner 可导入 | `from orchestrator.handoff_runner import run_from_handoff` | 无 ImportError |
| ORC-34 | build_run_plan_from_handoff 生成 Run Plan | 传入 1 actor Handoff | workflow_sequence 含 1 个步骤 |
| ORC-35 | Run Plan source_handoff_id 匹配 | 检查输出 | source_handoff_id == 输入 handoff_id |
| ORC-36 | Run Plan workflow_type 正确 | 检查 workflow_sequence[0] | workflow_type == "spawn_actor" |
| ORC-37 | handoff_runner simulated 模式 E2E | `run_from_handoff(path, bridge_mode="simulated")` | execution_status=="succeeded", 3/3 步骤成功 |

> 证据：Greenfield simulated 模式执行报告 `ProjectState/Reports/`

---

## 11. Compiler Plane（CP）

> 来源：`Docs/History/Tasks/task1_phase3.md` TASK 04 + `Docs/History/Tasks/task2_phase4.md` TASK 06~10 + `Docs/History/Tasks/task3_phase5.md` TASK 03~08 + `Docs/History/Tasks/task4_phase6.md` TASK 04~08
> 自动化方式：pytest / `python compiler_main.py`
> 环境要求：Python 3.x + pyyaml + jsonschema

| 编号 | 用例名称 | 测试方式 | 预期结果 |
|------|---------|---------|---------|
| CP-01 | compiler.intake 可导入 | `from compiler.intake import read_gdd, read_gdd_from_directory` | 无 ImportError |
| CP-02 | compiler.routing 可导入 | `from compiler.routing import determine_mode, load_mode_config` | 无 ImportError |
| CP-03 | compiler.handoff 可导入 | `from compiler.handoff import build_handoff, serialize_handoff` | 无 ImportError |
| CP-04 | project_state_intake 可导入 | `from compiler.intake import get_project_state_snapshot` | 无 ImportError |
| CP-05 | design_input_intake 从 GDD 提取 game_type | `read_gdd(gdd_path)` | game_type == "boardgame" |
| CP-06 | mode_router 空项目 + auto → greenfield | `determine_mode(auto_config, empty_state)` | "greenfield_bootstrap" |
| CP-07 | mode_router 非空项目 + auto → brownfield | `determine_mode(auto_config, nonempty_state)` | "brownfield_expansion" |
| CP-08 | mode_router force_mode 覆盖 | `determine_mode(force_config, nonempty_state)` | "greenfield_bootstrap"（force 覆盖 auto） |
| CP-09 | handoff_builder 生成 3 Actor Handoff | `build_handoff(design_input, "greenfield_bootstrap")` | actors 数组长度 == 3，首个为 Board |
| CP-10 | 生成 Handoff 通过 Schema 校验 | `jsonschema.validate(handoff, schema)` | 无 ValidationError |
| CP-11 | compiler_main.py 端到端 | `python compiler_main.py` | 输出 Handoff YAML 到 ProjectState/Handoffs/draft/ |
| CP-12 | Static Base registry 可加载 | `load_static_base_registry()` | 10 个静态基座全部可见 |
| CP-13 | Phase 4 GDD 结构化提取 | `read_gdd(gdd_path)` | 返回 board / piece_catalog / rules / prototype_preview 等字段 |
| CP-14 | Handoff 生成 richer spec 节点 | `build_handoff(...)` | `dynamic_spec_tree` 同时包含 `world_build_spec` / `boardgame_spec` / `validation_spec` / `scene_spec` |
| CP-15 | GDD 显式 0 示例棋子 | 临时 GDD + `build_handoff(...)` | `scene_spec.actors[]` 仅保留 Board |
| CP-16 | 缺失模板报 capability_gaps | `review_dynamic_spec_tree(...)` | `required_static_templates` 正确写入缺失 spec_id |
| CP-17 | 默认示例棋子策略 | 主 GDD + `build_handoff(...)` | 未写预览规则时，默认生成 `Board + PieceX_1 + PieceO_1` |
| CP-18 | GDD 覆盖示例棋子数量 | 临时 GDD + `build_handoff(...)` | 显式 `X=2, O=1` 时生成 `Board + PieceX_1 + PieceX_2 + PieceO_1` |
| CP-19 | project_state_intake 返回 Phase 5 快照 | `get_project_state_snapshot()` | 返回兼容字段 + `has_existing_content / baseline_refs / metadata / current_project_state_digest` |
| CP-20 | baseline_builder 序列化 snapshot | `build_and_save_baseline_snapshot(...)` | 生成 baseline 文件且可重新加载 |
| CP-21 | delta_scope_analyzer 识别 no_change | 目标状态与 baseline 相同 | `delta_intent == "no_change"` |
| CP-22 | delta_scope_analyzer 识别 append_actor | baseline 为 `Board + PieceX_1` | `delta_intent == "append_actor"` 且 append 仅含 `PieceO_1` |
| CP-23 | Contract registry 与 Common Contract 可加载 | `load_contract_registry()` + `load_contract_bundle(...)` | 3 类 Common Contract 可加载，template/schema 可解析 |
| CP-24 | Brownfield Handoff 含 baseline/delta/tree_type | `build_handoff(..., mode=\"brownfield_expansion\")` | Handoff 通过 Schema 校验，`scene_spec.actors[]` 仅含新增 Actor |
| CP-25 | 默认 `preview_static` 生成完整 10 节点 Spec Tree | `pytest Tests/scripts/test_phase6_playable_runtime.py::TestPhase6PlayableRuntime::test_cp25_preview_static_generates_full_spec_tree` | `dynamic_spec_tree` 含 10 个 Phase 6 关键节点，`scene_spec` 默认为 `Board + PieceX_1 + PieceO_1` |
| CP-26 | `runtime_playable` 生成 runtime actor 与 runtime config | `pytest Tests/scripts/test_phase6_playable_runtime.py::TestPhase6PlayableRuntime::test_cp26_runtime_playable_handoff_writes_runtime_config` | handoff 为 reviewed，`BoardRuntimeActor` 存在，`runtime_config_ref` 文件落盘 |
| CP-27 | runtime actor 暴露最小 callable 接口 | `pytest Tests/scripts/test_phase6_playable_runtime.py::TestPhase6PlayableRuntime::test_cp27_runtime_actor_exposes_minimum_callable_interfaces` | 头文件中存在 `LoadRuntimeConfigFromFile / ApplyMoveByCell / GetBoardRuntimeState / ResetBoard` |
| CP-28 | 缺少 runtime 关键节点时 reviewer 阻断 | `pytest Tests/scripts/test_phase6_playable_runtime.py::TestPhase6PlayableRuntime::test_cp28_reviewer_blocks_missing_phase6_runtime_nodes` | 缺少 `turn_flow_spec / decision_ui_spec / runtime_wiring_spec` 时 status=`blocked` |
| CP-29 | Brownfield patch 缺少 genre contract 时 reviewer 阻断 | `pytest Tests/scripts/test_phase6_playable_runtime.py::TestPhase6PlayableRuntime::test_cp29_brownfield_patch_without_genre_contracts_is_blocked` | 缺少 `TurnFlowPatchContract / DecisionUIPatchContract` 时 status=`blocked` |
| CP-30 | delta policy 影响 Brownfield trace 与 regression focus | `pytest Tests/scripts/test_phase6_playable_runtime.py::TestPhase6PlayableRuntime::test_cp30_delta_policy_flows_into_brownfield_trace_and_regression_focus` | `delta_policy`、`high_risk_breakpoints`、`required_regression_checks` 均正确下沉 |
| CP-31 | 合同 registry 中 Common + Genre 路径可读 | `pytest Tests/scripts/test_phase6_playable_runtime.py::TestPhase6PlayableRuntime::test_cp31_contract_registry_common_and_genre_paths_are_readable` | Common 与 Boardgame 合同 manifest/template/schema 路径均存在且可读取 |

> 证据：`ProjectState/Handoffs/draft/` 下生成的 Handoff YAML 文件

---

## 12. Skills & Specs（SS）

> 来源：`Docs/History/Tasks/task1_phase3.md` TASK 05 + `Docs/History/Tasks/task2_phase4.md` TASK 03~05 + `Docs/History/Tasks/task4_phase6.md` TASK 02~05
> 自动化方式：pytest / `yaml.safe_load`
> 环境要求：Python 3.x + pyyaml

| 编号 | 用例名称 | 测试方式 | 预期结果 |
|------|---------|---------|---------|
| SS-01 | Skills 目录结构完整 | 检查 base_domains/ + genre_packs/ 存在 | 目录齐全 |
| SS-02 | pack_manifest.yaml 可解析 | `yaml.safe_load(open(manifest_path))` | 无异常 |
| SS-03 | pack_manifest.yaml pack_id 正确 | 检查 pack_id 字段 | "genre-boardgame" |
| SS-04 | Specs 扩展目录完整 | 检查 StaticBase/ + Contracts/ 存在 | 目录齐全，现有 templates/ 未变 |
| SS-05 | StaticBase registry 完整 | `yaml.safe_load(open(spec_type_registry.yaml))` | 10 个静态基座全部登记，含 phase4_enabled 字段 |
| SS-06 | 10 个静态基座模板可解析 | 遍历 `Specs/StaticBase/**/*template.yaml` | 全部 `yaml.safe_load` 成功 |
| SS-07 | 10 个静态基座 schema 合法 | 遍历 `Specs/StaticBase/**/*schema.json` | 全部 `json.load` 成功 |
| SS-08 | `_core` registry 能发现 `genre-boardgame` | `pytest Tests/scripts/test_phase6_playable_runtime.py::TestPhase6PlayableRuntime::test_ss08_pack_registry_and_modules_load` | registry 含 `genre-boardgame`，且 required skills 可加载 |
| SS-09 | `boardgame` manifest 覆盖完整 Phase 6 字段 | `pytest Tests/scripts/test_phase6_playable_runtime.py::TestPhase6PlayableRuntime::test_ss09_boardgame_manifest_is_phase6_complete` | manifest 含 status / review / validation / delta policy 等 Phase 6 字段 |
| SS-10 | 3 个 required skills 模块可加载 | `pytest Tests/scripts/test_phase6_playable_runtime.py::TestPhase6PlayableRuntime::test_ss10_required_skills_modules_load` | `board_layout / piece_movement / turn_system` 均存在且可导入 |
| SS-11 | review / validation / delta policy 模块可加载 | `pytest Tests/scripts/test_phase6_playable_runtime.py::TestPhase6PlayableRuntime::test_ss11_review_validation_and_delta_policy_modules_load` | `boardgame_reviewer / boardgame_validator / boardgame_delta_policy` 均可导入 |
| SS-12 | Genre contracts 已登记到 contract registry | `pytest Tests/scripts/test_phase6_playable_runtime.py::TestPhase6PlayableRuntime::test_ss12_genre_contracts_registered_in_contract_registry` | registry 含 `TurnFlowPatchContract / DecisionUIPatchContract` |
| SS-13 | Common + Genre contract bundle 均可加载 | `pytest Tests/scripts/test_phase6_playable_runtime.py::TestPhase6PlayableRuntime::test_ss13_common_and_genre_contract_bundles_load` | Common 与 Boardgame 合同 bundle 均可解析与加载 |

> 证据：目录结构 + YAML 解析输出

---

## 13. Gauntlet CI/CD（GA）

> 来源：TASK 16
> 自动化基础设施：`RunUAT.bat RunUnreal` + `Gauntlet/AgentBridge.TestConfig.cs` + `AgentBridgeGauntletController`(C++)

| 编号 | 用例名称 | 测试命令 | 预期结果 |
|------|---------|---------|---------|
| GA-01 | SmokeTests 执行 | `RunUAT.bat -ScriptDir=...Gauntlet RunUnreal -test=SmokeTests -Build=Editor -Platform=Win64 -unattended` | exit code 0 (Selected=33, Passed=17, Warnings=16, Failed=0) |
| GA-02 | Gauntlet 全流程 | 同上 | 自动完成：启动 Editor→运行测试→收集结果→停止 Editor |
| GA-03 | 失败时非零退出码 | 有测试失败时执行 | exit code 1 |
| GA-04 | SmokeTests 使用 -NullRHI | 检查 TestConfig.cs SmokeTests 配置 | L1+L2 filter, -NullRHI, 300s timeout |
| GA-05 | AllTests 不使用 -NullRHI | 检查 TestConfig.cs AllTests 配置 | L1+L2+L3+FunctionalTest, 需 GPU, 900s timeout |
| GA-06 | Controller 生命周期 | 检查 Editor log | OnInit→test discovery→RunTests→Finish ExitCode=0 |

> 证据：`Docs/History/reports/AgentBridgeEvidence/task16_evidence_2026-03-28/` 含 `task16_smoke_rununreal_*.log` + `task16_alltests_rununreal_*.log`

---

## 14. 端到端集成（E2E）

> 来源：TASK 15, TASK 19 + `Docs/History/Tasks/task4_phase6.md` TASK 06~08
> 自动化方式：多步流水线，每步独立可执行

### L3 Functional Test (TASK 15)

| 编号 | 用例名称 | 自动化命令 | 预期结果 |
|------|---------|-----------|---------|
| E2E-01 | FTEST_WarehouseDemo 可发现 | `RunUAT.bat RunUnreal -test=AllTests`（Gauntlet 自动发现） | Session Frontend 可见 |
| E2E-02 | 5 个内置 Actor 全部 Spawn→Verify→PASS | Gauntlet AllTests 自动运行 | FinishTest(Succeeded), 5/5 actors verified |
| E2E-03 | bUndoAfterTest 清理无残留 | Gauntlet AllTests 自动运行 | CleanUp 执行 Undo |
| E2E-04 | L1+L2+L3 联合运行无冲突 | `UnrealEditor-Cmd.exe ... -run=AgentBridge -RunTests=Project.AgentBridge -NullRHI` 或 Gauntlet AllTests | 全部通过 |

> 证据：`Docs/History/reports/AgentBridgeEvidence/task15_evidence_2026-03-28/`

### 完整 Demo 验证 (TASK 19, 7 步)

| 编号 | 用例名称 | 验证步骤 | 自动化命令 | 预期结果 |
|------|---------|---------|-----------|---------|
| E2E-05 | Schema 全量验证 | Step 1/7 | `python Scripts/validation/validate_examples.py --strict` | 10/10 pass, exit 0 |
| E2E-06 | L1+L2 全绿 | Step 2/7 | `UnrealEditor-Cmd.exe ... -run=AgentBridge -RunTests=Project.AgentBridge.L1 -NullRHI` | ≥15 绿灯, SKIP 仅限 UITool/Import |
| E2E-07 | L3 Functional Test | Step 3/7 | `RunUAT.bat RunUnreal -test=AllTests`（含 FTEST_WarehouseDemo） | 5 Actors PASS, 或无 map 时 SKIP |
| E2E-08 | Orchestrator E2E | Step 4/7 | `python orchestrator.py --channel cpp_plugin --spec scene_spec.yaml --report report.json` | 4 actors (2 semantic+2 ui_tool), 报告含 overall_status |
| E2E-09 | Commandlet 无头执行 | Step 5/7 | `UnrealEditor-Cmd.exe -run=AgentBridge -Tool=GetCurrentProjectState -NullRHI` | Mode 3 JSON+exit 0; Mode 2 L1+exit 0 |
| E2E-10 | Gauntlet CI/CD | Step 6/7 | `RunUAT.bat RunUnreal -test=SmokeTests` + `-test=AllTests` | SmokeTests exit 0; AllTests exit 0 |
| E2E-11 | 三通道一致性 | Step 7/7 | Python 脚本：Channel A(`import unreal`) + B(`CPP_PLUGIN`) + C(`REMOTE_CONTROL`) 查询同一 Actor | transform 一致, `consistent: true` |

> 证据：`Docs/History/reports/AgentBridgeEvidence/task19_evidence_2026-03-27/` 含 step1~step7 全部日志 + JSON

### Greenfield 管线验证（`Docs/History/Tasks/task1_phase3.md` TASK 07, 09, 10 + `Docs/History/Tasks/task2_phase4.md` TASK 09, 10）

| 编号 | 用例名称 | 验证步骤 | 自动化命令 | 预期结果 |
|------|---------|---------|-----------|---------|
| E2E-12 | Greenfield simulated 端到端 | GDD→Compiler→Handoff→RunPlan→执行→Report | `python Scripts/run_greenfield_demo.py` | 输出 "执行状态: succeeded" |
| E2E-13 | Handoff draft 文件生成 | 检查 ProjectState/Handoffs/draft/ | `ls ProjectState/Handoffs/draft/*.yaml` | 有 handoff YAML 文件 |
| E2E-14 | Handoff approved 文件生成 | 检查 ProjectState/Handoffs/approved/ | `ls ProjectState/Handoffs/approved/*.yaml` | 有 handoff YAML 文件 |
| E2E-15 | Execution report 正确 | 检查 ProjectState/Reports/ | `python -c "import json,glob; r=json.load(open(glob.glob('ProjectState/Reports/*.json')[-1])); assert r['summary']['succeeded']==3"` | 3/3 步骤成功 |
| E2E-16 | Greenfield bridge_python 端到端 [UE5] | `python Scripts/run_greenfield_demo.py bridge_python` | 需 UE5 Editor 运行 | 3 个 Actor 在 UE5 中生成 |
| E2E-17 | UE5 Actor 位置验证 [UE5] | Bridge 查询 Board/PieceX_1/PieceO_1 | `query_tools.list_level_actors` + `get_actor_state` | Board@(0,0,0) scale(3,3,0.1), PieceX_1@(-100,-100,50), PieceO_1@(100,100,50) |
| E2E-18 | Phase 4 simulated richer spec 端到端 | `python Scripts/run_greenfield_demo.py` | `dynamic_spec_tree` 含 richer spec 节点，且执行状态为 succeeded |
| E2E-19 | Greenfield bridge_rc_api 真实 smoke [UE5] | `python Scripts/run_greenfield_demo.py bridge_rc_api` | 需 UE5 Editor + RC API 运行 | 3 个 Actor 在 UE5 中生成，RC API 链路闭环 |

> 证据：`ProjectState/Reports/` 下执行报告 + `ProjectState/Handoffs/` 下 Handoff 文件

### Brownfield 管线验证（`Docs/History/Tasks/task3_phase5.md` TASK 03~08）

| 编号 | 用例名称 | 验证步骤 | 自动化命令 | 预期结果 |
|------|---------|---------|-----------|---------|
| E2E-20 | Brownfield simulated append-only 端到端 | baseline(`Board + PieceX_1`) → delta handoff → 执行 | `python Scripts/run_brownfield_demo.py` | 输出 `append_actor`，且仅追加 `PieceO_1` |
| E2E-21 | Brownfield bridge_rc_api 真机 smoke + 截图证据 [UE5] | RC API 启动 → delta handoff → 执行 → 读回 → 截图取证 | `python Scripts/run_brownfield_demo.py bridge_rc_api` | `Board / PieceX_1 / PieceO_1` 在 UE5 中生成，且证据目录含 `overview_oblique + topdown_alignment + note + log` |

> 证据：`ProjectState/Reports/task_phase5_brownfield_rc_smoke_2026-04-01.md` + `Docs/History/reports/AgentBridgeEvidence/phase5_evidence_2026-04-01/`

### Phase 6 Playable Runtime 验证（`Docs/History/Tasks/task4_phase6.md` TASK 06~08）

| 编号 | 用例名称 | 验证步骤 | 自动化命令 | 预期结果 |
|------|---------|---------|-----------|---------|
| E2E-22 | Phase 6 Greenfield simulated 回归 | Greenfield compiler → handoff → 执行 | `python Scripts/run_greenfield_demo.py` | 输出执行状态 `succeeded`，作为 Phase 6 基线回归 |
| E2E-23 | Brownfield simulated append-only 回归 | Brownfield baseline → delta handoff → 执行 | `python Scripts/run_brownfield_demo.py` | 输出 `append_actor`、`PieceO_1`，且执行状态 `succeeded` |
| E2E-24 | playable runtime simulated 最小闭环 | `runtime_playable` handoff → 执行 | `python Scripts/run_boardgame_playable_demo.py` | 输出 `BoardRuntimeActor`，且执行状态 `succeeded` |
| E2E-25 | 真实 UE5 中成功生成 `BoardRuntimeActor` [UE5] | 启动 UE5 → `bridge_rc_api` playable demo → 写 acceptance report | `python Scripts/run_boardgame_playable_demo.py bridge_rc_api` | `phase6_runtime_acceptance_*.json` 中 `E2E-25.status == passed` |
| E2E-26 | 自动落子后终局可读回 [UE5] | `ApplyMoveByCell` 序列 → `GetBoardRuntimeState()` | `python Scripts/run_boardgame_playable_demo.py bridge_rc_api` | smoke 报告中 `result_state` 为 `X_wins / O_wins / draw` |
| E2E-27 | 真实截图证据链落盘 [UE5] | `bridge_rc_api` 成功后触发统一截图脚本 | `python Scripts/run_boardgame_playable_demo.py bridge_rc_api` | `ProjectState/Evidence/Phase6/` 与历史归档中均存在 `overview_oblique + topdown_alignment + note + log` |
| E2E-28 | 棋类顶视图证据完整性 [UE5] | 人工核验 `topdown_alignment` | 参考 `task_phase6_e2e28_fix_and_rerun_2026-04-02.md` | 顶视图完整覆盖棋盘边界与全部棋子，且可直接判断棋子与格位对应关系 |

> 证据：`ProjectState/Reports/task_phase6_doc_gap_and_entry_backfill_2026-04-02.md` + `ProjectState/Reports/phase6_runtime_acceptance_20260402_025815.json` + `Docs/History/reports/AgentBridgeEvidence/phase6_evidence_2026-04-02/`

---

## 附录 A：UE5 Automation Test ID 速查表

| Test ID | 全名 | 类型 | 所属分类 |
|---------|------|------|---------|
| T1-01 | Project.AgentBridge.L1.Query.GetCurrentProjectState | L1 | Q-01 |
| T1-02 | Project.AgentBridge.L1.Query.ListLevelActors | L1 | Q-02 |
| T1-03 | Project.AgentBridge.L1.Query.GetActorState | L1 | Q-03~05 |
| T1-04 | Project.AgentBridge.L1.Query.GetActorBounds | L1 | Q-06~07 |
| T1-05 | Project.AgentBridge.L1.Query.GetAssetMetadata | L1 | Q-08~10 |
| T1-06 | Project.AgentBridge.L1.Query.GetDirtyAssets | L1 | Q-11 |
| T1-07 | Project.AgentBridge.L1.Query.RunMapCheck | L1 | Q-12 |
| T1-08 | Project.AgentBridge.L1.Write.SpawnActor | L1 | W-01~06 |
| T1-09 | Project.AgentBridge.L1.Write.SetActorTransform | L1 | W-07~11 |
| T1-10 | Project.AgentBridge.L1.Write.ImportAssets | L1 | W-12~13 |
| T1-11 | Project.AgentBridge.L1.Write.CreateBlueprintChild | L1 | W-14~17 |
| T1-12 | Project.AgentBridge.L1.UITool.IsAutomationDriverAvailable | L1 | UI-01 |
| T1-13 | Project.AgentBridge.L1.UITool.ClickDetailPanelButton | L1 | UI-02~05 |
| T1-14 | Project.AgentBridge.L1.UITool.TypeInDetailPanelField | L1 | UI-06~07 |
| T1-15 | Project.AgentBridge.L1.UITool.DragAssetToViewport | L1 | UI-08~10 |

| Spec ID | 全名 | It 数 | 所属分类 |
|---------|------|------|---------|
| LT-01 | Project.AgentBridge.L2.SpawnReadbackLoop | 5 | CL-01~06 |
| LT-02 | Project.AgentBridge.L2.TransformModifyLoop | 3 | CL-07~09 |
| LT-03 | Project.AgentBridge.L2.ImportMetadataLoop | 2 | CL-10~12 |
| LT-04 | Project.AgentBridge.L2.UITool.DragAssetToViewportLoop | 5 | UI-12 |
| LT-05 | Project.AgentBridge.L2.UITool.TypeInFieldLoop | 3 | UI-13 |

---

## 附录 B：统计摘要

| 分类 | 用例数 | 自动化覆盖 |
|------|-------|-----------|
| SV Schema 验证 | 10 | 🟢 全部 |
| BL 编译与加载 | 6 | 🟢 全部 |
| Q L1 查询 | 12 | 🟢 全部 |
| W L1 写接口 | 20 | 🟢 全部 |
| CL L2 闭环 | 12 | 🟢 全部 |
| UI L3 工具 | 13 | 🟢 全部 |
| CMD Commandlet | 8 | 🟢 全部 |
| PY Python 客户端 | 10 | 🟢 全部 |
| ORC Orchestrator | 37 | 🟢 全部 |
| CP Compiler Plane | 31 | 🟢 全部 |
| SS Skills & Specs | 13 | 🟢 全部 |
| GA Gauntlet | 6 | 🟢 全部 |
| E2E 端到端 | 28 | 🟢 全部 |
| **合计** | **206** | **🟢 206 条已登记** |

---

## 附录 C：自动化工具链

| 工具 | 用途 | 覆盖分类 |
|------|------|---------|
| `Build.bat` (UnrealBuildTool) | C++ 编译验证 | BL-01, BL-03 |
| `Scripts/validation/start_ue_editor_project.ps1` | 启动 Editor + RC API 就绪等待 + log 抓取 | BL-02, BL-06 |
| `Scripts/validation/start_ue_editor_cmd_project.ps1` | 启动无头 Commandlet 编辑器 | CMD-01~08, E2E-06, E2E-09 |
| `UnrealEditor-Cmd.exe -run=AgentBridge` | Commandlet 无头执行（-Tool / -RunTests） | CMD, E2E |
| `Automation RunTests` | 仅已打开 Editor 的交互会话执行（非无头基线） | Q, W, CL, UI, BL-04~05 |
| `RunUAT.bat RunUnreal` | Gauntlet CI/CD 全流程 | GA, E2E-07, E2E-10 |
| `AgentBridge.TestConfig.cs` | Gauntlet C# 配置（SmokeTests/AllTests） | GA |
| `AgentBridgeGauntletController` (C++) | Editor 内 Gauntlet 生命周期管理 | GA |
| `python validate_examples.py --strict` | Schema 校验（jsonschema） | SV, E2E-05 |
| `pytest` | Python 单元/集成测试 | SV, PY, ORC |
| `python orchestrator.py` | Orchestrator 主编排（Mock / Channel C） | ORC-24~31, E2E-08 |
| `python compiler_main.py` | Compiler Plane 端到端（GDD→Handoff） | CP-11 |
| `python Scripts/run_greenfield_demo.py` | Greenfield 管线端到端（simulated / bridge_python / bridge_rc_api） | E2E-12~19 |
| `bridge_core.py` + `query_tools.py` | Python Bridge 客户端（三通道） | PY, ORC, E2E-11, E2E-17 |
| Python `import unreal` 脚本 | Channel A（Python Editor Scripting API） | E2E-11 |
| HTTP `curl localhost:30010` | RC API 探测 / Channel B | BL-06, E2E-11 |
