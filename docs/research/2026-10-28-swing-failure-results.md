# 波段突破失效退出：全年受控比較

父 portfolio_sweep_structure_confirm → 子 portfolio_swing_failure_exit。只新增每筆波段完成4h收盤跌回／升回原20根突破區間時的退出；下一1h開盤成交。事前設計見2026-10-28-swing-failure-design.md。

每年10,000 USDT重新開始，1x，正常費10bps／滑價5bps；雙成本20bps／10bps，另含實際funding與mark。四筆父完整快照與行情指紋重現後才測子候選。所有2024／2025皆為調參資料。

|年|成本倍數|父收益|子收益|父最大回撤|子最大回撤|總筆數|短線筆數|
|---|---:|---:|---:|---:|---:|---:|---:|
|2024|1|+3.920%|+4.149%|-2.323%|-2.192%|59|18|
|2024|2|+2.272%|+2.475%|-2.590%|-2.471%|60|18|
|2025|1|-1.109%|-0.572%|-2.961%|-2.517%|59|16|
|2025|2|-2.022%|-1.516%|-3.341%|-2.879%|59|16|

判斷：四組收益及回撤改善，保留研究候選。
2025仍虧，年淨10%目標未達，短線18／16筆的頻率不足也未解決。不能因退出組過去虧損，就直接將舊虧損相減宣稱可回收收益。
246項測試通過（含多空、等於／wick不觸發、未完成4h不觸發、每lot不同固定邊界及下一開盤成交）。另逐筆核對新退出及入場、cash/PnL、daily2、gross/stoprisk/margin。
歷史margin級距未驗證、MMR2%固定假設、1h OHLC路徑／滑價深度與最小量限制保留。虛擬多lot不是已驗證交易所hedge映射；無paper/testnet/live升級。
同時間入場的父子PnL仍受資金／連虧風控變動影響，不等於純單筆退出效果。完整風險調整、費用、曝險、平均盈虧等指標與提前截斷的原贏家如下。

## 2024／成本1倍

```json
{
  "year": 2024,
  "cost": 1,
  "checks": "passed",
  "metrics": {
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
  "parent_metrics": {
    "average_loss": -15.124561672368918,
    "average_win": 38.39119229146884,
    "cagr": 0.039121010594086236,
    "exposure": 0.24188958451906659,
    "fees": 87.49823439967211,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.023225887238582654,
    "maximum_margin_ratio": 0.023252979975666933,
    "net_funding": -37.83712280165091,
    "number_of_trades": 59,
    "profit_factor": 1.7405720291357756,
    "sharpe_ratio": 1.2807892177344706,
    "slippage": 43.74925747822347,
    "sortino_ratio": 1.890149592621491,
    "total_return": 0.039202895646233804,
    "win_rate": 0.4067796610169492
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
  "failure_exits": [
    {
      "position_id": "swing:1706443200000:3",
      "direction": 1,
      "boundary": 42239.3,
      "decision_hour_ms": 1706468400000,
      "execution_ms": 1706472000000,
      "pnl": -8.984627863946411
    },
    {
      "position_id": "swing:1706572800000:5",
      "direction": 1,
      "boundary": 42836.0,
      "decision_hour_ms": 1706698800000,
      "execution_ms": 1706702400000,
      "pnl": -8.65320819694146
    },
    {
      "position_id": "swing:1713830400000:15",
      "direction": 1,
      "boundary": 66449.0,
      "decision_hour_ms": 1713841200000,
      "execution_ms": 1713844800000,
      "pnl": -3.6967669135715844
    },
    {
      "position_id": "swing:1718121600000:23",
      "direction": -1,
      "boundary": 67300.0,
      "decision_hour_ms": 1718132400000,
      "execution_ms": 1718136000000,
      "pnl": -10.460491631084645
    },
    {
      "position_id": "swing:1720166400000:25",
      "direction": -1,
      "boundary": 56560.0,
      "decision_hour_ms": 1720191600000,
      "execution_ms": 1720195200000,
      "pnl": -9.39844696983729
    },
    {
      "position_id": "swing:1726776000000:38",
      "direction": 1,
      "boundary": 62697.0,
      "decision_hour_ms": 1727017200000,
      "execution_ms": 1727020800000,
      "pnl": -4.04018176055318
    },
    {
      "position_id": "swing:1730246400000:45",
      "direction": 1,
      "boundary": 72490.0,
      "decision_hour_ms": 1730257200000,
      "execution_ms": 1730260800000,
      "pnl": -8.294381920763383
    }
  ],
  "changed_same_entry_exits": [
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1706443200000,
      "parent_pnl": -6.890999033314486,
      "child_pnl": -8.984627863946411,
      "parent_exit": "signal",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1706760000000,
      "child_exit_ms": 1706472000000
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1706572800000,
      "parent_pnl": -12.21246260053213,
      "child_pnl": -8.65320819694146,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1706734800000,
      "child_exit_ms": 1706702400000
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1713830400000,
      "parent_pnl": -12.440019266257988,
      "child_pnl": -3.6967669135715844,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1713967200000,
      "child_exit_ms": 1713844800000
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1718121600000,
      "parent_pnl": -12.210825672730865,
      "child_pnl": -10.460491631084645,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1718182800000,
      "child_exit_ms": 1718136000000
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1720166400000,
      "parent_pnl": -12.522293180907726,
      "child_pnl": -9.39844696983729,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1720281600000,
      "child_exit_ms": 1720195200000
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1726776000000,
      "parent_pnl": 5.8083906966361765,
      "child_pnl": -4.04018176055318,
      "parent_exit": "time_limit",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1727380800000,
      "child_exit_ms": 1727020800000
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1730246400000,
      "parent_pnl": -25.67690009592008,
      "child_pnl": -8.294381920763383,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1730383200000,
      "child_exit_ms": 1730260800000
    }
  ],
  "grouped": {
    "swing/1/stop_loss": {
      "count": 8,
      "pnl": -147.58973086210952
    },
    "swing/-1/stop_loss": {
      "count": 4,
      "pnl": -60.13328871950146
    },
    "swing/1/breakout_failure": {
      "count": 5,
      "pnl": -33.66916665577602
    },
    "intraday/1/time_limit": {
      "count": 5,
      "pnl": 203.32683652740997
    },
    "swing/1/time_limit": {
      "count": 10,
      "pnl": 615.4339082438205
    },
    "swing/1/signal": {
      "count": 10,
      "pnl": -19.157479857507763
    },
    "intraday/-1/signal": {
      "count": 4,
      "pnl": -31.536195854204877
    },
    "swing/-1/signal": {
      "count": 2,
      "pnl": -10.361196634790062
    },
    "swing/-1/breakout_failure": {
      "count": 2,
      "pnl": -19.858938600921935
    },
    "intraday/1/signal": {
      "count": 3,
      "pnl": 48.33973791757918
    },
    "intraday/1/stop_loss": {
      "count": 4,
      "pnl": -86.433768452404
    },
    "intraday/-1/time_limit": {
      "count": 1,
      "pnl": -19.33539138150855
    },
    "intraday/-1/stop_loss": {
      "count": 1,
      "pnl": -24.159577074344593
    }
  },
  "earlier_exits_from_parent_winners": [
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1726776000000,
      "parent_pnl": 5.8083906966361765,
      "child_pnl": -4.04018176055318,
      "parent_exit": "time_limit",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1727380800000,
      "child_exit_ms": 1727020800000
    }
  ]
}
```

## 2024／成本2倍

```json
{
  "year": 2024,
  "cost": 2,
  "checks": "passed",
  "metrics": {
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
  "parent_metrics": {
    "average_loss": -15.10759120109563,
    "average_win": 32.12841338854751,
    "cagr": 0.02267378077424942,
    "exposure": 0.24188958451906659,
    "fees": 154.79594212441324,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.025898224476351928,
    "maximum_margin_ratio": 0.023278162960788665,
    "net_funding": -34.41840286186749,
    "number_of_trades": 60,
    "profit_factor": 1.4177602487336518,
    "sharpe_ratio": 0.8264858840463154,
    "slippage": 77.39846488365055,
    "sortino_ratio": 1.205602592374435,
    "total_return": 0.02272086380857119,
    "win_rate": 0.4
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
  "failure_exits": [
    {
      "position_id": "swing:1706443200000:3",
      "direction": 1,
      "boundary": 42239.3,
      "decision_hour_ms": 1706468400000,
      "execution_ms": 1706472000000,
      "pnl": -9.334738832505387
    },
    {
      "position_id": "swing:1706572800000:5",
      "direction": 1,
      "boundary": 42836.0,
      "decision_hour_ms": 1706698800000,
      "execution_ms": 1706702400000,
      "pnl": -9.030433510775039
    },
    {
      "position_id": "swing:1713830400000:15",
      "direction": 1,
      "boundary": 66449.0,
      "decision_hour_ms": 1713841200000,
      "execution_ms": 1713844800000,
      "pnl": -4.5162904919996265
    },
    {
      "position_id": "swing:1718121600000:23",
      "direction": -1,
      "boundary": 67300.0,
      "decision_hour_ms": 1718132400000,
      "execution_ms": 1718136000000,
      "pnl": -10.638506963528641
    },
    {
      "position_id": "swing:1720166400000:25",
      "direction": -1,
      "boundary": 56560.0,
      "decision_hour_ms": 1720191600000,
      "execution_ms": 1720195200000,
      "pnl": -9.491831275635828
    },
    {
      "position_id": "swing:1726776000000:39",
      "direction": 1,
      "boundary": 62697.0,
      "decision_hour_ms": 1727017200000,
      "execution_ms": 1727020800000,
      "pnl": -4.583281109513181
    },
    {
      "position_id": "swing:1730246400000:46",
      "direction": 1,
      "boundary": 72490.0,
      "decision_hour_ms": 1730257200000,
      "execution_ms": 1730260800000,
      "pnl": -9.754548984971754
    }
  ],
  "changed_same_entry_exits": [
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1706443200000,
      "parent_pnl": -7.454391071188714,
      "child_pnl": -9.334738832505387,
      "parent_exit": "signal",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1706760000000,
      "child_exit_ms": 1706472000000
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1706572800000,
      "parent_pnl": -12.224417075342076,
      "child_pnl": -9.030433510775039,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1706734800000,
      "child_exit_ms": 1706702400000
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1713830400000,
      "parent_pnl": -12.4054649344832,
      "child_pnl": -4.5162904919996265,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1713967200000,
      "child_exit_ms": 1713844800000
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1718121600000,
      "parent_pnl": -12.191398262005267,
      "child_pnl": -10.638506963528641,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1718182800000,
      "child_exit_ms": 1718136000000
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1720166400000,
      "parent_pnl": -12.448246490848398,
      "child_pnl": -9.491831275635828,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1720281600000,
      "child_exit_ms": 1720195200000
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1726776000000,
      "parent_pnl": 4.5069931514192545,
      "child_pnl": -4.583281109513181,
      "parent_exit": "time_limit",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1727380800000,
      "child_exit_ms": 1727020800000
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1730246400000,
      "parent_pnl": -25.365841916969508,
      "child_pnl": -9.754548984971754,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1730383200000,
      "child_exit_ms": 1730260800000
    }
  ],
  "grouped": {
    "swing/1/stop_loss": {
      "count": 9,
      "pnl": -153.454357380599
    },
    "swing/-1/stop_loss": {
      "count": 4,
      "pnl": -60.178931862556354
    },
    "swing/1/breakout_failure": {
      "count": 5,
      "pnl": -37.21929292976499
    },
    "intraday/1/time_limit": {
      "count": 5,
      "pnl": 153.1111868338525
    },
    "swing/1/time_limit": {
      "count": 10,
      "pnl": 540.0581516685183
    },
    "swing/1/signal": {
      "count": 10,
      "pnl": -33.055784633863226
    },
    "intraday/-1/signal": {
      "count": 4,
      "pnl": -35.334086116047175
    },
    "swing/-1/signal": {
      "count": 2,
      "pnl": -11.253139393841744
    },
    "swing/-1/breakout_failure": {
      "count": 2,
      "pnl": -20.13033823916447
    },
    "intraday/1/signal": {
      "count": 3,
      "pnl": 34.904500224065345
    },
    "intraday/1/stop_loss": {
      "count": 4,
      "pnl": -86.0212322990513
    },
    "intraday/-1/time_limit": {
      "count": 1,
      "pnl": -19.790708824966547
    },
    "intraday/-1/stop_loss": {
      "count": 1,
      "pnl": -24.129172516890804
    }
  },
  "earlier_exits_from_parent_winners": [
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1726776000000,
      "parent_pnl": 4.5069931514192545,
      "child_pnl": -4.583281109513181,
      "parent_exit": "time_limit",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1727380800000,
      "child_exit_ms": 1727020800000
    }
  ]
}
```

## 2025／成本1倍

```json
{
  "year": 2025,
  "cost": 1,
  "checks": "passed",
  "metrics": {
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
  "parent_metrics": {
    "average_loss": -13.529822326786658,
    "average_win": 20.839090595486876,
    "cagr": -0.011095678199957049,
    "exposure": 0.2107065403492752,
    "fees": 81.12953643246324,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.02961010260269914,
    "maximum_margin_ratio": 0.022656983414202803,
    "net_funding": -6.513029860603117,
    "number_of_trades": 59,
    "profit_factor": 0.7898635227997711,
    "sharpe_ratio": -0.4738658180890807,
    "slippage": 40.564772547746934,
    "sortino_ratio": -0.6731899343428122,
    "total_return": -0.011088125883494504,
    "win_rate": 0.3389830508474576
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
  "failure_exits": [
    {
      "position_id": "swing:1741651200000:8",
      "direction": -1,
      "boundary": 79142.8,
      "decision_hour_ms": 1741662000000,
      "execution_ms": 1741665600000,
      "pnl": -6.929166396449063
    },
    {
      "position_id": "swing:1742428800000:11",
      "direction": 1,
      "boundary": 85136.0,
      "decision_hour_ms": 1742482800000,
      "execution_ms": 1742486400000,
      "pnl": -10.71696640524471
    },
    {
      "position_id": "swing:1745611200000:22",
      "direction": 1,
      "boundary": 94904.3,
      "decision_hour_ms": 1745622000000,
      "execution_ms": 1745625600000,
      "pnl": -0.9153867727728475
    },
    {
      "position_id": "swing:1750622400000:28",
      "direction": -1,
      "boundary": 100789.9,
      "decision_hour_ms": 1750633200000,
      "execution_ms": 1750636800000,
      "pnl": -9.23009737794027
    },
    {
      "position_id": "swing:1754092800000:32",
      "direction": -1,
      "boundary": 113871.1,
      "decision_hour_ms": 1754118000000,
      "execution_ms": 1754121600000,
      "pnl": -3.732469972169586
    },
    {
      "position_id": "swing:1755129600000:34",
      "direction": 1,
      "boundary": 122450.0,
      "decision_hour_ms": 1755154800000,
      "execution_ms": 1755158400000,
      "pnl": -7.859581857654315
    },
    {
      "position_id": "swing:1755144000000:35",
      "direction": 1,
      "boundary": 122831.1,
      "decision_hour_ms": 1755154800000,
      "execution_ms": 1755158400000,
      "pnl": -8.540795024994331
    },
    {
      "position_id": "swing:1755648000000:38",
      "direction": -1,
      "boundary": 113506.0,
      "decision_hour_ms": 1755687600000,
      "execution_ms": 1755691200000,
      "pnl": -4.771377023485478
    },
    {
      "position_id": "swing:1756180800000:39",
      "direction": -1,
      "boundary": 110484.0,
      "decision_hour_ms": 1756234800000,
      "execution_ms": 1756238400000,
      "pnl": -5.526440930355314
    },
    {
      "position_id": "swing:1760659200000:51",
      "direction": -1,
      "boundary": 108250.0,
      "decision_hour_ms": 1760670000000,
      "execution_ms": 1760673600000,
      "pnl": -4.240689523433918
    },
    {
      "position_id": "swing:1761537600000:53",
      "direction": 1,
      "boundary": 114000.0,
      "decision_hour_ms": 1761620400000,
      "execution_ms": 1761624000000,
      "pnl": -16.1425378861106
    },
    {
      "position_id": "swing:1762286400000:55",
      "direction": -1,
      "boundary": 103550.0,
      "decision_hour_ms": 1762354800000,
      "execution_ms": 1762358400000,
      "pnl": -10.267148268730935
    },
    {
      "position_id": "swing:1765828800000:59",
      "direction": -1,
      "boundary": 87504.3,
      "decision_hour_ms": 1765897200000,
      "execution_ms": 1765900800000,
      "pnl": -20.49599518471932
    }
  ],
  "changed_same_entry_exits": [
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1741651200000,
      "parent_pnl": -24.33052634478877,
      "child_pnl": -6.929166396449063,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1741716000000,
      "child_exit_ms": 1741665600000
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1745611200000,
      "parent_pnl": -2.773338327010736,
      "child_pnl": -0.9153867727728475,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1745802000000,
      "child_exit_ms": 1745625600000
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1750622400000,
      "parent_pnl": -11.985645983265774,
      "child_pnl": -9.23009737794027,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1750654800000,
      "child_exit_ms": 1750636800000
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1754092800000,
      "parent_pnl": -4.884029244357064,
      "child_pnl": -3.732469972169586,
      "parent_exit": "signal",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1754251200000,
      "child_exit_ms": 1754121600000
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1755129600000,
      "parent_pnl": -11.9216251748912,
      "child_pnl": -7.859581857654315,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1755169200000,
      "child_exit_ms": 1755158400000
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1755144000000,
      "parent_pnl": -11.849244578427117,
      "child_pnl": -8.540795024994331,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1755165600000,
      "child_exit_ms": 1755158400000
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1755648000000,
      "parent_pnl": -11.61519023702701,
      "child_pnl": -4.771377023485478,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1755871200000,
      "child_exit_ms": 1755691200000
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1756180800000,
      "parent_pnl": -11.734238242482224,
      "child_pnl": -5.526440930355314,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1756353600000,
      "child_exit_ms": 1756238400000
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1760659200000,
      "parent_pnl": 0.185552847302953,
      "child_pnl": -4.240689523433918,
      "parent_exit": "signal",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1760875200000,
      "child_exit_ms": 1760673600000
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1761537600000,
      "parent_pnl": -23.810443085129997,
      "child_pnl": -16.1425378861106,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1761681600000,
      "child_exit_ms": 1761624000000
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1762286400000,
      "parent_pnl": -11.912613577275232,
      "child_pnl": -10.267148268730935,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1762365600000,
      "child_exit_ms": 1762358400000
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1765828800000,
      "parent_pnl": -23.701094114613635,
      "child_pnl": -20.49599518471932,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1765980000000,
      "child_exit_ms": 1765900800000
    }
  ],
  "grouped": {
    "swing/1/stop_loss": {
      "count": 7,
      "pnl": -119.57012350786066
    },
    "intraday/1/stop_loss": {
      "count": 1,
      "pnl": -24.106420492644705
    },
    "swing/1/signal": {
      "count": 10,
      "pnl": 66.09685538041626
    },
    "swing/-1/signal": {
      "count": 6,
      "pnl": 27.66666296611227
    },
    "swing/-1/stop_loss": {
      "count": 4,
      "pnl": -59.43109906701685
    },
    "swing/-1/breakout_failure": {
      "count": 8,
      "pnl": -65.19338467728389
    },
    "intraday/-1/stop_loss": {
      "count": 5,
      "pnl": -81.16736623643081
    },
    "swing/1/breakout_failure": {
      "count": 5,
      "pnl": -44.1752679467768
    },
    "intraday/1/signal": {
      "count": 2,
      "pnl": -24.263512603303013
    },
    "intraday/-1/time_limit": {
      "count": 6,
      "pnl": 156.06418691299586
    },
    "intraday/1/time_limit": {
      "count": 2,
      "pnl": 7.508600058975242
    },
    "swing/1/time_limit": {
      "count": 2,
      "pnl": 65.7162304155348
    },
    "swing/-1/time_limit": {
      "count": 1,
      "pnl": 37.64719579198225
    }
  },
  "earlier_exits_from_parent_winners": [
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1760659200000,
      "parent_pnl": 0.185552847302953,
      "child_pnl": -4.240689523433918,
      "parent_exit": "signal",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1760875200000,
      "child_exit_ms": 1760673600000
    }
  ]
}
```

## 2025／成本2倍

```json
{
  "year": 2025,
  "cost": 2,
  "checks": "passed",
  "metrics": {
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
  "parent_metrics": {
    "average_loss": -12.627151158373229,
    "average_win": 19.300707140699014,
    "cagr": -0.02023654287576493,
    "exposure": 0.2107065403492752,
    "fees": 136.2092530349811,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.03340705496733254,
    "maximum_margin_ratio": 0.022681181786137806,
    "net_funding": -5.191759338887436,
    "number_of_trades": 59,
    "profit_factor": 0.6186819883232856,
    "sharpe_ratio": -1.0131875995344564,
    "slippage": 68.10463379480544,
    "sortino_ratio": -1.416402688144172,
    "total_return": -0.020222832725979467,
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
  "failure_exits": [
    {
      "position_id": "swing:1741651200000:8",
      "direction": -1,
      "boundary": 79142.8,
      "decision_hour_ms": 1741662000000,
      "execution_ms": 1741665600000,
      "pnl": -7.883343893642267
    },
    {
      "position_id": "swing:1742428800000:11",
      "direction": 1,
      "boundary": 85136.0,
      "decision_hour_ms": 1742482800000,
      "execution_ms": 1742486400000,
      "pnl": -10.846041141092641
    },
    {
      "position_id": "swing:1745611200000:22",
      "direction": 1,
      "boundary": 94904.3,
      "decision_hour_ms": 1745622000000,
      "execution_ms": 1745625600000,
      "pnl": -4.6701152822387275
    },
    {
      "position_id": "swing:1750622400000:28",
      "direction": -1,
      "boundary": 100789.9,
      "decision_hour_ms": 1750633200000,
      "execution_ms": 1750636800000,
      "pnl": -9.455021034702499
    },
    {
      "position_id": "swing:1754092800000:32",
      "direction": -1,
      "boundary": 113871.1,
      "decision_hour_ms": 1754118000000,
      "execution_ms": 1754121600000,
      "pnl": -4.504573447556765
    },
    {
      "position_id": "swing:1755129600000:34",
      "direction": 1,
      "boundary": 122450.0,
      "decision_hour_ms": 1755154800000,
      "execution_ms": 1755158400000,
      "pnl": -8.29977431884552
    },
    {
      "position_id": "swing:1755144000000:35",
      "direction": 1,
      "boundary": 122831.1,
      "decision_hour_ms": 1755154800000,
      "execution_ms": 1755158400000,
      "pnl": -8.922226141369265
    },
    {
      "position_id": "swing:1755648000000:38",
      "direction": -1,
      "boundary": 113506.0,
      "decision_hour_ms": 1755687600000,
      "execution_ms": 1755691200000,
      "pnl": -5.518326218513228
    },
    {
      "position_id": "swing:1756180800000:39",
      "direction": -1,
      "boundary": 110484.0,
      "decision_hour_ms": 1756234800000,
      "execution_ms": 1756238400000,
      "pnl": -6.085678845936617
    },
    {
      "position_id": "swing:1760659200000:51",
      "direction": -1,
      "boundary": 108250.0,
      "decision_hour_ms": 1760670000000,
      "execution_ms": 1760673600000,
      "pnl": -4.832605092247936
    },
    {
      "position_id": "swing:1761537600000:53",
      "direction": 1,
      "boundary": 114000.0,
      "decision_hour_ms": 1761620400000,
      "execution_ms": 1761624000000,
      "pnl": -8.575055972116875
    },
    {
      "position_id": "swing:1762286400000:55",
      "direction": -1,
      "boundary": 103550.0,
      "decision_hour_ms": 1762354800000,
      "execution_ms": 1762358400000,
      "pnl": -10.329380972507863
    },
    {
      "position_id": "swing:1765828800000:59",
      "direction": -1,
      "boundary": 87504.3,
      "decision_hour_ms": 1765897200000,
      "execution_ms": 1765900800000,
      "pnl": -20.706768950281894
    }
  ],
  "changed_same_entry_exits": [
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1741651200000,
      "parent_pnl": -24.33634556955381,
      "child_pnl": -7.883343893642267,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1741716000000,
      "child_exit_ms": 1741665600000
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1745611200000,
      "parent_pnl": -11.90108273418141,
      "child_pnl": -4.6701152822387275,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1745802000000,
      "child_exit_ms": 1745625600000
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1750622400000,
      "parent_pnl": -11.957899900094109,
      "child_pnl": -9.455021034702499,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1750654800000,
      "child_exit_ms": 1750636800000
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1754092800000,
      "parent_pnl": -5.540316982560627,
      "child_pnl": -4.504573447556765,
      "parent_exit": "signal",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1754251200000,
      "child_exit_ms": 1754121600000
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1755129600000,
      "parent_pnl": -11.898837800279457,
      "child_pnl": -8.29977431884552,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1755169200000,
      "child_exit_ms": 1755158400000
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1755144000000,
      "parent_pnl": -11.835928486362905,
      "child_pnl": -8.922226141369265,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1755165600000,
      "child_exit_ms": 1755158400000
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1755648000000,
      "parent_pnl": -11.619797577882004,
      "child_pnl": -5.518326218513228,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1755871200000,
      "child_exit_ms": 1755691200000
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1756180800000,
      "parent_pnl": -11.715589471973859,
      "child_pnl": -6.085678845936617,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1756353600000,
      "child_exit_ms": 1756238400000
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1760659200000,
      "parent_pnl": -0.7774265499893455,
      "child_pnl": -4.832605092247936,
      "parent_exit": "signal",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1760875200000,
      "child_exit_ms": 1760673600000
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1761537600000,
      "parent_pnl": -11.847224507602919,
      "child_pnl": -8.575055972116875,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1761681600000,
      "child_exit_ms": 1761624000000
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1762286400000,
      "parent_pnl": -11.850914732289056,
      "child_pnl": -10.329380972507863,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1762365600000,
      "child_exit_ms": 1762358400000
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1765828800000,
      "parent_pnl": -23.582966236255047,
      "child_pnl": -20.706768950281894,
      "parent_exit": "stop_loss",
      "child_exit": "breakout_failure",
      "parent_exit_ms": 1765980000000,
      "child_exit_ms": 1765900800000
    }
  ],
  "grouped": {
    "swing/1/stop_loss": {
      "count": 7,
      "pnl": -119.9136268137214
    },
    "intraday/1/stop_loss": {
      "count": 1,
      "pnl": -24.1807394194044
    },
    "swing/1/signal": {
      "count": 10,
      "pnl": 48.14044773402374
    },
    "swing/-1/signal": {
      "count": 6,
      "pnl": 17.937685644192413
    },
    "swing/-1/stop_loss": {
      "count": 4,
      "pnl": -59.533591062412576
    },
    "swing/-1/breakout_failure": {
      "count": 8,
      "pnl": -69.31569845538907
    },
    "intraday/-1/stop_loss": {
      "count": 5,
      "pnl": -81.8345077878363
    },
    "swing/1/breakout_failure": {
      "count": 5,
      "pnl": -41.313212855663025
    },
    "intraday/1/signal": {
      "count": 2,
      "pnl": -26.049078490851414
    },
    "intraday/-1/time_limit": {
      "count": 6,
      "pnl": 115.17127002409437
    },
    "intraday/1/time_limit": {
      "count": 2,
      "pnl": 0.052428606113379184
    },
    "swing/1/time_limit": {
      "count": 2,
      "pnl": 54.8574474453529
    },
    "swing/-1/time_limit": {
      "count": 1,
      "pnl": 34.384907142157736
    }
  },
  "earlier_exits_from_parent_winners": []
}
```
