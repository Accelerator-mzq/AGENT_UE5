// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;
using System.Collections.Generic;

public class Mvpv4TestCodexEditorTarget : TargetRules
{
	public Mvpv4TestCodexEditorTarget( TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.V5;
		IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_5;
		ExtraModuleNames.Add("Mvpv4TestCodex");
		// 测试插件改为按需启用，避免普通打开项目时把 AgentBridgeTests 写进默认 receipt。
		// Task19 / Automation / Functional Test 场景下，继续通过命令行显式 -EnablePlugins=AgentBridgeTests。
	}
}
