# 網路策略研究與掃單微結構確認：實際全年驗證

2026-10-28。父portfolio_directional_loss_guard → portfolio_sweep_structure_confirm，只新增一項短線進場微結構門檻；全部結構stop、原退出、波段與方向風控保留。外部來源及事前設計見2026-10-28-web-pattern-design.md。

## 搜尋後採取的方向

[LuxAlgo作者Session Sweeps](https://www.tradingview.com/script/KdOv0Dfq-Session-Sweeps-LuxAlgo/)描述掃單後等待結構轉向與其他條件；本輪只借用確認概念，不複製其外匯／5m時段或FVG進場。

[LuxAlgo作者Market Structure](https://www.tradingview.com/script/kMDlPZuz-Market-Structure-with-Inducements-Sweeps-LuxAlgo/)區分wick與收盤確認結構；[mickes作者Turtle soup](https://www.tradingview.com/script/AmpHKmaz-Turtle-soup/)使用pivot假突破與轉向確認，不能把後來才確認的pivot畫回去當入場。三根是本次固定工程定義，不是原作者最佳參數，也非完整SMC／CHoCH複現。

[Liu與Tsyvinski原研究](https://www.nber.org/papers/w24877)的日／週動能與此1h圖形不同，不引用其收益證明本策略。搜尋到的二手勝率、圖形截圖或人氣未當盈利證據，未取得可信原版age細節就沒有套用。

## 圖形如何機械判斷

多單：掃過過去20根低點→收回→下一根完成close超過掃單high，且超過確認之前3根high的最高點→下一根開盤交給風控。空單對稱。三根含掃單及再前2根，不含確認bar；相等或僅wick越過不算。4h方向／原強收盤／ATR入場濾網保留，初始stop仍為當時掃單low／high。

## 全部年度及成本

每年10,000USDT，一般單邊費10bps／滑價5bps，雙成本20bps／10bps，另含實際funding，全部1x。父四筆原期間、243h暖機、行情／mark／funding指紋與完整快照（含guard trace）一致後才跑子候選。

|年|成本倍數|父淨收益|候選淨收益|父最大回撤|候選最大回撤|總交易數|短線筆數|
|---|---:|---:|---:|---:|---:|---:|---:|
|2024|1|+3.570%|+3.920%|-3.081%|-2.323%|59|18|
|2024|2|+0.328%|+2.272%|-3.877%|-2.590%|60|18|
|2025|1|-2.454%|-1.109%|-4.381%|-2.961%|59|16|
|2025|2|-3.617%|-2.022%|-4.895%|-3.341%|59|16|

## 判斷與取捨

四組相較父版本收益與回撤均改善，可保留下一輪研究候選：一般2024+3.570%→+3.920%、2025−2.454%→−1.109%；雙成本2024+0.328%→+2.272%、2025−3.617%→−2.022%。但2025仍虧，年淨10%目標未達；不能稱原作者方案有效或已建立可實盤優勢。

頻率代價很大：一般成本短線2024由60→18筆、2025由43→16筆，約日均0.049／0.044，遠低於有機會時每天1–2次的偏好。一般總筆數59／59，雙成本60／59；不把波段數量冒充短線頻率，也不強迫湊單。

改善不是全都來自更好的毛價差：2024一般成交價差損益（含滑價、未扣費/funding）由577.76降至517.36USDT，但費用179.19→87.50，成本減少是重要來源；2025價差由−99.18→−23.24、費用141.02→81.13，兩者都有改善，仍未有正價差。只是更少交易並非必然成功，之前三小時確認／回撤模型已失敗。

濾網也排除原贏家，逐筆在四筆案例保存；不能將被排除父PnL直接相減當候選收益，因共享名額、數量、連虧guard與波段路徑均可變。沒有加槓桿，沒有降低費率或隱藏雙成本失敗。

## 驗證與限制

242項pytest通過：三根只用已完成歷史、相等／wick不通過、多空對稱、原退出及結構stop保留、前綴因果；四筆父完整快照一致，子所有入場、初始stop及risk trace從同243h暖機重算，cash/PnL、ID、每日≤2、1x與gross/stoprisk/margin均核對。

2024／2025與15項研究皆調參，不是未見驗證，網路概念選擇也有多重嘗試風險。保留固定BTC選樣、1h盤中路徑、MMR2%非歷史級距、精度／最小量、滑價深度及虛擬部位到交易所映射限制。沒有paper/testnet/live升級或下單。候選data/perpetual-sweep-structure-confirm.json；審計data/structure-confirm-audit.json。

## 2024／成本1倍完整指標及排除代價

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding、頻率及被排除父贏家／輸家：

```json
{
  "year": 2024,
  "cost": 1,
  "checks": "passed",
  "metrics": {
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
  "grouped": {
    "swing/1/stop_loss": {
      "count": 11,
      "pnl": -197.84559887829656
    },
    "swing/-1/stop_loss": {
      "count": 6,
      "pnl": -84.82146159673896
    },
    "intraday/1/time_limit": {
      "count": 5,
      "pnl": 203.14395654368826
    },
    "swing/1/signal": {
      "count": 11,
      "pnl": -25.97969468629347
    },
    "swing/1/time_limit": {
      "count": 11,
      "pnl": 620.7756542514796
    },
    "intraday/-1/signal": {
      "count": 4,
      "pnl": -31.506309364233758
    },
    "swing/-1/signal": {
      "count": 2,
      "pnl": -10.347338547845387
    },
    "intraday/1/signal": {
      "count": 3,
      "pnl": 48.271189160648234
    },
    "intraday/1/stop_loss": {
      "count": 4,
      "pnl": -86.26184386601858
    },
    "intraday/-1/time_limit": {
      "count": 1,
      "pnl": -19.29299445345819
    },
    "intraday/-1/stop_loss": {
      "count": 1,
      "pnl": -24.10660210059114
    }
  },
  "past_only_risk_trace_checks": 59,
  "excluded_parent_events": [
    {
      "position_id": "intraday:1706061600000:3",
      "pnl": -23.231804563981935,
      "direction": -1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1707177600000:7",
      "pnl": 11.144876965601142,
      "direction": 1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1708398000000:11",
      "pnl": -24.021143279106766,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1708455600000:12",
      "pnl": 2.2663965922392957,
      "direction": 1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1710270000000:17",
      "pnl": 11.382170011920993,
      "direction": 1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1710450000000:18",
      "pnl": -25.214335416233528,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1711220400000:19",
      "pnl": -1.281240045463909,
      "direction": -1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1712260800000:21",
      "pnl": 1.86341489174968,
      "direction": -1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1713996000000:24",
      "pnl": -24.12021441253937,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1714154400000:25",
      "pnl": -11.956432540805267,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1714280400000:26",
      "pnl": 17.79653009576907,
      "direction": -1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1715216400000:28",
      "pnl": -11.751039185446535,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1716926400000:33",
      "pnl": -12.00383468594352,
      "direction": 1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1720090800000:38",
      "pnl": -12.062014344991024,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1720314000000:40",
      "pnl": 42.70341256865959,
      "direction": -1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1720436400000:41",
      "pnl": -12.59566603884036,
      "direction": -1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1720512000000:42",
      "pnl": -23.64659952166057,
      "direction": -1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1721124000000:47",
      "pnl": 23.473635267239505,
      "direction": 1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1721336400000:48",
      "pnl": 87.43298574516315,
      "direction": 1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1721592000000:49",
      "pnl": -7.28822033407215,
      "direction": 1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1721725200000:50",
      "pnl": -23.699953242817752,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1722027600000:52",
      "pnl": -11.930797445943103,
      "direction": -1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1722117600000:53",
      "pnl": -10.803460266733708,
      "direction": 1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1722279600000:54",
      "pnl": -12.110997671643148,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1723032000000:57",
      "pnl": -0.9166459228097008,
      "direction": -1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1723165200000:58",
      "pnl": 3.497530237547892,
      "direction": -1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1723255200000:59",
      "pnl": -12.908001579342633,
      "direction": -1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1723712400000:60",
      "pnl": -11.817091384943097,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1723759200000:61",
      "pnl": 1.9948885714188376,
      "direction": 1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1723989600000:62",
      "pnl": 52.239260509539946,
      "direction": -1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1724691600000:64",
      "pnl": -23.668087785859306,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1724950800000:65",
      "pnl": 35.73383156571978,
      "direction": -1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1725336000000:66",
      "pnl": 62.09168002118901,
      "direction": -1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1727697600000:73",
      "pnl": -24.155957990401593,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1729562400000:76",
      "pnl": -8.237542855472896,
      "direction": 1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1730412000000:81",
      "pnl": -24.42461495160452,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1731888000000:85",
      "pnl": -11.224996487538853,
      "direction": 1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1732291200000:88",
      "pnl": -4.225119807806454,
      "direction": 1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1733720400000:91",
      "pnl": -12.16111631194892,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1733860800000:93",
      "pnl": 32.370970891555444,
      "direction": 1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1734508800000:95",
      "pnl": -24.59616195332356,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1734645600000:97",
      "pnl": -12.53563459658063,
      "direction": 1,
      "exit_reason": "stop_loss"
    }
  ],
  "excluded_parent_winners": 14,
  "excluded_parent_pnl": -32.597140688541465,
  "parent_price_pnl_before_fees_funding": 577.7585518286476,
  "child_price_pnl_before_fees_funding": 517.364313663663,
  "parent_fees": 179.18870198633135,
  "child_fees": 87.49823439967211
}
```

## 2024／成本2倍完整指標及排除代價

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding、頻率及被排除父贏家／輸家：

```json
{
  "year": 2024,
  "cost": 2,
  "checks": "passed",
  "metrics": {
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
  "grouped": {
    "swing/1/stop_loss": {
      "count": 12,
      "pnl": -203.37532504726073
    },
    "swing/-1/stop_loss": {
      "count": 6,
      "pnl": -84.77787137615319
    },
    "intraday/1/time_limit": {
      "count": 5,
      "pnl": 152.98569323123377
    },
    "swing/1/signal": {
      "count": 11,
      "pnl": -40.43388764103817
    },
    "swing/1/time_limit": {
      "count": 11,
      "pnl": 544.195241278288
    },
    "intraday/-1/signal": {
      "count": 4,
      "pnl": -35.30415254202327
    },
    "swing/-1/signal": {
      "count": 2,
      "pnl": -11.239576751520266
    },
    "intraday/1/signal": {
      "count": 3,
      "pnl": 34.857696328310865
    },
    "intraday/1/stop_loss": {
      "count": 4,
      "pnl": -85.86629410316104
    },
    "intraday/-1/time_limit": {
      "count": 1,
      "pnl": -19.751507591737727
    },
    "intraday/-1/stop_loss": {
      "count": 1,
      "pnl": -24.081377699240825
    }
  },
  "past_only_risk_trace_checks": 60,
  "excluded_parent_events": [
    {
      "position_id": "intraday:1706061600000:3",
      "pnl": -23.49702112670379,
      "direction": -1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1707177600000:7",
      "pnl": 4.333265599998563,
      "direction": 1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1708398000000:11",
      "pnl": -24.19316924795533,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1708455600000:12",
      "pnl": -1.603206760031705,
      "direction": 1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1710270000000:17",
      "pnl": 4.4807671364863815,
      "direction": 1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1710450000000:18",
      "pnl": -25.066335473915913,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1711220400000:19",
      "pnl": -5.659450407330381,
      "direction": -1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1712260800000:21",
      "pnl": -0.39761229707456297,
      "direction": -1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1713996000000:24",
      "pnl": -12.07190449438415,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1714154400000:25",
      "pnl": -12.00386086609705,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1714280400000:26",
      "pnl": 11.798208263386696,
      "direction": -1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1715216400000:28",
      "pnl": -11.851067403395767,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1716926400000:33",
      "pnl": -13.549341976679688,
      "direction": 1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1720090800000:38",
      "pnl": -12.030611086242608,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1720314000000:40",
      "pnl": 32.52407310418433,
      "direction": -1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1720436400000:41",
      "pnl": -13.670474418542861,
      "direction": -1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1720512000000:42",
      "pnl": -23.69386124940037,
      "direction": -1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1721336400000:48",
      "pnl": 32.78622979285894,
      "direction": 1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1721592000000:49",
      "pnl": -8.879853051334727,
      "direction": 1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1721725200000:50",
      "pnl": -23.591027121604775,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1722027600000:52",
      "pnl": -11.844621803161436,
      "direction": -1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1722117600000:53",
      "pnl": -11.71328140343668,
      "direction": 1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1722279600000:54",
      "pnl": -11.96419780226028,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1723032000000:57",
      "pnl": -2.597228470253322,
      "direction": -1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1723165200000:58",
      "pnl": 1.9614757784532124,
      "direction": -1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1723255200000:59",
      "pnl": -14.1943910617865,
      "direction": -1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1723712400000:60",
      "pnl": -11.725266351208933,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1723759200000:61",
      "pnl": 0.7187955630162586,
      "direction": 1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1723989600000:62",
      "pnl": 35.65586121070495,
      "direction": -1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1724691600000:64",
      "pnl": -23.475290825396524,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1724950800000:65",
      "pnl": 26.68040670200886,
      "direction": -1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1725336000000:66",
      "pnl": 47.160414746098546,
      "direction": -1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1727697600000:73",
      "pnl": -23.85914633176395,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1729562400000:76",
      "pnl": -10.478053961827792,
      "direction": 1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1730412000000:81",
      "pnl": -23.994276510179766,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1731888000000:85",
      "pnl": -13.100951136484483,
      "direction": 1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1732291200000:88",
      "pnl": -5.2758655877427385,
      "direction": 1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1733720400000:91",
      "pnl": -11.946679950324107,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1733860800000:93",
      "pnl": 25.779654371133823,
      "direction": 1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1734508800000:95",
      "pnl": -24.089800701596946,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1734645600000:97",
      "pnl": -12.203346390864855,
      "direction": 1,
      "exit_reason": "stop_loss"
    }
  ],
  "excluded_parent_winners": 11,
  "excluded_parent_pnl": -200.34204300065142,
  "parent_price_pnl_before_fees_funding": 365.371385883534,
  "child_price_pnl_before_fees_funding": 416.42298307197814,
  "parent_fees": 295.78563641601147,
  "child_fees": 154.79594212441324
}
```

## 2025／成本1倍完整指標及排除代價

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding、頻率及被排除父贏家／輸家：

```json
{
  "year": 2025,
  "cost": 1,
  "checks": "passed",
  "metrics": {
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
  "grouped": {
    "swing/1/stop_loss": {
      "count": 12,
      "pnl": -181.76485772186433
    },
    "intraday/1/stop_loss": {
      "count": 1,
      "pnl": -24.106420492644705
    },
    "swing/1/signal": {
      "count": 10,
      "pnl": 65.86005475463355
    },
    "swing/-1/signal": {
      "count": 8,
      "pnl": 23.048413705849057
    },
    "swing/-1/stop_loss": {
      "count": 10,
      "pnl": -154.61317149448192
    },
    "intraday/-1/stop_loss": {
      "count": 5,
      "pnl": -80.99863561740126
    },
    "intraday/1/signal": {
      "count": 2,
      "pnl": -24.16444907421384
    },
    "intraday/-1/time_limit": {
      "count": 6,
      "pnl": 155.3157750947544
    },
    "intraday/1/time_limit": {
      "count": 2,
      "pnl": 7.493240314290028
    },
    "swing/1/time_limit": {
      "count": 2,
      "pnl": 65.59229656052375
    },
    "swing/-1/time_limit": {
      "count": 1,
      "pnl": 37.45649513561313
    }
  },
  "past_only_risk_trace_checks": 59,
  "excluded_parent_events": [
    {
      "position_id": "intraday:1736326800000:2",
      "pnl": -22.70615687998392,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1736733600000:4",
      "pnl": 2.0940449817480125,
      "direction": -1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1737428400000:7",
      "pnl": 11.620852101266324,
      "direction": 1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1737568800000:8",
      "pnl": -23.21603509417241,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1738029600000:9",
      "pnl": -23.433757001313683,
      "direction": -1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1738476000000:10",
      "pnl": -7.063576502737188,
      "direction": 1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1738627200000:11",
      "pnl": 25.888470157367532,
      "direction": -1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1741698000000:16",
      "pnl": -23.03431272799101,
      "direction": -1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1742284800000:18",
      "pnl": -11.476219589850757,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1742569200000:20",
      "pnl": -4.206584493338578,
      "direction": 1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1743440400000:24",
      "pnl": -5.198252927434967,
      "direction": -1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1746586800000:33",
      "pnl": -11.434902855180681,
      "direction": -1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1746684000000:34",
      "pnl": -9.249281271829911,
      "direction": -1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1750694400000:40",
      "pnl": -22.861752781767027,
      "direction": -1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1753909200000:44",
      "pnl": 2.436933179845871,
      "direction": 1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1755716400000:52",
      "pnl": -22.315407978297515,
      "direction": -1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1756256400000:54",
      "pnl": -11.097399197652287,
      "direction": -1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1756724400000:55",
      "pnl": -11.220271456910158,
      "direction": -1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1758916800000:58",
      "pnl": -4.347177480229282,
      "direction": -1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1760328000000:65",
      "pnl": -9.776316208985953,
      "direction": -1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1761069600000:70",
      "pnl": 28.909995510950314,
      "direction": -1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1762376400000:75",
      "pnl": 56.340126931612886,
      "direction": -1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1762560000000:76",
      "pnl": 15.289052815511457,
      "direction": -1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1764572400000:80",
      "pnl": -22.520215196183173,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1764748800000:81",
      "pnl": -22.889920967632523,
      "direction": -1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1764882000000:82",
      "pnl": -10.111107040077716,
      "direction": 1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1765429200000:83",
      "pnl": -11.46181090213197,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1765893600000:85",
      "pnl": -11.469762166568445,
      "direction": -1,
      "exit_reason": "stop_loss"
    }
  ],
  "excluded_parent_winners": 7,
  "excluded_parent_pnl": -158.51074504196677,
  "parent_price_pnl_before_fees_funding": -99.17589326344834,
  "child_price_pnl_before_fees_funding": -23.238692541875746,
  "parent_fees": 141.0222809076097,
  "child_fees": 81.12953643246324
}
```

## 2025／成本2倍完整指標及排除代價

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding、頻率及被排除父贏家／輸家：

```json
{
  "year": 2025,
  "cost": 2,
  "checks": "passed",
  "metrics": {
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
  "grouped": {
    "swing/1/stop_loss": {
      "count": 12,
      "pnl": -179.2371141184717
    },
    "intraday/1/stop_loss": {
      "count": 1,
      "pnl": -24.1807394194044
    },
    "swing/1/signal": {
      "count": 10,
      "pnl": 47.93754160850224
    },
    "swing/-1/signal": {
      "count": 8,
      "pnl": 11.710936742301662
    },
    "swing/-1/stop_loss": {
      "count": 10,
      "pnl": -154.49333184672457
    },
    "intraday/-1/stop_loss": {
      "count": 5,
      "pnl": -81.66475038900387
    },
    "intraday/1/signal": {
      "count": 2,
      "pnl": -25.94110427725934
    },
    "intraday/-1/time_limit": {
      "count": 6,
      "pnl": 114.61063570301427
    },
    "intraday/1/time_limit": {
      "count": 2,
      "pnl": 0.05133394756417653
    },
    "swing/1/time_limit": {
      "count": 2,
      "pnl": 54.75974355124618
    },
    "swing/-1/time_limit": {
      "count": 1,
      "pnl": 34.21852123844287
    }
  },
  "past_only_risk_trace_checks": 59,
  "excluded_parent_events": [
    {
      "position_id": "intraday:1736326800000:2",
      "pnl": -23.176498822491226,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1736733600000:4",
      "pnl": 0.4047426016243412,
      "direction": -1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1737428400000:7",
      "pnl": 9.275619387453158,
      "direction": 1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1737568800000:8",
      "pnl": -23.469167590090056,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1738029600000:9",
      "pnl": -23.595252831278955,
      "direction": -1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1738476000000:10",
      "pnl": -7.883618574505239,
      "direction": 1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1738627200000:11",
      "pnl": 19.69107377850802,
      "direction": -1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1741698000000:16",
      "pnl": -23.27452598599755,
      "direction": -1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1742284800000:18",
      "pnl": -11.585917263044749,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1742569200000:20",
      "pnl": -5.4191711755975875,
      "direction": 1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1743440400000:24",
      "pnl": -6.607876294180625,
      "direction": -1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1746586800000:33",
      "pnl": -11.50955301485341,
      "direction": -1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1746684000000:34",
      "pnl": -9.84674329642446,
      "direction": -1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1750694400000:40",
      "pnl": -22.973912587550977,
      "direction": -1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1753909200000:44",
      "pnl": -1.7372396805780732,
      "direction": 1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1755716400000:52",
      "pnl": -11.264706573139613,
      "direction": -1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1756256400000:54",
      "pnl": -11.21218830171662,
      "direction": -1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1756724400000:55",
      "pnl": -11.282336277236489,
      "direction": -1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1758916800000:58",
      "pnl": -5.632185301405825,
      "direction": -1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1760328000000:65",
      "pnl": -10.104287447564799,
      "direction": -1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1761069600000:70",
      "pnl": 22.267496072031054,
      "direction": -1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1762376400000:75",
      "pnl": 38.615412598393675,
      "direction": -1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1762560000000:76",
      "pnl": 7.0042840597984934,
      "direction": -1,
      "exit_reason": "time_limit"
    },
    {
      "position_id": "intraday:1764572400000:80",
      "pnl": -11.333673305151256,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1764748800000:81",
      "pnl": -22.910309511396896,
      "direction": -1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1764882000000:82",
      "pnl": -10.252813428684203,
      "direction": 1,
      "exit_reason": "signal"
    },
    {
      "position_id": "intraday:1765429200000:83",
      "pnl": -11.449301842340622,
      "direction": 1,
      "exit_reason": "stop_loss"
    },
    {
      "position_id": "intraday:1765893600000:85",
      "pnl": -11.45187693063749,
      "direction": -1,
      "exit_reason": "stop_loss"
    }
  ],
  "excluded_parent_winners": 6,
  "excluded_parent_pnl": -190.71452753805798,
  "parent_price_pnl_before_fees_funding": -128.54733009417387,
  "child_price_pnl_before_fees_funding": -60.82731488592394,
  "parent_fees": 228.9865357405867,
  "child_fees": 136.2092530349811
}
```
