# Git Ignore / VSCode / Codex 配置入库记录（2026-04-02）

## 目的

- 将 `.codex` 项目配置纳入 Git，避免本地配置丢失。
- 将 `.vscode` 的稳定工程配置纳入 Git，避免 VS Code 工程配置丢失。
- 继续忽略 `.vscode` 下自动生成的大目录，避免无意义产物进入版本库。

## 本次规则调整

- 更新 `.gitignore`
  - 不再整体忽略 `.vscode/`
  - 改为仅放行以下稳定配置文件：
    - `.vscode/c_cpp_properties.json`
    - `.vscode/compileCommands_Default.json`
    - `.vscode/compileCommands_Mvpv4TestCodex.json`
    - `.vscode/launch.json`
    - `.vscode/settings.json`
    - `.vscode/tasks.json`
  - 继续忽略 `.vscode/*` 下其他内容，因此自动生成目录 `compileCommands_Default/` 与 `compileCommands_Mvpv4TestCodex/` 仍不会入库
- 更新 `.ignore`
  - 去掉 `/.codex`
  - 去掉 `/.vscode`

## 本次纳入版本管理的文件

- `.codex/config.toml`
- `.vscode/c_cpp_properties.json`
- `.vscode/compileCommands_Default.json`
- `.vscode/compileCommands_Mvpv4TestCodex.json`
- `.vscode/launch.json`
- `.vscode/settings.json`
- `.vscode/tasks.json`
- `.gitignore`
- `.ignore`

## 分支与发布

- 分支：`feat/phase6-archive-and-followups`
- PR：`https://github.com/Accelerator-mzq/AGENT_UE5/pull/19`
- 配置提交：`32d5c34fb50e0500e2b60353278811cba8896c4b`
- 当前分支头：`d677b19ace7126655bdd466fa533b9705c8de68f`
- 推送结果：已推送到 `origin/feat/phase6-archive-and-followups`
- PR 状态：`OPEN`

## 核验结论

- `.codex` 已可被 Git 跟踪
- `.vscode` 的稳定配置文件已可被 Git 跟踪
- `.vscode/compileCommands_Default/` 与 `.vscode/compileCommands_Mvpv4TestCodex/` 仍被 `.gitignore` 忽略
