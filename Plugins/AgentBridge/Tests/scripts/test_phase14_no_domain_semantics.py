# -*- coding: utf-8 -*-
"""DMP-11~12: 防固化守则机器化——demo_plan 机制代码与 MCP 工具实现零游戏领域语义。

检查对象是机制源码;schema example、测试夹具、施工规范实例(项目层)不在范围内。
"""
import re
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]

# 领域词黑名单:来自既有 GDD/模板的游戏语义词根(小写比对)
_DOMAIN_WORDS = re.compile(
    r"monopoly|auction|stock|jrpg|dice|board|tile|jail|property|economy|turn[_ ]?loop",
    re.IGNORECASE,
)

_MECHANISM_FILES = [
    PLUGIN_ROOT / "Compiler" / "demo_plan" / "planner.py",
    PLUGIN_ROOT / "Compiler" / "demo_plan" / "story_store.py",
    PLUGIN_ROOT / "Compiler" / "demo_plan" / "evidence_validator.py",
    PLUGIN_ROOT / "Compiler" / "demo_plan" / "velocity.py",
    PLUGIN_ROOT / "Compiler" / "demo_plan" / "manifest_loader.py",
]


class TestNoDomainSemantics:
    def test_dmp11_demo_plan_modules_free_of_domain_words(self):
        for path in _MECHANISM_FILES:
            if not path.exists():
                continue  # 后续 task 才创建的模块,创建后自动纳入扫描
            hits = _DOMAIN_WORDS.findall(path.read_text(encoding="utf-8"))
            assert not hits, f"{path.name} 含游戏领域词(防固化违规): {sorted(set(hits))}"

    def test_dmp12_mcp_demo_tool_impl_free_of_domain_words(self):
        src = (PLUGIN_ROOT / "MCP" / "compiler_tools.py").read_text(encoding="utf-8")
        # 只扫描 Phase 14 两个工具函数体(文件其余部分属 Phase 13 既有范围)
        match = re.search(r"def demo_story_fetch.*?(?=\ndef [a-z]|\Z)", src, re.DOTALL)
        if match is None:
            return  # 工具尚未实现(Task 7),实现后自动生效
        segment = src[match.start():]
        hits = _DOMAIN_WORDS.findall(segment)
        assert not hits, f"MCP demo 工具实现含游戏领域词: {sorted(set(hits))}"
