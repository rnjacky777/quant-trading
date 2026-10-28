# 淨收益不足的問題診斷與48h出場實驗

2026-10-28。使用者要求先找問題、改善淨收益，而非增加成本。沿用portfolio_confirmed_efficiency，不採已失敗的放寬確認／回撤進場。父四筆指紋與完整快照逐一重播一致。

## 核心診斷

1. 負收益不是只有費用問題。成交價差損益=pnl+fees−funding，仍包含實際執行滑價，不是假設零成本重跑。2025原候選價差−166.73USDT、手續費128.31、funding−5.29，淨−300.34；回撤模型2024價差−180.49、費421.34、funding−43.49，淨−645.32；2025價差−229.85、費303.80、funding−5.48，淨−539.13。不能把負價差歸因佣金或透過降低設定美化。

2. 勝率與平均盈虧配比不足。2025原候選淨勝率30.59%、平均贏18.17／平均虧13.10USDT，依該樣本需約41.89%才損益兩平；2024勝率38.61%、樣本平衡勝率32.18%，故仍正收益。這是已實現樣本恆等式，不是預測未來需要固定勝率。回撤模型2024勝率28.90%、樣本平衡35.90%；2025勝率33.15%、樣本平衡43.76%，顯示不只是增加交易就能改善。

3. 重複事件有方向差異。回撤模型同一段4h SMA20/60方向內，後續短線多單2024為114筆−565.57、2025為37筆+93.64；後續短線空單2024為73筆−223.11、2025為69筆−287.31。首次進場組也虧，不能只靠去重保證盈利。原候選2025後續短線空單反而14筆+14.39，故不能將失敗回撤模型的規則直接套到原候選。重複不一定同時持有，不取消多部位能力。

4. 出場與進場品質須分開測。原候選短線24h到期組2024淨+521.28、2025+187.33，但其餘退出組淨虧，故提出延長一個完整交易日的單項exit假說；此分組非延長一定有效的證據。

全部原候選及回撤模型、2024／2025、一般／雙成本、各策略方向／首次重複／出場的數據保存data/profit-failure-diagnostics.json。重複分組使用當時完成4h均線方向，沒有用未來行情；同一成本和分組不當獨立樣本加總。

## 單項修改結果

portfolio_confirmed_efficiency → portfolio_holding_48h：只改短週期最大持有24→48h，所有進場／止損／訊號退出／波段／風控／成本不變。一般費10bps／滑價5bps，雙成本20bps／10bps，含實際funding；年度本金10,000，實際1x。

|年|成本倍數|父收益|48h收益|父回撤|48h回撤|交易數|短週期筆數|
|---|---:|---:|---:|---:|---:|---:|---:|
|2024|1|+3.054%|+0.948%|-2.970%|-4.218%|100|60|
|2024|2|-0.081%|-1.155%|-4.217%|-4.739%|101|59|
|2025|1|-3.003%|-3.636%|-4.292%|-4.700%|84|43|
|2025|2|-3.933%|-4.504%|-4.713%|-5.150%|84|43|

## 決策與限制

不採用48h：四筆成本情境收益全部比父候選差，不能說提高了淨收益；延長持有假說被本次歷史結果反駁。固定止損、訊號反向與時間上限的組合沒有因延長而改善，應回到事件品質，不再掃36／60／72小時直到數字好看。沒有降低費率或加槓桿。

下一個可辯護研究方向是先驗證『回撤模型的重複空頭恢復事件是否應先等待結構失效後重置』，但首次組也虧，且原掃單空單不同，因此需先定義能在當時觀察的事件並保留失敗跨年證據，不能直接禁止所有空單或所有同向多部位。本輪只執行上述一個exit候選，不把待驗證方向宣稱已提升收益。

204項pytest通過；新增真實引擎持有24／48h邊界及48h仍可訊號／止損提早退出。審計核對四筆輸入、僅holding變更、策略名稱和費率完全不變、現金／ID／每日上限／1x，以及每次進場gross／stoprisk／保證金上限；後續市場變動仍可能造成比例漂移。

2024／2025均為調參非未見資料，沒有泛化盈利證據。固定BTC選樣、1h盤中路徑、MMR2%非歷史級距、下單精度／最小單量、深度滑價、獨立研究部位與真實交易所倉位映射限制仍在。全部曲線交易存data/perpetual-holding-exit.json，儀表板標未採用並顯示各策略最長持有。未改live/paper/testnet或下單。

## 2024／成本1倍完整指標

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding與頻率：

```json
{
  "year": 2024,
  "cost": 1,
  "checks": "passed",
  "metrics": {
    "average_loss": -14.588435154022536,
    "average_win": 29.80279607255048,
    "cagr": 0.00946542966621644,
    "exposure": 0.3205463858850313,
    "fees": 161.29026529816704,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.04217650805674311,
    "maximum_margin_ratio": 0.023252979975666936,
    "net_funding": -41.5842441116435,
    "number_of_trades": 100,
    "profit_factor": 1.100026099732577,
    "sharpe_ratio": 0.2861188197690777,
    "slippage": 80.64522724140268,
    "sortino_ratio": 0.40634259038204945,
    "total_return": 0.009484957752777357,
    "win_rate": 0.35
  },
  "frequency": {
    "total": 100,
    "calendar_days": 366,
    "daily_average": 0.273224043715847,
    "active_days": 85,
    "zero_entry_days": 281,
    "intraday": 60,
    "intraday_daily_average": 0.16393442622950818,
    "intraday_active_days": 55,
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
        "count": 20,
        "daily_average": 0.0546448087431694
      },
      {
        "sleeve": "swing",
        "direction": 1,
        "count": 32,
        "daily_average": 0.08743169398907104
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
      "pnl": -193.79917771461726
    },
    "intraday/-1/signal": {
      "count": 15,
      "pnl": 0.03873013758897148
    },
    "swing/-1/stop_loss": {
      "count": 6,
      "pnl": -95.93354890822157
    },
    "intraday/1/time_limit": {
      "count": 4,
      "pnl": 167.48082361642855
    },
    "swing/1/signal": {
      "count": 11,
      "pnl": -25.099691435785395
    },
    "intraday/1/signal": {
      "count": 24,
      "pnl": -46.870877101807714
    },
    "swing/1/time_limit": {
      "count": 10,
      "pnl": 609.4022969842194
    },
    "intraday/1/stop_loss": {
      "count": 12,
      "pnl": -266.0521060255749
    },
    "swing/-1/signal": {
      "count": 2,
      "pnl": -10.17852512770464
    },
    "intraday/-1/stop_loss": {
      "count": 4,
      "pnl": -71.67160547221648
    },
    "intraday/-1/time_limit": {
      "count": 1,
      "pnl": 27.533258575492955
    }
  },
  "executed_price_pnl_before_fees_funding": 297.72408693761247
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
    "average_loss": -13.186071232125194,
    "average_win": 27.357750090438287,
    "cagr": -0.011524328719650145,
    "exposure": 0.3205463858850313,
    "fees": 263.70426549401077,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.04738687528375363,
    "maximum_margin_ratio": 0.023278162960788665,
    "net_funding": -37.04736417990719,
    "number_of_trades": 101,
    "profit_factor": 0.8766532889726124,
    "sharpe_ratio": -0.36185999507180816,
    "slippage": 131.85244987252324,
    "sortino_ratio": -0.5113698053938998,
    "total_return": -0.011547855476773838,
    "win_rate": 0.297029702970297
  },
  "frequency": {
    "total": 101,
    "calendar_days": 366,
    "daily_average": 0.27595628415300544,
    "active_days": 85,
    "zero_entry_days": 281,
    "intraday": 59,
    "intraday_daily_average": 0.16120218579234974,
    "intraday_active_days": 54,
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
        "count": 20,
        "daily_average": 0.0546448087431694
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
      "pnl": -200.60544695752094
    },
    "intraday/-1/signal": {
      "count": 15,
      "pnl": -28.91893663267429
    },
    "swing/-1/stop_loss": {
      "count": 6,
      "pnl": -95.87394569475936
    },
    "intraday/1/time_limit": {
      "count": 4,
      "pnl": 100.85465432260492
    },
    "swing/1/signal": {
      "count": 11,
      "pnl": -38.94759174059998
    },
    "intraday/1/signal": {
      "count": 23,
      "pnl": -82.88303029544042
    },
    "swing/1/time_limit": {
      "count": 11,
      "pnl": 533.4839107280937
    },
    "intraday/1/stop_loss": {
      "count": 12,
      "pnl": -240.23241584848247
    },
    "swing/-1/signal": {
      "count": 2,
      "pnl": -11.034193990229724
    },
    "intraday/-1/stop_loss": {
      "count": 4,
      "pnl": -70.91304749511762
    },
    "intraday/-1/time_limit": {
      "count": 1,
      "pnl": 19.591488836385977
    }
  },
  "executed_price_pnl_before_fees_funding": 185.27307490617775
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
    "average_loss": -13.39139611716549,
    "average_win": 17.059905990535597,
    "cagr": -0.03638391722017609,
    "exposure": 0.25339573108092683,
    "fees": 124.69022116983473,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.04699638208295276,
    "maximum_margin_ratio": 0.0226569834142028,
    "net_funding": -5.417602899971633,
    "number_of_trades": 84,
    "profit_factor": 0.5398073256556993,
    "sharpe_ratio": -1.5207850714838036,
    "slippage": 62.34506779945306,
    "sortino_ratio": -2.069010009849368,
    "total_return": -0.0363594721149364,
    "win_rate": 0.2976190476190476
  },
  "frequency": {
    "total": 84,
    "calendar_days": 365,
    "daily_average": 0.23013698630136986,
    "active_days": 73,
    "zero_entry_days": 292,
    "intraday": 43,
    "intraday_daily_average": 0.1178082191780822,
    "intraday_active_days": 43,
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
        "count": 28,
        "daily_average": 0.07671232876712329
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
        "count": 18,
        "daily_average": 0.049315068493150684
      }
    ]
  },
  "grouped": {
    "swing/1/stop_loss": {
      "count": 12,
      "pnl": -180.04640906338068
    },
    "intraday/1/stop_loss": {
      "count": 4,
      "pnl": -82.5557458293562
    },
    "intraday/-1/signal": {
      "count": 16,
      "pnl": -80.85866720795931
    },
    "swing/1/signal": {
      "count": 9,
      "pnl": 58.074167491454176
    },
    "intraday/1/signal": {
      "count": 10,
      "pnl": -44.75872297587748
    },
    "intraday/-1/time_limit": {
      "count": 4,
      "pnl": 128.8259966569683
    },
    "swing/-1/signal": {
      "count": 7,
      "pnl": 20.374400154805603
    },
    "swing/-1/stop_loss": {
      "count": 10,
      "pnl": -164.53474864114716
    },
    "intraday/-1/stop_loss": {
      "count": 8,
      "pnl": -126.1841304491901
    },
    "intraday/1/time_limit": {
      "count": 1,
      "pnl": 6.120326812666676
    },
    "swing/1/time_limit": {
      "count": 2,
      "pnl": 65.20721135693861
    },
    "swing/-1/time_limit": {
      "count": 1,
      "pnl": 36.741600544703516
    }
  },
  "executed_price_pnl_before_fees_funding": -233.48689707956768
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
    "average_loss": -12.710337123723454,
    "average_win": 15.3494549757034,
    "cagr": -0.04506542958391313,
    "exposure": 0.25339573108092683,
    "fees": 210.41420621653845,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.05149608185971333,
    "maximum_margin_ratio": 0.02268118178613781,
    "net_funding": -4.434954412683762,
    "number_of_trades": 84,
    "profit_factor": 0.428515840674624,
    "sharpe_ratio": -2.147694452033875,
    "slippage": 105.20697281150474,
    "sortino_ratio": -2.8857211424376357,
    "total_return": -0.045035289220535346,
    "win_rate": 0.2619047619047619
  },
  "frequency": {
    "total": 84,
    "calendar_days": 365,
    "daily_average": 0.23013698630136986,
    "active_days": 73,
    "zero_entry_days": 292,
    "intraday": 43,
    "intraday_daily_average": 0.1178082191780822,
    "intraday_active_days": 43,
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
        "count": 28,
        "daily_average": 0.07671232876712329
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
        "count": 18,
        "daily_average": 0.049315068493150684
      }
    ]
  },
  "grouped": {
    "swing/1/stop_loss": {
      "count": 12,
      "pnl": -177.58213743592947
    },
    "intraday/1/stop_loss": {
      "count": 4,
      "pnl": -83.09784269746324
    },
    "intraday/-1/signal": {
      "count": 16,
      "pnl": -100.2018897108846
    },
    "swing/1/signal": {
      "count": 9,
      "pnl": 43.26518364014699
    },
    "intraday/1/signal": {
      "count": 10,
      "pnl": -57.7968116429469
    },
    "intraday/-1/time_limit": {
      "count": 4,
      "pnl": 106.72871135172623
    },
    "swing/-1/signal": {
      "count": 7,
      "pnl": 6.663116770769742
    },
    "swing/-1/stop_loss": {
      "count": 10,
      "pnl": -164.2703067924626
    },
    "intraday/-1/stop_loss": {
      "count": 8,
      "pnl": -115.37192961491976
    },
    "intraday/1/time_limit": {
      "count": 1,
      "pnl": 3.3775098728968254
    },
    "swing/1/time_limit": {
      "count": 2,
      "pnl": 54.36913238852987
    },
    "swing/-1/time_limit": {
      "count": 1,
      "pnl": 33.564371665157516
    }
  },
  "executed_price_pnl_before_fees_funding": -235.50373157615715
}
```
