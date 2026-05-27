# LLM Internal Reopen + Provider Framework Migration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development`(推荐)或 `superpowers:executing-plans` 来按任务执行此计划。所有步骤使用 checkbox(`- [ ]`)语法。

**Goal:** 把 Phase 11 收尾时暂缓的 LLM Internal 路径重开为 promotable 候选,通过重度移植 ForgeUE_codex providers/ 框架 + Stage 4 Candidates 按 dimension 分批改造,让 `generator_provider="llm"` 在严格回归口径下 7/7 PASS,作为 UE 5.7 重构的前置门禁。

**Architecture:** Compiler/ 子树下新增 4 个子目录(`providers/` `observability/` `runtime/` 中的 budget_tracker.py)和 1 个新 stage 文件(`candidates_batch_orchestrator.py`);Stage 4 LLMProvider 内部委托给 batch executor;litellm + instructor + Pydantic 接管 provider 调用与 schema 校验。三路 generator_provider(mcp_agent / llm / heuristic_fallback)互不污染。

**Tech Stack:** Python 3.x + litellm + instructor + pydantic + httpx + pyyaml + pytest + asyncio.Semaphore;不引入新 C++ 依赖,不动 UE Editor。

**Spec 来源**:`Docs/superpowers/specs/2026-05-27-llm-internal-reopen-design.md` (v1.0,9 项决断 + 5 节逐节确认)

---

## 前置说明

### 工作目录

所有路径相对项目根 `D:\UnrealProjects\Mvpv4TestCodex`(Windows + Git-Bash + PowerShell 7)。

### Task 粒度

- 代码类 step:2-5 分钟
- 测试类 step(写 + 跑 + commit):3-8 分钟
- 文档同步 step:10-30 分钟

### 分支建议

在 `feat/llm-internal-reopen` 分支(或新阶段名 `phase12-llm-reopen`)执行,可考虑用 `superpowers:using-git-worktrees` skill 起隔离 worktree(避免与主线交叉污染)。

每个 Phase 末尾走 `superpowers:verification-before-completion`,Phase 4 末尾跑 `document-release` 收尾。

### Phase 依赖关系

```
Phase 0 (T01-T07) 依赖装 + 基础设施移植
        │
        ▼
Phase 1 (T08-T09) Schema 升级       ◀── 可与 Phase 0 后段并行
        │
        ▼
Phase 2 (T10-T12) 核心调度层
        │
        ▼
Phase 3 (T13-T16) 配置 + 离线测试
        │
        ▼
Phase 4 (T17-T20) 真 LLM 验收 + 文档同步
```

T01 依赖装是所有后续 task 的硬前置;T08-T09 Schema 可在 T03 后并行;T17(L2-D 真 LLM 脚本)与 T18(跑真 LLM)是顺序依赖,中间需要本地 `llm_config.yaml` 含真 API key。

### 验证策略

每个 task 严格 TDD:**先写失败测试 → 跑确认失败 → 写最小实现 → 跑确认通过 → commit**。code-only patch 也要先写 smoke 验证(import / 模块可载入)。

---

## File Structure

### 新建文件(17 个)

```
Plugins/AgentBridge/Compiler/
├── providers/                                  # 新子目录
│   ├── __init__.py
│   ├── base.py                                 # ProviderAdapter ABC + 4 类异常 + ProviderCall/Result
│   ├── litellm_adapter.py                      # LiteLLMAdapter async-first + prompt cache + auto-compact
│   ├── _retry.py                               # with_transient_retry + is_transient_network_message + is_rate_limited
│   ├── _retry_async.py                         # async 版 transient retry
│   ├── capability_router.py                    # CapabilityRouter 单 model policy + 扩展点
│   ├── model_registry.py                       # build_default_router + load_provider_policy_from_yaml
│   └── fake_adapter.py                         # FakeAdapter + FakeModelProgram (offline 单测桩)
├── observability/                              # 新子目录
│   ├── __init__.py
│   ├── secrets.py                              # redact_mapping + redact_text
│   └── compactor.py                            # compact_messages 4 char/token 估算
├── runtime/                                    # 新子目录
│   ├── __init__.py
│   └── budget_tracker.py                       # BudgetTracker observe-only
└── stages/
    └── candidates_batch_orchestrator.py        # 本 plan 最难一块:Stage 4 分批 + 聚合

Plugins/AgentBridge/Schemas/
├── provider_call.schema.json                   # 新
└── retry_policy.schema.json                    # 新

Plugins/AgentBridge/Tests/scripts/
├── test_providers_unit.py                      # L2-A
├── test_observability_unit.py                  # L2-A
├── test_candidates_batch_orchestrator.py       # L2-B
├── test_llm_provider_integration.py            # L2-B
├── test_llm_internal_system_integration.py     # L2-C
├── llm_internal_batch_real_run.py              # L2-D 真 LLM 验收脚本
└── llm_internal_batch_diagnostic.py            # 诊断脚本
```

### 修改文件(7 个)

```
Plugins/AgentBridge/Compiler/stages/agent_protocol.py            # LLMProvider.generate 内部改委托
Plugins/AgentBridge/Compiler/stages/llm_client.py                # 顶部加 DEPRECATED 注释,内容不动
Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py   # load_llm_client_from_config → build_default_router
Plugins/AgentBridge/Schemas/design_space_report.schema.json      # 加 per_dimension_batch_metadata 字段
Plugins/AgentBridge/Config/llm_config.example.yaml               # 扩 concurrency / retry / prompt_cache / auto_compact / budget
Plugins/AgentBridge/Tests/run_system_tests.py                    # 新增 Stage 11 "LLM Internal Reopen"
Docs/design/HLD.md                                                # §2.2 加图 B + 改"暂缓"措辞
Docs/design/LLD/04_compiler.md                                    # §2.1 加图 B + F-CMP-15 行补 "litellm 升级"
Docs/acceptance/acceptance_report.md                              # §残留 翻面 + §1 F-CMP-15 留待 msc 勾
task.md                                                           # 跳转 Phase 12 入口(若新阶段建立)
```

### Evidence 输出(实施期产生)

```
ProjectState/runs/{run_id}/
├── design_space_report.json                                     # 主产物
├── llm_usage.json                                                # budget_tracker dump
└── stage4_agent_traces/llm_internal/
    ├── dim_1.json ... dim_7.json
    └── aggregation.json

ProjectState/Reports/{date}/
├── llm_internal_reopen_acceptance.md
├── llm_internal_reopen_acceptance.json
└── llm_internal_unit_test_passed.md
```

---

# Phase 0:依赖装 + 基础设施移植(T01-T07)

## Task 01:依赖准备 + 装版本探测

**Files:**
- Create: `Plugins/AgentBridge/Scripts/setup/check_llm_deps.py`
- Test: `Plugins/AgentBridge/Tests/scripts/test_llm_deps_smoke.py`

**目的**:litellm / instructor / pydantic / httpx 装版本探测,提供清晰错误提示(避免后续 task 启动后才发现依赖缺失)。

- [ ] **Step 1:写 smoke 测试**

`Plugins/AgentBridge/Tests/scripts/test_llm_deps_smoke.py`:

```python
"""LLM 依赖装载 smoke 测试 — 验证 litellm/instructor/pydantic/httpx 可 import。"""

import importlib

import pytest


REQUIRED_PACKAGES = {
    "litellm": "1.0",       # 最低版本占位,以实际装为准
    "instructor": "0.5",
    "pydantic": "2.0",
    "httpx": "0.25",
}


@pytest.mark.parametrize("pkg_name", list(REQUIRED_PACKAGES.keys()))
def test_required_package_importable(pkg_name: str) -> None:
    """每个必需包必须可 import,否则后续 LLM 路径无法工作。"""
    try:
        mod = importlib.import_module(pkg_name)
    except ImportError as exc:
        pytest.fail(f"{pkg_name} 未安装: {exc}")
    assert mod is not None
```

- [ ] **Step 2:跑测试确认失败(若装则跳过)**

Run: `pytest Plugins/AgentBridge/Tests/scripts/test_llm_deps_smoke.py -v`

Expected:若未装则 FAIL;若已装则 PASS(后者也是 OK,可跳过 Step 3 直接 commit)。

- [ ] **Step 3:装依赖**

```bash
pip install "litellm>=1.0" "instructor>=0.5" "pydantic>=2.0" "httpx>=0.25"
```

记录实际装版本到 `Plugins/AgentBridge/Scripts/setup/check_llm_deps.py`:

```python
"""LLM 依赖版本登记 — 实施期实际装版本快照。"""

import sys

# 实施期填入实际版本,格式 "pkg>=actual_version"
REQUIRED = {
    "litellm": ">=1.0",
    "instructor": ">=0.5",
    "pydantic": ">=2.0",
    "httpx": ">=0.25",
}


def check_versions() -> dict[str, str | None]:
    """返回 {pkg: installed_version | None}。"""
    import importlib.metadata as md
    result: dict[str, str | None] = {}
    for pkg in REQUIRED:
        try:
            result[pkg] = md.version(pkg)
        except md.PackageNotFoundError:
            result[pkg] = None
    return result


if __name__ == "__main__":
    versions = check_versions()
    print("LLM 依赖装版本探测:")
    for pkg, ver in versions.items():
        print(f"  {pkg}: {ver or '未装'} ({REQUIRED[pkg]})")
    missing = [p for p, v in versions.items() if v is None]
    sys.exit(1 if missing else 0)
```

- [ ] **Step 4:再跑测试确认通过**

Run: `pytest Plugins/AgentBridge/Tests/scripts/test_llm_deps_smoke.py -v && python Plugins/AgentBridge/Scripts/setup/check_llm_deps.py`

Expected:pytest 全 PASS;check 脚本退出 0 并打印实际版本。

- [ ] **Step 5:commit**

```bash
git add Plugins/AgentBridge/Tests/scripts/test_llm_deps_smoke.py \
        Plugins/AgentBridge/Scripts/setup/check_llm_deps.py
git commit -m "feat(llm-reopen): T01 依赖装版本探测 + smoke 测试"
```

---

## Task 02:移植 providers/{base, _retry, _retry_async}

**Files:**
- Create: `Plugins/AgentBridge/Compiler/providers/__init__.py`
- Create: `Plugins/AgentBridge/Compiler/providers/base.py`
- Create: `Plugins/AgentBridge/Compiler/providers/_retry.py`
- Create: `Plugins/AgentBridge/Compiler/providers/_retry_async.py`
- Reference (only-read): `D:\ClaudeProject\ForgeUE_codex\src\framework\providers\{base,_retry,_retry_async}.py`
- Test: 暂无(T14 统一写单元测试)

**改动差异要点**:
- import 路径从 `framework.providers.base` → `Compiler.providers.base`(本项目使用相对 import)
- `base.py` 保留全部接口,**不动**(纯抽象,无 ForgeUE 业务耦合)
- `_retry.py` 增加 `is_rate_limited(exc) -> bool` 函数(spec §5.4 要求)

- [ ] **Step 1:建子目录 + `__init__.py`**

```bash
mkdir -p Plugins/AgentBridge/Compiler/providers
```

`Plugins/AgentBridge/Compiler/providers/__init__.py`:

```python
"""Provider Framework — LLM 抽象层。

从 ForgeUE_codex `src/framework/providers/` 重度移植适配,服务 Stage 4 Candidates 分批生成。
- base: ProviderAdapter 抽象 + 4 类 typed exception
- litellm_adapter: LiteLLM + Instructor 默认实现
- _retry / _retry_async: transient 错误重试工具
- capability_router: 按 ProviderPolicy 路由
- model_registry: 默认 router 构造工厂
- fake_adapter: offline 单测桩
"""

from .base import (
    ProviderAdapter,
    ProviderCall,
    ProviderResult,
    ProviderError,
    ProviderTimeout,
    ProviderUnsupportedResponse,
    SchemaValidationError,
)

__all__ = [
    "ProviderAdapter",
    "ProviderCall",
    "ProviderResult",
    "ProviderError",
    "ProviderTimeout",
    "ProviderUnsupportedResponse",
    "SchemaValidationError",
]
```

- [ ] **Step 2:写 `base.py`(从 ForgeUE 直拷贝,改 docstring)**

把 `D:/ClaudeProject/ForgeUE_codex/src/framework/providers/base.py` 完整内容拷贝到 `Plugins/AgentBridge/Compiler/providers/base.py`。

**修改点**:
- 文件顶部 docstring 把 "§F1-1, Plan C async" 替换为本项目语境:

```python
"""Provider adapter contract — async-first(主表面)+ sync shim(向后兼容)。

从 ForgeUE_codex 移植适配:把 LLM 提供商抽象成统一的 ProviderAdapter,
让 Stage 4 Candidates batch executor 不绑死具体 SDK。

Async 主表面:`acompletion` / `astructured` / `astructured_with_usage`。
Sync 子集是 `asyncio.run` shim,服务现有 sync 调用方(LLMProvider.generate 等)。
"""
```

- 其余代码原样保留(`_run_sync` / `_is_overridden` / `ProviderAdapter` ABC / `ProviderCall` / `ProviderResult` / `ImageResult` / 4 类异常)
- 删除 ForgeUE 特有的 `aimage_*` 接口(本期不做图像,YAGNI)— 把 `ProviderAdapter.aimage_generation` / `aimage_edit` 移除,`ImageResult` dataclass 也删

- [ ] **Step 3:写 `_retry.py`(基于 ForgeUE + 加 is_rate_limited)**

把 `D:/ClaudeProject/ForgeUE_codex/src/framework/providers/_retry.py` 完整拷贝。

**追加函数**(spec §5.4 要求):

```python
_RATE_LIMIT_MARKERS: tuple[str, ...] = (
    "429",
    "529",
    "rate limit",
    "rate-limit",
    "overload",
    "too many requests",
)


def is_rate_limited(exc: BaseException) -> bool:
    """True iff exception 像 429 / 529 / rate-limit / overload 类限流签名。

    用于 candidates_batch_orchestrator 在 retry 时区分:
      - 普通 transient 抖动 → 用常规 backoff
      - rate limit → 用更长退避(避免连续撞墙)
    """
    msg = str(exc).lower()
    return any(m in msg for m in _RATE_LIMIT_MARKERS)
```

- [ ] **Step 4:写 `_retry_async.py`(从 ForgeUE 直拷贝)**

把 `D:/ClaudeProject/ForgeUE_codex/src/framework/providers/_retry_async.py` 完整拷贝到 `Plugins/AgentBridge/Compiler/providers/_retry_async.py`,只改 docstring 顶部引用为本项目语境。

- [ ] **Step 5:写 smoke 测试 + 跑 + commit**

`Plugins/AgentBridge/Tests/scripts/test_providers_smoke.py`:

```python
"""providers 子树 smoke 测试 — 模块可 import,类层次正确。"""

from Plugins.AgentBridge.Compiler.providers import (
    ProviderAdapter,
    ProviderCall,
    ProviderResult,
    ProviderError,
    ProviderTimeout,
    ProviderUnsupportedResponse,
    SchemaValidationError,
)
from Plugins.AgentBridge.Compiler.providers._retry import (
    with_transient_retry,
    is_transient_network_message,
    is_rate_limited,
)


def test_exception_hierarchy() -> None:
    """4 类 typed exception 应继承自 ProviderError(SchemaValidationError 除外)。"""
    assert issubclass(ProviderTimeout, ProviderError)
    assert issubclass(ProviderUnsupportedResponse, ProviderError)
    # SchemaValidationError 也是 ProviderError 子类(便于统一 catch)
    assert issubclass(SchemaValidationError, ProviderError)


def test_is_rate_limited_429() -> None:
    assert is_rate_limited(Exception("HTTP 429 Too Many Requests")) is True


def test_is_rate_limited_529_overload() -> None:
    assert is_rate_limited(Exception("529 overloaded_error")) is True


def test_is_rate_limited_non_rate_limit() -> None:
    assert is_rate_limited(Exception("Connection reset by peer")) is False


def test_is_transient_network_message_timeout() -> None:
    assert is_transient_network_message("Request timed out") is True


def test_provider_call_dataclass_defaults() -> None:
    pc = ProviderCall(model="x", messages=[])
    assert pc.temperature == 0.0
    assert pc.timeout_s is None
    assert pc.extra == {}
```

Run: `pytest Plugins/AgentBridge/Tests/scripts/test_providers_smoke.py -v`
Expected:全 PASS。

```bash
git add Plugins/AgentBridge/Compiler/providers/__init__.py \
        Plugins/AgentBridge/Compiler/providers/base.py \
        Plugins/AgentBridge/Compiler/providers/_retry.py \
        Plugins/AgentBridge/Compiler/providers/_retry_async.py \
        Plugins/AgentBridge/Tests/scripts/test_providers_smoke.py
git commit -m "feat(llm-reopen): T02 移植 providers/{base,_retry,_retry_async} + is_rate_limited 扩展"
```

---

## Task 03:移植 + 适配 providers/litellm_adapter

**Files:**
- Create: `Plugins/AgentBridge/Compiler/providers/litellm_adapter.py`
- Reference: `D:/ClaudeProject/ForgeUE_codex/src/framework/providers/litellm_adapter.py`
- Test: `Plugins/AgentBridge/Tests/scripts/test_litellm_adapter_smoke.py`

**改动差异要点**:
- import `framework.observability.{compactor,secrets}` → `Compiler.observability.{compactor,secrets}`(T04 已建)
- 删除 `aimage_*` 接口(YAGNI)
- 保留 prompt cache + auto-compact + structured + usage 回传

- [ ] **Step 1:依赖前置 — 先做 T04 observability 移植**

如果 T04 还没做,**必须先做 T04**(litellm_adapter 依赖 `observability.secrets.redact_mapping` 和 `observability.compactor.compact_messages`)。

> 备选方案:T03 / T04 可掉换顺序,但 T03 必须在 T04 完成后才能跑通 import。Plan 内顺序按 spec §10 给出,实际执行可调换。

- [ ] **Step 2:写 `litellm_adapter.py`(从 ForgeUE 适配)**

把 `D:/ClaudeProject/ForgeUE_codex/src/framework/providers/litellm_adapter.py` 拷贝,做以下改动:

1. 顶部 import 路径:
   ```python
   from Compiler.observability.compactor import compact_messages
   from Compiler.observability.secrets import redact_mapping
   from Compiler.providers.base import (
       ProviderAdapter, ProviderCall, ProviderResult,
       ProviderError, ProviderTimeout, ProviderUnsupportedResponse,
       SchemaValidationError,
   )
   # 删除 ImageResult 相关 import
   ```

2. 删除 `LiteLLMAdapter.aimage_edit` / `aimage_generation` 两个方法
3. 删除 `_acollect_image_results` / `_afetch_url_bytes` 两个 helper
4. 保留 `_maybe_apply_prompt_cache` / `_maybe_auto_compact` / `_is_anthropic_family`
5. 保留 `_extract_text` / `_extract_usage` / `_raw_debug` / `_safe_finish_reason`
6. docstring 改为本项目语境

- [ ] **Step 3:写 smoke 测试**

`Plugins/AgentBridge/Tests/scripts/test_litellm_adapter_smoke.py`:

```python
"""LiteLLMAdapter smoke 测试 — 不打真 LLM,只验证类构造与基础逻辑。"""

import pytest

from Compiler.providers.litellm_adapter import LiteLLMAdapter, _is_anthropic_family
from Compiler.providers.base import ProviderCall


def test_litellm_adapter_init() -> None:
    a = LiteLLMAdapter(default_timeout_s=30.0)
    assert a.name == "litellm"
    assert a._default_timeout_s == 30.0


def test_litellm_adapter_supports_anything() -> None:
    a = LiteLLMAdapter()
    assert a.supports("anything/at/all") is True


def test_is_anthropic_family() -> None:
    assert _is_anthropic_family("anthropic/claude-3-haiku-20240307") is True
    assert _is_anthropic_family("claude-3-opus") is True
    assert _is_anthropic_family("gpt-4o") is False


def test_prompt_cache_short_system_no_inject() -> None:
    """system msg < 1024 字符不应注入 cache_control。"""
    from Compiler.providers.litellm_adapter import _maybe_apply_prompt_cache
    call = ProviderCall(
        model="claude-3-haiku",
        messages=[{"role": "system", "content": "短"}],
        extra={"_forge_prompt_cache": True},
    )
    out = _maybe_apply_prompt_cache(call)
    # 短 system 不被 tag
    assert isinstance(out[0]["content"], str)


def test_prompt_cache_long_system_injects() -> None:
    """system msg ≥ 1024 字符且开关开启时应注入 cache_control。"""
    from Compiler.providers.litellm_adapter import _maybe_apply_prompt_cache
    long_text = "x" * 1500
    call = ProviderCall(
        model="anthropic/claude-3-haiku",
        messages=[{"role": "system", "content": long_text}],
        extra={"_forge_prompt_cache": True},
    )
    out = _maybe_apply_prompt_cache(call)
    # 长 system 被 tag 成 multi-block 含 cache_control
    assert isinstance(out[0]["content"], list)
    assert out[0]["content"][0].get("cache_control") == {"type": "ephemeral"}
```

- [ ] **Step 4:跑测试 + commit**

Run: `pytest Plugins/AgentBridge/Tests/scripts/test_litellm_adapter_smoke.py -v`
Expected:全 PASS。

```bash
git add Plugins/AgentBridge/Compiler/providers/litellm_adapter.py \
        Plugins/AgentBridge/Tests/scripts/test_litellm_adapter_smoke.py
git commit -m "feat(llm-reopen): T03 移植 litellm_adapter(去 image 接口 + 适配 import 路径)"
```

---

## Task 04:移植 observability/{secrets, compactor}

**Files:**
- Create: `Plugins/AgentBridge/Compiler/observability/__init__.py`
- Create: `Plugins/AgentBridge/Compiler/observability/secrets.py`
- Create: `Plugins/AgentBridge/Compiler/observability/compactor.py`
- Reference: `D:/ClaudeProject/ForgeUE_codex/src/framework/observability/{secrets,compactor}.py`
- Test: T14 统一覆盖

> **执行顺序提示**:T04 是 T03 的硬前置(litellm_adapter 依赖 observability),若按 plan 顺序 T03 先列只是因 spec §10 顺序;实际先做 T04 再做 T03。

- [ ] **Step 1:建子目录 + `__init__.py`**

```bash
mkdir -p Plugins/AgentBridge/Compiler/observability
```

`Plugins/AgentBridge/Compiler/observability/__init__.py`:

```python
"""Observability — 横切支撑(secrets 脱敏 + compactor 超长上下文压缩)。

从 ForgeUE_codex `src/framework/observability/` 选择性移植,
本期仅需 secrets + compactor,不引入 tracing / event_bus / managed_process_registry。
"""

from .secrets import redact_mapping, redact_text
from .compactor import compact_messages

__all__ = ["redact_mapping", "redact_text", "compact_messages"]
```

- [ ] **Step 2:写 `secrets.py`(从 ForgeUE 拷贝)**

把 `D:/ClaudeProject/ForgeUE_codex/src/framework/observability/secrets.py` 完整拷贝,docstring 顶部改为本项目语境。

如果 ForgeUE 源文件依赖 `framework.*` 其他模块,**只拷贝必要部分**:

```python
"""Secret redaction — API key / Bearer token / 各类 credential 字段脱敏。

落盘 evidence 前必经此层,防止 API key / api_base 等敏感字段落到 git-tracked 文件。
"""

from __future__ import annotations

import re
from typing import Any

SENSITIVE_KEYS = {
    "api_key", "api-key", "apikey",
    "Authorization", "authorization",
    "x-api-key", "X-Api-Key",
    "token", "access_token", "refresh_token",
    "secret", "password",
}

SENSITIVE_VALUE_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._\-+/=]+"),
    re.compile(r"[A-Za-z0-9_-]{32,}\.[A-Za-z0-9_-]{32,}\.[A-Za-z0-9_-]{32,}"),  # JWT
]

REDACTED_MARK = "***"


def redact_mapping(d: dict[str, Any]) -> dict[str, Any]:
    """递归脱敏 dict 中的敏感字段。"""
    out: dict[str, Any] = {}
    for k, v in (d or {}).items():
        if k in SENSITIVE_KEYS:
            out[k] = REDACTED_MARK
        elif isinstance(v, dict):
            out[k] = redact_mapping(v)
        elif isinstance(v, list):
            out[k] = [redact_mapping(it) if isinstance(it, dict) else it for it in v]
        elif isinstance(v, str):
            out[k] = redact_text(v)
        else:
            out[k] = v
    return out


def redact_text(s: str) -> str:
    """脱敏字符串中的 API key / Bearer token / JWT 模式。"""
    if not isinstance(s, str):
        return s
    out = s
    for pat in SENSITIVE_VALUE_PATTERNS:
        out = pat.sub(REDACTED_MARK, out)
    return out
```

- [ ] **Step 3:写 `compactor.py`(从 ForgeUE 拷贝)**

`Plugins/AgentBridge/Compiler/observability/compactor.py`:

```python
"""消息历史 auto-compact — 4 char/token 估算,保留 first system + last N turns。"""

from __future__ import annotations

from typing import Any

DEFAULT_KEEP_TAIL = 4
CHARS_PER_TOKEN = 4


def _estimate_tokens(msg: dict[str, Any]) -> int:
    content = msg.get("content", "")
    if isinstance(content, str):
        return max(1, len(content) // CHARS_PER_TOKEN)
    if isinstance(content, list):
        total = 0
        for block in content:
            if isinstance(block, dict):
                t = block.get("text", "")
                total += max(1, len(t) // CHARS_PER_TOKEN)
        return total
    return 1


def compact_messages(
    messages: list[dict[str, Any]],
    *,
    max_tokens: int,
    keep_tail_turns: int = DEFAULT_KEEP_TAIL,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """裁剪消息历史到 ≤ max_tokens(粗估),保留 first system + last keep_tail turns。

    返回 (compacted_messages, stats),stats 含 dropped_count / kept_tokens_estimate。
    """
    if not messages or max_tokens <= 0:
        return list(messages), {"dropped_count": 0, "kept_tokens_estimate": 0}

    total = sum(_estimate_tokens(m) for m in messages)
    if total <= max_tokens:
        return list(messages), {"dropped_count": 0, "kept_tokens_estimate": total}

    # 保留 first system + last keep_tail turns
    system_msgs = [m for m in messages if m.get("role") == "system"]
    non_system = [m for m in messages if m.get("role") != "system"]

    keep_head = system_msgs[:1] if system_msgs else []
    keep_tail = non_system[-keep_tail_turns:] if keep_tail_turns > 0 else []

    compacted = keep_head + keep_tail
    kept = sum(_estimate_tokens(m) for m in compacted)
    dropped = len(messages) - len(compacted)
    return compacted, {"dropped_count": dropped, "kept_tokens_estimate": kept}
```

- [ ] **Step 4:写 smoke 测试**

`Plugins/AgentBridge/Tests/scripts/test_observability_smoke.py`:

```python
"""observability 子树 smoke 测试。"""

from Compiler.observability import redact_mapping, redact_text, compact_messages


def test_redact_mapping_api_key() -> None:
    out = redact_mapping({"api_key": "sk-abc123def456ghi789", "model": "gpt-4o"})
    assert out["api_key"] == "***"
    assert out["model"] == "gpt-4o"


def test_redact_mapping_nested() -> None:
    out = redact_mapping({"outer": {"api_key": "sk-xxx", "x": 1}})
    assert out["outer"]["api_key"] == "***"
    assert out["outer"]["x"] == 1


def test_redact_text_bearer() -> None:
    out = redact_text("Header: Bearer abc.def.ghi")
    assert "Bearer" in out
    assert "abc.def.ghi" not in out
    assert "***" in out


def test_compact_messages_short_noop() -> None:
    msgs = [{"role": "user", "content": "hi"}]
    out, stats = compact_messages(msgs, max_tokens=1000)
    assert out == msgs
    assert stats["dropped_count"] == 0


def test_compact_messages_long_drops_middle() -> None:
    msgs = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "u1" * 5000},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "u2"},
        {"role": "assistant", "content": "a2"},
        {"role": "user", "content": "tail"},
    ]
    out, stats = compact_messages(msgs, max_tokens=50, keep_tail_turns=2)
    # 保留 first system + last 2 turn
    assert any(m["role"] == "system" for m in out)
    assert out[-1]["content"] == "tail"
    assert stats["dropped_count"] > 0
```

- [ ] **Step 5:跑测试 + commit**

Run: `pytest Plugins/AgentBridge/Tests/scripts/test_observability_smoke.py -v`
Expected:全 PASS。

```bash
git add Plugins/AgentBridge/Compiler/observability/__init__.py \
        Plugins/AgentBridge/Compiler/observability/secrets.py \
        Plugins/AgentBridge/Compiler/observability/compactor.py \
        Plugins/AgentBridge/Tests/scripts/test_observability_smoke.py
git commit -m "feat(llm-reopen): T04 移植 observability/{secrets,compactor}"
```

---

## Task 05:移植 + 改造 providers/{capability_router, model_registry}

**Files:**
- Create: `Plugins/AgentBridge/Compiler/providers/capability_router.py`
- Create: `Plugins/AgentBridge/Compiler/providers/model_registry.py`
- Reference: `D:/ClaudeProject/ForgeUE_codex/src/framework/providers/capability_router.py` 和 `model_registry.py`
- Test: T14 统一覆盖

**改动差异要点**:
- `capability_router.py` 移植后**保留 fallback 循环骨架**,但 `policy.fallback_models=[]` 始终空(本期单 model)
- `model_registry.py` **重写**(ForgeUE 的与本项目语境不符):新建工厂 `build_default_router(config_path)` 负责从 `Config/llm_config.yaml` 读 provider 配置并组装 router + adapter

- [ ] **Step 1:`capability_router.py` 适配移植**

从 `D:/ClaudeProject/ForgeUE_codex/src/framework/providers/capability_router.py` 拷贝,改动:

1. import `from framework.core.policies` → 本项目定义内嵌(暂不建 `core/policies.py`,直接在 `capability_router.py` 顶部加 dataclass)
2. import `from framework.providers.base` → `from Compiler.providers.base`
3. **删除** 图像相关 `aimage_*` 方法
4. **简化** `_routes` — 只保留 `preferred_models + fallback_models` 字符串路径,删 `prepared_routes`(D plan 是 ForgeUE 特有概念)
5. **新建**内嵌 dataclass(本期单 model):

```python
@dataclass
class ProviderPolicy:
    """本项目最小化版 ProviderPolicy。

    本期单 model,fallback_models 默认空。中期扩多 model 路由时再丰富字段。
    """
    preferred_models: list[str] = field(default_factory=list)
    fallback_models: list[str] = field(default_factory=list)
    api_key_env: str | None = None
    api_base: str | None = None
    api_key: str | None = None       # 本项目直接传 key,不强制走 env(简化本期配置)
    timeout_s: float = 60.0
    max_tokens: int | None = None
    temperature: float = 0.7
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class PreparedRoute:
    """单条路由配置(simplified)。"""
    model: str
    api_key: str | None = None
    api_base: str | None = None
    timeout_s: float | None = None
```

6. `_rebind` 函数:负责把 policy 的 api_key/api_base 绑定到 `ProviderCall`,简化版即可。

- [ ] **Step 2:`model_registry.py` 新写(本项目特化)**

`Plugins/AgentBridge/Compiler/providers/model_registry.py`:

```python
"""默认 router 构造工厂 — 从 llm_config.yaml 装配 CapabilityRouter + LiteLLMAdapter。

本期单 model,fallback_models=[];中期扩多 model 路由只需改 build_default_router 内部装配逻辑。
"""

from __future__ import annotations

import os
import warnings
from pathlib import Path
from typing import Any

from .base import ProviderError
from .capability_router import CapabilityRouter, ProviderPolicy
from .litellm_adapter import LiteLLMAdapter


PLUGIN_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PLUGIN_DIR / "Config" / "llm_config.yaml"
CONFIG_ENV_VAR = "AGENT_BRIDGE_LLM_CONFIG"


def load_provider_policy_from_yaml(
    config_path: str | Path | None = None,
) -> ProviderPolicy | None:
    """从 llm_config.yaml 读配置,装配单 model ProviderPolicy。

    返回 None 的情况:
      - 配置文件不存在
      - 配置 provider/model 为空或占位符
      - pyyaml 未安装
    """
    resolved = _resolve_config_path(config_path)
    if not resolved.exists():
        return None

    try:
        import yaml
    except ImportError:
        warnings.warn("pyyaml 未安装,无法加载 llm_config.yaml", RuntimeWarning, stacklevel=2)
        return None

    try:
        with resolved.open("r", encoding="utf-8") as f:
            payload = yaml.safe_load(f) or {}
    except Exception as exc:
        warnings.warn(f"读取 llm_config 失败: {resolved} ({exc})", RuntimeWarning, stacklevel=2)
        return None

    if not isinstance(payload, dict):
        return None

    model = str(payload.get("model", "")).strip()
    api_key = str(payload.get("api_key", "")).strip()
    base_url = payload.get("base_url") or None

    placeholders = {"", "YOUR_API_KEY_HERE", "CHANGE_ME", "REPLACE_ME"}
    if api_key in placeholders or not model:
        return None

    return ProviderPolicy(
        preferred_models=[model],
        fallback_models=[],
        api_key=api_key,
        api_base=base_url,
        timeout_s=float(payload.get("timeout_sec", 60)),
        max_tokens=payload.get("max_tokens"),
        temperature=float(payload.get("temperature", 0.7)),
        extra={
            "prompt_cache_enabled": (payload.get("prompt_cache") or {}).get("enabled", True),
            "auto_compact": payload.get("auto_compact") or {},
            "concurrency": payload.get("concurrency") or {},
            "retry": payload.get("retry") or {},
            "budget": payload.get("budget") or {"observe_only": True, "cost_cap_usd": None},
        },
    )


def build_default_router(
    config_path: str | Path | None = None,
) -> tuple[CapabilityRouter, ProviderPolicy] | None:
    """组装默认 router + 单 model policy。

    返回 None 表示配置不可用(调用方应回退到 heuristic_fallback 或 abort)。
    """
    policy = load_provider_policy_from_yaml(config_path)
    if policy is None:
        return None

    router = CapabilityRouter()
    router.register(LiteLLMAdapter(default_timeout_s=policy.timeout_s))
    return router, policy


def _resolve_config_path(config_path: str | Path | None) -> Path:
    if config_path:
        return Path(config_path)
    env = os.getenv(CONFIG_ENV_VAR, "").strip()
    if env:
        return Path(env)
    return DEFAULT_CONFIG_PATH
```

- [ ] **Step 3:smoke 测试**

`Plugins/AgentBridge/Tests/scripts/test_router_registry_smoke.py`:

```python
"""capability_router + model_registry smoke 测试。"""

import tempfile
from pathlib import Path

import pytest

from Compiler.providers.capability_router import CapabilityRouter, ProviderPolicy, PreparedRoute
from Compiler.providers.model_registry import (
    load_provider_policy_from_yaml,
    build_default_router,
)
from Compiler.providers.base import ProviderError


def test_router_register_resolve() -> None:
    from Compiler.providers.litellm_adapter import LiteLLMAdapter
    r = CapabilityRouter()
    a = LiteLLMAdapter()
    r.register(a)
    # LiteLLMAdapter.supports 永远 True,resolve 任意 model 都返回它
    assert r._resolve("any/model") is a


def test_router_no_adapter_raises() -> None:
    r = CapabilityRouter()
    with pytest.raises(ProviderError):
        r._resolve("any/model")


def test_load_policy_missing_file_returns_none() -> None:
    assert load_provider_policy_from_yaml("/nonexistent/path.yaml") is None


def test_load_policy_placeholder_returns_none(tmp_path: Path) -> None:
    cfg = tmp_path / "llm_config.yaml"
    cfg.write_text(
        "provider: anthropic\nmodel: claude-3-haiku\napi_key: REPLACE_ME\n",
        encoding="utf-8",
    )
    assert load_provider_policy_from_yaml(cfg) is None


def test_load_policy_valid(tmp_path: Path) -> None:
    cfg = tmp_path / "llm_config.yaml"
    cfg.write_text(
        "provider: anthropic\n"
        "model: anthropic/claude-3-haiku-20240307\n"
        "api_key: sk-real-but-faked-for-test-1234567890\n"
        "base_url: https://api.example.com\n"
        "timeout_sec: 30\n"
        "max_tokens: 4096\n",
        encoding="utf-8",
    )
    p = load_provider_policy_from_yaml(cfg)
    assert p is not None
    assert p.preferred_models == ["anthropic/claude-3-haiku-20240307"]
    assert p.fallback_models == []
    assert p.timeout_s == 30.0
    assert p.max_tokens == 4096


def test_build_default_router_missing_config_returns_none() -> None:
    assert build_default_router("/nonexistent/path.yaml") is None
```

- [ ] **Step 4:跑 + commit**

Run: `pytest Plugins/AgentBridge/Tests/scripts/test_router_registry_smoke.py -v`
Expected:全 PASS。

```bash
git add Plugins/AgentBridge/Compiler/providers/capability_router.py \
        Plugins/AgentBridge/Compiler/providers/model_registry.py \
        Plugins/AgentBridge/Tests/scripts/test_router_registry_smoke.py
git commit -m "feat(llm-reopen): T05 移植 capability_router + 重写 model_registry(单 model + fallback=[])"
```

---

## Task 06:移植 providers/fake_adapter

**Files:**
- Create: `Plugins/AgentBridge/Compiler/providers/fake_adapter.py`
- Reference: `D:/ClaudeProject/ForgeUE_codex/src/framework/providers/fake_adapter.py`
- Test: T14 / T15 统一覆盖

- [ ] **Step 1:适配移植**

从 `D:/ClaudeProject/ForgeUE_codex/src/framework/providers/fake_adapter.py` 拷贝,改动:

1. import 路径调整
2. 删除 `image_bytes_list` 字段 + `aimage_generation` 方法(YAGNI)
3. 保留:
   - `FakeModelProgram(text, schema_value, schema_builder, raise_error, usage)` dataclass
   - `FakeAdapter.program(model, outputs)` 注册脚本
   - `FakeAdapter.acompletion / astructured / astructured_with_usage` async 实现
   - `supports(model)` 返回是否在已注册 model 列表中

- [ ] **Step 2:smoke 测试**

`Plugins/AgentBridge/Tests/scripts/test_fake_adapter_smoke.py`:

```python
"""FakeAdapter 单测桩 smoke 测试。"""

import asyncio

import pytest
from pydantic import BaseModel

from Compiler.providers.fake_adapter import FakeAdapter, FakeModelProgram
from Compiler.providers.base import ProviderCall, ProviderTimeout, SchemaValidationError


class DimSchema(BaseModel):
    dimension_id: str
    score: int


def test_fake_adapter_supports_only_programmed() -> None:
    fa = FakeAdapter()
    assert fa.supports("not-programmed") is False
    fa.program("test-model", outputs=[FakeModelProgram(text="x")])
    assert fa.supports("test-model") is True


def test_fake_adapter_sequential_pop() -> None:
    fa = FakeAdapter()
    fa.program("m", outputs=[
        FakeModelProgram(text="first"),
        FakeModelProgram(text="second"),
    ])
    call = ProviderCall(model="m", messages=[])
    r1 = asyncio.run(fa.acompletion(call))
    r2 = asyncio.run(fa.acompletion(call))
    assert r1.text == "first"
    assert r2.text == "second"


def test_fake_adapter_raise_error() -> None:
    fa = FakeAdapter()
    fa.program("m", outputs=[FakeModelProgram(raise_error=ProviderTimeout("simulated"))])
    call = ProviderCall(model="m", messages=[])
    with pytest.raises(ProviderTimeout):
        asyncio.run(fa.acompletion(call))


def test_fake_adapter_structured() -> None:
    fa = FakeAdapter()
    fa.program("m", outputs=[FakeModelProgram(
        schema_value={"dimension_id": "d1", "score": 5},
    )])
    call = ProviderCall(model="m", messages=[])
    obj = asyncio.run(fa.astructured(call, DimSchema))
    assert isinstance(obj, DimSchema)
    assert obj.dimension_id == "d1"
    assert obj.score == 5


def test_fake_adapter_structured_invalid_raises() -> None:
    fa = FakeAdapter()
    fa.program("m", outputs=[FakeModelProgram(
        schema_value={"dimension_id": "d1"},  # 缺 score
    )])
    call = ProviderCall(model="m", messages=[])
    with pytest.raises(SchemaValidationError):
        asyncio.run(fa.astructured(call, DimSchema))
```

- [ ] **Step 3:跑 + commit**

Run: `pytest Plugins/AgentBridge/Tests/scripts/test_fake_adapter_smoke.py -v`
Expected:全 PASS。

```bash
git add Plugins/AgentBridge/Compiler/providers/fake_adapter.py \
        Plugins/AgentBridge/Tests/scripts/test_fake_adapter_smoke.py
git commit -m "feat(llm-reopen): T06 移植 fake_adapter(去 image 接口)"
```

---

## Task 07:移植 + 改造 runtime/budget_tracker

**Files:**
- Create: `Plugins/AgentBridge/Compiler/runtime/__init__.py`
- Create: `Plugins/AgentBridge/Compiler/runtime/budget_tracker.py`
- Reference: `D:/ClaudeProject/ForgeUE_codex/src/framework/runtime/budget_tracker.py`
- Test: T14 统一覆盖

**改动差异要点**:
- 去掉 `BudgetExceeded` 抛出逻辑(observe-only)
- 保留 `record / spend / by_dimension / by_model / call_count`
- 新增 `dump_evidence(path)` 落盘到 `ProjectState/runs/{run_id}/llm_usage.json`

- [ ] **Step 1:建 runtime/ 子目录 + `__init__.py`**

```bash
mkdir -p Plugins/AgentBridge/Compiler/runtime
```

`Plugins/AgentBridge/Compiler/runtime/__init__.py`:

```python
"""Runtime 横切支撑 — budget_tracker(本期 observe-only)。"""

from .budget_tracker import BudgetTracker, BudgetSpend

__all__ = ["BudgetTracker", "BudgetSpend"]
```

- [ ] **Step 2:写 `budget_tracker.py`(observe-only 版本)**

`Plugins/AgentBridge/Compiler/runtime/budget_tracker.py`:

```python
"""Per-Run cost / usage 累计 — 本期 observe-only,只落盘不阻断 run。

中期开"软阈值"模式时,可在 record() / would_exceed_after() 上加阻断逻辑,
内核数据结构保持兼容。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass
class BudgetSpend:
    total_usd: float = 0.0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    by_dimension: dict[str, float] = field(default_factory=dict)
    by_model: dict[str, float] = field(default_factory=dict)
    by_dimension_tokens: dict[str, dict[str, int]] = field(default_factory=dict)
    call_count: int = 0


class BudgetTracker:
    """observe-only 模式:不抛 BudgetExceeded,只累计 + 落盘。"""

    def __init__(self, *, observe_only: bool = True, cost_cap_usd: float | None = None) -> None:
        self._observe_only = observe_only
        self._cost_cap_usd = cost_cap_usd
        self._spend = BudgetSpend()

    @property
    def spend(self) -> BudgetSpend:
        return self._spend

    @property
    def cap_usd(self) -> float | None:
        return self._cost_cap_usd

    @property
    def observe_only(self) -> bool:
        return self._observe_only

    def record(
        self,
        *,
        dimension_id: str,
        model: str,
        cost_usd: float = 0.0,
        usage: dict[str, int] | None = None,
    ) -> None:
        """累计一次调用的 cost + usage(token 数)。"""
        self._spend.total_usd += cost_usd
        self._spend.by_dimension[dimension_id] = (
            self._spend.by_dimension.get(dimension_id, 0.0) + cost_usd
        )
        self._spend.by_model[model] = self._spend.by_model.get(model, 0.0) + cost_usd

        if usage:
            prompt = int(usage.get("prompt", 0))
            completion = int(usage.get("completion", 0))
            total = int(usage.get("total", prompt + completion))

            self._spend.total_prompt_tokens += prompt
            self._spend.total_completion_tokens += completion
            self._spend.total_tokens += total

            dim_buckets = self._spend.by_dimension_tokens.setdefault(
                dimension_id, {"prompt": 0, "completion": 0, "total": 0},
            )
            dim_buckets["prompt"] += prompt
            dim_buckets["completion"] += completion
            dim_buckets["total"] += total

        self._spend.call_count += 1

    def would_exceed_after(self, extra_usd: float) -> bool:
        """observe-only 模式恒返 False;非 observe-only 才真比较 cap。"""
        if self._observe_only:
            return False
        if self._cost_cap_usd is None:
            return False
        return self._spend.total_usd + extra_usd > self._cost_cap_usd

    def dump_evidence(self, path: str | Path) -> None:
        """落盘到 ProjectState/runs/{run_id}/llm_usage.json。"""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {
            "observe_only": self._observe_only,
            "cost_cap_usd": self._cost_cap_usd,
            "over_budget": (
                False if self._observe_only or self._cost_cap_usd is None
                else self._spend.total_usd > self._cost_cap_usd
            ),
            "spend": asdict(self._spend),
        }
        p.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
```

- [ ] **Step 3:smoke 测试**

`Plugins/AgentBridge/Tests/scripts/test_budget_tracker_smoke.py`:

```python
"""BudgetTracker observe-only smoke 测试。"""

import json
from pathlib import Path

from Compiler.runtime import BudgetTracker


def test_budget_tracker_observe_only_no_block() -> None:
    bt = BudgetTracker(observe_only=True, cost_cap_usd=0.01)
    bt.record(dimension_id="d1", model="m", cost_usd=100.0)
    # observe_only 永远 False
    assert bt.would_exceed_after(0.0) is False


def test_budget_tracker_record_per_dim() -> None:
    bt = BudgetTracker()
    bt.record(dimension_id="d1", model="m", cost_usd=0.5, usage={"prompt": 100, "completion": 50, "total": 150})
    bt.record(dimension_id="d1", model="m", cost_usd=0.3, usage={"prompt": 50, "completion": 30, "total": 80})
    bt.record(dimension_id="d2", model="m", cost_usd=0.2, usage={"prompt": 80, "completion": 20, "total": 100})

    s = bt.spend
    assert s.call_count == 3
    assert s.by_dimension["d1"] == pytest_approx_eq(0.8)
    assert s.by_dimension["d2"] == pytest_approx_eq(0.2)
    assert s.total_prompt_tokens == 230
    assert s.total_tokens == 330


def test_budget_tracker_dump_evidence(tmp_path: Path) -> None:
    bt = BudgetTracker()
    bt.record(dimension_id="d1", model="m", cost_usd=0.5, usage={"prompt": 100, "completion": 50, "total": 150})
    target = tmp_path / "runs" / "run-XYZ" / "llm_usage.json"
    bt.dump_evidence(target)
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["observe_only"] is True
    assert payload["spend"]["total_usd"] == pytest_approx_eq(0.5)
    assert payload["spend"]["by_dimension"]["d1"] == pytest_approx_eq(0.5)


def pytest_approx_eq(value: float, tol: float = 1e-9):
    """简化 approx 比较。"""
    class _A:
        def __eq__(self, other):
            return abs(other - value) < tol
    return _A()
```

- [ ] **Step 4:跑 + commit**

Run: `pytest Plugins/AgentBridge/Tests/scripts/test_budget_tracker_smoke.py -v`
Expected:全 PASS。

```bash
git add Plugins/AgentBridge/Compiler/runtime/__init__.py \
        Plugins/AgentBridge/Compiler/runtime/budget_tracker.py \
        Plugins/AgentBridge/Tests/scripts/test_budget_tracker_smoke.py
git commit -m "feat(llm-reopen): T07 移植 budget_tracker(observe-only,去硬阻断)"
```

---

# Phase 1:Schema 升级(T08-T09)

## Task 08:新建 provider_call.schema.json + retry_policy.schema.json

**Files:**
- Create: `Plugins/AgentBridge/Schemas/provider_call.schema.json`
- Create: `Plugins/AgentBridge/Schemas/retry_policy.schema.json`
- Test: `Plugins/AgentBridge/Tests/scripts/test_new_schemas_validate.py`

- [ ] **Step 1:写 `provider_call.schema.json`**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "provider_call.schema.json",
  "title": "Provider Call Contract",
  "description": "ProviderCall 数据契约 — 服务于 evidence trace 落盘 (stage4_agent_traces/llm_internal/dim_*.json)。落盘前需经 secrets.redact_mapping 脱敏。",
  "type": "object",
  "required": ["model", "messages"],
  "additionalProperties": false,
  "properties": {
    "model": {"type": "string", "description": "litellm 格式 model 名,例如 anthropic/claude-3-haiku-20240307"},
    "messages": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["role", "content"],
        "properties": {
          "role": {"type": "string", "enum": ["system", "user", "assistant"]},
          "content": {}
        }
      }
    },
    "temperature": {"type": "number", "minimum": 0.0, "maximum": 2.0},
    "max_tokens": {"type": ["integer", "null"], "minimum": 1},
    "timeout_s": {"type": ["number", "null"], "minimum": 1.0},
    "seed": {"type": ["integer", "null"]},
    "api_key": {"type": ["string", "null"], "description": "落盘前必经脱敏,允许 *** 占位值"},
    "api_base": {"type": ["string", "null"]},
    "extra": {"type": "object", "additionalProperties": true}
  }
}
```

- [ ] **Step 2:写 `retry_policy.schema.json`**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "retry_policy.schema.json",
  "title": "Retry Policy Contract",
  "description": "Candidates batch executor 的 retry 策略,可在 llm_config.yaml retry: 字段配置。",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "max_attempts": {"type": "integer", "minimum": 1, "maximum": 10, "default": 3},
    "backoff_mode": {"type": "string", "enum": ["exponential", "fixed"], "default": "exponential"},
    "backoff_base_s": {"type": "number", "minimum": 0.0, "default": 2.0},
    "jitter_ms": {
      "type": "array",
      "items": {"type": "integer", "minimum": 0},
      "minItems": 2,
      "maxItems": 2,
      "default": [100, 500]
    },
    "retry_on": {
      "type": "array",
      "items": {"type": "string", "enum": [
        "timeout", "transient_network", "schema_fail", "rate_limit"
      ]},
      "default": ["timeout", "transient_network", "schema_fail"]
    },
    "no_retry_on": {
      "type": "array",
      "items": {"type": "string", "enum": ["unsupported_response", "4xx_non_429"]},
      "default": ["unsupported_response", "4xx_non_429"]
    }
  }
}
```

- [ ] **Step 3:写 schema 校验测试**

`Plugins/AgentBridge/Tests/scripts/test_new_schemas_validate.py`:

```python
"""新 Schema(provider_call / retry_policy)语法 + 实例校验。"""

import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator, validate

SCHEMA_DIR = Path("Plugins/AgentBridge/Schemas")


def test_provider_call_schema_valid_meta() -> None:
    s = json.loads((SCHEMA_DIR / "provider_call.schema.json").read_text(encoding="utf-8"))
    Draft7Validator.check_schema(s)


def test_retry_policy_schema_valid_meta() -> None:
    s = json.loads((SCHEMA_DIR / "retry_policy.schema.json").read_text(encoding="utf-8"))
    Draft7Validator.check_schema(s)


def test_provider_call_minimal_instance() -> None:
    s = json.loads((SCHEMA_DIR / "provider_call.schema.json").read_text(encoding="utf-8"))
    validate(
        instance={"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": "hi"}]},
        schema=s,
    )


def test_provider_call_extra_field_rejected() -> None:
    s = json.loads((SCHEMA_DIR / "provider_call.schema.json").read_text(encoding="utf-8"))
    with pytest.raises(Exception):
        validate(
            instance={"model": "m", "messages": [], "unknown_field": "x"},
            schema=s,
        )


def test_retry_policy_default_compatible() -> None:
    s = json.loads((SCHEMA_DIR / "retry_policy.schema.json").read_text(encoding="utf-8"))
    validate(
        instance={
            "max_attempts": 3,
            "backoff_mode": "exponential",
            "backoff_base_s": 2.0,
            "jitter_ms": [100, 500],
            "retry_on": ["timeout", "transient_network", "schema_fail"],
            "no_retry_on": ["unsupported_response", "4xx_non_429"],
        },
        schema=s,
    )
```

- [ ] **Step 4:跑测试 + commit**

Run: `pytest Plugins/AgentBridge/Tests/scripts/test_new_schemas_validate.py -v`
Expected:全 PASS。

```bash
git add Plugins/AgentBridge/Schemas/provider_call.schema.json \
        Plugins/AgentBridge/Schemas/retry_policy.schema.json \
        Plugins/AgentBridge/Tests/scripts/test_new_schemas_validate.py
git commit -m "feat(llm-reopen): T08 新建 provider_call + retry_policy schema"
```

---

## Task 09:扩 design_space_report.schema.json

**Files:**
- Modify: `Plugins/AgentBridge/Schemas/design_space_report.schema.json`
- Test: `Plugins/AgentBridge/Tests/scripts/test_design_space_report_per_dim_metadata.py`

- [ ] **Step 1:读现有 schema 找扩展点**

```bash
cat Plugins/AgentBridge/Schemas/design_space_report.schema.json
```

确认现有 `properties` 字段集与 `additionalProperties` 设置(若为 false 必须显式加新字段)。

- [ ] **Step 2:在 `properties` 顶层加 `per_dimension_batch_metadata`**

```json
"per_dimension_batch_metadata": {
  "type": "array",
  "description": "Stage 4 Candidates LLM 分批生成的 per-dimension 元数据(spec 2026-05-27-llm-internal-reopen-design.md §1.7)。仅 generator_provider=llm 时填,其他 provider 留空数组。",
  "items": {
    "type": "object",
    "required": ["dimension_id", "model", "attempt_count", "status"],
    "additionalProperties": false,
    "properties": {
      "dimension_id": {"type": "string"},
      "model": {"type": "string"},
      "attempt_count": {"type": "integer", "minimum": 1, "maximum": 10},
      "duration_ms": {"type": ["integer", "null"], "minimum": 0},
      "usage": {
        "type": "object",
        "properties": {
          "prompt": {"type": "integer", "minimum": 0},
          "completion": {"type": "integer", "minimum": 0},
          "total": {"type": "integer", "minimum": 0}
        }
      },
      "status": {"type": "string", "enum": ["success", "failed"]},
      "error_class": {"type": ["string", "null"], "enum": [
        null, "timeout", "schema_fail", "unsupported_response",
        "provider_error", "rate_limited"
      ]},
      "raw_response_id": {"type": ["string", "null"]}
    }
  }
}
```

- [ ] **Step 3:写校验测试**

`Plugins/AgentBridge/Tests/scripts/test_design_space_report_per_dim_metadata.py`:

```python
"""design_space_report 扩字段后向后兼容校验。"""

import json
from pathlib import Path

from jsonschema import validate, ValidationError
import pytest

SCHEMA_PATH = Path("Plugins/AgentBridge/Schemas/design_space_report.schema.json")


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_existing_report_without_new_field_still_valid() -> None:
    """老 report 不含 per_dimension_batch_metadata 仍合法(向后兼容)。"""
    schema = _load_schema()
    instance = {
        # 用现有最小实例(实施期参照 Schemas/examples/ 已有 example)
        "schema_version": "1.0",
        "dimensions": [],
        "candidates": [],
    }
    # 若 schema 必填字段不止上述,这里实施期需要照样补齐
    try:
        validate(instance=instance, schema=schema)
    except ValidationError as e:
        pytest.fail(f"老 schema 实例失败: {e.message}")


def test_new_per_dim_metadata_valid() -> None:
    schema = _load_schema()
    instance = {
        "schema_version": "1.0",
        "dimensions": [],
        "candidates": [],
        "per_dimension_batch_metadata": [
            {
                "dimension_id": "d1",
                "model": "anthropic/claude-3-haiku-20240307",
                "attempt_count": 1,
                "duration_ms": 28000,
                "usage": {"prompt": 1500, "completion": 800, "total": 2300},
                "status": "success",
                "error_class": None,
                "raw_response_id": "msg_abc123",
            }
        ],
    }
    validate(instance=instance, schema=schema)


def test_new_per_dim_metadata_invalid_status() -> None:
    schema = _load_schema()
    instance = {
        "schema_version": "1.0",
        "dimensions": [],
        "candidates": [],
        "per_dimension_batch_metadata": [{
            "dimension_id": "d1", "model": "m", "attempt_count": 1,
            "status": "INVALID_STATUS",
        }],
    }
    with pytest.raises(ValidationError):
        validate(instance=instance, schema=schema)
```

- [ ] **Step 4:跑测试 + commit**

Run: `pytest Plugins/AgentBridge/Tests/scripts/test_design_space_report_per_dim_metadata.py -v`
Expected:全 PASS。

```bash
git add Plugins/AgentBridge/Schemas/design_space_report.schema.json \
        Plugins/AgentBridge/Tests/scripts/test_design_space_report_per_dim_metadata.py
git commit -m "feat(llm-reopen): T09 扩 design_space_report.schema.json per_dimension_batch_metadata 字段"
```

---

# Phase 2:核心调度层(T10-T12)

## Task 10:实现 candidates_batch_orchestrator(本 plan 最难一块)

**Files:**
- Create: `Plugins/AgentBridge/Compiler/stages/candidates_batch_orchestrator.py`
- Test:本 task 自带详细单元测试

**实现要点**:
- `LLMBatchExecutor.run_candidates_batch()` 是核心 entry
- 内部用 `asyncio.Semaphore(concurrency)` 控制并发
- per-batch coroutine 含 jitter sleep + retry loop
- 7 个 batch 完成后 aggregator 纯结构拼接

- [ ] **Step 1:先写最小失败测试(happy path)**

`Plugins/AgentBridge/Tests/scripts/test_candidates_batch_orchestrator_minimal.py`:

```python
"""candidates_batch_orchestrator 最小 happy path:7 dim 全 FakeAdapter 返成功。"""

import asyncio
from pydantic import BaseModel

from Compiler.providers.fake_adapter import FakeAdapter, FakeModelProgram
from Compiler.providers.capability_router import CapabilityRouter, ProviderPolicy
from Compiler.stages.candidates_batch_orchestrator import (
    LLMBatchExecutor,
    DimensionBatch,
    AggregatedReport,
    RetryPolicySpec,
)


class CandSchema(BaseModel):
    dimension_id: str
    candidates: list[str]


def make_router_7_success() -> tuple[CapabilityRouter, ProviderPolicy]:
    fa = FakeAdapter()
    fa.program("m", outputs=[
        FakeModelProgram(schema_value={"dimension_id": f"d{i+1}", "candidates": [f"c_{i+1}"]})
        for i in range(7)
    ])
    r = CapabilityRouter()
    r.register(fa)
    p = ProviderPolicy(preferred_models=["m"], fallback_models=[])
    return r, p


def test_batch_7_dims_all_success() -> None:
    router, policy = make_router_7_success()
    ex = LLMBatchExecutor()
    dims = [
        {"dimension_id": f"d{i+1}", "prompt_messages": [{"role": "user", "content": f"d{i+1}"}]}
        for i in range(7)
    ]
    report: AggregatedReport = asyncio.run(ex.run_candidates_batch(
        dimensions=dims,
        router=router,
        policy=policy,
        schema=CandSchema,
        retry_policy=RetryPolicySpec(),
        concurrency=3,
    ))
    assert len(report.per_dimension) == 7
    assert all(b.status == "success" for b in report.per_dimension)
    assert report.promotable is True
```

跑 Expected:FAIL with "ModuleNotFoundError: candidates_batch_orchestrator"。

- [ ] **Step 2:写最小实现让 happy path 通过**

`Plugins/AgentBridge/Compiler/stages/candidates_batch_orchestrator.py`:

```python
"""Stage 4 Candidates 按 dimension 分批 + concurrency 控制 + 纯结构拼接聚合。

设计依据:Docs/superpowers/specs/2026-05-27-llm-internal-reopen-design.md §3.4 + §4
"""

from __future__ import annotations

import asyncio
import random
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any

from pydantic import BaseModel

from ..providers._retry import is_transient_network_message, is_rate_limited
from ..providers.base import (
    ProviderCall,
    ProviderError,
    ProviderTimeout,
    ProviderUnsupportedResponse,
    SchemaValidationError,
)
from ..providers.capability_router import CapabilityRouter, ProviderPolicy


@dataclass
class RetryPolicySpec:
    """retry_policy.schema.json 的运行时镜像。"""
    max_attempts: int = 3
    backoff_mode: str = "exponential"
    backoff_base_s: float = 2.0
    jitter_ms: tuple[int, int] = (100, 500)
    retry_on: tuple[str, ...] = ("timeout", "transient_network", "schema_fail")


@dataclass
class DimensionBatch:
    dimension_id: str
    prompt_messages: list[dict[str, Any]]
    attempt_count: int = 0
    duration_ms: int = 0
    usage: dict[str, int] = field(default_factory=dict)
    status: str = "pending"      # "success" | "failed" | "pending"
    error_class: str | None = None
    raw_response_id: str | None = None
    model: str | None = None
    parsed_payload: dict[str, Any] | None = None


@dataclass
class AggregatedReport:
    per_dimension: list[DimensionBatch]
    promotable: bool
    partial: bool = False
    aggregation_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class LLMBatchExecutor:
    """Stage 4 Candidates 分批执行器 — async-only,通过 asyncio.run 桥接到 sync 调用方。"""

    async def run_candidates_batch(
        self,
        *,
        dimensions: list[dict[str, Any]],
        router: CapabilityRouter,
        policy: ProviderPolicy,
        schema: type[BaseModel],
        retry_policy: RetryPolicySpec | None = None,
        concurrency: int = 3,
    ) -> AggregatedReport:
        retry_policy = retry_policy or RetryPolicySpec()
        sem = asyncio.Semaphore(concurrency)

        async def one_batch(d: dict[str, Any]) -> DimensionBatch:
            return await self._run_one(d, router, policy, schema, retry_policy, sem)

        results = await asyncio.gather(*(one_batch(d) for d in dimensions))
        promotable = all(b.status == "success" for b in results)
        partial = any(b.status == "failed" for b in results)
        return AggregatedReport(per_dimension=results, promotable=promotable, partial=partial)

    async def _run_one(
        self,
        d: dict[str, Any],
        router: CapabilityRouter,
        policy: ProviderPolicy,
        schema: type[BaseModel],
        retry_policy: RetryPolicySpec,
        sem: asyncio.Semaphore,
    ) -> DimensionBatch:
        batch = DimensionBatch(
            dimension_id=d["dimension_id"],
            prompt_messages=d["prompt_messages"],
        )
        async with sem:
            # 启动 jitter
            j_min, j_max = retry_policy.jitter_ms
            await asyncio.sleep(random.uniform(j_min, j_max) / 1000)

            start = time.monotonic()
            for attempt in range(retry_policy.max_attempts):
                batch.attempt_count = attempt + 1
                try:
                    call = ProviderCall(
                        model=policy.preferred_models[0],
                        messages=batch.prompt_messages,
                        temperature=policy.temperature,
                        max_tokens=policy.max_tokens,
                        timeout_s=policy.timeout_s,
                        api_key=policy.api_key,
                        api_base=policy.api_base,
                        extra={"_forge_prompt_cache": True},
                    )
                    obj, model_used, usage = await router.astructured(
                        policy=policy, call_template=call, schema=schema,
                    )
                    batch.model = model_used
                    batch.usage = usage or {}
                    batch.parsed_payload = obj.model_dump(mode="json")
                    batch.status = "success"
                    batch.duration_ms = int((time.monotonic() - start) * 1000)
                    return batch
                except ProviderUnsupportedResponse:
                    batch.status = "failed"
                    batch.error_class = "unsupported_response"
                    batch.duration_ms = int((time.monotonic() - start) * 1000)
                    return batch
                except (ProviderTimeout, ProviderError, SchemaValidationError) as exc:
                    error_class = self._classify(exc)
                    if attempt + 1 >= retry_policy.max_attempts or error_class not in retry_policy.retry_on:
                        batch.status = "failed"
                        batch.error_class = error_class
                        batch.duration_ms = int((time.monotonic() - start) * 1000)
                        return batch
                    await self._sleep_backoff(retry_policy, attempt, exc)
            # safety net,理论上 unreachable
            batch.status = "failed"
            batch.error_class = "exhausted"
            batch.duration_ms = int((time.monotonic() - start) * 1000)
            return batch

    def _classify(self, exc: Exception) -> str:
        if isinstance(exc, ProviderTimeout):
            return "timeout"
        if isinstance(exc, SchemaValidationError):
            return "schema_fail"
        if isinstance(exc, ProviderError):
            if is_rate_limited(exc):
                return "rate_limit"
            if is_transient_network_message(str(exc)):
                return "transient_network"
            return "provider_error"
        return "unknown"

    async def _sleep_backoff(self, rp: RetryPolicySpec, attempt: int, exc: Exception) -> None:
        if rp.backoff_mode == "exponential":
            base = min(rp.backoff_base_s * 2 ** attempt, 8.0)
        else:
            base = rp.backoff_base_s
        if is_rate_limited(exc):
            base = max(base * 2, 5.0)
        j_min, j_max = rp.jitter_ms
        await asyncio.sleep(base + random.uniform(j_min, j_max) / 1000)
```

- [ ] **Step 3:跑 happy path 测试**

Run: `pytest Plugins/AgentBridge/Tests/scripts/test_candidates_batch_orchestrator_minimal.py -v`
Expected:全 PASS。

- [ ] **Step 4:补 9 个剩余测试 case(spec §6.3 提及)**

在同测试文件继续追加:

```python
def test_batch_single_dim_retry_recovers() -> None:
    fa = FakeAdapter()
    fa.program("m", outputs=[
        FakeModelProgram(raise_error=ProviderTimeout("simulated 1")),
        FakeModelProgram(schema_value={"dimension_id": "d1", "candidates": ["c1"]}),
        # 其余 6 dim 直接成功
        *[FakeModelProgram(schema_value={"dimension_id": f"d{i+2}", "candidates": []}) for i in range(6)],
    ])
    router = CapabilityRouter()
    router.register(fa)
    policy = ProviderPolicy(preferred_models=["m"])
    ex = LLMBatchExecutor()
    # concurrency=1 让 FakeAdapter queue 顺序可控
    dims = [{"dimension_id": f"d{i+1}", "prompt_messages": [{"role": "user", "content": "x"}]} for i in range(7)]
    report = asyncio.run(ex.run_candidates_batch(
        dimensions=dims, router=router, policy=policy, schema=CandSchema,
        retry_policy=RetryPolicySpec(jitter_ms=(0, 1), backoff_base_s=0.01),
        concurrency=1,
    ))
    assert report.per_dimension[0].status == "success"
    assert report.per_dimension[0].attempt_count == 2  # 重试 1 次后成功
    assert report.promotable is True


def test_batch_single_dim_3x_timeout_fails() -> None:
    fa = FakeAdapter()
    fa.program("m", outputs=[
        FakeModelProgram(raise_error=ProviderTimeout(f"timeout {i}")) for i in range(3)
    ] + [FakeModelProgram(schema_value={"dimension_id": f"d{i+2}", "candidates": []}) for i in range(6)])
    router = CapabilityRouter()
    router.register(fa)
    policy = ProviderPolicy(preferred_models=["m"])
    ex = LLMBatchExecutor()
    dims = [{"dimension_id": f"d{i+1}", "prompt_messages": [{"role": "user", "content": "x"}]} for i in range(7)]
    report = asyncio.run(ex.run_candidates_batch(
        dimensions=dims, router=router, policy=policy, schema=CandSchema,
        retry_policy=RetryPolicySpec(jitter_ms=(0, 1), backoff_base_s=0.01),
        concurrency=1,
    ))
    assert report.per_dimension[0].status == "failed"
    assert report.per_dimension[0].error_class == "timeout"
    assert report.per_dimension[0].attempt_count == 3
    assert report.promotable is False


def test_batch_unsupported_response_no_retry() -> None:
    fa = FakeAdapter()
    fa.program("m", outputs=[
        FakeModelProgram(raise_error=ProviderUnsupportedResponse("bad shape")),
    ] + [FakeModelProgram(schema_value={"dimension_id": f"d{i+2}", "candidates": []}) for i in range(6)])
    router = CapabilityRouter()
    router.register(fa)
    policy = ProviderPolicy(preferred_models=["m"])
    ex = LLMBatchExecutor()
    dims = [{"dimension_id": f"d{i+1}", "prompt_messages": [{"role": "user", "content": "x"}]} for i in range(7)]
    report = asyncio.run(ex.run_candidates_batch(
        dimensions=dims, router=router, policy=policy, schema=CandSchema,
        retry_policy=RetryPolicySpec(jitter_ms=(0, 1), backoff_base_s=0.01),
        concurrency=1,
    ))
    assert report.per_dimension[0].status == "failed"
    assert report.per_dimension[0].error_class == "unsupported_response"
    assert report.per_dimension[0].attempt_count == 1   # 不重试
    assert report.promotable is False


def test_batch_concurrency_limit_enforced() -> None:
    """concurrency=2 时 max in-flight ≤ 2。"""
    in_flight = {"count": 0, "max": 0}

    class CountingFake(FakeAdapter):
        async def astructured_with_usage(self, call, schema):
            in_flight["count"] += 1
            in_flight["max"] = max(in_flight["max"], in_flight["count"])
            await asyncio.sleep(0.05)
            try:
                return await super().astructured_with_usage(call, schema)
            finally:
                in_flight["count"] -= 1

    fa = CountingFake()
    fa.program("m", outputs=[
        FakeModelProgram(schema_value={"dimension_id": f"d{i+1}", "candidates": []}) for i in range(7)
    ])
    router = CapabilityRouter()
    router.register(fa)
    policy = ProviderPolicy(preferred_models=["m"])
    ex = LLMBatchExecutor()
    dims = [{"dimension_id": f"d{i+1}", "prompt_messages": [{"role": "user", "content": "x"}]} for i in range(7)]
    asyncio.run(ex.run_candidates_batch(
        dimensions=dims, router=router, policy=policy, schema=CandSchema,
        retry_policy=RetryPolicySpec(jitter_ms=(0, 1)),
        concurrency=2,
    ))
    assert in_flight["max"] == 2
```

- [ ] **Step 5:跑全部 + commit**

Run: `pytest Plugins/AgentBridge/Tests/scripts/test_candidates_batch_orchestrator_minimal.py -v`
Expected:全 PASS(至少 4 个 case)。

```bash
git add Plugins/AgentBridge/Compiler/stages/candidates_batch_orchestrator.py \
        Plugins/AgentBridge/Tests/scripts/test_candidates_batch_orchestrator_minimal.py
git commit -m "feat(llm-reopen): T10 实现 candidates_batch_orchestrator(分批+retry+聚合+promotable)"
```

---

## Task 11:改造 agent_protocol.LLMProvider.generate 委托 batch executor

**Files:**
- Modify: `Plugins/AgentBridge/Compiler/stages/agent_protocol.py`
- Modify: `Plugins/AgentBridge/Compiler/stages/llm_client.py`(顶部加 DEPRECATED 注释)
- Test: `Plugins/AgentBridge/Tests/scripts/test_llm_provider_integration.py`

**保持公共签名不变**:`LLMProvider(provider_type="llm").generate(phase, context, system_prompt, ...)`

- [ ] **Step 1:写 LLMProvider 接缝测试(用 FakeAdapter 桩)**

`Plugins/AgentBridge/Tests/scripts/test_llm_provider_integration.py`:

```python
"""LLMProvider 内部委托 batch executor 的接缝测试。"""

import asyncio

from pydantic import BaseModel

from Compiler.providers.fake_adapter import FakeAdapter, FakeModelProgram
from Compiler.providers.capability_router import CapabilityRouter, ProviderPolicy
from Compiler.stages.agent_protocol import LLMProvider


def _make_fake_router() -> tuple[CapabilityRouter, ProviderPolicy]:
    fa = FakeAdapter()
    fa.program("m", outputs=[
        FakeModelProgram(schema_value={"dimension_id": f"d{i+1}", "candidates": [f"c{i+1}"]})
        for i in range(7)
    ])
    router = CapabilityRouter()
    router.register(fa)
    return router, ProviderPolicy(preferred_models=["m"])


def test_llm_provider_candidates_phase_routes_to_batch_executor() -> None:
    """phase='candidates' 必须走 LLMBatchExecutor 而非 llm_client.call。"""
    router, policy = _make_fake_router()
    provider = LLMProvider(router=router, policy=policy, batch_concurrency=2)
    ctx = {
        "dimensions": [
            {"dimension_id": f"d{i+1}", "prompt_messages": [{"role": "user", "content": "x"}]}
            for i in range(7)
        ],
    }
    out = provider.generate(phase="candidates", context=ctx, system_prompt="sys")
    # 应有 per_dimension_batch_metadata + promotable=True
    assert "per_dimension_batch_metadata" in out
    assert out["per_dimension_batch_metadata"][0]["status"] == "success"
    assert len(out["per_dimension_batch_metadata"]) == 7


def test_llm_provider_discovery_NOT_batched() -> None:
    """phase='discovery' 不走分批 — 保持现有 LLM client 单次调用语义。"""
    # 这里实施期可参照现有 agent_protocol.LLMProvider.generate(phase="discovery", ...) 行为
    # 用最小 stub 验证 'per_dimension_batch_metadata' 不出现
    pass    # 实施期补具体 assert
```

跑 Expected:FAIL(LLMProvider 还没改造完)。

- [ ] **Step 2:改造 LLMProvider 接受 router + policy**

读 `Plugins/AgentBridge/Compiler/stages/agent_protocol.py` 找到 `class LLMProvider`(line 565)。改造:

1. 构造函数:
   ```python
   def __init__(
       self,
       *,
       llm_client: Any = None,                          # 向后兼容,deprecate
       router: "CapabilityRouter | None" = None,       # 新增
       policy: "ProviderPolicy | None" = None,          # 新增
       batch_concurrency: int = 3,                       # 新增
   ) -> None:
       self._llm_client = llm_client                     # 向后兼容字段
       self._router = router
       self._policy = policy
       self._batch_concurrency = batch_concurrency
       if self._router is None and self._llm_client is None:
           raise RuntimeError("LLMProvider 需要 router(新)或 llm_client(deprecated)其一")
   ```

2. `generate(phase, context, system_prompt, ...)` 内部:
   ```python
   if phase == "candidates" and self._router is not None:
       # 走新分批路径
       return self._generate_candidates_via_batch(context, system_prompt)
   # discovery / convergence / 老路径
   return self._generate_via_llm_client(phase, context, system_prompt, ...)
   ```

3. 新方法 `_generate_candidates_via_batch`:
   ```python
   def _generate_candidates_via_batch(
       self, context: dict, system_prompt: str,
   ) -> dict:
       """调 LLMBatchExecutor.run_candidates_batch,返回 design_space_report payload。"""
       import asyncio
       from pydantic import BaseModel

       from .candidates_batch_orchestrator import LLMBatchExecutor, RetryPolicySpec

       class CandidatesDimSchema(BaseModel):
           """实施期由 SkillTemplate prompt 决定具体 Pydantic schema;
           此处占位 — 实际应从 self._policy.extra 或 SkillTemplate 装载。"""
           dimension_id: str
           candidates: list

       executor = LLMBatchExecutor()
       dimensions = context.get("dimensions", [])
       # 给每个 dim 注入 system_prompt 头
       for d in dimensions:
           d["prompt_messages"] = [
               {"role": "system", "content": system_prompt},
               *d.get("prompt_messages", []),
           ]
       report = asyncio.run(executor.run_candidates_batch(
           dimensions=dimensions,
           router=self._router,
           policy=self._policy,
           schema=CandidatesDimSchema,
           retry_policy=RetryPolicySpec(),
           concurrency=self._batch_concurrency,
       ))
       # 包成 design_space_report payload
       return {
           "schema_version": "1.0",
           "candidates": [b.parsed_payload for b in report.per_dimension if b.parsed_payload],
           "per_dimension_batch_metadata": [
               {
                   "dimension_id": b.dimension_id,
                   "model": b.model or "unknown",
                   "attempt_count": b.attempt_count,
                   "duration_ms": b.duration_ms,
                   "usage": b.usage or {},
                   "status": b.status,
                   "error_class": b.error_class,
                   "raw_response_id": b.raw_response_id,
               }
               for b in report.per_dimension
           ],
           "promotable": report.promotable,
       }
   ```

- [ ] **Step 3:llm_client.py 顶部加 DEPRECATED 注释**

在 `Plugins/AgentBridge/Compiler/stages/llm_client.py` 顶部 docstring 后追加:

```python
# DEPRECATED (2026-05-27):
# 本模块在 Phase 12 LLM Internal Reopen 后被 Compiler/providers/litellm_adapter.py 替代。
# 保留以维持 task09a 时期签名,但 Stage 4 Candidates 不再调用此处。
# Phase 13 评估物理删除时机。
```

- [ ] **Step 4:跑测试 + commit**

Run: `pytest Plugins/AgentBridge/Tests/scripts/test_llm_provider_integration.py -v`
Expected:happy path PASS;`test_llm_provider_discovery_NOT_batched` 占位即可。

```bash
git add Plugins/AgentBridge/Compiler/stages/agent_protocol.py \
        Plugins/AgentBridge/Compiler/stages/llm_client.py \
        Plugins/AgentBridge/Tests/scripts/test_llm_provider_integration.py
git commit -m "feat(llm-reopen): T11 LLMProvider.generate(candidates) 委托 batch executor"
```

---

## Task 12:改 pipeline_orchestrator 装 router

**Files:**
- Modify: `Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py:28` + `:750-751`
- Test: 已被 T16 覆盖

- [ ] **Step 1:改 import + provider 注入**

`Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py`:

```python
# 原 line 28
from ..stages.llm_client import load_llm_client_from_config

# 替换为:
from ..providers.model_registry import build_default_router
from ..stages.llm_client import load_llm_client_from_config  # 保留向后兼容
```

`line 750-751` 附近:

```python
# 原:
llm_client=load_llm_client_from_config(),

# 替换为:
router_with_policy = build_default_router()
if router_with_policy is not None:
    router, policy = router_with_policy
    llm_provider_kwargs = {"router": router, "policy": policy, "batch_concurrency": 3}
else:
    # 配置不可用,fallback 到老 llm_client(向后兼容)
    llm_provider_kwargs = {"llm_client": load_llm_client_from_config()}

# 后续传给 LLMProvider 的地方改用 **llm_provider_kwargs
```

- [ ] **Step 2:写 smoke 测试**

`Plugins/AgentBridge/Tests/scripts/test_pipeline_orchestrator_llm_wiring.py`:

```python
"""pipeline_orchestrator 装 router 的 smoke 测试。"""

from Compiler.pipeline.pipeline_orchestrator import build_default_router


def test_orchestrator_loads_router_smoke() -> None:
    """如果本地无 llm_config.yaml,返 None 不抛。"""
    out = build_default_router()
    # 不强制要求 not None — CI 无 llm_config 时应优雅返 None
    assert out is None or len(out) == 2
```

- [ ] **Step 3:跑 + commit**

Run: `pytest Plugins/AgentBridge/Tests/scripts/test_pipeline_orchestrator_llm_wiring.py -v`
Expected:PASS。

```bash
git add Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py \
        Plugins/AgentBridge/Tests/scripts/test_pipeline_orchestrator_llm_wiring.py
git commit -m "feat(llm-reopen): T12 pipeline_orchestrator 改装 router(向后兼容老 llm_client)"
```

---

# Phase 3:配置 + 离线测试(T13-T16)

## Task 13:扩 Config/llm_config.example.yaml

**Files:**
- Modify: `Plugins/AgentBridge/Config/llm_config.example.yaml`
- Test:无单独测试,T14 覆盖

- [ ] **Step 1:扩字段(向后兼容)**

`Plugins/AgentBridge/Config/llm_config.example.yaml`(覆盖现有内容):

```yaml
# AgentBridge LLM 客户端配置示例
# 实际配置文件:llm_config.yaml(不进 git,见 .gitignore)
#
# Phase 12 LLM Internal Reopen 后新增 5 个字段:concurrency / retry / prompt_cache / auto_compact / budget

# === 必填字段(原 task09a 已有)===
provider: anthropic                              # anthropic | openai | openai_compatible(底层会映射到 litellm 格式)
model: anthropic/claude-3-haiku-20240307         # litellm 标准 model 名
api_key: REPLACE_ME                              # 实际 API key,占位符则 build_default_router 返 None
base_url: https://api.minimaxi.com/anthropic     # 可选 base_url(中转站)
max_tokens: 8192
temperature: 0.7
timeout_sec: 60

# === 本次新增(可选,有默认值)===

concurrency:
  candidates_batch: 3           # 7 dimension 并发上限,默认 3
  jitter_ms: [100, 500]         # 启动 jitter 范围

retry:
  max_attempts: 3               # 单 dimension 最多 3 次
  backoff_mode: exponential     # exponential | fixed
  backoff_base_s: 2.0           # 指数 backoff 基数
  retry_on:                     # 白名单
    - timeout
    - transient_network
    - schema_fail

prompt_cache:
  enabled: true                 # Anthropic family 自动注入 cache_control

auto_compact:
  enabled: false                # 默认关
  max_tokens: 8000              # 超长 prompt 裁剪阈值

budget:
  observe_only: true            # 本期 observe-only,只落盘不阻断
  cost_cap_usd: null            # observe_only=true 时此字段被忽略
```

- [ ] **Step 2:smoke 测试(YAML 可解析 + model_registry 能装载)**

修改 `Plugins/AgentBridge/Tests/scripts/test_router_registry_smoke.py`,加一个 case:

```python
def test_load_policy_from_example_template_with_real_key_substituted(tmp_path: Path) -> None:
    """example yaml 替换 api_key 后应能装载。"""
    import shutil
    src = Path("Plugins/AgentBridge/Config/llm_config.example.yaml")
    dst = tmp_path / "llm_config.yaml"
    text = src.read_text(encoding="utf-8").replace("REPLACE_ME", "sk-test-fake-key-1234567890")
    dst.write_text(text, encoding="utf-8")

    p = load_provider_policy_from_yaml(dst)
    assert p is not None
    assert "concurrency" in p.extra
    assert p.extra["concurrency"]["candidates_batch"] == 3
    assert p.extra["budget"]["observe_only"] is True
```

- [ ] **Step 3:跑 + commit**

Run: `pytest Plugins/AgentBridge/Tests/scripts/test_router_registry_smoke.py -v`
Expected:全 PASS(含新 case)。

```bash
git add Plugins/AgentBridge/Config/llm_config.example.yaml \
        Plugins/AgentBridge/Tests/scripts/test_router_registry_smoke.py
git commit -m "feat(llm-reopen): T13 扩 llm_config.example.yaml(concurrency/retry/cache/compact/budget)"
```

---

## Task 14:L2-A providers + observability 完整单元测试

**Files:**
- Create: `Plugins/AgentBridge/Tests/scripts/test_providers_unit.py`(并入 T02/T05 smoke 内容)
- Create: `Plugins/AgentBridge/Tests/scripts/test_observability_unit.py`(并入 T04 smoke 内容)
- Test:自身

> 本 task 将 T02 / T04 / T05 中的零散 smoke 测试整合为完整覆盖。也可选择把 smoke 测试**直接重命名**为 `_unit.py`。

- [ ] **Step 1:整合 smoke 文件为 _unit 文件**

```bash
git mv Plugins/AgentBridge/Tests/scripts/test_providers_smoke.py \
       Plugins/AgentBridge/Tests/scripts/test_providers_unit.py
git mv Plugins/AgentBridge/Tests/scripts/test_observability_smoke.py \
       Plugins/AgentBridge/Tests/scripts/test_observability_unit.py
git mv Plugins/AgentBridge/Tests/scripts/test_litellm_adapter_smoke.py \
       Plugins/AgentBridge/Tests/scripts/test_providers_unit.py    # 合并;实施期手动合并内容
git mv Plugins/AgentBridge/Tests/scripts/test_router_registry_smoke.py \
       Plugins/AgentBridge/Tests/scripts/test_providers_unit.py    # 合并;实施期手动合并内容
git mv Plugins/AgentBridge/Tests/scripts/test_fake_adapter_smoke.py \
       Plugins/AgentBridge/Tests/scripts/test_providers_unit.py    # 合并;实施期手动合并内容
git mv Plugins/AgentBridge/Tests/scripts/test_budget_tracker_smoke.py \
       Plugins/AgentBridge/Tests/scripts/test_runtime_unit.py
```

(实际:手动合并文件,git mv 只是单文件改名;**多 smoke 合 1 unit 需要手动剪粘到目标文件**)

- [ ] **Step 2:补 spec §6.2 提及的剩余覆盖率**

确保 `test_providers_unit.py` 含 spec §6.2 表中**至少 13 个 case**(已在 T02-T06 smoke 实现部分,补齐空缺):

- `test_provider_call_dataclass_defaults` ✓(T02)
- `test_provider_result_dataclass` — 新增
- `test_exception_hierarchy` ✓
- `test_capability_router_register_resolve` ✓(T05)
- `test_capability_router_preferred_fallback_order` — 新增(本期 fallback=[],可用 mock 注 2 个 adapter 测顺序)
- `test_capability_router_unsupported_no_fallback` — 新增
- `test_retry_transient_check` ✓
- `test_retry_with_transient_retry_max_attempts` — 新增
- `test_retry_backoff_exponential` — 新增(mock time.sleep)
- `test_litellm_adapter_supports` ✓(T03)
- `test_litellm_adapter_acompletion_extract` — 新增(mock litellm.acompletion)
- `test_litellm_adapter_prompt_cache_anthropic` ✓
- `test_litellm_adapter_auto_compact_off_by_default` — 新增

`test_observability_unit.py` 含 spec §6.2 提及的 6 个 case(T04 已基本覆盖,确认即可)。

- [ ] **Step 3:跑覆盖率检查**

Run:

```bash
pytest Plugins/AgentBridge/Tests/scripts/test_providers_unit.py \
       Plugins/AgentBridge/Tests/scripts/test_observability_unit.py \
       Plugins/AgentBridge/Tests/scripts/test_runtime_unit.py \
       --cov=Plugins/AgentBridge/Compiler/providers \
       --cov=Plugins/AgentBridge/Compiler/observability \
       --cov=Plugins/AgentBridge/Compiler/runtime \
       --cov-report=term-missing \
       -v
```

Expected:覆盖率 ≥ 85%(spec §6.9 要求);所有 case PASS。

- [ ] **Step 4:commit**

```bash
git add Plugins/AgentBridge/Tests/scripts/test_providers_unit.py \
        Plugins/AgentBridge/Tests/scripts/test_observability_unit.py \
        Plugins/AgentBridge/Tests/scripts/test_runtime_unit.py
git commit -m "test(llm-reopen): T14 L2-A providers/observability/runtime 单元测试整合"
```

---

## Task 15:L2-B fake_adapter 集成 + LLMProvider 接缝完整测试

**Files:**
- Create / extend: `Plugins/AgentBridge/Tests/scripts/test_candidates_batch_orchestrator.py`
- Create / extend: `Plugins/AgentBridge/Tests/scripts/test_llm_provider_integration.py`(T11 已建)
- Test:自身

- [ ] **Step 1:把 T10 的 `*_minimal.py` 改名为正式名 + 补齐 spec §6.3 全 10 个 case**

```bash
git mv Plugins/AgentBridge/Tests/scripts/test_candidates_batch_orchestrator_minimal.py \
       Plugins/AgentBridge/Tests/scripts/test_candidates_batch_orchestrator.py
```

补齐到 10 个 case:
1. happy path 7 全 PASS ✓
2. single retry recovers ✓
3. 3x timeout fails ✓
4. unsupported no-retry ✓
5. schema fail retry — 新增
6. concurrency=3 enforcement ✓
7. jitter applied — 新增
8. promotable logic 6 PASS + 1 FAIL — 新增
9. per_dim metadata 字段全填 — 新增
10. evidence redaction(traces 落盘前 api_key 脱敏)— 新增

- [ ] **Step 2:补 T11 LLMProvider integration 测试**

完成 T11 留的 `test_llm_provider_discovery_NOT_batched` + 加 spec §6.3 表中其余 4 个 case:
- `test_llm_provider_convergence_NOT_batched` — 新增
- `test_llm_provider_public_signature_unchanged` — 新增(验证 `generate(phase,context,system_prompt,...)` 签名稳定)
- `test_llm_provider_router_failure_propagates` — 新增
- `test_llm_provider_with_heuristic_fallback_flag` — 新增

- [ ] **Step 3:跑 + commit**

Run: `pytest Plugins/AgentBridge/Tests/scripts/test_candidates_batch_orchestrator.py Plugins/AgentBridge/Tests/scripts/test_llm_provider_integration.py -v`
Expected:全 PASS,case 总数 ≥ 14。

```bash
git add Plugins/AgentBridge/Tests/scripts/test_candidates_batch_orchestrator.py \
        Plugins/AgentBridge/Tests/scripts/test_llm_provider_integration.py
git commit -m "test(llm-reopen): T15 L2-B fake_adapter 集成 + LLMProvider 接缝完整测试"
```

---

## Task 16:L2-C 系统测试套件接入

**Files:**
- Create: `Plugins/AgentBridge/Tests/scripts/test_llm_internal_system_integration.py`
- Modify: `Plugins/AgentBridge/Tests/run_system_tests.py`(新增 Stage 11)
- Test:自身

- [ ] **Step 1:写 system integration 测试**

`Plugins/AgentBridge/Tests/scripts/test_llm_internal_system_integration.py`:

```python
"""LLM Internal 接入 Phase 11 主链的系统集成测试(FakeAdapter 桩,offline)。"""

import asyncio

from Compiler.providers.fake_adapter import FakeAdapter, FakeModelProgram
from Compiler.providers.capability_router import CapabilityRouter, ProviderPolicy
from Compiler.pipeline.session import CompilerSession


def test_phase11_e2e_llm_internal_with_fake_router(tmp_path) -> None:
    """完整 Phase 11 主链 generator_provider=llm 用 FakeAdapter 走通。

    具体步骤(实施期参照 task11_phase11_mcp_e2e.py 的 fixture 装配):
      1. 构造 FakeAdapter 注册 7 dim schema_value 输出
      2. 装配 CapabilityRouter + ProviderPolicy
      3. 构造 CompilerSession(generator_provider="llm")
      4. 调 pipeline_orchestrator 入口至 Stage 4 Candidates
      5. assert run_id 下 design_space_report.json 存在
      6. assert per_dimension_batch_metadata 7 条全 status="success"
      7. assert session.is_promotable() is True
    """
    router, policy = _make_fake_router_7_success()
    session = CompilerSession(generator_provider="llm")
    # 实施期补:orchestrator entry call,具体 API 参 task11_phase11_mcp_e2e.py:run_full_pipeline()
    raise NotImplementedError(
        "实施期补:参照 task11_phase11_mcp_e2e.py 装 fixture + 触发 Stage 4 + 验证 per_dim_metadata"
    )


def test_phase11_e2e_mcp_agent_still_works() -> None:
    """同主链跑 mcp_agent,确认 LLM 新模块不污染 MCP Agent 路径。

    步骤:
      1. CompilerSession(generator_provider="mcp_agent")
      2. 调主链 — 不应触碰 providers/litellm_adapter / candidates_batch_orchestrator
      3. assert evidence 落 stage4_mcp_agent_sidecar/(不进 stage4_agent_traces/llm_internal/)
      4. assert promotable=True
    """
    raise NotImplementedError(
        "实施期补:参照 task11_phase11_mcp_e2e.py 现有 mcp_agent 路径回归"
    )


def test_phase11_e2e_heuristic_fallback_still_works() -> None:
    """同主链跑 heuristic,确认确定性引擎不被新模块污染。

    步骤:
      1. CompilerSession(generator_provider="heuristic_fallback", allow_heuristic_fallback=True)
      2. 调主链 — 走 agent_protocol.HeuristicFallbackProvider._default_evaluator
      3. assert evidence 落 stage4_agent_traces/heuristic/
      4. assert promotable=False(固化)
    """
    raise NotImplementedError(
        "实施期补:参照现有 heuristic_fallback 测试 case(如 stage4_*_fallback.py 关联用例)"
    )


def test_compiler_session_is_promotable_logic_llm_path() -> None:
    """is_promotable 在 LLM 路径 + 7/7 PASS / partial fail 两种场景下的判定。

    步骤:
      1. session = CompilerSession(generator_provider="llm")
      2. 注入 stage_outputs 含 design_space_report.per_dimension_batch_metadata 7 条全 success
      3. assert session.is_promotable() is True
      4. 注入同字段 6 success + 1 failed
      5. assert session.is_promotable() is False
    """
    raise NotImplementedError(
        "实施期补:is_promotable 具体调用参 Plugins/AgentBridge/Compiler/pipeline/session.py"
    )


def _make_fake_router_7_success():
    """7 dim 全 success 的 FakeAdapter helper(与 test_candidates_batch_orchestrator.py 同名复用)。"""
    raise NotImplementedError("实施期补,与 test_candidates_batch_orchestrator.py 同名 helper 复用")
```

> 4 个 case 给出**完整步骤骨架**;实施期把 `raise NotImplementedError` 换成具体 assert,fixture 装配参照 `task11_phase11_mcp_e2e.py`(已 work 的 mcp_agent E2E 同款风格)。**用 `raise NotImplementedError` 而非 `pass`**:让 pytest fail-loud,避免被误以为 PASS。

- [ ] **Step 2:在 `run_system_tests.py` 新增 Stage 11**

`Plugins/AgentBridge/Tests/run_system_tests.py` 的 `Stage 定义` 段(约 line 86)追加:

```python
{
    'id': 11,
    'name': 'LLM Internal Reopen',
    'description': 'Phase 12 LLM Internal 重开后的接入 + 整合测试(L2-A/B/C 全套 offline)',
    'count': 30,  # 实际 case 总数,实施期对账
    'runner': lambda: _run_pytest([
        'Plugins/AgentBridge/Tests/scripts/test_providers_unit.py',
        'Plugins/AgentBridge/Tests/scripts/test_observability_unit.py',
        'Plugins/AgentBridge/Tests/scripts/test_runtime_unit.py',
        'Plugins/AgentBridge/Tests/scripts/test_candidates_batch_orchestrator.py',
        'Plugins/AgentBridge/Tests/scripts/test_llm_provider_integration.py',
        'Plugins/AgentBridge/Tests/scripts/test_llm_internal_system_integration.py',
    ]),
}
```

(实际 stage 定义结构参照现有 `STAGE_DEFINITIONS` / `Stage 列表`,实施期对齐风格)

- [ ] **Step 3:跑 Stage 11**

Run:

```bash
python Plugins/AgentBridge/Tests/run_system_tests.py --stage 11
```

Expected:全 PASS。

- [ ] **Step 4:commit**

```bash
git add Plugins/AgentBridge/Tests/scripts/test_llm_internal_system_integration.py \
        Plugins/AgentBridge/Tests/run_system_tests.py
git commit -m "test(llm-reopen): T16 L2-C 系统测试套件接入 Stage 11 LLM Internal Reopen"
```

---

# Phase 4:真 LLM 验收 + 文档同步(T17-T20)

## Task 17:L2-D 真 LLM 验收脚本

**Files:**
- Create: `Plugins/AgentBridge/Tests/scripts/llm_internal_batch_real_run.py`
- Create: `Plugins/AgentBridge/Tests/scripts/llm_internal_batch_diagnostic.py`(选做)
- Test:本身就是验收脚本

- [ ] **Step 1:写 `llm_internal_batch_real_run.py`**

`Plugins/AgentBridge/Tests/scripts/llm_internal_batch_real_run.py`:

```python
"""真 LLM 端到端验收脚本 — 跑 Phase 11 主链 generator_provider=llm,7/7 PASS 收口。

执行:
    python Plugins/AgentBridge/Tests/scripts/llm_internal_batch_real_run.py --repeat 1

需要:
    Plugins/AgentBridge/Config/llm_config.yaml 含真 api_key

产出:
    ProjectState/runs/{run_id}/design_space_report.json
    ProjectState/runs/{run_id}/llm_usage.json
    ProjectState/runs/{run_id}/stage4_agent_traces/llm_internal/dim_*.json
    ProjectState/runs/{run_id}/stage4_agent_traces/llm_internal/aggregation.json
    ProjectState/Reports/{date}/llm_internal_reopen_acceptance.md
    ProjectState/Reports/{date}/llm_internal_reopen_acceptance.json
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
import uuid
from pathlib import Path

from Compiler.providers.model_registry import build_default_router


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeat", type=int, default=1, help="跑几轮(默认 1,本期满足验收)")
    parser.add_argument("--config", type=str, default=None, help="覆盖默认 llm_config.yaml 路径")
    args = parser.parse_args()

    router_with_policy = build_default_router(args.config)
    if router_with_policy is None:
        print("ERROR: llm_config.yaml 不可用 — 检查 api_key 是否非占位符", file=sys.stderr)
        return 2

    router, policy = router_with_policy

    today = datetime.date.today().isoformat()
    reports_dir = Path(f"ProjectState/Reports/{today}")
    reports_dir.mkdir(parents=True, exist_ok=True)

    all_runs: list[dict] = []
    for i in range(args.repeat):
        run_id = f"run-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
        print(f"=== 启动 run {i+1}/{args.repeat}: {run_id} ===")

        # 实施期:构造 CompilerSession + 触发 Phase 11 主链至 Stage 4
        # 参考 task11_phase11_mcp_e2e.py 与 stage4_candidates_diagnostic.py
        # 这里给出骨架,实施期补具体 entry call

        run_result = {
            "run_id": run_id,
            "promotable": False,        # 由实际 LLM 跑结果决定
            "per_dim_count": 0,
            "per_dim_status": [],
            "design_space_report_path": f"ProjectState/runs/{run_id}/design_space_report.json",
            "llm_usage_path": f"ProjectState/runs/{run_id}/llm_usage.json",
        }
        all_runs.append(run_result)

    # 落 acceptance report
    acceptance_json = reports_dir / "llm_internal_reopen_acceptance.json"
    acceptance_md = reports_dir / "llm_internal_reopen_acceptance.md"

    payload = {
        "spec": "Docs/superpowers/specs/2026-05-27-llm-internal-reopen-design.md",
        "date": today,
        "repeat": args.repeat,
        "all_promotable": all(r["promotable"] for r in all_runs),
        "runs": all_runs,
    }
    acceptance_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    md_lines = [
        f"# LLM Internal Reopen — Acceptance Report ({today})",
        "",
        f"- Spec: `{payload['spec']}`",
        f"- 跑了 {args.repeat} 轮,全部 promotable = **{payload['all_promotable']}**",
        "",
        "## Per-Run 摘要",
        "",
    ]
    for r in all_runs:
        md_lines.append(f"### {r['run_id']}")
        md_lines.append(f"- promotable: **{r['promotable']}**")
        md_lines.append(f"- per_dim_count: {r['per_dim_count']}")
        md_lines.append(f"- design_space_report: `{r['design_space_report_path']}`")
        md_lines.append(f"- llm_usage: `{r['llm_usage_path']}`")
        md_lines.append("")
    acceptance_md.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"\nAcceptance reports written:\n  {acceptance_md}\n  {acceptance_json}")
    return 0 if payload["all_promotable"] else 1


if __name__ == "__main__":
    sys.exit(main())
```

> **实施期警示**:`# 实施期:构造 CompilerSession + 触发 Phase 11 主链至 Stage 4` 这段必须补具体调用,参照 `task11_phase11_mcp_e2e.py` 与 `stage4_candidates_diagnostic.py`。本 plan 给出脚本骨架与 evidence 落盘合约。

- [ ] **Step 2:写 `llm_internal_batch_diagnostic.py`(选做)**

骨架:

```python
"""LLM Internal Batch 诊断脚本(长期回归用,可选跑)。"""

import argparse


def cmd_concurrency_sweep(args) -> int:
    """测 concurrency=1/2/3/5/7 各档总耗时 + 失败率。"""
    raise NotImplementedError("实施期填具体 sweep 逻辑")


def cmd_retry_stress(args) -> int:
    """强制注入 timeout 看 retry 收敛。"""
    raise NotImplementedError("实施期填")


def cmd_baseline_compare(args) -> int:
    """与 2026-04-16 原 diagnostic.json 对比。"""
    raise NotImplementedError("实施期填")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["concurrency-sweep", "retry-stress", "baseline-compare"], required=True)
    args = p.parse_args()
    funcs = {
        "concurrency-sweep": cmd_concurrency_sweep,
        "retry-stress": cmd_retry_stress,
        "baseline-compare": cmd_baseline_compare,
    }
    raise SystemExit(funcs[args.mode](args))
```

- [ ] **Step 3:commit(暂不跑,等 T18)**

```bash
git add Plugins/AgentBridge/Tests/scripts/llm_internal_batch_real_run.py \
        Plugins/AgentBridge/Tests/scripts/llm_internal_batch_diagnostic.py
git commit -m "feat(llm-reopen): T17 真 LLM 验收脚本 + 诊断脚本骨架"
```

---

## Task 18:跑 acceptance — 真 LLM 1 次 7/7

**Files:**
- 不创建文件,运行脚本
- Run output:`ProjectState/runs/{run_id}/*` + `ProjectState/Reports/{date}/llm_internal_reopen_acceptance.*`

- [ ] **Step 1:确认本地 llm_config.yaml 含真 api_key**

```bash
cat Plugins/AgentBridge/Config/llm_config.yaml
# 确认 api_key 不是 REPLACE_ME / CHANGE_ME / YOUR_API_KEY_HERE
```

如果没有,先按 example yaml 配真 API key(注意 yaml 不进 git,见 `.gitignore`)。

- [ ] **Step 2:跑 acceptance**

```bash
python Plugins/AgentBridge/Tests/scripts/llm_internal_batch_real_run.py --repeat 1
```

Expected:7 dimension 全 PASS,`all_promotable = True`,退出码 0。

- [ ] **Step 3:验证产物**

```bash
# 找最新 run
ls -lt ProjectState/runs/ | head -3

# 检查关键文件
ls ProjectState/runs/{最新 run_id}/
# 必须有:
#   design_space_report.json
#   llm_usage.json
#   stage4_agent_traces/llm_internal/dim_1.json ... dim_7.json
#   stage4_agent_traces/llm_internal/aggregation.json

# 检查 acceptance report
cat ProjectState/Reports/{date}/llm_internal_reopen_acceptance.md
```

- [ ] **Step 4:把 evidence 加入 git**

```bash
git add ProjectState/Reports/{date}/llm_internal_reopen_acceptance.md \
        ProjectState/Reports/{date}/llm_internal_reopen_acceptance.json
# ProjectState/runs/{run_id}/* 通常不进 git(实施期对账 .gitignore)
git commit -m "feat(llm-reopen): T18 真 LLM 验收 7/7 PASS — promotable=True"
```

> **若 7/7 不通过**:checkout 分支前 **STOP**。诊断 retry/concurrency/prompt cache 命中率,优先按 spec §9 风险表逐条排查;必要时回 spec brainstorming 调整参数。

---

## Task 19:同步文档(HLD / LLD / acceptance_report / task.md)

**Files:**
- Modify: `Docs/design/HLD.md`(§2.2)
- Modify: `Docs/design/LLD/04_compiler.md`(§2.1)
- Modify: `Docs/acceptance/acceptance_report.md`(§残留 + §1)
- Modify: `task.md`

- [ ] **Step 1:HLD §2.2 加图 B + 翻面 LLM 措辞**

读 `Docs/design/HLD.md:97-119` § 2.2。改动:

1. 在 §2.2 末尾追加 spec §2.2 图 B(三路 Provider 全景图)
2. 改 `LLM Internal` bullet 描述(原 line 104):
   - 原:`generator_type=llm,promotable=true。`
   - 改:`generator_type=llm,promotable=true。Phase 12 重开后稳定通过 7/7 严格回归(参 ProjectState/Reports/{date}/llm_internal_reopen_acceptance.md)。`

- [ ] **Step 2:LLD 04 §2.1 加图 B + 更新 F-CMP-15 行**

读 `Docs/design/LLD/04_compiler.md:13-50` §2.1 12 Stage 模块表。改动:

1. 在 §2.1 表后追加图 B
2. 改 F-CMP-15 行(原 line 28):
   - 原:`Stage 通用 LLM Client | Compiler/stages/llm_client.py | F-CMP-15 | OpenAI/Anthropic 统一 LLM 客户端`
   - 改:`Stage 通用 LLM Provider Framework | Compiler/providers/{base,litellm_adapter,capability_router,model_registry,fake_adapter,_retry}.py + observability/{secrets,compactor}.py + runtime/budget_tracker.py | F-CMP-15 | LiteLLM + Instructor 统一接入 + capability 路由 + observe-only budget(Phase 12 重开,旧 llm_client.py 已 deprecate)`

- [ ] **Step 3:acceptance_report.md §残留 翻面**

读 `Docs/acceptance/acceptance_report.md:450-462`。

改动 §"附:Phase 11 残留与重构注意事项" 第一条:
- 原:`LLM Internal 高负载验收暂缓,等 llm_client 框架升级后重开,不阻塞 UE 5.7 重构。Phase 11 正式主路径仍是 MCP Agent 驱动的 Stage 4 创造性生成,heuristic_fallback 是显式后备。`
- 改:`LLM Internal 已于 Phase 12 重开(2026-XX-XX,见 spec Docs/superpowers/specs/2026-05-27-llm-internal-reopen-design.md + acceptance ProjectState/Reports/{date}/llm_internal_reopen_acceptance.md)。LLM Internal 是 UE 5.7 重构前置门禁,promotable 候选。Phase 11 正式主路径仍是 MCP Agent,heuristic_fallback 仍是显式后备(固化 promotable=False)。`

§1 主表 F-CMP-15 勾选**留待 msc 手动勾**(Claude/Codex 不自动勾选)。

- [ ] **Step 4:task.md 跳转**

如果建立新阶段 `Phase 12`,改 `task.md` 入口页:

- 顶部加:
  ```
  当前阶段:Phase 12 LLM Internal Reopen — 已完成

  阶段验收报告:ProjectState/Reports/{date}/llm_internal_reopen_acceptance.md
  实施前 spec:Docs/superpowers/specs/2026-05-27-llm-internal-reopen-design.md
  实施 plan:Docs/superpowers/plans/2026-05-27-llm-internal-reopen.md
  ```

否则 task.md 保持现状,仅在 Docs/INDEX.md 补 spec/plan 链接即可。

- [ ] **Step 5:跑 document-release skill**

按 CLAUDE.md "任务收尾流程",在 commit 前调用 superpowers document-release skill 同步所有文档元数据。

详见 `.claude/skills/document-release/SKILL.md`(项目自带)。

- [ ] **Step 6:commit**

```bash
git add Docs/design/HLD.md \
        Docs/design/LLD/04_compiler.md \
        Docs/acceptance/acceptance_report.md \
        task.md
git commit -m "docs(llm-reopen): T19 同步 HLD/LLD/acceptance_report/task.md — Phase 12 收口"
```

---

## Task 20:document-release 收尾 + 收尾流程

**Files:**
- 走 superpowers:finishing-a-development-branch skill

- [ ] **Step 1:本地 sanity 检查**

```bash
# 跑全部 LLM 相关测试一遍
pytest Plugins/AgentBridge/Tests/scripts/test_providers_unit.py \
       Plugins/AgentBridge/Tests/scripts/test_observability_unit.py \
       Plugins/AgentBridge/Tests/scripts/test_runtime_unit.py \
       Plugins/AgentBridge/Tests/scripts/test_candidates_batch_orchestrator.py \
       Plugins/AgentBridge/Tests/scripts/test_llm_provider_integration.py \
       Plugins/AgentBridge/Tests/scripts/test_llm_internal_system_integration.py \
       Plugins/AgentBridge/Tests/scripts/test_design_space_report_per_dim_metadata.py \
       Plugins/AgentBridge/Tests/scripts/test_new_schemas_validate.py \
       -v

# 跑 Stage 11
python Plugins/AgentBridge/Tests/run_system_tests.py --stage 11

# 跑全套 Schema 校验
python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict
```

Expected:全绿。

- [ ] **Step 2:启动 verification-before-completion skill**

```
# Skill 调用,确认 spec 验收口径 §8.1 全部满足
Skill superpowers:verification-before-completion
```

- [ ] **Step 3:启动 finishing-a-development-branch skill**

```
Skill superpowers:finishing-a-development-branch
```

按 skill 引导选 merge / PR 模式。

- [ ] **Step 4:最终 commit(若 skill 没自动 commit)**

```bash
git status
# 应该 clean
git log --oneline -25
# 应该看到 T01-T19 的 20 个 commit
```

---

# 总结

## 完成清单(spec §8.1 验收口径)

- [ ] T01-T07 Phase 0 基础设施移植(6 子目录 13 文件)
- [ ] T08-T09 Phase 1 Schema 升级(新 2 改 1)
- [ ] T10-T12 Phase 2 核心调度层(新 1 改 2)
- [ ] T13-T16 Phase 3 配置 + 离线测试(覆盖率 ≥ 85%)
- [ ] T17-T18 Phase 4 真 LLM 7/7 PASS → `llm_internal_reopen_acceptance.{md,json}` 落盘
- [ ] T19-T20 文档同步 + 收尾(HLD/LLD/acceptance_report/task.md 翻面)

## CLAUDE.md 红线最终交叉检查

- [ ] `Source/*` C++ 0 改 ✓
- [ ] `Scripts/bridge/*` 0 改 ✓
- [ ] `Scripts/orchestrator/*` 0 改 ✓
- [ ] `AgentBridgeTests/` 0 改 ✓
- [ ] 所有改动 path 都在 "可以修改" 清单内 ✓
- [ ] 旧 `llm_client.py` 文件保留(顶部 DEPRECATED 注释),不删 ✓

## 风险检查(spec §9.1)

实施过程中遇到以下情况须 STOP 回 spec 重新决断:
- litellm / instructor / pydantic 版本不兼容,装失败
- LiteLLM 对 MiniMax 中转 base_url 兼容性问题(T18 第一次跑就 timeout)
- instructor 对 Anthropic-via-MiniMax tool_use 响应不支持 → spec §9.1 退路启用
- 真 LLM run 7 dim 中 ≥1 个稳定失败 → 回 spec §6 重新看 retry/concurrency 参数

## 与 Phase 13 / UE 5.7 衔接

本 plan 完成后:
- LLM Internal 拿回 promotable 资格 ✓
- UE 5.7 重构可启动(spec §1.2 前置门禁解锁)
- 旧 `llm_client.py` 物理删除留 Phase 13 评估(spec §7 yagni)
- 多 model 路由 / budget hard limit / Discovery+Convergence 也分批 等留中期 spec(spec §9.2 follow-up)

---

> **For agentic workers**:执行此 plan 时,建议每 Phase 末尾人工 review(spec §10 实施序列预告);若使用 `superpowers:subagent-driven-development`,每个 task 一个 subagent;若用 `superpowers:executing-plans`,建议 Phase 末批量 checkpoint。
