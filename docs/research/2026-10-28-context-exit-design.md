# 最新候選的一項短線退出試驗

2026-10-28，使用者要求繼續優化；queue無待辦，已讀13項研究經驗。父明確portfolio_directional_loss_guard（結構止損＋同方向連虧保護），原較早版本保留對照，不默默取消最新risk guard。

原策略有三個短線退出層：結構stop、完成4h SMA20/60方向反轉、完成1h突破反向10根通道，另有24h硬上限。實際signal退出拆解：2024一般成本10筆channel-only淨−46.24USDT；2025為8筆−5.67，其中空單組盈利+16.03，因此不是只刪除輸家。剩餘時間均值約6.5–11h，仍有可測持有差異；波段不是本輪對象。

假說：當原掃單結構仍有效、4h方向未反轉時，1h通道可能過早退出。只改exit類別：短線Signal.exit_long=完成4h fast≤slow，exit_short=fast≥slow，移除1h通道條件；保留原結構stop與24h上限。這不同於失敗的48h持有試驗，沒有放寬24h；也不同於波段通道10→5，沒有掃通道根數。

所有原進場、初始stop、波段、0.25%／0.125%風險及方向guard、gross/aggregate-stoprisk/reserved-margin、每日總計2次、費用slippage/funding與實際1x不變。改退出可使後續減倉歷史／資金／名額不同，不把父10筆虧損直接算可回收收益；保留被傷害原贏家及新增stop、funding等代價。

父四筆2024／2025正常與雙成本、243h暖機、market／mark／funding指紋與完整快照一致（含guard trace）後才跑子候選。每年10,000，全年各10%／回撤≤10%仍目標、未達標；頻率另報，不湊單。兩年與此分組都是調參，不是未見驗證。只試這一項，不在失敗後掃exit channel或holding參數。

影響app/strategies/sweep_context_exit.py（只改原Signal退出旗標，不改數量／exchange）、scripts/research_portfolio_overlap.py明確繼承父risk guard、scripts/research_context_exit.py及研究結果介面。完成市場資料→原Signal入場與結構失效＋新退出flags→原風控／guard／共享帳本→原成交引擎→獨立結果data/perpetual-sweep-context-exit.json。未改live/paper/testnet或下單。
