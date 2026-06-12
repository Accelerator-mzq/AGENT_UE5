// Copyright Phase14 demo agent.
#include "MADemoGameMode.h"
#include "MADemoGameState.h"
#include "MADemoPlayerData.h"
#include "MADemoBoardDataAsset.h"
#include "MADemoRulesDataAsset.h"
#include "MADemoStockMarket.h"
#include "MADemoPlayerController.h"

AMADemoGameMode::AMADemoGameMode()
{
	// 绑定本 demo 的 GameState/Controller 类,使标准 PIE 启动也能用本 demo 类型。
	GameStateClass = AMADemoGameState::StaticClass();
	PlayerControllerClass = AMADemoPlayerController::StaticClass();
	PrimaryActorTick.bCanEverTick = false;
}

AMADemoGameState* AMADemoGameMode::GetDemoGameState() const
{
	return CachedGameState;
}

void AMADemoGameMode::InitializeGame(int32 NumPlayers, int32 RandomSeed)
{
	// 玩家数夹到契约范围 [2,6]
	NumPlayers = FMath::Clamp(NumPlayers, 2, 6);
	RandomStream.Initialize(RandomSeed);
	ConsecutiveDoubles = 0;

	// 取/造 GameState。无 PIE(纯逻辑冒烟)时 GetGameState 可能为空,则手动 new 一个。
	CachedGameState = GetGameState<AMADemoGameState>();
	if (!CachedGameState)
	{
		CachedGameState = NewObject<AMADemoGameState>(this, AMADemoGameState::StaticClass());
	}
	AMADemoGameState* GS = CachedGameState;

	// 数据资产兜底:未在编辑器指定则用代码默认资产(数据驱动,仍可覆盖)。
	// 分支赋值而非三元,避免 TObjectPtr 与裸指针在 ?: 中类型不一致(C2445)。
	if (DefaultBoardData)
	{
		GS->BoardData = DefaultBoardData;
	}
	else
	{
		GS->BoardData = NewObject<UMADemoBoardDataAsset>(GS, UMADemoBoardDataAsset::StaticClass());
	}
	if (DefaultRulesData)
	{
		GS->RulesData = DefaultRulesData;
	}
	else
	{
		GS->RulesData = NewObject<UMADemoRulesDataAsset>(GS, UMADemoRulesDataAsset::StaticClass());
	}

	const UMADemoBoardDataAsset* Board = GS->BoardData;
	const UMADemoRulesDataAsset* Rules = GS->RulesData;

	// 初始化棋盘所有权(全无主)
	GS->TileOwners.Init(-1, Board->Tiles.Num());

	// 创建玩家
	GS->Players.Empty();
	static const FLinearColor Palette[] = {
		FLinearColor::Red, FLinearColor::Blue, FLinearColor::Green,
		FLinearColor(1,1,0), FLinearColor(1,0,1), FLinearColor(0,1,1)
	};
	for (int32 i = 0; i < NumPlayers; ++i)
	{
		UMADemoPlayerData* P = NewObject<UMADemoPlayerData>(GS, UMADemoPlayerData::StaticClass());
		P->PlayerIndex = i;
		P->DisplayName = FString::Printf(TEXT("玩家%d"), i + 1);
		P->Money = Rules->StartingCash;
		P->CurrentTileIndex = Board->StartTileIndex;
		P->PlayerColor = Palette[i % 6];
		P->StockHoldings.Init(0, 3);
		GS->Players.Add(P);
	}

	// 初始化股票市场
	GS->StockMarket = NewObject<UMADemoStockMarket>(GS, UMADemoStockMarket::StaticClass());
	GS->StockMarket->InitializeStocks(Rules);

	// 回合态归零
	GS->CurrentPlayerIndex = 0;
	GS->TurnNumber = 0;
	GS->TurnPhase = EMADemoTurnPhase::NotStarted;
	GS->WinnerIndex = -1;
	GS->AuctionState = FMADemoAuctionState();
}

void AMADemoGameMode::StartTurn()
{
	AMADemoGameState* GS = CachedGameState;
	if (!GS || GS->TurnPhase == EMADemoTurnPhase::GameOver)
	{
		return;
	}

	// 跳过已破产玩家
	int32 Guard = 0;
	while (GS->Players.IsValidIndex(GS->CurrentPlayerIndex)
		&& GS->Players[GS->CurrentPlayerIndex]->bIsBankrupt
		&& Guard++ < GS->Players.Num())
	{
		GS->CurrentPlayerIndex = (GS->CurrentPlayerIndex + 1) % GS->Players.Num();
	}

	GS->TurnNumber += 1;
	ConsecutiveDoubles = 0;
	GS->TurnPhase = EMADemoTurnPhase::WaitingForRoll;
}

FMADemoDiceResult AMADemoGameMode::RollDiceInternal()
{
	const UMADemoRulesDataAsset* Rules = CachedGameState ? CachedGameState->RulesData : nullptr;
	const int32 Sides = Rules ? Rules->DiceSides : 6;
	FMADemoDiceResult R;
	R.Die1 = RandomStream.RandRange(1, Sides);
	R.Die2 = RandomStream.RandRange(1, Sides);
	R.Sum = R.Die1 + R.Die2;
	R.bIsDouble = (R.Die1 == R.Die2);
	return R;
}

void AMADemoGameMode::RequestRollAndResolve()
{
	AMADemoGameState* GS = CachedGameState;
	if (!GS || GS->TurnPhase == EMADemoTurnPhase::GameOver)
	{
		return;
	}
	UMADemoPlayerData* Player = GS->GetPlayer(GS->CurrentPlayerIndex);
	if (!Player || Player->bIsBankrupt)
	{
		return;
	}
	const UMADemoRulesDataAsset* Rules = GS->RulesData;

	// 掷骰
	const FMADemoDiceResult Dice = RollDiceInternal();
	GS->LastDiceResult = Dice;

	// GDD 2.2:每回合开始按当轮掷骰结果对股票波动(放在掷骰得到结果后)
	if (GS->StockMarket && Rules)
	{
		GS->StockMarket->ApplyTurnSwing(Dice.Sum, Rules->StockSwingRatio);
	}

	GS->TurnPhase = EMADemoTurnPhase::Resolving;

	// 监狱处理:在狱中先决定能否移动
	if (Player->bIsInJail)
	{
		const bool bCanMove = HandleJailTurnStart();
		if (!bCanMove)
		{
			// 仍在狱中,本回合结束(不移动)
			GS->TurnPhase = EMADemoTurnPhase::TurnEnd;
			return;
		}
	}

	// 双数处理:连续双数计数
	if (Dice.bIsDouble && Rules && Rules->bDoublesGrantExtraTurn)
	{
		ConsecutiveDoubles += 1;
		// 三连双数直接入狱(契约 dice.triple_doubles_jail)
		if (Rules->bTripleDoublesJail && ConsecutiveDoubles >= 3)
		{
			HandleGoToJail();
			GS->TurnPhase = EMADemoTurnPhase::TurnEnd;
			return;
		}
	}
	else
	{
		ConsecutiveDoubles = 0;
	}

	// 移动并结算落点事件
	MoveCurrentPlayer(Dice.Sum);

	// 若破产或游戏结束则不再继续
	if (GS->TurnPhase == EMADemoTurnPhase::GameOver)
	{
		return;
	}

	// 双数可再掷:保持 WaitingForRoll;否则回合结束
	const bool bExtraTurn = Dice.bIsDouble && Rules && Rules->bDoublesGrantExtraTurn
		&& ConsecutiveDoubles < 3 && !Player->bIsInJail && !Player->bIsBankrupt;
	GS->TurnPhase = bExtraTurn ? EMADemoTurnPhase::WaitingForRoll : EMADemoTurnPhase::TurnEnd;
}

void AMADemoGameMode::MoveCurrentPlayer(int32 Steps)
{
	AMADemoGameState* GS = CachedGameState;
	UMADemoPlayerData* Player = GS->GetPlayer(GS->CurrentPlayerIndex);
	const UMADemoBoardDataAsset* Board = GS->BoardData;
	const UMADemoRulesDataAsset* Rules = GS->RulesData;
	if (!Player || !Board)
	{
		return;
	}

	const int32 Count = Board->Tiles.Num();
	const int32 Old = Player->CurrentTileIndex;
	const int32 New = (Old + Steps) % Count;

	// 过/达起点奖励:绕圈则新位置 < 旧位置(GDD 3.1 step 3)
	if (New < Old || New == Board->StartTileIndex)
	{
		Player->AddMoney(Rules ? Rules->StartBonus : 200);
	}
	Player->CurrentTileIndex = New;

	OnPlayerLanded(New);
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
	default:
		// Start/JailVisit/FreeParking/Chance/Community/Exchange:Phase 1 无强制结算
		break;
	}
}

void AMADemoGameMode::HandlePropertyTile(int32 TileIndex)
{
	AMADemoGameState* GS = CachedGameState;
	UMADemoPlayerData* Player = GS->GetPlayer(GS->CurrentPlayerIndex);
	// 局部命名 OwnerIndex 避免遮蔽 AActor::Owner(C4458)
	const int32 OwnerIndex = GS->GetTileOwner(TileIndex);
	const FMADemoTileInfo Info = GS->GetTileInfo(TileIndex);

	if (OwnerIndex < 0)
	{
		// 无主:自动购买策略(无人值守);拒购在 v0 不触发拍卖(拍卖在 increment-1)
		if (AutoBuyPolicy(Player, TileIndex))
		{
			Player->DeductMoney(Info.Price);
			Player->AddProperty(TileIndex);
			GS->SetTileOwner(TileIndex, Player->PlayerIndex);
		}
		// 否则放弃,无事发生(GDD 3.2 Phase 1 不做拍卖)
	}
	else if (OwnerIndex == Player->PlayerIndex)
	{
		// 自己拥有:无事
	}
	else
	{
		// 他人拥有:付租
		UMADemoPlayerData* OwnerPlayer = GS->GetPlayer(OwnerIndex);
		const int32 Rent = GS->CalculateRent(TileIndex);
		ProcessPayment(Player, OwnerPlayer, Rent);
	}
}

void AMADemoGameMode::HandleTaxTile(int32 TileIndex)
{
	AMADemoGameState* GS = CachedGameState;
	UMADemoPlayerData* Player = GS->GetPlayer(GS->CurrentPlayerIndex);
	const FMADemoTileInfo Info = GS->GetTileInfo(TileIndex);
	// 税务格 Price 字段复用为缴税金额,付给银行(Owner 为空)
	ProcessPayment(Player, nullptr, Info.Price);
}

void AMADemoGameMode::HandleGoToJail()
{
	AMADemoGameState* GS = CachedGameState;
	UMADemoPlayerData* Player = GS->GetPlayer(GS->CurrentPlayerIndex);
	const UMADemoRulesDataAsset* Rules = GS->RulesData;
	if (!Player)
	{
		return;
	}
	// 立即移到监狱探访格,标记在狱(不过起点不领奖,GDD GO_TO_JAIL)
	Player->CurrentTileIndex = Rules ? Rules->JailVisitTileIndex : 7;
	Player->bIsInJail = true;
	Player->JailTurnsRemaining = Rules ? Rules->JailMaxTurns : 3;
	ConsecutiveDoubles = 0;
}

bool AMADemoGameMode::HandleJailTurnStart()
{
	AMADemoGameState* GS = CachedGameState;
	UMADemoPlayerData* Player = GS->GetPlayer(GS->CurrentPlayerIndex);
	const UMADemoRulesDataAsset* Rules = GS->RulesData;
	if (!Player || !Player->bIsInJail)
	{
		return true;
	}
	const int32 Bail = Rules ? Rules->JailBailCost : 50;

	// 本回合掷骰已发生(LastDiceResult);掷出双数则免费出狱
	if (GS->LastDiceResult.bIsDouble)
	{
		Player->bIsInJail = false;
		Player->JailTurnsRemaining = 0;
		return true; // 用本次骰子点数正常移动
	}

	Player->JailTurnsRemaining -= 1;
	if (Player->JailTurnsRemaining <= 0)
	{
		// 满 3 回合未掷双:强制付保释出狱(GDD 监狱规则)
		ProcessPayment(Player, nullptr, Bail);
		Player->bIsInJail = false;
		Player->JailTurnsRemaining = 0;
		// 破产可能在 ProcessPayment 内发生
		return !Player->bIsBankrupt;
	}
	// 仍在狱中,本回合不移动
	return false;
}

void AMADemoGameMode::ProcessPayment(UMADemoPlayerData* Payer, UMADemoPlayerData* Creditor, int32 Amount)
{
	if (!Payer || Amount <= 0)
	{
		return;
	}
	if (Payer->CanAfford(Amount))
	{
		Payer->DeductMoney(Amount);
		if (Creditor)
		{
			Creditor->AddMoney(Amount);
		}
	}
	else
	{
		// 不足额:把现金尽数转给债主后破产(简化清算)
		if (Creditor)
		{
			Creditor->AddMoney(Payer->Money);
		}
		Payer->Money = 0;
		EliminatePlayer(Payer);
	}
}

void AMADemoGameMode::EliminatePlayer(UMADemoPlayerData* Player)
{
	AMADemoGameState* GS = CachedGameState;
	if (!Player || Player->bIsBankrupt)
	{
		return;
	}
	Player->bIsBankrupt = true;
	// 其地产全部归无主(GDD 3.3)
	for (int32 PropIdx : Player->OwnedProperties)
	{
		GS->SetTileOwner(PropIdx, -1);
	}
	Player->OwnedProperties.Empty();
	CheckGameOver();
}

void AMADemoGameMode::CheckGameOver()
{
	AMADemoGameState* GS = CachedGameState;
	if (GS->GetActivePlayerCount() <= 1)
	{
		// 找出唯一存活者为胜者
		for (const TObjectPtr<UMADemoPlayerData>& P : GS->Players)
		{
			if (P && !P->bIsBankrupt)
			{
				GS->WinnerIndex = P->PlayerIndex;
				break;
			}
		}
		GS->TurnPhase = EMADemoTurnPhase::GameOver;
	}
}

void AMADemoGameMode::AdvanceToNextPlayer()
{
	AMADemoGameState* GS = CachedGameState;
	if (!GS || GS->TurnPhase == EMADemoTurnPhase::GameOver)
	{
		return;
	}
	GS->CurrentPlayerIndex = (GS->CurrentPlayerIndex + 1) % GS->Players.Num();
}

bool AMADemoGameMode::IsGameOver() const
{
	return CachedGameState && CachedGameState->TurnPhase == EMADemoTurnPhase::GameOver;
}

bool AMADemoGameMode::AutoBuyPolicy(UMADemoPlayerData* Player, int32 TileIndex) const
{
	AMADemoGameState* GS = CachedGameState;
	if (!Player || !GS)
	{
		return false;
	}
	const FMADemoTileInfo Info = GS->GetTileInfo(TileIndex);
	// 保守策略:买得起且买后留够保释金缓冲再买,避免立即破产死循环
	const int32 Buffer = GS->RulesData ? GS->RulesData->JailBailCost : 50;
	return Player->CanAfford(Info.Price + Buffer);
}

int32 AMADemoGameMode::RunFullGameToCompletion()
{
	AMADemoGameState* GS = CachedGameState;
	if (!GS)
	{
		return -1;
	}
	const int32 MaxTurns = GS->RulesData ? GS->RulesData->MaxTurnsBeforeStalemate : 200;

	// 主循环:逐回合驱动直到 GameOver 或达回合上限(僵局收敛)
	while (!IsGameOver() && GS->TurnNumber < MaxTurns)
	{
		StartTurn();
		// 一个玩家回合内可能因双数多次掷骰
		int32 RollGuard = 0;
		while (GS->TurnPhase == EMADemoTurnPhase::WaitingForRoll && RollGuard++ < 10)
		{
			RequestRollAndResolve();
		}
		if (IsGameOver())
		{
			break;
		}
		AdvanceToNextPlayer();
	}

	// 达回合上限未分胜负:按净资产判最高者为胜(僵局收敛,provisional 规则)
	if (!IsGameOver())
	{
		int32 BestIdx = -1;
		int32 BestWorth = -1;
		for (int32 i = 0; i < GS->Players.Num(); ++i)
		{
			if (GS->Players[i] && !GS->Players[i]->bIsBankrupt)
			{
				const int32 W = GS->GetPlayerNetWorth(i);
				if (W > BestWorth)
				{
					BestWorth = W;
					BestIdx = i;
				}
			}
		}
		GS->WinnerIndex = BestIdx;
		GS->TurnPhase = EMADemoTurnPhase::GameOver;
	}

	return GS->WinnerIndex;
}
