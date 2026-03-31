# AgentBridge 系统测试用例总表

> 来源：task.md（v0.3 编码 Agent 任务清单）中的验收标准与验证步骤
> 最后更新：2026-03-31
> 维护者：msc

---

## 目录

- [1. 测试分类说明](#1-测试分类说明)
- [2. Schema 验证（SV）](#2-schema-验证sv)
- [3. 编译与加载（BL）](#3-编译与加载bl)
- [4. L1 查询接口（Q）](#4-l1-查询接口q)
- [5. L1 写接口（W）](#5-l1-写接口w)
- [6. L2 闭环验证（CL）](#6-l2-闭环验证cl)
- [7. L3 UI 工具（UI）](#7-l3-ui-工具ui)
- [8. Commandlet 无头执行（CMD）](#8-commandlet-无头执行cmd)
- [9. Python 客户端（PY）](#9-python-客户端py)
- [10. Orchestrator 编排（ORC）](#10-orchestrator-编排orc)
- [11. Gauntlet CI/CD（GA）](#11-gauntlet-cicdga)
- [12. 端到端集成（E2E）](#12-端到端集成e2e)
- [附录 A：UE5 Automation Test ID 速查表](#附录-aue5-automation-test-id-速查表)
- [附录 B：统计摘要](#附录-b统计摘要)
- [附录 C：自动化工具链](#附录-c自动化工具链)

---

## 1. 测试分类说明

| 前缀 | 分类 | 环境要求 | 自动化方式 |
|------|------|----------|-----------|
| SV | Schema 验证 | Python | `python validate_examples.py --strict` / pytest |
| BL | 编译与加载 | UE5 + VS2022 | `Build.bat` + `start_ue_editor_project.ps1` + HTTP 探测 |
| Q | L1 查询接口 | UE5 Editor + RC API | UE5 Automation Test (T1-01~07) |
| W | L1 写接口 | UE5 Editor + RC API | UE5 Automation Test (T1-08~11) |
| CL | L2 闭环验证 | UE5 Editor | UE5 Automation Spec (LT-01~03) |
| UI | L3 UI 工具 | UE5 Editor + Automation Driver | UE5 Automation Test (T1-12~15) + Spec (LT-04~05) |
| CMD | Commandlet | UE5 命令行（无头） | `UnrealEditor-Cmd.exe -run=AgentBridge` + `start_ue_editor_cmd_project.ps1` |
| PY | Python 客户端 | Python | pytest / `ast.parse` / Mock 模式调用 |
| ORC | Orchestrator | Python + UE5 | pytest / `orchestrator.py --channel mock` |
| GA | Gauntlet CI/CD | UE5 + UAT | `RunUAT.bat RunUnreal -test=SmokeTests/AllTests` |
| E2E | 端到端集成 | 全栈 | 多步流水线（Schema→Cmd→Gauntlet→三通道脚本） |

> 全部 134 条用例均已实现自动化。证据见 `Plugins/AgentBridge/reports/` 目录。

---

## 2. Schema 验证（SV）

> 来源：TASK 02, TASK 18

| 编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 自动化命令 |
|------|---------|---------|---------|---------|-----------|
| SV-01 | 全部 example 通过 Schema 校验 | 文件就位 | `python validate_examples.py --strict` | exit code 0, Passed=8(或10) | `python Scripts/validation/validate_examples.py --strict` |
| SV-02 | 全部 JSON 文件语法合法 | 文件就位 | 遍历 Schemas/**/*.json 做 json.load | 全部 OK，无 FAIL | `pytest Tests/scripts/test_schema_validation.py::TestSchemaValidation::test_sv02` |
| SV-03 | Schema 文件数量一致性 | TASK 01 完成 | 统计 Schemas/ 下文件数 | 初始 24 个，扩展后 28 个 | `pytest Tests/scripts/test_schema_validation.py::TestSchemaValidation::test_sv03` |
| SV-04 | example→Schema 映射完整 | 文件就位 | 检查每个 example 有对应 Schema | 全部 example 有映射 | `pytest Tests/scripts/test_schema_validation.py::TestSchemaValidation::test_sv04` |
| SV-05 | 新增 example 不破坏旧 example | TASK 18 扩展后 | 运行 validate_examples.py | 原 8 个仍通过，新增也通过 | `python Scripts/validation/validate_examples.py --strict` |

---

## 3. 编译与加载（BL）

> 来源：TASK 03
> 自动化基础设施：`Build.bat`（UBT）+ `Scripts/validation/start_ue_editor_project.ps1`

| 编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 自动化命令 |
|------|---------|---------|---------|---------|-----------|
| BL-01 | Plugin 编译零 error | VS2022 / UE5.5.4 | UBT 编译 | 零 error（允许引擎自身 warning） | `Build.bat Mvpv4TestCodexEditor Win64 Development -Project=...uproject` |
| BL-02 | Plugin 加载日志 | Editor 启动 | grep Editor log | 出现 `[AgentBridge] Plugin loaded, version 0.3.0` | `start_ue_editor_project.ps1` → 检查 `Saved/Logs/*.log` |
| BL-03 | BridgeTypes.h 可被外部引用 | BL-01 通过 | 编译含 `#include "BridgeTypes.h"` 的模块 | 编译通过 | BL-01 的 UBT 编译隐含验证（AgentBridgeTests 引用 BridgeTypes.h） |
| BL-04 | EBridgeStatus 枚举完整 | BL-01 通过 | UE5 Automation Test 检查枚举值 | 5 个值：Success/Warning/Failed/Mismatch/ValidationError | `Automation RunTests Project.AgentBridge.L1` |
| BL-05 | EBridgeErrorCode 枚举完整 | BL-01 通过 | UE5 Automation Test 检查枚举值 | 12 个值（含 3 个 L3 专用） | `Automation RunTests Project.AgentBridge.L1` |
| BL-06 | Remote Control API 可用 | Editor 运行 | HTTP GET 探测 | 返回有效 JSON | `start_ue_editor_project.ps1` → `curl http://localhost:30010/remote/info` |

---

## 4. L1 查询接口（Q）

> 来源：TASK 04, TASK 07
> UE5 Automation Test 编号：T1-01 ~ T1-07
> 自动化命令：`Automation RunTests Project.AgentBridge.L1.Query` 或 `UnrealEditor-Cmd.exe -run=AgentBridge -RunTests=Project.AgentBridge.L1`

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
> 自动化命令：`Automation RunTests Project.AgentBridge.L1.Write` 或 `UnrealEditor-Cmd.exe -run=AgentBridge -RunTests=Project.AgentBridge.L1`

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
> 自动化命令：`Automation RunTests Project.AgentBridge.L2` 或 `UnrealEditor-Cmd.exe -run=AgentBridge -RunTests=Project.AgentBridge.L2`

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
> 自动化命令：`Automation RunTests Project.AgentBridge.L1.UITool` + `Automation RunTests Project.AgentBridge.L2.UITool`
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

> 证据：`reports/task06_evidence_2026-03-28/` 下含每个用例的 `.log` + `_report.json`

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

> 证据：`reports/task09_evidence_2026-03-28/`

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

> 证据：`reports/task10_evidence_2026-03-28/`

### Plan Generator (TASK 11)

| 编号 | 用例名称 | 测试方式 | 预期结果 |
|------|---------|---------|---------|
| ORC-07 | 全新场景→全部 CREATE | `generate_plan(spec, existing_actors=[])` | semantic=CREATE, ui_tool=UI_TOOL |
| ORC-08 | 已存在 Actor→UPDATE | `generate_plan(spec, existing_actors=[...])` | existing_actor_path 正确 |
| ORC-09 | ui_tool Actor 不受 existing 影响 | existing 中含 ui_tool actor | 始终 UI_TOOL |
| ORC-10 | plan entry 字段完整 | 检查返回结构 | 含 actor_spec/action/execution_method/existing_actor_path/reason |

> 证据：`reports/task11_evidence_2026-03-28/`

### Verifier (TASK 12)

| 编号 | 用例名称 | 测试方式 | 预期结果 |
|------|---------|---------|---------|
| ORC-11 | verify_transform 精确匹配 | 输入完全相同的 transform | status=success, mismatches=[] |
| ORC-12 | verify_transform 超出容差 | location 偏差 > 0.01 | status=mismatch, mismatches 含字段名和值 |
| ORC-13 | L3 宽容差（50cm 偏差） | L3_TOLERANCES 下 50cm 偏差 | 在 100cm 容差内→success |
| ORC-14 | checks 列表字段完整 | 检查返回的 checks 数组 | field/expected/actual/delta/tolerance/pass |
| ORC-15 | verify_actor_state 自动选择容差 | 分别传 semantic 和 ui_tool | semantic→DEFAULT, ui_tool→L3 |

> 证据：`reports/task12_evidence_2026-03-28/`

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

> 证据：`reports/task13_evidence_2026-03-28/`

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

> 证据：`reports/task14_evidence_2026-03-28/`

---

## 11. Gauntlet CI/CD（GA）

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

> 证据：`reports/task16_evidence_2026-03-28/` 含 `task16_smoke_rununreal_*.log` + `task16_alltests_rununreal_*.log`

---

## 12. 端到端集成（E2E）

> 来源：TASK 15, TASK 19
> 自动化方式：多步流水线，每步独立可执行

### L3 Functional Test (TASK 15)

| 编号 | 用例名称 | 自动化命令 | 预期结果 |
|------|---------|-----------|---------|
| E2E-01 | FTEST_WarehouseDemo 可发现 | `RunUAT.bat RunUnreal -test=AllTests`（Gauntlet 自动发现） | Session Frontend 可见 |
| E2E-02 | 5 个内置 Actor 全部 Spawn→Verify→PASS | Gauntlet AllTests 自动运行 | FinishTest(Succeeded), 5/5 actors verified |
| E2E-03 | bUndoAfterTest 清理无残留 | Gauntlet AllTests 自动运行 | CleanUp 执行 Undo |
| E2E-04 | L1+L2+L3 联合运行无冲突 | `Automation RunTests Project.AgentBridge` 或 Gauntlet AllTests | 全部通过 |

> 证据：`reports/task15_evidence_2026-03-28/`

### 完整 Demo 验证 (TASK 19, 7 步)

| 编号 | 用例名称 | 验证步骤 | 自动化命令 | 预期结果 |
|------|---------|---------|-----------|---------|
| E2E-05 | Schema 全量验证 | Step 1/7 | `python Scripts/validation/validate_examples.py --strict` | 10/10 pass, exit 0 |
| E2E-06 | L1+L2 全绿 | Step 2/7 | `UnrealEditor-Cmd.exe ... -ExecCmds="Automation RunTests Project.AgentBridge.L1;Quit" -NullRHI` | ≥15 绿灯, SKIP 仅限 UITool/Import |
| E2E-07 | L3 Functional Test | Step 3/7 | `RunUAT.bat RunUnreal -test=AllTests`（含 FTEST_WarehouseDemo） | 5 Actors PASS, 或无 map 时 SKIP |
| E2E-08 | Orchestrator E2E | Step 4/7 | `python orchestrator.py --channel cpp_plugin --spec scene_spec.yaml --report report.json` | 4 actors (2 semantic+2 ui_tool), 报告含 overall_status |
| E2E-09 | Commandlet 无头执行 | Step 5/7 | `UnrealEditor-Cmd.exe -run=AgentBridge -Tool=GetCurrentProjectState -NullRHI` | Mode 3 JSON+exit 0; Mode 2 L1+exit 0 |
| E2E-10 | Gauntlet CI/CD | Step 6/7 | `RunUAT.bat RunUnreal -test=SmokeTests` + `-test=AllTests` | SmokeTests exit 0; AllTests exit 0 |
| E2E-11 | 三通道一致性 | Step 7/7 | Python 脚本：Channel A(`import unreal`) + B(`CPP_PLUGIN`) + C(`REMOTE_CONTROL`) 查询同一 Actor | transform 一致, `consistent: true` |

> 证据：`reports/task19_evidence_2026-03-27/` 含 step1~step7 全部日志 + JSON

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
| SV Schema 验证 | 5 | 🟢 全部 |
| BL 编译与加载 | 6 | 🟢 全部 |
| Q L1 查询 | 12 | 🟢 全部 |
| W L1 写接口 | 20 | 🟢 全部 |
| CL L2 闭环 | 12 | 🟢 全部 |
| UI L3 工具 | 13 | 🟢 全部 |
| CMD Commandlet | 8 | 🟢 全部 |
| PY Python 客户端 | 10 | 🟢 全部 |
| ORC Orchestrator | 31 | 🟢 全部 |
| GA Gauntlet | 6 | 🟢 全部 |
| E2E 端到端 | 11 | 🟢 全部 |
| **合计** | **134** | **🟢 134/134 (100%)** |

---

## 附录 C：自动化工具链

| 工具 | 用途 | 覆盖分类 |
|------|------|---------|
| `Build.bat` (UnrealBuildTool) | C++ 编译验证 | BL-01, BL-03 |
| `start_ue_editor_project.ps1` | 启动 Editor + RC API 就绪等待 + log 抓取 | BL-02, BL-06 |
| `start_ue_editor_cmd_project.ps1` | 启动无头 Commandlet 编辑器 | CMD-01~08, E2E-06, E2E-09 |
| `UnrealEditor-Cmd.exe -run=AgentBridge` | Commandlet 无头执行（-Tool / -RunTests） | CMD, E2E |
| `Automation RunTests` | UE5 Editor 内 Automation Test 执行 | Q, W, CL, UI, BL-04~05 |
| `RunUAT.bat RunUnreal` | Gauntlet CI/CD 全流程 | GA, E2E-07, E2E-10 |
| `AgentBridge.TestConfig.cs` | Gauntlet C# 配置（SmokeTests/AllTests） | GA |
| `AgentBridgeGauntletController` (C++) | Editor 内 Gauntlet 生命周期管理 | GA |
| `python validate_examples.py --strict` | Schema 校验（jsonschema） | SV, E2E-05 |
| `pytest` | Python 单元/集成测试 | SV, PY, ORC |
| `python orchestrator.py` | Orchestrator 主编排（Mock / Channel C） | ORC-24~31, E2E-08 |
| `bridge_core.py` + `query_tools.py` | Python Bridge 客户端（三通道） | PY, ORC, E2E-11 |
| Python `import unreal` 脚本 | Channel A（Python Editor Scripting API） | E2E-11 |
| HTTP `curl localhost:30010` | RC API 探测 / Channel B | BL-06, E2E-11 |
