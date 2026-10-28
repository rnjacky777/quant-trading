# 短線頻率目標與三小時確認實驗結果

2026-10-28。portfolio_confirmed_efficiency → portfolio_sweep_window。只改短線signal確認期限1根→最多3根1h；波段、出場及風控不變。全部父快照與指紋已在執行時逐一重播一致。

## 結論

未採用：增加交易卻令兩年一般及雙成本收益全部退步，回撤亦上升。保留父候選作研究參考，沒有宣稱父候選已可實盤獲利。兩年各10%／回撤10%仍未達成；不以加槓桿補足收益，不湊每日單量。

短線有機會時每日1–2次的偏好已加入AGENTS.md與合約研究頁，顯示全年筆數、全年日均、短線日均、有進場天數、無進場天數及短線／波段多空分組。全年日均除以365／366，不以活躍日平均冒充每天頻率。共享每日最多2次仍涵蓋波段。

## 全部期間與成本

每年重設10,000USDT；一般單邊費10bps／滑價5bps，雙成本20bps／10bps；含實際funding，全部實際1x。

|年|成本倍數|父收益|候選收益|父回撤|候選回撤|父短線筆數|候選短線筆數|候選總筆數|候選短線日均|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|2024|1|+3.054%|+0.939%|-2.970%|-4.501%|60|97|138|0.265|
|2024|2|-0.081%|-2.637%|-4.217%|-5.832%|59|96|138|0.262|
|2025|1|-3.003%|-3.935%|-4.292%|-4.969%|43|63|106|0.173|
|2025|2|-3.933%|-5.004%|-4.713%|-5.476%|43|63|106|0.173|

## 為什麼不採用與後續假說

原模式本身只出現82／98次合格掃單確認，波動門檻後63／44次；延長等待只提高到97／63筆實際短線，仍僅日均0.265／0.173，遠低於每天1次。新增訊號沒有帶來淨收益改善，不能透過持續放寬同一掃單形態來保證提高收益或頻率。新的訊號也會改變每日名額、風險與波段資金路徑，因此不能把全額變差只歸因手續費或新增交易。

[TradingView官方策略文件](https://www.tradingview.com/pine-script-docs/concepts/strategies/#simulating-trading-costs)說明必須模型化佣金及滑價，忽略成本可能高估績效；此處全部沿用父成本並保留雙成本失敗。該文件不證明任何進場模式能獲利。

下一個待驗證假說：若要接近每日機會，需要獨立、可重現的短線進場模型，而非只延長掃單。先用當時已完成的1h／4h資料建立趨勢回撤結束之機會事件與交易成本空間診斷，檢查同一事件重複與跨年穩定性；只有形成合理證據後，才單獨測試替換短線進場。尚未實作或宣稱此假說有優勢，不在本輪失敗後掃另一個等待根數。

200項pytest通過；新增期限、失效、首次跨越、過期拒絕、多空與原即時確認一致性，以及UTC日曆分母／進場日／分組統計。逐筆短線用截至進場前資料重算，核對現金、ID、每日上限、1x及每次新增的gross／stoprisk／margin預算。2024／2025為調參證據，非未見驗證；同一期間成本實驗非獨立樣本。

仍保留1h盤中路徑、固定MMR2%非歷史級距、精度／最小單量、深度滑價、虛擬獨立研究部位與真實交易所倉位映射等限制。沒有改live／paper／testnet或下單。全部曲線與交易保存在data/perpetual-sweep-frequency.json，儀表板標為未採用，父結果完整保留。

## 2024／成本1倍完整證據

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding：

```json
{
  "metrics": {
    "average_loss": -14.520428388881589,
    "average_win": 27.434143597542082,
    "cagr": 0.00937161452748736,
    "exposure": 0.3579965850882186,
    "fees": 223.05048695917853,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.04501470312325584,
    "maximum_margin_ratio": 0.023252979975666933,
    "net_funding": -39.39369138999995,
    "number_of_trades": 138,
    "profit_factor": 1.073493231194755,
    "sharpe_ratio": 0.2797613589522262,
    "slippage": 111.52536044933267,
    "sortino_ratio": 0.40147852388401356,
    "total_return": 0.009390948165551638,
    "win_rate": 0.36231884057971014
  },
  "frequency": {
    "total": 138,
    "calendar_days": 366,
    "daily_average": 0.3770491803278688,
    "active_days": 115,
    "zero_entry_days": 251,
    "intraday": 97,
    "intraday_daily_average": 0.2650273224043716,
    "intraday_active_days": 85,
    "groups": [
      {
        "sleeve": "intraday",
        "direction": 1,
        "count": 57,
        "daily_average": 0.1557377049180328
      },
      {
        "sleeve": "intraday",
        "direction": -1,
        "count": 40,
        "daily_average": 0.1092896174863388
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
  "grouped": {
    "intraday/1/stop_loss": {
      "count": 19,
      "pnl": -363.05584042555745
    },
    "swing/1/stop_loss": {
      "count": 11,
      "pnl": -195.2347350189774
    },
    "intraday/1/time_limit": {
      "count": 17,
      "pnl": 366.71790961407686
    },
    "intraday/-1/time_limit": {
      "count": 12,
      "pnl": 227.49438566944428
    },
    "intraday/-1/signal": {
      "count": 16,
      "pnl": -47.440499105219445
    },
    "swing/-1/stop_loss": {
      "count": 6,
      "pnl": -95.54673817227233
    },
    "swing/1/signal": {
      "count": 11,
      "pnl": -25.225890569286186
    },
    "swing/1/time_limit": {
      "count": 11,
      "pnl": 615.508691481685
    },
    "intraday/1/signal": {
      "count": 21,
      "pnl": -145.05491354026609
    },
    "intraday/-1/stop_loss": {
      "count": 11,
      "pnl": -240.8659905911045
    },
    "swing/-1/signal": {
      "count": 2,
      "pnl": -10.166169448264778
    },
    "intraday/-1/end_of_data": {
      "count": 1,
      "pnl": 6.779271761266441
    }
  }
}
```

## 2024／成本2倍完整證據

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding：

```json
{
  "metrics": {
    "average_loss": -14.03748017500494,
    "average_win": 22.341853772591953,
    "cagr": -0.026318966165868818,
    "exposure": 0.3579965850882186,
    "fees": 375.26628303197595,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.05832063747572136,
    "maximum_margin_ratio": 0.02327816296078866,
    "net_funding": -34.92129493225953,
    "number_of_trades": 138,
    "profit_factor": 0.7957928878280354,
    "sharpe_ratio": -0.8189622789972665,
    "slippage": 187.6334756141293,
    "sortino_ratio": -1.1494118986849058,
    "total_return": -0.026372290256121422,
    "win_rate": 0.3333333333333333
  },
  "frequency": {
    "total": 138,
    "calendar_days": 366,
    "daily_average": 0.3770491803278688,
    "active_days": 115,
    "zero_entry_days": 251,
    "intraday": 96,
    "intraday_daily_average": 0.26229508196721313,
    "intraday_active_days": 84,
    "groups": [
      {
        "sleeve": "intraday",
        "direction": 1,
        "count": 56,
        "daily_average": 0.15300546448087432
      },
      {
        "sleeve": "intraday",
        "direction": -1,
        "count": 40,
        "daily_average": 0.1092896174863388
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
  "grouped": {
    "intraday/1/stop_loss": {
      "count": 19,
      "pnl": -346.38389156254976
    },
    "swing/1/stop_loss": {
      "count": 12,
      "pnl": -199.2683636132968
    },
    "intraday/1/time_limit": {
      "count": 16,
      "pnl": 229.9285977636974
    },
    "intraday/-1/time_limit": {
      "count": 12,
      "pnl": 139.5415728305432
    },
    "intraday/-1/signal": {
      "count": 16,
      "pnl": -80.2153255912054
    },
    "swing/-1/stop_loss": {
      "count": 6,
      "pnl": -94.95956694659802
    },
    "swing/1/signal": {
      "count": 11,
      "pnl": -38.40360472173055
    },
    "swing/1/time_limit": {
      "count": 11,
      "pnl": 532.8845305270705
    },
    "intraday/1/signal": {
      "count": 21,
      "pnl": -162.00191264029024
    },
    "intraday/-1/stop_loss": {
      "count": 11,
      "pnl": -238.00010776946223
    },
    "swing/-1/signal": {
      "count": 2,
      "pnl": -10.913515296267175
    },
    "intraday/-1/end_of_data": {
      "count": 1,
      "pnl": 4.068684458864146
    }
  }
}
```

## 2025／成本1倍完整證據

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding：

```json
{
  "metrics": {
    "average_loss": -12.587127713694445,
    "average_win": 15.920087865226657,
    "cagr": -0.039376156499605575,
    "exposure": 0.2642392420956512,
    "fees": 165.0037004171724,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.04968718513024073,
    "maximum_margin_ratio": 0.0226569834142028,
    "net_funding": -4.915102902603064,
    "number_of_trades": 106,
    "profit_factor": 0.5717549080585111,
    "sharpe_ratio": -1.5851278538067735,
    "slippage": 82.50181493937563,
    "sortino_ratio": -2.166719192016257,
    "total_return": -0.03934974235472022,
    "win_rate": 0.3113207547169811
  },
  "frequency": {
    "total": 106,
    "calendar_days": 365,
    "daily_average": 0.29041095890410956,
    "active_days": 92,
    "zero_entry_days": 273,
    "intraday": 63,
    "intraday_daily_average": 0.1726027397260274,
    "intraday_active_days": 62,
    "groups": [
      {
        "sleeve": "intraday",
        "direction": 1,
        "count": 24,
        "daily_average": 0.06575342465753424
      },
      {
        "sleeve": "intraday",
        "direction": -1,
        "count": 39,
        "daily_average": 0.10684931506849316
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
        "count": 20,
        "daily_average": 0.0547945205479452
      }
    ]
  },
  "grouped": {
    "swing/1/stop_loss": {
      "count": 12,
      "pnl": -179.50465347922784
    },
    "intraday/1/stop_loss": {
      "count": 6,
      "pnl": -118.25113201072507
    },
    "intraday/1/signal": {
      "count": 13,
      "pnl": -84.62865969870461
    },
    "intraday/-1/signal": {
      "count": 17,
      "pnl": -71.18102871117812
    },
    "intraday/-1/stop_loss": {
      "count": 10,
      "pnl": -160.8493426239216
    },
    "swing/1/signal": {
      "count": 9,
      "pnl": 57.77595821596733
    },
    "intraday/1/time_limit": {
      "count": 5,
      "pnl": 41.6072036213063
    },
    "intraday/-1/time_limit": {
      "count": 12,
      "pnl": 169.34957122509118
    },
    "swing/-1/signal": {
      "count": 9,
      "pnl": 14.367969099498005
    },
    "swing/-1/stop_loss": {
      "count": 10,
      "pnl": -163.91149934915737
    },
    "swing/1/time_limit": {
      "count": 2,
      "pnl": 64.81086439905975
    },
    "swing/-1/time_limit": {
      "count": 1,
      "pnl": 36.91732576477721
    }
  }
}
```

## 2025／成本2倍完整證據

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding：

```json
{
  "metrics": {
    "average_loss": -11.425633115620974,
    "average_win": 14.896004287663754,
    "cagr": -0.050076693352317014,
    "exposure": 0.2642392420956512,
    "fees": 268.4964599274129,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.05475574487020207,
    "maximum_margin_ratio": 0.02268118178613781,
    "net_funding": -4.342242700090665,
    "number_of_trades": 106,
    "profit_factor": 0.4455805108188894,
    "sharpe_ratio": -2.338199103507197,
    "slippage": 134.24813661763764,
    "sortino_ratio": -3.1467417788805814,
    "total_return": -0.050043290036713706,
    "win_rate": 0.25471698113207547
  },
  "frequency": {
    "total": 106,
    "calendar_days": 365,
    "daily_average": 0.29041095890410956,
    "active_days": 92,
    "zero_entry_days": 273,
    "intraday": 63,
    "intraday_daily_average": 0.1726027397260274,
    "intraday_active_days": 62,
    "groups": [
      {
        "sleeve": "intraday",
        "direction": 1,
        "count": 24,
        "daily_average": 0.06575342465753424
      },
      {
        "sleeve": "intraday",
        "direction": -1,
        "count": 39,
        "daily_average": 0.10684931506849316
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
        "count": 20,
        "daily_average": 0.0547945205479452
      }
    ]
  },
  "grouped": {
    "swing/1/stop_loss": {
      "count": 12,
      "pnl": -176.83983733830436
    },
    "intraday/1/stop_loss": {
      "count": 6,
      "pnl": -118.81025210412434
    },
    "intraday/1/signal": {
      "count": 13,
      "pnl": -100.09260452383998
    },
    "intraday/-1/signal": {
      "count": 17,
      "pnl": -79.09824405640347
    },
    "intraday/-1/stop_loss": {
      "count": 10,
      "pnl": -149.9368536436172
    },
    "swing/1/signal": {
      "count": 9,
      "pnl": 43.04402658758163
    },
    "intraday/1/time_limit": {
      "count": 5,
      "pnl": 26.953676302399366
    },
    "intraday/-1/time_limit": {
      "count": 12,
      "pnl": 119.1196682994118
    },
    "swing/-1/signal": {
      "count": 9,
      "pnl": -0.3926206740393603
    },
    "swing/-1/stop_loss": {
      "count": 10,
      "pnl": -151.95150164982851
    },
    "swing/1/time_limit": {
      "count": 2,
      "pnl": 53.95712786127689
    },
    "swing/-1/time_limit": {
      "count": 1,
      "pnl": 33.614514572352086
    }
  }
}
```
