"""LiteLLM-backed adapter — Stage 4 Candidates 分批生成的默认 LLM 接入实现。

LiteLLM 把 100+ provider(Anthropic / OpenAI / OpenAI-compatible 中转 / Azure / etc)
统一到一套 chat-completion API。结构化输出通过 Instructor 套一层 Pydantic schema retry。

litellm 和 instructor 是 lazy import 的,framework 在没装它们的环境下仍可被 import
(只是 LiteLLMAdapter 实例化时才会触发 ProviderError)。
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from ..observability.compactor import compact_messages
from ..observability.secrets import redact_mapping
from .base import (
    ProviderAdapter,
    ProviderCall,
    ProviderError,
    ProviderResult,
    ProviderTimeout,
    SchemaValidationError,
)


def _import_litellm():
    try:
        import litellm  # type: ignore
    except ImportError as exc:
        raise ProviderError(
            "litellm is not installed. `pip install litellm`."
        ) from exc
    # Different providers accept different params (e.g. Anthropic rejects `seed`
    # that OpenAI accepts). Since this adapter routes across providers via a
    # single call signature, silently drop provider-unsupported params rather
    # than making the caller provider-aware. Overridable via env
    # LITELLM_DROP_PARAMS=False for strict-mode debugging.
    import os as _os
    if _os.environ.get("LITELLM_DROP_PARAMS", "True").lower() != "false":
        litellm.drop_params = True
    return litellm


def _import_instructor():
    try:
        import instructor  # type: ignore
    except ImportError as exc:
        raise ProviderError(
            "instructor is not installed. `pip install instructor`."
        ) from exc
    return instructor


class LiteLLMAdapter(ProviderAdapter):
    """Wraps `litellm.acompletion` + `instructor.from_litellm(acompletion)` for
    structured calls. Async-first; sync callers work via the base-class shim
    (`asyncio.run`).

    `supports(model)` is permissive — LiteLLM accepts a wide variety of model ids.
    Fine-grained gating should be done via ProviderPolicy.
    """

    name = "litellm"

    def __init__(self, *, default_timeout_s: float = 60.0) -> None:
        self._default_timeout_s = default_timeout_s
        self._async_instructor_client = None  # lazily initialized

    # ---- surface ----

    def supports(self, model: str) -> bool:
        return True

    async def acompletion(self, call: ProviderCall) -> ProviderResult:
        litellm = _import_litellm()
        messages = _maybe_apply_prompt_cache(call)
        kwargs: dict[str, Any] = {
            "model": call.model,
            "messages": messages,
            "temperature": call.temperature,
            "timeout": call.timeout_s or self._default_timeout_s,
        }
        if call.max_tokens is not None:
            kwargs["max_tokens"] = call.max_tokens
        if call.seed is not None:
            kwargs["seed"] = call.seed
        if call.api_key is not None:
            kwargs["api_key"] = call.api_key
        if call.api_base is not None:
            kwargs["api_base"] = call.api_base
        kwargs.update({k: v for k, v in call.extra.items()
                       if not k.startswith("_forge_")})
        try:
            resp = await litellm.acompletion(**kwargs)
        except Exception as exc:
            msg = str(exc)
            if "timeout" in msg.lower() or "timed out" in msg.lower():
                raise ProviderTimeout(msg) from exc
            raise ProviderError(msg) from exc

        text = _extract_text(resp)
        usage = _extract_usage(resp)
        return ProviderResult(
            text=text, model=call.model, usage=usage,
            raw=redact_mapping(_raw_debug(resp, call)),
        )

    async def astructured(
        self, call: ProviderCall, schema: type[BaseModel],
    ) -> BaseModel:
        obj, _usage = await self.astructured_with_usage(call, schema)
        return obj

    async def astructured_with_usage(
        self, call: ProviderCall, schema: type[BaseModel],
    ) -> tuple[BaseModel, dict[str, int]]:
        instructor = _import_instructor()
        litellm = _import_litellm()
        if self._async_instructor_client is None:
            self._async_instructor_client = instructor.from_litellm(
                litellm.acompletion,
            )

        messages = _maybe_apply_prompt_cache(call)
        kwargs: dict[str, Any] = {
            "model": call.model,
            "messages": messages,
            "temperature": call.temperature,
            "timeout": call.timeout_s or self._default_timeout_s,
            "response_model": schema,
        }
        if call.max_tokens is not None:
            kwargs["max_tokens"] = call.max_tokens
        if call.seed is not None:
            kwargs["seed"] = call.seed
        if call.api_key is not None:
            kwargs["api_key"] = call.api_key
        if call.api_base is not None:
            kwargs["api_base"] = call.api_base
        kwargs.update({k: v for k, v in call.extra.items()
                       if not k.startswith("_forge_")})

        try:
            # Prefer `create_with_completion` so we can read the raw LiteLLM
            # response for token usage — required for BudgetTracker to charge
            # this call. Fall back to plain `create` if the installed
            # instructor build doesn't expose it.
            completions = self._async_instructor_client.chat.completions
            create_with_completion = getattr(
                completions, "create_with_completion", None,
            )
            if create_with_completion is not None:
                obj, raw_completion = await create_with_completion(**kwargs)
                usage = _extract_usage(raw_completion)
            else:
                obj = await completions.create(**kwargs)
                usage = {}
        except Exception as exc:
            msg = str(exc)
            if "timeout" in msg.lower():
                raise ProviderTimeout(msg) from exc
            if "validation" in msg.lower() or "schema" in msg.lower():
                raise SchemaValidationError(msg) from exc
            raise ProviderError(msg) from exc

        if not isinstance(obj, schema):
            raise SchemaValidationError(
                f"instructor returned {type(obj).__name__}, expected {schema.__name__}"
            )
        return obj, usage


def _maybe_apply_prompt_cache(call: ProviderCall) -> list[dict[str, Any]]:
    """If caller set `extra['_forge_prompt_cache']=True` and model is Anthropic-
    family, inject `cache_control: {"type": "ephemeral"}` on the system message
    and first large user block. Reduces repeated long-prefix token cost by ~90%
    (pricing: cache write 25% more, cache hit 10% of normal input cost).

    For non-Anthropic models or when the flag is off, returns messages unchanged.
    """
    messages = _maybe_auto_compact(call)
    if not call.extra.get("_forge_prompt_cache"):
        return messages
    if not _is_anthropic_family(call.model):
        return messages

    out: list[dict[str, Any]] = []
    tagged = 0
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content")
        # Only tag the first system message + first large user block
        if tagged < 2 and role in ("system", "user"):
            if isinstance(content, str) and len(content) >= 1024:
                out.append({
                    "role": role,
                    "content": [{
                        "type": "text", "text": content,
                        "cache_control": {"type": "ephemeral"},
                    }],
                })
                tagged += 1
                continue
            if isinstance(content, list):
                # Already multimodal blocks — tag the last text block
                new_blocks: list[dict[str, Any]] = []
                cache_applied = False
                for block in content:
                    if (not cache_applied and isinstance(block, dict)
                            and block.get("type") == "text"):
                        b = dict(block)
                        b["cache_control"] = {"type": "ephemeral"}
                        new_blocks.append(b)
                        cache_applied = True
                    else:
                        new_blocks.append(block)
                if cache_applied:
                    out.append({"role": role, "content": new_blocks})
                    tagged += 1
                    continue
        out.append(dict(msg))
    return out


def _maybe_auto_compact(call: ProviderCall) -> list[dict[str, Any]]:
    """Auto-compact helper. Opt-in via `extra['_forge_auto_compact_tokens']=N`.

    Trims the message history to ≤ N tokens (rough 4-char/token estimate)
    while preserving the first system message and last few turns. No-op when
    the flag is absent or zero.
    """
    limit = call.extra.get("_forge_auto_compact_tokens")
    if not limit:
        return list(call.messages)
    try:
        max_tokens = int(limit)
    except (TypeError, ValueError):
        return list(call.messages)
    keep_tail = int(call.extra.get("_forge_auto_compact_tail", 4))
    compacted, _ = compact_messages(
        list(call.messages), max_tokens=max_tokens, keep_tail_turns=keep_tail,
    )
    return compacted


def _is_anthropic_family(model: str) -> bool:
    m = model.lower()
    return m.startswith("anthropic/") or m.startswith("claude-") or "claude" in m


def _extract_text(resp: Any) -> str:
    try:
        return resp.choices[0].message.content or ""
    except Exception:  # pragma: no cover
        return ""


def _extract_usage(resp: Any) -> dict[str, int]:
    u = getattr(resp, "usage", None)
    if u is None:
        return {}
    return {
        "prompt": int(getattr(u, "prompt_tokens", 0) or 0),
        "completion": int(getattr(u, "completion_tokens", 0) or 0),
        "total": int(getattr(u, "total_tokens", 0) or 0),
    }


def _raw_debug(resp: Any, call: ProviderCall) -> dict[str, Any]:
    return {
        "model": call.model,
        "response_id": getattr(resp, "id", None),
        "finish_reason": _safe_finish_reason(resp),
    }


def _safe_finish_reason(resp: Any) -> str | None:
    try:
        return resp.choices[0].finish_reason
    except Exception:  # pragma: no cover
        return None
