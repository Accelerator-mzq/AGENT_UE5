# Phase 13 验收 runbook

> 对应 spec §8 验收判据 1-7
> (`Docs/superpowers/specs/2026-06-10-phase13-skill-synthesis-design.md`)。
> 每条做完勾选并贴证据路径。已知预存失败清单见附录,验收时如实跳过不算 Phase 13 缺陷。
>
> **执行状态(2026-06-11):步骤 1-12 已全部执行完毕,逐步执行记录与最终判定见文末
> 「验收执行记录(2026-06-11)」一节;判据 5 按 msc 裁决以执行词表边界口径部分达成。**
>
> 验收 GDD:`ProjectInputs/GDD/monopoly_extended_auction_v1.md`
> 已知标准答案:本 GDD 应产生且仅产生 **2 个 capability gap**
> (gameplay-auction 类 + gameplay-stock-market 类)。

---

## 判据 1-4(机器,已 CI 化)

### C1. Phase 13 pytest 89 全绿

```bash
python -m pytest Plugins/AgentBridge/Tests/scripts/ -k phase13 -v
```

- [x] **已闭环(2026-06-11 执行)**:89 passed, 275 deselected in 6.06s

  ```
  ===================== 89 passed, 275 deselected in 6.06s ======================
  ```

### C2. Stage 13 系统测试 89/89

```bash
python Plugins/AgentBridge/Tests/run_system_tests.py --no-editor --stage 13
```

- [x] **已闭环(2026-06-11 执行)**:Stage 13 PASS — 89/89

  报告路径:
  `Plugins/AgentBridge/reports/2026-06-11/system_test_report_2026-06-11_085414.json`

  ```
  -> [PASS] Phase 13 Skill Synthesis 全部通过 (89/89)  (5.9s)
  总计: 1 passed / 0 failed / 12 skipped  (5.9s)
  ```

### C3. Schema 校验 28/28

```bash
python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict
```

- [x] **已闭环(2026-06-11 执行)**:28/28 passed

  ```
  Checked examples       : 28
  Passed                 : 28
  Failed                 : 0
  [SUCCESS] 全部 example 校验通过，无异常校验动作
  ```

### C4. 等价回归 5 用例全绿(判据 1"改造不破现状")

```bash
python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase13_registry_equivalence.py -v
```

- [x] **已闭环(2026-06-11 执行)**:5 passed in 0.17s

  ```
  test_sks01_metadata_equivalent PASSED
  test_sks01_edges_equivalent PASSED
  test_sks01_node_order_and_ids_equivalent PASSED
  test_sks01_each_node_equivalent PASSED
  test_sks01_baseline_skill_graph_unchanged PASSED
  ============================== 5 passed in 0.17s ==============================
  ```

---

## 判据 2+3+4 实战(Claude Code 端)

> 以下步骤需要在有 MCP server 运行的会话中执行。
> 验收 GDD:`ProjectInputs/GDD/monopoly_extended_auction_v1.md`

### 步骤 1. 建立合成 session

```
MCP 调用:compiler_create_session(
    allow_skill_synthesis=true,
    gdd="monopoly_extended_auction_v1.md"
)
```

- [ ] session 创建成功,记录 run_id:______________________________

### 步骤 2. Stage 1 能力抽取 + 覆盖矩阵

驱动 Agent 执行 Stage 1(Root Skill Contract):

- [ ] 确认每条能力清单项都有 `source_anchor` 字段(来自 GDD 哪一节)
- [ ] 查看 run 目录中 `gdd_coverage_matrix.md`:
  - [ ] "无人认领"列表为空,或逐条记录人工裁决结论如下:

  | GDD 段落 | 裁决 | 说明 |
  |----------|------|------|
  | (填入无人认领项) | 非功能/打回 | |

### 步骤 3. Stage 2 → Stage 3:gap 断言

- [ ] 执行 Stage 2(Skill Graph Planning),确认 `skill_graph.metadata.capability_gaps` **恰好为 2 条**:
  - capability_id 含 `auction` 或 `property-auction` 类
  - capability_id 含 `stock` 或 `stock-market` 类
- [ ] 标准答案断言:2 个 gap,零其他 gap

### 步骤 4. 合成闭环实战

a. **正常合成流程:**

```
MCP 调用:compiler_skill_synthesis_prepare(run_id=<run_id>, capability_id=<auction_gap_id>)
```

- [ ] prepare 返回包含:GDD 相关段落摘录、6 文件规范说明、few-shot 范例、白名单

```
MCP 调用:compiler_skill_synthesis_save(
    run_id=<run_id>,
    capability_id=<auction_gap_id>,
    six_files={...}
)
```

b. **重试闭环验证(判据 3):**

- [ ] 故意提交缺少 `evaluator_prompt` 字段的包,确认 save 返回具体校验错误:

  ```
  期望返回类似:{"status": "validation_failed", "errors": ["evaluator_prompt: 文件缺失"]}
  ```

- [ ] 修正后重提,save 返回成功

- [ ] 对股票市场 gap 同样执行 prepare → save 流程

- [ ] 两个合成包均落盘至 `SkillTemplates/synthesized/<capability_id>/manifest.yaml`
  - manifest 中 `review_status: pending_review`

### 步骤 5. 人审 gate(判据 4)

- [ ] 查看 `ProjectState/runs/<run_id>/synthesis_review.md`,确认两个合成包的审阅清单齐全

- [ ] **验证人审 gate 拦截:**在不修改 review_status 的情况下重跑 Stage 3,
  确认合成包**不被消费**(gap 不因此消除)

- [ ] 将两个 manifest 的 `review_status: pending_review` 改为 `approved`:

  ```bash
  # 编辑文件路径:
  # SkillTemplates/synthesized/<auction_capability_id>/manifest.yaml
  # SkillTemplates/synthesized/<stock_capability_id>/manifest.yaml
  # 将 review_status: pending_review 改为 review_status: approved
  ```

### 步骤 6. 重跑 Stage 3:gap 清空

- [ ] 重跑 Stage 3,确认:
  - `capability_gaps` 清空(空列表或 0 条)
  - 两个合成节点出现在 skill_graph 中,`template_source=synthesized`

### 步骤 7. Stage 4-7 + promote 守卫

- [ ] 执行 Stage 4-7,Handoff v3 生成

  产物路径:______________________________

- [ ] 调用 `evidence_promote_run`,确认返回 **PROMOTE_REJECTED**:

  ```
  期望:{"status": "PROMOTE_REJECTED", "reason": "...", "synthesized_nodes": [...]}
  ```

  拒绝理由应包含合成节点清单(判据 4"试制章生效")

---

## 判据 6(Codex 端)

### 步骤 8. Codex 注册 MCP server(需 msc 授权)

> **项目外改动,执行前须 msc 明确授权。**
>
> 目标文件:`~/.codex/config.toml`
> 动作:添加 agentbridge MCP server 配置项
>
> 配置格式参考:
> ```toml
> [mcpServers.agentbridge]
> command = "python"
> args = ["D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/MCP/server.py"]
> ```

- [ ] 已获得 msc 授权,执行配置

### 步骤 9. Codex 端等价验收

Codex 驱动,同一 GDD(`monopoly_extended_auction_v1.md`),新开 run:

- [ ] 全部 stage 产物 schema 校验通过
- [ ] capability_gaps 集合与 Claude Code 端一致(auction + stock-market 各 1 条)
- [ ] 两个合成包通过机器校验(save 返回成功)
- [ ] 不要求字节内容一致(LLM 非确定性),仅要求结构等价

  Codex run_id:______________________________
  对比报告路径:______________________________

---

## 判据 5(真机,人审挑一端产物)

### 步骤 10. 真机 UE 5.5 Editor 执行

- [ ] 选用步骤 6 审批后的 Handoff v3 产物,在 UE 5.5 Editor 中执行

  执行命令参考:
  ```bash
  python Plugins/AgentBridge/Scripts/orchestrator/handoff_runner.py \
      --handoff <handoff_v3_path>
  ```

- [ ] 拍卖面板:屏幕中央弹出层出现,含地产名/底价/出价记录/出价按钮/弃权按钮
- [ ] 交易所面板:弹出层出现,含 3 支股票现价/持仓/买入卖出按钮
- [ ] 基础交互响应(点击按钮无报错)

### 步骤 11. 截图 + 日志落盘

- [ ] 截图路径:`ProjectState/Evidence/phase13_auction_panel_<日期>.png`
- [ ] 截图路径:`ProjectState/Evidence/phase13_stock_panel_<日期>.png`
- [ ] 执行日志路径:`ProjectState/Evidence/phase13_true_machine_<日期>.log`

---

## 判据 7(stretch,非阻塞)

### 步骤 12. JRPG 全量合成尝试

```bash
# 使用已有的 jrpg_turn_based_v1.md 作为输入 GDD
# MCP 调用:compiler_create_session(allow_skill_synthesis=true, gdd="jrpg_turn_based_v1.md")
# 运行全部合成流程
```

- [ ] 尝试结果(成败皆可,如实记录):______________________________
- [ ] 与 `Docs/archive/history/Proposals/jrpg_genre_pack_design.md` 人工对照,质量评估:
  ______________________________

---

## 验收执行记录(2026-06-11,执行者:Claude Code,裁决:msc)

### 逐步执行结果

| 步骤 | 结果 | 关键证据 |
|---|---|---|
| 1. 建合成 session | ✅ | run_id=`run-20260611-052252-5101`,`allow_skill_synthesis=true`,经真 MCP stdio 协议(驱动器 `ProjectState/Reports/2026-06-11/mcp_driver.py`) |
| 2. Stage 1 + 覆盖矩阵 | ✅ | 16+2 required capability 全带 source_anchor(save 零 warning);矩阵 5 个无人认领段落经 msc 裁决:L1 标题/L12 PART A=非功能,3.1/3.2/4.2=表现层细节已被两扩展能力实质覆盖,不打回 |
| 3. gap 标准答案断言 | ✅ | capability_gaps **恰 2 条**:gameplay-property-auction(anchor=2.1 地产拍卖)+ gameplay-stock-market(anchor=2.2 股票市场),零其他 gap |
| 4a. 合成 prepare/save | ✅ | prepare 含 GDD 摘录(anchor 精准命中 §2.1)/6 文件规范/2 范例/21 family 白名单;两包 saved,provenance 戳 `synthesis_run_id` + `synthesized_by: mcp_agent` |
| 4b. 重试闭环实战 | ✅ | 故意缺 evaluator_prompt 提交 → `synthesis_status=rejected`,错误"缺少或为空: evaluator_prompt.md";修正重提 saved |
| 5. 人审 gate | ✅ | 拦截验证:pending 包重跑 Stage 3 gap 仍 2 条、合成节点不入图;msc 审阅 12 文件全文后批准,review_status 改 approved |
| 6. gap 清空 | ✅ | 重跑 Stage 3:gaps=0,18 节点,skill-property-auction/skill-stock-market 入图且 `template_source=synthesized`,manifest 声明依赖边换算正确 |
| 7. Stage 4-7 + promote | ✅ | 18 节点 Stage 4 完成(合成节点:**发散维度为 agent 创作且全程留痕**(auction.pass_reentry 等流入 design_space_report 与 decision_log),**收敛选择值落入 fallback 候选命名**(驱动脚本注入的收敛键未被 fragment 组装读到,事后核查披露,不影响本判据——测的是合成链/守卫而非 Stage 4 内容保真);库内节点 fallback——Phase 11 e2e 同款),Handoff v3:`ProjectState/runs/run-20260611-052252-5101/reviewed_handoff_v3.json`;`evidence_promote_run` → **PROMOTE_REJECTED**(双重拦截:synthesized 节点清单 + metadata.promotable=false) |
| 8. Codex MCP 注册 | ✅ | msc 授权,`~/.codex/config.toml` 加 `[mcp_servers.agentbridge]`(py312 起 server),`codex mcp list` 确认 enabled |
| 9. Codex 端等价 | ✅ | run_id=`run-20260611-073328-cec6`,gap 集合与 anchor 值逐项一致、四产物 schema 全过、两包过校验(pending_review)、Codex 拍卖包首提缺 realization_class 被拒后自修正重提(独立 agent 重试闭环实证);对比报告:`ProjectState/Reports/2026-06-11/phase13_dual_harness_comparison.md` |
| 10. 真机 UE 执行 | ⚠️ 部分达成(msc 裁决口径) | Handoff 6 个 widget 步骤真机落地(C++ Subsystem CreateBlueprintChild),元数据验证+SaveNamedAssets 成功;10 个 cpp 步骤按 Phase 11 先例不真机执行;**拍卖/交易所独立面板因 family 级 lowering 合并不可达成**(见发现 1) |
| 11. 证据落盘 | ✅ | `ProjectState/Evidence/phase13_editor_widgets_2026-06-11.png`(Editor 前台截图)+ `phase13_true_machine_2026-06-11.log`(执行日志)+ `Content/Generated/Phase13Acceptance/*.uasset` 6 件 |
| 12. JRPG stretch | ✅(部分执行,机制验证通过) | run_id=`run-20260611-103302-8f43`:4 个 JRPG gameplay capability 全部成 gap(跨类型 gap 机制正常);合成 1/4 包(回合制战斗)saved,跨类型合成闭环实证;与 `jrpg_genre_pack_design.md` 对照:单技能粒度忠实 GDD,全 genre pack 广度需逐 gap 合成 |

### 验收发现(进 backlog / Phase 14 输入)

1. **family 级 lowering 合并(Phase 14 关键输入)**:economy+拍卖+股票三个同 family fragment 合并为单一 build 步骤,合成能力在契约/fragment/handoff 层留痕完整但 build_ir 层失去独立呈现——"几份 demo 供挑选"必须先细化 lowering 粒度。
2. **SkillTemplates 树内目录默认信任**:备份目录放树内即被当正式库扫描(绕过审批门),实证于 Codex 第四跑 gap=0 事故;建议 registry_scan 加目录白名单或告警。
3. **bridge 缺陷**:`create_blueprint_child` 分发链缺 CPP_PLUGIN 分支(C++ 实现存在不可达);L2 资产工具依赖的 RC python 路由 404;UE 内部截图队列后台不消费。
4. **Stage 1 启发式模板 Monopoly 固化**:JRPG GDD 仍产出 Monopoly 契约,跨类型全靠 agent 重写(MCP agent 路径可承载,LLM Internal 路径跨类型质量未测)。
5. **词表硬边界的语义挤压**:JRPG 战斗被迫映射到 turn_flow_spec(21 个既有 family 中最近),全新 genre 的忠实呈现需要新 family(执行层扩词表,Phase 14+)。
6. **codex exec 非交互 MCP 审批**:`approval_policy=never` 不放行 MCP 工具调用,需 `--dangerously-bypass-approvals-and-sandbox`(受控场景);另 stdin 非 TTY 时需管道喂提示词。

### 最终判定

- **判据 1-4(机器)**:✅ 全过(此前已闭环)
- **判据 2/3/4(实战)**:✅ 全过(步骤 1-7)
- **判据 6(双端等价)**:✅ 全过(步骤 8-9)
- **判据 5(真机)**:⚠️ 按词表边界口径部分达成(msc 裁决,2026-06-11)——执行通路与 widget 步骤实证,合成能力独立真机呈现留 Phase 14
- **判据 7(stretch)**:✅ 非阻塞目标达成(跨类型机制验证)

---

## 附录:已知预存失败(验收时跳过,非 Phase 13 缺陷)

以下测试用例在本 Phase 开始前已存在失败,根因与 Phase 13 无关。
验收时如实跳过,不计入 Phase 13 缺陷。

| 用例 ID | 根因 | 说明 |
|---------|------|------|
| MCP-03 | 环境缺 `mcp` Python 包 | MCP server 启动依赖,CI 未安装 |
| MCP-04 | 环境缺 `mcp` Python 包 | 同上 |
| MCP-05 | 环境缺 `mcp` Python 包 | 同上 |
| MCP-08 | 历史证据文件缺失(gitignore 产物) | 前序 run 产物未提交,路径不存在 |
| MCP-10 | 历史证据文件缺失(gitignore 产物) | 同上 |
| P11-09 | gitignore 产物缺失 | Phase 11 执行产物被 .gitignore 排除 |
| P11-10 | gitignore 产物缺失 | 同上 |
| P11-18 | gitignore 产物缺失 | 同上 |
| CP-44  | gitignore 产物缺失 | 与 P11 同类,产物路径不存在 |

> 如需复现根因:MCP 包缺失可通过 `pip install mcp` 修复;产物缺失需在有 UE5 Editor
> 环境下重跑对应 stage 并手动保留产物。两类根因均与 Phase 13 Skill 合成无关。
