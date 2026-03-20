// AutomationDriverAdapter.cpp
// AGENT + UE5 可操作层 — L3 UI 工具层 Automation Driver 封装实现
//
// UE5 官方模块：Automation Driver（IAutomationDriverModule）
//
// 本文件实现语义级 UI 操作，将 Automation Driver 的底层 Widget 交互
// 封装为路径/名称/标签驱动的高层操作。

#include "AutomationDriverAdapter.h"

#include "Editor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "LevelEditorViewport.h"
#include "Selection.h"
#include "EditorLevelLibrary.h"

// Slate UI
#include "Framework/Application/SlateApplication.h"
#include "Widgets/SWidget.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SEditableTextBox.h"

// Module Manager（运行时检查 Automation Driver 模块）
#include "Modules/ModuleManager.h"

// 静态缓存
TSharedPtr<IAutomationDriver> FAutomationDriverAdapter::CachedDriver = nullptr;

// ============================================================
// 可用性检查
// ============================================================

bool FAutomationDriverAdapter::IsAvailable()
{
	return FModuleManager::Get().IsModuleLoaded(TEXT("AutomationDriver"));
}

// ============================================================
// Driver 实例管理
// ============================================================

TSharedPtr<IAutomationDriver> FAutomationDriverAdapter::GetOrCreateDriver()
{
	if (!IsAvailable())
	{
		return nullptr;
	}

	if (!CachedDriver.IsValid())
	{
		// 通过模块接口获取 Driver 实例
		// UE5.5 API:
		//   IAutomationDriverModule& Module = IAutomationDriverModule::Get();
		//   CachedDriver = Module.CreateDriver();
		//
		// 注意：实际 API 因 UE5 版本而异，集成时需根据 UE5.5.4 调整。
		UE_LOG(LogTemp, Log, TEXT("[AgentBridge L3] Creating Automation Driver instance"));
	}

	return CachedDriver;
}

// ============================================================
// 共用前置：选中 Actor + 打开 Detail Panel
// ============================================================

bool FAutomationDriverAdapter::SelectActorAndOpenDetails(const FString& ActorPath)
{
	if (!GEditor) return false;

	UWorld* World = GEditor->GetEditorWorldContext().World();
	if (!World) return false;

	// 查找 Actor
	AActor* TargetActor = nullptr;
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		if (It->GetPathName() == ActorPath)
		{
			TargetActor = *It;
			break;
		}
	}

	if (!TargetActor)
	{
		UE_LOG(LogTemp, Warning, TEXT("[AgentBridge L3] Actor not found: %s"), *ActorPath);
		return false;
	}

	// 选中 Actor（触发 Detail Panel 内容刷新）
	GEditor->SelectNone(/*bNoteSelectionChange=*/false, /*bDeselectBSPSurfs=*/true);
	GEditor->SelectActor(TargetActor, /*bInSelected=*/true, /*bNotify=*/true, /*bSelectEvenIfHidden=*/true);

	UE_LOG(LogTemp, Log, TEXT("[AgentBridge L3] Selected actor: %s"), *TargetActor->GetActorNameOrLabel());
	return true;
}

// ============================================================
// 操作 1: ClickDetailPanelButton
// ============================================================

FUIOperationResult FAutomationDriverAdapter::ClickDetailPanelButton(
	const FString& ActorPath,
	const FString& ButtonLabel,
	float TimeoutSeconds)
{
	FUIOperationResult Result;
	double StartTime = FPlatformTime::Seconds();

	if (!IsAvailable())
	{
		Result.FailureReason = TEXT("Automation Driver not available");
		return Result;
	}

	if (!SelectActorAndOpenDetails(ActorPath))
	{
		Result.FailureReason = FString::Printf(TEXT("Failed to select actor: %s"), *ActorPath);
		return Result;
	}

	// 在当前活跃窗口的 Widget 树中查找匹配按钮
	TSharedPtr<SWidget> ButtonWidget = nullptr;
	TSharedPtr<SWindow> ActiveWindow = FSlateApplication::Get().GetActiveTopLevelWindow();
	if (ActiveWindow.IsValid())
	{
		ButtonWidget = FindWidgetByLabel(ActiveWindow, ButtonLabel);
	}

	if (!ButtonWidget.IsValid())
	{
		Result.FailureReason = FString::Printf(TEXT("Button not found: '%s'"), *ButtonLabel);
		return Result;
	}

	// 计算按钮中心坐标并模拟点击
	FSlateApplication& SlateApp = FSlateApplication::Get();
	FGeometry ButtonGeometry = ButtonWidget->GetCachedGeometry();
	FVector2D ButtonCenter = ButtonGeometry.GetAbsolutePosition()
		+ ButtonGeometry.GetAbsoluteSize() * 0.5f;

	// Mouse Down
	FPointerEvent MouseDownEvent(
		0, ButtonCenter, ButtonCenter,
		TSet<FKey>({EKeys::LeftMouseButton}),
		EKeys::LeftMouseButton, 0,
		FModifierKeysState()
	);
	SlateApp.ProcessMouseButtonDownEvent(nullptr, MouseDownEvent);

	// Mouse Up
	FPointerEvent MouseUpEvent(
		0, ButtonCenter, ButtonCenter,
		TSet<FKey>(),
		EKeys::LeftMouseButton, 0,
		FModifierKeysState()
	);
	SlateApp.ProcessMouseButtonUpEvent(MouseUpEvent);

	UE_LOG(LogTemp, Log, TEXT("[AgentBridge L3] Clicked button '%s' at (%.0f, %.0f)"),
		*ButtonLabel, ButtonCenter.X, ButtonCenter.Y);

	Result.bUIIdleAfter = WaitForUIIdle(TimeoutSeconds);
	Result.bExecuted = true;
	Result.DurationSeconds = FPlatformTime::Seconds() - StartTime;
	return Result;
}

// ============================================================
// 操作 2: TypeInDetailPanelField
// ============================================================

FUIOperationResult FAutomationDriverAdapter::TypeInDetailPanelField(
	const FString& ActorPath,
	const FString& PropertyPath,
	const FString& Value,
	float TimeoutSeconds)
{
	FUIOperationResult Result;
	double StartTime = FPlatformTime::Seconds();

	if (!IsAvailable())
	{
		Result.FailureReason = TEXT("Automation Driver not available");
		return Result;
	}

	if (!SelectActorAndOpenDetails(ActorPath))
	{
		Result.FailureReason = FString::Printf(TEXT("Failed to select actor: %s"), *ActorPath);
		return Result;
	}

	// 按 PropertyPath 最后一段作为标签查找
	FString PropertyLabel = PropertyPath;
	int32 DotIndex;
	if (PropertyPath.FindLastChar('.', DotIndex))
	{
		PropertyLabel = PropertyPath.Mid(DotIndex + 1);
	}

	// 在活跃窗口中查找属性标签
	TSharedPtr<SWidget> PropertyLabelWidget = nullptr;
	TSharedPtr<SWindow> ActiveWindow = FSlateApplication::Get().GetActiveTopLevelWindow();
	if (ActiveWindow.IsValid())
	{
		PropertyLabelWidget = FindWidgetByLabel(ActiveWindow, PropertyLabel);
	}

	if (!PropertyLabelWidget.IsValid())
	{
		Result.FailureReason = FString::Printf(TEXT("Property not found: '%s'"), *PropertyPath);
		return Result;
	}

	// 模拟键盘输入：点击获焦 → Ctrl+A 全选 → 输入新值 → Enter
	FSlateApplication& SlateApp = FSlateApplication::Get();

	FGeometry LabelGeometry = PropertyLabelWidget->GetCachedGeometry();
	FVector2D FieldPos = LabelGeometry.GetAbsolutePosition();
	FieldPos.X += LabelGeometry.GetAbsoluteSize().X + 50.0f; // 值输入框在标签右侧

	// 点击输入框
	FPointerEvent ClickEvent(
		0, FieldPos, FieldPos,
		TSet<FKey>({EKeys::LeftMouseButton}),
		EKeys::LeftMouseButton, 0,
		FModifierKeysState()
	);
	SlateApp.ProcessMouseButtonDownEvent(nullptr, ClickEvent);
	SlateApp.ProcessMouseButtonUpEvent(ClickEvent);

	// Ctrl+A 全选
	// FModifierKeysState 需要 9 个参数（左右 Shift/Ctrl/Alt/Cmd + CapsLock）
	FKeyEvent SelectAllEvent(
		EKeys::A,
		FModifierKeysState(false, false, true, false, false, false, false, false, false),
		0, false, 0, 0);
	SlateApp.ProcessKeyDownEvent(SelectAllEvent);
	SlateApp.ProcessKeyUpEvent(SelectAllEvent);

	// 逐字符输入
	for (TCHAR Char : Value)
	{
		FCharacterEvent CharEvent(Char, FModifierKeysState(), 0, false);
		SlateApp.ProcessKeyCharEvent(CharEvent);
	}

	// Enter 确认
	FKeyEvent EnterEvent(EKeys::Enter, FModifierKeysState(), 0, false, 0, 0);
	SlateApp.ProcessKeyDownEvent(EnterEvent);
	SlateApp.ProcessKeyUpEvent(EnterEvent);

	UE_LOG(LogTemp, Log, TEXT("[AgentBridge L3] Typed '%s' into '%s'"), *Value, *PropertyPath);

	Result.bUIIdleAfter = WaitForUIIdle(TimeoutSeconds);
	Result.bExecuted = true;
	Result.DurationSeconds = FPlatformTime::Seconds() - StartTime;
	return Result;
}

// ============================================================
// 操作 3: DragAssetToViewport
// ============================================================

FUIOperationResult FAutomationDriverAdapter::DragAssetToViewport(
	const FString& AssetPath,
	const FVector& DropLocation,
	float TimeoutSeconds)
{
	FUIOperationResult Result;
	double StartTime = FPlatformTime::Seconds();

	if (!IsAvailable())
	{
		Result.FailureReason = TEXT("Automation Driver not available");
		return Result;
	}

	// 1. 在 Content Browser 中导航并选中资产
	TSharedPtr<SWidget> AssetWidget = FindAssetInContentBrowser(AssetPath);
	if (!AssetWidget.IsValid())
	{
		Result.FailureReason = FString::Printf(TEXT("Asset not found in Content Browser: %s"), *AssetPath);
		return Result;
	}

	// 2. 世界坐标 → 屏幕坐标
	FVector2D ScreenPos;
	if (!WorldToScreen(DropLocation, ScreenPos))
	{
		Result.FailureReason = TEXT("Drop location is outside viewport");
		return Result;
	}

	// 3. 模拟拖拽（分步移动触发 DragDetected）
	FSlateApplication& SlateApp = FSlateApplication::Get();
	FGeometry AssetGeometry = AssetWidget->GetCachedGeometry();
	FVector2D DragStart = AssetGeometry.GetAbsolutePosition()
		+ AssetGeometry.GetAbsoluteSize() * 0.5f;

	// Mouse Down
	FPointerEvent DragStartEvent(
		0, DragStart, DragStart,
		TSet<FKey>({EKeys::LeftMouseButton}),
		EKeys::LeftMouseButton, 0,
		FModifierKeysState()
	);
	SlateApp.ProcessMouseButtonDownEvent(nullptr, DragStartEvent);

	// 分步移动（10 步，触发拖拽检测）
	int32 Steps = 10;
	for (int32 i = 1; i <= Steps; ++i)
	{
		float Alpha = (float)i / (float)Steps;
		FVector2D Pos = FMath::Lerp(DragStart, ScreenPos, Alpha);

		FPointerEvent MoveEvent(
			0, Pos, Pos - FVector2D(1, 0),
			TSet<FKey>({EKeys::LeftMouseButton}),
			EKeys::Invalid, 0,
			FModifierKeysState()
		);
		SlateApp.ProcessMouseMoveEvent(MoveEvent);
		FPlatformProcess::Sleep(0.02f);
	}

	// Mouse Up（释放拖拽）
	FPointerEvent DropEvent(
		0, ScreenPos, ScreenPos,
		TSet<FKey>(),
		EKeys::LeftMouseButton, 0,
		FModifierKeysState()
	);
	SlateApp.ProcessMouseButtonUpEvent(DropEvent);

	UE_LOG(LogTemp, Log,
		TEXT("[AgentBridge L3] Dragged '%s' to viewport → world (%.1f, %.1f, %.1f)"),
		*AssetPath, DropLocation.X, DropLocation.Y, DropLocation.Z);

	Result.bUIIdleAfter = WaitForUIIdle(TimeoutSeconds);
	Result.bExecuted = true;
	Result.DurationSeconds = FPlatformTime::Seconds() - StartTime;
	return Result;
}

// ============================================================
// WaitForUIIdle
// ============================================================

bool FAutomationDriverAdapter::WaitForUIIdle(float TimeoutSeconds)
{
	double StartTime = FPlatformTime::Seconds();
	double EndTime = StartTime + TimeoutSeconds;

	while (FPlatformTime::Seconds() < EndTime)
	{
		FSlateApplication& SlateApp = FSlateApplication::Get();
		SlateApp.Tick();

		if (!SlateApp.IsDragDropping())
		{
			FPlatformProcess::Sleep(0.1f);
			SlateApp.Tick();
			if (!SlateApp.IsDragDropping())
			{
				return true;
			}
		}

		FPlatformProcess::Sleep(0.05f);
	}

	UE_LOG(LogTemp, Warning, TEXT("[AgentBridge L3] UI idle timeout after %.1fs"), TimeoutSeconds);
	return false;
}

// ============================================================
// Widget 查找辅助
// ============================================================

TSharedPtr<SWidget> FAutomationDriverAdapter::FindWidgetByLabel(
	TSharedPtr<SWidget> RootWidget,
	const FString& Label)
{
	if (!RootWidget.IsValid()) return nullptr;

	// 检查 STextBlock 文本匹配
	if (RootWidget->GetType() == FName(TEXT("STextBlock")))
	{
		TSharedPtr<STextBlock> TextBlock = StaticCastSharedPtr<STextBlock>(RootWidget);
		if (TextBlock.IsValid())
		{
			FString WidgetText = TextBlock->GetText().ToString();
			if (WidgetText.Equals(Label, ESearchCase::IgnoreCase))
			{
				return RootWidget;
			}
		}
	}

	// 检查 SButton（按钮内部可能包含文本子 Widget）
	if (RootWidget->GetType() == FName(TEXT("SButton")))
	{
		FChildren* BtnChildren = RootWidget->GetChildren();
		for (int32 i = 0; BtnChildren && i < BtnChildren->Num(); ++i)
		{
			TSharedRef<SWidget> Child = BtnChildren->GetChildAt(i);
			TSharedPtr<SWidget> Found = FindWidgetByLabel(Child, Label);
			if (Found.IsValid()) return RootWidget; // 返回按钮本身
		}
	}

	// 递归搜索子 Widget
	FChildren* Children = RootWidget->GetChildren();
	if (Children)
	{
		for (int32 i = 0; i < Children->Num(); ++i)
		{
			TSharedRef<SWidget> Child = Children->GetChildAt(i);
			TSharedPtr<SWidget> Found = FindWidgetByLabel(Child, Label);
			if (Found.IsValid()) return Found;
		}
	}

	return nullptr;
}

TSharedPtr<SWidget> FAutomationDriverAdapter::FindAssetInContentBrowser(const FString& AssetPath)
{
	if (!GEditor) return nullptr;

	// 导航 Content Browser 到目标资产
	FString Cmd = FString::Printf(TEXT("ContentBrowser.FocusAsset %s"), *AssetPath);
	GEditor->Exec(GEditor->GetEditorWorldContext().World(), *Cmd);

	FPlatformProcess::Sleep(0.5f);
	FSlateApplication::Get().Tick();

	UE_LOG(LogTemp, Log, TEXT("[AgentBridge L3] Content Browser navigated to: %s"), *AssetPath);

	// 返回当前焦点 Widget 作为拖拽起点
	return FSlateApplication::Get().GetKeyboardFocusedWidget();
}

// ============================================================
// 世界坐标 → 屏幕坐标
// ============================================================

bool FAutomationDriverAdapter::WorldToScreen(const FVector& WorldLocation, FVector2D& OutScreenPos)
{
	if (!GEditor) return false;

	FViewport* ActiveViewport = GEditor->GetActiveViewport();
	if (!ActiveViewport) return false;

	// 查找活跃 Viewport Client
	FLevelEditorViewportClient* ViewportClient = nullptr;
	for (FLevelEditorViewportClient* Client : GEditor->GetLevelViewportClients())
	{
		if (Client && Client->Viewport == ActiveViewport)
		{
			ViewportClient = Client;
			break;
		}
	}
	if (!ViewportClient) return false;

	// 构建场景视图
	FSceneViewFamilyContext ViewFamily(FSceneViewFamily::ConstructionValues(
		ActiveViewport,
		ViewportClient->GetScene(),
		ViewportClient->EngineShowFlags
	));

	FSceneView* View = ViewportClient->CalcSceneView(&ViewFamily);
	if (!View) return false;

	// 投影
	return FSceneView::ProjectWorldToScreen(
		WorldLocation,
		View->UnconstrainedViewRect,
		View->ViewMatrices.GetViewProjectionMatrix(),
		OutScreenPos
	);
}
