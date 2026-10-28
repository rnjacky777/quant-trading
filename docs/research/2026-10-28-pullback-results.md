# 對稱趨勢回撤恢復：完整結果與失敗證據

2026-10-28。portfolio_confirmed_efficiency → portfolio_directional_pullback，單項替換短線signal，波段／出場／風險／成本不變；全部父指紋及完整快照逐一重播一致。每年重設10,000USDT，一般單邊10bps費＋5bps滑價，雙成本20bps＋10bps，含實際funding。

## 結論

未採用。兩年一般及雙成本收益全部比父候選差，2024雙成本回撤超過10%。增加交易不代表增加有效優勢；保留原父候選研究參考，而非宣稱原候選已通過盈利目標。

## 全部四筆結果

|年|成本倍數|父收益|新收益|新回撤|父短線筆數|新短線筆數|新總筆數|短線日均|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|2024|1|+3.054%|-6.453%|-7.457%|60|225|263|0.615|
|2024|2|-0.081%|-10.970%|-11.328%|59|225|264|0.615|
|2025|1|-3.003%|-5.391%|-5.510%|43|141|178|0.386|
|2025|2|-3.933%|-7.777%|-7.800%|43|141|180|0.386|

## 機會與成本診斷

原始4h方向／1h回撤恢復事件2024有411次、2025有400次；ATR門檻後254／151次。這是執行前機會，尚未套退出日、風險與每日名額，不當成交。合格ATR/close中位數0.810%／0.757%，只約雙成本來回費／滑價0.6%的1.35／1.26倍，且不含funding；ATR是波動，不能當預期利潤。保存data/pullback-opportunity-diagnostics.json。

組合策略共用名額與風險，短線改動也會影響波段交易與資金路徑，不能把收益差全歸因短線本身或費用。詳細策略／方向／退出原因在各成本案例分開保存，不加總重疊樣本。

## 外部研究與後續可辯護方向

檢閱[Liu與Tsyvinski原研究](https://www.nber.org/papers/w24877)及[論文](https://www.nber.org/system/files/working_papers/w24877/w24877.pdf)：研究報告日／週頻率的加密貨幣時間序列動能，不直接支持1h均線回撤或此處的成本後策略。不能因論文有動能結果，就把本次失敗包裝成已驗證策略；也不把該歷史樣本直接外推2024／2025。

下一個待驗證假說應先回到交易級診斷：把回撤恢復後的損失按多空、首次／同方向重複恢復事件、進場時已知成本空間與退出原因拆解，檢查是否是高頻來回交叉重複消耗風險及成本。先保存診斷再決定是否有理由測試事件重置／冷卻，不盲掃SMA長度、ATR門檻或加槓桿。本輪不再新增另一個候選。

## 可重現與限制

203項pytest通過。所有實際短線進場以進場前完成資料重算方向／時間／止損；核對現金、獨立部位ID、1x、每日≤2，以及每次新增的gross／stoprisk／margin預算。交易成本、失敗期間及完整曲線保留data/perpetual-directional-pullback.json。儀表板名稱多空趨勢回撤恢復（未採用），未覆寫父結果。

2024／2025均為調參證據、非未見驗證。固定BTC有市場選樣限制，不能推廣到其他資產。仍有1h盤中路徑、固定MMR2%非歷史級距、下單精度／最小量、深度及實際滑價、虛擬研究部位與交易所倉位映射等限制；進場預算非永久持倉比例上限。未改live/paper/testnet，未下單。

## 2024／成本1倍完整指標及分組

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding與頻率：

```json
{
  "year": 2024,
  "cost": 1,
  "metrics": {
    "average_loss": -12.572652921633063,
    "average_win": 22.44429538030315,
    "cagr": -0.06440408001054487,
    "exposure": 0.450199203187251,
    "fees": 421.33605547908644,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.07457497878878638,
    "maximum_margin_ratio": 0.023252979975666933,
    "net_funding": -43.489927888749015,
    "number_of_trades": 263,
    "profit_factor": 0.7255227494877994,
    "sharpe_ratio": -1.563992866694111,
    "slippage": 210.66803528311317,
    "sortino_ratio": -2.1993850134297728,
    "total_return": -0.06453196474422984,
    "win_rate": 0.2889733840304182
  },
  "frequency": {
    "total": 263,
    "calendar_days": 366,
    "daily_average": 0.7185792349726776,
    "active_days": 199,
    "zero_entry_days": 167,
    "intraday": 225,
    "intraday_daily_average": 0.6147540983606558,
    "intraday_active_days": 179,
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
        "count": 91,
        "daily_average": 0.24863387978142076
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
  "parent_frequency": {
    "total": 101,
    "calendar_days": 366,
    "daily_average": 0.27595628415300544,
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
      "count": 50,
      "pnl": -885.759040499215
    },
    "intraday/1/signal": {
      "count": 50,
      "pnl": -253.35710336326792
    },
    "intraday/1/time_limit": {
      "count": 34,
      "pnl": 481.76280536776255
    },
    "swing/1/stop_loss": {
      "count": 9,
      "pnl": -163.1667013559263
    },
    "intraday/-1/signal": {
      "count": 33,
      "pnl": -105.73493923158442
    },
    "intraday/-1/time_limit": {
      "count": 28,
      "pnl": 337.08286035323204
    },
    "intraday/-1/stop_loss": {
      "count": 28,
      "pnl": -479.1655468090862
    },
    "swing/-1/stop_loss": {
      "count": 6,
      "pnl": -79.25570004162921
    },
    "swing/1/signal": {
      "count": 11,
      "pnl": -32.95472478388585
    },
    "swing/1/time_limit": {
      "count": 10,
      "pnl": 548.602115823255
    },
    "swing/-1/signal": {
      "count": 2,
      "pnl": -9.730412685888934
    },
    "intraday/-1/end_of_data": {
      "count": 2,
      "pnl": -3.6432602161096455
    }
  },
  "intraday_entries_recomputed": 225,
  "checks": "passed"
}
```

## 2024／成本2倍完整指標及分組

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding與頻率：

```json
{
  "year": 2024,
  "cost": 2,
  "metrics": {
    "average_loss": -12.354638470493965,
    "average_win": 18.133639267303955,
    "cagr": -0.10948367854450392,
    "exposure": 0.450199203187251,
    "fees": 707.2976077943531,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.11327912988399569,
    "maximum_margin_ratio": 0.023278162960788665,
    "net_funding": -40.184434943777504,
    "number_of_trades": 264,
    "profit_factor": 0.5399530148920451,
    "sharpe_ratio": -3.052463322800959,
    "slippage": 353.6488080711717,
    "sortino_ratio": -4.181785058234998,
    "total_return": -0.10969568368267413,
    "win_rate": 0.2689393939393939
  },
  "frequency": {
    "total": 264,
    "calendar_days": 366,
    "daily_average": 0.7213114754098361,
    "active_days": 199,
    "zero_entry_days": 167,
    "intraday": 225,
    "intraday_daily_average": 0.6147540983606558,
    "intraday_active_days": 179,
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
        "count": 91,
        "daily_average": 0.24863387978142076
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
  "parent_frequency": {
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
    "intraday/1/stop_loss": {
      "count": 50,
      "pnl": -857.1877865800009
    },
    "intraday/1/signal": {
      "count": 50,
      "pnl": -314.30256483037414
    },
    "intraday/1/time_limit": {
      "count": 34,
      "pnl": 340.989645769105
    },
    "swing/1/stop_loss": {
      "count": 10,
      "pnl": -166.51838492768002
    },
    "intraday/-1/signal": {
      "count": 33,
      "pnl": -158.48459566337758
    },
    "intraday/-1/time_limit": {
      "count": 28,
      "pnl": 188.79986584618413
    },
    "intraday/-1/stop_loss": {
      "count": 28,
      "pnl": -458.69717224451995
    },
    "swing/-1/stop_loss": {
      "count": 6,
      "pnl": -89.28601160169542
    },
    "swing/1/signal": {
      "count": 11,
      "pnl": -40.101229772900936
    },
    "swing/1/time_limit": {
      "count": 10,
      "pnl": 473.89969336872605
    },
    "swing/-1/signal": {
      "count": 2,
      "pnl": -10.373439201776504
    },
    "intraday/-1/end_of_data": {
      "count": 2,
      "pnl": -5.694856988444118
    }
  },
  "intraday_entries_recomputed": 225,
  "checks": "passed"
}
```

## 2025／成本1倍完整指標及分組

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding與頻率：

```json
{
  "year": 2025,
  "cost": 1,
  "metrics": {
    "average_loss": -12.484929513574935,
    "average_win": 16.04361594486701,
    "cagr": -0.053949239577267605,
    "exposure": 0.3234790549024084,
    "fees": 303.80079960306983,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.05510097375404721,
    "maximum_margin_ratio": 0.0226569834142028,
    "net_funding": -5.4825349757239215,
    "number_of_trades": 178,
    "profit_factor": 0.637119962331849,
    "sharpe_ratio": -1.557197055520377,
    "slippage": 151.90038031412882,
    "sortino_ratio": -2.18082655857979,
    "total_return": -0.05391332713682495,
    "win_rate": 0.33146067415730335
  },
  "frequency": {
    "total": 178,
    "calendar_days": 365,
    "daily_average": 0.4876712328767123,
    "active_days": 134,
    "zero_entry_days": 231,
    "intraday": 141,
    "intraday_daily_average": 0.3863013698630137,
    "intraday_active_days": 113,
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
        "count": 88,
        "daily_average": 0.2410958904109589
      },
      {
        "sleeve": "swing",
        "direction": 1,
        "count": 21,
        "daily_average": 0.057534246575342465
      },
      {
        "sleeve": "swing",
        "direction": -1,
        "count": 16,
        "daily_average": 0.043835616438356165
      }
    ]
  },
  "parent_frequency": {
    "total": 85,
    "calendar_days": 365,
    "daily_average": 0.2328767123287671,
    "active_days": 74,
    "zero_entry_days": 291,
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
        "count": 19,
        "daily_average": 0.052054794520547946
      }
    ]
  },
  "grouped": {
    "intraday/-1/signal": {
      "count": 38,
      "pnl": -210.2643414494469
    },
    "swing/1/stop_loss": {
      "count": 10,
      "pnl": -165.99691295313454
    },
    "intraday/1/stop_loss": {
      "count": 11,
      "pnl": -199.04900752883754
    },
    "intraday/1/signal": {
      "count": 23,
      "pnl": -147.4369645729625
    },
    "intraday/1/time_limit": {
      "count": 19,
      "pnl": 347.3330258728477
    },
    "swing/1/signal": {
      "count": 10,
      "pnl": 67.50067669266956
    },
    "intraday/-1/stop_loss": {
      "count": 27,
      "pnl": -439.02034044619046
    },
    "intraday/-1/time_limit": {
      "count": 23,
      "pnl": 243.65211553501643
    },
    "swing/-1/signal": {
      "count": 6,
      "pnl": 19.156763632402637
    },
    "swing/-1/stop_loss": {
      "count": 9,
      "pnl": -140.45187497247164
    },
    "swing/1/time_limit": {
      "count": 1,
      "pnl": 48.53706842799472
    },
    "swing/-1/time_limit": {
      "count": 1,
      "pnl": 36.90652039384889
    }
  },
  "intraday_entries_recomputed": 141,
  "checks": "passed"
}
```

## 2025／成本2倍完整指標及分組

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding與頻率：

```json
{
  "year": 2025,
  "cost": 2,
  "metrics": {
    "average_loss": -10.74372969255839,
    "average_win": 13.855008248053503,
    "cagr": -0.07782420660295186,
    "exposure": 0.3300993037324506,
    "fees": 485.54570109255184,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.07800455604897782,
    "maximum_margin_ratio": 0.022681181786137806,
    "net_funding": -4.351099739876561,
    "number_of_trades": 180,
    "profit_factor": 0.45571983607013455,
    "sharpe_ratio": -2.64894373757965,
    "slippage": 242.77280548520687,
    "sortino_ratio": -3.6319937607637547,
    "total_return": -0.07777306614517998,
    "win_rate": 0.2611111111111111
  },
  "frequency": {
    "total": 180,
    "calendar_days": 365,
    "daily_average": 0.4931506849315068,
    "active_days": 135,
    "zero_entry_days": 230,
    "intraday": 141,
    "intraday_daily_average": 0.3863013698630137,
    "intraday_active_days": 113,
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
        "count": 88,
        "daily_average": 0.2410958904109589
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
        "count": 17,
        "daily_average": 0.04657534246575343
      }
    ]
  },
  "parent_frequency": {
    "total": 85,
    "calendar_days": 365,
    "daily_average": 0.2328767123287671,
    "active_days": 74,
    "zero_entry_days": 291,
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
        "count": 19,
        "daily_average": 0.052054794520547946
      }
    ]
  },
  "grouped": {
    "intraday/-1/signal": {
      "count": 38,
      "pnl": -255.3848059408996
    },
    "swing/1/stop_loss": {
      "count": 10,
      "pnl": -153.27115988853197
    },
    "intraday/1/stop_loss": {
      "count": 11,
      "pnl": -175.82527301405358
    },
    "intraday/1/signal": {
      "count": 23,
      "pnl": -163.79981341945035
    },
    "intraday/1/time_limit": {
      "count": 19,
      "pnl": 186.22814733228654
    },
    "swing/1/signal": {
      "count": 10,
      "pnl": 46.50829270322025
    },
    "intraday/-1/stop_loss": {
      "count": 27,
      "pnl": -387.04989504396895
    },
    "intraday/-1/time_limit": {
      "count": 23,
      "pnl": 168.98446250769973
    },
    "swing/-1/signal": {
      "count": 7,
      "pnl": 8.386751172045086
    },
    "swing/-1/stop_loss": {
      "count": 9,
      "pnl": -139.0248479506188
    },
    "swing/1/time_limit": {
      "count": 2,
      "pnl": 53.26919579091005
    },
    "swing/-1/time_limit": {
      "count": 1,
      "pnl": 33.24828429961036
    }
  },
  "intraday_entries_recomputed": 141,
  "checks": "passed"
}
```
