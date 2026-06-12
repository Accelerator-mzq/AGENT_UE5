// Copyright Phase14 v0 attempt2. 回合状态机与规则裁决核心实现。
#include "MADemoGameMode.h"
#include "MADemoGameState.h"
#include "MADemoPlayerData.h"
#include "MADemoStockMarket.h"
#include "MADemoDataAssets.h"
#include "MADemoPlayerController.h"
#include "UI/MADemoHUDWidget.h"
#include "UI/MADemoHUD.h"
#include "Blueprint/UserWidget.h"
#include "Kismet/GameplayStatics.h"
#include "TimerManager.h"
#include "Engine/World.h"
#include "Engine/GameViewportClient.h"
#include "UnrealClient.h"
#include "Misc/Paths.h"
#include "GameFramework/PlayerInput.h"
#include "InputCoreTypes.h"

AMADemoGameMode::AMADemoGameMode()
{
	// 绑定本 demo 的 GameState / PlayerController / HUD。
	GameStateClass = AMADemoGameState::StaticClass();
	PlayerControllerClass = AMADemoPlayerController::StaticClass();
	// Canvas HUD:保证 -game 画面与截图里 HUD 真实可见。
	HUDClass = AMADemoHUD::StaticClass();
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

	StartTurn();

	// 延迟创建 HUD:确保 PlayerController/LocalPlayer/GameViewport 已就绪后再 CreateWidget+AddToViewport。
	// BeginPlay 时机 PC 可能尚未具备 LocalPlayer,直接建 widget 会拿不到有效 player context 而不渲染。
	FTimerHandle HUDHandle;
	GetWorldTimerManager().SetTimer(HUDHandle, this, &AMADemoGameMode::CreateHUDDeferred, 0.3f, false);

	// 若启动参数请求自动驾驶演示,起定时器逐回合自动推进(首发延迟 1.5s,确保 HUD 已上屏)。
	if (AutoPlayTurns > 0)
	{
		GetWorldTimerManager().SetTimer(AutoPlayTimerHandle, this,
			&AMADemoGameMode::AutoPlayTick, 0.8f, true, 1.5f);
	}
	else if (bAutoPauseShot)
	{
		// 真实 Esc 路径截图:2s 注入 Escape(暂停面板经真实输入管线上屏)→ 3.5s 截图 → 退出。
		FTimerHandle EscHandle;
		GetWorldTimerManager().SetTimer(EscHandle, this,
			&AMADemoGameMode::InjectEscapeKey, 2.0f, false);
		FTimerHandle PauseShotHandle;
		GetWorldTimerManager().SetTimer(PauseShotHandle, [this]()
		{
			RequestViewportScreenshot(AutoShotPath);
			GetWorldTimerManager().SetTimer(QuitTimerHandle, this,
				&AMADemoGameMode::FinishAutoShot, 3.0f, false);
		}, 3.5f, false);
	}
	else if (bAutoShotAndExit)
	{
		// 静态面板截图路径(无对局推进):延迟截图后退出,确保 HUD/面板已上屏。
		FTimerHandle StaticShotHandle;
		GetWorldTimerManager().SetTimer(StaticShotHandle, [this]()
		{
			RequestViewportScreenshot(AutoShotPath);
			GetWorldTimerManager().SetTimer(QuitTimerHandle, this,
				&AMADemoGameMode::FinishAutoShot, 3.0f, false);
		}, 2.0f, false);
	}
}

void AMADemoGameMode::CreateHUDDeferred()
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}
	APlayerController* PC = UGameplayStatics::GetPlayerController(World, 0);
	if (!PC)
	{
		UE_LOG(LogTemp, Warning, TEXT("[Demo_MonopolyAuction] CreateHUDDeferred: 无 PlayerController,重试"));
		FTimerHandle Retry;
		GetWorldTimerManager().SetTimer(Retry, this, &AMADemoGameMode::CreateHUDDeferred, 0.3f, false);
		return;
	}
	HUDWidget = CreateWidget<UMADemoHUDWidget>(PC, UMADemoHUDWidget::StaticClass());
	if (HUDWidget)
	{
		HUDWidget->AddToViewport(100);
		HUDWidget->BindGameState(CachedGameState);
		HUDWidget->SetVisibility(ESlateVisibility::HitTestInvisible);
		UE_LOG(LogTemp, Log, TEXT("[Demo_MonopolyAuction] HUD 已创建并加入视口(玩家数=%d)"),
			CachedGameState ? CachedGameState->Players.Num() : 0);
	}
	else
	{
		UE_LOG(LogTemp, Error, TEXT("[Demo_MonopolyAuction] HUD CreateWidget 失败"));
	}
	RefreshHUD();
}

void AMADemoGameMode::ParseLaunchArgs()
{
	// 解析自动驾驶参数:
	//   -MADemoAutoPlay=N   自动推进 N 回合
	//   -MADemoAutoShot     演示完截图退出
	//   -MADemoShotPath=... 截图输出绝对路径(.png)
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
	FString ShotPath;
	if (FParse::Value(CmdLine, TEXT("MADemoShotPath="), ShotPath))
	{
		AutoShotPath = ShotPath;
	}
	// 真实 Esc 路径截图:注入 Escape 按键事件(非面板演示),用于 pause 截图证据。
	if (FParse::Param(CmdLine, TEXT("MADemoAutoPauseShot")))
	{
		bAutoPauseShot = true;
	}
	// 拍卖面板截图:首场拍卖开始后延迟截取(增量批 1 呈现实证)。
	FString AuctionShot;
	if (FParse::Value(CmdLine, TEXT("MADemoAuctionShotPath="), AuctionShot))
	{
		AuctionShotPath = AuctionShot;
	}
}

void AMADemoGameMode::InjectEscapeKey()
{
	// 注入真实 Escape 按键事件:走 PlayerInput → InputComponent BindKey → IntentPause
	// 的完整输入管线,与人按物理 Esc 同一代码路径(非直接调 TogglePauseState)。
	if (UWorld* World = GetWorld())
	{
		if (APlayerController* PC = UGameplayStatics::GetPlayerController(World, 0))
		{
			FInputKeyParams Params(EKeys::Escape, IE_Pressed, 1.0);
			PC->InputKey(Params);
			UE_LOG(LogTemp, Log, TEXT("[Demo_MonopolyAuction] 已注入 Escape 按键事件(真实输入管线)"));
		}
	}
}

void AMADemoGameMode::RequestViewportScreenshot(const FString& OutPath)
{
	// 关键:请求"带 UI 的后台缓冲截图"(非 HighResShot)。
	// 普通 back-buffer 截图会把 Slate/UMG(HUD)合成进画面,从而真实呈现 HUD;
	// HighResShot 走离屏渲染管线,不含 UI 合成且场景缓冲可能为黑,故不能用于 HUD 截图。
	if (UWorld* World = GetWorld())
	{
		if (UGameViewportClient* VP = World->GetGameViewport())
		{
			if (!OutPath.IsEmpty())
			{
				// 指定绝对路径文件名,不加后缀(可重入覆盖)。
				FScreenshotRequest::RequestScreenshot(OutPath, /*bShowUI=*/true, /*bAddFilenameSuffix=*/false);
			}
			else
			{
				FScreenshotRequest::RequestScreenshot(/*bShowUI=*/true);
			}
		}
	}
}

void AMADemoGameMode::FinishAutoShot()
{
	FGenericPlatformMisc::RequestExit(false);
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
	// 暂停时掷骰意图被拒(试玩反馈修复轮;冒烟 InteractionSemantics 钉死此回归)。
	if (GS->bPaused)
	{
		return;
	}
	// TurnEnd 阶段 Space 无效:回合节奏还给玩家,结算后须按 Enter 结束回合。
	if (GS->TurnPhase == EMADemoTurnPhase::TurnEnd)
	{
		return;
	}
	// 拍卖进行中掷骰无效(拍卖期 Space 语义切换为出价,经 AuctionBidCurrent 进入)。
	if (GS->TurnPhase == EMADemoTurnPhase::Auction)
	{
		return;
	}
	UMADemoPlayerData* P = GS->GetPlayer(GS->CurrentPlayerIndex);
	if (!P || P->bIsBankrupt)
	{
		// 破产跳过:系统纠偏路径,保留自动切人(玩家对已退场者无操作空间,provisional)。
		AdvanceToNextPlayer();
		return;
	}

	// 监狱中且本回合未出狱:不移动,停 TurnEnd 让玩家看到蹲守反馈后按 Enter(provisional)。
	if (P->bIsInJail)
	{
		GS->TurnPhase = EMADemoTurnPhase::TurnEnd;
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
			// 三连双入狱:停 TurnEnd 让玩家看清入狱事件再按 Enter(provisional)。
			GS->TurnPhase = EMADemoTurnPhase::TurnEnd;
			return;
		}
	}

	MoveCurrentPlayer(Dice.Sum());

	if (GS->bGameOver)
	{
		return;
	}

	// 落格触发了拍卖:回合流被打断,暂存双数追加掷,待 FinishAuction 恢复。
	if (GS->TurnPhase == EMADemoTurnPhase::Auction)
	{
		bPendingExtraRollAfterAuction = Dice.bIsDouble && !P->bIsBankrupt && !P->bIsInJail;
		return;
	}

	// 双数追加掷(契约 dice.doubles_extra_turn):不切玩家,继续本玩家。
	if (Dice.bIsDouble && !P->bIsBankrupt && !P->bIsInJail)
	{
		GS->TurnPhase = EMADemoTurnPhase::WaitingForRoll;
		return;
	}

	// 正常路径:结算完停 TurnEnd,等玩家 Enter(IntentEndTurn → AdvanceToNextPlayer)。
	GS->TurnPhase = EMADemoTurnPhase::TurnEnd;
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
		// 无主:自动购买策略裁决"是否购买"(无人值守与人玩同语义,provisional)。
		if (AutoBuyPolicy(TileIndex))
		{
			const FMADemoTileInfo Info = GS->GetTileInfo(TileIndex);
			P->DeductMoney(Info.Price);
			P->AddProperty(TileIndex);
			GS->SetTileOwner(TileIndex, P->PlayerIndex);
		}
		else
		{
			// 拒购 → 立即进入英式拍卖(GDD 2.1;增量批 1 完整实现)。
			StartAuction(TileIndex);
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

// --- 拍卖(增量批 1,GDD 2.1 英式拍卖)---

void AMADemoGameMode::StartAuction(int32 TileIndex)
{
	AMADemoGameState* GS = CachedGameState;
	if (!GS || GS->bGameOver)
	{
		return;
	}
	const FMADemoTileInfo Info = GS->GetTileInfo(TileIndex);
	// 守卫:仅无主地产可拍(评审清单 1:途经/已有主不触发)。
	if (Info.TileType != EMADemoTileType::Property || GS->GetTileOwner(TileIndex) >= 0)
	{
		return;
	}

	FMADemoAuctionState& A = GS->AuctionState;
	A.bActive = true;
	A.TileIndex = TileIndex;
	// 起拍价 = 地价 50%(GDD 2.1 锁定,数据驱动)。
	A.StartPrice = (Info.Price * GS->RulesData->AuctionStartPricePercent) / 100;
	A.HighestBid = 0;
	A.HighestBidderIndex = -1;
	// 出价资格:全体未破产玩家(破产者开场即标弃权,评审清单 5)。
	A.PassedPlayers.Init(false, GS->Players.Num());
	int32 EligibleCount = 0;
	for (int32 i = 0; i < GS->Players.Num(); ++i)
	{
		const UMADemoPlayerData* P = GS->GetPlayer(i);
		if (!P || P->bIsBankrupt)
		{
			A.PassedPlayers[i] = true;
		}
		else
		{
			++EligibleCount;
		}
	}
	A.BidLog.Empty();
	A.BidLog.Add(FString::Printf(TEXT("开拍:%s(地价 $%d,起拍 $%d)"),
		*Info.Name, Info.Price, A.StartPrice));
	// 轮转起点:落格玩家(拒购者也可参拍,现实 Monopoly 惯例,provisional)。
	A.CurrentBidderIndex = GS->CurrentPlayerIndex;
	GS->TurnPhase = EMADemoTurnPhase::Auction;
	// 留痕:拍卖开局(无人值守验证与 msc 试玩观察点)。
	UE_LOG(LogTemp, Log, TEXT("[Demo_MonopolyAuction] 拍卖开始:%s(地价 $%d,起拍 $%d),P%d 拒购"),
		*Info.Name, Info.Price, A.StartPrice, GS->CurrentPlayerIndex + 1);

	// 首场拍卖面板截图(-MADemoAuctionShotPath 指定;仅关卡上下文,纯逻辑测试无 World 不进入)。
	if (!AuctionShotPath.IsEmpty() && !bAuctionShotTaken && GetWorld() && bInteractiveContext)
	{
		bAuctionShotTaken = true;
		FTimerHandle AuctionShotHandle;
		GetWorldTimerManager().SetTimer(AuctionShotHandle, [this]()
		{
			RequestViewportScreenshot(AuctionShotPath);
		}, 1.2f, false);
	}

	// 防御:无任何有资格竞价人(理论不可达,当前玩家必未破产)→ 直接流拍。
	if (EligibleCount == 0)
	{
		FinishAuction(false);
	}
}

int32 AMADemoGameMode::GetNextBidAmount() const
{
	const AMADemoGameState* GS = CachedGameState;
	if (!GS || !GS->AuctionState.bActive)
	{
		return 0;
	}
	const FMADemoAuctionState& A = GS->AuctionState;
	// 首口价 = 起拍价;其后 = 当前最高 + 步长(GDD 2.1 加价步长 10,数据驱动)。
	return (A.HighestBidderIndex < 0)
		? A.StartPrice
		: A.HighestBid + GS->RulesData->AuctionBidStep;
}

void AMADemoGameMode::AuctionBidCurrent()
{
	AMADemoGameState* GS = CachedGameState;
	if (!GS || !GS->AuctionState.bActive || GS->bPaused)
	{
		// 暂停期间拍卖冻结(Esc 暂停语义贯穿拍卖)。
		return;
	}
	FMADemoAuctionState& A = GS->AuctionState;
	UMADemoPlayerData* Bidder = GS->GetPlayer(A.CurrentBidderIndex);
	if (!Bidder || A.PassedPlayers[A.CurrentBidderIndex])
	{
		return;
	}
	const int32 Amount = GetNextBidAmount();
	// 出价守卫:买不起拟出价则无效(玩家只能弃权;成交时支付必然可兑现)。
	if (!Bidder->CanAfford(Amount))
	{
		return;
	}
	A.HighestBid = Amount;
	A.HighestBidderIndex = A.CurrentBidderIndex;
	A.BidLog.Add(FString::Printf(TEXT("P%d 出价 $%d"), A.CurrentBidderIndex + 1, Amount));
	AdvanceAuctionTurn();
}

void AMADemoGameMode::AuctionPassCurrent()
{
	AMADemoGameState* GS = CachedGameState;
	if (!GS || !GS->AuctionState.bActive || GS->bPaused)
	{
		// 暂停期间拍卖冻结。
		return;
	}
	FMADemoAuctionState& A = GS->AuctionState;
	if (!A.PassedPlayers.IsValidIndex(A.CurrentBidderIndex)
		|| A.PassedPlayers[A.CurrentBidderIndex])
	{
		return;
	}
	// 防御:当前最高出价者不该弃权(出价即承诺;轮转设计上不会轮到领先者,理论不可达)。
	if (A.CurrentBidderIndex == A.HighestBidderIndex)
	{
		return;
	}
	A.PassedPlayers[A.CurrentBidderIndex] = true;
	A.BidLog.Add(FString::Printf(TEXT("P%d 弃权"), A.CurrentBidderIndex + 1));
	AdvanceAuctionTurn();
}

void AMADemoGameMode::AdvanceAuctionTurn()
{
	AMADemoGameState* GS = CachedGameState;
	FMADemoAuctionState& A = GS->AuctionState;

	// 未弃权人数统计。
	int32 ActiveCount = 0;
	for (bool bPassed : A.PassedPlayers)
	{
		if (!bPassed)
		{
			++ActiveCount;
		}
	}

	// 收敛 1:全员弃权(弃权粘性,provisional)→ 无人出过价则流拍保持无主(GDD 2.1)。
	if (ActiveCount == 0)
	{
		FinishAuction(A.HighestBidderIndex >= 0);
		return;
	}

	// 找下一个未弃权竞价人(环形轮转,GDD 2.1 轮流出价或弃权)。
	const int32 Count = A.PassedPlayers.Num();
	int32 Next = A.CurrentBidderIndex;
	for (int32 Probe = 0; Probe < Count; ++Probe)
	{
		Next = (Next + 1) % Count;
		if (!A.PassedPlayers[Next])
		{
			break;
		}
	}

	// 收敛 2:仅剩当前最高出价者一人(其余全弃)→ 成交(GDD 2.1 最高出价者立付获契)。
	if (ActiveCount == 1 && Next == A.HighestBidderIndex)
	{
		FinishAuction(true);
		return;
	}

	A.CurrentBidderIndex = Next;
}

void AMADemoGameMode::FinishAuction(bool bSold)
{
	AMADemoGameState* GS = CachedGameState;
	FMADemoAuctionState& A = GS->AuctionState;

	if (bSold && A.HighestBidderIndex >= 0)
	{
		// 成交:按最终出价立即支付并转移地契(复用 property_economy 支付语义;
		// 出价守卫保证买得起,DeductMoney 不会失败)。
		UMADemoPlayerData* Winner = GS->GetPlayer(A.HighestBidderIndex);
		if (Winner && Winner->DeductMoney(A.HighestBid))
		{
			Winner->AddProperty(A.TileIndex);
			GS->SetTileOwner(A.TileIndex, A.HighestBidderIndex);
			A.BidLog.Add(FString::Printf(TEXT("成交:P%d 以 $%d 拍得 %s"),
				A.HighestBidderIndex + 1, A.HighestBid,
				*GS->GetTileInfo(A.TileIndex).Name));
		}
	}
	else
	{
		// 流拍:地产保持无主(GDD 2.1;不降价重拍)。
		A.BidLog.Add(FString::Printf(TEXT("流拍:%s 保持无主"),
			*GS->GetTileInfo(A.TileIndex).Name));
	}

	A.bActive = false;
	A.CurrentBidderIndex = -1;
	// 留痕:拍卖收敛结果。
	UE_LOG(LogTemp, Log, TEXT("[Demo_MonopolyAuction] 拍卖结束:%s"),
		A.BidLog.Num() > 0 ? *A.BidLog.Last() : TEXT("(无记录)"));

	// 恢复回合流:拍卖打断的双数追加掷优先,否则停 TurnEnd 等 Enter。
	UMADemoPlayerData* P = GS->GetPlayer(GS->CurrentPlayerIndex);
	if (bPendingExtraRollAfterAuction && P && !P->bIsBankrupt && !P->bIsInJail)
	{
		GS->TurnPhase = EMADemoTurnPhase::WaitingForRoll;
	}
	else
	{
		GS->TurnPhase = EMADemoTurnPhase::TurnEnd;
	}
	bPendingExtraRollAfterAuction = false;
	CheckGameOver();
}

void AMADemoGameMode::AutoAuctionStep()
{
	AMADemoGameState* GS = CachedGameState;
	if (!GS || !GS->AuctionState.bActive)
	{
		return;
	}
	const FMADemoAuctionState& A = GS->AuctionState;
	const UMADemoPlayerData* Bidder = GS->GetPlayer(A.CurrentBidderIndex);
	const int32 Amount = GetNextBidAmount();
	const FMADemoTileInfo Info = GS->GetTileInfo(A.TileIndex);
	// 竞价缓冲与购买缓冲拆分(增量批 1):拒购门槛高、竞价意愿高,拍卖才有成交。
	const int32 Buffer = GS->RulesData->AuctionBidReserveBuffer;
	// 自动竞价策略(provisional):出价后剩余 ≥ 竞价缓冲,且拟出价不超过地价
	// (简单理性,不溢价抢拍)——满足则出价,否则弃权。
	if (Bidder && Bidder->Money >= Amount + Buffer && Amount <= Info.Price)
	{
		AuctionBidCurrent();
	}
	else
	{
		AuctionPassCurrent();
	}
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

	// 硬上限保护:防止任何逻辑缺陷死循环(回合上限 ×玩家数 ×双数/TurnEnd/拍卖多步余量,
	// 增量批 1 拍卖逐口出价计步,乘数加大)。
	const int32 HardCap = (GS->RulesData->MaxGameRounds + 10) * NumPlayers * 12;
	int32 Steps = 0;
	while (!GS->bGameOver && Steps < HardCap)
	{
		// 自动直驱:拍卖阶段按自动竞价策略推进;TurnEnd 代按 Enter;否则掷骰结算。
		if (GS->TurnPhase == EMADemoTurnPhase::Auction)
		{
			AutoAuctionStep();
		}
		else if (GS->TurnPhase == EMADemoTurnPhase::TurnEnd)
		{
			AdvanceToNextPlayer();
		}
		else
		{
			RequestRollAndResolve();
		}
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
	// 推进当前玩家到切人或终局:拍卖阶段自动竞价,TurnEnd 代按 Enter,否则掷骰结算;
	// 双数追加掷会多迭代,Guard 放宽到 64。触发拍卖即退出本次推进(归还控制权给
	// AutoPlayTick 逐口分支),让自动演示下拍卖面板过程可见。
	const int32 PlayerBefore = GS->CurrentPlayerIndex;
	int32 Guard = 0;
	do
	{
		if (GS->TurnPhase == EMADemoTurnPhase::Auction)
		{
			AutoAuctionStep();
		}
		else if (GS->TurnPhase == EMADemoTurnPhase::TurnEnd)
		{
			AdvanceToNextPlayer();
		}
		else
		{
			RequestRollAndResolve();
		}
		++Guard;
	}
	while (!GS->bGameOver && GS->CurrentPlayerIndex == PlayerBefore
		&& GS->TurnPhase != EMADemoTurnPhase::Auction && Guard < 64);
	return !GS->bGameOver;
}

void AMADemoGameMode::TogglePauseState()
{
	if (CachedGameState && !CachedGameState->bGameOver)
	{
		CachedGameState->bPaused = !CachedGameState->bPaused;
	}
}

void AMADemoGameMode::SetPauseState(bool bNewPaused)
{
	if (CachedGameState)
	{
		CachedGameState->bPaused = bNewPaused;
	}
}

bool AMADemoGameMode::IsPaused() const
{
	return CachedGameState ? CachedGameState->bPaused : false;
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
	// 拍卖期逐口推进(每 tick 仅一步,不计回合数):自动演示下拍卖面板过程对旁观者可见。
	AMADemoGameState* GS = CachedGameState;
	if (GS && !GS->bGameOver && GS->TurnPhase == EMADemoTurnPhase::Auction)
	{
		AutoAuctionStep();
		RefreshHUD();
		return;
	}

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
			// 先请求截图(带 UI),再延迟退出,给截图异步落盘留足时间。
			RequestViewportScreenshot(AutoShotPath);
			GetWorldTimerManager().SetTimer(QuitTimerHandle, this,
				&AMADemoGameMode::FinishAutoShot, 3.0f, false);
		}
	}
}
