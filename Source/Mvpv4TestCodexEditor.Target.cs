// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class Mvpv4TestCodexEditorTarget : TargetRules
{
	public Mvpv4TestCodexEditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.V5;
		IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_5;
		ExtraModuleNames.Add("Mvpv4TestCodex");

		// 测试插件保持按需启用，但需要进入 Editor target 收据，命令行才能显式加载它。
		BuildPlugins.Add("AgentBridgeTests");
	}
}
