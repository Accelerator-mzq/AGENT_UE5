// Copyright Phase14 demo agent.
// Visual 证据辅助:把各 UI widget / 底座类的反射结构(必备元素对应的 UFUNCTION/UPROPERTY)
// dump 成 per-story JSON,作为"截图证据降级"时的诚实最接近物(widget 树/接口 dump)。
// 说明:本 demo 的 UI 为 C++ UMG 基类,无 authored WBP 资产与绑定关卡,无人值守无法对每个
// 具体页面做有意义的渲染截图;故对 Visual 类按任务"降级条款"产出反射 dump + 一张真实引擎渲染。
#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "UObject/UnrealType.h"
#include "UObject/Class.h"
#include "MADemoHUDWidget.h"
#include "MADemoFrontendWidgets.h"
#include "MADemoFoundations.h"

#if WITH_AUTOMATION_TESTS

// 把一个 UClass 的可反射 UFUNCTION/UPROPERTY 名称 dump 成 JSON 文本。
static FString DumpClassReflection(UClass* Cls, const TArray<FString>& RequiredElements)
{
	FString Json = TEXT("{\n");
	Json += FString::Printf(TEXT("  \"class\": \"%s\",\n"), *Cls->GetName());
	Json += TEXT("  \"note\": \"生成物:widget 树/接口反射 dump,截图证据降级为反射产物(无 authored WBP+关卡,无人值守不可渲染具体页面);与 run 数据不一致时以数据为准\",\n");

	// 必备元素清单
	Json += TEXT("  \"required_elements\": [");
	for (int32 i = 0; i < RequiredElements.Num(); ++i)
	{
		Json += FString::Printf(TEXT("\"%s\"%s"), *RequiredElements[i],
			i + 1 < RequiredElements.Num() ? TEXT(", ") : TEXT(""));
	}
	Json += TEXT("],\n");

	// 反射出的 UFUNCTION
	Json += TEXT("  \"ufunctions\": [");
	bool bFirst = true;
	for (TFieldIterator<UFunction> It(Cls); It; ++It)
	{
		if (!bFirst) { Json += TEXT(", "); }
		Json += FString::Printf(TEXT("\"%s\""), *It->GetName());
		bFirst = false;
	}
	Json += TEXT("],\n");

	// 反射出的 UPROPERTY
	Json += TEXT("  \"uproperties\": [");
	bFirst = true;
	for (TFieldIterator<FProperty> It(Cls); It; ++It)
	{
		if (!bFirst) { Json += TEXT(", "); }
		Json += FString::Printf(TEXT("\"%s\""), *It->GetName());
		bFirst = false;
	}
	Json += TEXT("]\n}\n");
	return Json;
}

// 写 dump 到 ProjectState/Evidence/visual_dumps/<name>.json
static bool WriteDump(const FString& StoryName, UClass* Cls, const TArray<FString>& Required)
{
	const FString Dir = FPaths::ProjectDir() / TEXT("ProjectState/Evidence/visual_dumps");
	IFileManager::Get().MakeDirectory(*Dir, true);
	const FString Path = Dir / (StoryName + TEXT(".json"));
	return FFileHelper::SaveStringToFile(DumpClassReflection(Cls, Required), *Path);
}

// ── Visual dump 用例:为 9 个 Visual story 各产出反射 dump ─────────────
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoVisualDumpTest,
	"Demo_MonopolyAuction.Smoke.VisualDump",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FMADemoVisualDumpTest::RunTest(const FString& Parameters)
{
	bool bOk = true;
	bOk &= WriteDump(TEXT("baseline-start-screen"), UMADemoStartScreenWidget::StaticClass(),
		{ TEXT("project_identity_display"), TEXT("user_interaction_trigger"), TEXT("navigate_to_main_menu") });
	bOk &= WriteDump(TEXT("baseline-main-menu"), UMADemoMainMenuWidget::StaticClass(),
		{ TEXT("New Game"), TEXT("Settings"), TEXT("Quit") });
	bOk &= WriteDump(TEXT("baseline-settings"), UMADemoSettingsWidget::StaticClass(),
		{ TEXT("Master Volume"), TEXT("SFX Volume"), TEXT("Window Mode"), TEXT("Resolution"), TEXT("Apply"), TEXT("Back") });
	bOk &= WriteDump(TEXT("baseline-pause"), UMADemoPauseWidget::StaticClass(),
		{ TEXT("ESC entry"), TEXT("Resume"), TEXT("Settings"), TEXT("Quit to Menu") });
	bOk &= WriteDump(TEXT("baseline-results"), UMADemoResultsWidget::StaticClass(),
		{ TEXT("winner_info"), TEXT("Return to Menu") });
	bOk &= WriteDump(TEXT("baseline-hud"), UMADemoHUDWidget::StaticClass(),
		{ TEXT("current_turn"), TEXT("current_player"), TEXT("player_cash"), TEXT("dice_result"), TEXT("stock_summary") });
	bOk &= WriteDump(TEXT("baseline-input-foundation"), UMADemoInputFoundation::StaticClass(),
		{ TEXT("menu_confirm"), TEXT("menu_cancel"), TEXT("pause_input"), TEXT("roll_dice_action") });
	bOk &= WriteDump(TEXT("baseline-audio-foundation"), UMADemoAudioFoundation::StaticClass(),
		{ TEXT("bgm_volume_control"), TEXT("sfx_volume_control"), TEXT("basic_sfx_playback") });
	bOk &= WriteDump(TEXT("baseline-platform-foundation"), UMADemoPlatformFoundation::StaticClass(),
		{ TEXT("window_mode"), TEXT("resolution"), TEXT("quit_handling") });

	TestTrue(TEXT("所有 Visual dump 应写盘成功"), bOk);
	return true;
}

#endif // WITH_AUTOMATION_TESTS
