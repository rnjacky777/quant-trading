# 研究總結、波段價格保護優化與收益核對

2026-10-28。已讀10項研究經驗（含本次），主流程仍保留原掃單＋波段確認／效率候選portfolio_confirmed_efficiency。尚無每年10%淨收益／回撤≤10%的可推薦版本。

## 之前經驗總結

增加頻率、延長持有、空單去重均未建立穩定正期望。2025原候選未扣費與funding的成交價差已負，不是只有成本問題。短線30筆虧損沒有完成收盤到過+1R，故本次不給短線加移動保護；波段29筆虧損有6筆曾到+1R，足以支持一次波段exit試驗，但不能先推定盈利。

## 唯一修改

portfolio_confirmed_efficiency → portfolio_swing_protection。只對波段：完成1h收盤達初始價格風險+1R，收盤後把止損提高／降低至成交價，下一根才生效；多空對稱、止損不放寬。初始止損、原訊號及退出、24h短線／168h波段、風險及成本均不變，無新增槓桿。價格保本≠淨保本，跳空仍按開盤價、費用滑價與funding照算。

## 全部期間／成本收益

每年本金10,000 USDT，一般單邊費10bps／滑價5bps，雙成本20bps／10bps，另含實際funding；全部實際1x。四筆父完整快照和行情／mark／funding指紋均逐一重播一致，再執行子候選，沒有刪除不利案例。

|年|成本倍數|父淨收益|候選淨收益|收益差（百分點）|父最大回撤|候選最大回撤|交易數|
|---|---:|---:|---:|---:|---:|---:|---:|
|2024|1|+3.054%|+2.238%|-0.815|-2.970%|-3.296%|104|
|2024|2|-0.081%|-0.293%|-0.212|-4.217%|-4.101%|106|
|2025|1|-3.003%|-2.743%|+0.260|-4.292%|-4.097%|86|
|2025|2|-3.933%|-3.681%|+0.252|-4.713%|-4.465%|86|

## 驗證判斷

只有部分提升：2025一般成本由−3.003%改善至−2.743%，雙成本由−3.933%改善至−3.681%；2024一般成本由+3.054%退步至+2.238%，雙成本由−0.081%退步至−0.293%，兩種成本的回撤亦較父版本大。因此本候選未採用為替代，不宣稱整體提升或解決虧損，仍保留父版本研究參考。

一般成本共同進場事件中，2024有4筆父版本原贏家被保護退出，另5筆父原輸家也走保護退出；2025為1筆父原贏家、6筆父原輸家。這是匹配同策略／方向／進場時間的描述比較，不是獨立因果估計：共享風險釋放、名額、數量與funding路徑都可改變，亦有子新單找不到同事件父單，不拿未匹配事件強行比較。

## 可信範圍

216項pytest通過。新增多空對稱、完成close後下一根生效、當根先觸及高低不追溯保護、wick不觸發、跳空可虧、初始止損保存、短線不受影響；四筆父快照逐一完整重播即驗證預設關閉行為不變。審計逐筆保護trigger close／1R／生效時間，並核對cash/PnL、ID、每日≤2、全部1x、新增gross／stoprisk／margin預算及費率完全一致。

這是同資料可重現比較，不是未見資料驗證。2024／2025已用於調參，10項策略選擇也造成多重嘗試風險；不能合併成本重複樣本或挑盈利月份。每年10%目標與頻率偏好都未被證明可同時達成。

原有固定BTC選樣、1h盤中路徑、固定MMR2%非歷史級距、滑價／深度、精度／最小單量、虛擬多筆部位與交易所倉位映射限制仍在。此出場僅在研究引擎實作，沒有宣稱paper/testnet/live可交易支援，未改交易設定或下單。結果data/perpetual-swing-protection.json，審計data/swing-protection-audit.json；已加入第10項研究經驗。

## 2024／成本1倍完整指標及代價

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding、頻率及共同進場事件對照：

```json
{
  "year": 2024,
  "cost": 1,
  "checks": "passed",
  "metrics": {
    "average_loss": -13.690366564722158,
    "average_win": 32.07682484100516,
    "cagr": 0.022335703438916443,
    "exposure": 0.29368241320432553,
    "fees": 173.11845991178316,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.03295548473479393,
    "maximum_margin_ratio": 0.023252979975666933,
    "net_funding": -37.98355034522608,
    "number_of_trades": 104,
    "profit_factor": 1.2404232103614727,
    "sharpe_ratio": 0.6941161743143024,
    "slippage": 86.5593603264165,
    "sortino_ratio": 1.0049794710913427,
    "total_return": 0.022382076787508698,
    "win_rate": 0.34615384615384615
  },
  "frequency": {
    "total": 104,
    "calendar_days": 366,
    "daily_average": 0.28415300546448086,
    "active_days": 87,
    "zero_entry_days": 279,
    "intraday": 61,
    "intraday_daily_average": 0.16666666666666666,
    "intraday_active_days": 56,
    "groups": [
      {
        "sleeve": "intraday",
        "direction": 1,
        "count": 41,
        "daily_average": 0.11202185792349727
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
        "count": 35,
        "daily_average": 0.09562841530054644
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
      "pnl": -215.0085659571454
    },
    "intraday/-1/signal": {
      "count": 10,
      "pnl": -65.75243227370255
    },
    "swing/-1/stop_loss": {
      "count": 5,
      "pnl": -84.50777905358551
    },
    "intraday/1/time_limit": {
      "count": 13,
      "pnl": 291.2087558606365
    },
    "swing/1/profit_protection": {
      "count": 8,
      "pnl": -18.572493946986835
    },
    "swing/1/time_limit": {
      "count": 10,
      "pnl": 571.9590218153211
    },
    "intraday/1/stop_loss": {
      "count": 11,
      "pnl": -243.76891007796183
    },
    "intraday/1/signal": {
      "count": 17,
      "pnl": -105.68220316969574
    },
    "intraday/-1/time_limit": {
      "count": 6,
      "pnl": 210.94534919371534
    },
    "swing/-1/profit_protection": {
      "count": 2,
      "pnl": -2.0399430318872467
    },
    "swing/1/signal": {
      "count": 5,
      "pnl": -22.92953168286735
    },
    "intraday/-1/stop_loss": {
      "count": 4,
      "pnl": -84.72870065808058
    },
    "swing/-1/signal": {
      "count": 1,
      "pnl": -7.301799142680864
    }
  },
  "stop_updates_checked": 19,
  "common_event_comparison": {
    "common_protected_events": 9,
    "parent_winners": 4,
    "parent_losers": 5,
    "parent_pnl": 29.975482169432777,
    "child_pnl": -14.899448209869233,
    "events": [
      {
        "parent_position_id": "swing:1706443200000:4",
        "child_position_id": "swing:1706443200000:4",
        "parent_pnl": -6.878476976793351,
        "child_pnl": -1.5225320210515845,
        "parent_exit": "signal",
        "child_exit": "profit_protection"
      },
      {
        "parent_position_id": "swing:1709121600000:14",
        "child_position_id": "swing:1709121600000:14",
        "parent_pnl": 15.872574858987392,
        "child_pnl": -1.755331902971432,
        "parent_exit": "signal",
        "child_exit": "profit_protection"
      },
      {
        "parent_position_id": "swing:1714507200000:27",
        "child_position_id": "swing:1714507200000:28",
        "parent_pnl": -2.973682495402992,
        "child_pnl": -0.687500993989221,
        "parent_exit": "signal",
        "child_exit": "profit_protection"
      },
      {
        "parent_position_id": "swing:1719244800000:37",
        "child_position_id": "swing:1719244800000:38",
        "parent_pnl": -12.032806814696821,
        "child_pnl": -1.3524420378980255,
        "parent_exit": "stop_loss",
        "child_exit": "profit_protection"
      },
      {
        "parent_position_id": "swing:1721030400000:45",
        "child_position_id": "swing:1721030400000:46",
        "parent_pnl": 3.210561082260462,
        "child_pnl": -1.0112709164598463,
        "parent_exit": "signal",
        "child_exit": "profit_protection"
      },
      {
        "parent_position_id": "swing:1721016000000:44",
        "child_position_id": "swing:1721016000000:45",
        "parent_pnl": 4.476280688928369,
        "child_pnl": -1.049933809140862,
        "parent_exit": "signal",
        "child_exit": "profit_protection"
      },
      {
        "parent_position_id": "swing:1728907200000:75",
        "child_position_id": "swing:1728907200000:76",
        "parent_pnl": 47.514571552312816,
        "child_pnl": -2.8496009276243406,
        "parent_exit": "time_limit",
        "child_exit": "profit_protection"
      },
      {
        "parent_position_id": "swing:1730188800000:78",
        "child_position_id": "swing:1730188800000:81",
        "parent_pnl": -9.164066679858008,
        "child_pnl": -3.1924334655234166,
        "parent_exit": "signal",
        "child_exit": "profit_protection"
      },
      {
        "parent_position_id": "swing:1734321600000:94",
        "child_position_id": "swing:1734321600000:97",
        "parent_pnl": -10.04947304630509,
        "child_pnl": -1.4784021352105048,
        "parent_exit": "signal",
        "child_exit": "profit_protection"
      }
    ]
  }
}
```

## 2024／成本2倍完整指標及代價

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding、頻率及共同進場事件對照：

```json
{
  "year": 2024,
  "cost": 2,
  "checks": "passed",
  "metrics": {
    "average_loss": -13.266688588216121,
    "average_win": 26.075634026181568,
    "cagr": -0.0029227770862699787,
    "exposure": 0.29413773477518496,
    "fees": 296.00071620200987,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.041008607033619526,
    "maximum_margin_ratio": 0.02327816296078866,
    "net_funding": -35.076711401385715,
    "number_of_trades": 106,
    "profit_factor": 0.9689068754483147,
    "sharpe_ratio": -0.0824669209435503,
    "slippage": 148.00080789153446,
    "sortino_ratio": -0.1172036398475975,
    "total_return": -0.002928769884699589,
    "win_rate": 0.330188679245283
  },
  "frequency": {
    "total": 106,
    "calendar_days": 366,
    "daily_average": 0.2896174863387978,
    "active_days": 88,
    "zero_entry_days": 278,
    "intraday": 62,
    "intraday_daily_average": 0.16939890710382513,
    "intraday_active_days": 57,
    "groups": [
      {
        "sleeve": "intraday",
        "direction": 1,
        "count": 42,
        "daily_average": 0.11475409836065574
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
        "count": 36,
        "daily_average": 0.09836065573770492
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
      "pnl": -212.86494587284085
    },
    "intraday/-1/signal": {
      "count": 10,
      "pnl": -81.64628508348929
    },
    "swing/-1/stop_loss": {
      "count": 5,
      "pnl": -84.26474451039465
    },
    "intraday/1/time_limit": {
      "count": 14,
      "pnl": 210.485095262206
    },
    "swing/1/profit_protection": {
      "count": 8,
      "pnl": -27.643481491876365
    },
    "swing/1/time_limit": {
      "count": 11,
      "pnl": 505.97282620789264
    },
    "intraday/1/stop_loss": {
      "count": 11,
      "pnl": -229.75748666580782
    },
    "intraday/1/signal": {
      "count": 17,
      "pnl": -120.53456667566262
    },
    "intraday/-1/time_limit": {
      "count": 6,
      "pnl": 134.76944606294373
    },
    "swing/-1/profit_protection": {
      "count": 2,
      "pnl": -3.759045775805725
    },
    "swing/1/signal": {
      "count": 5,
      "pnl": -28.989952607818843
    },
    "intraday/-1/stop_loss": {
      "count": 4,
      "pnl": -83.57117156942905
    },
    "swing/-1/signal": {
      "count": 1,
      "pnl": -7.483386126906842
    }
  },
  "stop_updates_checked": 20,
  "common_event_comparison": {
    "common_protected_events": 9,
    "parent_winners": 4,
    "parent_losers": 5,
    "parent_pnl": 12.759213415076879,
    "child_pnl": -24.964469602688837,
    "events": [
      {
        "parent_position_id": "swing:1706443200000:4",
        "child_position_id": "swing:1706443200000:4",
        "parent_pnl": -7.440282114520231,
        "child_pnl": -2.4196386722937246,
        "parent_exit": "signal",
        "child_exit": "profit_protection"
      },
      {
        "parent_position_id": "swing:1709121600000:14",
        "child_position_id": "swing:1709121600000:14",
        "parent_pnl": 13.168875189230455,
        "child_pnl": -2.9796884424905534,
        "parent_exit": "signal",
        "child_exit": "profit_protection"
      },
      {
        "parent_position_id": "swing:1714507200000:27",
        "child_position_id": "swing:1714507200000:29",
        "parent_pnl": -3.6167496789260736,
        "child_pnl": -1.3539968890272263,
        "parent_exit": "signal",
        "child_exit": "profit_protection"
      },
      {
        "parent_position_id": "swing:1719244800000:37",
        "child_position_id": "swing:1719244800000:39",
        "parent_pnl": -12.015611288658583,
        "child_pnl": -2.4050488867784985,
        "parent_exit": "stop_loss",
        "child_exit": "profit_protection"
      },
      {
        "parent_position_id": "swing:1721030400000:45",
        "child_position_id": "swing:1721030400000:47",
        "parent_pnl": 1.767576969751261,
        "child_pnl": -1.8453807149302608,
        "parent_exit": "signal",
        "child_exit": "profit_protection"
      },
      {
        "parent_position_id": "swing:1721016000000:44",
        "child_position_id": "swing:1721016000000:46",
        "parent_pnl": 2.921089362705169,
        "child_pnl": -1.8395508473293036,
        "parent_exit": "signal",
        "child_exit": "profit_protection"
      },
      {
        "parent_position_id": "swing:1728907200000:75",
        "child_position_id": "swing:1728907200000:77",
        "parent_pnl": 38.681041517803415,
        "child_pnl": -4.729035582322892,
        "parent_exit": "time_limit",
        "child_exit": "profit_protection"
      },
      {
        "parent_position_id": "swing:1730188800000:78",
        "child_position_id": "swing:1730188800000:82",
        "parent_pnl": -10.668984747908956,
        "child_pnl": -5.03737831904056,
        "parent_exit": "signal",
        "child_exit": "profit_protection"
      },
      {
        "parent_position_id": "swing:1734321600000:94",
        "child_position_id": "swing:1734321600000:99",
        "parent_pnl": -10.037741794399578,
        "child_pnl": -2.3547512484758166,
        "parent_exit": "signal",
        "child_exit": "profit_protection"
      }
    ]
  }
}
```

## 2025／成本1倍完整指標及代價

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding、頻率及共同進場事件對照：

```json
{
  "year": 2025,
  "cost": 1,
  "checks": "passed",
  "metrics": {
    "average_loss": -12.258694168964638,
    "average_win": 18.937223106400943,
    "cagr": -0.027453507411482447,
    "exposure": 0.23684510900582126,
    "fees": 131.29496396337623,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.040969324161320375,
    "maximum_margin_ratio": 0.022656983414202803,
    "net_funding": -5.559664105951314,
    "number_of_trades": 86,
    "profit_factor": 0.6331144984813306,
    "sharpe_ratio": -1.1627692246874608,
    "slippage": 65.64746401976231,
    "sortino_ratio": -1.615128989000278,
    "total_return": -0.027434976664684307,
    "win_rate": 0.29069767441860467
  },
  "frequency": {
    "total": 86,
    "calendar_days": 365,
    "daily_average": 0.2356164383561644,
    "active_days": 75,
    "zero_entry_days": 290,
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
  "grouped": {
    "swing/1/profit_protection": {
      "count": 6,
      "pnl": -14.665380285479808
    },
    "intraday/1/stop_loss": {
      "count": 4,
      "pnl": -82.73217186528079
    },
    "intraday/-1/signal": {
      "count": 11,
      "pnl": -83.9845243390001
    },
    "swing/1/stop_loss": {
      "count": 10,
      "pnl": -165.71955115585254
    },
    "intraday/1/time_limit": {
      "count": 4,
      "pnl": 14.614131290852745
    },
    "intraday/1/signal": {
      "count": 7,
      "pnl": -46.72705574543616
    },
    "intraday/-1/time_limit": {
      "count": 10,
      "pnl": 173.18777123613293
    },
    "swing/-1/signal": {
      "count": 7,
      "pnl": 13.712579010022251
    },
    "swing/-1/stop_loss": {
      "count": 9,
      "pnl": -153.45053752403362
    },
    "intraday/-1/stop_loss": {
      "count": 7,
      "pnl": -104.23000003102767
    },
    "swing/-1/profit_protection": {
      "count": 2,
      "pnl": -2.4528584118364263
    },
    "swing/1/time_limit": {
      "count": 2,
      "pnl": 65.43849734855091
    },
    "swing/1/signal": {
      "count": 6,
      "pnl": 75.51331930988357
    },
    "swing/-1/time_limit": {
      "count": 1,
      "pnl": 37.1460145156854
    }
  },
  "stop_updates_checked": 19,
  "common_event_comparison": {
    "common_protected_events": 7,
    "parent_winners": 1,
    "parent_losers": 6,
    "parent_pnl": -64.38275392536049,
    "child_pnl": -15.54884562241932,
    "events": [
      {
        "parent_position_id": "swing:1736150400000:1",
        "child_position_id": "swing:1736150400000:1",
        "parent_pnl": -24.19673620982446,
        "child_pnl": -3.856287856391622,
        "parent_exit": "stop_loss",
        "child_exit": "profit_protection"
      },
      {
        "parent_position_id": "swing:1737100800000:5",
        "child_position_id": "swing:1737100800000:5",
        "parent_pnl": -3.4969032293255418,
        "child_pnl": -2.3466675947813536,
        "parent_exit": "signal",
        "child_exit": "profit_protection"
      },
      {
        "parent_position_id": "swing:1742803200000:21",
        "child_position_id": "swing:1742803200000:21",
        "parent_pnl": -11.536908159637788,
        "child_pnl": -1.7226590030320552,
        "parent_exit": "stop_loss",
        "child_exit": "profit_protection"
      },
      {
        "parent_position_id": "swing:1743998400000:27",
        "child_position_id": "swing:1743998400000:27",
        "parent_pnl": -11.824182875426231,
        "child_pnl": -0.8544430467956229,
        "parent_exit": "stop_loss",
        "child_exit": "profit_protection"
      },
      {
        "parent_position_id": "swing:1752206400000:42",
        "child_position_id": "swing:1752206400000:42",
        "parent_pnl": -0.45675613190968384,
        "child_pnl": -1.6329692898633468,
        "parent_exit": "signal",
        "child_exit": "profit_protection"
      },
      {
        "parent_position_id": "swing:1760659200000:69",
        "child_position_id": "swing:1760659200000:70",
        "parent_pnl": 0.3218926298245381,
        "child_pnl": -1.5984153650408035,
        "parent_exit": "signal",
        "child_exit": "profit_protection"
      },
      {
        "parent_position_id": "swing:1761494400000:71",
        "child_position_id": "swing:1761494400000:72",
        "parent_pnl": -13.193159949061318,
        "child_pnl": -3.5374034665145153,
        "parent_exit": "signal",
        "child_exit": "profit_protection"
      }
    ]
  }
}
```

## 2025／成本2倍完整指標及代價

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding、頻率及共同進場事件對照：

```json
{
  "year": 2025,
  "cost": 2,
  "checks": "passed",
  "metrics": {
    "average_loss": -11.584703651521727,
    "average_win": 16.96918809310258,
    "cagr": -0.03683463166932688,
    "exposure": 0.23684510900582126,
    "fees": 216.0223450687685,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.04465366933150294,
    "maximum_margin_ratio": 0.02268118178613781,
    "net_funding": -4.687361464589468,
    "number_of_trades": 86,
    "profit_factor": 0.5035224536138901,
    "sharpe_ratio": -1.7707253734774235,
    "slippage": 108.01113315632205,
    "sortino_ratio": -2.424596425695524,
    "total_return": -0.036809889564912046,
    "win_rate": 0.2558139534883721
  },
  "frequency": {
    "total": 86,
    "calendar_days": 365,
    "daily_average": 0.2356164383561644,
    "active_days": 75,
    "zero_entry_days": 290,
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
  "grouped": {
    "swing/1/profit_protection": {
      "count": 6,
      "pnl": -20.90793919251518
    },
    "intraday/1/stop_loss": {
      "count": 4,
      "pnl": -83.25758959861102
    },
    "intraday/-1/signal": {
      "count": 11,
      "pnl": -73.74761154316231
    },
    "swing/1/stop_loss": {
      "count": 10,
      "pnl": -154.02798128986683
    },
    "intraday/1/time_limit": {
      "count": 4,
      "pnl": 6.64322015992481
    },
    "intraday/1/signal": {
      "count": 7,
      "pnl": -55.396823260726215
    },
    "intraday/-1/time_limit": {
      "count": 10,
      "pnl": 127.69166538313985
    },
    "swing/-1/signal": {
      "count": 7,
      "pnl": 1.423017635097123
    },
    "swing/-1/stop_loss": {
      "count": 9,
      "pnl": -153.27385469508297
    },
    "intraday/-1/stop_loss": {
      "count": 7,
      "pnl": -104.61850011044326
    },
    "swing/-1/profit_protection": {
      "count": 2,
      "pnl": -4.80555372624256
    },
    "swing/1/time_limit": {
      "count": 2,
      "pnl": 54.54664968026259
    },
    "swing/1/signal": {
      "count": 6,
      "pnl": 57.723417583265004
    },
    "swing/-1/time_limit": {
      "count": 1,
      "pnl": 33.90898732582723
    }
  },
  "stop_updates_checked": 19,
  "common_event_comparison": {
    "common_protected_events": 7,
    "parent_winners": 0,
    "parent_losers": 7,
    "parent_pnl": -63.430103042559765,
    "child_pnl": -23.177839373634132,
    "events": [
      {
        "parent_position_id": "swing:1736150400000:1",
        "child_position_id": "swing:1736150400000:1",
        "parent_pnl": -24.306086900156675,
        "child_pnl": -6.202906391154853,
        "parent_exit": "stop_loss",
        "child_exit": "profit_protection"
      },
      {
        "parent_position_id": "swing:1737100800000:5",
        "child_position_id": "swing:1737100800000:5",
        "parent_pnl": -5.274851636945344,
        "child_pnl": -3.880007681129653,
        "parent_exit": "signal",
        "child_exit": "profit_protection"
      },
      {
        "parent_position_id": "swing:1742803200000:21",
        "child_position_id": "swing:1742803200000:21",
        "parent_pnl": -11.617794310536619,
        "child_pnl": -2.9622487900785637,
        "parent_exit": "stop_loss",
        "child_exit": "profit_protection"
      },
      {
        "parent_position_id": "swing:1743998400000:27",
        "child_position_id": "swing:1743998400000:27",
        "parent_pnl": -11.826371051714561,
        "child_pnl": -1.588173720245068,
        "parent_exit": "stop_loss",
        "child_exit": "profit_protection"
      },
      {
        "parent_position_id": "swing:1752206400000:42",
        "child_position_id": "swing:1752206400000:42",
        "parent_pnl": -1.5993840965524908,
        "child_pnl": -2.4626075140461072,
        "parent_exit": "signal",
        "child_exit": "profit_protection"
      },
      {
        "parent_position_id": "swing:1760659200000:69",
        "child_position_id": "swing:1760659200000:70",
        "parent_pnl": -1.530882424347248,
        "child_pnl": -3.217380005997492,
        "parent_exit": "signal",
        "child_exit": "profit_protection"
      },
      {
        "parent_position_id": "swing:1761494400000:71",
        "child_position_id": "swing:1761494400000:72",
        "parent_pnl": -7.274732622306825,
        "child_pnl": -2.8645152709823947,
        "parent_exit": "signal",
        "child_exit": "profit_protection"
      }
    ]
  }
}
```
