# V13 → V15：回檔恢復趨勢再進場（未通過）

日期2026-10-27。使用者要求改進策略，本輪完成一項出場／再入變更及全部14筆父版本實驗比較。任務#16 completed代表實驗完成，不代表改善已通過。V15歸檔，主要研究與V13不被替換。前次任務#15停用追蹤失敗後未建版本，所以本輪新版本號為V15。

## 實作規則與架構

僅trailing_reentry_mode由inherit改pullback_reclaim。追蹤止損退出後，退出K線之後的已完成收盤先嚴格低於SMA24，再在較晚完成收盤嚴格高於SMA24、SMA180相較6根前斜率正、策略BUY時，下一根開盤可再入。等於均線、盤中高點、HOLD不確認。原SELL重置仍有效；初始止損不啟動這條路徑。

保留V13的SMA24/180、1%進場門檻、初始止損5%、收盤5%啟動／5%距離追蹤、動態風險0.25%／0.5%、1x。策略仍只產生訊號，數量由風控計算。新規則狀態在每次引擎run初始化，防止跨回測洩漏。

資料流：完成K線 → 原策略Signal → 再進場確認狀態 → 原風控數量 → 下一根成本含括成交 → 保存交易／曲線。實作於app/backtest/reentry.py、engine.py、models.py、configuration.py，CLI與dashboard支援新模式；既有參數保存／重播與鎖定沿用原機制。

## 年度拆解

BTC/USDT現貨4h，只做多／空手，單年初始10,000 USDT，1x。一般成本單邊手續費10bps、滑價5bps；雙成本皆加倍。使用父版本精確180根暖機，前6根斜率不足時沿用減半風險；新dashboard回測取186根暖機，不改寫原實驗指紋。

|年度|方案|成本|淨收益|最大回撤|交易數|
|---|---|---|---:|---:|---:|
|2024|V13|一般|+1.272%|-0.864%|8|
|2024|V13|雙倍|+1.045%|-0.877%|8|
|2024|V15|一般|+4.132%|-2.150%|17|
|2024|V15|雙倍|+3.517%|-2.284%|17|
|2025|V13|一般|+0.926%|-1.688%|8|
|2025|V13|雙倍|+0.730%|-1.728%|8|
|2025|V15|一般|-0.445%|-2.536%|11|
|2025|V15|雙倍|-0.649%|-2.586%|11|

## 新增交易

完整2024一般成本：新增9筆，6筆盈利，新增交易淨損益約+285.88 USDT。完整2025：新增3筆全部虧損，合計-137.54 USDT。這是依進場時間是否出現在父版本做描述性分組，資金路徑不同，不能把新增交易PnL直接當完整因果差額。

|2025新增進場 UTC|淨損益 USDT|退出|
|---|---:|---|
|2025-01-21 20:00|-50.01|初始止損|
|2025-06-02 00:00|-37.00|訊號|
|2025-07-16 12:00|-50.53|初始止損|

回檔站回快均線與慢線仍向上，不能可靠區分延續和反彈，慢線斜率可能在反轉初期仍正；這是根據失敗交易提出的解釋，尚非獨立驗證的因果結論。不能只針對這三筆調整條件以避開虧損。

## 全部保存實驗

父版本全部14筆已重現完整指紋與保存淨值，子版本逐筆使用相同資料、暖機、資金及成本，不略過較差時段。重複／重疊期間不視為獨立樣本，不加總收益和交易數。

|期間 UTC（結束不含）|本金|費率／滑價 bps|V13收益／回撤／筆數|V15收益／回撤／筆數|來源run key|
|---|---:|---|---|---|---|
|2020-03-01 → 2026-09-30|10000|10／5|+9.515%／-2.650%／49|+12.503%／-4.009%／89|d710912d4673e5be018ac0fca2d41ed7844c1378b791bd8449ccd2fe24669ed8|
|2020-03-01 → 2023-01-01|10000|10／5|+0.538%／-2.650%／19|+3.799%／-4.009%／41|e004891969e0abc685d2fe552283ab9e1ece43491235c0d23cc49cf80100197e|
|2023-01-01 → 2026-09-30|10000|10／5|+5.827%／-2.574%／30|+5.299%／-3.414%／48|f20d43b0f1ebaff40180562d4687c3ba72d2a430ab20ece9fb7941452054a701|
|2026-07-01 → 2026-08-30|10000|10／5|+0.929%／-0.401%／2|+0.929%／-0.401%／2|38ded82586d0e64c4b272173057d1ce2f5ba26f1e95f2067c77fde07e248aade|
|2020-03-01 → 2022-12-30|10000|10／5|+0.538%／-2.650%／19|+3.799%／-4.009%／41|c78a58ff6ee0edc1e953091dbb92b7822cfa8ed1272c8b6aab973fa11160586b|
|2022-01-01 → 2023-12-30|10000|10／5|+4.577%／-1.972%／18|+1.255%／-3.436%／25|40e3cc0c2b03cd37fd2798af8ecabae3930260b459585ac1ea564712a7c25e91|
|2023-01-01 → 2024-12-30|10000|10／5|+4.367%／-1.131%／16|+5.480%／-2.150%／29|0c0775542d95a600a87d22416dd4949e4bdde1e221f2b7d797c3654e925485d0|
|2024-01-01 → 2025-12-30|10000|10／5|+2.723%／-1.688%／15|+4.189%／-2.536%／27|abf4e33ec705ed3d4cebc5a73f2fc605970e149cff6acdea60de7f68241f6d0b|
|2026-01-01 → 2026-10-20|10000|10／5|+0.880%／-0.769%／6|+0.685%／-1.068%／8|5e94e59818adbe543fb4bebb43d90b51439f700d2224ecd00ac3f720fb774a40|
|2025-01-01 → 2025-12-31|10000|10／5|+0.661%／-1.688%／8|-0.208%／-2.536%／10|7b9427a308fe91b213a5ed300877f4478b332014dc6f79cdd6c9b56bea5144e7|
|2025-01-01 → 2025-12-31|10000|10／5|+0.661%／-1.688%／8|-0.208%／-2.536%／10|d55c5b17a88dcb13627c3c5e5cee148b17a149ad85d72cdb72ff4537b1e771ec|
|2025-01-01 → 2025-12-31|10000|10／5|+0.926%／-1.688%／8|-0.445%／-2.536%／11|e86a24d4e1fbd66ab6a4e62b520d1b62cb0af238729f1c5ffa7a4a59481c5585|
|2025-01-01 → 2026-01-01|10000|10／5|+0.926%／-1.688%／8|-0.445%／-2.536%／11|93b341b60c628cf6e9514c68260961e54885438665f1f8312b867026ac4a7c35|
|2024-01-01 → 2025-01-01|10000|10／5|+1.272%／-0.864%／8|+4.132%／-2.150%／17|e4ec4fffab28c91ddf817ffca3576ab136d2ef686bbfb76f3a869d057e994e81|

長區間（2020-03至2026-09）收益9.515%→12.503%，回撤-2.650%→-4.009%，交易49→89。2025完整年轉虧，2022–2023及2026部分區間退步，因此不採用全面替換。

## 全部年度指標

|年／模式／成本倍數|指標|值|
|---|---|---|
|2024／inherit／1|average_loss|-31.605765629010527|
|2024／inherit／1|average_win|63.39765451214477|
|2024／inherit／1|cagr|0.012690531972899599|
|2024／inherit／1|exposure|0.19299044151115158|
|2024／inherit／1|fees|12.661737987146088|
|2024／inherit／1|liquidation_count|0|
|2024／inherit／1|liquidation_fees|0.0|
|2024／inherit／1|maximum_drawdown|-0.008644588169916867|
|2024／inherit／1|maximum_margin_ratio|0.0|
|2024／inherit／1|net_funding|0.0|
|2024／inherit／1|number_of_trades|8|
|2024／inherit／1|profit_factor|2.0058889019272126|
|2024／inherit／1|sharpe_ratio|0.9158125816279125|
|2024／inherit／1|slippage|6.330905533622229|
|2024／inherit／1|sortino_ratio|1.3439754166291566|
|2024／inherit／1|total_return|0.012716755553253911|
|2024／inherit／1|win_rate|0.5|
|2024／inherit／2|average_loss|-32.26973720908357|
|2024／inherit／2|average_win|58.39477702782766|
|2024／inherit／2|cagr|0.010428490689280867|
|2024／inherit／2|exposure|0.19299044151115158|
|2024／inherit／2|fees|24.16709094732183|
|2024／inherit／2|liquidation_count|0|
|2024／inherit／2|liquidation_fees|0.0|
|2024／inherit／2|maximum_drawdown|-0.008769604989216084|
|2024／inherit／2|maximum_margin_ratio|0.0|
|2024／inherit／2|net_funding|0.0|
|2024／inherit／2|number_of_trades|8|
|2024／inherit／2|profit_factor|1.8095832838511674|
|2024／inherit／2|sharpe_ratio|0.7805204669519443|
|2024／inherit／2|slippage|12.083686224596775|
|2024／inherit／2|sortino_ratio|1.1295781127333997|
|2024／inherit／2|total_return|0.010450015927498058|
|2024／inherit／2|win_rate|0.5|
|2024／pullback_reclaim／1|average_loss|-34.19212135289383|
|2024／pullback_reclaim／1|average_win|65.24975095366976|
|2024／pullback_reclaim／1|cagr|0.04122888183438467|
|2024／pullback_reclaim／1|exposure|0.406463359126081|
|2024／pullback_reclaim／1|fees|30.442825568826287|
|2024／pullback_reclaim／1|liquidation_count|0|
|2024／pullback_reclaim／1|liquidation_fees|0.0|
|2024／pullback_reclaim／1|maximum_drawdown|-0.021501067659029705|
|2024／pullback_reclaim／1|maximum_margin_ratio|0.0|
|2024／pullback_reclaim／1|net_funding|0.0|
|2024／pullback_reclaim／1|number_of_trades|17|
|2024／pullback_reclaim／1|profit_factor|2.726181536727754|
|2024／pullback_reclaim／1|sharpe_ratio|1.5196019683675202|
|2024／pullback_reclaim／1|slippage|15.221527488664572|
|2024／pullback_reclaim／1|sortino_ratio|2.352786034809551|
|2024／pullback_reclaim／1|total_return|0.04131526600664448|
|2024／pullback_reclaim／1|win_rate|0.5882352941176471|
|2024／pullback_reclaim／2|average_loss|-34.9129087272404|
|2024／pullback_reclaim／2|average_win|59.606296299716156|
|2024／pullback_reclaim／2|cagr|0.035093946179675095|
|2024／pullback_reclaim／2|exposure|0.406463359126081|
|2024／pullback_reclaim／2|fees|58.02122609247181|
|2024／pullback_reclaim／2|liquidation_count|0|
|2024／pullback_reclaim／2|liquidation_fees|0.0|
|2024／pullback_reclaim／2|maximum_drawdown|-0.022842409747157344|
|2024／pullback_reclaim／2|maximum_margin_ratio|0.0|
|2024／pullback_reclaim／2|net_funding|0.0|
|2024／pullback_reclaim／2|number_of_trades|17|
|2024／pullback_reclaim／2|profit_factor|2.4389790183909428|
|2024／pullback_reclaim／2|sharpe_ratio|1.3510504274707946|
|2024／pullback_reclaim／2|slippage|29.01105175111413|
|2024／pullback_reclaim／2|sortino_ratio|2.070011658180372|
|2024／pullback_reclaim／2|total_return|0.035167260190648086|
|2024／pullback_reclaim／2|win_rate|0.5882352941176471|
|2025／inherit／1|average_loss|-35.460071048588915|
|2025／inherit／1|average_win|89.97085880897735|
|2025／inherit／1|cagr|0.009267594724445605|
|2025／inherit／1|exposure|0.2606115928799635|
|2025／inherit／1|fees|11.677747764401623|
|2025／inherit／1|liquidation_count|0|
|2025／inherit／1|liquidation_fees|0.0|
|2025／inherit／1|maximum_drawdown|-0.01688093293212689|
|2025／inherit／1|maximum_margin_ratio|0.0|
|2025／inherit／1|net_funding|0.0|
|2025／inherit／1|number_of_trades|8|
|2025／inherit／1|profit_factor|1.5223465066219761|
|2025／inherit／1|sharpe_ratio|0.5674566702271402|
|2025／inherit／1|slippage|5.838901414417852|
|2025／inherit／1|sortino_ratio|0.8366953199433602|
|2025／inherit／1|total_return|0.009261222118398083|
|2025／inherit／1|win_rate|0.375|
|2025／inherit／2|average_loss|-29.832118161159286|
|2025／inherit／2|average_win|126.00525548909921|
|2025／inherit／2|cagr|0.007306799647568862|
|2025／inherit／2|exposure|0.2606115928799635|
|2025／inherit／2|fees|22.288755058173344|
|2025／inherit／2|liquidation_count|0|
|2025／inherit／2|liquidation_fees|0.0|
|2025／inherit／2|maximum_drawdown|-0.017280644884251628|
|2025／inherit／2|maximum_margin_ratio|0.0|
|2025／inherit／2|net_funding|0.0|
|2025／inherit／2|number_of_trades|8|
|2025／inherit／2|profit_factor|1.4079372977405615|
|2025／inherit／2|sharpe_ratio|0.46818257092467286|
|2025／inherit／2|slippage|11.144483980127069|
|2025／inherit／2|sortino_ratio|0.687142448632551|
|2025／inherit／2|total_return|0.007301780201124153|
|2025／inherit／2|win_rate|0.25|
|2025／pullback_reclaim／1|average_loss|-39.112131915780594|
|2025／pullback_reclaim／1|average_win|89.47136777746807|
|2025／pullback_reclaim／1|cagr|-0.004451335185723049|
|2025／pullback_reclaim／1|exposure|0.3194888178913738|
|2025／pullback_reclaim／1|fees|17.21268387169148|
|2025／pullback_reclaim／1|liquidation_count|0|
|2025／pullback_reclaim／1|liquidation_fees|0.0|
|2025／pullback_reclaim／1|maximum_drawdown|-0.02536215341995174|
|2025／pullback_reclaim／1|maximum_margin_ratio|0.0|
|2025／pullback_reclaim／1|net_funding|0.0|
|2025／pullback_reclaim／1|number_of_trades|11|
|2025／pullback_reclaim／1|profit_factor|0.8578351849701494|
|2025／pullback_reclaim／1|sharpe_ratio|-0.2401460376501823|
|2025／pullback_reclaim／1|slippage|8.606337269862172|
|2025／pullback_reclaim／1|sortino_ratio|-0.3400993580120961|
|2025／pullback_reclaim／1|total_return|-0.004448295199383945|
|2025／pullback_reclaim／1|win_rate|0.2727272727272727|
|2025／pullback_reclaim／2|average_loss|-35.05193619623293|
|2025／pullback_reclaim／2|average_win|125.30161935635348|
|2025／pullback_reclaim／2|cagr|-0.006490847007975753|
|2025／pullback_reclaim／2|exposure|0.3194888178913738|
|2025／pullback_reclaim／2|fees|32.85240516842477|
|2025／pullback_reclaim／2|liquidation_count|0|
|2025／pullback_reclaim／2|liquidation_fees|0.0|
|2025／pullback_reclaim／2|maximum_drawdown|-0.025861661711442996|
|2025／pullback_reclaim／2|maximum_margin_ratio|0.0|
|2025／pullback_reclaim／2|net_funding|0.0|
|2025／pullback_reclaim／2|number_of_trades|11|
|2025／pullback_reclaim／2|profit_factor|0.7943870531295899|
|2025／pullback_reclaim／2|sharpe_ratio|-0.37034239516032796|
|2025／pullback_reclaim／2|slippage|16.42618699861649|
|2025／pullback_reclaim／2|sortino_ratio|-0.5219881521582994|
|2025／pullback_reclaim／2|total_return|-0.006486418705338615|
|2025／pullback_reclaim／2|win_rate|0.18181818181818182|

## 證據、測試與限制

- 事前設計：data/pullback-reclaim-design.json。
- 所有原證據：data/optimization-16-analysis.json；完整逐期比較：data/optimization-16-result.json。
- 年度完整交易／資產曲線／全部績效：data/pullback-reclaim-annual.json，執行python -m scripts.research_pullback_reentry可重現。
- 正式V15回測保存於dashboard，已封存，可勾選顯示封存版本後查看及比較。自訂參數可選回檔再進場模式，預設沿用原規則。
- 128項軟體測試通過；後續效能小修又通過14項相關測試。覆蓋下一根成交、必須先回檔、HOLD不確認、初始止損不解鎖、當根收盤不前視、每次run重置、版本重播與dashboard參數鎖定。HTTP驗證新選項已載入。
- 所有觀察區間皆為調整證據，無未見驗證、不保證15%。固定BTC不涉及多幣種選擇存活者偏差；4h仍有盤中先後路徑不確定、固定滑價未含完整深度、跳空可超出止損預算。實際延遲沿用下一根成交。
- 本輪沒有改動live設定或送單，槓桿固定1x；僅一組固定規則，未掃描參數追逐兩個年度。

決策：功能與研究完成，改善假設未通過。保留V15全部失敗證據並封存，父版本不覆寫。若繼續研究，先評估策略訊號本身的淨優勢與不同市場狀態，不能將增加交易或提高槓桿當作達標方法。
