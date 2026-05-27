# Document Release Audit — chore/forgeue-followup-batch @ <HEAD>

> 运行时间: 2026-05-27T03:05:00Z
> 比较基准: `6d3c63b` (origin/main,PR #38 merge)
> 触发事件: follow-up batch 收尾(7 条 FU-FORGEUE-* 闭环 + 真机验证)
> 范围: 5 commits / ~14 files / +500 / -80(commit chain `1423966` → audit/marker commit)

## 背景

PR #38 合并(`6d3c63b`)后,msc 决定"能做的都做"7 条 follow-up(FU-03/04/06/07/08/09/10),3 条等 UE 5.7 实测(FU-01/02/05)。本 batch 实施 7 条 follow-up + 真机验证 Phase 3,产出 5 commit。

## Coverage Map

| 变更点 | A 入口 | B 阶段事实 | C 框架 | D 证据落盘 |
|--------|--------|-----------|--------|-----------|
| FU-06 .gitignore `Content/Generated/` | (无 anchor 影响) | (无阶段事实) | `.gitignore` | 本 audit |
| FU-07 test section header 风格 | (无 anchor) | (无阶段事实) | `test_forgeue_manifest_importer.py` | 本 audit |
| FU-08 magic string 提常量 | (无 anchor) | (无阶段事实) | `Scripts/run_forgeue_real_smoke.py` 5 个 module-level 常量 | 本 audit |
| FU-09 material expression helper | (无 anchor) | (无阶段事实) | `forgeue_manifest_importer.py` 新增 `_add_material_constant_expression` | 本 audit + L3 真机 material 创建 PASS |
| FU-10 `_now_iso_utc` 抽 utils | (无 anchor) | (无阶段事实) | 新增 `_time_utils.py`(orchestrator/ 下,避 `bridge/` 红线)+ importer + smoke 脚本两处副本删 | 本 audit |
| FU-03 normal_texture_ref | (无 anchor) | `Docs/acceptance/acceptance_report.md ## 附 2`(标 [CLOSED]) | fixture 加 tex_normal.png + manifest 加 entry + `_creator_path_material` Normal 分支 + L1 测试 6→7 | `ProjectState/Reports/2026-05-27/task_followup_batch_l3_smoke_summary.md`(L3 真机 material 含 Normal PASS) |
| FU-04 OBJ(部分闭环) | (无 anchor) | `Docs/acceptance/acceptance_report.md ## 附 2`(标 [PARTIAL]) | fixture 加 mesh_cube_obj.obj + manifest 加 entry + `_build_mesh_factory` OBJ 分支 + L1 测试 7→8 | task_followup_batch_l3_smoke_summary.md(OBJ 真机失败,UE 5.5 binding 无 unreal.ObjFactory,代码层闭环) |
| acceptance_report ## 附 2 更新 | (无 anchor) | `Docs/acceptance/acceptance_report.md`(7 条标 [CLOSED]/[PARTIAL]) | (无 framework) | 本 audit |

## Documentation health

- **README.md**: Current — backlog 闭环不切阶段
- **AGENTS.md**: Current
- **CLAUDE.md**: Current
- **task.md**: Current
- **Docs/INDEX.md**: Current — 本 batch 不引入新 schema / 不改 MCP 工具数 / 不改测试主回归数
- **Layer B**:
  - `Docs/acceptance/acceptance_report.md ## 附 2`: Updated — 7 条 FU-FORGEUE-* 标 [CLOSED]/[PARTIAL] + 详细实施事实
- **Layer C**:
  - `Plugins/AgentBridge/Scripts/orchestrator/_time_utils.py`: 新增(FU-10)
  - `Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py`: 多处更新(FU-09 helper + FU-03 Normal + FU-10 import 改 + FU-04 OBJ 分支)
  - `Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py`: L1 测试断言 6→7→8(对应 FU-03 + FU-04 fixture 扩)
  - `Plugins/AgentBridge/Tests/scripts/generate_forgeue_fixture_payload.py`: 加 normal PNG + cube OBJ 生成
  - `Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/`: manifest.json 7→8 entry + payload/tex_normal.png + payload/mesh_cube_obj.obj
  - `Scripts/run_forgeue_real_smoke.py`: FU-08 5 常量 + FU-10 import 改
  - `Docs/contracts/schemas_catalog.md`: Current(本 batch 无新 schema)
  - `Docs/design/LLD/03_orchestrator.md`: Current(本 batch 是同一 family 内 helper 优化,LLD §3.8 表达不变)
  - `.gitignore`: Updated(FU-06 加 `Content/Generated/`)
- **Backlog**: Updated — 7 条 [CLOSED]/[PARTIAL] 显式标记;剩余 3 条 FU-01/02/05 仍 open 等 UE 5.7
- **ProjectState/Reports**: Updated — 本 audit + task_followup_batch_l3_smoke_summary.md
- **Archive**: Read-only

## 校验

- `python -m pytest Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py` → 17/17 PASS(L1,Phase 1/2A/2B/3A/3B 各跑 1 次都 PASS)
- `python Scripts/run_forgeue_real_smoke.py --bridge-mode simulated` → 8/8 PASS(L3 simulated,Phase 3B 后 fixture 8 entry)
- `python Scripts/run_forgeue_real_smoke.py --bridge-mode bridge_rc_api` → **7/8 PASS + 1/8 failed**(OBJ failed:UE 5.5 binding 无 `unreal.ObjFactory`;非代码 bug,记 FU-04 PARTIAL)
- `python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict` → 27/27 PASS(本 batch 不引入新 schema)

## 主要发现

### 正面
- 6 个 follow-up 完整闭环:FU-03/06/07/08/09/10
- 真机验证证明 FU-09 helper + FU-03 Normal expression 工作正确(material asset 创建 PASS,Normal expression 连对)
- FU-10 _time_utils.py 公共 utils 抽出后 importer + smoke 脚本无回归

### 中性 — FU-04 OBJ 部分闭环
- 代码层完整:fixture + manifest + `_build_mesh_factory` OBJ 分支 + L1 测试都更新
- UE 5.5 Python binding 实测限制:`unreal.ObjFactory` 不存在 → `getattr` 返 None → `_evidence_failure`
- 代码的容错链工作完整正确(implementer 设计的 fallback 不阻塞其他 asset)
- 已记 acceptance_report.md ## 附 2 FU-04 [PARTIAL] + 3 个升级 Follow-up 路径

### 已知 OK
- FU-01/02/05 仍 open(等 UE 5.7 实测,符合原 milestone 设计)
- GLTF/GLB 仍完全 follow-up(FU-04 升级条款 c)

## 结论

7 个 follow-up 中 6 个 [CLOSED] + 1 个 [PARTIAL],真机 L3 smoke 7/8 success(OBJ failed = UE binding 限制非代码 bug)。可合 main。
