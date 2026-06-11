# Phase 13 — Skill 合成主链设计(GDD 动态 Skill 生成)

> 创建日期:2026-06-10
> 状态:已实施(2026-06-11 实施完成,验收 runbook 判据 1-4 闭环、5-12 待执行;原状态:Design / 待实施)
> 关联工作流:Superpowers(brainstorming → writing-plans → executing-plans → verification-before-completion → finishing-a-development-branch)
> 前序分析:本设计源于 2026-06-10 brainstorming 会话对产品愿景("GDD → agent 发散创造 → N 份 demo → 使用者挑选")与现状的三缺口分析
> 落地范围:Compiler 插件层(`Plugins/AgentBridge/Compiler/`)+ SkillTemplates + MCP 工具 + 项目层验收资产;不动 Orchestrator/Bridge 稳定核心

## 修订记录(实施期裁决,2026-06-11)

实施期间对照真实代码做出的三条设计精化,以下记录为准、覆盖本文对应原文:

1. **synthesized 试制标记落在节点 `template_source`,非 §4.4 原文的 `generator_type`**——模板来源(谁提供的 SkillTemplate)与生成器类型(Stage 4 哪条 Provider 路径)是两根独立的轴,合成模板节点在 skill_graph 上以 `template_source: synthesized` 标记(单一事实源),promote 守卫只认该字段;`generator_type` 维持 Phase 11 语义不扩枚举。
2. **覆盖矩阵 status 增加第三态 `container`**——纯结构容器段落(只有子标题、无正文内容的 markdown 节点)既非 claimed 也不应计入 unclaimed 噪音,新增 `container` 态(plan 测试与参考实现矛盾时的裁决产物,边界已钉死:有任何正文内容即不算 container)。
3. **promote 守卫扩展:未解决 capability_gaps 同样拦截**——§4.1 的"gap 保留 + promotable=false"语义落实为 evidence 层拒绝路径(`PROMOTE_REJECTED`,与 synthesized 消费同一条),并对损坏 / 不可解析的 skill_graph fail-closed。

---

## 1. 背景与目标

### 1.1 三个结构性缺口(分析结论回顾)

产品愿景是"提供一份 GDD,agent 发散创造,自动生成几份游戏 demo 供使用者挑选"。对照现状的三个缺口:

| 缺口 | 病理 | 处置 |
|---|---|---|
| Skill 封闭世界 | Stage 3 能力→模板映射硬编码(`GAMEPLAY_NODE_CONFIGS`,`skill_graph_planning.py`),库外能力被 `continue` **静默丢弃**,`capability_gaps` 字段从未被填充 | **Phase 13 本体** |
| 无"人挑选"环节 | 系统把选择全部建模为验证型质检(promote 单 batch 单向),偏好型选择零基础设施 | Phase 14 |
| arbiter 收敛为 1 | "无人编译链"前提把选择权交给 AI 总监,与"使用者挑选"相反 | Phase 14/15 |

三者共同根因:**试点期假设(词表封闭、无人在环、单产物晋升)从未被任务书显式裁决,却固化成了架构。** Phase 13 先解决第一个——它是后续一切的前提:模板外的 GDD 现在连一份完整 demo 都编不出来,扇出只会扇出 N 个残缺品。

### 1.2 目标(一句话)

**让一份超出模板库的 GDD 能编出完整真机单 demo**:capability gap 显式化、Stage 3 注册表数据化、新增链内合成 stage(MCP 形态,Claude Code / Codex 双端可驱动)、合成产物经双 gate 信任审查后进入 Stage 4-7 与真机执行,并以 GDD 覆盖矩阵保证"写在 GDD 里的东西要么被覆盖、要么可见地等待人裁决"。

### 1.3 非目标 / YAGNI(全部记 backlog 或留后续阶段)

- 扇出 N demo + 用户挑选会话层(Phase 14)
- arbiter 改造为 N 方案包(Phase 14/15)
- Clarification Gate 第 5 档 "capability_not_in_library"(schema 升版连锁,backlog)
- LLM Internal 路径驱动合成(Phase 13 合成仅走 MCP agent 路径,backlog)
- Standalone 打包验收(stretch,非阻塞)
- 执行层新动作词表(硬边界,见 §3 第 4 条)
- synthesized 模板转正机制(搬入正式库、解除 promotable 限制;待跨 run 稳定性数据,backlog)
- 可复用的覆盖矩阵忽略规则(见 §5.3 防固化守则第 2 条,如需必须单独立项)

---

## 2. 总体流程(简化版)

全程只有 1 个新开关(`allow_skill_synthesis`)+ 1 个新人工动作(审核合成 skill)。

```
你提供 GDD(含模板库没有的玩法,如拍卖)
        ↓
① 编译器点名缺件                ←—— 以前:悄悄丢掉,demo 缺胳膊少腿
   "缺 2 个 skill:拍卖机制、股票市场"
   (+ GDD 覆盖矩阵:无人认领的 GDD 段落也列出来)
        ↓
② agent 现场造件(全自动)
   Claude Code 或 Codex 照规范写出缺的 skill(6 文件包),
   机器自动查格式,不合格直接打回重写
        ↓
③ 你验收一眼                    ←—— 唯一新增的人工动作
   审阅清单 + 覆盖矩阵的无人认领列表,你说"通过"
        ↓
④ 照常开工(全自动,现有流程原样)
   编译继续 → 真机 UE Editor 落地 → 可玩 demo + 截图证据
```

治理三句话:
1. 不开 `allow_skill_synthesis` 时,一切行为与现状一致——只是缺件会被**说出来**而不是吞掉。
2. agent 造的件全部进隔离区(`SkillTemplates/synthesized/`),人没点头的,编译器装作看不见。
3. 用了试制件的产物一律盖"试制"章(`promotable=false`),不会混进正式库。

术语对应:① = Stage 3 改造 + capability_gaps 显式化 + 覆盖矩阵;② = S3.5 合成 stage(MCP prepare/save + 机器校验重试);③ = 人审 gate(`review_status` 字段);④ = 重入 S3 → S4-7 → 真机执行(零改动)。

---

## 3. Stage 3 改造(病根清除)

1. **注册表下沉**:`GAMEPLAY_NODE_CONFIGS` / `BASELINE_NODE_CONFIGS` 的绑定信息(capability_id、allows_design_space_discovery、convergence_priority、fragment family)下沉为各模板 `manifest.yaml` 新增的 `capability_binding` 块;存量 12 模板补字段。`FRAGMENT_FAMILY_MAP` 同步从 manifest 的 `can_emit_families` 推导,代码里两张硬编码表删除。
2. **扫描建映射**:Stage 3 启动时 rglob 扫描全部 manifest(含 `SkillTemplates/synthesized/` 隔离区,但仅纳入 `review_status: approved` 的;正式库人写模板无 `review_status` 字段,默认信任)构建 capability→template 映射。加载机制本来就是 rglob 扫 manifest(`domain_skill_runtime._resolve_template_prompts`),此处只是提前到 Stage 3。
3. **gap 显式化**:required capability 查不到映射时,不再 `continue` 静默丢,写入 `skill_graph.metadata.capability_gaps[]`(记 capability_id、来源 anchor、原因 `no_template`)。
4. **执行词表硬边界**:合成 skill 的 `can_emit_families` 必须 ⊆ 现有执行层已支持的 family 白名单(UI widget / Actor 摆放 / 基础交互类)。Phase 13 不给执行层加新动作类型——"拍卖机制可玩"的水位 = 拍卖 UI 呈现 + Actor + 交互响应,与 Phase 11 可玩性基线同级。越界的合成需求被校验器拦截并记 gap,不静默放行。
5. **行为兼容回归**:改造后,基线 Monopoly GDD 跑出的 skill_graph 必须与改造前**等价**(排除 run_id / 时间戳等易变字段后逐项一致——老 GDD 是改造前后的对照组,它的产出不许变,变了即重构引入 bug);266 系统测试 + `validate_examples.py --strict` 不破。

---

## 4. S3.5 合成 stage 与信任治理

### 4.1 编排位置与触发

```
S3 Skill Graph Planning
 │ capability_gaps 为空 ──────────→ 直接进 S4(现状路径,零影响)
 │ capability_gaps 非空
 ↓
S3.5 Skill Synthesis(新增)
 ├─ allow_skill_synthesis=false(默认)→ 跳过合成,gap 保留在产物中,
 │   run 强制 promotable=false(诚实降级,与 fast_mode 同语义)
 └─ allow_skill_synthesis=true → 逐 gap 进入合成循环
      → 全部合成且校验通过 → 人审 gate(pipeline 暂停)
      → 人审通过 → 重跑 S3(新模板已可被扫描到,gap 清空)→ S4-7
```

fast_mode 下无条件跳过合成。默认行为与现状完全一致,合成是显式 opt-in。

### 4.2 MCP 工具对(harness 中立的合成交互面)

仿照 Stage 4 的 prepare/save 模式,新增两个 MCP 工具:

- **`compiler_skill_synthesis_prepare(run_id, capability_id)`** 返回:gap capability 上下文(GDD projection 相关段落 + Root Skill Contract 约束)、6 文件规范说明、最相近的 1-2 个现有模板全文作为 few-shot 范例、`can_emit_families` 白名单、命名规则。skill-creator 的方法论(怎么写好一个 skill)吸收进 prepare payload,不绑定任何 harness。
- **`compiler_skill_synthesis_save(run_id, capability_id, six_files)`** 接收 6 文件内容,先跑自动校验器,失败把具体校验错误返回给 agent(agent 修正重提,形成重试闭环——HUD arbiter 试点缺的"格式校验+重试"在此补上);通过则落盘 `SkillTemplates/synthesized/<capability_id>/`,manifest 初始 `review_status: pending_review`。

### 4.3 双 gate 信任链

1. **机器校验(save 内强制)**:6 文件齐全、manifest 必填字段完整、`template_id` 与目录一致、output_schema 为合法 JSON Schema draft-07 且 root + 所有嵌套 object 递归 `additionalProperties: false`、`can_emit_families` ⊆ 执行词表白名单。
2. **人审 gate(pipeline 暂停)**:全部 gap 合成且校验通过后,生成审阅清单 `ProjectState/runs/{run_id}/synthesis_review.md`(每个合成包的 6 文件路径 + 重点提示 output_schema 与 evaluator_prompt + 与最相近人写模板的丰富度对照参考),pipeline 停。人审后将对应 manifest 的 `review_status` 改为 `approved`,续跑命令重入 S3。`review_status != approved` 的 synthesized 模板,Stage 3 扫描时不纳入映射(未审包不可能被消费)。

### 4.4 Provenance 与治理(复用既有机制)

- 合成模板 manifest 标 `template_source: synthesized` + 合成时的 run_id / agent 标识;由它生成的 fragment 记 `generator_type=synthesized`,沿 provisional 传播机制(F-CHN-05)全链留痕到 Handoff v3。
- 凡消费了 synthesized skill 的 run,Phase 13 一律 `promotable=false`(与 heuristic_fallback 同级保守)。转正路径记 backlog。

---

## 5. GDD 覆盖矩阵(完整性保证)

### 5.1 问题:静默丢失有两个发生点

```
GDD 文档 ──①抽取──→ 能力清单(Root Skill Contract)──②查表──→ skill(库内或合成)
```

②由 §3 的 gap 显式化机器保证(确定性逻辑,可证明)。①是软肋:agent 读 GDD 漏识别一个能力,后面机制再严密也救不了。"LLM 读文档是否读全"是开放语义问题,**无法绝对保证**,保证模型是三层:

### 5.2 三层保证模型

1. **抽取强制留痕(机器)**:Stage 1 能力清单中每条能力必须标注 GDD source anchor(出自哪一节哪一段),无出处条目过不了 save 校验。
2. **反向覆盖审计(机器产报告 + 人看结论)**:确定性脚本把 GDD 按章节/段落切分,逐段比对"被哪条能力认领",产出 GDD 覆盖矩阵 sidecar(`ProjectState/runs/{run_id}/gdd_coverage_matrix.json` + 人读版 markdown)。人审只看"无人认领"列表:逐条裁决"非功能,不用管"或"抽取漏了,打回重抽"。漏掉的东西从"看不见"变成"列在表上等裁决"。
3. **已知答案用例(验收)**:验收 GDD 是自己写的,植入的库外能力是已知标准答案,断言 100% 被识别并合成(见 §8 判据 2)。

一句话:**"识别出的绝不丢"由机器证明;"没识别出的必然可见"由矩阵保证;最终裁决权在人,但只需看无人认领清单。**

### 5.3 防固化守则(四条,实施与评审时强制对照)

覆盖矩阵本体是无内容机制(两份产物的结构 diff),固化风险天然低于领域知识注册表;但有四个语义渗入口,逐条设防:

1. **切分器永远保持最笨**:只认文档结构(markdown 标题/段落),零语义判断。**切分器代码出现任何游戏词汇即视为违规。** 误报交给人看,不许用代码"优化"掉。
2. **裁决是 run 级证据,不是全局配置**:每次 run 的矩阵从零生成;人的"不用管"裁决只记录在当次 run 产物中供审计,**不被后续 run 自动消费**。可复用忽略机制如需,必须单独立项单独治理。
3. **认领关系只靠 anchor 引用**:覆盖判定不依赖任何能力分类词表;分类信息可携带但不参与判定。
4. **GDD 格式假设写在纸上**:Phase 13 明文支持 markdown GDD;非 markdown 输入优雅降级(整篇视为一个无人认领大段,人一眼看出矩阵失效,不假装工作)。**显式声明的边界不是固化,埋起来的假设才是。**

总判据:**矩阵机制代码中不允许出现游戏领域语义;所有语义判断要么 agent 当场做(run 级),要么人当场裁(run 级),永不沉淀为代码或全局配置。**

---

## 6. 合成 skill 的四道验收关

每个合成 skill(6 文件包:`manifest.yaml` 身份证 / `system_prompt.md` 人设 / `domain_prompt.md` 领域知识 / `evaluator_prompt.md` 自检清单 / `input_selector.yaml` 取料单 / `output_schema.json` 出货合同)须连过四关:

| 关 | 判什么 | 谁判 | 判法 |
|---|---|---|---|
| ① 格式关 | 长得像合法 skill:6 文件齐全、schema 合法、白名单内 | 机器(save 校验器) | 校验器全绿;不绿打回重写 |
| ② 内容关 | 写的是 GDD 要的东西:domain_prompt 与 GDD 一致、output_schema 覆盖关键设计点、evaluator_prompt 能查遗漏 | 人(审阅清单) | 人说通过 |
| ③ 上机关 | 装上编译链能转:S4 三 phase 走完、fragment 过 schema、S5-7 消化、Handoff 含其 spec | 机器(编译实证) | 全链无卡点,产物全过校验 |
| ④ 落地关 | 真机里真有这个玩法:UI/Actor 出现、与 spec 一致、交互响应 | 机器+人(真机证据) | 截图/日志落 `ProjectState/Evidence/`,与 GDD 描述对得上 |

补充两点:
- **质量软基准**:合成 skill 与最相近的人写模板(如 `monopoly_property_economy`)对照,维度丰富度、prompt 具体度应在同一量级;写进人审清单作参考项,不做硬指标。
- **稳定性最低保证**:Phase 13 不承诺跨运行稳定(推广前置条件,记 backlog);但双端验收(§7)使同一缺件被 Claude Code 与 Codex 各独立合成一次,两次都须过①③机器关——免费获得一组"不同 agent、同一任务"重复实验。

---

## 7. 双 harness 适配(Claude Code / Codex)

- **架构约束(总则)**:所有新增 agent 交互面一律走 MCP(prepare/save 工具对);harness 专属机制(如 `.claude/skills/` / `.agents/skills/` 双份 SKILL.md)只用于工程治理类 skill,不用于编译链 skill。编译链 SkillTemplate 经 MCP payload 投喂,单份生成、双端通用。
- **Codex 侧前置**:`~/.codex/config.toml` 注册 agentbridge MCP server(项目外改动,执行前单独征求用户授权)。
- **等价性验收**:同一份验收 GDD,Claude Code 与 Codex 分别通过 MCP 驱动"合成 + Stage 1-4"各跑通一次,断言产物**结构等价**(全部 stage 产物 schema 校验通过、节点全覆盖、合成包过自动校验;不要求字节一致——LLM 非确定)。真机执行只跑一次(人审挑一端产物),执行层 harness 无关。
- **风险缓解**:双端用例安排在单端主链跑通之后,Codex 兼容性问题(长 payload 等)不阻塞单端验收。

---

## 8. 验收判据(7 条,1-6 必过,7 为 stretch)

| # | 判据 | 怎么算过 |
|---|---|---|
| 1 | 改造不破现状 | 基线 Monopoly GDD skill_graph 改造前后等价;266 系统测试全过;schema --strict 全过 |
| 2 | 缺件被点名 + 覆盖完整 | Monopoly 扩展 GDD(植入 2-3 个库外能力)跑编译:植入能力 100% 被识别并记 gap,零静默丢弃;覆盖矩阵无人认领清单为空或全部经人裁决;Stage 1 source anchor 校验生效 |
| 3 | 造件闭环 | agent 合成出 6 文件包,机器校验通过;重试闭环以确定性测试用例验证(提交非法包 → save 返回具体校验错误 → 修正重提通过),不依赖现场恰好失败 |
| 4 | 人审 gate 生效 | 未审批的合成包编译器确实不消费;审批后正常进入后续阶段 |
| 5 | 真机 demo | 新能力(如拍卖)的 UI/Actor 进真机 Editor、交互响应,四道关全过,证据落 `ProjectState/Evidence/` |
| 6 | 双端等价 | Claude Code 与 Codex 各驱动"合成+S1-4"跑通,产物结构等价(schema 级) |
| 7 | JRPG stretch | `ProjectInputs/GDD/jrpg_turn_based_v1.md` 全量合成跑通(非阻塞,失败只记发现;Phase 7 历史设计 `jrpg_genre_pack_design.md` 作合成质量人工对照) |

验收载体:主验收为 Monopoly 扩展 GDD(新写,基于 `GDD_MonopolyGame.md` 加 2-3 个库外能力如拍卖机制/股票市场——大部分能力走现有模板、少量走合成,精准隔离"合成质量"单一变量,避免与"执行词表越界"两个未知数叠加)。

---

## 9. 测试

- 新增系统测试 stage:注册表扫描、gap 显式化、合成校验器(合法/非法包各若干)、人审 gate 拦截、覆盖矩阵切分与认领判定——纯 Python 单测,不依赖真机。
- 新增 schema:合成包 manifest 扩展字段、`gdd_coverage_matrix`、synthesis evidence(具体清单在 writing-plans 阶段定),全部入 `validate_examples.py --strict`。
- 真机部分沿用 Phase 11 证据验收模式(截图 + Actor 比对),不新造测试设施。

---

## 10. 风险与缓解

| 风险 | 等级 | 缓解 |
|---|---|---|
| 合成质量非确定(HUD arbiter 试点实测:同任务一次空一次满) | 高 | 机器校验+重试闭环兜格式;人审兜语义;试制章(promotable=false)兜污染;双端验收提供最低重复实验 |
| Stage 1 抽取漏识别(覆盖不完整) | 高 | §5 三层保证:anchor 强制留痕 + 反向覆盖审计 + 已知答案用例 |
| 合成需求超出执行层能力 | 中 | `can_emit_families` 白名单校验器硬拦,越界记 gap 不放行;可玩水位明文锚定 Phase 11 基线 |
| Stage 3 重构回归 | 中 | 判据 1 等价断言先行,过门再写新功能 |
| Codex 实测兼容性未知(长 payload 等) | 中 | 双端用例后置,不阻塞单端;问题如实记录 |
| 覆盖矩阵机制固化 | 中 | §5.3 四条防固化守则,实施与 review 强制对照 |

---

## 11. 关键决策记录(brainstorming 用户裁决)

| 决策点 | 裁决 |
|---|---|
| Phase 13 主线 | Skill 合成主线;扇出 N demo + 挑选会话层留 Phase 14 |
| 验收 GDD | Monopoly 扩展 GDD 主验收 + JRPG 全量合成 stretch |
| 信任 gate | 机器校验 + 人审双 gate(首版必开人审,后续可降抽检) |
| 双 harness 深度 | 双端驱动等价性验收(非协议层冒烟) |
| 真机水位 | 真机 Editor 在线可玩(Phase 11 同级);Standalone 打包 stretch |
| 实现方案 | 方案 A:链内合成 stage + 注册表下沉为 manifest 自描述(否决链外预合成与 Gate 第 5 档方案) |
| 覆盖保证 | GDD 覆盖矩阵三层模型 + 四条防固化守则 |
