# 完整訊號診斷：固定基準、不先調參

2026-10-28，使用者要求開始前述完整訊號診斷。queue無標記待辦，已查閱10項研究經驗。明確固定portfolio_confirmed_efficiency，全部2024／2025及一般／雙成本，原243h暖機及資料指紋，沒有選最高收益期間或更換候選。

範圍：每個完成1h後的合格非HOLD Signal（短線／波段、多／空），用研究引擎的當時真實狀態標記accepted、rejected及原因、open_exit_cooldown、方向不允許。observer預設關閉，回傳完整結果必須仍與保存父快照完全相同；原資料指紋先核對。觀察器只接收當時的複本，不參與決策、不改順序或帳本。所有實際成交position_id須一對一出現在accepted事件中，不遺漏原本無admission的退出當根訊號。

固定4／12／24h事件觀察：訊號已知後下一根1h開盤為entry，entry+H小時的開盤為exit。按多空方向計算價格、同父費率的進出slippage／fee與實際funding，正規化為1單位entry-fill名目本金，不選數量、不加槓桿。funding採entry_time<實際時間≤exit_time，與此研究開盤新單不付開盤那筆、退出舊單先付該筆的時間邊界一致。正常與雙成本各自計算。

這不是策略回測：固定時間事件沒有原止損、訊號退出、強平、共享資金、總風險或每日名額約束，也不複利；不能把事件平均或總和當年度可交易收益。完整策略淨收益和所有原指標另外列示，仍以保存快照與重播結果為準。含被拒絕訊號只為診斷，不把它們補作成交或建議放寬風控。

若endpoint不在同一研究年度或無資料，保留事件與各horizon的censored標記，不把12月尾巴偷偷漏掉，也不拿2025資料補2024事件。所有事件按sleeve／direction／all、accepted、rejected、skipped及reason分組，報數量、可觀察數、被截尾數、日數、平均／中位數淨變化、正變化比率。重疊訊號非獨立樣本；另按每組時間先後、間隔至少H選非重疊窗口作敏感度，仍不稱統計獨立或顯著性。

進場時特徵只用完成資料：4h ER20、簡單1h ATR14／close、下一根開盤相對訊號close的方向性gap（此為執行時才知，不是訊號決策前特徵）。本輪不以這些分組調門檻、不新增策略版本、也不宣稱驗證通過。2024／2025及此診斷皆調參資料，非未見驗證；未登記新未見期間、不下載未授權來源或下單。

影響app/backtest/portfolio_research.py的預設關閉觀察器、app/backtest/signal_diagnostics.py固定horizon計算、scripts/research_all_signals.py執行與報告。市場資料→原Signal→原風控／帳本／成交結果，旁路複本→事後事件分析→獨立JSON及報告。結果data/all-signal-diagnostics.json，審計data/all-signal-audit.json。不改exchange/paper/testnet/live。
