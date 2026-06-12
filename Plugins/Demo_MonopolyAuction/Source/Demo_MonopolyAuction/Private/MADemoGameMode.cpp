// Copyright Phase14 v0 attempt2. 回合状态机与规则裁决核心实现。
#include "MADemoGameMode.h"
#include "MADemoGameState.h"
#include "MADemoPlayerData.h"
#include "MADemoStockMarket.h"
#include "MADemoDataAssets.h"
#include "MADemoPlayerController.h"
#include "UI/MADemoHUDWidget.h"
#include "Blueprint/UserWidget.h"
#include "Kismet/GameplayStatics.h"
#include "TimerManager.h"
#include "Engine/World.h"

AMADemoGameMode::AMADemoGameMode()
{
	// 绑定本 demo 的 GameState 与 PlayerController。
	GameStateClass = AMADemoGameState::StaticClass();
	PlayerControllerClass = AMADemoPlayerController::StaticClass();
	PrimaryActorTick.bCanEverTick = false;
}

void AMADemoGameMode::BeginPlay()
{
	Super::BeginPlay();

	// 进入关卡上下文(-game 启动)。这是人玩/自动驾驶路径。
	bInteractiveContext = true;
	ParseLaunchArgs();

	// 关卡上下文默认开一局 4 人(可被自动驾驶参数覆盖玩家数)。
	const int32 Seed = 20260612;
	InitializeGame(4, Seed);

	// 创建 HUD widget 并加入视口(C++ CreateWidget 兜底,无需 WBP)。
	if (UWorld* World = GetWorld())
	{
		if (APlayerController* PC = UGameplayStatics::GetPlayerController(World, 0))
		{
			HUDWidget = CreateWidget<UMADemoHUDWidget>(PC, UMADemoHUDWidget::StaticClass());
			if (HUDWidget)
			{
				HUDWidget->AddToViewport();
				HUDWidget->BindGameState(CachedGameState);
			}
		}
	}

	StartTurn();
	RefreshHUD();

	// 若启动参数请求自动驾驶演示,起定时器逐回合自动推进。
	if (AutoPlayTurns > 0)
	{
		GetWorldTimerManager().SetTimer(AutoPlayTimerHandle, this,
			&AMADemoGameMode::AutoPlayTick, 0.8f, true, 1.0f);
	}
}

void AMADemoGameMode::ParseLaunchArgs()
{
	// 解析自动驾驶参数:-MADemoAutoPlay=N 自动推进 N 回合;-MADemoAutoShot 演示完截图退出。
	const TCHAR* CmdLine = FCommandLine::Get();
	int32 Turns = 0;
	if (FParse::Value(CmdLine, TEXT("MADemoAutoPlay="), Turns))
	{
		AutoPlayTurns = FMath::Max(0, Turns);
	}
	if (FParse::Param(CmdLine, TEXT("MADemoAutoShot")))
	{
		bAutoShotAndExit = true;
	}
}

AMADemoGameState* AMADemoGameMode::GetDemoGameState() const
{
	return CachedGameState;
}

void AMADemoGameMode::InitializeGame(int32 NumPlayers, int32 Seed)
{
	NumPlayers = FMath::Clamp(NumPlayers, 2, 6);

	// 取/建 GameState。关卡上下文用引擎已生成的 GameState;纯逻辑直驱时新建。
	AMADemoGameState* GS = GetGameState<AMADemoGameState>();
	if (!GS)
	{
		GS = NewObject<AMADemoGameState>(this);
	}
	CachedGameState = GS;

	// 准备数据资产(优先配置资产,否则代码默认兜底)。
	GS->BoardData = ConfiguredBoardData ? ToRawPtr(ConfiguredBoardData)
		: NewObject<UMADemoBoardDataAsset>(GS);
	GS->RulesData = ConfiguredRulesData ? ToRawPtr(ConfiguredRulesData)
		: NewObject<UMADemoRulesDataAsset>(GS);

	// 确定性骰子流。
	DiceStream.Initialize(Seed);
	ConsecutiveDoubles = 0;

	// 棋盘所有权全置无主。
	GS->TileOwnership.Init(-1, GS->BoardData->Tiles.Num());

	// 股票市场。
	GS->StockMarket = NewObject<UMADemoStockMarket>(GS);
	GS->StockMarket->InitializeStocks(GS->RulesData->StockInitialPrice);

	// 玩家。
	GS->Players.Empty();
	const FLinearColor Colors[6] = {
		FLinearColor::Red, FLinearColor::Blue, FLinearColor::Green,
		FLinearColor::Yellow, FLinearColor(1, 0, 1), FLinearColor(0, 1, 1)
	};
	for (int32 i = 0; i < NumPlayers; ++i)
	{
		UMADemoPlayerData* P = NewObject<UMADemoPlayerData>(GS);
		P->PlayerIndex = i;
		P->Money = GS->RulesData->StartingCash;
		P->CurrentTileIndex = GS->BoardData->StartTileIndex;
		P->PlayerColor = Colors[i % 6];
		P->StockHoldings.Init(0, 3);
		GS->Players.Add(P);
	}

	GS->TurnNumber = 1;
	GS->CurrentPlayerIndex = 0;
	GS->ActivePlayerCount = NumPlayers;
	GS->TurnPhase = EMADemoTurnPhase::WaitingForRoll;
	GS->bGameOver = false;
	GS->WinnerIndex = -1;
	GS->AuctionState = FMADemoAuctionState();
}

void AMADemoGameMode::StartTurn()
{
	AMADemoGameState* GS = CachedGameState;
	if (!GS || GS->bGameOver)
	{
		return;
	}

	// 回合开始:对所有股票按上一次掷骰和施加波动(GDD 2.2)。首回合用初值。
	GS->StockMarket->ApplyTurnSwing(GS->LastDice.Sum() > 0 ? GS->LastDice.Sum() : 7,
		GS->RulesData->StockSwingPercent);

	// 监狱回合开始处理。
	UMADemoPlayerData* P = GS->GetPlayer(GS->CurrentPlayerIndex);
	if (P && P->bIsInJail)
	{
		HandleJailTurnStart();
	}

	GS->TurnPhase = EMADemoTurnPhase::WaitingForRoll;
	ConsecutiveDoubles = 0;
}

FMADemoDiceResult AMADemoGameMode::RollDice()
{
	AMADemoGameState* GS = CachedGameState;
	const int32 Sides = GS && GS->RulesData ? GS->RulesData->DiceSides : 6;
	FMADemoDiceResult R;
	R.Die1 = DiceStream.RandRange(1, Sides);
	R.Die2 = DiceStream.RandRange(1, Sides);
	R.bIsDouble = (R.Die1 == R.Die2);
	return R;
}

void AMADemoGameMode::RequestRollAndResolve()
{
	AMADemoGameState* GS = CachedGameState;
	if (!GS || GS->bGameOver)
	{
		return;
	}
	UMADemoPlayerData* P = GS->GetPlayer(GS->CurrentPlayerIndex);
	if (!P || P->bIsBankrupt)
	{
		AdvanceToNextPlayer();
		return;
	}

	// 监狱中且本回合未出狱:不移动,直接结束回合(出狱判定在 StartTurn 已做)。
	if (P->bIsInJail)
	{
		GS->TurnPhase = EMADemoTurnPhase::TurnEnd;
		AdvanceToNextPlayer();
		return;
	}

	GS->TurnPhase = EMADemoTurnPhase::Resolving;
	const FMADemoDiceResult Dice = RollDice();
	GS->LastDice = Dice;

	// 双数计数:三连双直接入狱(契约 dice.triple_doubles_jail)。
	if (Dice.bIsDouble)
	{
		++ConsecutiveDoubles;
		if (ConsecutiveDoubles >= 3)
		{
			HandleGoToJail();
			ConsecutiveDoubles = 0;
			GS->TurnPhase = EMADemoTurnPhase::TurnEnd;
			AdvanceToNextPlayer();
			return;
		}
	}

	MoveCurrentPlayer(Dice.Sum());

	if (GS->bGameOver)
	{
		return;
	}

	// 双数追加掷(契约 dice.doubles_extra_turn):不切玩家,继续本玩家。
	if (Dice.bIsDouble && !P->bIsBankrupt && !P->bIsInJail)
	{
		GS->TurnPhase = EMADemoTurnPhase::WaitingForRoll;
		return;
	}

	GS->TurnPhase = EMADemoTurnPhase::TurnEnd;
	AdvanceToNextPlayer();
}

void AMADemoGameMode::MoveCurrentPlayer(int32 Steps)
{
	AMADemoGameState* GS = CachedGameState;
	UMADemoPlayerData* P = GS->GetPlayer(GS->CurrentPlayerIndex);
	if (!P)
	{
		return;
	}
	const int32 TileCount = GS->BoardData->Tiles.Num();
	const int32 OldIndex = P->CurrentTileIndex;
	const int32 NewIndex = (OldIndex + Steps) % TileCount;

	// 过/到起点 +200(契约 economy.start_bonus):新位置小于旧位置说明绕了一圈。
	if (NewIndex < OldIndex)
	{
		P->AddMoney(GS->RulesData->StartBonus);
	}

	P->CurrentTileIndex = NewIndex;
	OnPlayerLanded(NewIndex);
}

void AMADemoGameMode::OnPlayerLanded(int32 TileIndex)
{
	AMADemoGameState* GS = CachedGameState;
	const FMADemoTileInfo Info = GS->GetTileInfo(TileIndex);
	switch (Info.TileType)
	{
	case EMADemoTileType::Property:
		HandlePropertyTile(TileIndex);
		break;
	case EMADemoTileType::Tax:
		HandleTaxTile(TileIndex);
		break;
	case EMADemoTileType::GoToJail:
		HandleGoToJail();
		break;
	case EMADemoTileType::Start:
		// 落在起点已在移动时给奖励,这里再补领一次(停留)。
		GS->GetPlayer(GS->CurrentPlayerIndex)->AddMoney(GS->RulesData->StartBonus);
		break;
	default:
		// JailVisit / FreeParking / Chance / Community / StockExchange:v0 无强制事件。
		break;
	}
	CheckGameOver();
}

void AMADemoGameMode::HandlePropertyTile(int32 TileIndex)
{
	AMADemoGameState* GS = CachedGameState;
	UMADemoPlayerData* P = GS->GetPlayer(GS->CurrentPlayerIndex);
	const int32 TileOwnerIndex = GS->GetTileOwner(TileIndex);

	if (TileOwnerIndex < 0)
	{
		// 无主:自动购买策略(无人值守裁决)。放弃则进拍卖骨架(v0 不展开交互)。
		if (AutoBuyPolicy(TileIndex))
		{
			const FMADemoTileInfo Info = GS->GetTileInfo(TileIndex);
			P->DeductMoney(Info.Price);
			P->AddProperty(TileIndex);
			GS->SetTileOwner(TileIndex, P->PlayerIndex);
		}
		else
		{
			// 放弃购买 → 进入拍卖(GDD 2.1,v0 仅置数据态,不展开多轮交互 UI)。
			GS->AuctionState.bActive = true;
			GS->AuctionState.TileIndex = TileIndex;
			GS->AuctionState.HighestBid = 0;
			GS->AuctionState.HighestBidderIndex = -1;
			// v0 流拍收敛:无买家则保持无主,清拍卖态。
			GS->AuctionState.bActive = false;
		}
	}
	else if (TileOwnerIndex != P->PlayerIndex)
	{
		// 他人地产:付租。
		const int32 Rent = GS->CalculateRent(TileIndex);
		ProcessPayment(P, Rent, TileOwnerIndex);
	}
	// 自己地产:无事发生。
}

void AMADemoGameMode::HandleTaxTile(int32 TileIndex)
{
	AMADemoGameState* GS = CachedGameState;
	UMADemoPlayerData* P = GS->GetPlayer(GS->CurrentPlayerIndex);
	const FMADemoTileInfo Info = GS->GetTileInfo(TileIndex);
	// 税务格 Price 字段存缴纳金额(数据驱动)。无收款方(银行),ReceiverIndex=-1。
	ProcessPayment(P, Info.Price, -1);
}

void AMADemoGameMode::HandleGoToJail()
{
	AMADemoGameState* GS = CachedGameState;
	UMADemoPlayerData* P = GS->GetPlayer(GS->CurrentPlayerIndex);
	// 移动到监狱探访格,标记在狱,不过起点不领钱(契约 jail.visit_tile_index)。
	P->CurrentTileIndex = GS->BoardData->JailVisitTileIndex;
	P->bIsInJail = true;
	P->JailTurnsServed = 0;
}

void AMADemoGameMode::HandleJailTurnStart()
{
	AMADemoGameState* GS = CachedGameState;
	UMADemoPlayerData* P = GS->GetPlayer(GS->CurrentPlayerIndex);
	if (!P || !P->bIsInJail)
	{
		return;
	}
	++P->JailTurnsServed;

	// 尝试掷双出狱(免费)。
	const FMADemoDiceResult Dice = RollDice();
	if (Dice.bIsDouble)
	{
		P->bIsInJail = false;
		P->JailTurnsServed = 0;
		// 出狱后用该掷骰结果移动。
		GS->LastDice = Dice;
		MoveCurrentPlayer(Dice.Sum());
		return;
	}

	// 满回合强制保释出狱(契约 jail.max_turns / jail.bail_cost)。
	if (P->JailTurnsServed >= GS->RulesData->JailMaxTurns)
	{
		ProcessPayment(P, GS->RulesData->JailBailCost, -1);
		P->bIsInJail = false;
		P->JailTurnsServed = 0;
	}
}

bool AMADemoGameMode::ProcessPayment(UMADemoPlayerData* Payer, int32 Amount, int32 ReceiverIndex)
{
	AMADemoGameState* GS = CachedGameState;
	if (!Payer || Amount <= 0)
	{
		return true;
	}
	if (!Payer->CanAfford(Amount))
	{
		// 付不起 → 破产清算:现金尽数转债主(provisional 简化全转)。
		if (ReceiverIndex >= 0)
		{
			if (UMADemoPlayerData* Receiver = GS->GetPlayer(ReceiverIndex))
			{
				Receiver->AddMoney(Payer->Money);
			}
		}
		Payer->Money = 0;
		EliminatePlayer(Payer);
		return false;
	}
	Payer->DeductMoney(Amount);
	if (ReceiverIndex >= 0)
	{
		if (UMADemoPlayerData* Receiver = GS->GetPlayer(ReceiverIndex))
		{
			Receiver->AddMoney(Amount);
		}
	}
	return true;
}

void AMADemoGameMode::EliminatePlayer(UMADemoPlayerData* Player)
{
	AMADemoGameState* GS = CachedGameState;
	if (!Player || Player->bIsBankrupt)
	{
		return;
	}
	Player->bIsBankrupt = true;
	// 地产归无主(GDD 3.3)。
	for (int32 TileIdx : Player->OwnedProperties)
	{
		GS->SetTileOwner(TileIdx, -1);
	}
	Player->ClearProperties();
	GS->ActivePlayerCount = GS->GetActivePlayerCount();
}

bool AMADemoGameMode::AutoBuyPolicy(int32 TileIndex)
{
	AMADemoGameState* GS = CachedGameState;
	UMADemoPlayerData* P = GS->GetPlayer(GS->CurrentPlayerIndex);
	const FMADemoTileInfo Info = GS->GetTileInfo(TileIndex);
	// 保守策略:买完后还剩 >= 保释金缓冲才买(provisional)。
	const int32 Buffer = GS->RulesData->AutoBuyReserveBuffer;
	return P->Money >= (Info.Price + Buffer);
}

void AMADemoGameMode::AdvanceToNextPlayer()
{
	AMADemoGameState* GS = CachedGameState;
	if (!GS || GS->bGameOver)
	{
		return;
	}
	ConsecutiveDoubles = 0;

	// 找下一个存活玩家。
	const int32 Count = GS->Players.Num();
	int32 Next = GS->CurrentPlayerIndex;
	for (int32 i = 0; i < Count; ++i)
	{
		Next = (Next + 1) % Count;
		UMADemoPlayerData* P = GS->GetPlayer(Next);
		if (P && !P->bIsBankrupt)
		{
			break;
		}
	}

	// 回到 0 号附近视为新一轮:回合数 +1。
	if (Next <= GS->CurrentPlayerIndex)
	{
		++GS->TurnNumber;
	}
	GS->CurrentPlayerIndex = Next;

	// 达回合上限收敛(provisional cg-max-game-length)。
	if (GS->TurnNumber > GS->RulesData->MaxGameRounds)
	{
		CheckGameOver();
		if (!GS->bGameOver)
		{
			// 强制按净资产判最高者胜。
			int32 BestIdx = -1, BestWorth = INT32_MIN;
			for (int32 i = 0; i < GS->Players.Num(); ++i)
			{
				if (!GS->Players[i]->bIsBankrupt)
				{
					const int32 W = GS->GetPlayerNetWorth(i);
					if (W > BestWorth) { BestWorth = W; BestIdx = i; }
				}
			}
			GS->WinnerIndex = BestIdx;
			GS->bGameOver = true;
			GS->TurnPhase = EMADemoTurnPhase::GameOver;
		}
		return;
	}

	StartTurn();
}

void AMADemoGameMode::CheckGameOver()
{
	AMADemoGameState* GS = CachedGameState;
	if (!GS || GS->bGameOver)
	{
		return;
	}
	GS->ActivePlayerCount = GS->GetActivePlayerCount();
	if (GS->ActivePlayerCount <= 1)
	{
		// 存活 1 人胜(契约 last_non_bankrupt_player)。
		int32 Winner = -1;
		for (int32 i = 0; i < GS->Players.Num(); ++i)
		{
			if (!GS->Players[i]->bIsBankrupt)
			{
				Winner = i;
				break;
			}
		}
		GS->WinnerIndex = Winner;
		GS->bGameOver = true;
		GS->TurnPhase = EMADemoTurnPhase::GameOver;
	}
}

bool AMADemoGameMode::IsGameOver() const
{
	return CachedGameState ? CachedGameState->bGameOver : true;
}

int32 AMADemoGameMode::RunFullGameToCompletion(int32 NumPlayers, int32 Seed)
{
	InitializeGame(NumPlayers, Seed);
	AMADemoGameState* GS = CachedGameState;
	StartTurn();

	// 硬上限保护:防止任何逻辑缺陷死循环(回合上限 ×玩家数 ×双数追加余量)。
	const int32 HardCap = (GS->RulesData->MaxGameRounds + 10) * NumPlayers * 4;
	int32 Steps = 0;
	while (!GS->bGameOver && Steps < HardCap)
	{
		RequestRollAndResolve();
		++Steps;
	}
	// 若达保护上限仍未结束,强制收敛。
	if (!GS->bGameOver)
	{
		int32 BestIdx = -1, BestWorth = INT32_MIN;
		for (int32 i = 0; i < GS->Players.Num(); ++i)
		{
			if (!GS->Players[i]->bIsBankrupt)
			{
				const int32 W = GS->GetPlayerNetWorth(i);
				if (W > BestWorth) { BestWorth = W; BestIdx = i; }
			}
		}
		GS->WinnerIndex = BestIdx;
		GS->bGameOver = true;
		GS->TurnPhase = EMADemoTurnPhase::GameOver;
	}
	return GS->WinnerIndex;
}

bool AMADemoGameMode::AutoAdvanceOneTurn()
{
	AMADemoGameState* GS = CachedGameState;
	if (!GS || GS->bGameOver)
	{
		return false;
	}
	// 推进当前玩家:可能因双数多次掷,这里推进到切玩家或结束为止。
	const int32 PlayerBefore = GS->CurrentPlayerIndex;
	int32 Guard = 0;
	do
	{
		RequestRollAndResolve();
		++Guard;
	}
	while (!GS->bGameOver && GS->CurrentPlayerIndex == PlayerBefore && Guard < 10);
	return !GS->bGameOver;
}

void AMADemoGameMode::RefreshHUD()
{
	if (HUDWidget && CachedGameState)
	{
		HUDWidget->RefreshHUD();
	}
}

void AMADemoGameMode::AutoPlayTick()
{
	// 自动驾驶:逐回合推进并刷新 HUD,达到目标回合数后截图退出(无人值守演示)。
	const bool bContinue = AutoAdvanceOneTurn();
	++AutoPlayedTurns;
	RefreshHUD();

	const bool bReachedTarget = (AutoPlayedTurns >= AutoPlayTurns);
	if (!bContinue || bReachedTarget)
	{
		GetWorldTimerManager().ClearTimer(AutoPlayTimerHandle);
		if (bAutoShotAndExit)
		{
			// 触发高分辨率截图后短延迟退出(留给截图落盘时间)。
			if (UWorld* World = GetWorld())
			{
				GEngine->Exec(World, TEXT("HighResShot 1280x720"));
				FTimerHandle QuitHandle;
				World->GetTimerManager().SetTimer(QuitHandle, []()
				{
					FGenericPlatformMisc::RequestExit(false);
				}, 2.0f, false);
			}
		}
	}
}
