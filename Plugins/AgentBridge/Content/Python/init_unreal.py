"""UE Editor Python 插件启动时自动执行,完成 AgentBridge 端 Python endpoint 注册。

UE 5.4+ PythonScriptPlugin 标准 hook:任何 plugin 的 Content/Python/init_unreal.py
在 Editor 启动时被自动执行。

关键:即使注册失败,也不能阻塞 Editor 启动。
"""
import unreal

unreal.log("[AgentBridge] Loading ForgeUE RC endpoint...")
try:
    import forgeue_rc_endpoint  # noqa: F401  # 导入即触发 @unreal.uclass() 注册
    unreal.log("[AgentBridge] ForgeUE RC endpoint registered.")
except Exception as exc:
    # 关键:即使注册失败,也不能阻塞 Editor 启动
    unreal.log_error(f"[AgentBridge] ForgeUE RC endpoint registration failed: {exc}")
