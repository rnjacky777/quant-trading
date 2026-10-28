# 確認後失敗的方向／行情與效率過濾結果

2026-10-28。portfolio_pa_smc_confirmation → portfolio_confirmed_efficiency，僅新增波段ER20≥0.3的進場條件。設計在2026-10-28-confirmed-efficiency-design.md預先保存，沒有掃窗口或門檻。

## 原父候選虧損集中在哪裡

失敗在此指扣費後虧損，不等於證明是假突破。2024一般成本波段多單34筆、19虧，淨+411.56USDT；空單11筆、9虧，淨−96.28。2025多單25筆、17虧，淨−91.70；空單26筆、20虧，淨−171.92。2025空單最差月份為6月4筆−58.56、8月7筆−55.51、3月2筆−48.40；多單1月4筆−64.43與8月3筆−46.48較差。月份僅描述，不作季節交易條件。

用進場當時20次4H收盤變動的ER分類：2025低方向效率ER<0.3的波段9筆虧8筆，淨−93.90；ER≥0.3仍有42筆、29虧，淨−169.72。因此不能把全部損失歸因盤整。2024低ER僅6筆，合計約+0.02，樣本很小。2024較高ER空單8筆全虧，淨−107.83，更說明『有趨勢就能做空賺錢』沒有依據。

SMA60斜率同向已涵蓋2025全部26筆波段空單，新增同向斜率不能排除它們。2025確認收盤越過原突破wick的多空24筆合計約−267.66，比未越過wick組差，故未再加更強收盤條件。SMA間距≥1ATR的2025多空33筆合計約−271.05，但2024同組盈利，故不依單一年份刪掉它。

2025短線多單另虧−114.24、短線空單−15.60，僅改波段無法解決所有來源。分組重疊、部位共享名額及資金，不能把差異解讀為獨立因果，也不能加總重複成本案例。完整四筆方向／月份／行情／退出分組、費用滑價funding與逐筆特徵在data/confirmed-failure-diagnostics.json。

## 完整實驗結果

每年重設10,000USDT，BTC永續多空、多部位、實際1x。一般單邊費10bps／滑價5bps，雙成本20bps／10bps，含實際funding。四筆父快照與行情／mark／funding指紋完整重播一致才跑子候選。

|年|成本倍數|父收益|新收益|父回撤|新回撤|交易數|最高同時部位|
|---|---:|---:|---:|---:|---:|---:|---:|
|2024|1|+2.824%|+3.054%|-3.010%|-2.970%|101|4|
|2024|2|+0.067%|-0.081%|-3.951%|-4.217%|101|5|
|2025|1|-3.935%|-3.003%|-5.096%|-4.292%|85|4|
|2025|2|-4.909%|-3.933%|-5.567%|-4.713%|85|4|

## 判斷、來源與限制

一般成本兩年收益及回撤改善；2025雙成本也改善，但2024雙成本由+0.067%降至−0.081%，回撤由3.951%增至4.217%，所以不是全面優勝。2025仍虧3.003%，不達每年淨收益10%目標；僅保留研究候選，不增加槓桿或實盤部署。

ER概念參考[QuantConnect官方文件](https://www.quantconnect.com/docs/v2/writing-algorithms/indicators/supported-indicators/kaufman-efficiency-ratio)與[官方LEAN實作](https://github.com/QuantConnect/Lean/blob/master/Indicators/KaufmanEfficiencyRatio.cs)。本次明定20次變動，零路徑回傳0；非完全相同暖機慣例。這些來源沒有證明0.3為最佳值或BTC有正期望，門檻只有本次事前固定測試的意義。

196項pytest測試通過；驗證多空對稱、完成4H、過濾不阻擋退出、趨勢時止損一致、效率計算及尺度不變。保存審計核對四筆資料指紋、父設定不變、現金／逐筆損益對帳、部位ID、每日≤2、全部1x、每次進場的總曝險／總止損風險／不可重用保證金上限；逐筆波段訊號用截至進場前資料重算。這些是進場限制，不宣稱持倉後市場變動永不超標。

2024／2025均已用於調參，非未見驗證。只研究事前固定BTC，未處理其他市場的倖存者選樣；無跨資產可泛化證據。仍有1h盤中路徑、平面MMR2%非歷史級距、深度／滑價、實際下單精度及最小單量、虛擬獨立部位與交易所實際倉位模式差異。未改paper/testnet/live，未下單。完整曲線及交易在data/perpetual-confirmed-efficiency.json，儀表板名稱PA＋SMC確認後效率過濾（實驗）。

## 2024／成本1倍完整指標

包含收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding：

```json
{
  "average_loss": -15.11828530619079,
  "average_win": 31.863824096076215,
  "cagr": 0.03047202842589769,
  "exposure": 0.30096755833807626,
  "fees": 168.23863728510398,
  "liquidation_count": 0,
  "liquidation_fees": 0,
  "maximum_drawdown": -0.02969728199849264,
  "maximum_margin_ratio": 0.023252979975666933,
  "net_funding": -41.196495046053386,
  "number_of_trades": 101,
  "profit_factor": 1.3257702719446494,
  "sharpe_ratio": 0.9091562217951892,
  "slippage": 84.11946837005519,
  "sortino_ratio": 1.3333626949030122,
  "total_return": 0.030535545076314063,
  "win_rate": 0.38613861386138615
}
```

分策略／方向／退出原因（描述性）：

```json
{
  "swing/1/stop_loss": {
    "count": 11,
    "pnl": -197.09346180447716
  },
  "intraday/-1/signal": {
    "count": 10,
    "pnl": -65.90956575066875
  },
  "swing/-1/stop_loss": {
    "count": 6,
    "pnl": -96.7790624182681
  },
  "intraday/1/time_limit": {
    "count": 12,
    "pnl": 309.2305325934599
  },
  "swing/1/signal": {
    "count": 11,
    "pnl": -25.82989762665754
  },
  "swing/1/time_limit": {
    "count": 11,
    "pnl": 621.2446461796317
  },
  "intraday/1/stop_loss": {
    "count": 11,
    "pnl": -245.20959051217355
  },
  "intraday/1/signal": {
    "count": 17,
    "pnl": -110.78797592252562
  },
  "intraday/-1/time_limit": {
    "count": 6,
    "pnl": 212.0453770537929
  },
  "swing/-1/signal": {
    "count": 2,
    "pnl": -10.333253249858593
  },
  "intraday/-1/stop_loss": {
    "count": 4,
    "pnl": -85.22229777911166
  }
}
```

## 2024／成本2倍完整指標

包含收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding：

```json
{
  "average_loss": -14.30499429050049,
  "average_win": 26.74480952628108,
  "cagr": -0.0008044777363203082,
  "exposure": 0.30096755833807626,
  "fees": 280.4262319190377,
  "liquidation_count": 0,
  "liquidation_fees": 0,
  "maximum_drawdown": -0.042166618376891174,
  "maximum_margin_ratio": 0.02327816296078866,
  "net_funding": -36.523393642809474,
  "number_of_trades": 101,
  "profit_factor": 0.9914616705637282,
  "sharpe_ratio": -0.011737392674295263,
  "slippage": 140.21356506141274,
  "sortino_ratio": -0.016851289646115323,
  "total_return": -0.000806128975319953,
  "win_rate": 0.3465346534653465
}
```

分策略／方向／退出原因（描述性）：

```json
{
  "swing/1/stop_loss": {
    "count": 12,
    "pnl": -201.53713794079434
  },
  "intraday/-1/signal": {
    "count": 10,
    "pnl": -81.71526815175723
  },
  "swing/-1/stop_loss": {
    "count": 6,
    "pnl": -96.34694779413924
  },
  "intraday/1/time_limit": {
    "count": 11,
    "pnl": 184.84531084313298
  },
  "swing/1/signal": {
    "count": 11,
    "pnl": -39.401589284553786
  },
  "swing/1/time_limit": {
    "count": 11,
    "pnl": 538.862935629103
  },
  "intraday/1/stop_loss": {
    "count": 11,
    "pnl": -230.1509528102868
  },
  "intraday/1/signal": {
    "count": 17,
    "pnl": -122.77507461392739
  },
  "intraday/-1/time_limit": {
    "count": 6,
    "pnl": 134.96749736861003
  },
  "swing/-1/signal": {
    "count": 2,
    "pnl": -11.114447220201566
  },
  "intraday/-1/stop_loss": {
    "count": 4,
    "pnl": -83.69561577838024
  }
}
```

## 2025／成本1倍完整指標

包含收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding：

```json
{
  "average_loss": -13.098555618676043,
  "average_win": 18.172209899246887,
  "cagr": -0.030053991197581342,
  "exposure": 0.2444926378267321,
  "fees": 128.31101384885662,
  "liquidation_count": 0,
  "liquidation_fees": 0,
  "maximum_drawdown": -0.042921371143793574,
  "maximum_margin_ratio": 0.0226569834142028,
  "net_funding": -5.291518159530415,
  "number_of_trades": 85,
  "profit_factor": 0.6113721795825482,
  "sharpe_ratio": -1.2692918904961452,
  "slippage": 64.15548127959347,
  "sortino_ratio": -1.7426998533306284,
  "total_return": -0.030033732412145353,
  "win_rate": 0.3058823529411765
}
```

分策略／方向／退出原因（描述性）：

```json
{
  "swing/1/stop_loss": {
    "count": 12,
    "pnl": -180.29714912738095
  },
  "intraday/1/stop_loss": {
    "count": 4,
    "pnl": -82.55972430580627
  },
  "intraday/-1/signal": {
    "count": 11,
    "pnl": -83.73274776842281
  },
  "swing/1/signal": {
    "count": 9,
    "pnl": 58.17549797386169
  },
  "intraday/1/time_limit": {
    "count": 4,
    "pnl": 14.575803977660247
  },
  "intraday/1/signal": {
    "count": 7,
    "pnl": -46.616149479802445
  },
  "intraday/-1/time_limit": {
    "count": 10,
    "pnl": 172.75242621100386
  },
  "swing/-1/signal": {
    "count": 8,
    "pnl": 14.015588041356988
  },
  "swing/-1/stop_loss": {
    "count": 10,
    "pnl": -164.90302997655957
  },
  "intraday/-1/stop_loss": {
    "count": 7,
    "pnl": -103.9534919451339
  },
  "swing/1/time_limit": {
    "count": 2,
    "pnl": 65.15889428107087
  },
  "swing/-1/time_limit": {
    "count": 1,
    "pnl": 37.04675799668489
  }
}
```

## 2025／成本2倍完整指標

包含收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding：

```json
{
  "average_loss": -12.152397018857757,
  "average_win": 16.921984957871288,
  "cagr": -0.039358136617469563,
  "exposure": 0.2444926378267321,
  "fees": 211.75470180319033,
  "liquidation_count": 0,
  "liquidation_fees": 0,
  "maximum_drawdown": -0.04713477804219368,
  "maximum_margin_ratio": 0.02268118178613781,
  "net_funding": -4.331547460663529,
  "number_of_trades": 85,
  "profit_factor": 0.48626329268975943,
  "sharpe_ratio": -1.9084155938081524,
  "slippage": 105.87727954777498,
  "sortino_ratio": -2.5839267405021014,
  "total_return": -0.03933173431148573,
  "win_rate": 0.25882352941176473
}
```

分策略／方向／退出原因（描述性）：

```json
{
  "swing/1/stop_loss": {
    "count": 12,
    "pnl": -177.84061934007798
  },
  "intraday/1/stop_loss": {
    "count": 4,
    "pnl": -83.10175984573365
  },
  "intraday/-1/signal": {
    "count": 11,
    "pnl": -73.53788588716618
  },
  "swing/1/signal": {
    "count": 9,
    "pnl": 43.39665212769141
  },
  "intraday/1/time_limit": {
    "count": 4,
    "pnl": 6.6289876671611445
  },
  "intraday/1/signal": {
    "count": 7,
    "pnl": -55.26116672575914
  },
  "intraday/-1/time_limit": {
    "count": 10,
    "pnl": 127.35264395046636
  },
  "swing/-1/signal": {
    "count": 8,
    "pnl": -0.07747847149904619
  },
  "swing/-1/stop_loss": {
    "count": 10,
    "pnl": -164.7019840815658
  },
  "intraday/-1/stop_loss": {
    "count": 7,
    "pnl": -104.32955919625816
  },
  "swing/1/time_limit": {
    "count": 2,
    "pnl": 54.334620590819284
  },
  "swing/-1/time_limit": {
    "count": 1,
    "pnl": 33.82020609705129
  }
}
```
