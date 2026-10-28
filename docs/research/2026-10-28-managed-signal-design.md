# 保留止損及訊號退出的逐訊號診斷

2026-10-28，使用者要求繼續分析改善淨收益。queue無待辦，讀11項研究經驗；原portfolio_confirmed_efficiency仍固定，所有2024／2025、一般與雙成本都保留，不重試已失敗濾網。

上輪證據：固定24h均值與有止損的實際結果不能互換，且移除訊號會改變連虧減倉／共享名額與資金。先做單訊號獨立診斷而非再次根據固定窗口均值挑門檻。

每個原合格Signal（含原被拒／退出當根跳過）用原PortfolioResearchEngine單獨開一筆，保留原Signal的初始止損、未來當時完成資料的exit flags、24h／168h上限、下一根開盤、funding、mark強平與成本／滑價。wrapper只禁止其後新進場，不修改退出，不使用未來資料產生原Signal。預先計算的各時點Signal均只用該時點以前的完成資料，查表只按當時時間；不是將未來exit答案傳給入場。

為排除帳戶路徑，每筆獨立初始10,000、原risk 0.25%、loss_brake=False、原gross/stoprisk/margin控制，不與其他事件競爭。這是診斷設定，不是策略候選；全部候選依舊保留原連虧減倉。單筆以net/entry-notional與net/planned-risk呈現，不能加總成年收益。事件互相重疊、非統計獨立。年底依原引擎close/end_of_data保留並標註，不估填。實際1x核對。

關鍵核對：原已成交事件的入場價、退出時間／價／原因、初始止損，及每單位qty費用／funding／PnL應與父交易完全相同（只允許數量隨診斷固定風險不同）。若不相同先停下修正，不拿不一致診斷調參。原被拒事件的獨立結果只是反事實，不代表放寬風控可成交獲利。

另對短線掃單檢查止損相對形態：原掃單位於signal前一根1h，當時就已知高／低；多單ATR止損若高於掃單low、空單若低於掃單high，屬形態區間內。若ATR止損退出當根的完整low仍高於掃單low（空單反向），則該bar整段也未觸及形態極值；若同bar有觸及，只記錄未知順序，不推定未失效。此特徵僅描述，不先改止損。

資料來源及原完整回測重播審計先核對SHA256，並重算原指紋與完整訊號集合。影響app/backtest/frozen_entry.py與scripts/research_managed_signals.py，原資料→原Signal→獨立診斷wrapper→原風控／引擎→獨立結果；沒有修改策略或原共享帳本，不下單不改live/paper/testnet。輸出data/managed-signal-diagnostics.json及研究報告。兩年均調參、不是未見驗證。若診斷支持下一項止損試驗，另寫精確假說後才回測，不自動選最好參數。
