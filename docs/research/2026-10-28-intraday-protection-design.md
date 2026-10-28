# 短線+1R價格保護：事前設計

父portfolio_swing_failure_exit，未沿用斜率cap／成交量取捨或ATR消融失敗版本。queue無待辦，使用者針對止盈止損要求檢討優化。先讀19項研究經驗；原swing_price_protection在波段上犧牲2024，不能視為通用優勢，也不能聲稱這次已證明更好。

新scope與證據：本次只改短線；已換成三根結構確認＋掃單極值stop且父已有波段失效退出。原交易的完成1h收盤（不含退出小時）達+1R後，2024一般短線6筆中1筆最後stop−24.68；2025一般5筆中1筆stop−11.27。2025雙成本未有該類stop，cost與成交價不同會改觸發；完整保留。這些稀少例子是調參線索，不是可回收收益。
不選固定2R止盈：完成收盤達2R的原短線2024三筆、2025兩筆全部盈利，總淨166.81／167.40USDT，硬上限可能截斷主要贏家。

唯一exit變更：每筆intraday以進場實際成交價與初始stop距離為1R；所有當根盤中stop/強平先處理，存活lot的完成1h收盤若達+1R，將stop向進場價提高（空單降低），下一小時才有效。未完成bar、wick達標不算，stop不放寬。跳空穿過新stop按開盤成交；包含原slip/fee/funding，因此不保證淨保本。
不改波段stop/退出、原短線channel/24h、進場形態/ATR、loss guard、shared gross/stoprisk/margin、daily2、1x。保留初始stop在trade，變更在admission.stop_updates。原多lot可各自啟動，不互改邊界。

影響：app/backtest/portfolio_research.py用現有完成收盤價格保護機制、獨立新增短線flag（預設false）；scripts/research_portfolio_overlap.py只啟用該exit，先重播四筆父完整快照與data fingerprints。策略訊號及最終數量風控路徑保留，無交易所或live變更。

同每年10k，正常單邊fee/slip10/5bps與double20/10bps，實際mark/funding。四筆比較所有metrics、DD、費用/曝險/頻率、被提前退出原贏家；不將舊PnL相減當候選收益。不掃1R附近參數。2024/2025與這份診斷都是調參，非未見驗證，10%目標未達，原OHLC/歷史margin未驗證限制保留。
