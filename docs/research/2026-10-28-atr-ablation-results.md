# 舊1H ATR門檻消融：檢討與完整比較

父portfolio_swing_failure_exit → portfolio_sweep_no_atr_floor。只移除短線ATR14/close≥0.006，不繼承斜率risk候選。保留掃單＋三根確認、結構stop、4h方向、原退出／波段失效退出、共用風控、daily2與1x。
每年10,000 USDT，正常單邊費10bps／滑價5bps，雙成本20bps／10bps，含實際mark/funding。全部四筆父指紋與完整結果重現後才跑候選。事前設計及原始訊號盤點見atr-ablation-design.md與data/atr-gate-diagnostics.json。

|年|成本|父收益|子收益|父DD|子DD|總筆數|短線筆數|
|---|---:|---:|---:|---:|---:|---:|---:|
|2024|1|+4.149%|+3.179%|-2.192%|-2.497%|66|25|
|2024|2|+2.475%|+1.512%|-2.471%|-2.828%|67|25|
|2025|1|-0.572%|-1.213%|-2.517%|-2.900%|72|29|
|2025|2|-1.516%|-2.333%|-2.879%|-3.536%|72|29|

未全面改善，不採用為研究基準；原portfolio_swing_failure_exit保留。
檢討：ATR門檻不是短線稀少的主因，完整掃單＋下一根強收盤＋三根結構＋4h方向交集本來很少；移除前原始訊號19/16，移除後26/29，尚未計每日名額／風控與退出。不能承諾每天1–2。
新增交易品質與費用占比需一起看，交易更多不是有效優勢；下方列出新增低ATR成交與被擠掉的原交易（包含原贏家），不得將舊PnL直接相減當子策略收益。
254項pytest通過，逐筆入場/stop/數量與成本風險推導、breakout邊界、共享gross/stoprisk/margin、cash及每日2單均核對。
2024/2025與本診斷全部是調參，沒有未見驗證；年10%目標未達。MMR2%未驗證歷史級距、1h OHLC路徑、深度滑價、precision/min量與虛擬lot映射限制保留。沒有paper/testnet/live升級。

## 2024／成本1倍：全部指標與新增交易

```json
{
  "year": 2024,
  "cost": 1,
  "checks": "passed",
  "metrics": {
    "average_loss": -13.386573772946031,
    "average_win": 38.84832926580214,
    "cagr": 0.03172272645831109,
    "exposure": 0.2363118952760387,
    "fees": 101.37393940286316,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.024967419187163387,
    "maximum_margin_ratio": 0.023252979975666936,
    "net_funding": -37.14237154133146,
    "number_of_trades": 66,
    "profit_factor": 1.5522522239118186,
    "sharpe_ratio": 1.0622929051634105,
    "slippage": 50.68709647450292,
    "sortino_ratio": 1.5763577822721104,
    "total_return": 0.03178889008767638,
    "win_rate": 0.3484848484848485
  },
  "parent_metrics": {
    "average_loss": -13.930111995202777,
    "average_win": 39.84129480100177,
    "cagr": 0.04139982543365872,
    "exposure": 0.2330108138873079,
    "fees": 87.60501738173795,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.021924097242474128,
    "maximum_margin_ratio": 0.023252979975666933,
    "net_funding": -37.041204940423825,
    "number_of_trades": 59,
    "profit_factor": 1.8272760890991069,
    "sharpe_ratio": 1.393163590096627,
    "slippage": 43.80265451951992,
    "sortino_ratio": 2.0551473207064315,
    "total_return": 0.04148657485957341,
    "win_rate": 0.3898305084745763
  },
  "frequency": {
    "total": 66,
    "calendar_days": 366,
    "daily_average": 0.18032786885245902,
    "active_days": 53,
    "zero_entry_days": 313,
    "intraday": 25,
    "intraday_daily_average": 0.06830601092896176,
    "intraday_active_days": 24,
    "groups": [
      {
        "sleeve": "intraday",
        "direction": 1,
        "count": 16,
        "daily_average": 0.04371584699453552
      },
      {
        "sleeve": "intraday",
        "direction": -1,
        "count": 9,
        "daily_average": 0.02459016393442623
      },
      {
        "sleeve": "swing",
        "direction": 1,
        "count": 33,
        "daily_average": 0.09016393442622951
      },
      {
        "sleeve": "swing",
        "direction": -1,
        "count": 8,
        "daily_average": 0.02185792349726776
      }
    ]
  },
  "added_low_atr_fills": [
    {
      "position_id": "intraday:1706187600000:3",
      "direction": -1,
      "entry_ms": 1706187600000,
      "pnl": -16.068140932095716,
      "fees": 3.292940565840861,
      "funding": 0.3283256404565311,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1713880800000:17",
      "direction": 1,
      "entry_ms": 1713880800000,
      "pnl": -16.39645314894226,
      "fees": 3.4551942870204613,
      "funding": -0.09778001915729825,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1725732000000:38",
      "direction": -1,
      "entry_ms": 1725732000000,
      "pnl": -14.467067109314343,
      "fees": 2.9822974239547717,
      "funding": -0.11127971245429123,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1728489600000:43",
      "direction": 1,
      "entry_ms": 1728489600000,
      "pnl": -24.00354605487471,
      "fees": 3.4136171796980737,
      "funding": 0,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1729692000000:46",
      "direction": 1,
      "entry_ms": 1729692000000,
      "pnl": -24.10325581182685,
      "fees": 3.6200936169303484,
      "funding": 0,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1730055600000:48",
      "direction": -1,
      "entry_ms": 1730055600000,
      "pnl": -23.474743182053064,
      "fees": 4.814001038039095,
      "funding": 0,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1730300400000:52",
      "direction": 1,
      "entry_ms": 1730300400000,
      "pnl": -11.24328988473937,
      "fees": 2.962637115743794,
      "funding": -0.44448844158021006,
      "exit_reason": "signal"
    }
  ],
  "displaced_parent_trades": [],
  "grouped": {
    "swing/1/stop_loss": {
      "count": 8,
      "pnl": -146.9118215291173
    },
    "intraday/-1/signal": {
      "count": 5,
      "pnl": -40.9428210159612
    },
    "swing/-1/stop_loss": {
      "count": 4,
      "pnl": -59.986888487467695
    },
    "swing/1/breakout_failure": {
      "count": 5,
      "pnl": -33.508439709971555
    },
    "intraday/1/time_limit": {
      "count": 6,
      "pnl": 171.7934274085948
    },
    "swing/1/time_limit": {
      "count": 10,
      "pnl": 611.8214968828055
    },
    "swing/1/signal": {
      "count": 10,
      "pnl": -18.5910556557548
    },
    "swing/-1/signal": {
      "count": 2,
      "pnl": -10.322352349119413
    },
    "swing/-1/breakout_failure": {
      "count": 2,
      "pnl": -19.78014968991768
    },
    "intraday/1/signal": {
      "count": 4,
      "pnl": 33.165504011907196
    },
    "intraday/1/stop_loss": {
      "count": 6,
      "pnl": -109.39498879678378
    },
    "intraday/-1/time_limit": {
      "count": 2,
      "pnl": -24.024811446606844
    },
    "intraday/-1/stop_loss": {
      "count": 2,
      "pnl": -35.42819874583721
    }
  },
  "parent_executed_price_pnl": 539.5119709179025,
  "child_executed_price_pnl": 456.4052118209646
}
```

## 2024／成本2倍：全部指標與新增交易

```json
{
  "year": 2024,
  "cost": 2,
  "checks": "passed",
  "metrics": {
    "average_loss": -13.6255380480926,
    "average_win": 32.6409222253629,
    "cagr": 0.015090533868302725,
    "exposure": 0.2363118952760387,
    "fees": 177.0622543577584,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.028284743649771293,
    "maximum_margin_ratio": 0.023278162960788662,
    "net_funding": -33.77929901330072,
    "number_of_trades": 67,
    "profit_factor": 1.2522294674855408,
    "sharpe_ratio": 0.5657740084246415,
    "slippage": 88.53157776954282,
    "sortino_ratio": 0.8284686807151155,
    "total_return": 0.015121753706725194,
    "win_rate": 0.34328358208955223
  },
  "parent_metrics": {
    "average_loss": -14.044512185349495,
    "average_win": 33.354510669027036,
    "cagr": 0.024699339588851954,
    "exposure": 0.2330108138873079,
    "fees": 154.966687396521,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.024708957743533988,
    "maximum_margin_ratio": 0.023278162960788662,
    "net_funding": -33.69722772822824,
    "number_of_trades": 60,
    "profit_factor": 1.4762979829306409,
    "sharpe_ratio": 0.9254086136951009,
    "slippage": 77.48385735282352,
    "sortino_ratio": 1.3495283452922182,
    "total_return": 0.024750679452968605,
    "win_rate": 0.38333333333333336
  },
  "frequency": {
    "total": 67,
    "calendar_days": 366,
    "daily_average": 0.1830601092896175,
    "active_days": 53,
    "zero_entry_days": 313,
    "intraday": 25,
    "intraday_daily_average": 0.06830601092896176,
    "intraday_active_days": 24,
    "groups": [
      {
        "sleeve": "intraday",
        "direction": 1,
        "count": 16,
        "daily_average": 0.04371584699453552
      },
      {
        "sleeve": "intraday",
        "direction": -1,
        "count": 9,
        "daily_average": 0.02459016393442623
      },
      {
        "sleeve": "swing",
        "direction": 1,
        "count": 34,
        "daily_average": 0.09289617486338798
      },
      {
        "sleeve": "swing",
        "direction": -1,
        "count": 8,
        "daily_average": 0.02185792349726776
      }
    ]
  },
  "added_low_atr_fills": [
    {
      "position_id": "intraday:1706187600000:3",
      "direction": -1,
      "entry_ms": 1706187600000,
      "pnl": -17.526091973014026,
      "fees": 5.4944485309882936,
      "funding": 0.27391402282757626,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1713880800000:17",
      "direction": 1,
      "entry_ms": 1713880800000,
      "pnl": -17.848486132569597,
      "fees": 5.715683184865439,
      "funding": -0.08087514997547463,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1725732000000:39",
      "direction": -1,
      "entry_ms": 1725732000000,
      "pnl": -15.956759193569535,
      "fees": 5.024981260495676,
      "funding": -0.09374945952745747,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1728489600000:44",
      "direction": 1,
      "entry_ms": 1728489600000,
      "pnl": -24.009468070057288,
      "fees": 5.628306469004407,
      "funding": 0,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1729692000000:47",
      "direction": 1,
      "entry_ms": 1729692000000,
      "pnl": -24.09778150039443,
      "fees": 5.907644885377874,
      "funding": 0,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1730055600000:49",
      "direction": -1,
      "entry_ms": 1730055600000,
      "pnl": -23.679089402156578,
      "fees": 7.427173316550021,
      "funding": 0,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1730300400000:53",
      "direction": 1,
      "entry_ms": 1730300400000,
      "pnl": -13.20680434489913,
      "fees": 4.988383545469889,
      "funding": -0.3742065537358393,
      "exit_reason": "signal"
    }
  ],
  "displaced_parent_trades": [],
  "grouped": {
    "swing/1/stop_loss": {
      "count": 9,
      "pnl": -152.7486896600817
    },
    "intraday/-1/signal": {
      "count": 5,
      "pnl": -45.596397376681935
    },
    "swing/-1/stop_loss": {
      "count": 4,
      "pnl": -60.037458826338266
    },
    "swing/1/breakout_failure": {
      "count": 5,
      "pnl": -37.03159671779132
    },
    "intraday/1/time_limit": {
      "count": 6,
      "pnl": 124.0610896359692
    },
    "swing/1/time_limit": {
      "count": 10,
      "pnl": 536.8439176846686
    },
    "swing/1/signal": {
      "count": 10,
      "pnl": -32.406371256536346
    },
    "swing/-1/signal": {
      "count": 2,
      "pnl": -11.211084174050134
    },
    "swing/-1/breakout_failure": {
      "count": 2,
      "pnl": -20.052919875161685
    },
    "intraday/1/signal": {
      "count": 4,
      "pnl": 19.82371944240301
    },
    "intraday/1/stop_loss": {
      "count": 6,
      "pnl": -109.07220113829538
    },
    "intraday/-1/time_limit": {
      "count": 2,
      "pnl": -25.7382004798351
    },
    "intraday/-1/stop_loss": {
      "count": 2,
      "pnl": -35.616270190996566
    }
  },
  "parent_executed_price_pnl": 436.17070965443975,
  "child_executed_price_pnl": 362.05909043833145
}
```

## 2025／成本1倍：全部指標與新增交易

```json
{
  "year": 2025,
  "cost": 1,
  "checks": "passed",
  "metrics": {
    "average_loss": -10.786086693695058,
    "average_win": 21.98018958810244,
    "cagr": -0.01213552737541268,
    "exposure": 0.21059239812806757,
    "fees": 109.99649917492093,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.02899506229038895,
    "maximum_margin_ratio": 0.021957946303772773,
    "net_funding": -6.9181994217662925,
    "number_of_trades": 72,
    "profit_factor": 0.7837800040387938,
    "sharpe_ratio": -0.5396343859204208,
    "slippage": 54.99826224751511,
    "sortino_ratio": -0.7751310251736568,
    "total_return": -0.012127271631008796,
    "win_rate": 0.2777777777777778
  },
  "parent_metrics": {
    "average_loss": -11.881714000724664,
    "average_win": 22.003216685457183,
    "cagr": -0.005724651381584733,
    "exposure": 0.19803675379522886,
    "fees": 81.34102705903094,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.02517035245774435,
    "maximum_margin_ratio": 0.021957946303772773,
    "net_funding": -6.821681521561439,
    "number_of_trades": 59,
    "profit_factor": 0.8796313330681689,
    "sharpe_ratio": -0.2512295747706979,
    "slippage": 40.67053143596015,
    "sortino_ratio": -0.36124723918731383,
    "total_return": -0.005720744300528713,
    "win_rate": 0.3220338983050847
  },
  "frequency": {
    "total": 72,
    "calendar_days": 365,
    "daily_average": 0.19726027397260273,
    "active_days": 62,
    "zero_entry_days": 303,
    "intraday": 29,
    "intraday_daily_average": 0.07945205479452055,
    "intraday_active_days": 28,
    "groups": [
      {
        "sleeve": "intraday",
        "direction": 1,
        "count": 11,
        "daily_average": 0.030136986301369864
      },
      {
        "sleeve": "intraday",
        "direction": -1,
        "count": 18,
        "daily_average": 0.049315068493150684
      },
      {
        "sleeve": "swing",
        "direction": 1,
        "count": 24,
        "daily_average": 0.06575342465753424
      },
      {
        "sleeve": "swing",
        "direction": -1,
        "count": 19,
        "daily_average": 0.052054794520547946
      }
    ]
  },
  "added_low_atr_fills": [
    {
      "position_id": "intraday:1735826400000:1",
      "direction": -1,
      "entry_ms": 1735826400000,
      "pnl": -22.161852986775827,
      "fees": 5.692763116318798,
      "funding": 0,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1739775600000:6",
      "direction": 1,
      "entry_ms": 1739775600000,
      "pnl": -11.248226221517863,
      "fees": 2.40236090036944,
      "funding": -0.07683092484652408,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1739890800000:7",
      "direction": -1,
      "entry_ms": 1739890800000,
      "pnl": -9.696861025808012,
      "fees": 1.760105062036981,
      "funding": 0.21742715150982622,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1748858400000:29",
      "direction": -1,
      "entry_ms": 1748858400000,
      "pnl": -4.203366201999455,
      "fees": 1.44697504059438,
      "funding": 0.03223082375284474,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1749423600000:30",
      "direction": -1,
      "entry_ms": 1749423600000,
      "pnl": -2.336522646392963,
      "fees": 2.184075579179037,
      "funding": -0.02363520394552156,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1749740400000:32",
      "direction": 1,
      "entry_ms": 1749740400000,
      "pnl": -11.427239799090191,
      "fees": 1.8214049108497683,
      "funding": -0.010901139155945436,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1749938400000:33",
      "direction": 1,
      "entry_ms": 1749938400000,
      "pnl": -1.8953538675765058,
      "fees": 1.773165279500612,
      "funding": 0,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1750993200000:36",
      "direction": 1,
      "entry_ms": 1750993200000,
      "pnl": -11.30827755393351,
      "fees": 2.059585806031167,
      "funding": -0.02743697968603646,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1751425200000:37",
      "direction": 1,
      "entry_ms": 1751425200000,
      "pnl": 23.825446103843333,
      "fees": 2.0648041626307863,
      "funding": -0.12926232158456427,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1753333200000:41",
      "direction": -1,
      "entry_ms": 1753333200000,
      "pnl": -10.977330776720981,
      "fees": 3.175347066696699,
      "funding": 0,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1753347600000:42",
      "direction": 1,
      "entry_ms": 1753347600000,
      "pnl": -17.081240377193385,
      "fees": 2.6798792706997014,
      "funding": -0.2691085850352403,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1753603200000:43",
      "direction": -1,
      "entry_ms": 1753603200000,
      "pnl": -10.518986170572973,
      "fees": 3.5371049608454377,
      "funding": 0,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1759024800000:54",
      "direction": -1,
      "entry_ms": 1759024800000,
      "pnl": -8.254740354033931,
      "fees": 3.0205679803158243,
      "funding": 0.07516909125699488,
      "exit_reason": "signal"
    }
  ],
  "displaced_parent_trades": [],
  "grouped": {
    "intraday/-1/stop_loss": {
      "count": 7,
      "pnl": -90.22719871045183
    },
    "swing/1/stop_loss": {
      "count": 7,
      "pnl": -119.16200254619282
    },
    "intraday/1/stop_loss": {
      "count": 4,
      "pnl": -58.036739772486726
    },
    "swing/1/signal": {
      "count": 10,
      "pnl": 65.71581487133685
    },
    "intraday/-1/signal": {
      "count": 5,
      "pnl": -35.468821004955345
    },
    "swing/-1/signal": {
      "count": 6,
      "pnl": 27.58998673467883
    },
    "swing/-1/stop_loss": {
      "count": 4,
      "pnl": -59.10883349020751
    },
    "swing/-1/breakout_failure": {
      "count": 8,
      "pnl": -64.78175187488155
    },
    "swing/1/breakout_failure": {
      "count": 5,
      "pnl": -43.90777139516344
    },
    "intraday/1/signal": {
      "count": 4,
      "pnl": -33.16138885000255
    },
    "intraday/-1/time_limit": {
      "count": 6,
      "pnl": 155.04937900148497
    },
    "intraday/1/time_limit": {
      "count": 3,
      "pnl": 31.31063730913742
    },
    "swing/1/time_limit": {
      "count": 2,
      "pnl": 65.51135312680032
    },
    "swing/-1/time_limit": {
      "count": 1,
      "pnl": 37.40462029080917
    }
  },
  "parent_executed_price_pnl": 30.955265575292305,
  "child_executed_price_pnl": -4.358017713407027
}
```

## 2025／成本2倍：全部指標與新增交易

```json
{
  "year": 2025,
  "cost": 2,
  "checks": "passed",
  "metrics": {
    "average_loss": -10.683129430785344,
    "average_win": 19.088525467457025,
    "cagr": -0.023345344243302812,
    "exposure": 0.21059239812806757,
    "fees": 180.84362369688276,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.03536071485985892,
    "maximum_margin_ratio": 0.021981013765317733,
    "net_funding": -5.656565287377653,
    "number_of_trades": 72,
    "profit_factor": 0.5955971856102399,
    "sharpe_ratio": -1.2067248327819362,
    "slippage": 90.42185547494974,
    "sortino_ratio": -1.7024920655895728,
    "total_return": -0.02332955308481921,
    "win_rate": 0.25
  },
  "parent_metrics": {
    "average_loss": -11.449247090317385,
    "average_win": 19.36894761788156,
    "cagr": -0.015169930976807744,
    "exposure": 0.19803675379522886,
    "fees": 136.57102340986847,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.02879256212101089,
    "maximum_margin_ratio": 0.021981013765317726,
    "net_funding": -5.570988199995605,
    "number_of_trades": 59,
    "profit_factor": 0.6847447757221886,
    "sharpe_ratio": -0.7876556563560773,
    "slippage": 68.28557053624392,
    "sortino_ratio": -1.1138488164767593,
    "total_return": -0.015159626828935902,
    "win_rate": 0.288135593220339
  },
  "frequency": {
    "total": 72,
    "calendar_days": 365,
    "daily_average": 0.19726027397260273,
    "active_days": 62,
    "zero_entry_days": 303,
    "intraday": 29,
    "intraday_daily_average": 0.07945205479452055,
    "intraday_active_days": 28,
    "groups": [
      {
        "sleeve": "intraday",
        "direction": 1,
        "count": 11,
        "daily_average": 0.030136986301369864
      },
      {
        "sleeve": "intraday",
        "direction": -1,
        "count": 18,
        "daily_average": 0.049315068493150684
      },
      {
        "sleeve": "swing",
        "direction": 1,
        "count": 24,
        "daily_average": 0.06575342465753424
      },
      {
        "sleeve": "swing",
        "direction": -1,
        "count": 19,
        "daily_average": 0.052054794520547946
      }
    ]
  },
  "added_low_atr_fills": [
    {
      "position_id": "intraday:1735826400000:1",
      "direction": -1,
      "entry_ms": 1735826400000,
      "pnl": -22.885421286886835,
      "fees": 8.487111472082262,
      "funding": 0,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1739775600000:6",
      "direction": 1,
      "entry_ms": 1739775600000,
      "pnl": -11.499185579977329,
      "fees": 3.7201264622467076,
      "funding": -0.059487378937232195,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1739890800000:7",
      "direction": -1,
      "entry_ms": 1739890800000,
      "pnl": -10.161687269404753,
      "fees": 2.8995119167300754,
      "funding": 0.17908911453725485,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1748858400000:29",
      "direction": -1,
      "entry_ms": 1748858400000,
      "pnl": -5.394058033682617,
      "fees": 2.4490996873908686,
      "funding": 0.027276366845843402,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1749423600000:30",
      "direction": -1,
      "entry_ms": 1749423600000,
      "pnl": -4.412900694761414,
      "fees": 3.434431782134106,
      "funding": -0.01858303675047269,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1749740400000:32",
      "direction": 1,
      "entry_ms": 1749740400000,
      "pnl": -11.534921369294358,
      "fees": 2.967623097954891,
      "funding": -0.008880616012166253,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1749938400000:33",
      "direction": 1,
      "entry_ms": 1749938400000,
      "pnl": -3.731466326928805,
      "fees": 2.9050968556854904,
      "funding": 0,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1750993200000:36",
      "direction": 1,
      "entry_ms": 1750993200000,
      "pnl": -11.448786917164718,
      "fees": 3.275504766837262,
      "funding": -0.021817439887497965,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1751425200000:37",
      "direction": 1,
      "entry_ms": 1751425200000,
      "pnl": 16.527055072307125,
      "fees": 3.2925974799619717,
      "funding": -0.10306342607930419,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1753333200000:41",
      "direction": -1,
      "entry_ms": 1753333200000,
      "pnl": -13.099217177008622,
      "fees": 5.285090304342722,
      "funding": 0,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1753347600000:42",
      "direction": 1,
      "entry_ms": 1753347600000,
      "pnl": -18.025257810996386,
      "fees": 4.578500769755692,
      "funding": -0.22988179663209435,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1753603200000:43",
      "direction": -1,
      "entry_ms": 1753603200000,
      "pnl": -10.978353590418557,
      "fees": 4.907738704433776,
      "funding": 0,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1759024800000:54",
      "direction": -1,
      "entry_ms": 1759024800000,
      "pnl": -9.249902763866421,
      "fees": 4.370540017922879,
      "funding": 0.054382042879015824,
      "exit_reason": "signal"
    }
  ],
  "displaced_parent_trades": [],
  "grouped": {
    "intraday/-1/stop_loss": {
      "count": 7,
      "pnl": -91.91555193075992
    },
    "swing/1/stop_loss": {
      "count": 7,
      "pnl": -119.44800870654262
    },
    "intraday/1/stop_loss": {
      "count": 4,
      "pnl": -58.60829464497666
    },
    "swing/1/signal": {
      "count": 10,
      "pnl": 47.7886613652332
    },
    "intraday/-1/signal": {
      "count": 5,
      "pnl": -42.31776593872383
    },
    "swing/-1/signal": {
      "count": 6,
      "pnl": 17.937624730803677
    },
    "swing/-1/stop_loss": {
      "count": 4,
      "pnl": -59.163470111315696
    },
    "swing/-1/breakout_failure": {
      "count": 8,
      "pnl": -68.77402389854163
    },
    "swing/1/breakout_failure": {
      "count": 5,
      "pnl": -41.0268289658233
    },
    "intraday/1/signal": {
      "count": 4,
      "pnl": -37.32328996408389
    },
    "intraday/-1/time_limit": {
      "count": 6,
      "pnl": 114.19781160222338
    },
    "intraday/1/time_limit": {
      "count": 3,
      "pnl": 16.579312780192765
    },
    "swing/1/time_limit": {
      "count": 2,
      "pnl": 54.67863207638344
    },
    "swing/-1/time_limit": {
      "count": 1,
      "pnl": 34.09966075774896
    }
  },
  "parent_executed_price_pnl": -9.454256679479592,
  "child_executed_price_pnl": -46.79534186392172
}
```
