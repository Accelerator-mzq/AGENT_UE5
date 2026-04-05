"""
Remote Control API 通道包装（Channel B）。

直接导入并复用已有的 remote_control_client.py。
MCP Server 通过此模块调用 RC API。
"""

import sys
import os

# 确保 Bridge 目录在路径中
BRIDGE_DIR = os.path.join(os.path.dirname(__file__), '..', 'Scripts', 'bridge')
sys.path.insert(0, os.path.abspath(BRIDGE_DIR))

# 直接复用已有的 remote_control_client
from remote_control_client import (
    configure,
    get_base_url,
    call_function,
    get_property,
    set_property,
    batch,
    search_actors,
    search_assets,
    check_connection,
)

__all__ = [
    'configure',
    'get_base_url',
    'call_function',
    'get_property',
    'set_property',
    'batch',
    'search_actors',
    'search_assets',
    'check_connection',
]
