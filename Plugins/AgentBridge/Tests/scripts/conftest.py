# -*- coding: utf-8 -*-
"""
pytest 共享 fixtures
用于 AgentBridge 系统测试
"""
import os
import sys
import pytest


@pytest.fixture
def plugin_root():
    """返回 AgentBridge 插件根目录路径"""
    # Tests/scripts/ -> Tests/ -> AgentBridge/
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


@pytest.fixture
def project_root(plugin_root):
    """返回项目根目录路径"""
    return os.path.abspath(os.path.join(plugin_root, '..', '..'))


@pytest.fixture
def schemas_dir(plugin_root):
    """返回 Schemas 目录路径"""
    return os.path.join(plugin_root, 'Schemas')


@pytest.fixture
def scripts_dir(plugin_root):
    """返回 Scripts 目录路径"""
    return os.path.join(plugin_root, 'Scripts')


@pytest.fixture
def bridge_module(scripts_dir):
    """将 bridge 模块目录加入 sys.path 并返回路径"""
    bridge_path = os.path.join(scripts_dir, 'bridge')
    if bridge_path not in sys.path:
        sys.path.insert(0, bridge_path)
    return bridge_path


@pytest.fixture
def orchestrator_module(scripts_dir):
    """将 orchestrator 模块目录加入 sys.path 并返回路径"""
    orc_path = os.path.join(scripts_dir, 'orchestrator')
    if orc_path not in sys.path:
        sys.path.insert(0, orc_path)
    return orc_path


@pytest.fixture
def compiler_module(scripts_dir):
    """将 compiler 所在 Scripts 目录加入 sys.path 并返回路径"""
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    return scripts_dir
