"""
project_config.py — 项目根目录解析器

插件仓在项目中的位置：
  <ProjectRoot>/Plugins/AgentBridge/Scripts/bridge/project_config.py

解析策略（优先级从高到低）：
  1. 环境变量 UE_PROJECT_ROOT
  2. 从本文件位置向上搜索，找到含 .uproject 的目录
  3. 抛出 RuntimeError
"""

from __future__ import annotations

import os
import pathlib
from datetime import date
from functools import lru_cache


@lru_cache(maxsize=1)
def get_project_root() -> pathlib.Path:
    """返回 UE5 项目根目录（含 .uproject 的目录）。"""
    env_root = os.environ.get("UE_PROJECT_ROOT", "").strip()
    if env_root:
        path = pathlib.Path(env_root).resolve()
        if not path.is_dir():
            raise RuntimeError(f"UE_PROJECT_ROOT 指向的目录不存在：{path}")
        if not list(path.glob("*.uproject")):
            raise RuntimeError(f"UE_PROJECT_ROOT={path} 下未找到 .uproject 文件。")
        return path

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
    返回插件仓根目录（AgentBridge.uplugin 所在目录）。
    路径：Scripts/bridge/project_config.py → bridge → Scripts → 插件根
    """
    return pathlib.Path(__file__).resolve().parent.parent.parent


def get_schemas_dir() -> pathlib.Path:
    """返回插件仓 Schemas/ 路径。"""
    return get_plugin_root() / "Schemas"


def get_specs_dir() -> pathlib.Path:
    """返回插件仓 Specs/ 路径。"""
    return get_plugin_root() / "Specs"


def get_reports_dir() -> pathlib.Path:
    """返回插件仓 reports/ 路径。"""
    return get_plugin_root() / "reports"


def get_project_reports_dir() -> pathlib.Path:
    """返回 <ProjectRoot>/ProjectState/Reports/ 路径。"""
    return get_project_root() / "ProjectState" / "Reports"


def get_report_date_dirname(target_date: str | None = None) -> str:
    """返回用于报告分层的日期目录名。"""
    return target_date or date.today().isoformat()


def get_dated_reports_dir(target_date: str | None = None) -> pathlib.Path:
    """返回插件仓 reports/<YYYY-MM-DD>/ 路径。"""
    return get_reports_dir() / get_report_date_dirname(target_date)


def get_dated_project_reports_dir(target_date: str | None = None) -> pathlib.Path:
    """返回 <ProjectRoot>/ProjectState/Reports/<YYYY-MM-DD>/ 路径。"""
    return get_project_reports_dir() / get_report_date_dirname(target_date)


def iter_report_files(report_dir: str | pathlib.Path, pattern: str = "*.json") -> list[pathlib.Path]:
    """递归遍历报告目录，兼容新增的按日期子目录布局。"""
    root = pathlib.Path(report_dir)
    if not root.exists():
        return []
    return [path for path in root.rglob(pattern) if path.is_file()]


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
        print(f"reports_daily : {get_dated_reports_dir()}")
        print(f"project_reports_dir   : {get_project_reports_dir()}")
        print(f"project_reports_daily : {get_dated_project_reports_dir()}")
        print("\n[OK] 全部路径解析成功。")
    except RuntimeError as exc:
        print(f"\n[ERROR] {exc}")

