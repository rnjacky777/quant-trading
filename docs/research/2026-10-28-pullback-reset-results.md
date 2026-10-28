# 回撤空單事件重置：部分問題得到改善，仍未獲利

2026-10-28。portfolio_directional_pullback → portfolio_pullback_reset。單項signal改動：重置後第一個合格空單才允許；必須完成1h向上越過當時完成4h SMA20才重新武裝。多單、波段、止損、24h上限、風險、費率與funding完全不變。設計事先保存於2026-10-28-pullback-reset-design.md。

## 全部四筆比較

每年本金10,000USDT，一般單邊費10bps／滑價5bps，雙成本20bps／10bps，另含實際funding，實際全部1x。父全部四筆資料指紋與完整快照已逐一重播一致。

|年|成本倍數|失敗回撤父收益|事件重置收益|重置回撤|總筆數|短線筆數|原掃單參考收益|
|---|---:|---:|---:|---:|---:|---:|---:|
|2024|1|-6.453%|-5.667%|-6.690%|221|183|+3.054%|
|2024|2|-10.970%|-9.132%|-9.500%|222|183|-0.081%|
|2025|1|-5.391%|-4.550%|-4.670%|147|106|-3.003%|
|2025|2|-7.777%|-6.768%|-6.791%|148|106|-3.933%|

## 決策

四組均改善失敗回撤父候選的淨收益與回撤，但都仍虧，且每組都不如原掃單參考portfolio_confirmed_efficiency。未採用、不提升槓桿、不宣稱已解決負期望；首次進場組原本也虧，去重只能處理部分問題。收益差也受到共享每日名額／資金路徑影響，不能將全部改善直接歸因被移除空單的因果效果。

當前空單事件會在原合格Signal發出時消耗，即便當時風控拒絕成交也不補發，這是可在策略層重現的明確選擇。沒有硬性單持倉限制，新重置可在舊部位仍存在時允許新Signal。未觀察到完整重置或暖機不足時保守不發空單；逐筆審計使用相同243h暖機，沒有偷偷追加更早行情。

## 後續研究判斷與限制

不在本輪接著掃重置均線長度或冷卻時數。下一步應先固定現有候選，檢查各自逐月扣成本期望與訊號後路徑，形成能否放棄這個回撤進場家族的判斷；不能因相較一個很差的父版本改善，就替換較好的原掃單參考或宣稱有可交易優勢。

參考作者原文[The Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf)：反覆在相同資料測試策略有多重嘗試及過擬合問題。因此保留所有失敗，不宣稱本專案已計算PBO或取得獨立統計驗證。2024／2025皆調參，並非未見驗證；成本案例／重疊分組不能加總為獨立樣本。

206項pytest通過，新增第一個空單、無新重置拒絕重複、重新跨越後允許、多單及退出不變、無成交依賴、歷史重放與呼叫順序一致；逐筆全部短線進場用相同暖機的完成歷史重算方向／時間／止損。核對現金、ID、每日≤2、1x與新增部位gross／stoprisk／margin。完整曲線與交易存data/perpetual-pullback-reset.json，儀表板標未採用。

仍有固定BTC選樣、1h盤中路徑、MMR2%非歷史級距、下單精度／最小單量、深度滑價與虛擬部位和交易所倉位映射限制；進場比例不是永久持倉上限。未改live/paper/testnet或下單。

## 2024／成本1倍完整指標

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding與頻率：

```json
{
  "year": 2024,
  "cost": 1,
  "checks": "passed",
  "metrics": {
    "average_loss": -12.908461737596744,
    "average_win": 22.261589244222282,
    "cagr": -0.05655889044025797,
    "exposure": 0.41548093340922027,
    "fees": 356.0672463631262,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.06690273738899366,
    "maximum_margin_ratio": 0.02325297997566693,
    "net_funding": -46.514662606339044,
    "number_of_trades": 221,
    "profit_factor": 0.7185722337524262,
    "sharpe_ratio": -1.491442788076976,
    "slippage": 178.0336266562445,
    "sortino_ratio": -2.0791567421507393,
    "total_return": -0.05667167301906606,
    "win_rate": 0.29411764705882354
  },
  "frequency": {
    "total": 221,
    "calendar_days": 366,
    "daily_average": 0.6038251366120219,
    "active_days": 173,
    "zero_entry_days": 193,
    "intraday": 183,
    "intraday_daily_average": 0.5,
    "intraday_active_days": 151,
    "groups": [
      {
        "sleeve": "intraday",
        "direction": 1,
        "count": 134,
        "daily_average": 0.366120218579235
      },
      {
        "sleeve": "intraday",
        "direction": -1,
        "count": 49,
        "daily_average": 0.13387978142076504
      },
      {
        "sleeve": "swing",
        "direction": 1,
        "count": 30,
        "daily_average": 0.08196721311475409
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
      "count": 50,
      "pnl": -888.1518342522758
    },
    "intraday/1/signal": {
      "count": 50,
      "pnl": -248.8339612933011
    },
    "intraday/1/time_limit": {
      "count": 34,
      "pnl": 468.3392041564146
    },
    "swing/1/stop_loss": {
      "count": 9,
      "pnl": -163.5621164939558
    },
    "intraday/-1/signal": {
      "count": 16,
      "pnl": -66.33954926572231
    },
    "intraday/-1/time_limit": {
      "count": 17,
      "pnl": 185.26031620073036
    },
    "intraday/-1/stop_loss": {
      "count": 15,
      "pnl": -265.3558825033382
    },
    "swing/-1/stop_loss": {
      "count": 6,
      "pnl": -93.32031278092047
    },
    "swing/1/signal": {
      "count": 11,
      "pnl": -32.952512260477384
    },
    "swing/1/time_limit": {
      "count": 10,
      "pnl": 549.4625485310947
    },
    "swing/-1/signal": {
      "count": 2,
      "pnl": -9.708566915191152
    },
    "intraday/-1/end_of_data": {
      "count": 1,
      "pnl": -1.5540633137012354
    }
  },
  "intraday_entries_recomputed": 183,
  "executed_price_pnl_before_fees_funding": -164.13482122117873
}
```

## 2024／成本2倍完整指標

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding與頻率：

```json
{
  "year": 2024,
  "cost": 2,
  "checks": "passed",
  "metrics": {
    "average_loss": -12.733332567581444,
    "average_win": 18.63776105062631,
    "cagr": -0.09113798718898247,
    "exposure": 0.41548093340922027,
    "fees": 603.3740942152671,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.09499757040644419,
    "maximum_margin_ratio": 0.023278162960788662,
    "net_funding": -42.62941575474115,
    "number_of_trades": 222,
    "profit_factor": 0.5545690347267567,
    "sharpe_ratio": -2.724602118061756,
    "slippage": 301.68708163508984,
    "sortino_ratio": -3.736252286893425,
    "total_return": -0.09131631192924228,
    "win_rate": 0.2747747747747748
  },
  "frequency": {
    "total": 222,
    "calendar_days": 366,
    "daily_average": 0.6065573770491803,
    "active_days": 173,
    "zero_entry_days": 193,
    "intraday": 183,
    "intraday_daily_average": 0.5,
    "intraday_active_days": 151,
    "groups": [
      {
        "sleeve": "intraday",
        "direction": 1,
        "count": 134,
        "daily_average": 0.366120218579235
      },
      {
        "sleeve": "intraday",
        "direction": -1,
        "count": 49,
        "daily_average": 0.13387978142076504
      },
      {
        "sleeve": "swing",
        "direction": 1,
        "count": 31,
        "daily_average": 0.08469945355191257
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
      "count": 50,
      "pnl": -862.3894295240058
    },
    "intraday/1/signal": {
      "count": 50,
      "pnl": -310.79164159929724
    },
    "intraday/1/time_limit": {
      "count": 34,
      "pnl": 331.7507356147699
    },
    "swing/1/stop_loss": {
      "count": 10,
      "pnl": -167.55725819359932
    },
    "intraday/-1/signal": {
      "count": 16,
      "pnl": -92.67057290927266
    },
    "intraday/-1/time_limit": {
      "count": 17,
      "pnl": 120.60892258633186
    },
    "intraday/-1/stop_loss": {
      "count": 15,
      "pnl": -262.4558678658293
    },
    "swing/-1/stop_loss": {
      "count": 6,
      "pnl": -92.31451112310204
    },
    "swing/1/signal": {
      "count": 11,
      "pnl": -40.654205890165656
    },
    "swing/1/time_limit": {
      "count": 10,
      "pnl": 476.36055635295594
    },
    "swing/-1/signal": {
      "count": 2,
      "pnl": -10.421239989877034
    },
    "intraday/-1/end_of_data": {
      "count": 1,
      "pnl": -2.6286067513160813
    }
  },
  "intraday_entries_recomputed": 183,
  "executed_price_pnl_before_fees_funding": -267.1596093223991
}
```

## 2025／成本1倍完整指標

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding與頻率：

```json
{
  "year": 2025,
  "cost": 1,
  "checks": "passed",
  "metrics": {
    "average_loss": -12.647247665574609,
    "average_win": 15.436110200212225,
    "cagr": -0.045528193790402516,
    "exposure": 0.3054445839516037,
    "fees": 248.14832036423405,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.04669596225814654,
    "maximum_margin_ratio": 0.022656983414202806,
    "net_funding": -6.438419943379132,
    "number_of_trades": 147,
    "profit_factor": 0.6291295976451045,
    "sharpe_ratio": -1.4537440000309216,
    "slippage": 124.0741411029444,
    "sortino_ratio": -2.0129858802059193,
    "total_return": -0.04549775135501277,
    "win_rate": 0.3401360544217687
  },
  "frequency": {
    "total": 147,
    "calendar_days": 365,
    "daily_average": 0.40273972602739727,
    "active_days": 118,
    "zero_entry_days": 247,
    "intraday": 106,
    "intraday_daily_average": 0.29041095890410956,
    "intraday_active_days": 92,
    "groups": [
      {
        "sleeve": "intraday",
        "direction": 1,
        "count": 53,
        "daily_average": 0.14520547945205478
      },
      {
        "sleeve": "intraday",
        "direction": -1,
        "count": 53,
        "daily_average": 0.14520547945205478
      },
      {
        "sleeve": "swing",
        "direction": 1,
        "count": 22,
        "daily_average": 0.06027397260273973
      },
      {
        "sleeve": "swing",
        "direction": -1,
        "count": 19,
        "daily_average": 0.052054794520547946
      }
    ]
  },
  "grouped": {
    "intraday/-1/signal": {
      "count": 21,
      "pnl": -85.8642363798966
    },
    "swing/1/stop_loss": {
      "count": 11,
      "pnl": -177.66487808988086
    },
    "intraday/1/stop_loss": {
      "count": 11,
      "pnl": -186.82775103873504
    },
    "intraday/1/signal": {
      "count": 23,
      "pnl": -148.15394959737196
    },
    "intraday/1/time_limit": {
      "count": 19,
      "pnl": 375.38425211531535
    },
    "swing/1/signal": {
      "count": 10,
      "pnl": 65.49399382114206
    },
    "intraday/-1/stop_loss": {
      "count": 19,
      "pnl": -323.92428818714006
    },
    "intraday/-1/time_limit": {
      "count": 13,
      "pnl": 85.64010459962535
    },
    "swing/-1/signal": {
      "count": 8,
      "pnl": 19.982167129648175
    },
    "swing/-1/stop_loss": {
      "count": 10,
      "pnl": -164.43506162736412
    },
    "swing/1/time_limit": {
      "count": 1,
      "pnl": 48.7314207810442
    },
    "swing/-1/time_limit": {
      "count": 1,
      "pnl": 36.66071292348779
    }
  },
  "intraday_entries_recomputed": 106,
  "executed_price_pnl_before_fees_funding": -200.3907732425126
}
```

## 2025／成本2倍完整指標

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding與頻率：

```json
{
  "year": 2025,
  "cost": 2,
  "checks": "passed",
  "metrics": {
    "average_loss": -10.778801133391003,
    "average_win": 14.045177793012579,
    "cagr": -0.06772228293592653,
    "exposure": 0.3068142906060952,
    "fees": 399.6833635614034,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.06791155874846444,
    "maximum_margin_ratio": 0.022681181786137806,
    "net_funding": -5.206109918581228,
    "number_of_trades": 148,
    "profit_factor": 0.4343457007014402,
    "sharpe_ratio": -2.55957553898796,
    "slippage": 199.84160973642608,
    "sortino_ratio": -3.44551208777826,
    "total_return": -0.0676775347464893,
    "win_rate": 0.25
  },
  "frequency": {
    "total": 148,
    "calendar_days": 365,
    "daily_average": 0.4054794520547945,
    "active_days": 118,
    "zero_entry_days": 247,
    "intraday": 106,
    "intraday_daily_average": 0.29041095890410956,
    "intraday_active_days": 92,
    "groups": [
      {
        "sleeve": "intraday",
        "direction": 1,
        "count": 53,
        "daily_average": 0.14520547945205478
      },
      {
        "sleeve": "intraday",
        "direction": -1,
        "count": 53,
        "daily_average": 0.14520547945205478
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
        "count": 19,
        "daily_average": 0.052054794520547946
      }
    ]
  },
  "grouped": {
    "intraday/-1/signal": {
      "count": 21,
      "pnl": -110.04021468209953
    },
    "swing/1/stop_loss": {
      "count": 11,
      "pnl": -164.86415069753028
    },
    "intraday/1/stop_loss": {
      "count": 11,
      "pnl": -152.39739328009972
    },
    "intraday/1/signal": {
      "count": 23,
      "pnl": -164.43514019691
    },
    "intraday/1/time_limit": {
      "count": 19,
      "pnl": 213.02437755191497
    },
    "swing/1/signal": {
      "count": 10,
      "pnl": 46.95426406553386
    },
    "intraday/-1/stop_loss": {
      "count": 19,
      "pnl": -318.3841862749225
    },
    "intraday/-1/time_limit": {
      "count": 13,
      "pnl": 43.64398161412689
    },
    "swing/-1/signal": {
      "count": 8,
      "pnl": 5.869771706335687
    },
    "swing/-1/stop_loss": {
      "count": 10,
      "pnl": -162.64973999382042
    },
    "swing/1/time_limit": {
      "count": 2,
      "pnl": 53.42597460694961
    },
    "swing/-1/time_limit": {
      "count": 1,
      "pnl": 33.07710811558567
    }
  },
  "intraday_entries_recomputed": 106,
  "executed_price_pnl_before_fees_funding": -271.8858739849512
}
```
