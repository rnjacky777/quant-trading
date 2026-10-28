# V13 追蹤退出消融研究：未採用

日期：2026-10-27；任務 #15，狀態 skipped／rejected_after_research。沒有建立 V15，避免已失敗的探索繼續增加版本。

## 選擇與假設

佇列原為空。依使用者「繼續改善」延續未封存的V13，不從已失敗V14繼續調整。已讀V11再進場失敗研究，不重複其突破再入規則。本輪僅停用追蹤退出，保留SMA24/180、1%門檻、初始止損5%、訊號反轉退出、SMA180斜率動態風險0.25%／0.5%、1x。固定止盈仍停用。設計先記錄在data/optimization-15-design.json。

假設：追蹤退出可能切斷趨勢，取消後可能改善持有大趨勢能力；相對風險是獲利回吐。這是出場類別單一實驗，不掃描追蹤距離或均線參數。

## 年度結果

BTC/USDT現貨4h，只做多，每年重設本金10,000 USDT。一般手續費10bps、滑價5bps，雙成本兩者加倍。使用父版本精確180根暖機，歷史不足186根時原動態風控採減半風險。

|年度|追蹤退出|成本|淨收益|最大回撤|交易數|
|---|---|---|---:|---:|---:|
|2024|保留（V13）|一般|+1.272%|-0.864%|8|
|2024|保留（V13）|雙倍|+1.045%|-0.877%|8|
|2024|停用（研究）|一般|+4.946%|-2.174%|8|
|2024|停用（研究）|雙倍|+4.552%|-2.194%|8|
|2025|保留（V13）|一般|+0.926%|-1.688%|8|
|2025|保留（V13）|雙倍|+0.730%|-1.728%|8|
|2025|停用（研究）|一般|+0.059%|-2.275%|8|
|2025|停用（研究）|雙倍|-0.094%|-2.289%|8|

## 逐筆問題

2025年1月進場保留追蹤退出時約賺1.31 USDT，取消後持有至2月觸發原始止損，變為虧25.00 USDT。4月15日主要趨勢交易，原追蹤5月29日退出淨賺225.73 USDT，取消後6月5日才因訊號退出，淨賺降至177.81 USDT。6月27日交易也由42.87 USDT降至29.11 USDT。以上是不同資金路徑下的描述性比較，非獨立因果貢獻加總。

兩年交易數皆維持8筆。取消追蹤沒有解決交易數疑慮，也沒有改善2025；它只能改善2024單一年份收益，卻增加回撤。故停止，不建立候選，不提高槓桿補收益。

## 父版本全部保存證據

analyze-request先重現以下全部14筆資料指紋和保存淨值，沒有略過虧損或較差時段；各筆包含完整成本與metrics於data/optimization-15-analysis.json。重複或重疊區間不視為獨立樣本，不加總收益或交易次數。候選只進行上述年度篩選，失敗後未繼續全區間候選比較。

|區間 UTC（結束不含）|本金|手續費／滑價 bps|淨收益|回撤|交易數|run key|
|---|---:|---|---:|---:|---:|---|
|2020-03-01 → 2026-09-30|10000|10／5|+9.515%|-2.650%|49|d710912d4673e5be018ac0fca2d41ed7844c1378b791bd8449ccd2fe24669ed8|
|2020-03-01 → 2023-01-01|10000|10／5|+0.538%|-2.650%|19|e004891969e0abc685d2fe552283ab9e1ece43491235c0d23cc49cf80100197e|
|2023-01-01 → 2026-09-30|10000|10／5|+5.827%|-2.574%|30|f20d43b0f1ebaff40180562d4687c3ba72d2a430ab20ece9fb7941452054a701|
|2026-07-01 → 2026-08-30|10000|10／5|+0.929%|-0.401%|2|38ded82586d0e64c4b272173057d1ce2f5ba26f1e95f2067c77fde07e248aade|
|2020-03-01 → 2022-12-30|10000|10／5|+0.538%|-2.650%|19|c78a58ff6ee0edc1e953091dbb92b7822cfa8ed1272c8b6aab973fa11160586b|
|2022-01-01 → 2023-12-30|10000|10／5|+4.577%|-1.972%|18|40e3cc0c2b03cd37fd2798af8ecabae3930260b459585ac1ea564712a7c25e91|
|2023-01-01 → 2024-12-30|10000|10／5|+4.367%|-1.131%|16|0c0775542d95a600a87d22416dd4949e4bdde1e221f2b7d797c3654e925485d0|
|2024-01-01 → 2025-12-30|10000|10／5|+2.723%|-1.688%|15|abf4e33ec705ed3d4cebc5a73f2fc605970e149cff6acdea60de7f68241f6d0b|
|2026-01-01 → 2026-10-20|10000|10／5|+0.880%|-0.769%|6|5e94e59818adbe543fb4bebb43d90b51439f700d2224ecd00ac3f720fb774a40|
|2025-01-01 → 2025-12-31|10000|10／5|+0.661%|-1.688%|8|7b9427a308fe91b213a5ed300877f4478b332014dc6f79cdd6c9b56bea5144e7|
|2025-01-01 → 2025-12-31|10000|10／5|+0.661%|-1.688%|8|d55c5b17a88dcb13627c3c5e5cee148b17a149ad85d72cdb72ff4537b1e771ec|
|2025-01-01 → 2025-12-31|10000|10／5|+0.926%|-1.688%|8|e86a24d4e1fbd66ab6a4e62b520d1b62cb0af238729f1c5ffa7a4a59481c5585|
|2025-01-01 → 2026-01-01|10000|10／5|+0.926%|-1.688%|8|93b341b60c628cf6e9514c68260961e54885438665f1f8312b867026ac4a7c35|
|2024-01-01 → 2025-01-01|10000|10／5|+1.272%|-0.864%|8|e4ec4fffab28c91ddf817ffca3576ab136d2ef686bbfb76f3a869d057e994e81|

## 完整研究指標

|年度／追蹤／成本倍數|指標|值|
|---|---|---|
|2024／True／1|average_loss|-31.605765629010527|
|2024／True／1|average_win|63.39765451214477|
|2024／True／1|cagr|0.012690531972899599|
|2024／True／1|exposure|0.19299044151115158|
|2024／True／1|fees|12.661737987146088|
|2024／True／1|liquidation_count|0|
|2024／True／1|liquidation_fees|0.0|
|2024／True／1|maximum_drawdown|-0.008644588169916867|
|2024／True／1|maximum_margin_ratio|0.0|
|2024／True／1|net_funding|0.0|
|2024／True／1|number_of_trades|8|
|2024／True／1|profit_factor|2.0058889019272126|
|2024／True／1|sharpe_ratio|0.9158125816279125|
|2024／True／1|slippage|6.330905533622229|
|2024／True／1|sortino_ratio|1.3439754166291566|
|2024／True／1|total_return|0.012716755553253911|
|2024／True／1|win_rate|0.5|
|2024／True／2|average_loss|-32.26973720908357|
|2024／True／2|average_win|58.39477702782766|
|2024／True／2|cagr|0.010428490689280867|
|2024／True／2|exposure|0.19299044151115158|
|2024／True／2|fees|24.16709094732183|
|2024／True／2|liquidation_count|0|
|2024／True／2|liquidation_fees|0.0|
|2024／True／2|maximum_drawdown|-0.008769604989216084|
|2024／True／2|maximum_margin_ratio|0.0|
|2024／True／2|net_funding|0.0|
|2024／True／2|number_of_trades|8|
|2024／True／2|profit_factor|1.8095832838511674|
|2024／True／2|sharpe_ratio|0.7805204669519443|
|2024／True／2|slippage|12.083686224596775|
|2024／True／2|sortino_ratio|1.1295781127333997|
|2024／True／2|total_return|0.010450015927498058|
|2024／True／2|win_rate|0.5|
|2024／False／1|average_loss|-40.384179736674454|
|2024／False／1|average_win|232.18633818534155|
|2024／False／1|cagr|0.04935998996040358|
|2024／False／1|exposure|0.5266272189349113|
|2024／False／1|fees|13.00544993926597|
|2024／False／1|liquidation_count|0|
|2024／False／1|liquidation_fees|0.0|
|2024／False／1|maximum_drawdown|-0.021737453797191164|
|2024／False／1|maximum_margin_ratio|0.0|
|2024／False／1|net_funding|0.0|
|2024／False／1|number_of_trades|8|
|2024／False／1|profit_factor|3.449662809040304|
|2024／False／1|sharpe_ratio|1.3685439310985401|
|2024／False／1|slippage|6.502853506237141|
|2024／False／1|sortino_ratio|2.0071486739781683|
|2024／False／1|total_return|0.049463811587265205|
|2024／False／1|win_rate|0.375|
|2024／False／2|average_loss|-40.342517367165364|
|2024／False／2|average_win|218.97295651335742|
|2024／False／2|cagr|0.045425261063521294|
|2024／False／2|exposure|0.5266272189349113|
|2024／False／2|fees|24.826316499892737|
|2024／False／2|liquidation_count|0|
|2024／False／2|liquidation_fees|0.0|
|2024／False／2|maximum_drawdown|-0.021942313176717465|
|2024／False／2|maximum_margin_ratio|0.0|
|2024／False／2|net_funding|0.0|
|2024／False／2|number_of_trades|8|
|2024／False／2|profit_factor|3.2567073767921895|
|2024／False／2|sharpe_ratio|1.3175685640291206|
|2024／False／2|slippage|12.413650696195862|
|2024／False／2|sortino_ratio|1.929418455714923|
|2024／False／2|total_return|0.04552062827042436|
|2024／False／2|win_rate|0.375|
|2025／True／1|average_loss|-35.460071048588915|
|2025／True／1|average_win|89.97085880897735|
|2025／True／1|cagr|0.009267594724445605|
|2025／True／1|exposure|0.2606115928799635|
|2025／True／1|fees|11.677747764401623|
|2025／True／1|liquidation_count|0|
|2025／True／1|liquidation_fees|0.0|
|2025／True／1|maximum_drawdown|-0.01688093293212689|
|2025／True／1|maximum_margin_ratio|0.0|
|2025／True／1|net_funding|0.0|
|2025／True／1|number_of_trades|8|
|2025／True／1|profit_factor|1.5223465066219761|
|2025／True／1|sharpe_ratio|0.5674566702271402|
|2025／True／1|slippage|5.838901414417852|
|2025／True／1|sortino_ratio|0.8366953199433602|
|2025／True／1|total_return|0.009261222118398083|
|2025／True／1|win_rate|0.375|
|2025／True／2|average_loss|-29.832118161159286|
|2025／True／2|average_win|126.00525548909921|
|2025／True／2|cagr|0.007306799647568862|
|2025／True／2|exposure|0.2606115928799635|
|2025／True／2|fees|22.288755058173344|
|2025／True／2|liquidation_count|0|
|2025／True／2|liquidation_fees|0.0|
|2025／True／2|maximum_drawdown|-0.017280644884251628|
|2025／True／2|maximum_margin_ratio|0.0|
|2025／True／2|net_funding|0.0|
|2025／True／2|number_of_trades|8|
|2025／True／2|profit_factor|1.4079372977405615|
|2025／True／2|sharpe_ratio|0.46818257092467286|
|2025／True／2|slippage|11.144483980127069|
|2025／True／2|sortino_ratio|0.687142448632551|
|2025／True／2|total_return|0.007301780201124153|
|2025／True／2|win_rate|0.25|
|2025／False／1|average_loss|-33.498950761981426|
|2025／False／1|average_win|103.4574235043878|
|2025／False／1|cagr|0.0005925199215166543|
|2025／False／1|exposure|0.36786855317206757|
|2025／False／1|fees|11.520548180765747|
|2025／False／1|liquidation_count|0|
|2025／False／1|liquidation_fees|0.0|
|2025／False／1|maximum_drawdown|-0.022754221035994004|
|2025／False／1|maximum_margin_ratio|0.0|
|2025／False／1|net_funding|0.0|
|2025／False／1|number_of_trades|8|
|2025／False／1|profit_factor|1.029459342766476|
|2025／False／1|sharpe_ratio|0.04173869210595198|
|2025／False／1|slippage|5.7602798908749255|
|2025／False／1|sortino_ratio|0.06002069762925378|
|2025／False／1|total_return|0.0005921142436886573|
|2025／False／1|win_rate|0.25|
|2025／False／2|average_loss|-33.77035398366406|
|2025／False／2|average_win|96.62340256601922|
|2025／False／2|cagr|-0.0009381737207999619|
|2025／False／2|exposure|0.36786855317206757|
|2025／False／2|fees|21.995623217544495|
|2025／False／2|liquidation_count|0|
|2025／False／2|liquidation_fees|0.0|
|2025／False／2|maximum_drawdown|-0.02288719786576532|
|2025／False／2|maximum_margin_ratio|0.0|
|2025／False／2|net_funding|0.0|
|2025／False／2|number_of_trades|8|
|2025／False／2|profit_factor|0.9537300340683376|
|2025／False／2|sharpe_ratio|-0.04539743351504706|
|2025／False／2|slippage|10.997835226911285|
|2025／False／2|sortino_ratio|-0.06509384608368589|
|2025／False／2|total_return|-0.000937531876994746|
|2025／False／2|win_rate|0.25|

## 限制與決策

2024、2025及其他保存區間均已用於調整；無未見驗證，不宣稱達成15%或未來收益。固定BTC不涉及多幣種存活者篩選，但4h無法還原盤中路徑，固定滑價沒有完整委託簿與流動性模型；下一根開盤執行及成本沿用引擎，未修改執行順序、策略程式或live設定。

本輪只用既有功能進行一項研究，沒有程式變更，因此沒有為參數探索新增程式測試。原版本、回測及主要研究分類不變。下一步若要再探索，應先提出能區分「趨勢延續」與「獲利回吐」的可觀察證據；不能只因2025退步就掃描追蹤距離直到變好。
