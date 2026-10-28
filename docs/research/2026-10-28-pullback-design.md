# 對稱趨勢回撤恢復：短線替換設計

使用者要求執行上輪下一步。2026-10-28，queue無待辦。明確沿用未採失敗三小時窗口前的portfolio_confirmed_efficiency父候選全部四筆資料。以backtest-strategy-optimizer的父重播、單類變更、完整成本證據原則進行。

上輪3h延長確認增加交易卻降低兩年各成本收益，故不再掃等待根數。新假說：短線用較常見的趨勢回撤恢復事件，取代稀少掃過20根極值事件，有機會增加合格機會，但不預設有正期望。之前現貨僅多單pullback曾失敗；本輪是不同的BTC永續多空／共享多部位／成本風控上下文重測，不宣稱首次發明或因改名而有效。

只有signal類別改動：4h SMA20>60時，上一根1h收盤低於當時1h SMA20，現在收盤嚴格回到當前SMA20以上，且綠K、收在上三分之一則做多；空單對稱。SMA只用各自當時完成收盤，相等不算交叉。原ATR14/close≥0.006、ATR×2止損公式、反向10根通道／4h趨勢退出、24h持有、波段與資金風控不變。完成當根才發Signal，下一根1h開盤執行，不強制湊單。每個新的均線交叉事件可進場，共享每日最多2次與風險上限。

先執行analyze_pullback_opportunities，只計原始事件、ATR後事件與當時ATR相對來回固定成本比，不用未來最大漲幅篩選。ATR是波動，非預期收益；成本比不含funding、不保證足以賺錢。若有可測事件，再跑四筆2024／2025與一般／雙成本；原父指紋和完整快照必須一致，候選與父分開保存。每年10,000，本輪不加槓桿，目標每年10%／回撤10%，另報短線日均與活躍天，兩年皆已調參非未見驗證。

影響app/strategies/directional_pullback.py、scripts/analyze_pullback_opportunities.py、scripts/research_directional_pullback.py與研究目錄／合約研究候選標籤。資料→完成1h／4h→策略Signal→原共享風控／資金→研究成交→全部曲線與逐筆交易；不改exchange/paper/testnet/live，不下單。
