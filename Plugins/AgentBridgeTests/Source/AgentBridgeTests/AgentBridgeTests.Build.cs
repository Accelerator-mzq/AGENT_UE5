// AgentBridgeTests.Build.cs
// AGENT + UE5 可操作层 — 测试 Plugin 构建配置
//
// 依赖的 UE5 官方测试模块：
//   AutomationController    — 触发和管理 Automation Test
//   FunctionalTesting       — AFunctionalTest 基类（L3 Functional Test）
//   Gauntlet               — GauntletTestController 基类
//   AutomationDriver        — L1_UIToolTests / L2_UIToolClosedLoopSpec 中引用 FAutomationDriverAdapter
//
// 依赖的项目模块：
//   AgentBridge            — 被测试的目标模块（含 AutomationDriverAdapter.h）

using UnrealBuildTool;

public class AgentBridgeTests : ModuleRules
{
    public AgentBridgeTests(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[]
        {
            "Core",
            "CoreUObject",
            "Engine",
        });

        PrivateDependencyModuleNames.AddRange(new string[]
        {
            // 被测试的目标
            "AgentBridge",

            // Editor 核心
            "UnrealEd",
            "EditorScriptingUtilities",

            // UE5 Automation Test Framework（L1 / L2）
            "AutomationController",

            // UE5 Functional Testing（L3 Functional Test）
            "FunctionalTesting",

            // Automation Driver（L1_UIToolTests + L2_UIToolClosedLoopSpec 引用 FAutomationDriverAdapter）
            "AutomationDriver",

            // JSON（解析 Bridge 响应）
            "Json",
            "JsonUtilities",

            // Gauntlet（CI/CD Controller）
            "Gauntlet",
        });
    }
}
