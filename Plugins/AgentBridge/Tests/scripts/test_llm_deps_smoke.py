# -*- coding: utf-8 -*-
"""LLM 依赖装载 smoke 测试 — 验证 litellm/instructor/pydantic/httpx 可 import。

Phase 12 LLM Internal Reopen T01 破冰 task 产物:任何后续 T02-T20 task
都依赖这 4 个包,先在最早阶段卡住缺依赖的情况,给出清晰错误提示。
"""

import importlib

import pytest


# 必需包及其最低版本约束(版本字符串仅作记号,实际版本校验交给 check_llm_deps.py)
REQUIRED_PACKAGES = {
    "litellm": "1.0",
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
