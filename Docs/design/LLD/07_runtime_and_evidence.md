# LLD/07 — 运行时、证据落盘、测试、Hooks、输入与 Demo 子系统详细设计

> 版本: v1 (2026-05-26)
> 范围: 运行时执行域(UE Editor / Standalone Staged)+ 证据/报告/Run Workspace 落盘 + C++/Python 测试体系 + document-release Git Hooks + ProjectInputs GDD/Presets + 4 个可运行 Demo + 治理校验脚本族,共 6 个相关子域。
> 上游: `Docs/design/HLD.md` §3/§6 + `Docs/requirements/SRS.md` §3.7 + `Docs/FEATURE_INVENTORY.md` F-RT/TST/HOOK/INP/DEMO/VAL
> 契约: `Docs/contracts/schemas_catalog.md`(evidence_manifest + run_comparison + batch_manifest)+ `Docs/contracts/tool_contract.md`
> UE 版本: 当前 5.5.4 → 目标 5.7

## 1. 模块概述

本 LLD 不对应单一代码模块,而是把 SRS §3.7 一次性覆盖的 6 个跨域子系统集中落实:**运行时执行域**(F-RT-01..05)负责 UE Editor 在线引导 + Standalone Staged 脱机运行,并把每次运行的副作用收敛到 `ProjectState/` 下三个分轨目录(Evidence / Reports / runs);**测试体系**(F-TST-01..04)以 C++ Automation L1/L2/L3 + Gauntlet Controller 为引擎内闭环、以 `run_system_tests.py` 11 个 Stage 为引擎外编排,系统测试 TOTAL_CASES = 266(Phase 11 后从 FEATURE_INVENTORY 早期登记的 240 扩到 266),C++ Automation 独立 ~26 条测试不计入 266;**治理 Hook**(F-HOOK-01/02)用 `doc_release_gate.py` 跨平台门禁脚本 + `install_git_hooks.py` 模板安装器实现 commit/push 前文档释放强制,逃生通道为 `[skip-doc]` 标记 + trivial 白名单 + `--no-verify`;**输入实例**(F-INP-01/02)以 `ProjectInputs/GDD/{boardgame_tictactoe_v1, GDD_MonopolyGame, jrpg_turn_based_v1}.md` + `ProjectInputs/Presets/{compiler_profile, mode_override}.yaml` 给上游 Compiler 提供 3 套 GDD + 2 套预设,Profile 默认值不可改,所有改动通过 mode_override 实现以便回溯;**可运行 Demo**(F-DEMO-02/03)由 `Scripts/run_{greenfield,brownfield,boardgame_playable,jrpg_turn_based}_demo.py` 4 个脚本 + Phase 7 P1 收敛入口 + Monopoly 资产生成 + Skills 同步辅助 6 个脚本组成;**治理校验**(F-VAL-01..03)聚焦 Plugin 发布 staging、Schema 校验(`--strict` 26/26 通过)、legacy Automation token 检测、Functional Map 生成与 Editor 证据捕获。F-* IDs 计 RT 5 + TST 4 + HOOK 2 + INP 2 + DEMO 2 + VAL 3 = 18 行,完全对齐 SRS §3.7 表头。6 子域共用 `ProjectState/` 落盘根目录但各占独立子目录,共用 `Plugins/AgentBridge/Scripts/` + `Scripts/` 双 import 根,共用 Run ID 与日期两套索引维度。

## 2. 内部分层

### 2.1 运行时 + 证据落盘层(F-RT-01..05)

| F-* ID | 子层角色 | 主体路径(文件 / 目录) | 落盘位置 |
|---|---|---|---|
| F-RT-01 | UE Editor 在线引导关卡(Editor game,Compiler+Bridge 链路) | `Scripts/validation/start_ue_editor_{cmd_project,project}.ps1` + Editor 内 `AgentBridgeSubsystem` | 直接读写 Editor 进程内 World |
| F-RT-02 | Standalone Staged 运行时(UAT BuildCookRun 产物) | `Plugins/AgentBridge/Tests/scripts/task14a_phase11_standalone_smoke.py`:250 + 4 个 demo 脚本 | `ProjectState/StagedBuilds/<game_or_task>/` |
| F-RT-03 | Evidence 落盘(工具执行级证据) | `Scripts/validation/capture_editor_evidence.py`:373 | `ProjectState/Evidence/<phase_name>/` 子目录 |
| F-RT-04 | Reports 生成(系统测试 + Demo + Phase 验收) | `Plugins/AgentBridge/Tests/run_system_tests.py`:2913 行 Stage 报告聚合 | `ProjectState/Reports/<YYYY-MM-DD>/` |
| F-RT-05 | Run Workspace 隔离(每 run_id 独立 workspace) | Orchestrator 主链 `Compiler/stages/*` 产出 `run_id` + Demo 脚本入参 | `ProjectState/runs/<run_id>/{input,output,snapshots,runtime_config}/` |

> 同时管理但不属于"运行时"的稳定子目录:`ProjectState/{batches,Handoffs,RuntimeConfigs,Snapshots}/` 由 Orchestrator(LLD 03)与 Compiler(LLD 04)消费,本 LLD 仅记录写入路径约束(见 §6)。这五大 ProjectState 子目录的写入入口对应关系:Evidence 由 capture 工具与 MCP `mcp_evidence_*` 写;Reports 由系统测试编排器与 demo 脚本写;runs 由 Compiler 主链 Stage 1 创建并贯穿全 Stage;Handoffs 由 `compiler.handoff.serialize_handoff` 与人工审核流程写;Snapshots / StagedBuilds 由 demo + Standalone Smoke 写;batches 由 F-GOV-04 promote 流程在 Phase 7 写入 baseline batch。13 个子目录中 `phase8 / phase10 / phase11_task09_refactor_session` 三个为历史保留,只读不写。

### 2.2 测试 + Hooks + Inputs + Demos + Validation 层

| F-* ID | 子域 | 主体文件 | 角色一句话 |
|---|---|---|---|
| F-TST-01 | C++ L1 测试族(3 份) | `Plugins/AgentBridge/AgentBridgeTests/Source/AgentBridgeTests/Private/{L1_QueryTests, L1_WriteTests, L1_UIToolTests}.cpp` | Subsystem 单接口断言,Editor 模式运行 |
| F-TST-02 | C++ L2 闭环 Spec 测试(2 份) | `Plugins/AgentBridge/.../Private/{L2_ClosedLoopSpecs, L2_UIToolClosedLoopSpec}.spec.cpp` | 写→读回→容差比对→Undo→再读回 BDD 闭环 |
| F-TST-03 | C++ L3 + Gauntlet Controller | `Plugins/AgentBridge/.../Private/{L3_FunctionalTestActor, AgentBridgeGauntletController}.{h,cpp}` | 关卡级 FunctionalTest Actor + Gauntlet 外控 |
| F-TST-04 | 系统测试套件(11 Stage / 240+ 用例) | `Plugins/AgentBridge/Tests/run_system_tests.py`:2913 + `scripts/` 19 脚本 + `SystemTestCases.md` + `fixtures/` | Python 编排 + per-Stage helper + 用例登记表 |
| F-HOOK-01 | document-release gate(跨平台) | `Scripts/hooks/doc_release_gate.py`:398 | check / write-marker / notify 三 CLI + marker TTL 24h |
| F-HOOK-02 | Git hooks 安装 + CC 通知 | `Scripts/hooks/{install_git_hooks.py, cc_notify_wrapper.py, pre-commit, pre-push, commit-msg}` | 把 3 个 hook 模板复制到 `.git/hooks/` |
| F-INP-01 | GDD 实例族(3 GDD) | `ProjectInputs/GDD/{boardgame_tictactoe_v1, GDD_MonopolyGame, jrpg_turn_based_v1}.md` | Compiler Intake 的源头 markdown |
| F-INP-02 | Compiler Profile / Mode Override 预设 | `ProjectInputs/Presets/{compiler_profile, mode_override}.yaml` | 编译器开关 + 模式路由覆盖 |
| F-DEMO-02 | 可运行游戏 demo 族 | `Scripts/run_{greenfield,brownfield,boardgame_playable,jrpg_turn_based}_demo.py` + `Scripts/run_phase7_p1_convergence.py` | Compiler→Orchestrator→UE 端到端入口 |
| F-DEMO-03 | 资产生成 / Skills 同步辅助 | `Scripts/phase8_generate_monopoly_assets.py` + `Scripts/sync_skills.py` | 批量造 Monopoly Asset + 同步 SkillTemplates |
| F-VAL-01 | Plugin/Project 治理校验脚本族 | `Plugins/AgentBridge/Scripts/validation/{stage_plugin_release.ps1, validate_no_legacy_automation_entrypoints.ps1}` + `Scripts/validation/phase7_governance_audit.py` | 发布前 staging + 对 legacy token 扫描 + 治理审计 |
| F-VAL-02 | Schema 校验脚本族 | `Plugins/AgentBridge/Scripts/validation/{validate_examples.py, test_handoff_schema.py}` | `--strict` 模式 26/26 通过 |
| F-VAL-03 | Evidence / Functional Map 生成 | `Scripts/validation/{capture_editor_evidence.py, create_task15_functional_map.py}` | Editor 内截图证据 + Task15 FTEST 地图自动建图 |

## 3. 关键类/函数签名

> 仅列与运行编排、证据落盘、Hook 决策、Demo 入口、测试 fixture 强相关的签名,后置 1 行中文用途。

**系统测试编排 — `Plugins/AgentBridge/Tests/run_system_tests.py` (2913 行):**

```python
PROJECT_ROOT = os.path.abspath(os.path.join(PLUGIN_ROOT, '..', '..'))   # 测试套件 PROJECT_ROOT 锚点
UPROJECT_PATH = os.path.join(PROJECT_ROOT, 'Mvpv4TestCodex.uproject')   # 唯一 uproject 路径
PS_EDITOR_CMD / PS_EDITOR_GUI = Scripts/validation/start_ue_editor_{cmd_project, project}.ps1
def find_engine_root() -> str:
    # 探测 E:\Epic Games\UE_5.5 / E:\GameProject\UE5-SourceCode-5.5.4 / C:\...UE_5.5 / D:\...UE_5.5(BC-025 命中)
def run_command(cmd, timeout=...) -> tuple[int, str, str]:
    # 通用子进程包装,捕获 stdout/stderr 并落 Reports/<date>/
def parse_args() -> argparse.Namespace:
    # --interactive / --stage=N / --engine-root / --report-dir / --no-editor
# Stage 1..11 各自的 run_stage_N 入口函数(SV/BL/L1L2L3/CMD/PY/ORC/CP+SS/GA/E2E/MCP/P11,共 11 类)
```

**Standalone Staged Smoke — `Plugins/AgentBridge/Tests/scripts/task14a_phase11_standalone_smoke.py`:**

```python
UAT_PATH = Path(r"E:\Epic Games\UE_5.5\Engine\Build\BatchFiles\RunUAT.bat")   # BC-025 命中(line 25)
STAGED_ROOT = ProjectState/StagedBuilds/task14a_standalone_runtime_smoke
def run_command(command, log_path, cwd, timeout=None) -> int:                 # subprocess + 日志落盘
def ensure_dir(path) -> Path:                                                 # 幂等 mkdir
```

**document-release Gate — `Scripts/hooks/doc_release_gate.py` (398 行):**

```python
@dataclass(frozen=True)
class Marker:                                              # branch + head_sha + staged_files_hash + audit_evidence_path + timestamp
def write_marker_file(marker_dir, marker) -> None:         # 落 .git 外部目录,跨平台
def read_marker_file(marker_dir, branch) -> Optional[Marker]:
def compute_staged_files_hash(staged_paths) -> str:        # 排序后 sha256
def validate_evidence(path) -> tuple[bool, str]:           # 必须含 ## Coverage Map + ## Documentation health 两区块
def check_marker(*, marker_dir, branch, head_sha, staged_paths, now, skip_staged_check=False) -> CheckResult:
    # HEAD 校验 + staged hash 校验(commit)/ 仅 HEAD 校验(push)+ 24h TTL + evidence 存在性
def is_trivial(staged_paths) -> bool:                      # 全部命中 Saved/ Intermediate/ DerivedDataCache/ Binaries/ Build/ .codex/ 或 .lock
def is_skip_doc_commit(message) -> bool:                   # 首行 [skip-doc] 前缀(允许前置空白)
MARKER_TTL = timedelta(hours=24)
TRIVIAL_PREFIXES = ("Saved/", "Intermediate/", "DerivedDataCache/", "Binaries/", "Build/", ".codex/")
```

**Git Hooks 安装器 — `Scripts/hooks/install_git_hooks.py` (47 行):**

```python
HOOK_NAMES = ("pre-commit", "pre-push", "commit-msg")
def main() -> int:                                          # 把 Scripts/hooks/<name> 复制到 .git/hooks/,POSIX chmod +x
```

**Demo 入口(F-DEMO-02):**

```python
# Scripts/run_greenfield_demo.py:25
def run_greenfield_demo(bridge_mode: str = "simulated") -> None:                      # simulated / bridge_python / bridge_rc_api
# Scripts/run_brownfield_demo.py / run_boardgame_playable_demo.py / run_jrpg_turn_based_demo.py 类似入口
# Scripts/run_phase7_p1_convergence.py — Phase 7 P1 治理回归收敛
# Scripts/phase8_generate_monopoly_assets.py — Monopoly Genre Pack 资产批量生成(F-DEMO-03)
# Scripts/sync_skills.py — SkillTemplates 同步辅助(F-DEMO-03)
```

**Validation 脚本族(F-VAL-01..03):**

```powershell
# Plugins/AgentBridge/Scripts/validation/stage_plugin_release.ps1 (358 行)
#   把 AgentBridge 插件打包到 release staging 目录,跑 -strict schema 校验 + legacy token 扫描
# Plugins/AgentBridge/Scripts/validation/validate_no_legacy_automation_entrypoints.ps1 (124 行)
#   扫描代码库内是否还有 `RunUAT RunAutomationTests` legacy token(BC-021 相关)
```

```python
# Plugins/AgentBridge/Scripts/validation/validate_examples.py (473 行)
def main() -> int:                                          # --strict 模式 26/26 通过,Schema example fixture 全量校验
# Plugins/AgentBridge/Scripts/validation/test_handoff_schema.py (125 行)
def test_reviewed_handoff_v2() -> None:                     # reviewed_handoff_v2.schema.json 正向 / 反向 fixture
# Scripts/validation/phase7_governance_audit.py (359 行)
def build_execution_governance_entry(entry_name, execution_report_path, ...) -> dict:
def load_json_file / load_yaml_file -> dict:                 # 治理审计三联校验(execution_report + snapshot manifest + promotion_status)
# Scripts/validation/capture_editor_evidence.py (373 行)
def get_evidence_root(phase_name, project_root=None) -> str: # ProjectState/Evidence/<phase>
# 通过 RC HTTP 调用 AgentBridgeSubsystem 截屏 + hash + manifest 落盘
# Scripts/validation/create_task15_functional_map.py
#   UE -ExecutePythonScript= 入口,创建 /Game/Tests/FTEST_WarehouseDemo + 放置 AAgentBridgeFunctionalTest
```

**C++ AgentBridgeTests 关键类(F-TST-01..03):**

```cpp
// L1_QueryTests.cpp / L1_WriteTests.cpp / L1_UIToolTests.cpp
static UAgentBridgeSubsystem* GetQueryTestSubsystem(FAutomationTestBase& Test);  // Editor Subsystem 取用,Unity Build 下用 static 避免冲突
// L2_ClosedLoopSpecs.spec.cpp / L2_UIToolClosedLoopSpec.spec.cpp
const float LocationTolerance = 0.01f;  // cm   RotationTolerance = 0.01f;  // deg   ScaleTolerance = 0.001f;
BEGIN_DEFINE_SPEC(...)  // BDD 风格,写→读回→容差→Undo→再读回
// L3_FunctionalTestActor.h
UCLASS(Blueprintable)
class AAgentBridgeFunctionalTest : public AFunctionalTest {
    UPROPERTY(EditAnywhere) FString SpecPath;
    UPROPERTY() float LocationTolerance = 0.01f;  // 同 L2
    UPROPERTY() bool bUndoAfterTest = true;
    virtual void PrepareTest() override; virtual void StartTest() override; virtual void CleanUp() override;
    bool SpawnAndVerifyActor(int32, const FString&, const FString&, const FBridgeTransform&, TArray<FString>&);
};
// AgentBridgeGauntletController.h
UCLASS()
class UAgentBridgeGauntletController : public UGauntletTestController {
    virtual void OnInit() override; virtual void OnTick(float TimeDelta) override;
    enum class EAgentBridgeGauntletState { Initializing, WaitingForTestDiscovery, WaitingForAutomationRun, WaitingForSpecProcess, Finished };
};
```

## 4. 数据流与状态机

**场景 A — Run Workspace 创建(F-RT-05):** Compiler 主链入口或 Demo 脚本启动时,Orchestrator 生成 `run_id`(`<phase>_<timestamp>_<short_hash>` 形态);随即 `mkdir -p ProjectState/runs/<run_id>/{input,output,snapshots,runtime_config}` 四个子目录;`input/` 接 GDD Projection + Clarification Gate Report 等上游 fragment,`output/` 接 Stage 3/4/5 产物(`skill_graph.json` / `skill_fragments/*.json` / `lowered_spec.json`),`snapshots/` 接 World 快照,`runtime_config/` 接 mode_override 合并后的 effective profile。Run 结束后 workspace 不自动清理,由 Reports 索引 `ProjectState/Reports/<date>/<task>.md` 反向引用 run_id 以追溯。

**场景 B — Evidence 落盘(F-RT-03):** 工具(L1/L2 接口写 / capture_editor_evidence Editor 截屏 / 系统测试 fixture 比对)在执行前先调用 `get_evidence_root(phase_name)` 解出 `ProjectState/Evidence/<phase_name>/`,执行后写入 `<timestamp>/<tool>/<artifact>.{json,png,md}` 三层结构;manifest(`evidence_manifest.json`,Schema 见契约目录)同时落同目录;`Plugins/AgentBridge/MCP/server.py` 的 `mcp_evidence_*` 工具(F-MCP-10)读写也走这条路径。Phase 6/7 历史数据仍保留在 `Docs/History/reports/AgentBridgeEvidence/` 下,新 Phase 不再回写历史目录。

**场景 C — Reports 生成(F-RT-04):** `run_system_tests.py` 主入口按 Stage 串行(或 `--stage=N,M` 子集)调用 11 个 stage_* helper,每个 Stage 把子进程 stdout/stderr + 退出码 + 关键 fixture diff 序列化为 `ProjectState/Reports/<YYYY-MM-DD>/<stage_id>_<test_id>.{json,log}`,同时聚合一份 `summary.md` 索引;Demo 脚本与 `task14a_phase11_standalone_smoke.py` 走相同的 Reports 根但用各自的子目录命名(如 `task14a_standalone_runtime_smoke_validation.md`)。Reports 按"日期"分桶,Evidence 按"phase / run_id"分桶,**两者不可混用**——查询时按日期翻 Reports 找入口,顺着 Reports 内部链接跳到 Evidence。

**场景 D — document-release Gate(F-HOOK-01):** 开发者 `git commit -m "..."` → `.git/hooks/pre-commit` 模板调用 `doc_release_gate.py check --context=commit`;Gate 先读 `git diff --cached --name-only`(staged paths),若 `is_skip_doc_commit(message)` 或 `is_trivial(staged_paths)` → 直接放行;否则 `check_marker()` 校验 `(branch, head_sha, staged_files_hash)` 与 marker 文件一致 + 24h TTL 未过期 + `audit_evidence_path` 存在,任一失败 → 退出 1 阻塞 commit;放行后开发者继续 `git push`,`pre-push` hook 调用 `check --context=push --skip-staged-check`(push 上下文 `git diff --cached` 为空,只校验 HEAD SHA 与 evidence)。Marker 写入由 document-release skill 在审计完成后 `doc_release_gate.py write-marker --evidence=<path>` 显式调用。

**场景 E — Standalone Staged 流程(F-RT-02):** `Scripts/run_*_demo.py` 或 `task14a_phase11_standalone_smoke.py` 调用 `RunUAT.bat BuildCookRun -project=<UProject> -platform=Win64 -clientconfig=Development -build -cook -stage -pak` → 产出 `ProjectState/StagedBuilds/<game>/Windows/<Project>/Binaries/Win64/<Project>.exe`;Smoke 阶段再调用产出的 exe 起一个无 Editor 进程 + 短超时,落 `task14a_standalone_smoke.log` + 验收 md 到 `ProjectState/Reports/<date>/`。StagedBuilds 不进 git(`.gitignore` 排除),只本地保留最新 1 份。

**场景 G — Editor 在线引导(F-RT-01):** `Scripts/validation/start_ue_editor_project.ps1` 起 UE Editor GUI 实例,加载 `Mvpv4TestCodex.uproject`,Editor 启动后 `AgentBridgeSubsystem` 在 `Initialize` 中开启 RC HTTP 服务(端口 30010);开发者 / 自动化脚本通过 `bridge.remote_control_client` 把 spec 指令打到 Subsystem,Subsystem 内部转给 `BridgeExecutor` 执行写操作并按 transaction 提交,最后通过 RC HTTP 回写 `FBridgeResponse` JSON。Editor 在线模式与 Bridge 通信通道(CPP_PLUGIN / REMOTE_CONTROL / MOCK)概念正交——CPP_PLUGIN 走 C++ Subsystem 内嵌调用,REMOTE_CONTROL 走 HTTP,MOCK 走纯 Python stub;F-RT-01 不强制特定通道,但默认走 REMOTE_CONTROL。

**场景 F — Demo 端到端运行(F-DEMO-02):** 以 `run_greenfield_demo.py` 为代表:(1) 加 `Plugins/AgentBridge/Scripts` 到 `sys.path`;(2) 从 `ProjectInputs/GDD/` 读 GDD + `ProjectInputs/Presets/mode_override.yaml` 决定模式;(3) `compiler.handoff.build_handoff` 拼装 Reviewed Handoff 草稿落 `ProjectState/Handoffs/draft/`;(4) 人工 / 自动 review 后晋升到 `approved/`;(5) `orchestrator.handoff_runner.run_from_handoff(bridge_mode=...)` 按 `simulated / bridge_python / bridge_rc_api` 三模式之一执行,产物落 `ProjectState/Reports/<date>/` + `ProjectState/Evidence/<phase>/` + `ProjectState/runs/<run_id>/`。`bridge_mode` 决定是否真起 UE Editor(simulated 不起,bridge_rc_api 需 Editor + RC HTTP 30010 端口就绪)。

## 5. 扩展点

1. **新增系统测试 Stage:** 在 `run_system_tests.py` 增加 `def stage_12_<name>(args) -> StageResult`、注册到 `STAGES` 表 + 更新 `SystemTestCases.md` 用例登记 + 在 `Tests/scripts/` 下加同名 helper 脚本。每条新增系统测试用例必须能在 `--no-editor` 路径下可选执行(若依赖 Editor 须显式跳过)。

2. **新增 Demo 入口(F-DEMO-02):** 在 `Scripts/run_<game>_demo.py` 添加新脚本,沿用现有 `bridge_mode: simulated / bridge_python / bridge_rc_api` 三模式枚举;输出统一落 `ProjectState/Reports/<date>/<demo_name>_*.md`;若涉及 Standalone 走 BuildCookRun,落 `ProjectState/StagedBuilds/<demo_name>/`。

3. **新增 Validation 脚本(F-VAL-01..03):** 项目级落 `Scripts/validation/` / 插件级落 `Plugins/AgentBridge/Scripts/validation/`(共用 import 路径前缀 `from bridge.* / from compiler.*`);新增脚本必须能被 `run_system_tests.py` Stage 1(SV)或新 Stage 调用,且自带 `--help`。Schema 校验脚本要兼容 `--strict` 模式且默认通过 fixture 自测。

4. **新增 Hook 类型(F-HOOK-02):** 在 `Scripts/hooks/` 添加新模板(如 `post-commit` / `pre-rebase`),更新 `install_git_hooks.HOOK_NAMES` 元组,sync 到 `.git/hooks/`;若 hook 需要复用 doc-release marker,通过 `doc_release_gate.py` 的 `check` 子命令 + 显式 `--context=<new>` 串接,不要在 hook 模板里塞业务逻辑。

5. **新增 GDD / Preset(F-INP-01/02):** GDD markdown 放 `ProjectInputs/GDD/<game>_v<n>.md`,filename 由上游 Compiler intake(`Plugins/AgentBridge/Compiler/intake/design_intake.py` 或 Demo 脚本直接读 `ProjectInputs/GDD/*.md`)消化;新预设落 `ProjectInputs/Presets/<name>.yaml`,在 `mode_override.yaml` 中追加覆盖键。**不要直接改 `compiler_profile.yaml` 默认值**——所有改动通过 `mode_override.yaml` 实现,以便回溯。

6. **新增 C++ 自动化测试(F-TST-01..03):** L1 接口测试在 `Plugins/AgentBridge/AgentBridgeTests/Source/AgentBridgeTests/Private/L1_*Tests.cpp` 添加 `IMPLEMENT_SIMPLE_AUTOMATION_TEST`;L2 闭环用 `BEGIN_DEFINE_SPEC` / `END_DEFINE_SPEC` BDD 风格;L3 关卡测试创建新 `AFunctionalTest` 子类并在专用 `FTEST_*` 地图放置(可参考 `create_task15_functional_map.py` 自动建图)。Test Filter 命名约定为 `Project.AgentBridge.<L1|L2|L3>.<TestName>`,会被 Gauntlet Controller 的 `TestFilter` 命令行参数过滤匹配。

7. **新增证据捕获工具(F-VAL-03):** 在 `Scripts/validation/capture_*_evidence.py` 添加新捕获脚本,沿用 `get_evidence_root(phase_name)` 解析落盘根 + 写 `evidence_manifest.json` 索引;若需通过 RC HTTP 调 Editor Subsystem,复用 `bridge.remote_control_client.call_function`,不要直接拼 HTTP 请求体。

## 6. 已知约束与陷阱

1. **`ProjectState/` 是稳定核心,evidence 写入路径必须落合规子目录:** `CLAUDE.md` user-rule 与 `AGENTS.md` 明确 `ProjectState/{batches, Evidence, Handoffs, Reports, runs, RuntimeConfigs, Snapshots, StagedBuilds, phase10, phase11_task09_refactor_session, phase8, Temp, tmp}` 13 个子目录是稳定 layout;新工具要落证据**只能在已有子目录下扩展**,不允许新增顶层目录;`Temp/` `tmp/` 是过渡区,允许但要求 Run 结束清理。

2. **Reports 按日期分目录、Evidence 按 phase/run_id 分目录,不可混用:** Reports 是"时间维度的执行日志索引",Evidence 是"语义维度的证据存档"。Reports 内可以反向链接 Evidence(`![evidence](../../Evidence/<phase>/...)`)但反过来不行——Evidence manifest 不写日期路径,避免重命名日期文件夹时引用断链。新写工具时要遵守这条单向引用规则。

3. **document-release gate 两条逃生通道有副作用:** `[skip-doc]` 标记**永久跳过 marker 校验**,只用于工具/CI/treat-as-trivial 提交;trivial 白名单(`Saved/ Intermediate/ DerivedDataCache/ Binaries/ Build/ .codex/` + `.lock`)只对 100% 命中的 staged 集合放行——只要有一个文件不在白名单内,即视为常规提交。`--no-verify` 是 git 原生逃生,**审计层无法拦截**,只在用户明确请求时使用。

4. **Snapshots / StagedBuilds 是大文件目录,严禁进 git:** `ProjectState/Snapshots/` 单次 World 快照可达数十 MB,`ProjectState/StagedBuilds/` 单次 cooked 产物 GB 级;`.gitignore` 必须排除这两个目录;若发现意外 staged 命中,先 `git rm --cached -r ProjectState/Snapshots/ ProjectState/StagedBuilds/` 再补 `.gitignore`。

5. **C++ tests 必须 Editor 模式 + Gauntlet 外控:** `L1_*Tests.cpp` / `L2_*Spec.cpp` 全部依赖 `GEditor->GetEditorSubsystem<UAgentBridgeSubsystem>()`,在 Standalone 模式下 GEditor 为 nullptr 直接 fail。L3 `AAgentBridgeFunctionalTest` 走 `AFunctionalTest`,允许 EditorContext + ProductFilter;Gauntlet `UAgentBridgeGauntletController` 是引擎内"触角",负责 OnTick 轮询 + EndTest 退出码,**Gauntlet C# 端在引擎外驱动启动/停止**,二者不能颠倒。

6. **`run_system_tests.py` 硬编码 UE_5.5 路径(BC-025 命中):** `find_engine_root()` 候选列表是 4 条硬编码路径(`E:\Epic Games\UE_5.5` / `E:\GameProject\UE5-SourceCode-5.5.4\UnrealEngine` / `C:\Program Files\Epic Games\UE_5.5` / `D:\Epic Games\UE_5.5`);`task14a_phase11_standalone_smoke.py:25` 硬编码 `UAT_PATH = E:\Epic Games\UE_5.5\Engine\Build\BatchFiles\RunUAT.bat`;`Scripts/validation/start_ue_editor_*.ps1` 至少 5 处 `UE_5.5` 字符串。5.7 迁移必须批量替换 + 抽到 `$env:UE_INSTALL_ROOT` 环境变量。

7. **marker TTL 24h 是硬上限,跨日 commit 必须重审:** `MARKER_TTL = timedelta(hours=24)` 在 `doc_release_gate.py` 硬编码,marker 写入后超过 24h 即视为过期,需重跑 document-release skill 再写 marker;跨夜调试场景常踩这个坑。若 audit_evidence 文件被误删 / 改名,即使 marker 还在 TTL 内也会因 `Path(marker.audit_evidence_path).exists()` 失败而 block;evidence 文件命名一旦确定就不要改。

8. **`PROJECT_ROOT` 解析在 demo 与 system_tests 中不一致:** `Scripts/run_greenfield_demo.py` 用 `os.path.dirname(os.path.dirname(__file__))` 上溯 1 层(2 个 dirname)取项目根;`Plugins/AgentBridge/Tests/scripts/task14a_phase11_standalone_smoke.py` 用 `Path(__file__).resolve().parents[4]` 上溯 4 层。新增脚本须按所在目录深度选对应 parents 数,否则 ProjectState 路径会落到错位置。

## 7. UE 5.7 迁移变更点

> 本子系统受 UE 5.7 迁移直接影响主要在 **运行时入口 + UAT 调用 + RC HTTP 通信** 三处。BC 列表与 `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md` 对齐。

- **BC-025(P1 confirmed,由 msc 在 Phase 0.2 §4 裁决,源:`run_system_tests.py:727-730` find_engine_root 候选列表 + `task14a_phase11_standalone_smoke.py:25` UAT_PATH + `Scripts/validation/start_ue_editor_{cmd_project,project}.ps1` 中 `UE_5.5` 字符串共 7 处硬编码):** 必须批量替换为 5.7 路径或抽到 `$env:UE_INSTALL_ROOT`。迁移策略:(a) 优先环境变量化,避免 8.0/8.1 再次硬改;(b) 保留 5.5 / 5.7 双候选,运行时探测;(c) `task14a_phase11_standalone_smoke.py` 的 `UAT_PATH` 改为 `Path(os.environ.get("UE_INSTALL_ROOT", r"E:\Epic Games\UE_5.5")) / "Engine/Build/BatchFiles/RunUAT.bat"`。

- **BC-020(P2 suspected,pending-msc,源:`UAT BuildCookRun -editortest -RunAutomationTest=<Filter>` 调用形态):** 影响 `run_system_tests.py` Stage 4(Commandlet -RunTests)/ Stage 8(Gauntlet RunUnreal)/ Stage 9(E2E 三通道)+ `task14a_phase11_standalone_smoke.py` BuildCookRun 命令拼装 + 4 个 demo 脚本通过 UAT 起 Standalone 的部分。5.7 UAT 参数面预期向后兼容,但是否保留 `-editortest` 短开关 / `-RunAutomationTest=` 拼接形态需 5.7 实测。**严禁标 P1 confirmed**;迁移阶段一次 `run_system_tests.py --stage=4,8,9` 全跑即可确诊。

- **BC-021(P2 suspected,pending-msc,源:`validate_no_legacy_automation_entrypoints.ps1` 的 token 表):** 当前禁用 `RunUAT RunAutomationTests`(legacy 入口);若 5.7 引入新 legacy token(如废弃 `-editortest` 名),需在该脚本扩充黑名单。本 BC 影响治理校验脚本,不影响业务运行时;迁移阶段跟 BC-020 一起跑。

- **BC-019(P2 suspected,pending-msc,源:`Plugins/AgentBridge/MCP/server.py` + `Plugins/AgentBridge/Scripts/bridge/remote_control_client.py` 中的 RC HTTP `/remote/object/*` 端点形态):** 间接影响本子系统——`Scripts/validation/capture_editor_evidence.py` 通过 `bridge.remote_control_client.call_function` 调 Editor Subsystem 截屏;4 个 demo 脚本在 `bridge_mode=bridge_rc_api` 时走 RC HTTP。RC 端点稳定预期,但 5.7 是否改 JSON 序列化形态(尤其字段命名 / null 处理)需在 5.7 启动后跑一次 `capture_editor_evidence.py` smoke 验证。**严禁标 P1 confirmed**。

- **整体结论:** 本子系统对 UE 5.7 迁移**必须先修 BC-025 才能让 `run_system_tests.py` 跑通 5.7**,其余 BC-019/020/021 都是 P2 suspected,在 P1 修完后通过一次 `run_system_tests.py --stage=1..11` 全套回归 + `validate_examples.py --strict` + 4 个 demo 各跑一遍 simulated/bridge_rc_api 双模式即可确诊。Hook / Inputs / Presets / Validation 中除 BC-021 外不直接受 5.7 影响。
