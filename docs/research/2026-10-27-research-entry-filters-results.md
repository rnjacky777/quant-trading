# 從外部研究提出新假設：合約多空進場濾網結果

2026-10-27。依使用者要求，失敗後查閱其他資料而非重複微調同一組均線；並將做多／做空設為合約研究預設能力。已更新AGENTS.md，不改現貨市場的物理限制或實際下單權限。

本輪查閱三個主要研究來源，固定兩個新的進場假設，各自從R1多空基準比較，不疊加，不掃描小時／週幾／量能倍數。兩者都未達2024／2025各年淨收益10%、最大回撤10%的目標。時段濾網大幅降低歷史虧損，但仍不是淨獲利策略。

## 外部資料與取捨

1. [Concretum季節性研究](https://concretumgroup.com/seasonality-in-bitcoin-intraday-trend-trading/)描述其多空趨勢基準在紐約週日晚間到週一較強，但報告為扣費前，模型也不同。因此只取固定時段作本策略的進場假設，不套用其績效。
2. [Shen等人日內動能研究](https://onlinelibrary.wiley.com/doi/abs/10.1111/fire.12290)將成交量用於交易時段定義，描述高量／波動時段與動能關係。這裡改寫為突破1h成交量高於前20根均量，不是其半小時模型的重現。
3. [Wu與Pinsky時段研究](https://www.mdpi.com/1911-8074/19/9/692)包含多空動能／反轉，但成本條件低於本模型，且作者披露BTC訓練選擇沒有在獨立時段延續優勢。本輪不採全樣本最高收益規則。

## 固定規則

- asia_session：只在紐約週日19:00至週一19:00前接受新進場；依IANA America/New_York處理夏令時間。冬季起點為週一00UTC，夏季為週日23UTC。這是進場限制，原持倉仍可在時段外持有至退出，並非原研究每小時損益季節性的完全重現。
- volume_confirmation：完成的觸發1h成交量嚴格高於此前20根均量，當根不納入均值；相等不確認。多空適用同一條件，退出不受限制。
- 其他維持R1：4H20/60方向、1H20通道突破、ATR0.6%濾網、強收盤、ATR14×2止損、10根相反通道或方向失效退出、24h、每日合計2次、風險0.25%／連虧後0.125%、曝險50%。最低必要槓桿仍全部1x。

## 完整曆年一般成本

每年重設10,000 USDT，UTC完整2024／2025，含單邊費10bps、滑價5bps及實際資金費；最大回撤依小時標記收盤，盤中可能更大。

|方案|2024淨收益|2024回撤|2024筆數|2025淨收益|2025回撤|2025筆數|
|---|---:|---:|---:|---:|---:|---:|
|多空突破R1|-3.308%|-3.983%|113|-4.191%|-4.786%|75|
|固定時段濾網|-0.382%|-1.554%|23|-1.276%|-1.619%|20|
|成交量確認|-3.586%|-3.925%|110|-3.827%|-4.424%|71|

## 所有新實驗（含雙倍成本）

|年|條件|成本倍數|收益|回撤|交易數|多／空筆數|淨資金費|
|---|---|---:|---:|---:|---:|---|---:|
|2024|asia_session|1|-0.382%|-1.554%|23|13／10|-6.69|
|2024|volume_confirmation|1|-3.586%|-3.925%|110|68／42|-14.19|
|2024|asia_session|2|-0.953%|-1.624%|23|13／10|-5.86|
|2024|volume_confirmation|2|-5.632%|-5.884%|110|68／42|-12.54|
|2025|asia_session|1|-1.276%|-1.619%|20|7／13|+0.08|
|2025|volume_confirmation|1|-3.827%|-4.424%|71|27／44|+0.41|
|2025|asia_session|2|-1.491%|-1.733%|20|7／13|+0.08|
|2025|volume_confirmation|2|-4.867%|-5.167%|71|27／44|+0.36|

判斷：時段濾網改善兩年虧損與回撤，代價為樣本降至23／20筆；不表示識別到可靠優勢。成交量確認未穩定改善。因全部正常與雙成本結果仍虧損，不提高風險或槓桿來追逐目標，不建立自稱已獲利的交易版本。

## 資產曲線與逐筆多空結果

Dashboard新增「合約多空研究」入口：/derivatives-research，預設多空雙向，可切換完整年度、方向對照及一般／雙倍成本。每筆可查看資產曲線、績效與明確標示方向的交易。此頁只讀保存結果，不下單，不代表已開通實際合約交易，也不把空單塞入現貨只做多紀錄。

研究目錄讀取R1原12筆及本輪8筆，共20筆；預設只顯示雙向與所選成本。快照以完整內容SHA256識別，未知識別碼404，損壞來源503明確報錯，不靜默省略失敗證據。

## 可重現性與完整指標

- 設計先保存於2026-10-27-research-entry-filters-design.md；原R1四筆both證據重跑與完整序列化快照完全相同，再計算每個新條件。
- 三種來源指紋（成交、標記、funding）與原R1完全一致，資金、暖機及成本相同，沒有挑掉虧損區間。原資料及結果保留。
- 結果data/perpetual-entry-filters.json含全部CAGR、Sharpe、Sortino、回撤、勝率、profit factor、平均盈虧、交易數、曝險、費用、滑價、funding、強平指標、完整交易與資產曲線。
- data/perpetual-entry-filters-audit.json記錄程式來源SHA256、時區資料版本、各情境多空筆數、每日上限及目標判定。全部8筆資金帳核對、每日≤2、持倉≤24h、名目曝險≤50%，且都維持1x。
- 重現：python -m scripts.research_perpetual_entry_filters。沒有參數搜尋。正常／雙成本是同年度情境，不是獨立樣本。

## 完整新實驗績效

|年／條件／成本倍數|指標|值|
|---|---|---|
|2024／asia_session／1|average_loss|-16.066329187927224|
|2024／asia_session／1|average_win|20.744583352427885|
|2024／asia_session／1|cagr|-0.003814917331906087|
|2024／asia_session／1|exposure|0.039385315879339786|
|2024／asia_session／1|fees|49.82125178583391|
|2024／asia_session／1|liquidation_count|0|
|2024／asia_session／1|liquidation_fees|0|
|2024／asia_session／1|maximum_drawdown|-0.015539681935503591|
|2024／asia_session／1|maximum_margin_ratio|0.021528225729704458|
|2024／asia_session／1|net_funding|-6.687687326136976|
|2024／asia_session／1|number_of_trades|23|
|2024／asia_session／1|profit_factor|0.8300467037439149|
|2024／asia_session／1|sharpe_ratio|-0.2688800457863281|
|2024／asia_session／1|slippage|24.91063669096877|
|2024／asia_session／1|sortino_ratio|-0.38342438443926774|
|2024／asia_session／1|total_return|-0.0038227358459135274|
|2024／asia_session／1|win_rate|0.391304347826087|
|2024／volume_confirmation／1|average_loss|-13.518129819577904|
|2024／volume_confirmation／1|average_win|20.677144440119086|
|2024／volume_confirmation／1|cagr|-0.03578288007821606|
|2024／volume_confirmation／1|exposure|0.17495731360273192|
|2024／volume_confirmation／1|fees|206.64903196991108|
|2024／volume_confirmation／1|liquidation_count|0|
|2024／volume_confirmation／1|liquidation_fees|0|
|2024／volume_confirmation／1|maximum_drawdown|-0.039251787029805474|
|2024／volume_confirmation／1|maximum_margin_ratio|0.021936631326499735|
|2024／volume_confirmation／1|net_funding|-14.194818063854882|
|2024／volume_confirmation／1|number_of_trades|110|
|2024／volume_confirmation／1|profit_factor|0.655536930755434|
|2024／volume_confirmation／1|sharpe_ratio|-1.509264090735799|
|2024／volume_confirmation／1|slippage|103.32450738947634|
|2024／volume_confirmation／1|sortino_ratio|-2.1157639397340775|
|2024／volume_confirmation／1|total_return|-0.035855022958358185|
|2024／volume_confirmation／1|win_rate|0.3|
|2024／asia_session／2|average_loss|-15.615031510459643|
|2024／asia_session／2|average_win|17.361329474768667|
|2024／asia_session／2|cagr|-0.009514041087414382|
|2024／asia_session／2|exposure|0.039385315879339786|
|2024／asia_session／2|fees|86.09058050071444|
|2024／asia_session／2|liquidation_count|0|
|2024／asia_session／2|liquidation_fees|0|
|2024／asia_session／2|maximum_drawdown|-0.016236534265130276|
|2024／asia_session／2|maximum_margin_ratio|0.02155060996658515|
|2024／asia_session／2|net_funding|-5.859060785143532|
|2024／asia_session／2|number_of_trades|23|
|2024／asia_session／2|profit_factor|0.59297835637887|
|2024／asia_session／2|sharpe_ratio|-0.7627589496906818|
|2024／asia_session／2|slippage|43.04532991048892|
|2024／asia_session／2|sortino_ratio|-1.054164156765396|
|2024／asia_session／2|total_return|-0.009533483685873367|
|2024／asia_session／2|win_rate|0.34782608695652173|
|2024／volume_confirmation／2|average_loss|-13.054666597455958|
|2024／volume_confirmation／2|average_win|17.041000595788635|
|2024／volume_confirmation／2|cagr|-0.05621178642404945|
|2024／volume_confirmation／2|exposure|0.17495731360273192|
|2024／volume_confirmation／2|fees|340.16512836859715|
|2024／volume_confirmation／2|liquidation_count|0|
|2024／volume_confirmation／2|liquidation_fees|0|
|2024／volume_confirmation／2|maximum_drawdown|-0.058844798365083384|
|2024／volume_confirmation／2|maximum_margin_ratio|0.02195966539786721|
|2024／volume_confirmation／2|net_funding|-12.539356285209372|
|2024／volume_confirmation／2|number_of_trades|110|
|2024／volume_confirmation／2|profit_factor|0.46735004170294936|
|2024／volume_confirmation／2|sharpe_ratio|-2.7940544301587367|
|2024／volume_confirmation／2|slippage|170.08252373231954|
|2024／volume_confirmation／2|sortino_ratio|-3.740570424417563|
|2024／volume_confirmation／2|total_return|-0.05632389771160684|
|2024／volume_confirmation／2|win_rate|0.2636363636363636|
|2025／asia_session／1|average_loss|-12.100310588154812|
|2025／asia_session／1|average_win|26.02742326346869|
|2025／asia_session／1|cagr|-0.012770986266304907|
|2025／asia_session／1|exposure|0.02842141308069855|
|2025／asia_session／1|fees|27.81935169875679|
|2025／asia_session／1|liquidation_count|0|
|2025／asia_session／1|liquidation_fees|0|
|2025／asia_session／1|maximum_drawdown|-0.016187047797446952|
|2025／asia_session／1|maximum_margin_ratio|0.021700809429656603|
|2025／asia_session／1|net_funding|0.07984326849989762|
|2025／asia_session／1|number_of_trades|20|
|2025／asia_session／1|profit_factor|0.37958320657070843|
|2025／asia_session／1|sharpe_ratio|-1.4619768791309464|
|2025／asia_session／1|slippage|13.90965435591471|
|2025／asia_session／1|sortino_ratio|-2.1380076747323766|
|2025／asia_session／1|total_return|-0.01276230102082232|
|2025／asia_session／1|win_rate|0.15|
|2025／volume_confirmation／1|average_loss|-13.684612357155267|
|2025／volume_confirmation／1|average_win|17.310560221351384|
|2025／volume_confirmation／1|cagr|-0.038295623672520485|
|2025／volume_confirmation／1|exposure|0.11003310124415021|
|2025／volume_confirmation／1|fees|129.47789328315744|
|2025／volume_confirmation／1|liquidation_count|0|
|2025／volume_confirmation／1|liquidation_fees|0|
|2025／volume_confirmation／1|maximum_drawdown|-0.04424204276707544|
|2025／volume_confirmation／1|maximum_margin_ratio|0.021543872745499452|
|2025／volume_confirmation／1|net_funding|0.40881378834163934|
|2025／volume_confirmation／1|number_of_trades|71|
|2025／volume_confirmation／1|profit_factor|0.46219887151304967|
|2025／volume_confirmation／1|sharpe_ratio|-2.2896908189462852|
|2025／volume_confirmation／1|slippage|64.7388994187667|
|2025／volume_confirmation／1|sortino_ratio|-3.129584215290693|
|2025／volume_confirmation／1|total_return|-0.038269919836640076|
|2025／volume_confirmation／1|win_rate|0.2676056338028169|
|2025／asia_session／2|average_loss|-12.469909661613865|
|2025／asia_session／2|average_win|20.973380786497312|
|2025／asia_session／2|cagr|-0.014916965814158356|
|2025／asia_session／2|exposure|0.02842141308069855|
|2025／asia_session／2|fees|48.825926021283394|
|2025／asia_session／2|liquidation_count|0|
|2025／asia_session／2|liquidation_fees|0|
|2025／asia_session／2|maximum_drawdown|-0.01733494117813783|
|2025／asia_session／2|maximum_margin_ratio|0.021723466601409412|
|2025／asia_session／2|net_funding|0.07987932115157441|
|2025／asia_session／2|number_of_trades|20|
|2025／asia_session／2|profit_factor|0.29680927489549963|
|2025／asia_session／2|sharpe_ratio|-1.8813456346556656|
|2025／asia_session／2|slippage|24.412887101252437|
|2025／asia_session／2|sortino_ratio|-2.675010565321039|
|2025／asia_session／2|total_return|-0.014906832188794406|
|2025／asia_session／2|win_rate|0.15|
|2025／volume_confirmation／2|average_loss|-13.708704985034386|
|2025／volume_confirmation／2|average_win|13.323441241431038|
|2025／volume_confirmation／2|cagr|-0.048706455099456814|
|2025／volume_confirmation／2|exposure|0.11003310124415021|
|2025／volume_confirmation／2|fees|218.834463981161|
|2025／volume_confirmation／2|liquidation_count|0|
|2025／volume_confirmation／2|liquidation_fees|0|
|2025／volume_confirmation／2|maximum_drawdown|-0.05166642773482122|
|2025／volume_confirmation／2|maximum_margin_ratio|0.02156628199927434|
|2025／volume_confirmation／2|net_funding|0.3620724956430095|
|2025／volume_confirmation／2|number_of_trades|71|
|2025／volume_confirmation／2|profit_factor|0.33007802803768566|
|2025／volume_confirmation／2|sharpe_ratio|-3.312295005066048|
|2025／volume_confirmation／2|slippage|109.41707314061789|
|2025／volume_confirmation／2|sortino_ratio|-4.372447022387127|
|2025／volume_confirmation／2|total_return|-0.04867394218610532|
|2025／volume_confirmation／2|win_rate|0.2535211267605634|

## 測試與限制

171項程式測試通過，新增夏令時間、起點／終點、用已知的下一根執行時間而非K線開盤標記、只用此前成交量、買入賣出退出均不被濾網阻擋、dashboard方向與資產曲線、年度成本篩選、快照損壞可見錯誤。Windows直接宣告tzdata依賴，避免僅依賴系統時區。

這些來源提供新假設而非獲利證明。2024／2025已多次用於調整，仍是調整資料；沒有新的獨立未見驗證。固定BTC無多幣種選擇存活者偏差，但1h盤中路徑、固定滑價與深度、funding邊界以及歷史維持保證金仍有模型限制。固定2%MMR非歷史級距，沒有ADL／部分成交模型；歷史最大回撤10%不是未來損失保證。不修改live、paper、testnet設定，不送單。

後續原則已寫入AGENTS.md：合約策略原生考慮多空；失敗時先檢查證據與原始研究再提出新假設，不以任意參數掃描或未驗證信心加槓桿補足收益。
