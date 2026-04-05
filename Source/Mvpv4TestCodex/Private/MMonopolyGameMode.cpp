#include "MMonopolyGameMode.h"

#include "Blueprint/UserWidget.h"
#include "Camera/CameraActor.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/SkyAtmosphereComponent.h"
#include "Components/SkyLightComponent.h"
#include "Engine/DirectionalLight.h"
#include "Engine/SkyLight.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "MBoardManager.h"
#include "MDice.h"
#include "MGameHUDWidget.h"
#include "MMonopolyGameState.h"
#include "MMonopolyPlayerController.h"
#include "MMonopolyPlayerState.h"
#include "MPopupWidget.h"
#include "MPlayerPawn.h"
#include "MTile.h"

namespace MonopolyGameMode
{
	static constexpr int32 StartTileIndex = 0;
	static constexpr int32 JailTileIndex = 7;
	static constexpr int32 MaxJailAttempts = 3;
}

AMMonopolyGameMode::AMMonopolyGameMode()
{
	GameStateClass = AMMonopolyGameState::StaticClass();
	PlayerStateClass = AMMonopolyPlayerState::StaticClass();
	PlayerControllerClass = AMMonopolyPlayerController::StaticClass();
	DefaultPawnClass = nullptr;

	BoardManagerClass = AMBoardManager::StaticClass();
	PlayerPawnClass = AMPlayerPawn::StaticClass();
	DiceClass = AMDice::StaticClass();
	HUDWidgetClass = UMGameHUDWidget::StaticClass();
	PopupWidgetClass = UMPopupWidget::StaticClass();
}

void AMMonopolyGameMode::BeginPlay()
{
	Super::BeginPlay();
	UE_LOG(LogTemp, Log, TEXT("[Phase8] MonopolyGameMode BeginPlay started."));

	AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState();
	if (MonopolyGameState == nullptr)
	{
		return;
	}

	MonopolyGameState->InitializeTileData();
	MonopolyGameState->GamePhase = EMGamePhase::Setup;
	MonopolyGameState->SetTurnNumber(1);
	MonopolyGameState->ConsecutiveDoublesCount = 0;

	InitializeMonopolyPlayers(FMath::Clamp(DefaultPlayerCount, 2, 4));
	EnsureRuntimeActors();
	SpawnPlayerPawns();
	RefreshTileOwnershipVisuals();
	CreateHUDWidget();
	UE_LOG(LogTemp, Log, TEXT("[Phase8] Runtime initialized. Players=%d Tiles=%d"), MonopolyGameState->MonopolyPlayers.Num(), MonopolyGameState->TileDataArray.Num());

	MonopolyGameState->GamePhase = EMGamePhase::InProgress;
	MonopolyGameState->SetCurrentPlayerIndex(0);
	SetTurnState(EMTurnState::WaitForRoll);
	StartTurn();
}

AMMonopolyGameState* AMMonopolyGameMode::GetMonopolyGameState() const
{
	return GetGameState<AMMonopolyGameState>();
}

AMMonopolyPlayerState* AMMonopolyGameMode::GetMonopolyPlayerState(const int32 PlayerIndex) const
{
	if (const AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState())
	{
		return MonopolyGameState->GetMonopolyPlayer(PlayerIndex);
	}

	return nullptr;
}

AMPlayerPawn* AMMonopolyGameMode::GetCurrentPlayerPawn() const
{
	const AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState();
	return MonopolyGameState != nullptr && PlayerPawns.IsValidIndex(MonopolyGameState->CurrentPlayerIndex) ? PlayerPawns[MonopolyGameState->CurrentPlayerIndex] : nullptr;
}

FLinearColor AMMonopolyGameMode::GetPlayerColor(const int32 PlayerIndex) const
{
	static const TArray<FLinearColor> PlayerColors =
	{
		FLinearColor(0.95f, 0.2f, 0.2f),
		FLinearColor(0.2f, 0.55f, 1.0f),
		FLinearColor(0.18f, 0.8f, 0.35f),
		FLinearColor(1.0f, 0.78f, 0.1f)
	};

	return PlayerColors.IsValidIndex(PlayerIndex) ? PlayerColors[PlayerIndex] : FLinearColor::White;
}

void AMMonopolyGameMode::EnsureRuntimeActors()
{
	UWorld* World = GetWorld();
	AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState();
	if (World == nullptr || MonopolyGameState == nullptr)
	{
		return;
	}

	if (BoardManager == nullptr)
	{
		for (TActorIterator<AMBoardManager> It(World); It; ++It)
		{
			BoardManager = *It;
			break;
		}
	}

	if (BoardManager == nullptr)
	{
		BoardManager = World->SpawnActor<AMBoardManager>(BoardManagerClass != nullptr ? BoardManagerClass.Get() : AMBoardManager::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator);
	}

	if (BoardManager != nullptr && BoardManager->TileActors.Num() != MonopolyGameState->TileDataArray.Num())
	{
		BoardManager->SpawnBoard(MonopolyGameState->TileDataArray);
	}

	if (DiceActor == nullptr)
	{
		for (TActorIterator<AMDice> It(World); It; ++It)
		{
			DiceActor = *It;
			break;
		}
	}

	if (DiceActor == nullptr)
	{
		DiceActor = World->SpawnActor<AMDice>(DiceClass != nullptr ? DiceClass.Get() : AMDice::StaticClass(), FVector(0.0f, 0.0f, 180.0f), FRotator::ZeroRotator);
	}

	if (BoardCameraActor == nullptr)
	{
		for (TActorIterator<ACameraActor> It(World); It; ++It)
		{
			BoardCameraActor = *It;
			break;
		}
	}

	if (BoardCameraActor == nullptr)
	{
		BoardCameraActor = World->SpawnActor<ACameraActor>(ACameraActor::StaticClass(), FVector(0.0f, 0.0f, 4200.0f), FRotator(-90.0f, 0.0f, 0.0f));
	}

	if (APlayerController* LocalController = UGameplayStatics::GetPlayerController(this, 0))
	{
		if (BoardCameraActor != nullptr)
		{
			LocalController->SetViewTarget(BoardCameraActor);
		}
	}

	// 场景光源：如果地图中没有方向光，自动生成基础光照环境
	bool bHasDirectionalLight = false;
	for (TActorIterator<ADirectionalLight> It(World); It; ++It)
	{
		bHasDirectionalLight = true;
		break;
	}

	if (!bHasDirectionalLight)
	{
		// 太阳光（方向光）
		ADirectionalLight* SunLight = World->SpawnActor<ADirectionalLight>(ADirectionalLight::StaticClass(), FVector::ZeroVector, FRotator(-50.0f, -30.0f, 0.0f));
		if (SunLight != nullptr)
		{
			SunLight->GetLightComponent()->SetIntensity(3.14f);
			SunLight->GetLightComponent()->SetLightColor(FLinearColor(1.0f, 0.95f, 0.85f));
			UE_LOG(LogTemp, Log, TEXT("[Phase8] DirectionalLight spawned (auto)."));
		}

		// 天空光
		ASkyLight* Sky = World->SpawnActor<ASkyLight>(ASkyLight::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator);
		if (Sky != nullptr)
		{
			Sky->GetLightComponent()->SetIntensity(1.0f);
			Sky->GetLightComponent()->SetMobility(EComponentMobility::Movable);
			Sky->GetLightComponent()->bRealTimeCapture = true;
			UE_LOG(LogTemp, Log, TEXT("[Phase8] SkyLight spawned (auto)."));
		}

		// 大气
		AActor* AtmosphereActor = World->SpawnActor<AActor>(AActor::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator);
		if (AtmosphereActor != nullptr)
		{
			USkyAtmosphereComponent* AtmosphereComp = NewObject<USkyAtmosphereComponent>(AtmosphereActor, TEXT("SkyAtmosphere"));
			AtmosphereComp->RegisterComponent();
			AtmosphereActor->AddOwnedComponent(AtmosphereComp);
			UE_LOG(LogTemp, Log, TEXT("[Phase8] SkyAtmosphere spawned (auto)."));
		}
	}

	UE_LOG(LogTemp, Log, TEXT("[Phase8] Runtime actors ready. HasBoard=%s HasDice=%s HasCamera=%s"), BoardManager != nullptr ? TEXT("true") : TEXT("false"), DiceActor != nullptr ? TEXT("true") : TEXT("false"), BoardCameraActor != nullptr ? TEXT("true") : TEXT("false"));
}

void AMMonopolyGameMode::InitializeMonopolyPlayers(const int32 PlayerCount)
{
	AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState();
	UWorld* World = GetWorld();
	if (MonopolyGameState == nullptr || World == nullptr)
	{
		return;
	}

	MonopolyGameState->MonopolyPlayers.Reset();

	TArray<AMMonopolyPlayerState*> PlayersToConfigure;
	if (APlayerController* LocalController = UGameplayStatics::GetPlayerController(this, 0))
	{
		if (AMMonopolyPlayerState* LocalPlayerState = LocalController->GetPlayerState<AMMonopolyPlayerState>())
		{
			PlayersToConfigure.Add(LocalPlayerState);
		}
	}

	while (PlayersToConfigure.Num() < PlayerCount)
	{
		if (AMMonopolyPlayerState* ExtraPlayerState = World->SpawnActor<AMMonopolyPlayerState>(AMMonopolyPlayerState::StaticClass()))
		{
			PlayersToConfigure.Add(ExtraPlayerState);
		}
	}

	for (int32 PlayerIndex = 0; PlayerIndex < PlayersToConfigure.Num(); ++PlayerIndex)
	{
		AMMonopolyPlayerState* PlayerState = PlayersToConfigure[PlayerIndex];
		if (PlayerState == nullptr)
		{
			continue;
		}

		PlayerState->Money = 1500;
		PlayerState->CurrentTileIndex = MonopolyGameMode::StartTileIndex;
		PlayerState->OwnedTileIndices.Reset();
		PlayerState->bIsInJail = false;
		PlayerState->JailTurnsRemaining = 0;
		PlayerState->bIsBankrupt = false;
		PlayerState->PlayerColor = GetPlayerColor(PlayerIndex);
		PlayerState->PlayerDisplayName = FString::Printf(TEXT("玩家%d"), PlayerIndex + 1);
		PlayerState->SetPlayerName(PlayerState->PlayerDisplayName);
		MonopolyGameState->RegisterMonopolyPlayer(PlayerState);
	}

	UE_LOG(LogTemp, Log, TEXT("[Phase8] Monopoly players configured: %d"), MonopolyGameState->MonopolyPlayers.Num());
}

void AMMonopolyGameMode::SpawnPlayerPawns()
{
	UWorld* World = GetWorld();
	AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState();
	if (World == nullptr || MonopolyGameState == nullptr || BoardManager == nullptr)
	{
		return;
	}

	for (AMPlayerPawn* ExistingPawn : PlayerPawns)
	{
		if (ExistingPawn != nullptr)
		{
			ExistingPawn->Destroy();
		}
	}

	PlayerPawns.Reset();

	for (int32 PlayerIndex = 0; PlayerIndex < MonopolyGameState->MonopolyPlayers.Num(); ++PlayerIndex)
	{
		AMMonopolyPlayerState* PlayerState = MonopolyGameState->MonopolyPlayers[PlayerIndex];
		if (PlayerState == nullptr)
		{
			continue;
		}

		AMPlayerPawn* Pawn = World->SpawnActor<AMPlayerPawn>(PlayerPawnClass != nullptr ? PlayerPawnClass.Get() : AMPlayerPawn::StaticClass(), BoardManager->GetPlayerStandLocation(PlayerState->CurrentTileIndex, PlayerIndex), FRotator::ZeroRotator);
		if (Pawn == nullptr)
		{
			continue;
		}

		Pawn->PlayerIndex = PlayerIndex;
		Pawn->SetPawnColor(PlayerState->PlayerColor);
		Pawn->SetLabelText(FString::Printf(TEXT("P%d"), PlayerIndex + 1));
		Pawn->MoveToTile(BoardManager->GetPlayerStandLocation(PlayerState->CurrentTileIndex, PlayerIndex), PlayerState->CurrentTileIndex);
		PlayerPawns.Add(Pawn);
	}

	UE_LOG(LogTemp, Log, TEXT("[Phase8] Player pawns spawned: %d"), PlayerPawns.Num());
}

void AMMonopolyGameMode::MovePlayerPawnToTile(const int32 PlayerIndex, const int32 TileIndex)
{
	AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState();
	if (BoardManager == nullptr || MonopolyGameState == nullptr || !PlayerPawns.IsValidIndex(PlayerIndex))
	{
		return;
	}

	AMMonopolyPlayerState* PlayerState = MonopolyGameState->GetMonopolyPlayer(PlayerIndex);
	AMPlayerPawn* Pawn = PlayerPawns[PlayerIndex];
	if (PlayerState == nullptr || Pawn == nullptr)
	{
		return;
	}

	PlayerState->CurrentTileIndex = TileIndex;
	Pawn->MoveToTile(BoardManager->GetPlayerStandLocation(TileIndex, PlayerIndex), TileIndex);
	MonopolyGameState->OnPawnMoved.Broadcast(PlayerState, TileIndex);

	for (int32 Index = 0; Index < MonopolyGameState->TileDataArray.Num(); ++Index)
	{
		BoardManager->HighlightTile(Index, Index == TileIndex);
	}
}

void AMMonopolyGameMode::RefreshTileOwnershipVisuals()
{
	AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState();
	if (BoardManager == nullptr || MonopolyGameState == nullptr)
	{
		return;
	}

	for (const FMTileData& TileData : MonopolyGameState->TileDataArray)
	{
		AMTile* TileActor = BoardManager->GetTileActor(TileData.TileIndex);
		if (TileActor == nullptr)
		{
			continue;
		}

		TileActor->InitTile(TileData);
		if (TileData.OwnerPlayerIndex != INDEX_NONE)
		{
			if (AMMonopolyPlayerState* OwnerPlayerState = GetMonopolyPlayerState(TileData.OwnerPlayerIndex))
			{
				TileActor->SetOwnerColor(OwnerPlayerState->PlayerColor);
			}
		}
	}
}

void AMMonopolyGameMode::CreateHUDWidget()
{
	if (ActiveHUDWidget != nullptr)
	{
		return;
	}

	APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
	if (PC == nullptr)
	{
		return;
	}

	ActiveHUDWidget = CreateWidget<UMGameHUDWidget>(PC, HUDWidgetClass != nullptr ? HUDWidgetClass.Get() : UMGameHUDWidget::StaticClass());
	if (ActiveHUDWidget != nullptr)
	{
		ActiveHUDWidget->AddToViewport(1000);
		ActiveHUDWidget->SetVisibility(ESlateVisibility::Visible);
		ActiveHUDWidget->BindToGame(this, GetMonopolyGameState());

		// HUD 加入视口后立即把输入焦点切回 HUD，避免鼠标可见但不可点击。
		FInputModeGameAndUI InputMode;
		InputMode.SetWidgetToFocus(ActiveHUDWidget->TakeWidget());
		InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
		InputMode.SetHideCursorDuringCapture(false);
		PC->SetInputMode(InputMode);
		PC->bShowMouseCursor = true;
		PC->bEnableClickEvents = true;
		PC->bEnableMouseOverEvents = true;

		UE_LOG(LogTemp, Log, TEXT("[Phase8] HUD widget created: %s Owner=%s"), *ActiveHUDWidget->GetClass()->GetName(), *PC->GetClass()->GetName());
		UE_LOG(LogTemp, Log, TEXT("[Phase8] HUD input mode refreshed. Click=%s Hover=%s Cursor=%s"),
			PC->bEnableClickEvents ? TEXT("true") : TEXT("false"),
			PC->bEnableMouseOverEvents ? TEXT("true") : TEXT("false"),
			PC->bShowMouseCursor ? TEXT("true") : TEXT("false"));
	}
}

void AMMonopolyGameMode::StartTurn()
{
	AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState();
	AMMonopolyPlayerState* CurrentPlayerState = GetMonopolyPlayerState(MonopolyGameState != nullptr ? MonopolyGameState->CurrentPlayerIndex : INDEX_NONE);
	if (MonopolyGameState == nullptr || CurrentPlayerState == nullptr)
	{
		return;
	}

	if (CurrentPlayerState->bIsBankrupt)
	{
		EndTurn();
		return;
	}

	MonopolyGameState->OnActivePlayerChanged.Broadcast(MonopolyGameState->CurrentPlayerIndex, CurrentPlayerState);
	SetTurnState(EMTurnState::WaitForRoll);
	UE_LOG(LogTemp, Log, TEXT("[Phase8] StartTurn -> PlayerIndex=%d Name=%s InJail=%s"), MonopolyGameState->CurrentPlayerIndex, *CurrentPlayerState->GetResolvedDisplayName(), CurrentPlayerState->bIsInJail ? TEXT("true") : TEXT("false"));

	if (CurrentPlayerState->bIsInJail)
	{
		ShowPopup(TEXT("监狱回合"), FString::Printf(TEXT("%s 仍在监狱中，还剩 %d 次双骰机会。"), *CurrentPlayerState->GetResolvedDisplayName(), CurrentPlayerState->JailTurnsRemaining), { TEXT("继续") },
			[this](int32)
			{
				SetTurnState(EMTurnState::WaitForRoll);
			});
	}
}

void AMMonopolyGameMode::OnPlayerRequestRoll()
{
	AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState();
	AMMonopolyPlayerState* CurrentPlayerState = GetMonopolyPlayerState(MonopolyGameState != nullptr ? MonopolyGameState->CurrentPlayerIndex : INDEX_NONE);
	if (MonopolyGameState == nullptr || CurrentPlayerState == nullptr || MonopolyGameState->TurnState != EMTurnState::WaitForRoll)
	{
		return;
	}

	if (CurrentPlayerState->bIsBankrupt)
	{
		EndTurn();
		return;
	}

	if (CurrentPlayerState->bIsInJail)
	{
		HandleJailTurn();
		return;
	}

	RollAndMoveCurrentPlayer();
}

void AMMonopolyGameMode::RequestEndTurnFromUI()
{
	if (GetMonopolyGameState() == nullptr || GetMonopolyGameState()->TurnState == EMTurnState::GameOver)
	{
		return;
	}

	EndTurn();
}

void AMMonopolyGameMode::RequestPayBailFromUI()
{
	AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState();
	const int32 CurrentPlayerIndex = MonopolyGameState != nullptr ? MonopolyGameState->CurrentPlayerIndex : INDEX_NONE;
	AMMonopolyPlayerState* CurrentPlayerState = GetMonopolyPlayerState(CurrentPlayerIndex);
	if (MonopolyGameState == nullptr || CurrentPlayerState == nullptr || !CurrentPlayerState->bIsInJail)
	{
		return;
	}

	PayBail(CurrentPlayerIndex, true);
}

void AMMonopolyGameMode::SetTurnState(const EMTurnState NewTurnState)
{
	if (AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState())
	{
		MonopolyGameState->SetTurnState(NewTurnState);
	}
}

void AMMonopolyGameMode::RollAndMoveCurrentPlayer()
{
	AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState();
	AMMonopolyPlayerState* CurrentPlayerState = GetMonopolyPlayerState(MonopolyGameState != nullptr ? MonopolyGameState->CurrentPlayerIndex : INDEX_NONE);
	if (MonopolyGameState == nullptr || CurrentPlayerState == nullptr || DiceActor == nullptr)
	{
		return;
	}

	SetTurnState(EMTurnState::RollingDice);
	DiceActor->PlayRollAnimation();
	LastDiceResult = DiceActor->RollDice();

	if (LastDiceResult.bIsDouble)
	{
		MonopolyGameState->ConsecutiveDoublesCount += 1;
	}
	else
	{
		MonopolyGameState->ConsecutiveDoublesCount = 0;
	}

	if (MonopolyGameState->ConsecutiveDoublesCount >= 3)
	{
		MonopolyGameState->ConsecutiveDoublesCount = 0;
		bPendingExtraTurn = false;
		SendToJail(MonopolyGameState->CurrentPlayerIndex);
		return;
	}

	const int32 TileCount = MonopolyGameState->TileDataArray.Num();
	const int32 OldTileIndex = CurrentPlayerState->CurrentTileIndex;
	const int32 RawTargetIndex = OldTileIndex + LastDiceResult.Total;
	const int32 NewTileIndex = TileCount > 0 ? RawTargetIndex % TileCount : OldTileIndex;

	if (RawTargetIndex >= TileCount)
	{
		CurrentPlayerState->AddMoney(PassStartReward);
		MonopolyGameState->OnMoneyChanged.Broadcast(CurrentPlayerState, CurrentPlayerState->Money);
	}

	bPendingExtraTurn = LastDiceResult.bIsDouble;
	SetTurnState(EMTurnState::MovingPawn);
	MovePlayerPawnToTile(MonopolyGameState->CurrentPlayerIndex, NewTileIndex);
	ResolveCurrentTileEvent();
}

void AMMonopolyGameMode::HandleJailTurn()
{
	AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState();
	AMMonopolyPlayerState* CurrentPlayerState = GetMonopolyPlayerState(MonopolyGameState != nullptr ? MonopolyGameState->CurrentPlayerIndex : INDEX_NONE);
	if (MonopolyGameState == nullptr || CurrentPlayerState == nullptr || DiceActor == nullptr)
	{
		return;
	}

	SetTurnState(EMTurnState::RollingDice);
	LastDiceResult = DiceActor->RollDice();
	if (LastDiceResult.bIsDouble)
	{
		CurrentPlayerState->bIsInJail = false;
		CurrentPlayerState->JailTurnsRemaining = 0;
		ShowPopup(TEXT("出狱成功"), FString::Printf(TEXT("%s 掷出双骰，立即出狱并继续移动。"), *CurrentPlayerState->GetResolvedDisplayName()), { TEXT("继续") },
			[this](int32)
			{
				RollAndMoveCurrentPlayer();
			});
		return;
	}

	CurrentPlayerState->JailTurnsRemaining = FMath::Max(0, CurrentPlayerState->JailTurnsRemaining - 1);
	if (CurrentPlayerState->JailTurnsRemaining == 0)
	{
		ForcePayBail(MonopolyGameState->CurrentPlayerIndex);
		return;
	}

	ShowPopup(TEXT("监狱"), FString::Printf(TEXT("%s 没有掷出双骰，还剩 %d 次机会。"), *CurrentPlayerState->GetResolvedDisplayName(), CurrentPlayerState->JailTurnsRemaining), { TEXT("结束回合") },
		[this](int32)
		{
			bPendingExtraTurn = false;
			EndTurn();
		});
}

void AMMonopolyGameMode::ResolveCurrentTileEvent()
{
	AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState();
	const int32 CurrentPlayerIndex = MonopolyGameState != nullptr ? MonopolyGameState->CurrentPlayerIndex : INDEX_NONE;
	AMMonopolyPlayerState* CurrentPlayerState = GetMonopolyPlayerState(CurrentPlayerIndex);
	if (MonopolyGameState == nullptr || CurrentPlayerState == nullptr)
	{
		return;
	}

	const FMTileData* TileData = MonopolyGameState->GetTileData(CurrentPlayerState->CurrentTileIndex);
	if (TileData == nullptr)
	{
		ProcessPostEvent();
		return;
	}

	SetTurnState(EMTurnState::ResolvingTileEvent);

	switch (TileData->TileType)
	{
	case EMTileType::Property:
		ResolvePropertyTile(CurrentPlayerState, CurrentPlayerIndex, *TileData);
		break;
	case EMTileType::Chance:
		ResolveChanceTile(CurrentPlayerState);
		break;
	case EMTileType::CommunityChest:
		ResolveCommunityChestTile(CurrentPlayerState);
		break;
	case EMTileType::Tax:
		ResolveTaxTile(CurrentPlayerState, *TileData);
		break;
	case EMTileType::GoToJail:
		SendToJail(CurrentPlayerIndex);
		break;
	case EMTileType::FreeParking:
		ShowPopup(TEXT("免费停车"), FString::Printf(TEXT("%s 在免费停车区短暂停留。"), *CurrentPlayerState->GetResolvedDisplayName()), { TEXT("继续") },
			[this](int32)
			{
				ProcessPostEvent();
			});
		break;
	case EMTileType::JailVisit:
		ShowPopup(TEXT("探访监狱"), FString::Printf(TEXT("%s 只是路过监狱，没有被关进去。"), *CurrentPlayerState->GetResolvedDisplayName()), { TEXT("继续") },
			[this](int32)
			{
				ProcessPostEvent();
			});
		break;
	case EMTileType::Start:
		ShowPopup(TEXT("起点"), FString::Printf(TEXT("%s 到达起点。"), *CurrentPlayerState->GetResolvedDisplayName()), { TEXT("继续") },
			[this](int32)
			{
				ProcessPostEvent();
			});
		break;
	default:
		ProcessPostEvent();
		break;
	}
}

void AMMonopolyGameMode::ResolvePropertyTile(AMMonopolyPlayerState* CurrentPlayerState, const int32 CurrentPlayerIndex, const FMTileData& TileData)
{
	if (TileData.OwnerPlayerIndex == INDEX_NONE)
	{
		if (!CurrentPlayerState->CanAfford(TileData.Cost))
		{
			ShowPopup(TEXT("地产"), FString::Printf(TEXT("%s 到达 %s，但资金不足，无法购买。"), *CurrentPlayerState->GetResolvedDisplayName(), *TileData.TileName), { TEXT("继续") },
				[this](int32)
				{
					ProcessPostEvent();
				});
			return;
		}

		ShowPopup(TEXT("购买地产"), FString::Printf(TEXT("%s 到达 %s。\n价格：%d\n租金：%d"), *CurrentPlayerState->GetResolvedDisplayName(), *TileData.TileName, TileData.Cost, TileData.Rent), { TEXT("购买"), TEXT("跳过") },
			[this, CurrentPlayerIndex, TileIndex = TileData.TileIndex](const int32 ButtonIndex)
			{
				if (ButtonIndex == 0)
				{
					TryPurchaseProperty(CurrentPlayerIndex, TileIndex);
				}
				ProcessPostEvent();
			});
		return;
	}

	if (TileData.OwnerPlayerIndex == CurrentPlayerIndex)
	{
		ShowPopup(TEXT("我的地产"), FString::Printf(TEXT("%s 回到了自己的地产 %s。"), *CurrentPlayerState->GetResolvedDisplayName(), *TileData.TileName), { TEXT("继续") },
			[this](int32)
			{
				ProcessPostEvent();
			});
		return;
	}

	CollectRent(CurrentPlayerIndex, TileData.OwnerPlayerIndex, TileData.TileIndex);
	if (CurrentPlayerState->bIsBankrupt)
	{
		ProcessPostEvent();
		return;
	}

	const int32 RentAmount = CalculateEffectiveRent(TileData);
	ShowPopup(TEXT("支付租金"), FString::Printf(TEXT("%s 支付了 %d 租金。"), *CurrentPlayerState->GetResolvedDisplayName(), RentAmount), { TEXT("继续") },
		[this](int32)
		{
			ProcessPostEvent();
		});
}

void AMMonopolyGameMode::ResolveChanceTile(AMMonopolyPlayerState* CurrentPlayerState)
{
	AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState();
	if (MonopolyGameState == nullptr || CurrentPlayerState == nullptr)
	{
		return;
	}

	const int32 ChanceOutcome = FMath::RandRange(0, 2);
	FString Message;
	if (ChanceOutcome == 0)
	{
		CurrentPlayerState->AddMoney(120);
		MonopolyGameState->OnMoneyChanged.Broadcast(CurrentPlayerState, CurrentPlayerState->Money);
		Message = FString::Printf(TEXT("%s 抽到机会卡：股票获利，获得 120。"), *CurrentPlayerState->GetResolvedDisplayName());
	}
	else if (ChanceOutcome == 1)
	{
		if (!DeductMoney(CurrentPlayerState, 80))
		{
			TriggerBankruptcy(MonopolyGameState->CurrentPlayerIndex, TEXT("机会卡罚款"));
		}
		Message = FString::Printf(TEXT("%s 抽到机会卡：维修房产，支付 80。"), *CurrentPlayerState->GetResolvedDisplayName());
	}
	else
	{
		CurrentPlayerState->AddMoney(60);
		MonopolyGameState->OnMoneyChanged.Broadcast(CurrentPlayerState, CurrentPlayerState->Money);
		Message = FString::Printf(TEXT("%s 抽到机会卡：成功谈判，获得 60。"), *CurrentPlayerState->GetResolvedDisplayName());
	}

	ShowPopup(TEXT("机会"), Message, { TEXT("继续") },
		[this](int32)
		{
			ProcessPostEvent();
		});
}

void AMMonopolyGameMode::ResolveCommunityChestTile(AMMonopolyPlayerState* CurrentPlayerState)
{
	AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState();
	if (MonopolyGameState == nullptr || CurrentPlayerState == nullptr)
	{
		return;
	}

	const int32 Reward = FMath::RandRange(40, 120);
	CurrentPlayerState->AddMoney(Reward);
	MonopolyGameState->OnMoneyChanged.Broadcast(CurrentPlayerState, CurrentPlayerState->Money);

	ShowPopup(TEXT("公共基金"), FString::Printf(TEXT("%s 领取公共基金 %d。"), *CurrentPlayerState->GetResolvedDisplayName(), Reward), { TEXT("继续") },
		[this](int32)
		{
			ProcessPostEvent();
		});
}

void AMMonopolyGameMode::ResolveTaxTile(AMMonopolyPlayerState* CurrentPlayerState, const FMTileData& TileData)
{
	AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState();
	if (MonopolyGameState == nullptr || CurrentPlayerState == nullptr)
	{
		return;
	}

	if (!DeductMoney(CurrentPlayerState, TileData.TaxAmount))
	{
		TriggerBankruptcy(MonopolyGameState->CurrentPlayerIndex, TEXT("税款不足"));
	}

	ShowPopup(TEXT("缴税"), FString::Printf(TEXT("%s 支付税金 %d。"), *CurrentPlayerState->GetResolvedDisplayName(), TileData.TaxAmount), { TEXT("继续") },
		[this](int32)
		{
			ProcessPostEvent();
		});
}

void AMMonopolyGameMode::ProcessPostEvent()
{
	CheckGameEndCondition();
	if (GetMonopolyGameState() != nullptr && GetMonopolyGameState()->TurnState == EMTurnState::GameOver)
	{
		return;
	}

	EndTurn();
}

void AMMonopolyGameMode::EndTurn()
{
	AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState();
	if (MonopolyGameState == nullptr || MonopolyGameState->TurnState == EMTurnState::GameOver)
	{
		return;
	}

	CloseActivePopup();

	const int32 CurrentPlayerIndex = MonopolyGameState->CurrentPlayerIndex;
	if (bPendingExtraTurn)
	{
		bPendingExtraTurn = false;
		ShowPopup(TEXT("额外回合"), TEXT("掷出双骰，获得一次额外回合。"), { TEXT("继续") },
			[this](int32)
			{
				StartTurn();
			});
		return;
	}

	const int32 NextPlayerIndex = FindNextNonBankruptPlayer(CurrentPlayerIndex);
	if (NextPlayerIndex == INDEX_NONE)
	{
		CheckGameEndCondition();
		return;
	}

	MonopolyGameState->ConsecutiveDoublesCount = 0;
	MonopolyGameState->SetCurrentPlayerIndex(NextPlayerIndex);
	MonopolyGameState->SetTurnNumber(MonopolyGameState->TurnNumber + 1);
	StartTurn();
}

int32 AMMonopolyGameMode::FindNextNonBankruptPlayer(const int32 StartIndex) const
{
	const AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState();
	if (MonopolyGameState == nullptr || MonopolyGameState->MonopolyPlayers.IsEmpty())
	{
		return INDEX_NONE;
	}

	for (int32 Offset = 1; Offset <= MonopolyGameState->MonopolyPlayers.Num(); ++Offset)
	{
		const int32 CandidateIndex = (StartIndex + Offset) % MonopolyGameState->MonopolyPlayers.Num();
		const AMMonopolyPlayerState* Candidate = MonopolyGameState->GetMonopolyPlayer(CandidateIndex);
		if (Candidate != nullptr && !Candidate->bIsBankrupt)
		{
			return CandidateIndex;
		}
	}

	return INDEX_NONE;
}

bool AMMonopolyGameMode::TryPurchaseProperty(const int32 PlayerIndex, const int32 TileIndex)
{
	AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState();
	AMMonopolyPlayerState* PlayerState = GetMonopolyPlayerState(PlayerIndex);
	FMTileData* TileData = MonopolyGameState != nullptr ? MonopolyGameState->GetMutableTileData(TileIndex) : nullptr;
	if (MonopolyGameState == nullptr || PlayerState == nullptr || TileData == nullptr || TileData->OwnerPlayerIndex != INDEX_NONE || !TileData->bCanBeOwned)
	{
		return false;
	}

	if (!DeductMoney(PlayerState, TileData->Cost))
	{
		return false;
	}

	TileData->OwnerPlayerIndex = PlayerIndex;
	PlayerState->AddProperty(TileIndex);
	RefreshTileOwnershipVisuals();
	MonopolyGameState->OnPropertyPurchased.Broadcast(PlayerState, TileIndex);
	return true;
}

void AMMonopolyGameMode::CollectRent(const int32 PayerIndex, const int32 ReceiverIndex, const int32 TileIndex)
{
	AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState();
	AMMonopolyPlayerState* Payer = GetMonopolyPlayerState(PayerIndex);
	AMMonopolyPlayerState* Receiver = GetMonopolyPlayerState(ReceiverIndex);
	const FMTileData* TileData = MonopolyGameState != nullptr ? MonopolyGameState->GetTileData(TileIndex) : nullptr;
	if (MonopolyGameState == nullptr || Payer == nullptr || Receiver == nullptr || TileData == nullptr)
	{
		return;
	}

	const int32 RentAmount = CalculateEffectiveRent(*TileData);
	if (!TransferMoney(Payer, Receiver, RentAmount))
	{
		TriggerBankruptcy(PayerIndex, TEXT("无力支付租金"));
		return;
	}

	MonopolyGameState->OnRentPaid.Broadcast(Payer, Receiver, RentAmount);
}

int32 AMMonopolyGameMode::CalculateEffectiveRent(const FMTileData& TileData) const
{
	const AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState();
	if (MonopolyGameState == nullptr || TileData.OwnerPlayerIndex == INDEX_NONE)
	{
		return TileData.Rent;
	}

	const bool bOwnsFullSet = MonopolyGameState->DoesPlayerOwnFullColorGroup(TileData.OwnerPlayerIndex, TileData.ColorGroup);
	return bOwnsFullSet ? TileData.Rent * 2 : TileData.Rent;
}

bool AMMonopolyGameMode::TransferMoney(AMMonopolyPlayerState* FromPlayer, AMMonopolyPlayerState* ToPlayer, const int32 Amount)
{
	if (FromPlayer == nullptr || ToPlayer == nullptr || Amount <= 0)
	{
		return false;
	}

	if (!FromPlayer->DeductMoney(Amount))
	{
		return false;
	}

	ToPlayer->AddMoney(Amount);

	if (AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState())
	{
		MonopolyGameState->OnMoneyChanged.Broadcast(FromPlayer, FromPlayer->Money);
		MonopolyGameState->OnMoneyChanged.Broadcast(ToPlayer, ToPlayer->Money);
	}

	return true;
}

bool AMMonopolyGameMode::DeductMoney(AMMonopolyPlayerState* PlayerState, const int32 Amount)
{
	if (PlayerState == nullptr)
	{
		return false;
	}

	if (!PlayerState->DeductMoney(Amount))
	{
		return false;
	}

	if (AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState())
	{
		MonopolyGameState->OnMoneyChanged.Broadcast(PlayerState, PlayerState->Money);
	}

	return true;
}

void AMMonopolyGameMode::SendToJail(const int32 PlayerIndex)
{
	AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState();
	AMMonopolyPlayerState* PlayerState = GetMonopolyPlayerState(PlayerIndex);
	if (MonopolyGameState == nullptr || PlayerState == nullptr)
	{
		return;
	}

	PlayerState->bIsInJail = true;
	PlayerState->JailTurnsRemaining = MonopolyGameMode::MaxJailAttempts;
	bPendingExtraTurn = false;
	MovePlayerPawnToTile(PlayerIndex, MonopolyGameMode::JailTileIndex);
	MonopolyGameState->OnPlayerJailed.Broadcast(PlayerState, PlayerState->JailTurnsRemaining);

	ShowPopup(TEXT("前往监狱"), FString::Printf(TEXT("%s 被送入监狱。"), *PlayerState->GetResolvedDisplayName()), { TEXT("继续") },
		[this](int32)
		{
			EndTurn();
		});
}

void AMMonopolyGameMode::PayBail(const int32 PlayerIndex, const bool bContinueWithRoll)
{
	AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState();
	AMMonopolyPlayerState* PlayerState = GetMonopolyPlayerState(PlayerIndex);
	if (MonopolyGameState == nullptr || PlayerState == nullptr || !PlayerState->bIsInJail)
	{
		return;
	}

	if (!DeductMoney(PlayerState, BailAmount))
	{
		TriggerBankruptcy(PlayerIndex, TEXT("无力支付保释金"));
		return;
	}

	PlayerState->bIsInJail = false;
	PlayerState->JailTurnsRemaining = 0;
	ShowPopup(TEXT("支付保释金"), FString::Printf(TEXT("%s 支付保释金 %d，立即恢复行动。"), *PlayerState->GetResolvedDisplayName(), BailAmount), { TEXT("继续") },
		[this, bContinueWithRoll](int32)
		{
			if (bContinueWithRoll)
			{
				SetTurnState(EMTurnState::WaitForRoll);
				OnPlayerRequestRoll();
			}
			else
			{
				ProcessPostEvent();
			}
		});
}

void AMMonopolyGameMode::ForcePayBail(const int32 PlayerIndex)
{
	AMMonopolyPlayerState* PlayerState = GetMonopolyPlayerState(PlayerIndex);
	if (PlayerState == nullptr)
	{
		return;
	}

	if (!PlayerState->CanAfford(BailAmount))
	{
		TriggerBankruptcy(PlayerIndex, TEXT("最后一次监狱尝试失败且无法保释"));
		return;
	}

	PayBail(PlayerIndex, true);
}

void AMMonopolyGameMode::TriggerBankruptcy(const int32 PlayerIndex, const FString& Reason)
{
	AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState();
	AMMonopolyPlayerState* PlayerState = GetMonopolyPlayerState(PlayerIndex);
	if (MonopolyGameState == nullptr || PlayerState == nullptr || PlayerState->bIsBankrupt)
	{
		return;
	}

	PlayerState->bIsBankrupt = true;
	PlayerState->bIsInJail = false;
	PlayerState->JailTurnsRemaining = 0;
	ReleaseAllProperties(PlayerState);
	MonopolyGameState->ActivePlayerCount = FMath::Max(0, MonopolyGameState->ActivePlayerCount - 1);
	MonopolyGameState->OnPlayerBankrupt.Broadcast(PlayerState);

	ShowPopup(TEXT("玩家破产"), FString::Printf(TEXT("%s 破产。原因：%s"), *PlayerState->GetResolvedDisplayName(), *Reason), { TEXT("继续") },
		[this](int32)
		{
			CheckGameEndCondition();
			if (GetMonopolyGameState() != nullptr && GetMonopolyGameState()->TurnState != EMTurnState::GameOver)
			{
				EndTurn();
			}
		});
}

void AMMonopolyGameMode::ReleaseAllProperties(AMMonopolyPlayerState* PlayerState)
{
	AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState();
	if (MonopolyGameState == nullptr || PlayerState == nullptr)
	{
		return;
	}

	for (const int32 TileIndex : PlayerState->OwnedTileIndices)
	{
		if (FMTileData* TileData = MonopolyGameState->GetMutableTileData(TileIndex))
		{
			TileData->OwnerPlayerIndex = INDEX_NONE;
		}
	}

	PlayerState->RemoveAllProperties();
	RefreshTileOwnershipVisuals();
}

void AMMonopolyGameMode::CheckGameEndCondition()
{
	AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState();
	if (MonopolyGameState == nullptr)
	{
		return;
	}

	TArray<AMMonopolyPlayerState*> Survivors;
	for (AMMonopolyPlayerState* PlayerState : MonopolyGameState->MonopolyPlayers)
	{
		if (PlayerState != nullptr && !PlayerState->bIsBankrupt)
		{
			Survivors.Add(PlayerState);
		}
	}

	MonopolyGameState->ActivePlayerCount = Survivors.Num();
	if (Survivors.Num() <= 1)
	{
		DeclareWinner(Survivors.IsEmpty() ? nullptr : Survivors[0]);
	}
}

void AMMonopolyGameMode::DeclareWinner(AMMonopolyPlayerState* Winner)
{
	AMMonopolyGameState* MonopolyGameState = GetMonopolyGameState();
	if (MonopolyGameState == nullptr || MonopolyGameState->TurnState == EMTurnState::GameOver)
	{
		return;
	}

	MonopolyGameState->GamePhase = EMGamePhase::Finished;
	SetTurnState(EMTurnState::GameOver);
	MonopolyGameState->OnGameOver.Broadcast(Winner);

	const FString WinnerName = Winner != nullptr ? Winner->GetResolvedDisplayName() : TEXT("无");
	ShowPopup(TEXT("游戏结束"), FString::Printf(TEXT("胜利者：%s"), *WinnerName), { TEXT("确定") },
		[](int32)
		{
		});
}

void AMMonopolyGameMode::ShowPopup(const FString& Title, const FString& Message, const TArray<FString>& ButtonLabels, TFunction<void(int32)> Callback)
{
	CloseActivePopup();
	SetTurnState(EMTurnState::WaitingForPopup);

	UWorld* World = GetWorld();
	APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
	if (World != nullptr)
	{
		if (PC != nullptr)
		{
			ActivePopupWidget = CreateWidget<UMPopupWidget>(PC, PopupWidgetClass != nullptr ? PopupWidgetClass.Get() : UMPopupWidget::StaticClass());
		}
		else
		{
			ActivePopupWidget = CreateWidget<UMPopupWidget>(World, PopupWidgetClass != nullptr ? PopupWidgetClass.Get() : UMPopupWidget::StaticClass());
		}

		if (ActivePopupWidget != nullptr)
		{
			ActivePopupWidget->AddToViewport(2000);
			ActivePopupWidget->SetVisibility(ESlateVisibility::Visible);

			if (PC != nullptr)
			{
				FInputModeGameAndUI InputMode;
				InputMode.SetWidgetToFocus(ActivePopupWidget->TakeWidget());
				InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
				InputMode.SetHideCursorDuringCapture(false);
				PC->SetInputMode(InputMode);
				PC->bShowMouseCursor = true;
				PC->bEnableClickEvents = true;
				PC->bEnableMouseOverEvents = true;
			}

			UE_LOG(LogTemp, Log, TEXT("[Phase8] Popup widget created: %s Owner=%s"),
				*ActivePopupWidget->GetClass()->GetName(),
				PC != nullptr ? *PC->GetClass()->GetName() : TEXT("World"));

			ActivePopupWidget->ShowPopup(Title, Message, ButtonLabels,
				[this, LocalCallback = MoveTemp(Callback)](const int32 ButtonIndex) mutable
				{
					ActivePopupWidget = nullptr;

					if (APlayerController* LocalPC = UGameplayStatics::GetPlayerController(this, 0))
					{
						FInputModeGameAndUI InputMode;
						if (ActiveHUDWidget != nullptr)
						{
							InputMode.SetWidgetToFocus(ActiveHUDWidget->TakeWidget());
						}
						InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
						InputMode.SetHideCursorDuringCapture(false);
						LocalPC->SetInputMode(InputMode);
						LocalPC->bShowMouseCursor = true;
						LocalPC->bEnableClickEvents = true;
						LocalPC->bEnableMouseOverEvents = true;
					}

					if (LocalCallback)
					{
						LocalCallback(ButtonIndex);
					}
				});
			return;
		}
	}

	if (Callback)
	{
		Callback(0);
	}
}

void AMMonopolyGameMode::CloseActivePopup()
{
	if (ActivePopupWidget != nullptr)
	{
		ActivePopupWidget->ClosePopup();
		ActivePopupWidget = nullptr;
	}
}
