# PA＋SMC：波段延後確認結果

2026-10-27。portfolio_pa_smc → portfolio_pa_smc_confirmation，單一signal類別變更：波段突破延後一根完整4H確認，之後下一根1H開盤才成交；不採用較快退出或風險遞減。規則及假說見2026-10-27-pa-smc-confirmation-design.md。

每年本金10,000 USDT，BTC多空、多部位共用資金。一般成本為單邊10bps費、5bps滑價；雙成本為20bps／10bps；均含實際funding。全部四筆父快照與資料指紋在研究執行時完整重播一致。

|年度|成本倍數|父收益|候選收益|父回撤|候選回撤|交易數|最高同時部位|
|---|---:|---:|---:|---:|---:|---:|---:|
|2024|1|+2.123%|+2.824%|-4.524%|-3.010%|104|3|
|2024|2|-0.966%|+0.067%|-5.380%|-3.951%|104|3|
|2025|1|-6.002%|-3.935%|-8.005%|-5.096%|94|4|
|2025|2|-7.130%|-4.909%|-8.436%|-5.567%|94|4|

## 判斷

四個期間／成本組合的收益和回撤均優於原PA＋SMC父候選；但2025一般成本仍虧3.935%、雙成本仍虧4.909%，未達兩年各10%目標。2024雙成本只餘0.067%，成本餘裕很薄。可保留作下一輪研究候選，不能升格為可實盤獲利方案，未調高槓桿。

強收盤分組沒有跨年一致優勢，已記錄並未實作；下一根延續的事後分組也未拿原進場價當可執行結果。實際候選等確認後才交易，付出較差進場價或錯過行情的代價。事後24h MFE／MAE僅是診斷路徑，可能跨過原退出點，非已實現收益。

2024／2025已反覆用於調參，非未見驗證。四筆重疊成本實驗不是四份獨立樣本，不能加總其收益或交易數。193項pytest測試通過。新增測試覆蓋多空、真正前一根突破、下一根完成確認、相等／wick拒絕、保留原止損及退出。逐筆實際波段進場也用截至進場前的完成資料重算方向、時間及止損一致。

仍保留1h盤中順序、固定MMR2%非歷史級距、深度與實際滑價、下單精度／最小單量、虛擬多筆隔離與交易所實際倉位模式等限制。未改paper/testnet/live設定、未下單。完整曲線與逐筆交易在data/perpetual-pa-smc-confirmation.json，介面名稱為PA＋SMC波段延後確認（實驗）。

下一步先評估剩餘虧損是否集中在特定市場狀態與方向，尤其確認後仍回落的突破；先保存分組結果，再決定是否有足夠依據測試一項條件。不靠提高槓桿把負期望放大，不掃等待根數。

## 2024／成本1倍

完整指標（含收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding）：

```json
{
  "average_loss": -15.043814954359966,
  "average_win": 31.13080172842458,
  "cagr": 0.028184108625664228,
  "exposure": 0.3347751849743882,
  "fees": 171.71752505171312,
  "liquidation_count": 0,
  "liquidation_fees": 0,
  "maximum_drawdown": -0.03010338607939589,
  "maximum_margin_ratio": 0.023252979975666933,
  "net_funding": -41.84231214753473,
  "number_of_trades": 104,
  "profit_factor": 1.2933388996935546,
  "sharpe_ratio": 0.8004106416344555,
  "slippage": 85.85890798751112,
  "sortino_ratio": 1.1703170331501005,
  "total_return": 0.02824279120579276,
  "win_rate": 0.38461538461538464
}
```

部位／方向／退出原因分組（共享名額與資金，不作獨立因果解釋）：

```json
{
  "swing/1/stop_loss": {
    "count": 10,
    "pnl": -190.89666526930372
  },
  "swing/1/signal": {
    "count": 13,
    "pnl": -17.717529745544468
  },
  "intraday/-1/signal": {
    "count": 10,
    "pnl": -65.83809628516201
  },
  "swing/-1/stop_loss": {
    "count": 7,
    "pnl": -110.05576644105314
  },
  "intraday/1/time_limit": {
    "count": 11,
    "pnl": 261.72245009582304
  },
  "swing/1/time_limit": {
    "count": 11,
    "pnl": 620.1738777210052
  },
  "intraday/1/stop_loss": {
    "count": 11,
    "pnl": -244.8426516512307
  },
  "intraday/1/signal": {
    "count": 17,
    "pnl": -110.59453570746882
  },
  "intraday/-1/time_limit": {
    "count": 6,
    "pnl": 211.77488073207087
  },
  "swing/-1/signal": {
    "count": 3,
    "pnl": -5.2088647653034394
  },
  "swing/-1/time_limit": {
    "count": 1,
    "pnl": 18.9882847241916
  },
  "intraday/-1/stop_loss": {
    "count": 4,
    "pnl": -85.07747135007887
  }
}
```

## 2024／成本2倍

完整指標（含收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding）：

```json
{
  "average_loss": -14.434910724650614,
  "average_win": 26.31998618756934,
  "cagr": 0.0006686735326777438,
  "exposure": 0.3347751849743882,
  "fees": 290.62503083730456,
  "liquidation_count": 0,
  "liquidation_fees": 0,
  "maximum_drawdown": -0.039513872542355055,
  "maximum_margin_ratio": 0.023278162960788662,
  "net_funding": -36.98522986618009,
  "number_of_trades": 104,
  "profit_factor": 1.006928135728108,
  "sharpe_ratio": 0.03686868206424163,
  "slippage": 145.31299504237114,
  "sortino_ratio": 0.053083137496132984,
  "total_return": 0.000670047038846322,
  "win_rate": 0.3557692307692308
}
```

部位／方向／退出原因分組（共享名額與資金，不作獨立因果解釋）：

```json
{
  "swing/1/stop_loss": {
    "count": 10,
    "pnl": -188.82236159792865
  },
  "swing/1/signal": {
    "count": 13,
    "pnl": -38.24891607679459
  },
  "intraday/-1/signal": {
    "count": 10,
    "pnl": -81.702688214848
  },
  "swing/-1/stop_loss": {
    "count": 7,
    "pnl": -109.45667041641283
  },
  "intraday/1/time_limit": {
    "count": 11,
    "pnl": 185.0667541724709
  },
  "swing/1/time_limit": {
    "count": 11,
    "pnl": 533.402804772442
  },
  "intraday/1/stop_loss": {
    "count": 11,
    "pnl": -230.47972279962283
  },
  "intraday/1/signal": {
    "count": 17,
    "pnl": -122.85806901903915
  },
  "intraday/-1/time_limit": {
    "count": 6,
    "pnl": 135.18570034201602
  },
  "swing/-1/signal": {
    "count": 3,
    "pnl": -7.355452338449408
  },
  "swing/-1/time_limit": {
    "count": 1,
    "pnl": 15.728520556482001
  },
  "intraday/-1/stop_loss": {
    "count": 4,
    "pnl": -83.75942899184098
  }
}
```

## 2025／成本1倍

完整指標（含收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding）：

```json
{
  "average_loss": -13.010403909217418,
  "average_win": 17.71280413686586,
  "cagr": -0.03937154613816185,
  "exposure": 0.2681200776167104,
  "fees": 138.27122824941765,
  "liquidation_count": 0,
  "liquidation_fees": 0,
  "maximum_drawdown": -0.050959355317509725,
  "maximum_margin_ratio": 0.022656983414202806,
  "net_funding": -4.112093091776788,
  "number_of_trades": 94,
  "profit_factor": 0.5486375170788451,
  "sharpe_ratio": -1.5864358937055825,
  "slippage": 69.13556864158612,
  "sortino_ratio": -2.1499528296032646,
  "total_return": -0.0393451350222207,
  "win_rate": 0.2872340425531915
}
```

部位／方向／退出原因分組（共享名額與資金，不作獨立因果解釋）：

```json
{
  "swing/1/stop_loss": {
    "count": 13,
    "pnl": -203.33134239437967
  },
  "intraday/1/stop_loss": {
    "count": 4,
    "pnl": -82.51654412707678
  },
  "intraday/-1/signal": {
    "count": 11,
    "pnl": -83.45416190297091
  },
  "swing/1/signal": {
    "count": 10,
    "pnl": 46.63534677481825
  },
  "intraday/1/time_limit": {
    "count": 4,
    "pnl": 14.54707775052702
  },
  "intraday/1/signal": {
    "count": 7,
    "pnl": -46.26560255132134
  },
  "intraday/-1/time_limit": {
    "count": 10,
    "pnl": 171.3745625866236
  },
  "swing/-1/signal": {
    "count": 10,
    "pnl": 13.792335165517361
  },
  "swing/-1/stop_loss": {
    "count": 15,
    "pnl": -222.44881416197433
  },
  "intraday/-1/stop_loss": {
    "count": 7,
    "pnl": -103.51977861086272
  },
  "swing/1/time_limit": {
    "count": 2,
    "pnl": 64.99994887419743
  },
  "swing/-1/time_limit": {
    "count": 1,
    "pnl": 36.73562237471336
  }
}
```

## 2025／成本2倍

完整指標（含收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding）：

```json
{
  "average_loss": -12.195751345447144,
  "average_win": 16.30372830583131,
  "cagr": -0.049124043861435984,
  "exposure": 0.2681200776167104,
  "fees": 229.6129120068468,
  "liquidation_count": 0,
  "liquidation_fees": 0,
  "maximum_drawdown": -0.055668416212023786,
  "maximum_margin_ratio": 0.02268118178613781,
  "net_funding": -3.2800867489515673,
  "number_of_trades": 94,
  "profit_factor": 0.43305978464020173,
  "sharpe_ratio": -2.2624791581101467,
  "slippage": 114.80631279013406,
  "sortino_ratio": -3.02152057846806,
  "total_return": -0.04909125944926218,
  "win_rate": 0.24468085106382978
}
```

部位／方向／退出原因分組（共享名額與資金，不作獨立因果解釋）：

```json
{
  "swing/1/stop_loss": {
    "count": 13,
    "pnl": -200.91650402694128
  },
  "intraday/1/stop_loss": {
    "count": 4,
    "pnl": -83.05825248833403
  },
  "intraday/-1/signal": {
    "count": 11,
    "pnl": -73.29956093064692
  },
  "swing/1/signal": {
    "count": 10,
    "pnl": 30.5983341007381
  },
  "intraday/1/time_limit": {
    "count": 4,
    "pnl": 6.617863678516099
  },
  "intraday/1/signal": {
    "count": 7,
    "pnl": -54.8318954151981
  },
  "intraday/-1/time_limit": {
    "count": 10,
    "pnl": 126.27653028725527
  },
  "swing/-1/signal": {
    "count": 10,
    "pnl": -3.9965295955875066
  },
  "swing/-1/stop_loss": {
    "count": 15,
    "pnl": -222.15567520673616
  },
  "intraday/-1/stop_loss": {
    "count": 7,
    "pnl": -103.86607161707332
  },
  "swing/1/time_limit": {
    "count": 2,
    "pnl": 54.20184648374659
  },
  "swing/-1/time_limit": {
    "count": 1,
    "pnl": 33.51732023763425
  }
}
```
