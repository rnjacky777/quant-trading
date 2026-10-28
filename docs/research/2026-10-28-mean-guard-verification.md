# 進場延伸診斷與短線空單位置限制：實際回測

2026-10-28。固定原候選portfolio_confirmed_efficiency，先完成全訊號延伸／gap分組，再事前記錄單項signal候選portfolio_sweep_mean_guard。不是重新調整已失敗的SMA回撤模型。

## 診斷結果

2025各策略方向的開盤gap絕對中位數約0.009bps，最大約0.235bps，遠低於既定單邊5bps滑價。不是以此否定真實滑價／深度，而是目前bar-close到next-open的價格差沒有足夠經濟幅度支持先改gap限制。

波段2024多單45次全在>2個4h ATR仍有正24h事件均值，不能將2ATR上限套用全部策略。2025低延伸波多僅2筆，樣本不足。短線空單位於4h SMA20上方時，12／24h分組均值兩年較佳，但4h不一致且2025保留組24h仍負。因此只支持一次探索，不是已找到正期望或統計顯著優勢。所有窗口與正常／雙成本資料在data/entry-extension-diagnostics.json及entry-extension-results.md。

## 唯一候選與全期間結果

短線原掃單空單只在完成close≥當時完成4h SMA20時准入；多單、波段、止損、退出、費用、槓桿、共享風控全部不變。父四筆完整快照及指紋逐一重播一致才執行候選。每年10,000USDT，一般單邊費10bps／滑價5bps，雙成本20bps／10bps，含實際funding，全部實際1x。

|年|成本倍數|父收益|候選收益|父回撤|候選回撤|總交易數|短線筆數|
|---|---:|---:|---:|---:|---:|---:|---:|
|2024|1|+3.054%|+2.905%|-2.970%|-2.970%|97|56|
|2024|2|-0.081%|-0.092%|-4.217%|-4.186%|97|55|
|2025|1|-3.003%|-3.399%|-4.292%|-3.753%|69|26|
|2025|2|-3.933%|-3.888%|-4.713%|-4.175%|69|26|

## 是否提升收益

沒有穩定提升：2024一般成本+3.054%→+2.905%、雙成本−0.081%→−0.092%；2025一般成本−3.003%→−3.399%，只有雙成本−3.933%→−3.888%微升。候選未採用，原候選仍保留研究參考；10%年目標未達，不升槓桿。

為何分組看似較好，實際卻退步：固定24h均值沒有原止損及動態退出。2024被排除4筆父短空有2贏、合計原本+14.79USDT；2025排除17筆有5贏、合計−15.06，並非可直接視為大額虧損機會。原止損會截斷後續價格路徑，事件24h負不等於實際交易負。刪除事件也改變短線多空共用的連虧減倉、波段名額與風險路徑，不能拿凍結父交易直接相減當候選收益。

2025一般成本實際總費用下降，成交價差損益（仍含滑價、未扣費／funding）卻由約−166.73變成−230.93USDT，顯示不是只要省費就能提高淨收益。頻率亦下降，不能聲稱此候選滿足每日1–2次偏好。

## 保存及決策

228項pytest通過；新增完成4h均線／ATR不讀未完成bar、自然分組邊界、短空均線相等准入、多單／退出不變。四筆父完整快照重播、候選所有短線進場從相同暖機重算方向／時間／止損，並核對cash/PnL、ID、每日≤2、1x與新增gross／stoprisk／margin。結果data/perpetual-sweep-mean-guard.json，審計data/sweep-mean-guard-audit.json，已列第11項研究經驗。

本輪停止，不繼續掃1ATR、2ATR或小數距離直到數字變好。後續應把候選入場事件的原止損／動態退出路徑一併納入評估，再形成新的假說；先明確哪些訊號真的產生負期望，不只依固定時間均值分組。這不是新交易規則，也不保證可解決損失。

2024／2025及分組已調參，非未見驗證；成本重複／重疊訊號非獨立樣本。仍有固定BTC選樣、1h盤中路徑、固定MMR2%非歷史級距、精度／最小量、深度滑價與虛擬多筆部位到交易所模式的限制。未改live/paper/testnet、未下單。

## 2024／成本1倍完整指標與排除代價

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding、頻率與逐筆排除對照：

```json
{
  "year": 2024,
  "cost": 1,
  "checks": "passed",
  "metrics": {
    "average_loss": -15.11798630469046,
    "average_win": 32.36786600285351,
    "cagr": 0.028992796348491057,
    "exposure": 0.2965281730221969,
    "fees": 160.3640156061764,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.029697281998492864,
    "maximum_margin_ratio": 0.023252979975666936,
    "net_funding": -41.52080882338084,
    "number_of_trades": 97,
    "profit_factor": 1.320293829668321,
    "sharpe_ratio": 0.8807300366679482,
    "slippage": 80.18215095278873,
    "sortino_ratio": 1.2853006214627052,
    "total_return": 0.029053186382411278,
    "win_rate": 0.38144329896907214
  },
  "frequency": {
    "total": 97,
    "calendar_days": 366,
    "daily_average": 0.2650273224043716,
    "active_days": 82,
    "zero_entry_days": 284,
    "intraday": 56,
    "intraday_daily_average": 0.15300546448087432,
    "intraday_active_days": 51,
    "groups": [
      {
        "sleeve": "intraday",
        "direction": 1,
        "count": 40,
        "daily_average": 0.1092896174863388
      },
      {
        "sleeve": "intraday",
        "direction": -1,
        "count": 16,
        "daily_average": 0.04371584699453552
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
    "swing/1/stop_loss": {
      "count": 11,
      "pnl": -197.1217063475018
    },
    "swing/-1/stop_loss": {
      "count": 6,
      "pnl": -96.91295122496817
    },
    "intraday/1/time_limit": {
      "count": 12,
      "pnl": 309.23832538837917
    },
    "swing/1/signal": {
      "count": 11,
      "pnl": -25.65674884761712
    },
    "swing/1/time_limit": {
      "count": 11,
      "pnl": 621.1368377907944
    },
    "intraday/1/stop_loss": {
      "count": 11,
      "pnl": -245.32475458693554
    },
    "intraday/1/signal": {
      "count": 17,
      "pnl": -110.72291509452572
    },
    "intraday/-1/signal": {
      "count": 8,
      "pnl": -54.90863223874724
    },
    "intraday/-1/time_limit": {
      "count": 5,
      "pnl": 173.9827297227457
    },
    "swing/-1/signal": {
      "count": 2,
      "pnl": -10.310380253585478
    },
    "intraday/-1/stop_loss": {
      "count": 3,
      "pnl": -72.86794048388597
    }
  },
  "intraday_entries_recomputed": 56,
  "parent_fill_price_pnl_before_fees_funding": 514.7905830943008,
  "child_fill_price_pnl_before_fees_funding": 492.4166882537094,
  "excluded_parent_short_events": {
    "count": 4,
    "winners": 2,
    "net_pnl": 14.790468906830228,
    "events": [
      {
        "position_id": "intraday:1706061600000:3",
        "pnl": -18.0849812047878,
        "exit_reason": "signal"
      },
      {
        "position_id": "intraday:1724950800000:65",
        "pnl": 38.161643027125486,
        "exit_reason": "time_limit"
      },
      {
        "position_id": "intraday:1725634800000:67",
        "pnl": 6.984269853242906,
        "exit_reason": "signal"
      },
      {
        "position_id": "intraday:1735596000000:101",
        "pnl": -12.270462768750365,
        "exit_reason": "stop_loss"
      }
    ]
  }
}
```

## 2024／成本2倍完整指標與排除代價

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding、頻率與逐筆排除對照：

```json
{
  "year": 2024,
  "cost": 2,
  "checks": "passed",
  "metrics": {
    "average_loss": -14.279703005938646,
    "average_win": 27.41448180811211,
    "cagr": -0.0009204201632779796,
    "exposure": 0.2965281730221969,
    "fees": 266.9598993532907,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.04186238400916387,
    "maximum_margin_ratio": 0.02327816296078867,
    "net_funding": -36.824845793784554,
    "number_of_trades": 97,
    "profit_factor": 0.9899079957355621,
    "sharpe_ratio": -0.016338735559692424,
    "slippage": 133.48037771866908,
    "sortino_ratio": -0.02335881407042218,
    "total_return": -0.0009223092712385972,
    "win_rate": 0.3402061855670103
  },
  "frequency": {
    "total": 97,
    "calendar_days": 366,
    "daily_average": 0.2650273224043716,
    "active_days": 82,
    "zero_entry_days": 284,
    "intraday": 55,
    "intraday_daily_average": 0.15027322404371585,
    "intraday_active_days": 50,
    "groups": [
      {
        "sleeve": "intraday",
        "direction": 1,
        "count": 39,
        "daily_average": 0.10655737704918032
      },
      {
        "sleeve": "intraday",
        "direction": -1,
        "count": 16,
        "daily_average": 0.04371584699453552
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
    "swing/1/stop_loss": {
      "count": 12,
      "pnl": -201.67201347003362
    },
    "swing/-1/stop_loss": {
      "count": 6,
      "pnl": -96.48528971061147
    },
    "intraday/1/time_limit": {
      "count": 11,
      "pnl": 184.9024853069372
    },
    "swing/1/signal": {
      "count": 11,
      "pnl": -39.30985351902957
    },
    "swing/1/time_limit": {
      "count": 11,
      "pnl": 539.1266158791818
    },
    "intraday/1/stop_loss": {
      "count": 11,
      "pnl": -230.3537009704832
    },
    "intraday/1/signal": {
      "count": 17,
      "pnl": -122.79530363392443
    },
    "intraday/-1/signal": {
      "count": 8,
      "pnl": -66.62798454361881
    },
    "intraday/-1/time_limit": {
      "count": 5,
      "pnl": 106.80910852706604
    },
    "swing/-1/signal": {
      "count": 2,
      "pnl": -11.102322556938798
    },
    "intraday/-1/stop_loss": {
      "count": 3,
      "pnl": -71.71483402091873
    }
  },
  "intraday_entries_recomputed": 55,
  "parent_fill_price_pnl_before_fees_funding": 308.8883358086527,
  "child_fill_price_pnl_before_fees_funding": 294.56165243470156,
  "excluded_parent_short_events": {
    "count": 4,
    "winners": 2,
    "net_pnl": 1.0571286382241722,
    "events": [
      {
        "position_id": "intraday:1706061600000:3",
        "pnl": -18.836424942363756,
        "exit_reason": "signal"
      },
      {
        "position_id": "intraday:1724950800000:65",
        "pnl": 28.234441629202962,
        "exit_reason": "time_limit"
      },
      {
        "position_id": "intraday:1725634800000:67",
        "pnl": 3.623034273587297,
        "exit_reason": "signal"
      },
      {
        "position_id": "intraday:1735596000000:101",
        "pnl": -11.96392232220233,
        "exit_reason": "stop_loss"
      }
    ]
  }
}
```

## 2025／成本1倍完整指標與排除代價

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding、頻率與逐筆排除對照：

```json
{
  "year": 2025,
  "cost": 1,
  "checks": "passed",
  "metrics": {
    "average_loss": -13.578791795805719,
    "average_win": 13.557416933729492,
    "cagr": -0.03401688716656759,
    "exposure": 0.22942586462732564,
    "fees": 102.27117340813346,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.037529491868951825,
    "maximum_margin_ratio": 0.0226569834142028,
    "net_funding": -6.736368408507614,
    "number_of_trades": 69,
    "profit_factor": 0.46734827686682384,
    "sharpe_ratio": -1.6161233209665964,
    "slippage": 51.13554175482103,
    "sortino_ratio": -2.166395353526999,
    "total_return": -0.033994004186080895,
    "win_rate": 0.3188405797101449
  },
  "frequency": {
    "total": 69,
    "calendar_days": 365,
    "daily_average": 0.18904109589041096,
    "active_days": 61,
    "zero_entry_days": 304,
    "intraday": 26,
    "intraday_daily_average": 0.07123287671232877,
    "intraday_active_days": 26,
    "groups": [
      {
        "sleeve": "intraday",
        "direction": 1,
        "count": 15,
        "daily_average": 0.0410958904109589
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
        "count": 20,
        "daily_average": 0.0547945205479452
      }
    ]
  },
  "grouped": {
    "swing/1/stop_loss": {
      "count": 12,
      "pnl": -180.8256118648398
    },
    "intraday/1/stop_loss": {
      "count": 4,
      "pnl": -94.18178567830128
    },
    "swing/1/signal": {
      "count": 9,
      "pnl": 58.67835314125113
    },
    "intraday/1/time_limit": {
      "count": 4,
      "pnl": 3.3731163870849326
    },
    "intraday/1/signal": {
      "count": 7,
      "pnl": -60.16352719561312
    },
    "intraday/-1/time_limit": {
      "count": 3,
      "pnl": 47.470793928283065
    },
    "swing/-1/signal": {
      "count": 9,
      "pnl": 14.206323589931955
    },
    "swing/-1/stop_loss": {
      "count": 10,
      "pnl": -165.26156566647535
    },
    "intraday/-1/signal": {
      "count": 7,
      "pnl": -54.14661799961087
    },
    "intraday/-1/stop_loss": {
      "count": 1,
      "pnl": -11.597298002704292
    },
    "swing/1/time_limit": {
      "count": 2,
      "pnl": 65.3980471417016
    },
    "swing/-1/time_limit": {
      "count": 1,
      "pnl": 37.10973035847209
    }
  },
  "intraday_entries_recomputed": 26,
  "parent_fill_price_pnl_before_fees_funding": -166.7347921130804,
  "child_fill_price_pnl_before_fees_funding": -230.93250004417882,
  "excluded_parent_short_events": {
    "count": 17,
    "winners": 5,
    "net_pnl": -15.056448893090113,
    "events": [
      {
        "position_id": "intraday:1736733600000:4",
        "pnl": 2.8498256363444074,
        "exit_reason": "signal"
      },
      {
        "position_id": "intraday:1738029600000:9",
        "pnl": -15.03432601888439,
        "exit_reason": "signal"
      },
      {
        "position_id": "intraday:1741698000000:16",
        "pnl": -23.800203576812645,
        "exit_reason": "stop_loss"
      },
      {
        "position_id": "intraday:1741748400000:17",
        "pnl": -17.601943288368723,
        "exit_reason": "signal"
      },
      {
        "position_id": "intraday:1743764400000:26",
        "pnl": -11.559462905525685,
        "exit_reason": "stop_loss"
      },
      {
        "position_id": "intraday:1750694400000:40",
        "pnl": -22.863813718188783,
        "exit_reason": "stop_loss"
      },
      {
        "position_id": "intraday:1755716400000:52",
        "pnl": -18.275567350565456,
        "exit_reason": "signal"
      },
      {
        "position_id": "intraday:1756256400000:54",
        "pnl": -3.8030996259534358,
        "exit_reason": "time_limit"
      },
      {
        "position_id": "intraday:1756724400000:55",
        "pnl": -11.226019702564406,
        "exit_reason": "stop_loss"
      },
      {
        "position_id": "intraday:1758916800000:58",
        "pnl": -3.90737682591595,
        "exit_reason": "time_limit"
      },
      {
        "position_id": "intraday:1760277600000:64",
        "pnl": -11.425388511782455,
        "exit_reason": "stop_loss"
      },
      {
        "position_id": "intraday:1760500800000:66",
        "pnl": 1.8385182944534346,
        "exit_reason": "time_limit"
      },
      {
        "position_id": "intraday:1760623200000:67",
        "pnl": 52.556799482200475,
        "exit_reason": "time_limit"
      },
      {
        "position_id": "intraday:1761930000000:73",
        "pnl": -20.356211084685157,
        "exit_reason": "time_limit"
      },
      {
        "position_id": "intraday:1762376400000:75",
        "pnl": 30.737299576302018,
        "exit_reason": "time_limit"
      },
      {
        "position_id": "intraday:1763622000000:78",
        "pnl": 68.3245478886194,
        "exit_reason": "time_limit"
      },
      {
        "position_id": "intraday:1765893600000:85",
        "pnl": -11.51002716176277,
        "exit_reason": "stop_loss"
      }
    ]
  }
}
```

## 2025／成本2倍完整指標與排除代價

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding、頻率與逐筆排除對照：

```json
{
  "year": 2025,
  "cost": 2,
  "checks": "passed",
  "metrics": {
    "average_loss": -11.978847051074622,
    "average_win": 13.770774978209413,
    "cagr": -0.03890579224666835,
    "exposure": 0.22942586462732564,
    "fees": 168.00163580142683,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.041752683618308306,
    "maximum_margin_ratio": 0.022681181786137806,
    "net_funding": -5.572621331769406,
    "number_of_trades": 69,
    "profit_factor": 0.37582783287041516,
    "sharpe_ratio": -2.142270667414847,
    "slippage": 84.00068667878033,
    "sortino_ratio": -2.834734026652279,
    "total_return": -0.03887968720263291,
    "win_rate": 0.2463768115942029
  },
  "frequency": {
    "total": 69,
    "calendar_days": 365,
    "daily_average": 0.18904109589041096,
    "active_days": 61,
    "zero_entry_days": 304,
    "intraday": 26,
    "intraday_daily_average": 0.07123287671232877,
    "intraday_active_days": 26,
    "groups": [
      {
        "sleeve": "intraday",
        "direction": 1,
        "count": 15,
        "daily_average": 0.0410958904109589
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
        "count": 20,
        "daily_average": 0.0547945205479452
      }
    ]
  },
  "grouped": {
    "swing/1/stop_loss": {
      "count": 12,
      "pnl": -178.431202139104
    },
    "intraday/1/stop_loss": {
      "count": 4,
      "pnl": -94.83467722857685
    },
    "swing/1/signal": {
      "count": 9,
      "pnl": 43.75344519542433
    },
    "intraday/1/time_limit": {
      "count": 4,
      "pnl": -4.653225582773093
    },
    "intraday/1/signal": {
      "count": 7,
      "pnl": -70.46709996697908
    },
    "intraday/-1/time_limit": {
      "count": 3,
      "pnl": 33.616704025399386
    },
    "swing/-1/signal": {
      "count": 9,
      "pnl": -0.7174407294041556
    },
    "swing/-1/stop_loss": {
      "count": 10,
      "pnl": -153.63625219919584
    },
    "intraday/-1/signal": {
      "count": 7,
      "pnl": -40.271828287503595
    },
    "intraday/-1/stop_loss": {
      "count": 1,
      "pnl": -11.663438473062426
    },
    "swing/1/time_limit": {
      "count": 2,
      "pnl": 54.550132060240955
    },
    "swing/-1/time_limit": {
      "count": 1,
      "pnl": 33.95801129921397
    }
  },
  "intraday_entries_recomputed": 26,
  "parent_fill_price_pnl_before_fees_funding": -177.23109385101657,
  "child_fill_price_pnl_before_fees_funding": -215.22261489312413,
  "excluded_parent_short_events": {
    "count": 17,
    "winners": 5,
    "net_pnl": -41.94994618685603,
    "events": [
      {
        "position_id": "intraday:1736733600000:4",
        "pnl": 0.5286237148823504,
        "exit_reason": "signal"
      },
      {
        "position_id": "intraday:1738029600000:9",
        "pnl": -15.901610704474923,
        "exit_reason": "signal"
      },
      {
        "position_id": "intraday:1741698000000:16",
        "pnl": -23.84331824052053,
        "exit_reason": "stop_loss"
      },
      {
        "position_id": "intraday:1741748400000:17",
        "pnl": -18.173326609819306,
        "exit_reason": "signal"
      },
      {
        "position_id": "intraday:1743764400000:26",
        "pnl": -11.617203180112062,
        "exit_reason": "stop_loss"
      },
      {
        "position_id": "intraday:1750694400000:40",
        "pnl": -23.00383710023813,
        "exit_reason": "stop_loss"
      },
      {
        "position_id": "intraday:1755716400000:52",
        "pnl": -9.534025262305516,
        "exit_reason": "signal"
      },
      {
        "position_id": "intraday:1756256400000:54",
        "pnl": -3.410924912695505,
        "exit_reason": "time_limit"
      },
      {
        "position_id": "intraday:1756724400000:55",
        "pnl": -11.299802470138294,
        "exit_reason": "stop_loss"
      },
      {
        "position_id": "intraday:1758916800000:58",
        "pnl": -5.157668602580667,
        "exit_reason": "time_limit"
      },
      {
        "position_id": "intraday:1760277600000:64",
        "pnl": -11.444595510873295,
        "exit_reason": "stop_loss"
      },
      {
        "position_id": "intraday:1760500800000:66",
        "pnl": 0.14414130276105883,
        "exit_reason": "time_limit"
      },
      {
        "position_id": "intraday:1760623200000:67",
        "pnl": 42.05619307852009,
        "exit_reason": "time_limit"
      },
      {
        "position_id": "intraday:1761930000000:73",
        "pnl": -20.702594269014437,
        "exit_reason": "time_limit"
      },
      {
        "position_id": "intraday:1762376400000:75",
        "pnl": 23.392504903992123,
        "exit_reason": "time_limit"
      },
      {
        "position_id": "intraday:1763622000000:78",
        "pnl": 57.50707693887744,
        "exit_reason": "time_limit"
      },
      {
        "position_id": "intraday:1765893600000:85",
        "pnl": -11.489579263116426,
        "exit_reason": "stop_loss"
      }
    ]
  }
}
```
