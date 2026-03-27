# AgentUE5Framework 仓库拆分重构规格 v2

> 执行者：Codex
> 目标：将现有单仓重构为**项目仓**（原地保留）+ **插件仓**（新建，挂载为 submodule）

---

## 0. 目录结构对比

### 重构前

```
Mvpv4TestCodex/              ← 项目仓根（唯一 .git）
├── Mvpv4TestCodex.uproject
├── AGENTS.md
├── README.md
├── task.md
├── Config/
├── Content/
├── Docs/
├── Gauntlet/
├── Plugins/
│   ├── AgentUE5Framework/         ← 插件 C++ 源码
│   └── AgentUE5FrameworkTests/    ← 测试插件 C++ 源码
├── reports/
├── roadmap/
├── Saved/
├── Schemas/
├── Scripts/
│   ├── bridge/
│   ├── orchestrator/
│   └── validation/
├── Source/
└── Specs/
```

### 重构后

```
Mvpv4TestCodex/                        ← 项目仓根（.git）
├── Mvpv4TestCodex.uproject
├── .gitmodules                         ← 新增
├── Config/
├── Content/
├── Source/
│   ├── Mvpv4TestCodex/
│   ├── Mvpv4TestCodex.Target.cs
│   └── Mvpv4TestCodexEditor.Target.cs
├── Scripts/
│   └── validation/
│       ├── start_ue_editor_project.ps1      ← 保留（项目级）
│       └── create_task15_functional_map.py  ← 保留（项目级）
└── Plugins/
    └── AgentUE5Framework/                   ← 插件仓根（独立 .git，submodule）
        ├── AgentUE5Framework.uplugin
        ├── AGENTS.md
        ├── README.md
        ├── task.md
        ├── .gitignore
        ├── Source/
        │   └── AgentUE5Framework/
        │       ├── AgentUE5Framework.Build.cs
        │       ├── Public/
        │       └── Private/
        ├── AgentUE5FrameworkTests/          ← 测试插件（嵌套在插件仓内）
        │   ├── AgentUE5FrameworkTests.uplugin
        │   └── Source/AgentUE5FrameworkTests/
        ├── Docs/
        ├── Gauntlet/
        ├── Schemas/
        ├── Scripts/
        │   ├── bridge/
        │   │   ├── project_config.py  ← 新增（路径解析核心）
        │   │   ├── bridge_core.py
        │   │   ├── query_tools.py
        │   │   ├── write_tools.py
        │   │   ├── ui_tools.py
        │   │   ├── remote_control_client.py
        │   │   ├── uat_runner.py
        │   │   ├── ue_helpers.py
        │   │   └── __init__.py
        │   ├── orchestrator/
        │   └── validation/
        │       ├── validate_examples.py
        │       └── validate_no_legacy_automation_entrypoints.ps1
        ├── Specs/
        ├── reports/
        └── roadmap/
```

---

## 1. 第一阶段：在项目仓外建立插件仓裸仓

插件仓最终要挂载到 `Plugins/AgentUE5Framework/`，但建立 submodule 时目标目录必须为空。
因此先在**项目仓外**初始化插件仓，迁移内容，再用 `git submodule add` 挂入。

```powershell
# 在项目仓的上一级目录操作
cd <Mvpv4TestCodex 的父目录>

# 初始化插件仓（临时位置，稍后挂入）
New-Item -ItemType Directory AgentUE5Framework_repo
cd AgentUE5Framework_repo
git init
```

---

## 2. 第二阶段：迁移文件到插件仓

所有源路径均相对于 `<父目录>/Mvpv4TestCodex/`。

```powershell
$src = "<父目录>\Mvpv4TestCodex"
$dst = "<父目录>\AgentUE5Framework_repo"

# ── C++ 插件核心（展开到插件仓根，uplugin 在根目录）
Copy-Item -Recurse "$src\Plugins\AgentUE5Framework\*" $dst

# ── 测试插件（嵌套在插件仓内）
New-Item -ItemType Directory "$dst\AgentUE5FrameworkTests"
Copy-Item -Recurse "$src\Plugins\AgentUE5FrameworkTests\*" "$dst\AgentUE5FrameworkTests\"

# ── 文档生态
foreach ($d in @("Docs","Schemas","Specs","Gauntlet","roadmap","reports")) {
    Copy-Item -Recurse "$src\$d" $dst
}

# ── Scripts（部分迁移，保留项目级2个脚本）
New-Item -ItemType Directory -Force "$dst\Scripts\bridge"
New-Item -ItemType Directory -Force "$dst\Scripts\orchestrator"
New-Item -ItemType Directory -Force "$dst\Scripts\validation"
Copy-Item -Recurse "$src\Scripts\bridge\*"       "$dst\Scripts\bridge\"
Copy-Item -Recurse "$src\Scripts\orchestrator\*" "$dst\Scripts\orchestrator\"
Copy-Item "$src\Scripts\validation\validate_examples.py"                          "$dst\Scripts\validation\"
Copy-Item "$src\Scripts\validation\validate_no_legacy_automation_entrypoints.ps1" "$dst\Scripts\validation\"

# ── 根文档
foreach ($f in @("AGENTS.md","README.md","task.md")) {
    Copy-Item "$src\$f" $dst
}
```

---

## 3. 第三阶段：新增文件

### 3.1 `AgentUE5Framework_repo/.gitignore`

```gitignore
Binaries/
Intermediate/
DerivedDataCache/
.vs/
__pycache__/
*.pyc
*.pyo
.venv/
venv/
.DS_Store
Thumbs.db
*.suo
*.user
local_config.py
project_local.env
```

### 3.2 `AgentUE5Framework_repo/Scripts/bridge/project_config.py`（必须新建）

```python
"""
project_config.py — 项目根目录解析器

插件仓在项目中的位置：
  <ProjectRoot>/Plugins/AgentUE5Framework/Scripts/bridge/project_config.py

解析策略（优先级从高到低）：
  1. 环境变量 UE_PROJECT_ROOT
  2. 从本文件位置向上搜索，找到含 .uproject 的目录
  3. 抛出 RuntimeError
"""

import os
import pathlib
from functools import lru_cache


@lru_cache(maxsize=1)
def get_project_root() -> pathlib.Path:
    """返回 UE5 项目根目录（含 .uproject 的目录）。"""
    env_root = os.environ.get("UE_PROJECT_ROOT", "").strip()
    if env_root:
        p = pathlib.Path(env_root).resolve()
        if not p.is_dir():
            raise RuntimeError(f"UE_PROJECT_ROOT 指向的目录不存在：{p}")
        if not list(p.glob("*.uproject")):
            raise RuntimeError(f"UE_PROJECT_ROOT={p} 下未找到 .uproject 文件。")
        return p

    # 本文件路径：<ProjectRoot>/Plugins/AgentUE5Framework/Scripts/bridge/project_config.py
    # 向上遍历祖先目录，找到第一个含 .uproject 的目录
    for ancestor in pathlib.Path(__file__).resolve().parents:
        if list(ancestor.glob("*.uproject")):
            return ancestor

    raise RuntimeError(
        "未能自动定位 UE5 项目根目录。\n"
        "请设置环境变量 UE_PROJECT_ROOT，例如：\n"
        "  $env:UE_PROJECT_ROOT = 'D:\\Projects\\Mvpv4TestCodex'"
    )


def get_uproject_path() -> pathlib.Path:
    """返回 .uproject 文件完整路径。"""
    root = get_project_root()
    candidates = list(root.glob("*.uproject"))
    if not candidates:
        raise RuntimeError(f"项目根 {root} 下未找到 .uproject 文件。")
    return candidates[0]


def get_saved_dir() -> pathlib.Path:
    """返回 <ProjectRoot>/Saved/ 路径。"""
    return get_project_root() / "Saved"


def get_plugin_root() -> pathlib.Path:
    """
    返回插件仓根目录（AgentUE5Framework.uplugin 所在目录）。
    路径：Scripts/bridge/project_config.py → bridge → Scripts → 插件根
    """
    return pathlib.Path(__file__).resolve().parent.parent.parent


def get_schemas_dir() -> pathlib.Path:
    return get_plugin_root() / "Schemas"


def get_specs_dir() -> pathlib.Path:
    return get_plugin_root() / "Specs"


def get_reports_dir() -> pathlib.Path:
    return get_plugin_root() / "reports"


if __name__ == "__main__":
    print("=== project_config 路径自检 ===")
    try:
        print(f"plugin_root   : {get_plugin_root()}")
        print(f"project_root  : {get_project_root()}")
        print(f"uproject_path : {get_uproject_path()}")
        print(f"saved_dir     : {get_saved_dir()}")
        print(f"schemas_dir   : {get_schemas_dir()}")
        print(f"specs_dir     : {get_specs_dir()}")
        print(f"reports_dir   : {get_reports_dir()}")
        print("\n[OK] 全部路径解析成功。")
    except RuntimeError as e:
        print(f"\n[ERROR] {e}")
```

---

## 4. 第四阶段：修改现有脚本中的路径引用

### 规则

Codex 修改时遵循以下约束：
- **不得**硬编码 `Mvpv4TestCodex` 字符串
- **不得**用超过 3 级的 `../../..` 构造跨 submodule 边界的路径
- 凡需要 `.uproject` → 用 `get_uproject_path()`
- 凡需要 `Saved/` → 用 `get_saved_dir()`
- 凡需要 `Schemas/` → 用 `get_schemas_dir()`
- 凡需要 `Specs/` → 用 `get_specs_dir()`
- 凡需要 `reports/` → 用 `get_reports_dir()`

### import 写法

同目录模块间调用：
```python
from project_config import get_uproject_path, get_saved_dir
```

从 orchestrator/ 或其他子目录调用：
```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "bridge"))
from project_config import get_uproject_path, get_saved_dir
```

### 各文件改动要点

| 文件 | 需要替换的旧模式 | 新写法 |
|---|---|---|
| `Scripts/bridge/bridge_core.py` | 任何通过 `__file__` 推导的项目根路径（`PROJECT_ROOT` 等全局变量） | `from project_config import get_project_root, get_plugin_root` |
| `Scripts/bridge/uat_runner.py` | `.uproject` 路径构造、`Saved/` 路径构造 | `get_uproject_path()`、`get_saved_dir()` |
| `Scripts/bridge/ue_helpers.py` | UE Editor 路径（通常通过 `.uproject` 位置推导） | `get_uproject_path()` |
| `Scripts/orchestrator/orchestrator.py` | `Saved/`、`reports/` 路径构造 | `get_saved_dir()`、`get_reports_dir()` |
| `Scripts/orchestrator/report_generator.py` | `reports/` 路径构造 | `get_reports_dir()` |
| `Scripts/orchestrator/spec_reader.py` | `Specs/` 路径构造 | `get_specs_dir()` |
| `Scripts/validation/validate_examples.py` | `Schemas/` 路径构造 | `get_schemas_dir()` |

**不需要修改的文件**（内部相对路径不跨边界）：
`query_tools.py` / `write_tools.py` / `ui_tools.py` / `remote_control_client.py` /
`__init__.py` / `verifier.py` / `plan_generator.py`

---

## 5. 第五阶段：提交插件仓

```powershell
cd <父目录>/AgentUE5Framework_repo
git add .
git commit -m "init: migrate AgentUE5Framework plugin ecosystem from Mvpv4TestCodex"
```

---

## 6. 第六阶段：清理项目仓 + 建立 submodule

### 6.1 删除项目仓中已迁出的文件

```powershell
cd <父目录>/Mvpv4TestCodex

# 插件目录（将由 submodule 接管）
Remove-Item -Recurse -Force Plugins\AgentUE5Framework
Remove-Item -Recurse -Force Plugins\AgentUE5FrameworkTests

# 迁出的文档与脚本
Remove-Item -Recurse -Force Docs, Schemas, Specs, Gauntlet, roadmap, reports
Remove-Item -Force AGENTS.md, README.md, task.md
Remove-Item -Recurse -Force Scripts\bridge, Scripts\orchestrator
Remove-Item -Force Scripts\validation\validate_examples.py
Remove-Item -Force "Scripts\validation\validate_no_legacy_automation_entrypoints.ps1"

# 提交清理
git add -A
git commit -m "chore: remove plugin files before submodule attach"
```

### 6.2 将插件仓挂载为 submodule

```powershell
# 本地阶段（插件仓还未推远端）
git submodule add ../AgentUE5Framework_repo Plugins/AgentUE5Framework

# 验证 .gitmodules 内容
Get-Content .gitmodules
# 预期：
# [submodule "Plugins/AgentUE5Framework"]
#     path = Plugins/AgentUE5Framework
#     url = ../AgentUE5Framework_repo
#     ignore = untracked

# 提交
git add .gitmodules Plugins/AgentUE5Framework
git commit -m "feat: add AgentUE5Framework as git submodule at Plugins/AgentUE5Framework"
```

### 6.3 确认项目仓 `.gitignore` 包含以下条目

```gitignore
Saved/
Intermediate/
Binaries/
DerivedDataCache/
.vs/
Build/
```

---

## 7. 验证清单（按顺序执行）

### V1：路径自检

```powershell
cd <父目录>/Mvpv4TestCodex
python Plugins/AgentUE5Framework/Scripts/bridge/project_config.py
```

预期输出：
```
=== project_config 路径自检 ===
plugin_root   : ...\Mvpv4TestCodex\Plugins\AgentUE5Framework
project_root  : ...\Mvpv4TestCodex
uproject_path : ...\Mvpv4TestCodex\Mvpv4TestCodex.uproject
saved_dir     : ...\Mvpv4TestCodex\Saved
schemas_dir   : ...\Mvpv4TestCodex\Plugins\AgentUE5Framework\Schemas
specs_dir     : ...\Mvpv4TestCodex\Plugins\AgentUE5Framework\Specs
reports_dir   : ...\Mvpv4TestCodex\Plugins\AgentUE5Framework\reports

[OK] 全部路径解析成功。
```

### V2：Schema 校验链

```powershell
python Plugins/AgentUE5Framework/Scripts/validation/validate_examples.py --strict
# 预期：Checked examples: 8 / Passed: 8 / Failed: 0
```

### V3：submodule 状态

```powershell
git submodule status
# 预期：<hash> Plugins/AgentUE5Framework (heads/main)
# 无前缀 - （- 表示未初始化）
```

### V4：UE5 插件发现

打开 UE5 Editor，进入 Edit → Plugins，确认以下两个插件可见且已启用：
- `AgentUE5Framework`（位于 `Plugins/AgentUE5Framework/AgentUE5Framework.uplugin`）
- `AgentUE5FrameworkTests`（位于 `Plugins/AgentUE5Framework/AgentUE5FrameworkTests/AgentUE5FrameworkTests.uplugin`）

### V5：Bridge 连通性（UE5 Editor 运行中）

```powershell
python -c "
from Plugins.AgentUE5Framework.Scripts.bridge.project_config import get_uproject_path
print('uproject:', get_uproject_path())
"
# 或在插件 Scripts 目录下直接运行
cd Plugins/AgentUE5Framework/Scripts/bridge
python -c "from project_config import get_uproject_path; print(get_uproject_path())"
```

---

## 8. 远端推送（本地验证全部通过后）

```powershell
# 第一步：推插件仓
cd <父目录>/AgentUE5Framework_repo
git remote add origin https://github.com/Accelerator-mzq/AgentUE5Framework
git push -u origin main

# 第二步：更新项目仓的 submodule URL
cd <父目录>/Mvpv4TestCodex
# 编辑 .gitmodules，将 url 行改为远端地址：
#   url = https://github.com/Accelerator-mzq/AgentUE5Framework
git submodule sync
git add .gitmodules
git commit -m "chore: update submodule url to GitHub remote"
git push
```

---

## 9. 注意事项

1. **AgentUE5FrameworkTests 不需要单独挂 submodule**。UE5 递归扫描 `Plugins/AgentUE5Framework/` 下所有 `.uplugin` 文件，`AgentUE5FrameworkTests/AgentUE5FrameworkTests.uplugin` 会被自动发现和加载。

2. **`Saved/` 跨 submodule 边界访问是唯一的合法跨界点**。插件仓脚本通过 `get_saved_dir()` 读取 `<ProjectRoot>/Saved/`，这是设计上允许的，其他路径不得跨边界。

3. **本地 submodule URL 使用相对路径**（`../AgentUE5Framework_repo`），推远端后改为 GitHub URL，两步不要混淆。

4. **Codex 执行顺序**：第 1-5 阶段（建仓、迁移、新增、修改、提交）完成并跑 V1/V2 验证后，再执行第 6 阶段（清理项目仓、挂 submodule）。避免清理后发现脚本有问题无法回滚。
