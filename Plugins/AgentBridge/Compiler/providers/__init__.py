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
