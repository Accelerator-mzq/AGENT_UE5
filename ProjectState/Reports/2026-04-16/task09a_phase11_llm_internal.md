# TASK 09A Evidence — LLM Internal 路径接入

日期：2026-04-16

## 任务范围

- 新增 [llm_client.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/stages/llm_client.py)，提供 `UnifiedLLMClient` 与 `load_llm_client_from_config()`。
- 新增 [llm_config.example.yaml](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Config/llm_config.example.yaml)，覆盖 `anthropic / openai / openai_compatible` 三种配置示例。
- 修改 [.gitignore](/D:/UnrealProjects/Mvpv4TestCodex/.gitignore)，忽略 `Plugins/AgentBridge/Config/llm_config.yaml`。
- 修改 [pipeline_orchestrator.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py)，将 Stage 4 的 `llm_client=None` 改为 `load_llm_client_from_config()`。
- 修改 [session.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/pipeline/session.py)，将 `VALID_GENERATOR_PROVIDERS` 扩展为 `{"llm", "mcp_agent", "heuristic_fallback"}`。
- 修改 [compiler_session.schema.json](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Schemas/compiler_session.schema.json)，同步放开 `mcp_agent` 枚举值。

## 关键实现说明

### 1. 统一客户端接口

`UnifiedLLMClient.call(messages) -> str` 已实现三路兼容：

- `anthropic`
- `openai`
- `openai_compatible`

实现约束：

- `anthropic` 的 `system` 从 messages 中拆出后单独传入 API。
- `openai / openai_compatible` 统一走 `chat.completions.create()`。
- SDK 缺失时不抛错，加载函数返回 `None`。

### 2. 配置加载策略

`load_llm_client_from_config()` 查找顺序：

1. 显式传入 `config_path`
2. 环境变量 `AGENT_BRIDGE_LLM_CONFIG`
3. `Plugins/AgentBridge/Config/llm_config.yaml`

容错约束：

- 配置文件不存在：返回 `None`
- `api_key` 为占位符：返回 `None`
- provider 非法：返回 `None`
- 对应 SDK 缺失：返回 `None` 并给出轻量警告

### 3. Git 管理策略

- 仓库中只提交模板 [llm_config.example.yaml](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Config/llm_config.example.yaml)
- 实际私密配置 `Plugins/AgentBridge/Config/llm_config.yaml` 由本地或 CI 创建，不进入版本库

本轮**没有**提交真实 `llm_config.yaml`，因为当前线程未提供可用 API key。

## 验证结果

### 1. 语法编译

```text
PY_COMPILE_OK
```

覆盖文件：

- [llm_client.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/stages/llm_client.py)
- [pipeline_orchestrator.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py)
- [session.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/pipeline/session.py)

### 2. `llm_client` 定向测试

```text
LLM_CLIENT_TESTS=passed
```

已验证：

- 缺失配置文件时 `load_llm_client_from_config()` 返回 `None`
- 占位符 API key 时返回 `None`
- 注入 fake `openai` SDK 后，`openai_compatible` 配置可成功构造客户端
- `UnifiedLLMClient.call()` 可返回底层响应文本

### 3. `.gitignore` 命中验证

```text
.gitignore:32:Plugins/AgentBridge/Config/llm_config.yaml	Plugins/AgentBridge/Config/llm_config.yaml
```

### 4. Session / Schema 对齐验证

```text
SESSION_MCP_AGENT_OK
```

已验证：

- `CompilerSession(generator_provider="mcp_agent")` 可成功构造
- `to_dict()` 会序列化 `generator_provider`
- `session.is_promotable` 在 `mcp_agent` 路径下为 `True`

### 5. Schema 示例校验

```text
Checked examples       : 19
Passed                 : 19
Failed                 : 0
Reference-only skipped : 0
Unmapped examples      : 0
Missing schema targets : 0

[SUCCESS] 全部 example 校验通过，本地校验链正常。
```

## 结论

TASK 09A 当前范围已完成：

- LLM Internal 路径缺失的客户端层已补齐
- pipeline Stage 4 不再硬编码 `llm_client=None`
- `mcp_agent` 已进入 session / schema 的合法枚举集合
- 私密配置文件已具备正确的 gitignore 保护

后续应继续执行 [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md) 中的 **TASK 09B**，完成三路 Generator（LLM Internal / MCP Agent / Heuristic Fallback）的完整运行验证与产物对比。
