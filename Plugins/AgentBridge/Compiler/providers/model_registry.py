"""默认 router 构造工厂 — 从 llm_config.yaml 装配 CapabilityRouter + LiteLLMAdapter。

本项目特化(不复用 ForgeUE model_registry):
- ForgeUE 的 model_registry 是为多 provider 类型 + comfy/qwen/hunyuan 等 worker 设计的,
  与本项目"LLM 文本路径单 model"语境不符,重写更简洁。
- 本期单 model,fallback_models=[];中期扩多 model 路由只需改 build_default_router 内部装配逻辑。
"""

from __future__ import annotations

import os
import warnings
from pathlib import Path

from .capability_router import CapabilityRouter, ProviderPolicy
from .litellm_adapter import LiteLLMAdapter


# Plugins/AgentBridge/Compiler/providers/model_registry.py
#   parents[0] = providers
#   parents[1] = Compiler
#   parents[2] = AgentBridge   ← Plugin root,llm_config.yaml 在 Config/ 下
PLUGIN_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PLUGIN_DIR / "Config" / "llm_config.yaml"
CONFIG_ENV_VAR = "AGENT_BRIDGE_LLM_CONFIG"


def load_provider_policy_from_yaml(
    config_path: str | Path | None = None,
) -> ProviderPolicy | None:
    """从 llm_config.yaml 读配置,装配单 model ProviderPolicy。

    返回 None 的情况(调用方应回退到 heuristic_fallback 或 abort):
      - 配置文件不存在
      - 配置 provider/model 为空或占位符
      - pyyaml 未安装
      - yaml 文件读取/解析失败
    """
    resolved = _resolve_config_path(config_path)
    if not resolved.exists():
        return None

    try:
        import yaml  # type: ignore
    except ImportError:
        warnings.warn(
            "pyyaml 未安装,无法加载 llm_config.yaml",
            RuntimeWarning, stacklevel=2,
        )
        return None

    try:
        with resolved.open("r", encoding="utf-8") as f:
            payload = yaml.safe_load(f) or {}
    except Exception as exc:  # noqa: BLE001 — 任何 yaml 解析失败都降级返回 None
        warnings.warn(
            f"读取 llm_config 失败: {resolved} ({exc})",
            RuntimeWarning, stacklevel=2,
        )
        return None

    if not isinstance(payload, dict):
        return None

    model = str(payload.get("model", "")).strip()
    api_key = str(payload.get("api_key", "")).strip()
    provider = str(payload.get("provider", "")).strip()
    base_url = payload.get("base_url") or None

    # 占位符识别:llm_config.example.yaml 的 YOUR_API_KEY_HERE 等都视为未配置。
    placeholders = {"", "YOUR_API_KEY_HERE", "CHANGE_ME", "REPLACE_ME"}
    if api_key in placeholders or not model:
        return None

    # Phase 12 follow-up F2:若 model 不带 litellm provider 前缀,从 provider 字段补上。
    # litellm 要求 model 形如 "anthropic/claude-3-haiku" / "openai/gpt-4o" / "openai_compatible/llama3"。
    # 已带 "/" 的视为已经合规(用户显式写了完整形式),不动。
    if "/" not in model and provider:
        known_providers = {"anthropic", "openai", "openai_compatible"}
        if provider in known_providers:
            model = f"{provider}/{model}"
        # 未知 provider 不强拼,让 litellm 抛错给清晰反馈

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
    # 优先级:函数参数 > 环境变量 AGENT_BRIDGE_LLM_CONFIG > 默认 Plugin/Config 路径
    if config_path:
        return Path(config_path)
    env = os.getenv(CONFIG_ENV_VAR, "").strip()
    if env:
        return Path(env)
    return DEFAULT_CONFIG_PATH
