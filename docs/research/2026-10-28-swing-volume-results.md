# 波段確認成交量：檢討與全年比較

父portfolio_swing_failure_exit → portfolio_swing_volume；只加確認4h volume≥之前20根4h平均量。短線及原波段退出／固定失效邊界、風控全部保留。未沿用斜率risk或移除ATR候選。事前設計見2026-10-28-swing-volume-design.md。
每年本金10,000 USDT、1x，正常單邊fee/slip10/5bps、double20/10bps，含實際mark/funding。四筆父完整快照與資料指紋一致後才測子候選。

|年|成本|父收益|子收益|父DD|子DD|總筆數|短線筆數|
|---|---:|---:|---:|---:|---:|---:|---:|
|2024|1|+4.149%|+4.183%|-2.192%|-2.356%|53|18|
|2024|2|+2.475%|+2.654%|-2.471%|-2.584%|53|18|
|2025|1|-0.572%|-0.551%|-2.517%|-2.395%|54|16|
|2025|2|-1.516%|-1.410%|-2.879%|-2.782%|54|16|

四組收益全升：True；四組回撤均不退步：False。
判斷：不是全面升級，不取代原portfolio_swing_failure_exit研究基準，保留取捨／失敗證據。
少量低量交易分組雖虧，排除後仍有共享資金、連虧guard及名額路徑改變；不可用舊PnL相減推算新收益。排除原贏家逐筆保留如下。
2024/2025與成交量分組都是調參，不能叫未見驗證；目前每年10%目標未達。此規則會減少波段訊號，不解決短線18/16筆的頻率；不把成交量當勝率或加槓桿理由。
256項pytest通過；核對完成4h volume不含確認bar的歷史基準、入場/stop、成本risk sizing、gross/stoprisk/margin、cash/PnL、daily2與獨立lot失效邊界。
MMR2%非已驗證歷史級距、1h OHLC盤中路徑、precision/min量、滑價深度與虛擬lot映射限制保留。無交易所訂單／paper/testnet/live變更。

## 2024／成本1倍完整指標與排除代價

```json
{
  "year": 2024,
  "cost": 1,
  "checks": "passed",
  "metrics": {
    "average_loss": -15.32980325708103,
    "average_win": 40.61287673625553,
    "cagr": 0.04173846555709715,
    "exposure": 0.2136596471257826,
    "fees": 81.54141287174106,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.023555401472814652,
    "maximum_margin_ratio": 0.023252979975666933,
    "net_funding": -35.896739004424546,
    "number_of_trades": 53,
    "profit_factor": 1.8801312105195298,
    "sharpe_ratio": 1.4441244130666673,
    "slippage": 40.770850552962784,
    "sortino_ratio": 2.134826732801025,
    "total_return": 0.041825938722808376,
    "win_rate": 0.41509433962264153
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
    "total": 53,
    "calendar_days": 366,
    "daily_average": 0.1448087431693989,
    "active_days": 44,
    "zero_entry_days": 322,
    "intraday": 18,
    "intraday_daily_average": 0.04918032786885246,
    "intraday_active_days": 18,
    "groups": [
      {
        "sleeve": "intraday",
        "direction": 1,
        "count": 12,
        "daily_average": 0.03278688524590164
      },
      {
        "sleeve": "intraday",
        "direction": -1,
        "count": 6,
        "daily_average": 0.01639344262295082
      },
      {
        "sleeve": "swing",
        "direction": 1,
        "count": 27,
        "daily_average": 0.07377049180327869
      },
      {
        "sleeve": "swing",
        "direction": -1,
        "count": 8,
        "daily_average": 0.02185792349726776
      }
    ]
  },
  "parent_volume_groups": {
    "1/volume_pass=True": {
      "count": 27,
      "pnl": 424.3138048504652
    },
    "-1/volume_pass=True": {
      "count": 8,
      "pnl": -90.35342395521346
    },
    "1/volume_pass=False": {
      "count": 6,
      "pnl": -9.296273982038015
    }
  },
  "filtered_parent_trades": [
    {
      "position_id": "swing:1706443200000:3",
      "direction": 1,
      "pnl": -8.984627863946411,
      "confirmation_volume": 30902.798,
      "prior20_mean": 37918.5677
    },
    {
      "position_id": "swing:1706572800000:5",
      "direction": 1,
      "pnl": -8.65320819694146,
      "confirmation_volume": 22428.970999999998,
      "prior20_mean": 37959.67445
    },
    {
      "position_id": "swing:1713830400000:15",
      "direction": 1,
      "pnl": -3.6967669135715844,
      "confirmation_volume": 31961.435,
      "prior20_mean": 38577.542
    },
    {
      "position_id": "swing:1715817600000:18",
      "direction": 1,
      "pnl": -2.289348921918747,
      "confirmation_volume": 37064.181,
      "prior20_mean": 44768.3367
    },
    {
      "position_id": "swing:1720958400000:26",
      "direction": 1,
      "pnl": 23.53079286147284,
      "confirmation_volume": 26938.154,
      "prior20_mean": 38380.97505
    },
    {
      "position_id": "swing:1730188800000:43",
      "direction": 1,
      "pnl": -9.203114947132653,
      "confirmation_volume": 27074.597,
      "prior20_mean": 28859.7784
    }
  ],
  "filtered_parent_winners": [
    {
      "position_id": "swing:1720958400000:26",
      "direction": 1,
      "pnl": 23.53079286147284,
      "confirmation_volume": 26938.154,
      "prior20_mean": 38380.97505
    }
  ],
  "grouped": {
    "swing/1/stop_loss": {
      "count": 8,
      "pnl": -154.0023622058566
    },
    "swing/-1/stop_loss": {
      "count": 4,
      "pnl": -60.1832908824097
    },
    "intraday/1/time_limit": {
      "count": 5,
      "pnl": 203.3821375977677
    },
    "swing/1/time_limit": {
      "count": 10,
      "pnl": 616.0335918464955
    },
    "swing/1/signal": {
      "count": 7,
      "pnl": -31.168585661204055
    },
    "intraday/-1/signal": {
      "count": 4,
      "pnl": -31.59253967435368
    },
    "swing/-1/signal": {
      "count": 2,
      "pnl": -10.363435509513945
    },
    "swing/-1/breakout_failure": {
      "count": 2,
      "pnl": -19.905711555468045
    },
    "intraday/1/signal": {
      "count": 3,
      "pnl": 48.31772213774025
    },
    "intraday/1/stop_loss": {
      "count": 4,
      "pnl": -86.44008116003859
    },
    "swing/1/breakout_failure": {
      "count": 2,
      "pnl": -12.308916603208214
    },
    "intraday/-1/time_limit": {
      "count": 1,
      "pnl": -19.34169173455657
    },
    "intraday/-1/stop_loss": {
      "count": 1,
      "pnl": -24.167449367284306
    }
  }
}
```

## 2024／成本2倍完整指標與排除代價

```json
{
  "year": 2024,
  "cost": 2,
  "checks": "passed",
  "metrics": {
    "average_loss": -15.575002185426497,
    "average_win": 34.01169385784859,
    "cagr": 0.026488113784022937,
    "exposure": 0.2136596471257826,
    "fees": 143.49970337005172,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.025839047308768848,
    "maximum_margin_ratio": 0.023278162960788662,
    "net_funding": -32.69843071870292,
    "number_of_trades": 53,
    "profit_factor": 1.549748169378112,
    "sharpe_ratio": 1.0201592962339043,
    "slippage": 71.75036506571841,
    "sortino_ratio": 1.49275122817226,
    "total_return": 0.02654321971244289,
    "win_rate": 0.41509433962264153
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
    "total": 53,
    "calendar_days": 366,
    "daily_average": 0.1448087431693989,
    "active_days": 44,
    "zero_entry_days": 322,
    "intraday": 18,
    "intraday_daily_average": 0.04918032786885246,
    "intraday_active_days": 18,
    "groups": [
      {
        "sleeve": "intraday",
        "direction": 1,
        "count": 12,
        "daily_average": 0.03278688524590164
      },
      {
        "sleeve": "intraday",
        "direction": -1,
        "count": 6,
        "daily_average": 0.01639344262295082
      },
      {
        "sleeve": "swing",
        "direction": 1,
        "count": 27,
        "daily_average": 0.07377049180327869
      },
      {
        "sleeve": "swing",
        "direction": -1,
        "count": 8,
        "daily_average": 0.02185792349726776
      }
    ]
  },
  "parent_volume_groups": {
    "1/volume_pass=True": {
      "count": 27,
      "pnl": 333.8050849053652
    },
    "-1/volume_pass=True": {
      "count": 8,
      "pnl": -91.56240949556256
    },
    "1/volume_pass=False": {
      "count": 7,
      "pnl": -17.476368181074157
    }
  },
  "filtered_parent_trades": [
    {
      "position_id": "swing:1706443200000:3",
      "direction": 1,
      "pnl": -9.334738832505387,
      "confirmation_volume": 30902.798,
      "prior20_mean": 37918.5677
    },
    {
      "position_id": "swing:1706572800000:5",
      "direction": 1,
      "pnl": -9.030433510775039,
      "confirmation_volume": 22428.970999999998,
      "prior20_mean": 37959.67445
    },
    {
      "position_id": "swing:1713830400000:15",
      "direction": 1,
      "pnl": -4.5162904919996265,
      "confirmation_volume": 31961.435,
      "prior20_mean": 38577.542
    },
    {
      "position_id": "swing:1715817600000:18",
      "direction": 1,
      "pnl": -3.138492631937733,
      "confirmation_volume": 37064.181,
      "prior20_mean": 44768.3367
    },
    {
      "position_id": "swing:1721102400000:30",
      "direction": 1,
      "pnl": -0.574554870784208,
      "confirmation_volume": 33143.185,
      "prior20_mean": 39649.3701
    },
    {
      "position_id": "swing:1720958400000:26",
      "direction": 1,
      "pnl": 19.98442222615185,
      "confirmation_volume": 26938.154,
      "prior20_mean": 38380.97505
    },
    {
      "position_id": "swing:1730188800000:44",
      "direction": 1,
      "pnl": -10.866280069224013,
      "confirmation_volume": 27074.597,
      "prior20_mean": 28859.7784
    }
  ],
  "filtered_parent_winners": [
    {
      "position_id": "swing:1720958400000:26",
      "direction": 1,
      "pnl": 19.98442222615185,
      "confirmation_volume": 26938.154,
      "prior20_mean": 38380.97505
    }
  ],
  "grouped": {
    "swing/1/stop_loss": {
      "count": 8,
      "pnl": -153.02755958877913
    },
    "swing/-1/stop_loss": {
      "count": 4,
      "pnl": -60.25049418439363
    },
    "intraday/1/time_limit": {
      "count": 5,
      "pnl": 153.26812575895184
    },
    "swing/1/time_limit": {
      "count": 10,
      "pnl": 540.9306365867301
    },
    "swing/1/signal": {
      "count": 7,
      "pnl": -39.090086671974916
    },
    "intraday/-1/signal": {
      "count": 4,
      "pnl": -35.4104967533266
    },
    "swing/-1/signal": {
      "count": 2,
      "pnl": -11.266695616855838
    },
    "swing/-1/breakout_failure": {
      "count": 2,
      "pnl": -20.18261693826883
    },
    "intraday/1/signal": {
      "count": 3,
      "pnl": 34.932989827631616
    },
    "intraday/1/stop_loss": {
      "count": 4,
      "pnl": -86.14563964660016
    },
    "swing/1/breakout_failure": {
      "count": 2,
      "pnl": -14.329257662948617
    },
    "intraday/-1/time_limit": {
      "count": 1,
      "pnl": -19.825327628392195
    },
    "intraday/-1/stop_loss": {
      "count": 1,
      "pnl": -24.17138035732611
    }
  }
}
```

## 2025／成本1倍完整指標與排除代價

```json
{
  "year": 2025,
  "cost": 1,
  "checks": "passed",
  "metrics": {
    "average_loss": -13.512751065440852,
    "average_win": 21.989934745811432,
    "cagr": -0.005517518817172884,
    "exposure": 0.18924780276224176,
    "fees": 77.4479179499726,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.023953535871204523,
    "maximum_margin_ratio": 0.021957946303772777,
    "net_funding": -6.575508373167887,
    "number_of_trades": 54,
    "profit_factor": 0.8834169363377338,
    "sharpe_ratio": -0.2543387782939535,
    "slippage": 38.72397587745068,
    "sortino_ratio": -0.37262203846044517,
    "total_return": -0.00551375271200083,
    "win_rate": 0.35185185185185186
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
    "total": 54,
    "calendar_days": 365,
    "daily_average": 0.14794520547945206,
    "active_days": 46,
    "zero_entry_days": 319,
    "intraday": 16,
    "intraday_daily_average": 0.043835616438356165,
    "intraday_active_days": 16,
    "groups": [
      {
        "sleeve": "intraday",
        "direction": 1,
        "count": 5,
        "daily_average": 0.0136986301369863
      },
      {
        "sleeve": "intraday",
        "direction": -1,
        "count": 11,
        "daily_average": 0.030136986301369864
      },
      {
        "sleeve": "swing",
        "direction": 1,
        "count": 23,
        "daily_average": 0.06301369863013699
      },
      {
        "sleeve": "swing",
        "direction": -1,
        "count": 15,
        "daily_average": 0.0410958904109589
      }
    ]
  },
  "parent_volume_groups": {
    "1/volume_pass=True": {
      "count": 22,
      "pnl": -27.512820230676546
    },
    "1/volume_pass=False": {
      "count": 2,
      "pnl": -4.419485428009879
    },
    "-1/volume_pass=True": {
      "count": 15,
      "pnl": -37.494999140489
    },
    "-1/volume_pass=False": {
      "count": 4,
      "pnl": -21.81562584571721
    }
  },
  "filtered_parent_trades": [
    {
      "position_id": "swing:1737100800000:3",
      "direction": 1,
      "pnl": -3.5040986552370317,
      "confirmation_volume": 16966.096,
      "prior20_mean": 36736.10525
    },
    {
      "position_id": "swing:1741651200000:8",
      "direction": -1,
      "pnl": -6.929166396449063,
      "confirmation_volume": 39532.566,
      "prior20_mean": 48045.0318
    },
    {
      "position_id": "swing:1745611200000:22",
      "direction": 1,
      "pnl": -0.9153867727728475,
      "confirmation_volume": 31103.127,
      "prior20_mean": 40105.11225
    },
    {
      "position_id": "swing:1755648000000:38",
      "direction": -1,
      "pnl": -4.771377023485478,
      "confirmation_volume": 14498.385,
      "prior20_mean": 17362.944649999998
    },
    {
      "position_id": "swing:1758844800000:41",
      "direction": -1,
      "pnl": -5.874392902348753,
      "confirmation_volume": 16440.324,
      "prior20_mean": 21239.98915
    },
    {
      "position_id": "swing:1760659200000:51",
      "direction": -1,
      "pnl": -4.240689523433918,
      "confirmation_volume": 15470.185,
      "prior20_mean": 33713.94675
    }
  ],
  "filtered_parent_winners": [],
  "grouped": {
    "swing/1/stop_loss": {
      "count": 8,
      "pnl": -143.74088000064305
    },
    "intraday/1/stop_loss": {
      "count": 1,
      "pnl": -24.106420492644705
    },
    "swing/-1/signal": {
      "count": 5,
      "pnl": 33.44749878087059
    },
    "swing/-1/stop_loss": {
      "count": 4,
      "pnl": -59.33334492196683
    },
    "intraday/-1/stop_loss": {
      "count": 5,
      "pnl": -81.08069767425607
    },
    "swing/1/breakout_failure": {
      "count": 4,
      "pnl": -43.22689574893356
    },
    "intraday/1/signal": {
      "count": 2,
      "pnl": -24.241161651334203
    },
    "intraday/-1/time_limit": {
      "count": 6,
      "pnl": 156.0613708160039
    },
    "intraday/1/time_limit": {
      "count": 2,
      "pnl": 7.49870579036618
    },
    "swing/1/time_limit": {
      "count": 2,
      "pnl": 65.62447499468836
    },
    "swing/1/signal": {
      "count": 9,
      "pnl": 69.54191808096695
    },
    "swing/-1/breakout_failure": {
      "count": 5,
      "pnl": -49.23712837424436
    },
    "swing/-1/time_limit": {
      "count": 1,
      "pnl": 37.655033281114136
    }
  }
}
```

## 2025／成本2倍完整指標與排除代價

```json
{
  "year": 2025,
  "cost": 2,
  "checks": "passed",
  "metrics": {
    "average_loss": -12.71153846867232,
    "average_win": 19.370019354232603,
    "cagr": -0.014113250982448422,
    "exposure": 0.18924780276224176,
    "fees": 128.44887177120435,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.02781594745132454,
    "maximum_margin_ratio": 0.021981013765317733,
    "net_funding": -5.34400164579989,
    "number_of_trades": 54,
    "profit_factor": 0.700130723291162,
    "sharpe_ratio": -0.7719090281077841,
    "slippage": 64.22449286637028,
    "sortino_ratio": -1.1132007187358877,
    "total_return": -0.014103659431890292,
    "win_rate": 0.3148148148148148
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
    "total": 54,
    "calendar_days": 365,
    "daily_average": 0.14794520547945206,
    "active_days": 46,
    "zero_entry_days": 319,
    "intraday": 16,
    "intraday_daily_average": 0.043835616438356165,
    "intraday_active_days": 16,
    "groups": [
      {
        "sleeve": "intraday",
        "direction": 1,
        "count": 5,
        "daily_average": 0.0136986301369863
      },
      {
        "sleeve": "intraday",
        "direction": -1,
        "count": 11,
        "daily_average": 0.030136986301369864
      },
      {
        "sleeve": "swing",
        "direction": 1,
        "count": 23,
        "daily_average": 0.06301369863013699
      },
      {
        "sleeve": "swing",
        "direction": -1,
        "count": 15,
        "daily_average": 0.0410958904109589
      }
    ]
  },
  "parent_volume_groups": {
    "1/volume_pass=True": {
      "count": 22,
      "pnl": -48.27176229046459
    },
    "1/volume_pass=False": {
      "count": 2,
      "pnl": -9.957182199543187
    },
    "-1/volume_pass=True": {
      "count": 15,
      "pnl": -51.7873679611436
    },
    "-1/volume_pass=False": {
      "count": 4,
      "pnl": -24.7393287703079
    }
  },
  "filtered_parent_trades": [
    {
      "position_id": "swing:1737100800000:3",
      "direction": 1,
      "pnl": -5.287066917304459,
      "confirmation_volume": 16966.096,
      "prior20_mean": 36736.10525
    },
    {
      "position_id": "swing:1741651200000:8",
      "direction": -1,
      "pnl": -7.883343893642267,
      "confirmation_volume": 39532.566,
      "prior20_mean": 48045.0318
    },
    {
      "position_id": "swing:1745611200000:22",
      "direction": 1,
      "pnl": -4.6701152822387275,
      "confirmation_volume": 31103.127,
      "prior20_mean": 40105.11225
    },
    {
      "position_id": "swing:1755648000000:38",
      "direction": -1,
      "pnl": -5.518326218513228,
      "confirmation_volume": 14498.385,
      "prior20_mean": 17362.944649999998
    },
    {
      "position_id": "swing:1758844800000:41",
      "direction": -1,
      "pnl": -6.505053565904466,
      "confirmation_volume": 16440.324,
      "prior20_mean": 21239.98915
    },
    {
      "position_id": "swing:1760659200000:51",
      "direction": -1,
      "pnl": -4.832605092247936,
      "confirmation_volume": 15470.185,
      "prior20_mean": 33713.94675
    }
  ],
  "filtered_parent_winners": [],
  "grouped": {
    "swing/1/stop_loss": {
      "count": 8,
      "pnl": -144.16892887659446
    },
    "intraday/1/stop_loss": {
      "count": 1,
      "pnl": -24.1807394194044
    },
    "swing/-1/signal": {
      "count": 5,
      "pnl": 24.361302540027165
    },
    "swing/-1/stop_loss": {
      "count": 4,
      "pnl": -59.458339412894176
    },
    "intraday/-1/stop_loss": {
      "count": 5,
      "pnl": -81.78147536177934
    },
    "swing/1/breakout_failure": {
      "count": 4,
      "pnl": -36.62886700309862
    },
    "intraday/1/signal": {
      "count": 2,
      "pnl": -26.04127310664208
    },
    "intraday/-1/time_limit": {
      "count": 6,
      "pnl": 115.2711452313217
    },
    "intraday/1/time_limit": {
      "count": 2,
      "pnl": 0.053014834020306045
    },
    "swing/1/time_limit": {
      "count": 2,
      "pnl": 54.79573636606949
    },
    "swing/1/signal": {
      "count": 9,
      "pnl": 53.425122247778916
    },
    "swing/-1/breakout_failure": {
      "count": 5,
      "pnl": -51.10506774968509
    },
    "swing/-1/time_limit": {
      "count": 1,
      "pnl": 34.421775391959095
    }
  }
}
```
