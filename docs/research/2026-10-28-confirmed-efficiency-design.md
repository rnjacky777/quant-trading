# 確認後仍失敗：狀態診斷與單項效率過濾

2026-10-28，使用者要求繼續優化並找出確認後失敗集中在哪些行情與方向。佇列無待辦；明確父候選portfolio_pa_smc_confirmation全部四筆實驗，非另挑最高收益版本。

scripts.analyze_confirmed_failures保留data/confirmed-failure-diagnostics.json，分開2024／2025與一般／雙成本。失敗定義為扣成本後pnl<0，不等同證明價格形態假突破。行情特徵全部使用進場前完成4H：20期ER、SMA60斜率是否同向、SMA20/60間距／ATR、確認收盤是否突破原突破K線wick；另按UTC月份及出場原因拆解。不將重疊分組或成本實驗加總當獨立樣本。

一般成本2024波段多34筆+411.56、空11筆−96.28；2025多25筆−91.70、空26筆−171.92。2025短線多−114.24、空−15.60，故單改波段不能宣稱解決所有虧損。2025空單損失集中於6月4筆−58.56、8月7筆−55.51、3月2筆−48.40；月份非可交易過濾依據。2024空單ER≥0.3的8筆全虧−107.83，因此不能簡化為只在盤整虧，也不取消空單。

ER<0.3：2024多3筆−11.54、空3筆+11.56，總接近0；2025多2筆−23.31、空7筆−70.59，合計9筆−93.90。樣本很小，尚非顯著優勢，只足以支持一次候選。SMA慢斜率已同向的2025空單仍全包含26筆，故不加斜率過濾。2025確認收盤突破原wick的多空組反而更差，故不因「更強」直覺新增該條件。

只測signal變更：最近21個已完成4H收盤（20次變動），ER=abs(last-first)/sum(abs(adjacent changes))，ER<0.3時不新增波段部位。等於0.3通過；零變動路徑定義0（無方向）。固定窗口與門檻，不掃參數；其他訊號、ATR×2止損公式、10根反向通道退出、最大168h、共享10,000本金、短線PA＋SMC、多空與多部位、每日總計≤2、風險及槓桿不變。過濾只影響新進場，不阻擋已有部位退出。

公式參考[QuantConnect官方指標文件](https://www.quantconnect.com/docs/v2/writing-algorithms/indicators/supported-indicators/kaufman-efficiency-ratio)及[LEAN原始碼](https://github.com/QuantConnect/Lean/blob/master/Indicators/KaufmanEfficiencyRatio.cs)的淨移動／路徑移動概念；本實作明定20次變動與flat=0，非逐行移植或完全相同暖機／flat慣例。來源不支持0.3為最佳門檻或BTC獲利證據，此門檻只是先記錄的固定實驗。

影響app/strategies/swing_efficiency.py（只輸出Signal，不選數量）、scripts/research_portfolio_overlap.py（重播指定父候選並單項替換）、scripts/research_confirmed_efficiency.py；資料→完成4H策略→Signal→既有共享風控／資金→研究成交→保存全部曲線交易。四筆父完整快照逐一重播與指紋一致才跑候選，保存data/perpetual-confirmed-efficiency.json並保留全部失敗。2024／2025皆調參資料，不稱未見驗證。目標兩年各淨收益≥10%、回撤≤10%，不保證達標；不加槓桿，不改paper/testnet/live或下單。
