# 短線+1R價格保護：止盈止損檢討與全年比較

父portfolio_swing_failure_exit → portfolio_intraday_protection。短線完成1h收盤達初始價格風險+1R後，stop移至實際進場價，下一根生效；原stop在當根先執行。原短線進場/24h、波段/失效退出、共享風控保留，非固定百分比止盈。事前假說見2026-10-28-intraday-protection-design.md。
正常單邊fee/slip10/5bps、double20/10bps，實際funding/mark，每年重設10,000 USDT，全部1x。先完整重現四筆父結果與資料指紋。

|年|成本|父收益|子收益|父DD|子DD|總筆數|短線筆數|
|---|---:|---:|---:|---:|---:|---:|---:|
|2024|1|+4.149%|+4.397%|-2.192%|-2.192%|59|18|
|2024|2|+2.475%|+2.639%|-2.471%|-2.471%|60|18|
|2025|1|-0.572%|-0.551%|-2.517%|-2.497%|59|16|
|2025|2|-1.516%|-1.541%|-2.879%|-2.904%|59|16|

四組收益均改善：False；四組回撤不退步：False。
判斷：保留取捨／失敗結果，不取代父研究基準。
價格保護不等於淨保本：費用、滑價、funding與跳空仍可能虧損；不是每筆固定止盈，也未替波段啟用原失敗1R保護。共用風險與連虧路徑會改變後續數量，共同進場事件不能直接當獨立因果收益。
262項pytest通過；另逐筆核對首次完成close觸發、下一根生效、初始stop保留、保護成交價、多空數量推導、gross/stoprisk/margin、ID、每日2與cash/PnL。
2024/2025與診斷全部是調參，不是未見驗證；每年10%目標未達，短線頻率仍不足。原1h OHLC路徑、固定MMR2%非歷史級距、滑價深度、precision/min單量及虛擬多lot映射限制保留，未動paper/testnet/live或下單。

## 2024／成本1倍完整指標與提前保護代價

```json
{
  "year": 2024,
  "cost": 1,
  "checks": "passed",
  "metrics": {
    "average_loss": -13.395911633627117,
    "average_win": 40.0862897447256,
    "cagr": 0.043881126834297124,
    "exposure": 0.2330108138873079,
    "fees": 88.0563074894245,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.021924097242474128,
    "maximum_margin_ratio": 0.023252979975666933,
    "net_funding": -37.242574797234404,
    "number_of_trades": 59,
    "profit_factor": 1.911828460438371,
    "sharpe_ratio": 1.4769346705487678,
    "slippage": 44.02830600946524,
    "sortino_ratio": 2.1924716256600267,
    "total_return": 0.04397318453181143,
    "win_rate": 0.3898305084745763
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
    "total": 59,
    "calendar_days": 366,
    "daily_average": 0.16120218579234974,
    "active_days": 49,
    "zero_entry_days": 317,
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
  "parent_giveback_diagnostics": {
    "swing/reached_1R=False": {
      "count": 24,
      "pnl": -300.044909859353,
      "losses": 23
    },
    "intraday/reached_1R=True": {
      "count": 6,
      "pnl": 205.86895102701905,
      "losses": 1
    },
    "swing/reached_1R=True": {
      "count": 17,
      "pnl": 624.7090167725667,
      "losses": 4
    },
    "intraday/reached_1R=False": {
      "count": 12,
      "pnl": -115.66730934449194,
      "losses": 8
    }
  },
  "stop_updates": [
    {
      "position_id": "intraday:1706486400000:4",
      "update": {
        "activation_r": 1.0,
        "active_from_ms": 1706544000000,
        "decision_timestamp_ms": 1706540400000,
        "from_stop": 41600.0,
        "initial_stop": 41600.0,
        "to_stop": 42042.21059999999,
        "trigger_close": 42623.2
      }
    },
    {
      "position_id": "intraday:1715259600000:17",
      "update": {
        "activation_r": 1.0,
        "active_from_ms": 1715288400000,
        "decision_timestamp_ms": 1715284800000,
        "from_stop": 60550.0,
        "initial_stop": 60550.0,
        "to_stop": 61511.5404,
        "trigger_close": 62580.0
      }
    },
    {
      "position_id": "intraday:1721919600000:30",
      "update": {
        "activation_r": 1.0,
        "active_from_ms": 1721955600000,
        "decision_timestamp_ms": 1721952000000,
        "from_stop": 63710.0,
        "initial_stop": 63710.0,
        "to_stop": 64837.4025,
        "trigger_close": 66358.4
      }
    },
    {
      "position_id": "intraday:1726682400000:36",
      "update": {
        "activation_r": 1.0,
        "active_from_ms": 1726704000000,
        "decision_timestamp_ms": 1726700400000,
        "from_stop": 59138.0,
        "initial_stop": 59138.0,
        "to_stop": 60009.88995,
        "trigger_close": 61735.3
      }
    },
    {
      "position_id": "intraday:1727319600000:39",
      "update": {
        "activation_r": 1.0,
        "active_from_ms": 1727348400000,
        "decision_timestamp_ms": 1727344800000,
        "from_stop": 62634.4,
        "initial_stop": 62634.4,
        "to_stop": 63351.76005,
        "trigger_close": 64373.8
      }
    },
    {
      "position_id": "intraday:1733148000000:51",
      "update": {
        "activation_r": 1.0,
        "active_from_ms": 1733155200000,
        "decision_timestamp_ms": 1733151600000,
        "from_stop": 94826.0,
        "initial_stop": 94826.0,
        "to_stop": 95787.36975,
        "trigger_close": 97106.5
      }
    }
  ],
  "common_protected_exits": [
    {
      "parent_position_id": "intraday:1733148000000:51",
      "child_position_id": "intraday:1733148000000:51",
      "parent_pnl": -24.67948417207865,
      "child_pnl": -5.141205744257009,
      "parent_exit": "stop_loss"
    }
  ],
  "protected_parent_winners": []
}
```

## 2024／成本2倍完整指標與提前保護代價

```json
{
  "year": 2024,
  "cost": 2,
  "checks": "passed",
  "metrics": {
    "average_loss": -13.602989520384504,
    "average_win": 33.354809612,
    "cagr": 0.026330227623686753,
    "exposure": 0.2330108138873079,
    "fees": 155.03701301715924,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.024708957743533988,
    "maximum_margin_ratio": 0.023278162960788662,
    "net_funding": -33.69790779400229,
    "number_of_trades": 60,
    "profit_factor": 1.5242289798739637,
    "sharpe_ratio": 0.9888484114501004,
    "slippage": 77.51903661254181,
    "sortino_ratio": 1.4488572005046525,
    "total_return": 0.026385000882176213,
    "win_rate": 0.38333333333333336
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
    "total": 60,
    "calendar_days": 366,
    "daily_average": 0.16393442622950818,
    "active_days": 49,
    "zero_entry_days": 317,
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
  "parent_giveback_diagnostics": {
    "swing/reached_1R=False": {
      "count": 25,
      "pnl": -308.95810699199546,
      "losses": 24
    },
    "intraday/reached_1R=True": {
      "count": 6,
      "pnl": 150.83402928079215,
      "losses": 1
    },
    "swing/reached_1R=True": {
      "count": 17,
      "pnl": 533.7244142207239,
      "losses": 4
    },
    "intraday/reached_1R=False": {
      "count": 12,
      "pnl": -128.09354197983012,
      "losses": 8
    }
  },
  "stop_updates": [
    {
      "position_id": "intraday:1706486400000:4",
      "update": {
        "activation_r": 1.0,
        "active_from_ms": 1706544000000,
        "decision_timestamp_ms": 1706540400000,
        "from_stop": 41600.0,
        "initial_stop": 41600.0,
        "to_stop": 42063.22119999999,
        "trigger_close": 42623.2
      }
    },
    {
      "position_id": "intraday:1715259600000:17",
      "update": {
        "activation_r": 1.0,
        "active_from_ms": 1715288400000,
        "decision_timestamp_ms": 1715284800000,
        "from_stop": 60550.0,
        "initial_stop": 60550.0,
        "to_stop": 61542.28079999999,
        "trigger_close": 62580.0
      }
    },
    {
      "position_id": "intraday:1721919600000:31",
      "update": {
        "activation_r": 1.0,
        "active_from_ms": 1721955600000,
        "decision_timestamp_ms": 1721952000000,
        "from_stop": 63710.0,
        "initial_stop": 63710.0,
        "to_stop": 64869.80499999999,
        "trigger_close": 66358.4
      }
    },
    {
      "position_id": "intraday:1726682400000:37",
      "update": {
        "activation_r": 1.0,
        "active_from_ms": 1726704000000,
        "decision_timestamp_ms": 1726700400000,
        "from_stop": 59138.0,
        "initial_stop": 59138.0,
        "to_stop": 60039.87989999999,
        "trigger_close": 61735.3
      }
    },
    {
      "position_id": "intraday:1727319600000:40",
      "update": {
        "activation_r": 1.0,
        "active_from_ms": 1727348400000,
        "decision_timestamp_ms": 1727344800000,
        "from_stop": 62634.4,
        "initial_stop": 62634.4,
        "to_stop": 63383.42009999999,
        "trigger_close": 64373.8
      }
    },
    {
      "position_id": "intraday:1733148000000:52",
      "update": {
        "activation_r": 1.0,
        "active_from_ms": 1733155200000,
        "decision_timestamp_ms": 1733151600000,
        "from_stop": 94826.0,
        "initial_stop": 94826.0,
        "to_stop": 95835.2395,
        "trigger_close": 97106.5
      }
    }
  ],
  "common_protected_exits": [
    {
      "parent_position_id": "intraday:1733148000000:52",
      "child_position_id": "intraday:1733148000000:52",
      "parent_pnl": -24.591265041118646,
      "child_pnl": -8.075396763396313,
      "parent_exit": "stop_loss"
    }
  ],
  "protected_parent_winners": []
}
```

## 2025／成本1倍完整指標與提前保護代價

```json
{
  "year": 2025,
  "cost": 1,
  "checks": "passed",
  "metrics": {
    "average_loss": -11.438453336121906,
    "average_win": 22.991706854104496,
    "cagr": -0.005516351651417506,
    "exposure": 0.1964387626983221,
    "fees": 80.2529679109305,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.024966266382893343,
    "maximum_margin_ratio": 0.021957946303772773,
    "net_funding": -6.718517496251609,
    "number_of_trades": 59,
    "profit_factor": 0.8824549775810882,
    "sharpe_ratio": -0.24376202427958915,
    "slippage": 40.12650194849183,
    "sortino_ratio": -0.35166351320353767,
    "total_return": -0.00551258634071039,
    "win_rate": 0.3050847457627119
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
    "total": 59,
    "calendar_days": 365,
    "daily_average": 0.16164383561643836,
    "active_days": 50,
    "zero_entry_days": 315,
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
  "parent_giveback_diagnostics": {
    "swing/reached_1R=True": {
      "count": 18,
      "pnl": 166.26251442601966,
      "losses": 6
    },
    "intraday/reached_1R=False": {
      "count": 11,
      "pnl": -132.50684800594502,
      "losses": 9
    },
    "swing/reached_1R=False": {
      "count": 25,
      "pnl": -257.5054450709123,
      "losses": 24
    },
    "intraday/reached_1R=True": {
      "count": 5,
      "pnl": 166.54233564553758,
      "losses": 1
    }
  },
  "stop_updates": [
    {
      "position_id": "intraday:1743555600000:15",
      "update": {
        "activation_r": 1.0,
        "active_from_ms": 1743573600000,
        "decision_timestamp_ms": 1743570000000,
        "from_stop": 85595.5,
        "initial_stop": 85595.5,
        "to_stop": 84875.9408,
        "trigger_close": 84075.1
      }
    },
    {
      "position_id": "intraday:1744772400000:19",
      "update": {
        "activation_r": 1.0,
        "active_from_ms": 1744819200000,
        "decision_timestamp_ms": 1744815600000,
        "from_stop": 83063.9,
        "initial_stop": 83063.9,
        "to_stop": 83903.23065,
        "trigger_close": 84810.7
      }
    },
    {
      "position_id": "intraday:1750118400000:27",
      "update": {
        "activation_r": 1.0,
        "active_from_ms": 1750176000000,
        "decision_timestamp_ms": 1750172400000,
        "from_stop": 108900.0,
        "initial_stop": 108900.0,
        "to_stop": 106696.72495000002,
        "trigger_close": 104199.2
      }
    },
    {
      "position_id": "intraday:1760623200000:49",
      "update": {
        "activation_r": 1.0,
        "active_from_ms": 1760630400000,
        "decision_timestamp_ms": 1760626800000,
        "from_stop": 111960.0,
        "initial_stop": 111960.0,
        "to_stop": 110739.30265,
        "trigger_close": 108474.0
      }
    },
    {
      "position_id": "intraday:1763622000000:57",
      "update": {
        "activation_r": 1.0,
        "active_from_ms": 1763654400000,
        "decision_timestamp_ms": 1763650800000,
        "from_stop": 93150.0,
        "initial_stop": 93150.0,
        "to_stop": 91892.2309,
        "trigger_close": 89835.4
      }
    }
  ],
  "common_protected_exits": [
    {
      "parent_position_id": "intraday:1743555600000:15",
      "child_position_id": "intraday:1743555600000:15",
      "parent_pnl": -11.269241745273048,
      "child_pnl": -2.539826210446198,
      "parent_exit": "stop_loss"
    },
    {
      "parent_position_id": "intraday:1744772400000:19",
      "child_position_id": "intraday:1744772400000:19",
      "parent_pnl": 1.1320094871056758,
      "child_pnl": -2.3579134094619105,
      "parent_exit": "time_limit"
    }
  ],
  "protected_parent_winners": [
    {
      "parent_position_id": "intraday:1744772400000:19",
      "child_position_id": "intraday:1744772400000:19",
      "parent_pnl": 1.1320094871056758,
      "child_pnl": -2.3579134094619105,
      "parent_exit": "time_limit"
    }
  ]
}
```

## 2025／成本2倍完整指標與提前保護代價

```json
{
  "year": 2025,
  "cost": 2,
  "checks": "passed",
  "metrics": {
    "average_loss": -11.506710788281454,
    "average_win": 19.36460500162853,
    "cagr": -0.015418828693171682,
    "exposure": 0.19689533158315262,
    "fees": 136.54288240585788,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.029037848984025172,
    "maximum_margin_ratio": 0.021981013765317726,
    "net_funding": -5.559310911150762,
    "number_of_trades": 59,
    "profit_factor": 0.681172452287879,
    "sharpe_ratio": -0.8030718906033035,
    "slippage": 68.27149749304748,
    "sortino_ratio": -1.136776814200654,
    "total_return": -0.015408356808014445,
    "win_rate": 0.288135593220339
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
    "total": 59,
    "calendar_days": 365,
    "daily_average": 0.16164383561643836,
    "active_days": 50,
    "zero_entry_days": 315,
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
  "parent_giveback_diagnostics": {
    "swing/reached_1R=True": {
      "count": 18,
      "pnl": 126.37547180076479,
      "losses": 6
    },
    "intraday/reached_1R=False": {
      "count": 12,
      "pnl": -154.59915935978088,
      "losses": 10
    },
    "swing/reached_1R=False": {
      "count": 25,
      "pnl": -261.13111302222416,
      "losses": 25
    },
    "intraday/reached_1R=True": {
      "count": 4,
      "pnl": 137.7585322918965,
      "losses": 1
    }
  },
  "stop_updates": [
    {
      "position_id": "intraday:1744772400000:19",
      "update": {
        "activation_r": 1.0,
        "active_from_ms": 1744822800000,
        "decision_timestamp_ms": 1744819200000,
        "from_stop": 83063.9,
        "initial_stop": 83063.9,
        "to_stop": 83945.16129999999,
        "trigger_close": 85000.1
      }
    },
    {
      "position_id": "intraday:1750118400000:27",
      "update": {
        "activation_r": 1.0,
        "active_from_ms": 1750176000000,
        "decision_timestamp_ms": 1750172400000,
        "from_stop": 108900.0,
        "initial_stop": 108900.0,
        "to_stop": 106643.3499,
        "trigger_close": 104199.2
      }
    },
    {
      "position_id": "intraday:1760623200000:49",
      "update": {
        "activation_r": 1.0,
        "active_from_ms": 1760630400000,
        "decision_timestamp_ms": 1760626800000,
        "from_stop": 111960.0,
        "initial_stop": 111960.0,
        "to_stop": 110683.9053,
        "trigger_close": 108474.0
      }
    },
    {
      "position_id": "intraday:1763622000000:57",
      "update": {
        "activation_r": 1.0,
        "active_from_ms": 1763654400000,
        "decision_timestamp_ms": 1763650800000,
        "from_stop": 93150.0,
        "initial_stop": 93150.0,
        "to_stop": 91846.2618,
        "trigger_close": 89835.4
      }
    }
  ],
  "common_protected_exits": [
    {
      "parent_position_id": "intraday:1744772400000:19",
      "child_position_id": "intraday:1744772400000:19",
      "parent_pnl": -1.3110101110033447,
      "child_pnl": -3.787982118505208,
      "parent_exit": "time_limit"
    }
  ],
  "protected_parent_winners": []
}
```
