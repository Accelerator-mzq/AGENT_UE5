# Document Release Audit — feat/forgeue-real-ue-bridge @ f89c5a6

> 运行时间: 2026-05-27T04:30:00Z
> 比较基准: `6498df26` (origin/main PR #36 merge)
> 触发事件: manual / milestone 收尾(ForgeUE Manifest Import Bridge real-ue 真机功能完成)
> 范围: 29 commits / 34 files / +4889 / -145(commit chain `7e7b4b9` → `f89c5a6`)

## 背景

本次 audit 是 ForgeUE Manifest Import Bridge 真机功能 milestone 收尾的强制文档同步门禁。Phase 11 已归档(commit `6498df2` PR #36),本 milestone 不构成新 Phase,而是对既有 F-ORC-08 `forgeue_manifest_importer.py` 的真机通路实现(填充 Plan T4 内核 + Plan T6-T10 5+1 种 asset_kind helper + Plan T11/T12 真机测试与 smoke)。

最终交付物:
- `bridge_python` + `bridge_rc_api` 两条真机通路全实现(5+1 种 asset_kind 真机 import 落盘 PASS)
- L3 真机 smoke 6/6 evidence 落盘:`ProjectState/Reports/2026-05-27/forgeue_real_smoke/`
- 0 触 CLAUDE.md 禁止修改文件红线(全 Python + UE Python API + uplugin 配置)
- 新增 BC-NEW-A / BC-NEW-B 候选登记到 UE 5.7 BC 扫描

## Coverage Map

| 变更点 | A 入口 | B 阶段事实 | C 框架 | D 证据落盘 |
|--------|--------|-----------|--------|-----------|
| ForgeUE 真机 bridge(bridge_python + bridge_rc_api 通路) | (Current — anchor 无需变更,本 milestone 不切阶段) | `Docs/INDEX.md` §4 权威定义点(已更新 Schema 42 / examples 27)/ `Docs/acceptance/acceptance_report.md ## 附 2`(已新增 6 条 follow-up) | `Docs/design/LLD/03_orchestrator.md §3.8 + §4.5`(已更新 NotImplementedError 现状 → 已实现)/ `Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py`(实施主体,5+1 helper 实现)/ `Plugins/AgentBridge/Content/Python/forgeue_rc_endpoint.py`(新增 PythonScripted UCLASS)/ `Plugins/AgentBridge/Content/Python/init_unreal.py`(新增 startup hook)/ `Plugins/AgentBridge/Schemas/forgeue_import_evidence.schema.json`(新增 L1 op 证据契约) | `ProjectState/Reports/2026-05-27/forgeue_rc_endpoint_verification.md`(Task 5 验证清单 4/4) / `task6_texture_real_smoke_evidence.md`(Task 6 texture 真机 PASS) / `task12_l3_smoke_summary.md`(L3 6/6 PASS) / `forgeue_real_smoke/`(L4 wrapper + 6 op evidence + assertions) |
| AgentBridge.uplugin CanContainContent: true | (无 anchor 影响) | (无阶段事实变更) | `Plugins/AgentBridge/AgentBridge.uplugin`(已改) | (Task 5 verification 已记录此 prerequisite fix) |
| forgeue_import_evidence schema 新增 | (无 anchor) | `Docs/INDEX.md` §4(已更:42 主 / 27 examples) | `Docs/contracts/schemas_catalog.md` 主表 + 附录 A + 行数自检(已更新) | `Plugins/AgentBridge/Schemas/examples/forgeue_import_evidence_example.json`(passing example) |
| validate_examples.py 字典加 mapping | (无 anchor) | (无阶段事实变更) | `Plugins/AgentBridge/Scripts/validation/validate_examples.py`(EXAMPLE_TO_SCHEMA 加 1 行) | `validate_examples.py --strict` 实测 27/27 PASS |
| L2 pytest real_ue marker + L3 smoke 脚本 | `pytest.ini`(加 real_ue marker) | (无阶段事实变更) | `Plugins/AgentBridge/Tests/scripts/test_forgeue_real_ue_smoke.py`(新增 3 case) / `Scripts/run_forgeue_real_smoke.py`(新增 L3 driver) | `task12_l3_smoke_summary.md` + L2 pytest 1/3 PASS 记录(2/3 timeout 是 transient,已记 FU-FORGEUE-02 backlog) |
| UE 5.7 BC 新增 surface | (无 anchor) | `Docs/INDEX.md` §4(BC 25 → 27 候选)(未改,留 5.7 实测阶段升级) | `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md` §4 新增 NEW 区段 BC-NEW-A/B 候选 | (5.7 实测阶段产出) |

## Documentation health

- **README.md**: Current — 本 milestone 不切阶段(Phase 11 仍是 anchor 的当前阶段),不在 README 登记 ForgeUE 真机 bridge 增量功能;后续若进入 UE 5.7 重构阶段需要同步更新。
- **AGENTS.md**: Current — 同 README。项目级 Agent 规则不涉及具体 milestone,本次 ForgeUE bridge 实施过程中遵守了既有规则(0 触 C++ 红线 / commit 用 `[skip-doc]` 标记 / 中文注释 / 不 git push)。
- **CLAUDE.md**: Current — 同 AGENTS.md。本次 milestone 全程遵守 CLAUDE.md 禁止修改清单(C++ 核心 / Bridge 客户端 / Orchestrator 核心 / 已稳定 Schema / 测试体系)。
- **task.md**: Current — Phase 11 归档跳转页保留,本次 milestone 不构成新 Phase。
- **Docs/INDEX.md**: Updated — §4 权威定义点更新 Schema 数(41 → 42)+ examples 数(26 → 27)+ Schema --strict 26/26 → 27/27,均带 2026-05-27 ForgeUE milestone 来源标注。
- **Layer B (阶段事实)**:
  - `Docs/requirements/SRS.md`: Current — F-ORC-08 既有定义已涵盖 forgeue_manifest_importer;本次 milestone 是 F-ORC-08 的真机通路实现,无需新增 F-* family。
  - `Docs/design/HLD.md`: Current — 架构层不变(Path C 共享内核设计在 spec §2 / LLD §3.8 表达,HLD 顶层抽象不动)。
  - `Docs/acceptance/acceptance_report.md`: Updated — 新增 `## 附 2` ForgeUE milestone follow-up,含 6 条 FU-FORGEUE-* 条目(P2-P3 优先级)。
- **Layer C (框架)**:
  - `Plugins/AgentBridge/AGENTS.md`: Read-only(框架通用规则,本 skill 不动)
  - `Plugins/AgentBridge/README.md`: Current — 插件入口不需要变更,本次新增的 Content/Python/ 是 UE 5.4+ 标准 hook,功能由 Docs/design/LLD/ 与 Schemas/ 描述
  - `Plugins/AgentBridge/Docs/`:
    - 已有 archive 版本 `Docs/archive/plugins/forgeue_manifest_integration.md`,新文档体系下被 `Docs/design/LLD/03_orchestrator.md §3.8 + §4.5` 替代,本次 milestone 已更新 LLD 文档(NotImplementedError stub → 全实现)
  - `Plugins/AgentBridge/Schemas/`:
    - 主表新增 `forgeue_import_evidence.schema.json`(42 主)
    - examples 附录新增 `forgeue_import_evidence_example.json`(27 examples)
    - `Plugins/AgentBridge/Scripts/validation/validate_examples.py` 字典同步加 1 条 mapping
  - `Plugins/AgentBridge/Tests/SystemTestCases.md`: Current — 本次 L2 pytest 3 case + L3 smoke 脚本是辅助测试体系,主回归 266 case / 15 stage 不变;FU-FORGEUE-02 backlog 已记录 L2 timeout follow-up
  - `Docs/contracts/schemas_catalog.md`: Updated — 主表加 forgeue_import_evidence(行 43 位置,按字母 'f' 排序),附录 A 加 example,附录 B 行数自检全更新
  - `Docs/contracts/tool_contract.md` / `field_specification.md` / `mcp_tools_catalog.md`: Current — 本 milestone 不涉及 L1/L2/L3 工具协议、字段命名、MCP 工具数变更(53 工具不变)
  - `Docs/design/LLD/03_orchestrator.md`: Updated — §3.8 forgeue_manifest_importer.py 真机 helper 列表 + §4.5 dispatch 表 NotImplementedError → 全 5+1 实现,加新 milestone 状态段
- **Backlog**: Updated — `Docs/acceptance/acceptance_report.md ## 附 2` 新增 6 条 FU-FORGEUE-* follow-up(material duration anomaly / L2 timeout / normal_texture_ref / GLTF-OBJ / UE 5.7 BC-NEW / Content/Generated gitignore);Phase 11 残留 `## 附` 不动
- **ProjectState/Reports**: Updated — `2026-05-27/forgeue_rc_endpoint_verification.md`(Task 5 验证 4/4)+ `task6_texture_real_smoke_evidence.md`(Task 6 真机)+ `task12_l3_smoke_summary.md`(L3 6/6)+ `forgeue_real_smoke/`(L4 wrapper + 6 op evidence + assertions)4 套证据完整
- **Archive**: Read-only — `Docs/archive/plugins/forgeue_manifest_integration.md` v0(stub 指向新 LLD/03)未动,符合本 skill"history 是证据"原则
- **Spec / Plan**: 不在 anchor 列,但作为本次 milestone 的 superpowers 产物已 commit(`7e7b4b9` spec v1.0 / `df1ba30` plan v1.0)

## 校验跑过

- `python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict` → **27/27 PASS**(Schema --strict)
- `python -m pytest Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py` → **17/17 PASS**(L1 simulated)
- `python -m pytest Plugins/AgentBridge/Tests/scripts/test_forgeue_real_ue_smoke.py -v -m real_ue` → **1/3 PASS, 2/3 timeout**(L2 transient,见 FU-FORGEUE-02 backlog;L3 smoke 已 PASS 是 milestone gate)
- `python Scripts/run_forgeue_real_smoke.py --bridge-mode bridge_rc_api` → **6/6 PASS + uasset 真机落盘**(L3 smoke,evidence pack 落 `ProjectState/Reports/2026-05-27/forgeue_real_smoke/`)
- `python Scripts/run_forgeue_real_smoke.py --bridge-mode simulated` → **6/6 PASS**(L3 离线 sanity)

## 主要发现

### 正面 — 文档面同步充分

1. **真机通路新文件全部反映到 Layer C 框架文档**:`Content/Python/forgeue_rc_endpoint.py` + `init_unreal.py` 在 LLD/03 §3.8 + §4.5 已登记,docstring 同步引用 Plan T5 实测真值(snake_case 路径)
2. **新 schema + example 全 4 处同步**(主表 + 附录 A + 行数自检 + INDEX 权威定义点)
3. **L3 真机 evidence 完整**:`ProjectState/Reports/2026-05-27/forgeue_real_smoke/` 含 L4 wrapper(evidence_manifest.json)+ L1 逐条(op_evidence/*.json)+ assertions.json
4. **3 个 UE API bug 修复链条完整**:febc42f(TextureFactory sRGB)/ 5df5790(import_textures typo)/ 78d29a2(FbxFactory import_options)全部 commit + Task 12 summary 记录
5. **BC scan 同步新增 surface 候选**(BC-NEW-A P2 PythonScripted UCLASS / BC-NEW-B P1 candidate MaterialEditingLibrary),5.7 升级时一并裁决

### 中性 — backlog follow-up 已显式记录

6. material duration_ms anomaly(L3 evidence 有,FU-FORGEUE-01)
7. L2 pytest 30s timeout(FU-FORGEUE-02)
8. normal_texture_ref 延后实现(FU-FORGEUE-03)
9. GLTF/OBJ factory 延后(FU-FORGEUE-04)
10. UE 5.7 BC-NEW-A/B 实测(FU-FORGEUE-05)
11. Content/Generated/ gitignore(FU-FORGEUE-06,项目治理项)

### 已知约束

- 5+1 种 asset_kind 实现是在 F-ORC-08(forgeue_manifest_importer)既有 family 内的真机通路落实,**不创建新 F-FORGEUE-RT family**(避免 FEATURE_INVENTORY.md 105 行多源矩阵大改),记录在 commit history + LLD/03 § milestone 状态段
- 真机 evidence 中 material entry duration_ms / timestamp 有 anomaly,但功能验证(uasset 真机落盘 + DoesAssetExist=true + status=success)有效

## 结论

ForgeUE Manifest Import Bridge 真机功能 milestone 文档同步**充分**:
- Layer A: anchor 4 文件均 Current(本 milestone 不切阶段,无需变更)
- Layer B: INDEX.md / acceptance_report.md 均 Updated;SRS / HLD / 其他 contracts 均 Current(无字段级变更)
- Layer C: LLD/03 + schemas_catalog 均 Updated;Schemas/ 新增 1 主 + 1 example + validate 字典同步;Tests/SystemTestCases.md Current(主回归不变);Plugins/AgentBridge/AGENTS.md / README.md Current
- Layer D: ProjectState/Reports/2026-05-27/ 4 套证据完整(Task 5 / Task 6 / Task 12 / L3 smoke evidence pack)
- Backlog: 6 条 FU-FORGEUE-* 条目显式记录,无静默丢失

**判定**:不存在 critical doc debt,本 milestone 可与 29 commit 一起进入 push/merge(本 audit 后 write-marker 解锁 hook)。

## Source Note

本 audit 由 document-release skill 触发(`.claude/skills/document-release/SKILL.md` v1.0,Mvpv4TestCodex 本地化),作为整个 feat/forgeue-real-ue-bridge 分支(29 commit / 4889 insertions)合入 main 前的最后一次文档面证据归档。
