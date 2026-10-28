# PA＋SMC：波段較快退出結果

2026-10-27。父候選 portfolio_pa_smc → portfolio_pa_smc_fast_exit。只將波段反向通道退出10根4H改為5根；其餘設定不變。設計見2026-10-27-pa-smc-exit-design.md。

四筆父候選已在執行腳本中逐一完整快照重播一致，核對行情、mark、funding指紋後才執行候選。每年重設10,000 USDT；含費用、滑價與實際funding；全部實際成交1x。

|年度|成本倍數|父收益|新收益|父最大回撤|新最大回撤|交易數|
|---|---:|---:|---:|---:|---:|---:|
|2024|1|+2.123%|+0.135%|-4.524%|-3.808%|147|
|2024|2|-0.966%|-2.755%|-5.380%|-4.524%|149|
|2025|1|-6.002%|-4.641%|-8.005%|-6.673%|144|
|2025|2|-7.130%|-5.997%|-8.436%|-7.258%|147|

## 判斷與限制

2025虧損與回撤下降，但2024收益由2.123%降至0.135%，且雙成本兩年皆虧損；不取代父候選，不增加槓桿。兩年各淨收益10%目標未通過。較快退出存在截斷贏家的代價，不能用2025改善推論全面較優。

下一個研究方向應先量測失敗突破進場後的持續性／最大有利與不利變動，再形成一個可於當時觀察的進場假說；不在5根附近反覆掃參數，也不把事後最大漲跌視為當時可知。

2024、2025已用於調參，非未見驗證。未新增資料或提出未經來源支持的市場規律；本輪是對內部交易證據的單項退出實驗。仍有固定MMR2%非歷史級距、1h盤中路徑、虛擬獨立部位與真實交易所倉位差異、精度／最小下單未驗證等原有限制。未改paper/testnet/live或下單。

188項pytest測試通過；包含多空對稱的較快通道退出與未完成4H禁止提前退出。所有指標與逐筆資產曲線保存於data/perpetual-pa-smc-exit.json，儀表板候選名稱為PA＋SMC波段快速退出（實驗）。

## 2024／成本1倍

全部指標（收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價與funding）：

```json
{
  "average_loss": -13.225999610550929,
  "average_win": 23.02734749311246,
  "cagr": 0.0013431202823870336,
  "exposure": 0.3964712578258395,
  "fees": 210.66696474622657,
  "liquidation_count": 0,
  "liquidation_fees": 0,
  "maximum_drawdown": -0.038075480662166816,
  "maximum_margin_ratio": 0.022809664519905966,
  "net_funding": -37.96848596947516,
  "number_of_trades": 147,
  "profit_factor": 1.0109419547056553,
  "sharpe_ratio": 0.054626583905536805,
  "slippage": 105.33357423005799,
  "sortino_ratio": 0.0793278393417221,
  "total_return": 0.0013458800846806174,
  "win_rate": 0.3673469387755102
}
```

依部位／方向／退出原因拆解（描述性，非獨立因果貢獻）：

```json
{
  "swing/1/signal": {
    "count": 40,
    "pnl": 367.0980159553231
  },
  "swing/-1/signal": {
    "count": 18,
    "pnl": -13.683420587886031
  },
  "swing/-1/stop_loss": {
    "count": 10,
    "pnl": -120.06991824918165
  },
  "intraday/-1/signal": {
    "count": 10,
    "pnl": -64.75668182898242
  },
  "intraday/1/time_limit": {
    "count": 13,
    "pnl": 337.4439460123207
  },
  "swing/1/stop_loss": {
    "count": 17,
    "pnl": -352.2801323776122
  },
  "intraday/1/stop_loss": {
    "count": 11,
    "pnl": -239.52163904217258
  },
  "intraday/1/signal": {
    "count": 17,
    "pnl": -103.8515812702651
  },
  "swing/1/time_limit": {
    "count": 1,
    "pnl": 78.53735932950812
  },
  "intraday/-1/time_limit": {
    "count": 6,
    "pnl": 207.48214853270952
  },
  "intraday/-1/stop_loss": {
    "count": 4,
    "pnl": -82.93929562692495
  }
}
```

## 2024／成本2倍

全部指標（收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價與funding）：

```json
{
  "average_loss": -13.108255502288108,
  "average_win": 18.545125177476802,
  "cagr": -0.02749441759984894,
  "exposure": 0.3964712578258395,
  "fees": 365.48902724044746,
  "liquidation_count": 0,
  "liquidation_fees": 0,
  "maximum_drawdown": -0.045236659069205376,
  "maximum_margin_ratio": 0.0228341112193495,
  "net_funding": -34.80305722688437,
  "number_of_trades": 149,
  "profit_factor": 0.7810691913411474,
  "sharpe_ratio": -0.7927840965723596,
  "slippage": 182.7448211562261,
  "sortino_ratio": -1.1370232839154155,
  "total_return": -0.02755008938134107,
  "win_rate": 0.35570469798657717
}
```

依部位／方向／退出原因拆解（描述性，非獨立因果貢獻）：

```json
{
  "swing/1/signal": {
    "count": 41,
    "pnl": 277.19765169597036
  },
  "swing/-1/signal": {
    "count": 18,
    "pnl": -28.510337324769083
  },
  "swing/-1/stop_loss": {
    "count": 10,
    "pnl": -119.38984339001048
  },
  "intraday/-1/signal": {
    "count": 10,
    "pnl": -80.44385355635787
  },
  "intraday/1/time_limit": {
    "count": 14,
    "pnl": 248.9771635574774
  },
  "swing/1/stop_loss": {
    "count": 17,
    "pnl": -351.4184444723241
  },
  "intraday/1/stop_loss": {
    "count": 11,
    "pnl": -225.48209732749368
  },
  "intraday/1/signal": {
    "count": 17,
    "pnl": -118.18496101282456
  },
  "swing/1/time_limit": {
    "count": 1,
    "pnl": 70.74192366693256
  },
  "intraday/-1/time_limit": {
    "count": 6,
    "pnl": 132.59553370070915
  },
  "intraday/-1/stop_loss": {
    "count": 4,
    "pnl": -81.5836293506976
  }
}
```

## 2025／成本1倍

全部指標（收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價與funding）：

```json
{
  "average_loss": -10.848714845557716,
  "average_win": 16.603085316952747,
  "cagr": -0.04644533377625648,
  "exposure": 0.3587490012555644,
  "fees": 195.87495555293955,
  "liquidation_count": 0,
  "liquidation_fees": 0,
  "maximum_drawdown": -0.06673228740737203,
  "maximum_margin_ratio": 0.02247704748262925,
  "net_funding": -11.931648717855218,
  "number_of_trades": 144,
  "profit_factor": 0.5886229047302,
  "sharpe_ratio": -1.3058527526068784,
  "slippage": 97.93743817673665,
  "sortino_ratio": -1.7888175193322575,
  "total_return": -0.04641429312598866,
  "win_rate": 0.2777777777777778
}
```

依部位／方向／退出原因拆解（描述性，非獨立因果貢獻）：

```json
{
  "swing/1/stop_loss": {
    "count": 18,
    "pnl": -235.19139736351045
  },
  "swing/1/signal": {
    "count": 31,
    "pnl": 41.897227955896504
  },
  "intraday/1/stop_loss": {
    "count": 4,
    "pnl": -82.25616344151102
  },
  "swing/-1/stop_loss": {
    "count": 20,
    "pnl": -291.7404649892776
  },
  "intraday/-1/signal": {
    "count": 11,
    "pnl": -83.11107078337197
  },
  "intraday/1/time_limit": {
    "count": 4,
    "pnl": 14.473143314621888
  },
  "intraday/1/signal": {
    "count": 7,
    "pnl": -46.12483501974575
  },
  "intraday/-1/time_limit": {
    "count": 10,
    "pnl": 171.19165353490354
  },
  "swing/-1/signal": {
    "count": 26,
    "pnl": 59.98732509662963
  },
  "intraday/-1/stop_loss": {
    "count": 7,
    "pnl": -102.99639466640662
  },
  "swing/1/time_limit": {
    "count": 6,
    "pnl": 89.72804510187945
  }
}
```

## 2025／成本2倍

全部指標（收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價與funding）：

```json
{
  "average_loss": -9.986893174464223,
  "average_win": 14.13339979289255,
  "cagr": -0.06001409519752354,
  "exposure": 0.3587490012555644,
  "fees": 325.024929201184,
  "liquidation_count": 0,
  "liquidation_fees": 0,
  "maximum_drawdown": -0.07257620999054204,
  "maximum_margin_ratio": 0.022500952574451484,
  "net_funding": -11.028133111777763,
  "number_of_trades": 147,
  "profit_factor": 0.4589821136723367,
  "sharpe_ratio": -1.912245639015934,
  "slippage": 162.5123634232584,
  "sortino_ratio": -2.5779637720572293,
  "total_return": -0.05997427498213914,
  "win_rate": 0.24489795918367346
}
```

依部位／方向／退出原因拆解（描述性，非獨立因果貢獻）：

```json
{
  "swing/1/stop_loss": {
    "count": 18,
    "pnl": -233.50279322483152
  },
  "swing/1/signal": {
    "count": 32,
    "pnl": -7.307464045619977
  },
  "intraday/1/stop_loss": {
    "count": 4,
    "pnl": -82.78088330493031
  },
  "swing/-1/stop_loss": {
    "count": 20,
    "pnl": -257.3158396724855
  },
  "intraday/-1/signal": {
    "count": 11,
    "pnl": -63.893713402796294
  },
  "intraday/1/time_limit": {
    "count": 4,
    "pnl": 6.581606356833011
  },
  "intraday/1/signal": {
    "count": 7,
    "pnl": -54.43153622291039
  },
  "intraday/-1/time_limit": {
    "count": 10,
    "pnl": 125.60472398556574
  },
  "swing/-1/signal": {
    "count": 27,
    "pnl": 1.0122894415436967
  },
  "intraday/-1/stop_loss": {
    "count": 8,
    "pnl": -104.01742739760427
  },
  "swing/1/time_limit": {
    "count": 6,
    "pnl": 70.3082876658387
  }
}
```
