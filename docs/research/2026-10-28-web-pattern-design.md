# 外部策略與圖形：來源比較及一項可重現假說

2026-10-28。使用者明確要求搜尋網路策略及圖形判斷並調整。queue無待辦，先讀14項研究經驗；父仍保留portfolio_directional_loss_guard，不採最新失敗的移除通道退出。先做來源研究，再記錄此signal候選，不根據結果掃參數。

## 可追溯來源與不直接照抄的部分

1. [LuxAlgo作者Liquidity Sweeps](https://www.tradingview.com/script/JRqryeJ5-Liquidity-Sweeps-LuxAlgo/)：舊高低被突破後收回的價格形態，與目前基準相近；不是新優勢證據，不因重新命名而重測相同規則。
2. [LuxAlgo作者Session Sweeps](https://www.tradingview.com/script/KdOv0Dfq-Session-Sweeps-LuxAlgo/)：掃單後等結構轉向，示例另含FVG回測與交易時段。原示例是外匯／5分鐘，不支持BTC1h收益；本輪只借用結構確認概念，沒有時段、FVG或limit fill假設。
3. [LuxAlgo作者Market Structure](https://www.tradingview.com/script/kMDlPZuz-Market-Structure-with-Inducements-Sweeps-LuxAlgo/)：區分wick掃過與收盤確認結構，使用swing／trailing高低。不能把後續確認的swing回填成當時已知；本輪不使用需要未來資料的pivot。
4. [mickes作者Turtle soup指標](https://www.tradingview.com/script/AmpHKmaz-Turtle-soup/)：高週期pivot假突破加CHoCH等確認。這是作者自己的公開指標，不稱Connors／Raschke原版；不將其pivot／多根假突破設定默默等同目前單根掃單。
5. [Liu與Tsyvinski原研究](https://www.nber.org/papers/w24877)及[論文](https://www.nber.org/system/files/working_papers/w24877/w24877.pdf)：日／週動能與加密貨幣特定因素，無法直接證明1h SMC圖形或扣成本BTC合約策略。沒有套其歷史收益或宣稱複現。

網路搜尋也出現大量二手Turtle Soup教學、勝率宣稱與交易截圖，未用作參數或盈利證據。找到的ATAA演講由Neil Wrightson主講，不誤稱為Raschke本人資料。沒有取得原作者日線四日age細節的可靠原版，因此不以二手說法新增age過濾。沒有複製公開腳本代碼或下載付費書籍。

## 單項候選：原掃單後更完整的微結構確認

原規則只要求確認close越過掃單bar極值。本輪只加一項signal條件：多單確認close嚴格高於確認bar之前3根已完成1h的最高high；空單嚴格低於同3根最低low。包含掃單bar及它之前2根，不包含確認bar、不使用未完成4h或未來pivot。相等／只有wick穿過不算。

3根是本次固定工程定義，不是宣稱LuxAlgo或mickes的原設定，也不是完整CHoCH／BOS／FVG實作或智慧資金識別。這個rolling過去結構代理與舊『強收盤』條件不同，後者仍照原保留；不加其他指標、不掃3／5／10直到盈利。不把圖上漂亮例子當成功率。

結構low／high初始stop、原1h通道／4h反轉／24h上限、波段、同方向連虧guard、單筆0.25%／0.125%risk、每日合計2次、gross／stoprisk／reserved margin、費率slippage／funding與實際1x均不變。新條件可能減少機會／錯過贏家；不聲稱同時滿足每日1–2次頻率偏好。

父完整2024／2025一般與雙成本、243h暖機、指紋及完整快照（含guard trace）一致後跑候選，保存全部失敗與被排除原贏家。年本金10,000、目標各年淨10%／回撤10%仍未達；兩年與外部假說選擇都是調參，非未見驗證。圖形僅用完成K線作機械判定，沒有用未來路徑挑圖。

影響app/strategies/sweep_structure_confirm.py（只改entry_conditions，依然Signal不選qty／exchange）、scripts/research_structure_confirm.py及研究介面／報告。資料→完成1h及4h→原掃單＋三根微結構門檻→原結構stop及risk guard→共享資金／原成交→獨立結果data/perpetual-sweep-structure-confirm.json。未改live/paper/testnet，未下單。
