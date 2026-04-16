"""
统一 LLM 客户端加载与调用封装。

职责：
  - 从本地 yaml 配置加载 LLM Internal 路径所需的客户端
  - 统一兼容 Anthropic / OpenAI / OpenAI-Compatible 三种 provider
  - 向 Stage 4 提供稳定的 call(messages) -> str 接口
"""

from __future__ import annotations

import os
import warnings
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml
    HAS_YAML = True
except ImportError:  # pragma: no cover - 运行环境通常会有 pyyaml
    yaml = None
    HAS_YAML = False

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:  # pragma: no cover - 可选依赖
    anthropic = None
    HAS_ANTHROPIC = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:  # pragma: no cover - 可选依赖
    OpenAI = None
    HAS_OPENAI = False


PLUGIN_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PLUGIN_DIR / "Config" / "llm_config.yaml"
CONFIG_ENV_VAR = "AGENT_BRIDGE_LLM_CONFIG"
VALID_PROVIDERS = {"anthropic", "openai", "openai_compatible"}
PLACEHOLDER_API_KEYS = {
    "",
    "YOUR_API_KEY_HERE",
    "CHANGE_ME",
    "REPLACE_ME",
}


def _warn(message: str) -> None:
    """统一输出轻量告警，不让配置问题升级成异常。"""
    warnings.warn(message, RuntimeWarning, stacklevel=2)


def _normalize_text(value: Any) -> str:
    """把任意 content 安全归一为字符串。"""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _extract_openai_text(response: Any) -> str:
    """从 OpenAI 响应对象中提取文本。"""
    choices = getattr(response, "choices", None) or []
    if not choices:
        return ""

    message = getattr(choices[0], "message", None)
    if message is None:
        return ""

    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(_normalize_text(item.get("text", "")))
            else:
                text = getattr(item, "text", None)
                if text is not None:
                    parts.append(_normalize_text(text))
        return "".join(parts)
    return _normalize_text(content)


def _extract_anthropic_text(response: Any) -> str:
    """从 Anthropic 响应对象中提取文本。"""
    content = getattr(response, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(_normalize_text(block.get("text", "")))
            else:
                text = getattr(block, "text", None)
                if text is not None:
                    parts.append(_normalize_text(text))
        return "".join(parts)
    return _normalize_text(content)


def _is_placeholder_api_key(provider: str, api_key: str) -> bool:
    """判断 API key 是否仍然是占位符。"""
    normalized = api_key.strip()
    if provider == "openai_compatible" and normalized == "not-needed":
        return False
    if normalized in PLACEHOLDER_API_KEYS:
        return True
    if normalized.endswith("..."):
        return True
    return False


class UnifiedLLMClient:
    """统一 LLM 客户端，兼容 Anthropic / OpenAI / OpenAI-Compatible。"""

    def __init__(
        self,
        provider: str,
        api_key: str,
        model: str,
        base_url: str | None = None,
        max_tokens: int = 8192,
        temperature: float = 0.7,
    ) -> None:
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.max_tokens = int(max_tokens)
        self.temperature = float(temperature)
        self._client = self._create_client()

    def _create_client(self) -> Any:
        """按 provider 创建底层 SDK 客户端。"""
        if self.provider == "anthropic":
            if not HAS_ANTHROPIC:
                raise RuntimeError("未安装 anthropic SDK。")
            return anthropic.Anthropic(api_key=self.api_key)

        if self.provider in {"openai", "openai_compatible"}:
            if not HAS_OPENAI:
                raise RuntimeError("未安装 openai SDK。")

            client_kwargs: Dict[str, Any] = {"api_key": self.api_key}
            if self.provider == "openai_compatible" and self.base_url:
                client_kwargs["base_url"] = self.base_url
            return OpenAI(**client_kwargs)

        raise ValueError(f"不支持的 provider: {self.provider}")

    def call(self, messages: List[Dict[str, Any]]) -> str:
        """
        统一调用入口。

        参数：
          messages: [{"role": "...", "content": "..."}]

        返回：
          模型生成的纯文本。
        """
        normalized_messages = self._normalize_messages(messages)
        if self.provider == "anthropic":
            return self._call_anthropic(normalized_messages)
        return self._call_openai(normalized_messages)

    def _normalize_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """清洗消息结构，保证 role/content 都是字符串。"""
        normalized: List[Dict[str, str]] = []
        for message in messages or []:
            if not isinstance(message, dict):
                continue
            role = _normalize_text(message.get("role", "user")).strip() or "user"
            content = _normalize_text(message.get("content", ""))
            normalized.append({"role": role, "content": content})
        return normalized

    def _call_openai(self, messages: List[Dict[str, str]]) -> str:
        """调用 OpenAI 或兼容接口。"""
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        return _extract_openai_text(response)

    def _call_anthropic(self, messages: List[Dict[str, str]]) -> str:
        """调用 Anthropic；system 需要从 messages 中单独拆出。"""
        system_parts: List[str] = []
        anthropic_messages: List[Dict[str, str]] = []

        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            if role == "system":
                system_parts.append(content)
                continue

            normalized_role = role if role in {"user", "assistant"} else "user"
            anthropic_messages.append({
                "role": normalized_role,
                "content": content,
            })

        if not anthropic_messages:
            anthropic_messages.append({"role": "user", "content": ""})

        request_kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": anthropic_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        if system_parts:
            request_kwargs["system"] = "\n\n".join(system_parts)

        response = self._client.messages.create(**request_kwargs)
        return _extract_anthropic_text(response)


def _resolve_config_path(config_path: str | Path | None = None) -> Path:
    """按约定顺序解析配置路径。"""
    if config_path:
        return Path(config_path)

    env_path = os.getenv(CONFIG_ENV_VAR, "").strip()
    if env_path:
        return Path(env_path)

    return DEFAULT_CONFIG_PATH


def load_llm_client_from_config(config_path: str | Path | None = None) -> UnifiedLLMClient | None:
    """
    从配置文件加载 LLM 客户端。

    行为约束：
      - 配置文件缺失：返回 None
      - 依赖缺失：返回 None，并给出轻量告警
      - 配置占位符未替换：返回 None
      - 不抛异常给外层，让 Stage 4 自己决定走哪条 provider 路径
    """
    resolved_path = _resolve_config_path(config_path)
    if not resolved_path.exists():
        return None

    if not HAS_YAML:
        _warn("未安装 pyyaml，无法加载 llm_config.yaml。")
        return None

    try:
        with resolved_path.open("r", encoding="utf-8") as file:
            payload = yaml.safe_load(file) or {}
    except Exception as exc:
        _warn(f"读取 LLM 配置失败，已忽略：{resolved_path} ({exc})")
        return None

    if not isinstance(payload, dict):
        _warn(f"LLM 配置格式非法，期望 object：{resolved_path}")
        return None

    provider = _normalize_text(payload.get("provider", "")).strip()
    api_key = _normalize_text(payload.get("api_key", "")).strip()
    model = _normalize_text(payload.get("model", "")).strip()
    base_url = _normalize_text(payload.get("base_url", "")).strip() or None
    max_tokens = payload.get("max_tokens", 8192)
    temperature = payload.get("temperature", 0.7)

    if provider not in VALID_PROVIDERS:
        _warn(f"LLM 配置 provider 非法，已忽略：{provider!r}")
        return None

    if _is_placeholder_api_key(provider, api_key):
        return None

    if not model:
        _warn("LLM 配置缺少 model，已忽略。")
        return None

    if provider == "anthropic" and not HAS_ANTHROPIC:
        _warn("配置为 anthropic，但环境未安装 anthropic SDK，已忽略。")
        return None

    if provider in {"openai", "openai_compatible"} and not HAS_OPENAI:
        _warn(f"配置为 {provider}，但环境未安装 openai SDK，已忽略。")
        return None

    try:
        return UnifiedLLMClient(
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=base_url,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    except Exception as exc:
        _warn(f"创建 UnifiedLLMClient 失败，已忽略：{exc}")
        return None


__all__ = [
    "UnifiedLLMClient",
    "load_llm_client_from_config",
]
