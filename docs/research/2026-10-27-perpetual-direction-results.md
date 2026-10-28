# BTC合約多空研究R1：2024／2025完整年度結果

2026-10-27。使用者已明確授權新增合約做空研究。結論：本固定規則加入空單後未改善年度淨收益，全部模式均未達兩年各10%收益目標，沒有理由放大槓桿。這是獨立合約研究基準R1，不是現貨V6的正式升級，也未新增live／paper／testnet交易。

## 相同合約市場內比較

每年重設本金10,000 USDT，BTC/USDT USDT永續、1h訊號＋已完成4h方向；一般單邊手續費10bps、滑價5bps，實際歷史資金費另計。下列最大回撤依小時標記收盤淨值，盤中可能更大。

|年|方向|淨收益|淨賺／虧USDT|最大回撤|交易數|淨資金費USDT|強平次數|
|---|---|---:|---:|---:|---:|---:|---:|
|2024|只做多|-1.410%|-141.05|-2.186%|71|-18.64|0|
|2024|只做空|-2.153%|-215.30|-2.856%|42|+3.85|0|
|2024|多空雙向|-3.308%|-330.82|-3.983%|113|-14.03|0|
|2025|只做多|-0.783%|-78.27|-1.746%|28|-2.52|0|
|2025|只做空|-3.322%|-332.17|-3.612%|47|+2.81|0|
|2025|多空雙向|-4.191%|-419.12|-4.786%|75|+0.46|0|

正資金費表示實際收到，負值表示支付。不能只看空單有收到資金費，就推論做空有利可圖；價格損益、進出費與滑價仍須一起計算。

## 雙倍成本

|年|方向|收益|回撤|交易數|
|---|---|---:|---:|---:|
|2024|只做多|-2.846%|-3.194%|71|
|2024|只做空|-2.675%|-2.803%|42|
|2024|多空雙向|-5.467%|-5.720%|113|
|2025|只做多|-1.413%|-2.100%|28|
|2025|只做空|-3.866%|-4.100%|47|
|2025|多空雙向|-5.243%|-5.542%|75|

## 實際規則與槓桿

- 4h SMA20>SMA60允許做多，<允許做空，等於則空手。只使用已完成UTC四小時時段。
- 多單突破前20根高點，且上漲K線收於上方三分之一；空單跌破前20根低點，且下跌K線收於下方三分之一。ATR14／價格至少0.6%。
- 初始止損距離為已完成1h simple ATR14×2。多單跌破前10根低點或4h方向失效退出；空單突破前10根高點或4h方向失效退出。
- 每UTC日合計最多2次成功進場，同時一個方向、無對鎖，最多24h；開盤退出當根不立即重新進場／反向。
- 單筆風險0.25%，連虧兩筆後0.125%，正淨利恢復。含進出費、止損滑價及名目部位0.1%的資金費預留反推數量，再限制名目曝險≤50%資金。預留不等於實際累積資金費上限。
- 槓桿按ceil(notional/equity)取最低必要整數，研究上限2x；本輪所有交易實際都只需1x。不使用未校準的趨勢強度當勝率或加槓桿理由。

只做多、只做空與多空雙向是同一訊號的方向拆解，並非三個獨立市場樣本。雙向共用帳戶、每日次數與連虧煞車，因此不能把單向收益或資金路徑直接相加。

這個合約只做多對照與現貨V6不是完全相同實驗：市場成交價、4h合成方向、資金費、標記淨值及費用預留都不同，不能將差額全部歸因於資金費或做空。比較方向效果應使用本表同一合約市場內結果。

## 資料與可重現性

Binance官方2023-12到2025-12的1h成交／標記月檔50份，SHA256全驗證，成交與標記各18,288根；2286筆原始實際資金費含當時funding mark。每年完整UTC曆年，243根暖機。來源／檔案雜湊data/btc-perpetual-1h/manifest.json。

執行python -m scripts.fetch_btc_perpetual_hourly及python -m scripts.research_perpetual_directions。全部12筆都完成，沒有略過失敗期間；每個情境記錄成交、標記與資金費的獨立指紋及完整設定。

完整績效、逐筆交易方向、費用、資金費與資產曲線：data/perpetual-direction-research.json。逐筆方向、風險、止損、部位、有效曝險、槓桿與原因：data/perpetual-direction-audit.json。所有結果均驗證資金＝本金＋已實現淨損益、每日≤2次、持倉≤24h、名目曝險≤50%、方向符合模式。

## 完整績效

|年／方向／成本倍數|指標|值|
|---|---|---|
|2024／long_only／1|average_loss|-15.531308448051725|
|2024／long_only／1|average_win|20.086213765796018|
|2024／long_only／1|cagr|-0.014076280746422642|
|2024／long_only／1|exposure|0.11656232214001139|
|2024／long_only／1|fees|148.72586876396215|
|2024／long_only／1|liquidation_count|0|
|2024／long_only／1|liquidation_fees|0|
|2024／long_only／1|maximum_drawdown|-0.02185521765022802|
|2024／long_only／1|maximum_margin_ratio|0.020039905593290122|
|2024／long_only／1|net_funding|-18.64392218308483|
|2024／long_only／1|number_of_trades|71|
|2024／long_only／1|profit_factor|0.7935990206937065|
|2024／long_only／1|sharpe_ratio|-0.6782072967999563|
|2024／long_only／1|slippage|74.36295955271028|
|2024／long_only／1|sortino_ratio|-0.9734426850952589|
|2024／long_only／1|total_return|-0.014104980003777579|
|2024／long_only／1|win_rate|0.38028169014084506|
|2024／long_only／2|average_loss|-14.561390974836446|
|2024／long_only／2|average_win|16.657256058356793|
|2024／long_only／2|cagr|-0.028403637309828533|
|2024／long_only／2|exposure|0.11656232214001139|
|2024／long_only／2|fees|243.7779772285253|
|2024／long_only／2|liquidation_count|0|
|2024／long_only／2|liquidation_fees|0|
|2024／long_only／2|maximum_drawdown|-0.031940583373707865|
|2024／long_only／2|maximum_margin_ratio|0.020039905593290122|
|2024／long_only／2|net_funding|-15.689850663006144|
|2024／long_only／2|number_of_trades|71|
|2024／long_only／2|profit_factor|0.5841360138988083|
|2024／long_only／2|sharpe_ratio|-1.6087264132129648|
|2024／long_only／2|slippage|121.88908535993794|
|2024／long_only／2|sortino_ratio|-2.203124663092832|
|2024／long_only／2|total_return|-0.02846112304167414|
|2024／long_only／2|win_rate|0.3380281690140845|
|2024／short_only／1|average_loss|-11.896283185567425|
|2024／short_only／1|average_win|28.72394149503061|
|2024／short_only／1|cagr|-0.021486590197105526|
|2024／short_only／1|exposure|0.06317586795674444|
|2024／short_only／1|fees|67.1125484948631|
|2024／short_only／1|liquidation_count|0|
|2024／short_only／1|liquidation_fees|0|
|2024／short_only／1|maximum_drawdown|-0.028555348242350287|
|2024／short_only／1|maximum_margin_ratio|0.021936631326499735|
|2024／short_only／1|net_funding|3.851009852561804|
|2024／short_only／1|number_of_trades|42|
|2024／short_only／1|profit_factor|0.48290614886973277|
|2024／short_only／1|sharpe_ratio|-1.3425984773226327|
|2024／short_only／1|slippage|33.556244626293775|
|2024／short_only／1|sortino_ratio|-1.878346850302205|
|2024／short_only／1|total_return|-0.021530232102964897|
|2024／short_only／1|win_rate|0.16666666666666666|
|2024／short_only／2|average_loss|-11.863305937728848|
|2024／short_only／2|average_win|26.589654831797457|
|2024／short_only／2|cagr|-0.026700022993979555|
|2024／short_only／2|exposure|0.06317586795674444|
|2024／short_only／2|fees|112.95066432437055|
|2024／short_only／2|liquidation_count|0|
|2024／short_only／2|liquidation_fees|0|
|2024／short_only／2|maximum_drawdown|-0.02803269466744307|
|2024／short_only／2|maximum_margin_ratio|0.02195966539786721|
|2024／short_only／2|net_funding|3.3358650812603616|
|2024／short_only／2|number_of_trades|42|
|2024／short_only／2|profit_factor|0.3735560021712895|
|2024／short_only／2|sharpe_ratio|-1.9255212063010596|
|2024／short_only／2|slippage|56.47523071112751|
|2024／short_only／2|sortino_ratio|-2.634407150872339|
|2024／short_only／2|total_return|-0.02675410847674431|
|2024／short_only／2|win_rate|0.14285714285714285|
|2024／both／1|average_loss|-13.612795590732846|
|2024／both／1|average_win|21.89963719332849|
|2024／both／1|cagr|-0.033015658701688766|
|2024／both／1|exposure|0.17973819009675585|
|2024／both／1|fees|211.36132137522478|
|2024／both／1|liquidation_count|0|
|2024／both／1|liquidation_fees|0|
|2024／both／1|maximum_drawdown|-0.03983401434424749|
|2024／both／1|maximum_margin_ratio|0.02193663132649974|
|2024／both／1|net_funding|-14.031091889452787|
|2024／both／1|number_of_trades|113|
|2024／both／1|profit_factor|0.6923750708097839|
|2024／both／1|sharpe_ratio|-1.2759846717191747|
|2024／both／1|slippage|105.68066075007266|
|2024／both／1|sortino_ratio|-1.8087620358604275|
|2024／both／1|total_return|-0.03308231870947387|
|2024／both／1|win_rate|0.3008849557522124|
|2024／both／2|average_loss|-13.14588106306131|
|2024／both／2|average_win|18.14538824105822|
|2024／both／2|cagr|-0.05456572383453262|
|2024／both／2|exposure|0.17973819009675585|
|2024／both／2|fees|348.32198756976084|
|2024／both／2|liquidation_count|0|
|2024／both／2|liquidation_fees|0|
|2024／both／2|maximum_drawdown|-0.05719995449675541|
|2024／both／2|maximum_margin_ratio|0.02195966539786721|
|2024／both／2|net_funding|-12.387714552044645|
|2024／both／2|number_of_trades|113|
|2024／both／2|profit_factor|0.49890715057981677|
|2024／both／2|sharpe_ratio|-2.4891074667028827|
|2024／both／2|slippage|174.160981909073|
|2024／both／2|sortino_ratio|-3.3873237842186597|
|2024／both／2|total_return|-0.05467464810023537|
|2024／both／2|win_rate|0.26548672566371684|
|2025／long_only／1|average_loss|-13.775720761782761|
|2025／long_only／1|average_win|24.655057342724803|
|2025／long_only／1|cagr|-0.007832735827716375|
|2025／long_only／1|exposure|0.038237644104554276|
|2025／long_only／1|fees|55.528637625295545|
|2025／long_only／1|liquidation_count|0|
|2025／long_only／1|liquidation_fees|0|
|2025／long_only／1|maximum_drawdown|-0.0174552207854185|
|2025／long_only／1|maximum_margin_ratio|0.020006011073169825|
|2025／long_only／1|net_funding|-2.516223086527205|
|2025／long_only／1|number_of_trades|28|
|2025／long_only／1|profit_factor|0.7158988707472642|
|2025／long_only／1|sharpe_ratio|-0.746733154603707|
|2025／long_only／1|slippage|27.764320696451055|
|2025／long_only／1|sortino_ratio|-1.0485546009515747|
|2025／long_only／1|total_return|-0.007827395649385283|
|2025／long_only／1|win_rate|0.2857142857142857|
|2025／long_only／2|average_loss|-14.219549570580847|
|2025／long_only／2|average_win|17.885532840551438|
|2025／long_only／2|cagr|-0.014140282658391956|
|2025／long_only／2|exposure|0.038237644104554276|
|2025／long_only／2|fees|95.23867229851656|
|2025／long_only／2|liquidation_count|0|
|2025／long_only／2|liquidation_fees|0|
|2025／long_only／2|maximum_drawdown|-0.021002953034170657|
|2025／long_only／2|maximum_margin_ratio|0.020006011073169825|
|2025／long_only／2|net_funding|-2.174893055716179|
|2025／long_only／2|number_of_trades|28|
|2025／long_only／2|profit_factor|0.5031251588321821|
|2025／long_only／2|sharpe_ratio|-1.5276429079554563|
|2025／long_only／2|slippage|47.61933987543228|
|2025／long_only／2|sortino_ratio|-2.0499521790265267|
|2025／long_only／2|total_return|-0.014130672868720828|
|2025／long_only／2|win_rate|0.2857142857142857|
|2025／short_only／1|average_loss|-12.937039350596205|
|2025／short_only／1|average_win|12.142300885123058|
|2025／short_only／1|cagr|-0.03323917955341449|
|2025／short_only／1|exposure|0.07898641707567629|
|2025／short_only／1|fees|80.10989122353224|
|2025／short_only／1|liquidation_count|0|
|2025／short_only／1|liquidation_fees|0|
|2025／short_only／1|maximum_drawdown|-0.036122793433760236|
|2025／short_only／1|maximum_margin_ratio|0.021543872745499456|
|2025／short_only／1|net_funding|2.8143867271400005|
|2025／short_only／1|number_of_trades|47|
|2025／short_only／1|profit_factor|0.28678489661589435|
|2025／short_only／1|sharpe_ratio|-2.4272146717574614|
|2025／short_only／1|slippage|40.054891907333925|
|2025／short_only／1|sortino_ratio|-3.2239213328163157|
|2025／short_only／1|total_return|-0.03321681068850957|
|2025／short_only／1|win_rate|0.23404255319148937|
|2025／short_only／2|average_loss|-13.047830715438524|
|2025／short_only／2|average_win|9.617262585354736|
|2025／short_only／2|cagr|-0.03868567139883938|
|2025／short_only／2|exposure|0.07898641707567629|
|2025／short_only／2|fees|134.8042598814397|
|2025／short_only／2|liquidation_count|0|
|2025／short_only／2|liquidation_fees|0|
|2025／short_only／2|maximum_drawdown|-0.04099596161483443|
|2025／short_only／2|maximum_margin_ratio|0.021566281999274337|
|2025／short_only／2|net_funding|2.4241493191320433|
|2025／short_only／2|number_of_trades|47|
|2025／short_only／2|profit_factor|0.1992101380598441|
|2025／short_only／2|sharpe_ratio|-3.263976070941704|
|2025／short_only／2|slippage|67.40194312565978|
|2025／short_only／2|sortino_ratio|-4.206285965129996|
|2025／short_only／2|total_return|-0.0386597110617688|
|2025／short_only／2|win_rate|0.2127659574468085|
|2025／both／1|average_loss|-13.342782931763823|
|2025／both／1|average_win|17.26708011766388|
|2025／both／1|cagr|-0.041940228552420966|
|2025／both／1|exposure|0.11722406118023057|
|2025／both／1|fees|133.7910557571056|
|2025／both／1|liquidation_count|0|
|2025／both／1|liquidation_fees|0|
|2025／both／1|maximum_drawdown|-0.047861637822465775|
|2025／both／1|maximum_margin_ratio|0.021543872745499456|
|2025／both／1|net_funding|0.45541680430322606|
|2025／both／1|number_of_trades|75|
|2025／both／1|profit_factor|0.4390743401366117|
|2025／both／1|sharpe_ratio|-2.481683542494105|
|2025／both／1|slippage|66.89547315599283|
|2025／both／1|sortino_ratio|-3.354865969219164|
|2025／both／1|total_return|-0.04191213219431489|
|2025／both／1|win_rate|0.25333333333333335|
|2025／both／2|average_loss|-13.395740962510107|
|2025／both／2|average_win|13.289487573076991|
|2025／both／2|cagr|-0.052469600875849065|
|2025／both／2|exposure|0.11722406118023057|
|2025／both／2|fees|226.30122503837086|
|2025／both／2|liquidation_count|0|
|2025／both／2|liquidation_fees|0|
|2025／both／2|maximum_drawdown|-0.05541530175655218|
|2025／both／2|maximum_margin_ratio|0.02156628199927434|
|2025／both／2|net_funding|0.40254389844739885|
|2025／both／2|number_of_trades|75|
|2025／both／2|profit_factor|0.31328466995441673|
|2025／both／2|sharpe_ratio|-3.5326672954540146|
|2025／both／2|slippage|113.15042722182973|
|2025／both／2|sortino_ratio|-4.60748726024437|
|2025／both／2|total_return|-0.05243464585476865|
|2025／both／2|win_rate|0.24|

## 實作與限制

新增app/strategies/directional_intraday.py及app/backtest/long_short_research.py。DirectionalSignal繼承既有Signal，明確區分方向與多空退出，策略不設定數量；研究引擎自行隔離，不更動原spot BUY/SELL意義。空單損益為qty×(entry-exit)，資金費正值多付空收、負值反向；隔離保證金依方向計算。

159項程式測試通過，含多空損益、保證金不當作支出、正負資金費、雙向費用與滑價、空單跳空超風險、空單標記強平、缺標記／資金費拒絕、空頭方向、不讀未來、每日合計上限及每次run狀態重置。

歷史維持保證金級距未取得，固定2% MMR是研究假設，不是已驗證歷史規則。小時標記極值不能還原盤中次序，採強平先於成交價止損的固定順序；它不代表所有情況都保守。實際時間恰好開盤的funding由原持倉承擔，時段內事件歸開盤交易後持倉，在極值檢查前處理；空單收到資金費若先改善保證金，仍可能低估極值先發生時的風險。沒有ADL、保險基金、委託簿深度與部分成交模型。

強平次數0不證明實盤不會強平。模型內跳空可超止損預算；歷史小時收盤最大回撤低於10%也不保證盤中或未來損失上限。BTC固定標的沒有多幣種存活者選擇，但2024/2025已多次用於研究，全部為調整證據，不稱未見驗證。

研究輸出與現貨dashboard版本分開保存，避免把空單錯當現貨賣出紀錄。尚未接成可執行合約策略或dashboard下單功能；未改live設定，仍需獨立驗證與paper／testnet門檻。

[官方公開資料說明](https://github.com/binance/binance-public-data)與[資金費歷史API](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-History)提供來源定義；本研究未將現貨回報乘槓桿，也未把資金費率插值成虛構事件。
