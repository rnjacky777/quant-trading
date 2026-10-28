# 慢均線方向衝突風險上限：全年比較

父portfolio_swing_failure_exit → portfolio_slope_risk_cap；只改風控：完成4h SMA60的24h斜率不支持方向時，risk multiplier=min(原連虧倍率,0.5)。保持訊號／stop／波段失效退出、每日2新單與1x。事前設計見2026-10-28-slope-cap-design.md。
每年10,000 USDT，單邊fee/slippage一般10/5bps、雙成本20/10bps，含實際funding與mark。四筆父完整快照及資料指紋一致才跑候選。全部2024/2025都是調參證據。

|年|成本|父收益|候選收益|父DD|候選DD|總筆數|短線筆數|
|---|---:|---:|---:|---:|---:|---:|---:|
|2024|1|+4.149%|+4.317%|-2.192%|-2.266%|59|18|
|2024|2|+2.475%|+2.686%|-2.471%|-2.386%|60|18|
|2025|1|-0.572%|-0.554%|-2.517%|-2.517%|59|16|
|2025|2|-1.516%|-1.490%|-2.879%|-2.879%|59|16|

四組收益全改善：True；四組回撤皆不退步：False。
判斷：保留風控取捨候選，不宣稱全面升級；2025仍虧，10%目標未達，短線18/16筆頻率未改善。收益提升若來自倉位配置，不等於找到新訊號優勢。
原贏家也可能被縮倉；下方逐筆列出。共享cash與連虧路徑導致後續部位數量變化，即使entry/exit不變也不應直接相減舊交易PnL。
250項pytest通過，另逐筆重算完成bar cap、原signal/stop、risk/stop/cost推導quantity、共享gross/stoprisk/margin、daily2與cash/PnL。原MMR2%非歷史級距、1h OHLC路徑、深度/precision/min quantity、虛擬lot映射限制保留。無paper/testnet/live升級。

## 2024／成本1倍完整指標與取捨

```json
{
  "year": 2024,
  "cost": 1,
  "checks": "passed",
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
  "metrics": {
    "average_loss": -13.068947140094785,
    "average_win": 39.223379559718175,
    "cagr": 0.043075230978348866,
    "exposure": 0.2330108138873079,
    "fees": 82.03088670819652,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.022664788401225988,
    "maximum_margin_ratio": 0.023252979975666936,
    "net_funding": -36.879457983849115,
    "number_of_trades": 59,
    "profit_factor": 1.9174751505800147,
    "sharpe_ratio": 1.471535219966719,
    "slippage": 41.015591249485375,
    "sortino_ratio": 2.1873588544250318,
    "total_return": 0.04316556328300991,
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
  "same_entry_exit_price_paths": true,
  "grouped": {
    "swing/1": {
      "count": 33,
      "pnl": 415.06043569102957
    },
    "swing/-1": {
      "count": 8,
      "pnl": -90.32879231711509
    },
    "intraday/1": {
      "count": 12,
      "pnl": 175.48551485243476
    },
    "intraday/-1": {
      "count": 6,
      "pnl": -68.56152539624351
    }
  },
  "resized_trades": [
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1715259600000,
      "parent_pnl": 28.672269270220802,
      "child_pnl": 14.336134635110401,
      "parent_quantity": 0.021817292533309808,
      "child_quantity": 0.010908646266654904,
      "slope_cap": 0.5
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1715817600000,
      "parent_pnl": -2.289348921918747,
      "child_pnl": -2.2861581139123146,
      "parent_quantity": 0.0057892484707170126,
      "child_quantity": 0.005781179634990518,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1716249600000,
      "parent_pnl": -12.518354333133084,
      "child_pnl": -12.500906723967399,
      "parent_quantity": 0.005892223555323319,
      "child_quantity": 0.005884011196815617,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1716501600000,
      "parent_pnl": 7.843048320571394,
      "child_pnl": 7.832116976233047,
      "parent_quantity": 0.012044458153960933,
      "child_quantity": 0.012027671043379908,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1717426800000,
      "parent_pnl": -13.08604199910415,
      "child_pnl": -6.5339015841620744,
      "parent_quantity": 0.014038647228296173,
      "child_quantity": 0.007009540346174678,
      "slope_cap": 0.5
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1718121600000,
      "parent_pnl": -10.460491631084645,
      "child_pnl": -10.452569961973389,
      "parent_quantity": 0.007719747241608992,
      "child_quantity": 0.007713901122188673,
      "slope_cap": 0.5
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1718107200000,
      "parent_pnl": -12.093014955477651,
      "child_pnl": -12.083856986004198,
      "parent_quantity": 0.008499091265908764,
      "child_quantity": 0.008492654953818533,
      "slope_cap": 0.5
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1719244800000,
      "parent_pnl": -12.16470942019879,
      "child_pnl": -12.155497156926659,
      "parent_quantity": 0.009282065007506798,
      "child_quantity": 0.009275035753982978,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1720166400000,
      "parent_pnl": -9.39844696983729,
      "child_pnl": -9.391329580934315,
      "parent_quantity": 0.0038938832324651768,
      "child_quantity": 0.003890934417475085,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1721088000000,
      "parent_pnl": -6.142938933348858,
      "child_pnl": -6.138286921634974,
      "parent_quantity": 0.0027978312547552293,
      "child_quantity": 0.0027957124735152055,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1720958400000,
      "parent_pnl": 23.53079286147284,
      "child_pnl": 23.51297312970992,
      "parent_quantity": 0.0073111769261573565,
      "child_quantity": 0.0073056402146465145,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1721016000000,
      "parent_pnl": 4.5131846443831485,
      "child_pnl": 4.5097668360571435,
      "parent_quantity": 0.006596690086561369,
      "child_quantity": 0.00659169445175392,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1721030400000,
      "parent_pnl": 3.237030021855257,
      "child_pnl": 3.2345786379585246,
      "parent_quantity": 0.0066458936785067976,
      "child_quantity": 0.006640860782107044,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1721919600000,
      "parent_pnl": 35.064646992259135,
      "child_pnl": 35.038092740243826,
      "parent_quantity": 0.0189391123307163,
      "child_quantity": 0.018924769851754883,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1722376800000,
      "parent_pnl": -24.55519815990185,
      "child_pnl": -12.268301325999946,
      "parent_quantity": 0.020176887026955415,
      "child_quantity": 0.010080803594229177,
      "slope_cap": 0.5
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1722844800000,
      "parent_pnl": -12.6428138099841,
      "child_pnl": -12.648360833391813,
      "parent_quantity": 0.003184556581145128,
      "child_quantity": 0.0031859538025362107,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1724457600000,
      "parent_pnl": -14.191232637250131,
      "child_pnl": -14.197459028052542,
      "parent_quantity": 0.010062815616492207,
      "child_quantity": 0.010067230667968174,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1725634800000,
      "parent_pnl": 2.0318630992578655,
      "child_pnl": 2.032754577400487,
      "parent_quantity": 0.005088729316908462,
      "child_quantity": 0.00509096199240781,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1725652800000,
      "parent_pnl": -7.363272361036235,
      "child_pnl": -7.366502990289963,
      "parent_quantity": 0.004897586920017794,
      "child_quantity": 0.004899735731959101,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1726682400000,
      "parent_pnl": 82.870545890312,
      "child_pnl": 82.90690526922653,
      "parent_quantity": 0.023656676814268373,
      "child_quantity": 0.02366705616035458,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1726776000000,
      "parent_pnl": -4.04018176055318,
      "child_pnl": -4.041954386737033,
      "parent_quantity": 0.0048674538301649055,
      "child_quantity": 0.004869589421239617,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1726761600000,
      "parent_pnl": 3.4703193469858844,
      "child_pnl": 3.471841946538414,
      "parent_quantity": 0.0019125771573273752,
      "child_quantity": 0.0019134162988681828,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1727319600000,
      "parent_pnl": 36.39247799503274,
      "child_pnl": 36.40844516265356,
      "parent_quantity": 0.027463566598433593,
      "child_quantity": 0.02747561621405478,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1728892800000,
      "parent_pnl": 58.310014902047,
      "child_pnl": 58.335598369653695,
      "parent_quantity": 0.016286380467839548,
      "child_quantity": 0.016293526102904625,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1728907200000,
      "parent_pnl": 47.66769422513019,
      "child_pnl": 47.68860838392682,
      "parent_quantity": 0.015827264911786165,
      "child_quantity": 0.015834209110305985,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1729713600000,
      "parent_pnl": 7.3756399587730215,
      "child_pnl": 7.378876014299348,
      "parent_quantity": 0.017335267914519163,
      "child_quantity": 0.01734287374802632,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1730246400000,
      "parent_pnl": -8.294381920763383,
      "child_pnl": -8.298021073515171,
      "parent_quantity": 0.011730399607573614,
      "child_quantity": 0.011735546310054797,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1730232000000,
      "parent_pnl": -25.758308229060745,
      "child_pnl": -25.769609664076476,
      "parent_quantity": 0.01199512280912699,
      "child_quantity": 0.012000385658679356,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1730188800000,
      "parent_pnl": -9.203114947132653,
      "child_pnl": -9.207152805698225,
      "parent_quantity": 0.014644205442735035,
      "child_quantity": 0.014650630574956313,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1731225600000,
      "parent_pnl": 70.10071047941739,
      "child_pnl": 70.13146710430883,
      "parent_quantity": 0.006278126808883815,
      "child_quantity": 0.006280881331483674,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1731240000000,
      "parent_pnl": 61.86611728588032,
      "child_pnl": 61.89326099027132,
      "parent_quantity": 0.0060422940168343734,
      "child_quantity": 0.006044945068004735,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1731340800000,
      "parent_pnl": 30.480792309988612,
      "child_pnl": 30.494165730729428,
      "parent_quantity": 0.003962198879919009,
      "child_quantity": 0.003963937291182768,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1732176000000,
      "parent_pnl": -11.153704729779243,
      "child_pnl": -11.158598407891459,
      "parent_quantity": 0.008141559032990053,
      "child_quantity": 0.008145131134834626,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1732190400000,
      "parent_pnl": -19.431255138244364,
      "child_pnl": -19.439780584297193,
      "parent_quantity": 0.007978120098381907,
      "child_quantity": 0.007981620491538081,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1733148000000,
      "parent_pnl": -24.67948417207865,
      "child_pnl": -12.345156136995469,
      "parent_quantity": 0.020356729402888386,
      "child_quantity": 0.010182830449979263,
      "slope_cap": 0.5
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1733371200000,
      "parent_pnl": -13.213569153012177,
      "child_pnl": -13.234870848277117,
      "parent_quantity": 0.003325625848998219,
      "child_quantity": 0.003330987115706724,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1733752800000,
      "parent_pnl": -24.483232103126024,
      "child_pnl": -24.522701707691017,
      "parent_quantity": 0.01802759820017585,
      "child_quantity": 0.018056660628258076,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1734321600000,
      "parent_pnl": -10.106258118155978,
      "child_pnl": -10.122550493683656,
      "parent_quantity": 0.004657858199071901,
      "child_quantity": 0.004665367167677959,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1734580800000,
      "parent_pnl": -12.715854017297481,
      "child_pnl": -12.736353342209114,
      "parent_quantity": 0.004641685585197132,
      "child_quantity": 0.0046491684818094365,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1734703200000,
      "parent_pnl": 5.899450966547023,
      "child_pnl": 5.908961516290593,
      "parent_quantity": 0.00397222136743422,
      "child_quantity": 0.003978625015692622,
      "slope_cap": 0.5
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1735070400000,
      "parent_pnl": -19.33539138150855,
      "child_pnl": -19.366562112918643,
      "parent_quantity": 0.011453305588981482,
      "child_quantity": 0.011471769549975483,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1735164000000,
      "parent_pnl": -24.159577074344593,
      "child_pnl": -24.19852491217766,
      "parent_quantity": 0.019899196697710685,
      "child_quantity": 0.01993127634395639,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1735596000000,
      "parent_pnl": -8.234196042895244,
      "child_pnl": -8.24747045292227,
      "parent_quantity": 0.0038671785235089764,
      "child_quantity": 0.0038734128314002803,
      "slope_cap": 1.0
    }
  ],
  "reduced_parent_winners": [
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1715259600000,
      "parent_pnl": 28.672269270220802,
      "child_pnl": 14.336134635110401,
      "parent_quantity": 0.021817292533309808,
      "child_quantity": 0.010908646266654904,
      "slope_cap": 0.5
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1716501600000,
      "parent_pnl": 7.843048320571394,
      "child_pnl": 7.832116976233047,
      "parent_quantity": 0.012044458153960933,
      "child_quantity": 0.012027671043379908,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1720958400000,
      "parent_pnl": 23.53079286147284,
      "child_pnl": 23.51297312970992,
      "parent_quantity": 0.0073111769261573565,
      "child_quantity": 0.0073056402146465145,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1721016000000,
      "parent_pnl": 4.5131846443831485,
      "child_pnl": 4.5097668360571435,
      "parent_quantity": 0.006596690086561369,
      "child_quantity": 0.00659169445175392,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1721030400000,
      "parent_pnl": 3.237030021855257,
      "child_pnl": 3.2345786379585246,
      "parent_quantity": 0.0066458936785067976,
      "child_quantity": 0.006640860782107044,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1721919600000,
      "parent_pnl": 35.064646992259135,
      "child_pnl": 35.038092740243826,
      "parent_quantity": 0.0189391123307163,
      "child_quantity": 0.018924769851754883,
      "slope_cap": 1.0
    }
  ]
}
```

## 2024／成本2倍完整指標與取捨

```json
{
  "year": 2024,
  "cost": 2,
  "checks": "passed",
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
  "metrics": {
    "average_loss": -13.196588632543499,
    "average_win": 32.90646891973181,
    "cagr": 0.02680173369366967,
    "exposure": 0.2330108138873079,
    "fees": 145.57350914596424,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.023862812154700652,
    "maximum_margin_ratio": 0.023278162960788662,
    "net_funding": -33.57653098343352,
    "number_of_trades": 60,
    "profit_factor": 1.5500500274200504,
    "sharpe_ratio": 1.017573895703336,
    "slippage": 72.78727508529924,
    "sortino_ratio": 1.4956722974409606,
    "total_return": 0.026857500574976045,
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
  "same_entry_exit_price_paths": true,
  "grouped": {
    "swing/1": {
      "count": 34,
      "pnl": 316.4138700507422
    },
    "swing/-1": {
      "count": 8,
      "pnl": -91.56495127094756
    },
    "intraday/1": {
      "count": 12,
      "pnl": 115.9473719247996
    },
    "intraday/-1": {
      "count": 6,
      "pnl": -72.22128495487225
    }
  },
  "resized_trades": [
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1715259600000,
      "parent_pnl": 21.161194116800104,
      "child_pnl": 10.580597058400052,
      "parent_quantity": 0.018768336255215727,
      "child_quantity": 0.009384168127607864,
      "slope_cap": 0.5
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1715817600000,
      "parent_pnl": -3.138492631937733,
      "child_pnl": -3.1352432112206867,
      "parent_quantity": 0.005286184252071902,
      "child_quantity": 0.005280711230899887,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1716249600000,
      "parent_pnl": -12.465674977878566,
      "child_pnl": -12.45276871131197,
      "parent_quantity": 0.005336082799201997,
      "child_quantity": 0.005330558115849498,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1716501600000,
      "parent_pnl": 4.874045013199431,
      "child_pnl": 4.868998698073324,
      "parent_quantity": 0.01093317581555499,
      "child_quantity": 0.0109218562133878,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1717426800000,
      "parent_pnl": -14.264036425357835,
      "child_pnl": -7.124634117684138,
      "parent_quantity": 0.01251532888377837,
      "child_quantity": 0.006251185604159605,
      "slope_cap": 0.5
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1718121600000,
      "parent_pnl": -10.638506963528641,
      "child_pnl": -10.634927452143245,
      "parent_quantity": 0.0068390126975203126,
      "child_quantity": 0.006836711592308879,
      "slope_cap": 0.5
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1718107200000,
      "parent_pnl": -12.09592941644773,
      "child_pnl": -12.091859529835673,
      "parent_quantity": 0.007441446503874502,
      "child_quantity": 0.007438942699292171,
      "slope_cap": 0.5
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1719244800000,
      "parent_pnl": -12.154645016306759,
      "child_pnl": -12.150555373806128,
      "parent_quantity": 0.008131644118232502,
      "child_quantity": 0.008128908084613973,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1720166400000,
      "parent_pnl": -9.491831275635828,
      "child_pnl": -9.488637583303262,
      "parent_quantity": 0.0036787370444484042,
      "child_quantity": 0.0036774992691497076,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1721088000000,
      "parent_pnl": -12.414109806817105,
      "child_pnl": -12.409932862858213,
      "parent_quantity": 0.005201489171831986,
      "child_quantity": 0.005199739039997192,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1721102400000,
      "parent_pnl": -0.574554870784208,
      "child_pnl": -0.5743615517678778,
      "parent_quantity": 0.00023899915385404614,
      "child_quantity": 0.0002389187384165028,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1720958400000,
      "parent_pnl": 19.98442222615185,
      "child_pnl": 19.977698118423742,
      "parent_quantity": 0.00658876700369686,
      "child_quantity": 0.006586550098017681,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1721016000000,
      "parent_pnl": 2.9589730841524253,
      "child_pnl": 2.9579774860031645,
      "parent_quantity": 0.005977914375289884,
      "child_quantity": 0.005975903001641252,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1721030400000,
      "parent_pnl": 1.7905007441532292,
      "child_pnl": 1.7898982989209038,
      "parent_quantity": 0.006016489367705265,
      "child_quantity": 0.006014465014827029,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1721919600000,
      "parent_pnl": 27.188152501257704,
      "child_pnl": 27.179004572722302,
      "parent_quantity": 0.016438554950429576,
      "child_quantity": 0.016433023911646975,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1722376800000,
      "parent_pnl": -24.485305085282153,
      "child_pnl": -12.238533288471869,
      "parent_quantity": 0.017312948898133698,
      "child_quantity": 0.008653561827121502,
      "slope_cap": 0.5
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1722844800000,
      "parent_pnl": -12.53527227784159,
      "child_pnl": -12.54614766260692,
      "parent_quantity": 0.0030324607628189676,
      "child_quantity": 0.003035091673169413,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1724457600000,
      "parent_pnl": -14.858348284763466,
      "child_pnl": -14.871239129971496,
      "parent_quantity": 0.009283520345066062,
      "child_quantity": 0.009291574566266178,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1725634800000,
      "parent_pnl": 1.1156065805272652,
      "child_pnl": 1.1165744614428974,
      "parent_quantity": 0.004727079993663967,
      "child_quantity": 0.004731181126260703,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1725652800000,
      "parent_pnl": -7.606334031365569,
      "child_pnl": -7.612933154815883,
      "parent_quantity": 0.004565672221942993,
      "child_quantity": 0.004569633319957099,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1726682400000,
      "parent_pnl": 66.72179358780221,
      "child_pnl": 66.77968025842387,
      "parent_quantity": 0.020111620500920992,
      "child_quantity": 0.02012906899396956,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1726776000000,
      "parent_pnl": -4.583281109513181,
      "child_pnl": -4.587257484692663,
      "parent_quantity": 0.004498611674322115,
      "child_quantity": 0.004502514591768477,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1726761600000,
      "parent_pnl": 7.386633345739979,
      "child_pnl": 7.393041860686827,
      "parent_quantity": 0.004554077181895313,
      "child_quantity": 0.004558028220253825,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1727319600000,
      "parent_pnl": 25.614865291868817,
      "child_pnl": 25.637088304627326,
      "parent_quantity": 0.022610818567899295,
      "child_quantity": 0.022630435321834525,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1728892800000,
      "parent_pnl": 48.56179968086585,
      "child_pnl": 48.60393105581501,
      "parent_quantity": 0.014364758271475288,
      "child_quantity": 0.01437722088655065,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1728907200000,
      "parent_pnl": 39.35166892975753,
      "child_pnl": 39.385809755045095,
      "parent_quantity": 0.013994067458032418,
      "child_quantity": 0.014006208468188812,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1729713600000,
      "parent_pnl": 3.4051600878523867,
      "child_pnl": 3.4081143456716196,
      "parent_quantity": 0.01512621538433009,
      "child_quantity": 0.015139338626386752,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1730246400000,
      "parent_pnl": -9.754548984971754,
      "child_pnl": -9.763011862448426,
      "parent_quantity": 0.01055037222137567,
      "child_quantity": 0.010559525541286243,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1730232000000,
      "parent_pnl": -25.442356721285268,
      "child_pnl": -25.464430068600638,
      "parent_quantity": 0.010770799702594865,
      "child_quantity": 0.010780144261564152,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1730188800000,
      "parent_pnl": -10.866280069224013,
      "child_pnl": -10.875707465302987,
      "parent_quantity": 0.012922015892963669,
      "child_quantity": 0.012933226809780252,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1731225600000,
      "parent_pnl": 60.71301173080756,
      "child_pnl": 60.76568528653109,
      "parent_quantity": 0.005564031549531789,
      "child_quantity": 0.0055688588067789035,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1731240000000,
      "parent_pnl": 53.590010006351335,
      "child_pnl": 53.636503769349126,
      "parent_quantity": 0.005368203648208049,
      "child_quantity": 0.005372861008565214,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1731340800000,
      "parent_pnl": 26.982835991838435,
      "child_pnl": 27.006245832244606,
      "parent_quantity": 0.0036325218207483388,
      "child_quantity": 0.003635673333662747,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1732176000000,
      "parent_pnl": -12.221613102562396,
      "child_pnl": -12.232216362068685,
      "parent_quantity": 0.00736517945290727,
      "child_quantity": 0.007371569354828906,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1732190400000,
      "parent_pnl": -19.69167689132819,
      "child_pnl": -19.70876104858636,
      "parent_quantity": 0.0072221381073730665,
      "child_quantity": 0.00722840390910481,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1733148000000,
      "parent_pnl": -24.591265041118646,
      "child_pnl": -12.30629999802857,
      "parent_quantity": 0.01641387573701237,
      "child_quantity": 0.008214058065426303,
      "slope_cap": 0.5
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1733371200000,
      "parent_pnl": -13.00126417107118,
      "child_pnl": -13.027993929360322,
      "parent_quantity": 0.0030396699394976494,
      "child_quantity": 0.003045919304304984,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1733752800000,
      "parent_pnl": -24.394132137703203,
      "child_pnl": -24.44428489570693,
      "parent_quantity": 0.014751282986373812,
      "child_quantity": 0.014781610670166121,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1734321600000,
      "parent_pnl": -10.243673734705899,
      "child_pnl": -10.26473406540288,
      "parent_quantity": 0.004129285606626469,
      "child_quantity": 0.004137775150775381,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1734580800000,
      "parent_pnl": -12.550530034947299,
      "child_pnl": -12.57633311300345,
      "parent_quantity": 0.004129339509934575,
      "child_quantity": 0.0041378291649052015,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1734703200000,
      "parent_pnl": 4.31118763495525,
      "child_pnl": 4.320051157910034,
      "parent_quantity": 0.0036017948760419466,
      "child_quantity": 0.003609199933363826,
      "slope_cap": 0.5
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1735070400000,
      "parent_pnl": -19.790708824966547,
      "child_pnl": -19.831397242362083,
      "parent_quantity": 0.009980161952253415,
      "child_quantity": 0.010000680519768088,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1735164000000,
      "parent_pnl": -24.129172516890804,
      "child_pnl": -24.178780535050194,
      "parent_quantity": 0.015970096153024412,
      "child_quantity": 0.016002929637861565,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1735596000000,
      "parent_pnl": -8.459045274443431,
      "child_pnl": -8.476436524445555,
      "parent_quantity": 0.0035126547087424164,
      "child_quantity": 0.003519876499645397,
      "slope_cap": 1.0
    }
  ],
  "reduced_parent_winners": [
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1715259600000,
      "parent_pnl": 21.161194116800104,
      "child_pnl": 10.580597058400052,
      "parent_quantity": 0.018768336255215727,
      "child_quantity": 0.009384168127607864,
      "slope_cap": 0.5
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1716501600000,
      "parent_pnl": 4.874045013199431,
      "child_pnl": 4.868998698073324,
      "parent_quantity": 0.01093317581555499,
      "child_quantity": 0.0109218562133878,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1720958400000,
      "parent_pnl": 19.98442222615185,
      "child_pnl": 19.977698118423742,
      "parent_quantity": 0.00658876700369686,
      "child_quantity": 0.006586550098017681,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1721016000000,
      "parent_pnl": 2.9589730841524253,
      "child_pnl": 2.9579774860031645,
      "parent_quantity": 0.005977914375289884,
      "child_quantity": 0.005975903001641252,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1721030400000,
      "parent_pnl": 1.7905007441532292,
      "child_pnl": 1.7898982989209038,
      "parent_quantity": 0.006016489367705265,
      "child_quantity": 0.006014465014827029,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1721919600000,
      "parent_pnl": 27.188152501257704,
      "child_pnl": 27.179004572722302,
      "parent_quantity": 0.016438554950429576,
      "child_quantity": 0.016433023911646975,
      "slope_cap": 1.0
    }
  ]
}
```

## 2025／成本1倍完整指標與取捨

```json
{
  "year": 2025,
  "cost": 1,
  "checks": "passed",
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
  "metrics": {
    "average_loss": -11.839148174480503,
    "average_win": 22.007149962123915,
    "cagr": -0.0055467938016101614,
    "exposure": 0.19803675379522886,
    "fees": 80.60106311938954,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.025170352457745127,
    "maximum_margin_ratio": 0.021957946303772777,
    "net_funding": -6.551935711431979,
    "number_of_trades": 59,
    "profit_factor": 0.8829517189878021,
    "sharpe_ratio": -0.25081485578825163,
    "slippage": 40.30054956555791,
    "sortino_ratio": -0.3649245934923985,
    "total_return": -0.005543007769886588,
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
  "same_entry_exit_price_paths": true,
  "grouped": {
    "swing/1": {
      "count": 24,
      "pnl": -30.154731433401704
    },
    "intraday/1": {
      "count": 5,
      "pnl": -40.8643281311674
    },
    "swing/-1": {
      "count": 19,
      "pnl": -59.321227304071
    },
    "intraday/-1": {
      "count": 11,
      "pnl": 74.91020916977439
    }
  },
  "resized_trades": [
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1737129600000,
      "parent_pnl": -24.632084152616724,
      "child_pnl": -24.610206051583056,
      "parent_quantity": 0.007063961907030286,
      "child_quantity": 0.0070576877293625565,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1737100800000,
      "parent_pnl": -3.5040986552370317,
      "child_pnl": -1.7520493276185158,
      "parent_quantity": 0.007418427707898628,
      "child_quantity": 0.003709213853949314,
      "slope_cap": 0.5
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1740427200000,
      "parent_pnl": 39.00638558273115,
      "child_pnl": 39.01335833169146,
      "parent_quantity": 0.006185193010384345,
      "child_quantity": 0.006186298670329202,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1740484800000,
      "parent_pnl": 5.551410085973689,
      "child_pnl": 5.552402451411473,
      "parent_quantity": 0.003537799036787415,
      "child_quantity": 0.0035384314507931475,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1741564800000,
      "parent_pnl": -24.31246822450156,
      "child_pnl": -24.316814301047796,
      "parent_quantity": 0.007434637550804175,
      "child_quantity": 0.007435966560413194,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1741651200000,
      "parent_pnl": -6.929166396449063,
      "child_pnl": -6.93040504845603,
      "parent_quantity": 0.005994180827182444,
      "child_quantity": 0.00599525234194871,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1741705200000,
      "parent_pnl": -24.077730112936617,
      "child_pnl": -24.08203422789377,
      "parent_quantity": 0.008806864113167555,
      "child_quantity": 0.008808438420852594,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1741748400000,
      "parent_pnl": -11.748553720227461,
      "child_pnl": -11.750653881893651,
      "parent_quantity": 0.0073722872210600235,
      "child_quantity": 0.007373605084976088,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1742428800000,
      "parent_pnl": -10.71696640524471,
      "child_pnl": -10.718882161222696,
      "parent_quantity": 0.004411819584644216,
      "child_quantity": 0.004412608237834257,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1742817600000,
      "parent_pnl": -11.682345205918107,
      "child_pnl": -11.684433532205494,
      "parent_quantity": 0.007561358866483808,
      "child_quantity": 0.007562710528689547,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1743022800000,
      "parent_pnl": -4.287764940112167,
      "child_pnl": -4.288531417397397,
      "parent_quantity": 0.006936265624575903,
      "child_quantity": 0.006937505545634967,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1742803200000,
      "parent_pnl": -11.62902482476392,
      "child_pnl": -11.631103619544437,
      "parent_quantity": 0.00810054634422091,
      "child_quantity": 0.008101994391130556,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1743555600000,
      "parent_pnl": -11.269241745273048,
      "child_pnl": -11.271256225530284,
      "parent_quantity": 0.012113439271780622,
      "child_quantity": 0.012115604660083741,
      "slope_cap": 0.5
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1743764400000,
      "parent_pnl": -6.460730423237053,
      "child_pnl": -6.461885338020064,
      "parent_quantity": 0.004955414821266194,
      "child_quantity": 0.004956300647087443,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1743998400000,
      "parent_pnl": -11.929801796030075,
      "child_pnl": -11.931934357451155,
      "parent_quantity": 0.004547671041720984,
      "child_quantity": 0.004548483979604208,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1744412400000,
      "parent_pnl": -11.398393262591888,
      "child_pnl": -11.400430829866664,
      "parent_quantity": 0.009801234222322234,
      "child_quantity": 0.009802986282778803,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1744772400000,
      "parent_pnl": 1.1320094871056758,
      "child_pnl": 1.1322118441776354,
      "parent_quantity": 0.01084844774642143,
      "child_quantity": 0.010850387005894323,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1745611200000,
      "parent_pnl": -0.9153867727728475,
      "child_pnl": -0.9155504065490189,
      "parent_quantity": 0.0009925775767821012,
      "child_quantity": 0.0009927550091220288,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1745222400000,
      "parent_pnl": 49.917980673254874,
      "child_pnl": 49.92690396985465,
      "parent_quantity": 0.0071614036544734305,
      "child_quantity": 0.007162683821018984,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1745352000000,
      "parent_pnl": 15.798249742279923,
      "child_pnl": 15.801073824230082,
      "parent_quantity": 0.004355725471727993,
      "child_quantity": 0.004356504097581186,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1746705600000,
      "parent_pnl": 25.70907622174944,
      "child_pnl": 25.71367195477665,
      "parent_quantity": 0.009483771600266477,
      "child_quantity": 0.00948546691136945,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1746734400000,
      "parent_pnl": 6.894988043735175,
      "child_pnl": 6.896220586048304,
      "parent_quantity": 0.008313307374608935,
      "child_quantity": 0.00831479345450295,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1747324800000,
      "parent_pnl": 6.376590571869566,
      "child_pnl": 6.377730445882906,
      "parent_quantity": 0.010551681630271223,
      "child_quantity": 0.010553567840080656,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1749513600000,
      "parent_pnl": -23.721412714377973,
      "child_pnl": -23.72565313433407,
      "parent_quantity": 0.011020564364125107,
      "child_quantity": 0.011022534391021051,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1750118400000,
      "parent_pnl": 9.277350996984723,
      "child_pnl": 9.279009408512783,
      "parent_quantity": 0.004797765681750324,
      "child_quantity": 0.004798623326342851,
      "slope_cap": 0.5
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1750622400000,
      "parent_pnl": -9.23009737794027,
      "child_pnl": -9.231747342450792,
      "parent_quantity": 0.003885255230435265,
      "child_quantity": 0.0038859497554204364,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1752480000000,
      "parent_pnl": -11.863487794248122,
      "child_pnl": -11.865608501433542,
      "parent_quantity": 0.004671708562668527,
      "child_quantity": 0.004672543673395563,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1752192000000,
      "parent_pnl": 2.8748871814640267,
      "child_pnl": 2.8754010938992858,
      "parent_quantity": 0.003945058505770733,
      "child_quantity": 0.003945763721139534,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1752206400000,
      "parent_pnl": -0.4635765087696627,
      "child_pnl": -0.4636593773198049,
      "parent_quantity": 0.0038229403221682725,
      "child_quantity": 0.003823623707792405,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1754092800000,
      "parent_pnl": -3.732469972169586,
      "child_pnl": -3.7331371853893933,
      "parent_quantity": 0.0036974110500173755,
      "child_quantity": 0.003698071996133494,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1754884800000,
      "parent_pnl": -11.845032606111358,
      "child_pnl": -11.847150014262738,
      "parent_quantity": 0.004718022292019926,
      "child_quantity": 0.004718865681750602,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1755129600000,
      "parent_pnl": -7.859581857654315,
      "child_pnl": -7.860986829953273,
      "parent_quantity": 0.004006857849420032,
      "child_quantity": 0.004007574111987972,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1755144000000,
      "parent_pnl": -8.540795024994331,
      "child_pnl": -8.542321770391036,
      "parent_quantity": 0.0042062067357754255,
      "child_quantity": 0.0042069586337840584,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1755504000000,
      "parent_pnl": -11.569182844823825,
      "child_pnl": -11.571250942301894,
      "parent_quantity": 0.006289895746567311,
      "child_quantity": 0.006291020123085972,
      "slope_cap": 0.5
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1755648000000,
      "parent_pnl": -4.771377023485478,
      "child_pnl": -4.77222995086346,
      "parent_quantity": 0.004180173515380967,
      "child_quantity": 0.00418092075971283,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1755633600000,
      "parent_pnl": -11.61964620166139,
      "child_pnl": -11.621723319927057,
      "parent_quantity": 0.004242416754396671,
      "child_quantity": 0.004243175125278037,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1756180800000,
      "parent_pnl": -5.526440930355314,
      "child_pnl": -5.52742883232766,
      "parent_quantity": 0.0035782455104033384,
      "child_quantity": 0.0035788851545869656,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1757098800000,
      "parent_pnl": -19.975747663190848,
      "child_pnl": -19.979318511185834,
      "parent_quantity": 0.017110606612288866,
      "child_quantity": 0.017113665290058765,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1758844800000,
      "parent_pnl": -5.874392902348753,
      "child_pnl": -5.875443003925464,
      "parent_quantity": 0.004372575223383774,
      "child_quantity": 0.004373356861284522,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1759334400000,
      "parent_pnl": 17.722039544354846,
      "child_pnl": 17.725207521365807,
      "parent_quantity": 0.004584577770995251,
      "child_quantity": 0.004585397306294625,
      "slope_cap": 0.5
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1759348800000,
      "parent_pnl": 16.845843382321753,
      "child_pnl": 16.84885473123743,
      "parent_quantity": 0.004366395854120715,
      "child_quantity": 0.0043671763874025635,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1759377600000,
      "parent_pnl": 11.463626523579228,
      "child_pnl": 11.465675751897336,
      "parent_quantity": 0.004509139644324709,
      "child_quantity": 0.004509945694367464,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1759435200000,
      "parent_pnl": 1.9955115736874052,
      "child_pnl": 1.995868289672308,
      "parent_quantity": 0.004230862180686415,
      "child_quantity": 0.004231618486081818,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1760277600000,
      "parent_pnl": -22.673447395401787,
      "child_pnl": -22.67750048195133,
      "parent_quantity": 0.017596164328765533,
      "child_quantity": 0.01759930980442791,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1760155200000,
      "parent_pnl": -4.802076962171988,
      "child_pnl": -4.802935377445406,
      "parent_quantity": 0.002027900973285098,
      "child_quantity": 0.002028263479172063,
      "slope_cap": 0.5
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1760500800000,
      "parent_pnl": 2.2066511184558038,
      "child_pnl": 2.2070455775696636,
      "parent_quantity": 0.005996308501496797,
      "child_quantity": 0.005997380396604342,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1760659200000,
      "parent_pnl": -4.240689523433918,
      "child_pnl": -4.241447585556914,
      "parent_quantity": 0.0032158457248642916,
      "child_quantity": 0.003216420586764449,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1760623200000,
      "parent_pnl": 71.62902351376209,
      "child_pnl": 71.64182785827563,
      "parent_quantity": 0.015254437594856844,
      "child_quantity": 0.01525716446540098,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1760644800000,
      "parent_pnl": 0.23910359543670506,
      "child_pnl": 0.23914633739604235,
      "parent_quantity": 0.002998884389945935,
      "child_quantity": 0.0029994204680187813,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1761537600000,
      "parent_pnl": -16.1425378861106,
      "child_pnl": -16.14542351272223,
      "parent_quantity": 0.01125821704219207,
      "child_quantity": 0.011260229551682564,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1761494400000,
      "parent_pnl": -13.441441926468933,
      "child_pnl": -13.4438447074192,
      "parent_quantity": 0.011155951045628186,
      "child_quantity": 0.011157945274134412,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1761930000000,
      "parent_pnl": -16.361301685927856,
      "child_pnl": -16.364226418573917,
      "parent_quantity": 0.008624390292515325,
      "child_quantity": 0.008625931981332333,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1762286400000,
      "parent_pnl": -10.267148268730935,
      "child_pnl": -10.268983615593912,
      "parent_quantity": 0.0029696636861086456,
      "child_quantity": 0.0029701945407128397,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1763622000000,
      "parent_pnl": 95.77319339295813,
      "child_pnl": 95.790313729146,
      "parent_quantity": 0.01556883772820485,
      "child_quantity": 0.015571620800654648,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1763121600000,
      "parent_pnl": 37.64719579198225,
      "child_pnl": 37.65392557330889,
      "parent_quantity": 0.002741079528435346,
      "child_quantity": 0.0027415695215261254,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1763712000000,
      "parent_pnl": -6.453766433508532,
      "child_pnl": -6.454920103414538,
      "parent_quantity": 0.0025885867594593426,
      "child_quantity": 0.0025890494930699004,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1765828800000,
      "parent_pnl": -20.49599518471932,
      "child_pnl": -20.499659031727393,
      "parent_quantity": 0.009827619174016236,
      "child_quantity": 0.009829375951024757,
      "slope_cap": 1.0
    }
  ],
  "reduced_parent_winners": []
}
```

## 2025／成本2倍完整指標與取捨

```json
{
  "year": 2025,
  "cost": 2,
  "checks": "passed",
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
  "metrics": {
    "average_loss": -11.38842899204137,
    "average_win": 19.374145073854677,
    "cagr": -0.014905481023492206,
    "exposure": 0.19803675379522886,
    "fees": 135.2217521264161,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.028792562121010667,
    "maximum_margin_ratio": 0.021981013765317733,
    "net_funding": -5.32369393519993,
    "number_of_trades": 59,
    "profit_factor": 0.688586271970181,
    "sharpe_ratio": -0.7993930268700797,
    "slippage": 67.61093526603386,
    "sortino_ratio": -1.1440446620429137,
    "total_return": -0.014895355141020805,
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
  "same_entry_exit_price_paths": true,
  "grouped": {
    "swing/1": {
      "count": 24,
      "pnl": -55.56766210936238
    },
    "intraday/1": {
      "count": 5,
      "pnl": -50.184365235199195
    },
    "swing/-1": {
      "count": 19,
      "pnl": -76.54723187589386
    },
    "intraday/-1": {
      "count": 11,
      "pnl": 33.34570781024738
    }
  },
  "resized_trades": [
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1737129600000,
      "parent_pnl": -24.648476396045336,
      "child_pnl": -24.629657519668882,
      "parent_quantity": 0.006496399693379584,
      "child_quantity": 0.006491439754243495,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1737100800000,
      "parent_pnl": -5.287066917304459,
      "child_pnl": -2.6435334586522297,
      "parent_quantity": 0.006809471959371016,
      "child_quantity": 0.003404735979685508,
      "slope_cap": 0.5
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1740427200000,
      "parent_pnl": 32.68579240738208,
      "child_pnl": 32.694563300377155,
      "parent_quantity": 0.005416521209884448,
      "child_quantity": 0.005417974677107922,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1740484800000,
      "parent_pnl": 4.280077779814289,
      "child_pnl": 4.281226294243721,
      "parent_quantity": 0.0032814937822715985,
      "child_quantity": 0.003282374337054225,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1741564800000,
      "parent_pnl": -24.33100296849602,
      "child_pnl": -24.337531940498273,
      "parent_quantity": 0.006918554519507397,
      "child_quantity": 0.006920411041772936,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1741651200000,
      "parent_pnl": -7.883343893642267,
      "child_pnl": -7.885459307118332,
      "parent_quantity": 0.005658990773607281,
      "child_quantity": 0.005660509305020462,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1741705200000,
      "parent_pnl": -24.11304891567173,
      "child_pnl": -24.11951940196706,
      "parent_quantity": 0.008099917996362092,
      "child_quantity": 0.008102091525249792,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1741748400000,
      "parent_pnl": -11.819129616778415,
      "child_pnl": -11.822301157485501,
      "parent_quantity": 0.006413631190377435,
      "child_quantity": 0.006415352221710542,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1742428800000,
      "parent_pnl": -10.846041141092641,
      "child_pnl": -10.848951563611475,
      "parent_quantity": 0.004037494277098097,
      "child_quantity": 0.004038577696763473,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1742817600000,
      "parent_pnl": -11.761799571442726,
      "child_pnl": -11.764955728227445,
      "parent_quantity": 0.006512595794302199,
      "child_quantity": 0.006514343381759158,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1743022800000,
      "parent_pnl": -5.316949344013958,
      "child_pnl": -5.318376092161143,
      "parent_quantity": 0.006046158910930581,
      "child_quantity": 0.0060477813348931994,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1742803200000,
      "parent_pnl": -11.722320174050482,
      "child_pnl": -11.725465736948852,
      "parent_quantity": 0.006918686027302386,
      "child_quantity": 0.006920542584856675,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1743555600000,
      "parent_pnl": -11.46839550701374,
      "child_pnl": -11.471472931864376,
      "parent_quantity": 0.009669151323173832,
      "child_quantity": 0.009671745939530435,
      "slope_cap": 0.5
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1743764400000,
      "parent_pnl": -6.98159225962196,
      "child_pnl": -6.983465697410501,
      "parent_quantity": 0.004495584201272394,
      "child_quantity": 0.0044967905446122855,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1743998400000,
      "parent_pnl": -11.944793633758792,
      "child_pnl": -11.947998895099989,
      "parent_quantity": 0.004176680839758362,
      "child_quantity": 0.004177801608692567,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1744412400000,
      "parent_pnl": -11.532951385673407,
      "child_pnl": -11.536046133423751,
      "parent_quantity": 0.008153506608365403,
      "child_quantity": 0.008155694517200692,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1744772400000,
      "parent_pnl": -1.3110101110033447,
      "child_pnl": -1.3113619069535773,
      "parent_quantity": 0.008871159352183822,
      "child_quantity": 0.008873539835681066,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1745611200000,
      "parent_pnl": -4.6701152822387275,
      "child_pnl": -4.671368459181926,
      "parent_quantity": 0.0038693060086198304,
      "child_quantity": 0.0038703442967097674,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1745222400000,
      "parent_pnl": 41.57799796518997,
      "child_pnl": 41.589154989213036,
      "parent_quantity": 0.006208112022235679,
      "child_quantity": 0.006209777904634055,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1745352000000,
      "parent_pnl": 13.279449480162931,
      "child_pnl": 13.283012882541923,
      "parent_quantity": 0.003967445340480911,
      "child_quantity": 0.003968509963241509,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1746705600000,
      "parent_pnl": 20.454708390776545,
      "child_pnl": 20.460197199378918,
      "parent_quantity": 0.008494210435271614,
      "child_quantity": 0.00849648976844111,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1746734400000,
      "parent_pnl": 3.9428737757368153,
      "child_pnl": 3.943931804973158,
      "parent_quantity": 0.0075275939627502605,
      "child_quantity": 0.007529613914426351,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1747324800000,
      "parent_pnl": 1.363438717116724,
      "child_pnl": 1.363804581739008,
      "parent_quantity": 0.004648797999673005,
      "child_quantity": 0.004650045456344781,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1749513600000,
      "parent_pnl": -23.7564461959054,
      "child_pnl": -23.762820991563732,
      "parent_quantity": 0.009577534584410111,
      "child_quantity": 0.009580104616366183,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1750118400000,
      "parent_pnl": 6.862905585538639,
      "child_pnl": 6.864747174990587,
      "parent_quantity": 0.004244752019672351,
      "child_quantity": 0.00424589105480086,
      "slope_cap": 0.5
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1750622400000,
      "parent_pnl": -9.455021034702499,
      "child_pnl": -9.457558191419647,
      "parent_quantity": 0.0035342199020083624,
      "child_quantity": 0.003535168273221006,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1752480000000,
      "parent_pnl": -11.8702819951369,
      "child_pnl": -11.873467262053582,
      "parent_quantity": 0.0040870463726798084,
      "child_quantity": 0.004088143089135507,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1752192000000,
      "parent_pnl": 1.341051445703886,
      "child_pnl": 1.341411302934347,
      "parent_quantity": 0.003538857117208226,
      "child_quantity": 0.0035398067327694167,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1752206400000,
      "parent_pnl": -1.623544695505886,
      "child_pnl": -1.6239803568666242,
      "parent_quantity": 0.0034372790954064914,
      "child_quantity": 0.0034382014535602806,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1754092800000,
      "parent_pnl": -4.504573447556765,
      "child_pnl": -4.505782203067556,
      "parent_quantity": 0.0033361521177453757,
      "child_quantity": 0.003337047339524776,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1754884800000,
      "parent_pnl": -11.84821558098388,
      "child_pnl": -11.851394926607453,
      "parent_quantity": 0.004124717440093962,
      "child_quantity": 0.004125824265189438,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1755129600000,
      "parent_pnl": -8.29977431884552,
      "child_pnl": -8.302001477102129,
      "parent_quantity": 0.0035634590956506043,
      "child_quantity": 0.0035644153128972524,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1755144000000,
      "parent_pnl": -8.922226141369265,
      "child_pnl": -8.924620328109135,
      "parent_quantity": 0.0037203138903541223,
      "child_quantity": 0.0037213121979562057,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1755504000000,
      "parent_pnl": -11.624285456211327,
      "child_pnl": -11.627404712511126,
      "parent_quantity": 0.005315087541952301,
      "child_quantity": 0.005316513790504239,
      "slope_cap": 0.5
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1755648000000,
      "parent_pnl": -5.518326218513228,
      "child_pnl": -5.5198070040536615,
      "parent_quantity": 0.0037258073861247804,
      "child_quantity": 0.003726807167849411,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1755633600000,
      "parent_pnl": -11.633509003946438,
      "child_pnl": -11.636630735289502,
      "parent_quantity": 0.0037748715087382637,
      "child_quantity": 0.003775884456310734,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1756180800000,
      "parent_pnl": -6.085678845936617,
      "child_pnl": -6.087311874663437,
      "parent_quantity": 0.003244353978878522,
      "child_quantity": 0.0032452245675805565,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1757098800000,
      "parent_pnl": -20.732129146837458,
      "child_pnl": -20.73769239841908,
      "parent_quantity": 0.013824599752629096,
      "child_quantity": 0.013828309440423072,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1758844800000,
      "parent_pnl": -6.505053565904466,
      "child_pnl": -6.506799129482756,
      "parent_quantity": 0.0038909279579424404,
      "child_quantity": 0.0038919720480579665,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1759334400000,
      "parent_pnl": 14.144456108438789,
      "child_pnl": 14.148251626364567,
      "parent_quantity": 0.004033377163713626,
      "child_quantity": 0.004034459478594378,
      "slope_cap": 0.5
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1759348800000,
      "parent_pnl": 13.516469345555725,
      "child_pnl": 13.520096349754477,
      "parent_quantity": 0.0038625885445270113,
      "child_quantity": 0.0038636250300552117,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1759377600000,
      "parent_pnl": 8.658529344906272,
      "child_pnl": 8.660852771348939,
      "parent_quantity": 0.003968915181826863,
      "child_quantity": 0.003969980199004125,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1759435200000,
      "parent_pnl": 0.4035067720980826,
      "child_pnl": 0.4036150489505066,
      "parent_quantity": 0.0037433308463153173,
      "child_quantity": 0.0037443353302785308,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1760277600000,
      "parent_pnl": -22.900982362699015,
      "child_pnl": -22.90712760352053,
      "parent_quantity": 0.014104276305080876,
      "child_quantity": 0.01410806104117364,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1760155200000,
      "parent_pnl": -5.161996995627966,
      "child_pnl": -5.163382163921433,
      "parent_quantity": 0.0019063207721190492,
      "child_quantity": 0.0019068323135037017,
      "slope_cap": 0.5
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1760500800000,
      "parent_pnl": 0.16930842604681878,
      "child_pnl": 0.16935385820491067,
      "parent_quantity": 0.005112223900522874,
      "child_quantity": 0.005113595712723095,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1760659200000,
      "parent_pnl": -4.832605092247936,
      "child_pnl": -4.833901871644417,
      "parent_quantity": 0.0029385325901256556,
      "child_quantity": 0.0029393211148335562,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1760623200000,
      "parent_pnl": 54.84190999494436,
      "child_pnl": 54.85662625203296,
      "parent_quantity": 0.01254739870288403,
      "child_quantity": 0.012550765667038302,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1760644800000,
      "parent_pnl": -0.6724286566736907,
      "child_pnl": -0.6726090959214532,
      "parent_quantity": 0.002754825239588634,
      "child_quantity": 0.002755564468336569,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1761537600000,
      "parent_pnl": -8.575055972116875,
      "child_pnl": -8.577356999346714,
      "parent_quantity": 0.004825487124123347,
      "child_quantity": 0.004826781993486993,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1761494400000,
      "parent_pnl": -7.410535836382028,
      "child_pnl": -7.412524376725396,
      "parent_quantity": 0.004797733748010604,
      "child_quantity": 0.004799021170043951,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1761930000000,
      "parent_pnl": -17.08598854523034,
      "child_pnl": -17.090573392841733,
      "parent_quantity": 0.00767585685713605,
      "child_quantity": 0.007677916593620344,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1762286400000,
      "parent_pnl": -10.329380972507863,
      "child_pnl": -10.332152754635281,
      "parent_quantity": 0.002744539776840602,
      "child_quantity": 0.0027452762455914097,
      "slope_cap": 1.0
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1763622000000,
      "parent_pnl": 77.36472682241686,
      "child_pnl": 77.38548684353238,
      "parent_quantity": 0.013145226115168114,
      "child_quantity": 0.013148753500100856,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1763121600000,
      "parent_pnl": 34.384907142157736,
      "child_pnl": 34.39413397494891,
      "parent_quantity": 0.0025533015400685797,
      "child_quantity": 0.002553986692024299,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1763712000000,
      "parent_pnl": -6.688705324797839,
      "child_pnl": -6.690500169418658,
      "parent_quantity": 0.002433524530394732,
      "child_quantity": 0.002434177541433627,
      "slope_cap": 1.0
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1765828800000,
      "parent_pnl": -20.706768950281894,
      "child_pnl": -20.712325396718118,
      "parent_quantity": 0.008824105614483425,
      "child_quantity": 0.008826473471598758,
      "slope_cap": 1.0
    }
  ],
  "reduced_parent_winners": []
}
```
