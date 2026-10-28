# 波段確認成交量：事前受控設計

父portfolio_swing_failure_exit；不繼承斜率risk取捨或移除ATR失敗候選。queue無待辦，使用者接續研究的授權指向目前基準。先讀18項經驗；不重做放寬ATR、延長窗口、較快通道／1R價格保護。

原因：2025的波段多空仍虧；低於前20根4h平均volume的確認bar原交易，2024一般6筆−9.30USDT／雙成本7筆−17.48；2025一般6筆−26.24／雙成本6筆−34.70。跨兩年分組合計皆負，但少量樣本且含原贏家，無法視為可回收收益或預測能力。這是已觀察的調參證據，並非獨立驗證。

唯一signal改動：波段已完成確認bar的volume >= 之前20根已完成4h volume平均（不含確認bar）；等於通過，不足21根不入場。20沿用既有突破lookback，不掃倍數與長度。保留原breakout+下一4h確認、ER20>=0.3、ATR、4h20/60、fresh4h限制；只阻擋新增波段，不抑制既有持倉退出。

影響資料流：app/strategies/swing_volume.py輸出原Signal，scripts/research_portfolio_overlap.py的現有swing_entry_candidate替換波段訊號；原風控根據原stop與cost sizing後，共用cash／gross／stoprisk／margin繼續admission。原固定突破邊界失效退出完整繼承，短線三根結構與ATR門檻保留，不限制單lot，不動daily2。維持1x，每年10k、fee/slip10/5bps及double20/10bps、實際funding/mark。

完整四筆父快照與資料指紋重現後才測子候選；全部年度/成本及原贏家排除代價保留，不用舊交易PnL相減作為新策略收益。標準指標、費用、滑價、頻率與DD一併檢討。
此輪不解決短線頻率、不強迫湊筆數、不把成交量當勝率或槓桿信心。2024/2025全部調參、每年10%目標未達；保留paper/testnet/live gates與原margin/OHLC/precision限制。
