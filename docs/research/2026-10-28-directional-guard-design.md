# 結構止損候選上的同方向連虧保護

2026-10-28，使用者要求繼續微調回測提升收益。queue無待辦，已讀12項研究經驗；明確父候選portfolio_sweep_structural_stop，不換回較差模型或挑最佳期間。

先診斷結構stop是否過近：多單較窄組虧損不等於加ATR下限會改善，2024一般成本該組相對舊ATR對照仍較好。因此本輪不掃ATR倍數或buffer，也不更改止損。

第二項診斷逐筆重建每次准入前已知的平倉PnL。前bar已平倉可用；當bar只納入開盤訊號／時間退出及確實跳空穿stop的開盤退出，不納入之後的盤中stop。依重建共享multiplier呼叫原_open，乘原admission.scale後，四筆全部101／101／85／85次planned_risk均重現一致。原四筆無強平／保護stop／同向risk decay，故重建範圍明確。

原共享紀錄只按sleeve合併多空；相反方向盈利可解除共享連虧減倉，即使當前方向尚未有盈利。若額外要求同方向減倉，父四筆會影響6／5／10／8筆，凍結父PnL合計−91.44／−74.44／−64.10／−37.93USDT。這是事後診斷，不當可得收益：2025一般成本組含贏家，群組非隨機、成本案例重疊，樣本小。

唯一risk類別變更：brake=min(原sleeve共享連虧multiplier, 同sleeve且同方向連虧multiplier)。沿用原兩次虧損後0.5、直到盈利才解除，零PnL不解除；不是把兩個0.5相乘成0.25。原共享減倉仍保留，不將原半倉直接恢復滿倉。不改risk 0.25%上限（減倉後0.125%），不改gross/stoprisk/reserved-margin與每日總計2次，不改槓桿，不把連虧當勝率或信心。

結構stop、全部原多空訊號與退出、波段、持有時間、成本與funding不變。同一已知歷史下此guard只維持／降低預算，但實際新帳戶路徑可改變後續平倉次序、損益正負、名額與大小，不能宣稱每個相同時間的qty一定小於父，也不能拿凍結父群組直接除半當候選收益。

影響app/risk/regime.py純風控函式、app/backtest/portfolio_research.py預設關閉的guard及准入審計trace、scripts/research_portfolio_overlap.py精確重建結構父與risk替換、固定入口scripts/research_directional_guard.py。資料→原Signal及結構失效位→原風險預算＋保守方向guard→共享資金／原成交→獨立快照；不讓策略選數量或接exchange。observer提供深拷貝，避免新trace被旁路修改。

父四筆2024／2025正常與雙成本、243h暖機、行情／mark／funding指紋及完整快照一致才跑子候選；預設關閉必須與父一致。每年10,000、實際槓桿核對1x，結果data/perpetual-directional-loss-guard.json；完整收益／回撤／費用／風險／頻率與被削減原贏家一併保存。兩年皆調參非未見，目標年淨10%／回撤10%未保證，若失敗不掃連虧次數或倍率。

這是研究引擎風控能力，不宣稱paper/testnet/live支援；未改交易設定、未下單。
