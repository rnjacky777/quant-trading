# 掃單結構策略的舊ATR門檻消融：事前設計

研究父版本仍為portfolio_swing_failure_exit，不繼承上一輪斜率risk取捨候選。queue無待辦，本輪由使用者接續優化授權。先讀17項研究經驗：延長確認窗口、替換回撤進場皆失敗，不重做；上一風險cap沒有產生新訊號優勢。

發現：短線初始stop改為掃單極值後，generate仍保留原ATR14/close>=0.006。此門檻原與2ATR stop一起引入，但現在獨立於結構失效位置。假說是它可能錯排除符合完整掃單/三根確認的低ATR機會；不預設低ATR收益較好。

事前原始訊號診斷data/atr-gate-diagnostics.json：2024原19個，額外7個；2025原16個，額外13個。新增形態stop距離中位數2024多1.090%/空1.117%，2025多0.879%/空0.731%。這是已知確認收盤距離，不是成交量或盈利；尚未套daily2、gap、共用風控與退出。仍遠低於每日1–2，不把門檻當頻率主因。

唯一signal變更：短線minimum_atr_fraction由0.006改0；保留ATR計算但不以其固定百分比阻擋結構形態。其他4h20/60、掃單20、三根結構、強收盤、結構stop、原短線channel/24h、swing ER/固定突破失效退出、loss guard、共享gross/stoprisk/margin、1x、daily2均不變。
風控仍用實際stop、原費用與滑價/funding reserve反推數量，不直接加倉位；保留低stop距離造成費用占風險較高的代價。一般費/滑價10/5bps，double20/10bps，實際mark/funding。每年10k。

影響資料流：app/strategies/directional_intraday.py提供原值不變的門檻屬性；sweep_no_atr_floor.py覆寫單一參數；scripts/research_portfolio_overlap.py重現四筆父完整快照再套短線新策略；後續風控與execution模擬原流程。未動live/paper/testnet。

全部2024/2025與診斷均調參，不是未見驗證。四筆收益/DD/交易數/費用及價差一起判斷，不能從刪舊結果或新增訊號固定未來收益推算策略回報。若成本壓力下退步就記錄未採用，不掃附近ATR門檻以湊歷史收益。
