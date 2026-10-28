# 慢均線斜率衝突風險上限：事前設計

父portfolio_swing_failure_exit；四筆2024/2025正常及雙成本全部為調參證據。queue無待辦，本輪接續使用者明確指定的上一研究候選。

檢查前16項經驗，既有重疊風險遞減實驗改變同向lot數量分配且犧牲2024；方向連虧guard則保留。此輪測市場方向衝突的風險上限，不重做lot數量遞減、不改已失敗確認／退出。

父交易分組：完成4h SMA60與24小時前值的斜率不支持進場方向時，一般成本2024共10筆合計約−75.63 USDT；2025共6筆約−4.14。雙成本同組亦虧，但組內有贏家，2025不利組樣本少且效應很小。分組是已觀察調參線索，不是勝率、因果證明或可直接相減的策略收益。

唯一改動risk：用已完成4h bars最多66根；當direction*(SMA60_current-SMA60_6bars_ago)>0時上限1，否則含平坦／不足66根上限0.5。最終risk multiplier=min(原共享/方向連虧倍率,此上限)；不相乘成0.25。60沿用原慢線，6根為固定24h跨度，不掃參數。

單筆risk預算仍由止損距離、費用、slippage與funding reserve反推數量，gross/aggregate stop risk/reserved margin admission繼續有效，最低必要leverage仍1x。
不刪訊號、不改stop或出場、不改daily2與多lot，原波段固定突破失效退出完整繼承。不能稱增加交易頻率；共享風控路徑可能讓成交數不同。

影響：app/risk/regime.py產生完成bar上限 → app/backtest/portfolio_research.py在原風控後取min並保存trace → scripts/research_portfolio_overlap.py先重播四筆父完整快照再跑子候選。沒有交易所呼叫或live設定更動。

成功判斷四筆收益／DD、全部metrics、費用與原贏家縮倉代價，不預設一定改善；不能藉增加槓桿把負期望放大。2024/2025不是未見驗證，年10%目標未達，既有margin/ohlc/precision/funding輸入限制保留。
