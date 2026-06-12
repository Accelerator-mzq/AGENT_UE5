// Copyright Phase14 v0 attempt2. 自包含 demo 插件构建规则。
using UnrealBuildTool;

// Demo_MonopolyAuction 运行时模块构建规则。
// 依赖严格限定在施工规范 §1 白名单内:Core/CoreUObject/Engine/InputCore + UMG/Slate/SlateCore。
// 不依赖 Mvpv4TestCodex 主模块任何类(完全自包含),保证扇出与隔离。
public class Demo_MonopolyAuction : ModuleRules
{
	public Demo_MonopolyAuction(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		// 公开依赖:核心反射/引擎/输入。
		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore"
		});

		// 私有依赖:UMG/Slate 用于运行时 CreateWidget 呈现 HUD 与前台外壳。
		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"UMG",
			"Slate",
			"SlateCore"
		});
	}
}
