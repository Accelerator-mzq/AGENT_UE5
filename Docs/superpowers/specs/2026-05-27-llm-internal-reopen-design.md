# LLM Internal Reopen + Provider Framework Migration — Design Spec

> 文档版本: v1.0
> 日期: 2026-05-27
> 作者: Claude Code (msc 主导决断)
> 类型: superpowers spec (brainstorming 阶段产物)
> 阶段: Phase 12(候选名),依赖 Phase 11 已收尾基线
> 后续: 通过 `superpowers:writing-plans` 生成 implementation plan
>
> **修订记录**
> - v1.0 (2026-05-27): 初版,基于 9 次 AskUserQuestion 决断 + 5 节逐节确认整合

---

## 0. 目的与场景

Phase 11 收尾(2026-04-17 acceptance_report)显式记录了一条残留:

> `LLM Internal` 高负载验收暂缓,等 `llm_client` 框架升级后重开,不阻塞 UE 5.7 重构。
> Phase 11 正式主路径仍是 `MCP Agent` 驱动的 Stage 4 创造性生成,`heuristic_fallback` 是显式后备。

实测诊断(`ProjectState/Reports/2026-04-16/stage4_candidates_prompt_vs_provider_diagnostic.{md,json}`)结论:

- Provider 不是不稳 — 轻载 3/3 PASS、单 dimension 分批 3/3 PASS(26-32s/dim)
- 6/6 稳定失败的是 **"7 维度一次吃"** — 卡 181s 超时,1 次 `529 overloaded_error`
- 诊断报告 §7 自给方向:`batch by dimension` 是**第一性原理**路径

本 spec 是 LLM Internal 重开 + provider 框架重度移植的实施前设计,产出后等 `superpowers:writing-plans` 翻成可执行 implementation plan。

**目标读者**:
- 主读者:实施本阶段的开发者(可能是 Claude Code / Codex / msc 本人)
- 次读者:UE 5.7 重构启动前需要回看 LLM 路径 promotable 状态的 reviewer

**不在 spec 范围**:见 §7 yagni 划界。

---

## 1. 已确认前提(brainstorming 阶段 9 项决断)

### 1.1 改造范围

**选 C 全栈系统化(含 Schema)**:同时改 Stage 4 调用层、调度层、Schema 层、pipeline_orchestrator 通用化。让 LLM 路径变成一等公民,不只是 patch 现有 `llm_client.py`。

### 1.2 与 UE 5.7 重构的时间关系

**选 A LLM 先行,UE 5.7 重构的前置门禁**:UE 5.7 重构之前 LLM Internal 必须先 promotable,作为 UE 5.7 E2E 验证的 generator 变量之一。

**与 acceptance_report §残留措辞的冲突说明**:当前 `acceptance_report.md:452` 写"LLM Internal 暂缓,不阻塞 UE 5.7 重构"。本期完成后必须翻面改写为"LLM Internal 是 UE 5.7 重构前置门禁",并删 §残留 条目。

### 1.3 参照力度

**选 α 重度移植**:从 `D:\ClaudeProject\ForgeUE_codex\src\framework\providers\` 整套移植适配。引入依赖:

- `litellm`(100+ provider 统一接入)
- `instructor`(Pydantic schema 自动 retry)
- `pydantic`(若环境未装)
- `httpx`(若环境未装,litellm 异步底层)

### 1.4 Router 启用度

**选 ① 单 model 配置(扩展点保留)**:CapabilityRouter 代码全量移植,但只配单 model policy,`fallback_models=[]`。中期再扩多 model 路由。

### 1.5 严格回归通过口径

**选 A 7/7 全 PASS + 单 dimension retry≤3**:

- 7 个 dimension 必须最终全部 PASS 才算 promotable
- 单 dimension 允许 `RetryPolicy.max_attempts=3` 内 retry(transient/timeout/529 等)
- 单次全链跑成功 = 1 份 promotable 证据(non-repeated)

### 1.6 执行模式

**选 I 可配 concurrency=N 带令牌桶**:

- 默认 `concurrency=3`(避免 ≥6 并发触发 MiniMax 中转 rate limit)
- 启动间 jitter `[100, 500]ms` 避雪崩
- Schema/config 暴露字段可调

### 1.7 聚合策略

**选 Ⅰ 纯结构拼接**:

- 7 个 dimension 各自的 candidate group 按 dimension key 索引拼接到 `design_space_report.dimensions[]`
- **不**做跨 dimension 去重 / 二轮 LLM review,聚合层零 LLM 调用
- 加 `per_dimension_batch_metadata`(per-batch usage / duration_ms / attempts / model / status)字段

### 1.8 BudgetTracker 限额行为

**选 i 只观测不限额**:

- 记录每 run 的 prompt_tokens / completion_tokens / total + per-model + per-dimension
- 落盘到 `ProjectState/runs/{run_id}/llm_usage.json`
- **不**设硬阈值阻断,future-proof 扩展点保留(`budget.observe_only: false` 切换)

### 1.9 与 MCP Agent 主路径定位

**选 P MCP Agent 仍主路径,LLM Internal 并列可切换**:

- `generator_provider ∈ {mcp_agent, llm, heuristic_fallback}`三者并列 promotable(`heuristic_fallback` 仍固化 promotable=False)
- 默认仍 MCP Agent;不动 Phase 11 既有优先级
- LLM Internal 重开只是拿回 promotable 资格

---

## 2. 架构(Architecture)

### 2.1 图 A — 改动焦点图(spec 内主图)

只画"本次改动 + 接口面",MCP Agent / HeuristicFallback 作黑盒。

```
            session.generator_provider 分支
                       │
   ┌───────────────────┼────────────────────────┐
   │                   │                        │
   ▼                   ▼                        ▼
┌──────────┐  ┌────────────────────┐  ┌──────────────────────┐
│ mcp_agent│  │ llm  (本次改造)    │  │ heuristic_fallback   │
│ (不动)   │  │                    │  │ (不动)              │
└──────────┘  │ LLMProvider 内部:  │  └──────────────────────┘
              │ 一次调 llm_client  │
              │       ↓ 改为       │
              │ candidates_batch_  │
              │ orchestrator       │
              └─────────┬──────────┘
                        │
                        │ 新增基础设施(只服务 llm 路径)
                        ▼
         ┌──────────────────────────────────────┐
         │ Compiler/stages/                      │
         │   candidates_batch_orchestrator.py    │
         │ Compiler/providers/                   │
         │   base / litellm_adapter / _retry /   │
         │   capability_router / model_registry  │
         │   / fake_adapter                      │
         │ Compiler/observability/               │
         │   secrets / compactor                 │
         │ Compiler/runtime/                     │
         │   budget_tracker                      │
         │ Schemas/                              │
         │   provider_call / retry_policy /      │
         │   design_space_report(扩字段)        │
         └──────────────────────────────────────┘

旧: Compiler/stages/llm_client.py(deprecate,保留以兼容签名)
```

### 2.2 图 B — 三路 Provider 全景图(同步增量补到 HLD §2.2 + LLD 04 §2.1)

显式标"新增基础设施只服务 LLM 路径"的对比关系。

```
                Compiler/pipeline/pipeline_orchestrator.py
                       (按 session.generator_provider 分支)
                                    │
        ┌───────────────────────────┼───────────────────────────────┐
        │ "mcp_agent"               │ "llm"                         │ "heuristic_fallback"
        ▼                           ▼                               ▼
┌──────────────────┐  ┌────────────────────────────┐  ┌──────────────────────────┐
│ stages/          │  │ stages/agent_protocol.py   │  │ stages/agent_protocol.py │
│   domain_skill_  │  │   LLMProvider              │  │   HeuristicFallback      │
│   runtime.py     │  │   (改 generate 内部实现)   │  │   Provider               │
│                  │  │                            │  │                          │
│ sidecar mode     │  │ Stage 4 Discovery /        │  │ _default_evaluator       │
│ ↓                │  │ Candidates / Convergence   │  │ 确定性算法               │
│ skill_runtime    │  │ ↓                          │  │                          │
│ Phase 11 已稳定  │  │ candidates_batch_orches.   │  │ promotable=False         │
│ promotable=True  │  │ (按 dimension 分批)        │  │                          │
└────────┬─────────┘  └──────────┬─────────────────┘  └────────────┬─────────────┘
         │                       │                                 │
         │                       │ uses                            │
         │                       ▼                                 │
         │       ┌────────────────────────────────────┐            │
         │       │ providers/                          │            │
         │       │   base ProviderAdapter ABC          │            │
         │       │   litellm_adapter async+structured  │            │
         │       │   _retry transient retry            │            │
         │       │   capability_router 单 model policy │            │
         │       │   model_registry 1 条注册           │            │
         │       │   fake_adapter offline 单测桩       │            │
         │       │ observability/                      │            │
         │       │   secrets API key 脱敏              │            │
         │       │   compactor 超长上下文裁剪          │            │
         │       │ runtime/                            │            │
         │       │   budget_tracker observe-only       │            │
         │       │                                     │            │
         │       │ ★ 仅 LLM 路径依赖这一基础设施块 ★   │            │
         │       └─────────────────────────────────────┘            │
         │                                                          │
         ▼                                                          ▼
┌─────────────────────┐                                ┌────────────────────────┐
│ skill_runtime/      │                                │ json / hashlib / yaml  │
│   skill_runtime.py  │                                │ 标准库                 │
│ (Skill Graph 执行)  │                                │ 无外部 LLM 依赖        │
└─────────────────────┘                                └────────────────────────┘

公共依赖(三路共用,本次不动):
  pipeline/session.py  CompilerSession + VALID_GENERATOR_PROVIDERS
  Schemas/compiler_session.schema.json
  Schemas/design_space_report.schema.json(本次扩 per_dimension_batch_metadata)
```

### 2.3 三条核心边界

1. **providers/** 层只懂"如何把一个 `ProviderCall` 变成 `ProviderResult`(或 typed exception)";不懂 dimension / design space / compiler session 等业务概念
2. **stages/candidates_batch_orchestrator.py** 是**唯一**懂"按 dimension 分批 + 聚合"的地方;把 7 个并发问题压到 `asyncio.Semaphore(3)` + 7 个 `ProviderCall`
3. **pipeline_orchestrator.py** 只做 generator_provider 分支选择(mcp_agent / llm / heuristic),不耦合 LLM 调用细节

### 2.4 CLAUDE.md "绝对不要修改" 清单兼容性

- 不动 `Source/*` C++ 核心 ✓
- 不动 `Scripts/bridge/*` Bridge 客户端 ✓
- 不动 `Scripts/orchestrator/*` ✓
- 改的范围:`Compiler/{providers(新),observability(新),runtime(新),stages,pipeline}` + `Config/llm_config*` + `Schemas/{design_space_report,compiler_session,provider_call(新),retry_policy(新)}` + Docs(HLD §2.2 增量 / LLD 04 §2.1 增量 / acceptance_report §残留翻面)— 全在"可以修改"清单内 ✓

### 2.5 文档同步面(实施完成后)

1. `Docs/superpowers/specs/2026-05-27-llm-internal-reopen-design.md` 首发(本 spec)
2. 实施完后 `Docs/design/HLD.md §2.2` 加图 B + 改"暂缓"为"重开 promotable"
3. 实施完后 `Docs/design/LLD/04_compiler.md §2.1` 加图 B + F-CMP-15 行补"litellm 升级"
4. `Docs/acceptance/acceptance_report.md` §残留 删 "LLM Internal 暂缓",改 "LLM Internal 是 UE 5.7 重构前置门禁";§3 模板项 F-CMP-15 留待 promotable 证据补完
5. `task.md` 跳转到 Phase 12 入口页(若新阶段建立)

---

## 3. 组件清单 + 接口契约(Components)

### 3.1 `Compiler/providers/`(新增,从 ForgeUE_codex 移植)

| 文件 | 角色 | 关键 API | 上游 / 下游 |
|---|---|---|---|
| `base.py` | Provider 抽象基类 + 4 类 typed exception + 调用/结果 dataclass | `class ProviderAdapter(ABC)` <br>`async acompletion(call) -> ProviderResult` <br>`async astructured_with_usage(call, schema) -> (BaseModel, usage)` <br>`@dataclass ProviderCall(model, messages, timeout_s, max_tokens, seed, api_key, api_base, extra)` <br>`exceptions: ProviderError / ProviderTimeout / ProviderUnsupportedResponse / SchemaValidationError` | 上游:被 `capability_router` / `candidates_batch_orchestrator` 引用 <br>下游:无(纯抽象) |
| `litellm_adapter.py` | LiteLLM 统一接入 + instructor structured + Anthropic prompt cache + auto-compact | `class LiteLLMAdapter(ProviderAdapter)` <br>`acompletion / astructured / astructured_with_usage` <br>`_maybe_apply_prompt_cache(call)` 内部 helper <br>`_maybe_auto_compact(call)` 内部 helper(读 `extra._forge_auto_compact_tokens`) | 上游:`capability_router` 注册 <br>下游:`litellm` + `instructor` SDK |
| `_retry.py` / `_retry_async.py` | transient 错误重试工具 | `with_transient_retry(fn, *, transient_check, max_attempts=2, backoff_s=2.0) -> T` <br>`is_transient_network_message(msg) -> bool` <br>`is_rate_limited(exc) -> bool`(新增,本期对 429/529 特殊退避) | 上游:`candidates_batch_orchestrator` 的 per-batch retry 包装 <br>下游:无 |
| `capability_router.py` | 按 ProviderPolicy 路由 + preferred→fallback 串行 + 调 budget_tracker 计费 | `class CapabilityRouter` <br>`register(adapter)` <br>`async acompletion(*, policy, call_template) -> (ProviderResult, model)` <br>`async astructured(*, policy, call_template, schema) -> (BaseModel, model, usage)` | 上游:`build_default_router()` 注册 LiteLLMAdapter <br>下游:`base.ProviderAdapter` + `runtime/budget_tracker` |
| `model_registry.py` | 默认 router 构造工厂(本期只配单 model + fallback=[]) | `build_default_router(config_path=None) -> CapabilityRouter` <br>`load_provider_policy_from_yaml(path) -> ProviderPolicy` | 上游:`pipeline_orchestrator` 启动时调一次 <br>下游:Config/llm_config.yaml + `capability_router` |
| `fake_adapter.py` | offline 单测桩,按 model 名队列脚本化响应 | `class FakeAdapter(ProviderAdapter)` <br>`program(model, outputs: list[FakeModelProgram])` <br>`@dataclass FakeModelProgram(text, schema_value, schema_builder, raise_error, usage)` | 上游:测试套件注册 <br>下游:无 |

### 3.2 `Compiler/observability/`(新增,移植)

| 文件 | 角色 | 关键 API | 上下游 |
|---|---|---|---|
| `secrets.py` | API key / token 脱敏 | `redact_mapping(d: dict) -> dict` 把 `api_key` 等字段值替换为 `***` <br>`redact_text(s: str) -> str` 正则脱敏文本 | 上游:`litellm_adapter._raw_debug` + evidence 落盘前调 <br>下游:无 |
| `compactor.py` | 超长 prompt 历史自动压缩 | `compact_messages(msgs, *, max_tokens, keep_tail_turns=4) -> (list[msg], stats)` 4 char/token 估算 | 上游:`litellm_adapter._maybe_auto_compact` <br>下游:无 |

### 3.3 `Compiler/runtime/`(新增,移植 + 改造)

| 文件 | 角色 | 关键 API | 与 ForgeUE 原版差异 |
|---|---|---|---|
| `budget_tracker.py` | per-run usage 累计(本期 **observe-only**) | `class BudgetTracker` <br>`record(*, step_id, model, cost_usd, usage_tokens)` <br>`@property spend / by_dimension / by_model / call_count` <br>`dump_evidence(path)` 落盘到 `ProjectState/runs/{run_id}/llm_usage.json` | **去掉** `would_exceed_after` 触发 `BudgetExceeded` 的硬阻断逻辑(对应决断 §1.8) |

### 3.4 `Compiler/stages/`(新增 1 改 1 deprecate 1)

| 文件 | 角色 | 关键 API | 上下游 |
|---|---|---|---|
| `candidates_batch_orchestrator.py` **(新)** | Stage 4 Candidates 按 dimension 分批 + concurrency=3 + 聚合 | `class LLMBatchExecutor` <br>`async run_candidates_batch(*, design_space, dimensions, router, policy, retry_policy, concurrency=3) -> AggregatedReport` <br>`@dataclass DimensionBatch(dimension_id, prompt_messages, schema_ref, attempt_count, duration_ms, usage, status)` <br>`@dataclass AggregatedReport(per_dimension: list[DimensionBatch], merged_design_space_report, promotable: bool)` | 上游:`agent_protocol.LLMProvider.generate` <br>下游:`providers.capability_router` + `runtime.budget_tracker` |
| `agent_protocol.py` **(改)** | `LLMProvider.generate` 内部从"一次调 llm_client" 改为"调 LLMBatchExecutor"。**公共签名不变**,只改私有实现 | `LLMProvider(provider_type="llm").generate(phase, context, system_prompt, ...)` 仍为同步签名,内部用 `asyncio.run(self._batch_executor.run_candidates_batch(...))` 适配 | 上游:`pipeline_orchestrator.resolve_provider` <br>下游:**改为** `stages.candidates_batch_orchestrator` |
| `llm_client.py` **(deprecate)** | 旧 `UnifiedLLMClient` + `load_llm_client_from_config` | 文件保留,内部不动。文件顶部加 `# DEPRECATED: use Compiler/providers/litellm_adapter instead, kept for legacy compatibility` 注释,后续 Phase 13 视情况删除 | 上游:无新调用方 <br>下游:无 |

### 3.5 `Compiler/pipeline/`(改 1)

| 文件 | 改动 |
|---|---|
| `pipeline_orchestrator.py` | line 28 `from ..stages.llm_client import load_llm_client_from_config` 替换为 `from ..providers.model_registry import build_default_router` <br>line 750-751 `llm_client=load_llm_client_from_config()` 替换为 `router=build_default_router()` <br>新增传递给 `LLMProvider(router=router, batch_concurrency=3)` <br>**其他 generator_provider 分支(mcp_agent / heuristic)入口完全不动** |
| `session.py` | `VALID_GENERATOR_PROVIDERS` 已含 `llm`(task09a 时扩过),保留不动 |

### 3.6 `Schemas/`(新 2 改 1 确认 1)

| 文件 | 角色 | 状态 |
|---|---|---|
| `provider_call.schema.json` **(新)** | `ProviderCall` 数据契约(model / messages / temperature / max_tokens / timeout_s / extra) | 配合 evidence trace 落盘格式 |
| `retry_policy.schema.json` **(新)** | RetryPolicy 契约(max_attempts / backoff_mode / retry_on enum) | 让 Stage 4 retry 行为可审计 |
| `design_space_report.schema.json` **(改)** | 加 `per_dimension_batch_metadata: array[{dimension_id, model, attempt_count, duration_ms, usage, status, error_class}]` 顶层字段 | 显式落地决断 §1.7 |
| `compiler_session.schema.json` **(确认)** | `generator_provider` enum 已含 `llm`(task09a 时扩) | 仅确认,不改 |

### 3.7 `Config/llm_config.example.yaml`(改 1)

扩字段(向后兼容):

```yaml
# 原 task09a 已有字段
provider: anthropic
model: anthropic/claude-3-haiku-20240307   # litellm 标准 model 名
api_key: REPLACE_ME
base_url: https://api.minimaxi.com/anthropic
max_tokens: 8192
temperature: 0.7
timeout_sec: 60

# 本次新增(可选,有默认值)
concurrency:
  candidates_batch: 3
  jitter_ms: [100, 500]
retry:
  max_attempts: 3
  backoff_mode: exponential
  retry_on: [timeout, transient_network, schema_fail]
prompt_cache:
  enabled: true
auto_compact:
  enabled: false
  max_tokens: 8000
budget:
  observe_only: true
  cost_cap_usd: null
```

### 3.8 接口契约图(组件互调关系)

```
pipeline_orchestrator
       │ 启动时 build_default_router()
       ▼
[model_registry] ── 注册 ──▶ [capability_router] ◀── 注入 ── [litellm_adapter]
                                                                  │ uses
                                                                  ▼
                                                       [observability/secrets + compactor]

pipeline_orchestrator (resolve_provider)
       │ generator_provider == "llm"
       ▼
[agent_protocol.LLMProvider] ── 持有 ──▶ [candidates_batch_orchestrator.LLMBatchExecutor]
       │ generate(phase, ...)                  │ run_candidates_batch(...)
       ▼                                       ▼
   (phase trace 不变)                  [capability_router.astructured] ──▶ adapter
                                              │ usage
                                              ▼
                                       [budget_tracker.record]
                                              │ run 结束
                                              ▼
                                       ProjectState/runs/{run_id}/llm_usage.json
```

### 3.9 责任边界总结(谁懂什么)

- **`providers/`** 只懂"如何把 ProviderCall 变成 ProviderResult",不懂业务
- **`observability/` + `runtime/`** 横切支撑,不绑业务
- **`candidates_batch_orchestrator.py`** 是**唯一**懂"按 dimension 分批 + 聚合"的地方
- **`agent_protocol.LLMProvider`** 是**唯一**懂"Stage 4 phase + GeneratorProvider 协议"的地方,内部委托给 batch executor
- **`pipeline_orchestrator.py`** 是**唯一**懂"三路 generator_provider 分支选择"的地方,不耦合任何 LLM 调用细节

---

## 4. 数据流(Data Flow)

### 4.1 happy path 主时序(7 dimension 全 PASS)

完整时序略,关键步骤:

1. `pipeline_orchestrator.resolve_provider(gp="llm")` 一次性建 router(`build_default_router()`)
2. `LLMProvider.generate(phase="candidates")` 拉 7 个 dim prompt + context bundle
3. `LLMBatchExecutor.run_candidates_batch(...)` 起 7 个 coroutine 经 `asyncio.Semaphore(3)` 节流并行
4. 每个 coroutine:acquire sem → jitter sleep → `router.astructured(policy, call, schema)` → `litellm.acompletion`(注入 prompt cache + auto-compact)→ instructor 解析为 Pydantic 对象 → 回传 (obj, model, usage)
5. `budget_tracker.record(dim, model, cost, usage)` 累计
6. 7 个 batch 完成后 aggregator 纯结构拼接 → `AggregatedReport(promotable = all success)`
7. `LLMProvider.generate` 包成 `design_space_report v3` 落盘
8. `pipeline_orchestrator` 走 schema validate + trace 落盘 + usage dump

### 4.2 失败 + retry 流(单 dimension transient timeout)

- attempt 1 → `ProviderTimeout`
- `_retry.transient_check(exc)` 返 True
- sleep `backoff_base_s * 2^0 = 2.0s` + jitter
- attempt 2 → `ProviderResult` → `DimensionBatch.status="success"`, `attempt_count=2`

**关键 invariant**:retry 期间 `ProviderCall.seed` 不变(若设置),便于 prompt cache hit。

### 4.3 失败 + 三次重试穷尽流(单 dimension 全失败)

- attempt 1/2/3 → 全 `ProviderTimeout` 或 `529 overloaded`
- 第 3 次后 max_attempts 到 → raise `ProviderTimeout`
- per-batch coroutine catch → `DimensionBatch.status="failed"`, `error_class="timeout"`, `attempt_count=3`
- 7 batch collect 后 `promotable = all(b.status=="success") = False`
- `design_space_report.partial = true`
- `pipeline_orchestrator` 看到 `promotable=False`,run 不进 promoted_artifacts

### 4.4 ProviderCall / ProviderResult 数据契约

```
ProviderCall                           ProviderResult                    DimensionBatch
─────────────                          ──────────────                    ──────────────
model       :str (litellm format)      text        :str                   dimension_id :str
messages    :[{role, content}]   ───▶  model       :str (chosen)   ───▶  prompt_messages :[...]
temperature :float                     usage       :{prompt,             schema_ref :str
max_tokens  :int                         completion, total}              attempt_count :int
timeout_s   :float (60)                raw         :{response_id,        duration_ms :int
seed        :int (per-batch fixed)       finish_reason}                  usage :{prompt,completion,total}
api_key     :str (router 注入)         (redacted)                        status :"success"|"failed"
api_base    :str (router 注入)                                            error_class :str|null
extra       :{_forge_prompt_cache:T,                                      raw_response_id :str|null
              _forge_auto_compact_tokens}                                 generator_call_template :ProviderCall(redacted)
```

### 4.5 Evidence 落盘点

| 落盘文件 | 内容 | 写入时机 | 路径 |
|---|---|---|---|
| `design_space_report.json` | 主产物(7 dim 聚合 + per_dimension_batch_metadata) | Stage 4 Candidates 完成时 | `ProjectState/runs/{run_id}/design_space_report.json` |
| `llm_usage.json` | budget_tracker dump(per-dim cost + total + by_model) | run 结束时(observe-only) | `ProjectState/runs/{run_id}/llm_usage.json` |
| `stage4_agent_traces/llm_internal/dim_{N}.json` | per-batch ProviderCall(redacted) + ProviderResult.raw + 三次 attempt timeline + retry decisions | 每个 batch 完成时 | `ProjectState/runs/{run_id}/stage4_agent_traces/llm_internal/` |
| `stage4_agent_traces/llm_internal/aggregation.json` | AggregatedReport 元数据 | aggregator 完成时 | 同上目录 |

**与已有 MCP Agent sidecar 并列**:`stage4_agent_traces/llm_internal/` 与 `stage4_mcp_agent_sidecar/` 同级,不交叉污染。

### 4.6 关键不变量

1. **provider_id 一致性**:同 run 内所有 `DimensionBatch.generator_call_template.model` 必须一致(本期单 model 假设)
2. **promotable 判定原子性**:`promotable = all(batch.status == "success")`,不允许 partial promote
3. **retry 计数封顶**:`max_attempts=3` 硬上限,fail-fast
4. **secrets 落盘前必脱敏**:任何写到 `stage4_agent_traces/` 的字段都先经 `redact_mapping`
5. **budget 不阻断**:`BudgetTracker.would_exceed_after` 在 observe-only 模式永远返 False

### 4.7 三路 generator_provider 数据流隔离

- `mcp_agent` → `domain_skill_runtime → skill_runtime` → evidence 落 `stage4_mcp_agent_sidecar/`
- `heuristic_fallback` → `agent_protocol.HeuristicFallbackProvider._default_evaluator` → evidence 落 `stage4_agent_traces/heuristic/`,固化 promotable=False
- `llm` (本次) → `agent_protocol.LLMProvider → candidates_batch_orchestrator` → evidence 落 `stage4_agent_traces/llm_internal/`,promotable = 7/7 success

---

## 5. 错误处理(Error Handling)

### 5.1 错误分类(4 类 typed exception + 1 类业务失败)

| Exception | 触发条件 | 性质 | 重试 |
|---|---|---|---|
| `ProviderTimeout` | HTTP timeout / "timed out" 关键字 / `winerror 10060` | transient 网络抖动 | ✓ |
| `ProviderError`(generic) | HTTP 4xx/5xx / SSL EOF / 429 / 5xx / connection reset | 按消息内容二次判定 | △ 仅 transient 子集 |
| `ProviderUnsupportedResponse` | `choices=[]` / `data=[]` / 协议字段缺失等 | deterministic 坏响应 | ✗ |
| `SchemaValidationError` | instructor 解析失败 / Pydantic 字段不符 | schema 漂移 | ✓ |
| `BatchPartialFailure`(业务) | 7 dim 中 ≥1 个最终失败(状态字段) | 业务级降级 | — |

### 5.2 RetryPolicy 默认值

```yaml
max_attempts: 3
backoff_mode: exponential        # exponential | fixed
backoff_base_s: 2.0              # sleep = base * 2^(N-1) 上限 8s
jitter_ms: [100, 500]
retry_on:
  - timeout
  - transient_network
  - schema_fail
no_retry_on:
  - unsupported_response
  - 4xx_non_429
```

### 5.3 retry 路径决策

```
attempt N 失败 ─▶ exception 类型?
                    │
                    ├── ProviderUnsupportedResponse ─▶ fail-fast,DimensionBatch.status="failed"
                    │
                    ├── ProviderTimeout
                    │     │ N+1 ≤ max_attempts?
                    │     ├── 是 ─▶ sleep backoff + jitter ─▶ attempt N+1
                    │     └── 否 ─▶ failed + error_class="timeout"
                    │
                    ├── SchemaValidationError(instructor 自带 1 次 schema retry 后再触发)
                    │     │ N+1 ≤ max_attempts?
                    │     ├── 是 ─▶ 同 timeout 路径(不改 prompt 保 cache hit)
                    │     └── 否 ─▶ failed + error_class="schema_fail"
                    │
                    └── ProviderError(generic)
                          │ is_transient_network_message(str(exc))?
                          ├── 是 ─▶ 同 timeout 路径
                          └── 否 ─▶ failed + error_class="provider_error"
```

### 5.4 rate limit(429 / 529)特殊处理

```python
# _retry.py 增强(本次新增)
def is_rate_limited(exc) -> bool:
    msg = str(exc).lower()
    return "429" in msg or "529" in msg or "rate" in msg or "overload" in msg

# candidates_batch_orchestrator 内 retry 时:
if is_rate_limited(exc):
    sleep_s = max(backoff_base_s * 2 ** attempt, 5.0) + random_jitter()
else:
    sleep_s = backoff_base_s * 2 ** attempt + random_jitter()
```

Semaphore 节流是第一道防线(concurrency=3),provider 端令牌桶仍可能限流,retry 是第二道防线。

### 5.5 dimension 间错误隔离

```python
async def one_batch(dim):
    async with sem:
        await asyncio.sleep(random.uniform(*jitter_ms) / 1000)
        try:
            return await _retry_loop(dim, retry_policy)
        except (ProviderTimeout, ProviderError, SchemaValidationError) as exc:
            return DimensionBatch(
                dimension_id=dim.id, status="failed",
                error_class=_classify(exc), attempt_count=N,
            )

results = await asyncio.gather(*(one_batch(d) for d in dimensions))
promotable = all(r.status == "success" for r in results)
```

**关键不变量**:`one_batch` **永不向外抛 ProviderError/Timeout/SchemaValidationError**,所有 LLM 层 exception 都内化为 `DimensionBatch.status="failed"`,让 `asyncio.gather` 一定能拿到 7 条结果。

### 5.6 schema validation 失败特别处理

1. 不修改 prompt(保 cache hit)
2. 保持 ProviderCall.seed 不变
3. 退避 + retry,期望 temperature>0 下抽出不同 schema-valid 输出
4. 若 3 次都 schema_fail,落 `error_class="schema_fail"`,evidence 保留每次 attempt 的 raw 响应(redacted)

### 5.7 budget 异常(observe-only)

| 情况 | 行为 |
|---|---|
| `cost_cap_usd: null`(默认) | `would_exceed_after` 永远返 False |
| usage 拿不到 | 落 `usage={}`,evidence 标 "usage_unavailable" |
| `cost_cap_usd` 显式配置 | 仅 WARN log + evidence 标 `over_budget=true`,不中断 |

### 5.8 全 run abort 兜底(pipeline_orchestrator 层)

| 情况 | 兜底 |
|---|---|
| `build_default_router()` 失败 | 转 heuristic_fallback(若允许),否则拒绝 run |
| `litellm` / `instructor` 模块未安装 | 同上 |
| `asyncio` 嵌套 event loop 异常 | 暴露给 pipeline,要求显式 async 接入 |
| KeyboardInterrupt / SystemExit | 向上传播 + evidence 标 `terminated_by_user` |
| `OSError`(evidence 写盘失败) | 向上传播 + 日志 `evidence_write_failed` |

### 5.9 错误信息脱敏

所有 evidence 落盘前,exception message 必经 `redact_text(str(exc))`,`raw_response_id` 等元字段可保留。

### 5.10 错误处理总表

| 场景 | 单 dim 处理 | 整 run promotable |
|---|---|---|
| 7 dim 全首次 PASS | success(attempt=1) | true |
| 个别 dim 1-2 次 retry 后 PASS | success(attempt=2-3) | true |
| 单 dim 3 次都失败(timeout) | failed(timeout) | **false** |
| 单 dim unsupported_response | failed(unsupported,attempt=1) | **false** |
| rate limit 全收敛 | 全 success | true |
| router 启动失败 | 不进 batch | 切 heuristic 或 abort |
| schema 3 次都不符 | failed(schema_fail) | **false** |

---

## 6. 测试(Testing)

### 6.1 测试金字塔(新增 7 文件)

```
                    L2-D 真 LLM 端到端  (1 文件,需 API key)
                  ─────────────────────────────────────────
                 L2-C 系统测试套件接入  (1 文件)
                ─────────────────────────────────────────────
               L2-B fake_adapter 集成测试  (2 文件,offline)
              ─────────────────────────────────────────────────
             L2-A providers/observability 单元测试  (2 文件,offline)
            ─────────────────────────────────────────────────────
           诊断脚本  (1 文件,llm_internal_batch_diagnostic.py)
```

### 6.2 L2-A providers/observability 单元(2 文件)

**`Tests/scripts/test_providers_unit.py`**:`ProviderCall` 字段 / exception 继承 / CapabilityRouter 注册 + preferred-fallback 顺序 / `_retry` transient 判定 + backoff / litellm prompt cache 注入。

**`Tests/scripts/test_observability_unit.py`**:`redact_mapping`(嵌套)/`redact_text`(Bearer token / sk- key)/`compact_messages`(短不动 / 长裁剪 / 4 char/token 口径)。

### 6.3 L2-B fake_adapter 集成测试(2 文件)

**`Tests/scripts/test_candidates_batch_orchestrator.py`**:happy / single retry / 3x timeout / unsupported no-retry / schema fail / concurrency=3 enforcement / jitter / promotable logic / per_dim metadata / evidence redaction(10 case)。

**`Tests/scripts/test_llm_provider_integration.py`**:`LLMProvider.generate` 路由到 batch executor / discovery+convergence 不走 batch / 公共签名不变 / router 失败传播 / heuristic_fallback flag。

### 6.4 L2-C 系统测试套件接入(1 文件)

**`Tests/scripts/test_llm_internal_system_integration.py`**:Phase 11 主链 generator_provider="llm" 用 FakeAdapter 桩走通 / mcp_agent 仍 work / heuristic 仍 work / `is_promotable` LLM 路径判定。

**run_system_tests.py 改动**:推荐**新增 Stage 11 "LLM Internal Reopen"**(11→12 Stage)而非改现有 Stage,避免破坏 240+ 现有 case。

### 6.5 L2-D 真 LLM 端到端验收(1 文件)

**`Tests/scripts/llm_internal_batch_real_run.py`** — acceptance 证据生成器:

```
执行流:
  1. 读 Plugins/AgentBridge/Config/llm_config.yaml
  2. 跑 Phase 11 主链至 Stage 4 Candidates,generator_provider="llm"
  3. 7 dimension 全部跑,concurrency=3
  4. 7/7 PASS → promotable=true
  5. 产出:
     - ProjectState/runs/{run_id}/design_space_report.json
     - ProjectState/runs/{run_id}/llm_usage.json
     - ProjectState/runs/{run_id}/stage4_agent_traces/llm_internal/{dim_*.json + aggregation.json}
     - ProjectState/Reports/{date}/llm_internal_reopen_acceptance.md + .json
  6. 支持 --repeat N(本期 N=1 即满足决断 §1.5 non-repeated)
```

### 6.6 诊断脚本(1 文件)

**`Tests/scripts/llm_internal_batch_diagnostic.py`**:

| 模式 | 用途 |
|---|---|
| `--mode=concurrency-sweep` | concurrency=1/2/3/5/7 各档总耗时 + 失败率 |
| `--mode=retry-stress` | 强制注入 timeout 看 retry 收敛 |
| `--mode=baseline-compare` | 与 2026-04-16 原 `stage4_candidates_diagnostic.json` 对比 |

### 6.7 fake_adapter 用法范式

```python
from Compiler.providers.fake_adapter import FakeAdapter, FakeModelProgram
from Compiler.providers.capability_router import CapabilityRouter

def make_test_router():
    fa = FakeAdapter()
    fa.program("anthropic/claude-3-haiku-20240307", outputs=[
        FakeModelProgram(schema_value={"dimension_id": "d1", "candidates": [...]}),
        FakeModelProgram(raise_error=ProviderTimeout("simulated")),
        FakeModelProgram(schema_value={"dimension_id": "d3", "candidates": [...]}),
    ])
    router = CapabilityRouter()
    router.register(fa)
    return router
```

### 6.8 acceptance 证据落盘路径

| 证据 | 路径 | 关联 acceptance_report |
|---|---|---|
| 真 LLM 7/7 PASS | `ProjectState/Reports/2026-XX-XX/llm_internal_reopen_acceptance.{md,json}` | 删 §残留 LLM 暂缓 + 补 §1 主表 F-CMP-15 勾选 |
| 单元 + 集成 pytest 全绿 | `ProjectState/Reports/2026-XX-XX/llm_internal_unit_test_passed.md` | §3 F-TST-01/02 关联 |
| concurrency sweep | `ProjectState/Reports/2026-XX-XX/llm_internal_concurrency_sweep.json` | 选填,follow-up 数据 |

### 6.9 测试覆盖率口径

- `providers/` + `observability/` + `runtime/budget_tracker`:**单元覆盖率 ≥ 85%**
- `candidates_batch_orchestrator`:**关键路径 100%**(分批/retry/聚合/promotable/evidence 5 主路径)
- `agent_protocol.LLMProvider`:**改动行 100%**
- 真 LLM 端到端:**1 次 7/7 PASS** 即可(决断 §1.5 non-repeated)

### 6.10 与 CLAUDE.md 测试相关红线一致性

- `AgentBridgeTests/` C++ 不动 ✓
- `run_system_tests.py` 在 "可以修改" 范围,改动是新增 Stage 不删现有 ✓
- 不引入新 C++ 测试 ✓
- 真 LLM 测试默认需要本地 `llm_config.yaml`,**CI 跳过 L2-D**,只跑 L2-A/B/C(offline)✓

---

## 7. YAGNI 划界(本期不做)

| 不在范围 | 原因 |
|---|---|
| 多 model 路由 / fallback_models 配置 | 决断 §1.4 单 model + 扩展点保留,留中期 |
| BudgetTracker 硬阈值 / human-review terminate | 决断 §1.8 observe-only,留中期 |
| 跨 dimension 二轮 LLM review / 去重聚合 | 决断 §1.7 纯结构拼接,加 LLM 反而是新失败源 |
| Image / Audio / Video provider 接入 | ForgeUE_codex `aimage_generation` 等接口不移植,本期 LLM 文本路径专用 |
| ManagedProcessRegistry / ScheduleEngine / Tracing 全套 observability | ForgeUE_codex 这些与游戏管线特性强绑定,本期不需要 |
| Discovery / Convergence 也走分批 | 本期仅 Candidates 改造,Discovery/Convergence 仍走单次调用(若它们也出问题再单独 spec) |
| 自动迁移 `llm_client.py` 调用方 | 文件 deprecate 不删,Phase 13 评估是否真清理 |
| UE 5.7 binding 适配 | 本 spec 不涉及 UE 引擎层,与 UE 5.7 重构正交但作前置门禁 |
| pricing_probe / comparison / engine_bridge/godot4 | ForgeUE_codex 特有,与本项目无关 |

---

## 8. 验收口径(Acceptance Criteria)

### 8.1 必须满足(决断 §1.5)

- [ ] 真 LLM 端到端 1 次跑 7/7 PASS,产物 `design_space_report.json` `promotable=true`
- [ ] `ProjectState/Reports/{date}/llm_internal_reopen_acceptance.{md,json}` 完整落盘
- [ ] L2-A/B 全部 pytest 绿(覆盖率 ≥ 85%)
- [ ] L2-C 系统测试套件 mcp_agent / heuristic / llm 三路均 PASS
- [ ] `acceptance_report.md` §残留 删 "LLM Internal 暂缓" 改写 + §1 主表 F-CMP-15 勾选(由 msc 手动勾选,Claude/Codex 不自动)
- [ ] CLAUDE.md "绝对不要修改" 红线 0 违反(实施完做 final 交叉检查)

### 8.2 加分项(若顺手做)

- [ ] HLD §2.2 + LLD 04 §2.1 加图 B 全景图
- [ ] `llm_internal_concurrency_sweep.json` 产出(为后续 model 路由扩展提供数据)
- [ ] 与 2026-04-16 diagnostic 基线对比(原失败 case 现 PASS 比例)

### 8.3 不计入验收(纯 follow-up 性质)

- 旧 `llm_client.py` 物理删除(Phase 13 再评估)
- pipeline_orchestrator 通用化让 Discovery/Convergence 也复用分批(若本期没出问题暂不动)
- 多 model 路由实测(中期 spec 单独立项)

---

## 9. 风险与 follow-up

### 9.1 已知风险

| 风险 | 影响 | 缓解 |
|---|---|---|
| `litellm` / `instructor` 版本兼容性 | 真 LLM run 启动失败 | model_registry 启动期试探性 `acompletion` smoke,失败则清晰报错 + 回 heuristic |
| `concurrency=3` 仍触发 MiniMax 中转 rate limit | 部分 retry 频繁,虚耗 token | retry 路径已有 rate-limit 特殊退避,evidence 暴露 retry 次数供 follow-up 调参 |
| LiteLLM 对 MiniMax 中转 base_url 的兼容性未实测 | adapter 接入失败 | spec 实施前先做 1 次 1-message smoke 验证 |
| `instructor` 对 Anthropic-via-MiniMax 中转的 tool_use 响应支持 | structured 输出失败 | 若不兼容,降级到 `acompletion` + `json.loads` + jsonschema 手工校验(已有 spec §5.6 退路) |
| asyncio + sync `LLMProvider.generate` 桥接(`asyncio.run` in sync ctx) | 嵌套 event loop 异常 | 单测覆盖 + base.py `_run_sync` 已有 raise 清晰报错 |

### 9.2 follow-up 候选(实施后建 backlog)

- FU-LLM-01:多 model 路由实测(中期 spec)
- FU-LLM-02:Discovery / Convergence 也走分批(若实测有类似负载问题)
- FU-LLM-03:旧 `llm_client.py` 物理清理(Phase 13)
- FU-LLM-04:BudgetTracker 硬阈值模式启用(中期 — 当真 run 量大到需要预算阻断时)
- FU-LLM-05:prompt cache 命中率 evidence 暴露(litellm `cache_creation_input_tokens` / `cache_read_input_tokens`)
- FU-LLM-06:UE 5.7 重构期间对 LLM 路径做 regression 验证(与 mcp_agent 主路径同步基线)

---

## 10. 实施序列预告(交给 writing-plans)

writing-plans 阶段应拆出的关键 task 大致顺序(供 plan 作者参考,不是硬约束):

1. 依赖准备:litellm / instructor / pydantic / httpx 装版本探测
2. 移植 `providers/{base,_retry,_retry_async}.py`
3. 移植 + 适配 `providers/litellm_adapter.py`(改 import 路径 + 去 ForgeUE 特有 hook)
4. 移植 `observability/{secrets,compactor}.py`
5. 移植 + 改造 `providers/{capability_router,model_registry}.py`(单 model + observe-only budget)
6. 移植 `providers/fake_adapter.py`
7. 移植 + 改造 `runtime/budget_tracker.py`(去硬阻断)
8. Schema 升级:`provider_call.schema.json` + `retry_policy.schema.json` 新建,`design_space_report.schema.json` 扩字段
9. 实现 `stages/candidates_batch_orchestrator.py`(本期最难一块)
10. 改造 `stages/agent_protocol.LLMProvider.generate` 委托 batch executor
11. 改 `pipeline/pipeline_orchestrator.py` 装 router
12. 扩 `Config/llm_config.example.yaml`
13. 写 L2-A / L2-B 单元 + 集成测试(7 文件 × N case)
14. 写 L2-D `llm_internal_batch_real_run.py` 验收脚本
15. 跑 acceptance:真 LLM 1 次 7/7 + 落 `ProjectState/Reports/{date}/llm_internal_reopen_acceptance.*`
16. 同步文档:HLD §2.2 / LLD 04 §2.1 / acceptance_report §残留 翻面 / task.md 跳转
17. document-release skill + git push 收尾

---

## 附录 A:依赖关系一句话索引

- 本 spec 决断锚:`Docs/acceptance/acceptance_report.md:452` "§Phase 11 残留与重构注意事项"
- 实测诊断锚:`ProjectState/Reports/2026-04-16/stage4_candidates_prompt_vs_provider_diagnostic.md`
- task09a 实现锚:`ProjectState/Reports/2026-04-16/task09a_phase11_llm_internal.md`
- task09b 暂停锚:`ProjectState/Reports/2026-04-16/task09b_llm_internal_pause_sync.md`
- ForgeUE 参照锚:`D:\ClaudeProject\ForgeUE_codex\src\framework\providers\`(项目外只读引用)
- 主链 Stage 4 SRS 锚:`Docs/requirements/SRS.md#4` Skill/Spec/Handoff 四层主链
- MCP 总口径 HLD 锚:`Docs/design/HLD.md#4`
- CLAUDE.md 红线锚:`CLAUDE.md` "绝对不要修改的文件" + "可以修改的文件"
- 现有 generator_provider enum 锚:`Plugins/AgentBridge/Compiler/pipeline/session.py:35`
- 旧 llm_client 锚:`Plugins/AgentBridge/Compiler/stages/llm_client.py`

## 附录 B:9 项决断速查表

| # | 主题 | 选项 | 理由 |
|---|---|---|---|
| §1.1 | 改造范围 | C 全栈系统化(含 Schema) | LLM 一等公民,不只 patch |
| §1.2 | 与 UE 5.7 关系 | A LLM 先行,前置门禁 | UE 5.7 E2E 需要 LLM 作 generator 变量 |
| §1.3 | 参照力度 | α 重度移植 | litellm + instructor + 完整 ForgeUE 框架 |
| §1.4 | Router 启用度 | ① 单 model + 扩展点 | 中期再扩多 model,本期不被矩阵拖 |
| §1.5 | 通过口径 | A 7/7 PASS + retry≤3 | 严格回归,与原暂停决策对齐 |
| §1.6 | 执行模式 | I concurrency=3 + 令牌桶 | 平衡耗时与 rate limit |
| §1.7 | 聚合策略 | Ⅰ 纯结构拼接 + per-batch metadata | 零额外 LLM 调用 = 零新失败源 |
| §1.8 | BudgetTracker | i 只观测不限额 | 提供成本可见性,本期不阻断 run |
| §1.9 | 主路径定位 | P 三者并列可切换 | 默认仍 MCP Agent,LLM 拿回 promotable 资格 |
