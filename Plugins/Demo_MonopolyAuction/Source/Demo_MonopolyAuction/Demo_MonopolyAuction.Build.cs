// Copyright Phase14 demo agent. 自包含 runtime 模块构建规则。
using UnrealBuildTool;

// Demo_MonopolyAuction 模块构建规则。
// 依赖严格限定在施工规范 §1 白名单内:Core/CoreUObject/Engine/InputCore/UMG/Slate/SlateCore。
// 不依赖 Mvpv4TestCodex 主模块的任何类——本 demo 完全自包含。
public class Demo_MonopolyAuction : ModuleRules
{
	public Demo_MonopolyAuction(ReadOnlyTargetRules Target) : base(Target)
	{
		// 使用显式 include 路径策略,头文件冲突更可控
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

		// 公有依赖:游戏逻辑与状态使用 Core/CoreUObject/Engine/InputCore
		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore"
		});

		// 私有依赖:UI 层使用 UMG/Slate/SlateCore(Widget 与 UI 构建)
		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"UMG",
			"Slate",
			"SlateCore"
		});
	}
}
