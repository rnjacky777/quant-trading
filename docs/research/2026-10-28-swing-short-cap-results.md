# 波段空單風險上限：全年比較與決策

portfolio_swing_failure_exit → portfolio_swing_short_risk_cap。只將波段空單risk倍率與0.5取min，不重複減半；訊號、stop、退出及共享風控保留。事前登記見2026-10-28-swing-short-cap-design.md。
每年10,000 USDT，正常單邊費10bps／滑價5bps，雙成本20／10bps，實際mark與funding。設定maximum_leverage=2保留，實際交易全部1x。四組父完整快照及指紋重播相同後才測候選。

|年|成本|父收益|子收益|增加USDT|父DD|子DD|總筆數|短線筆數|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|2024|1|+4.149%|+4.270%|+12.16|-2.192%|-2.192%|59|18|
|2024|2|+2.475%|+2.596%|+12.04|-2.471%|-2.471%|60|18|
|2025|1|-0.572%|-0.313%|+25.89|-2.517%|-2.364%|59|16|
|2025|2|-1.516%|-1.253%|+26.35|-2.879%|-2.722%|59|16|

決策：保留風險配置研究候選，不取代原基準。四組收益小升，2024最大回撤不變、2025改善；但2025仍虧、每年10%目標未達、頻率不變。這是直接用歷史分組提出的假說，不能據此宣稱未見優勢。
策略回測4組父重播＋4組候選；研究候選1個。39項相關程式測試通過，測試數不是策略優化次數或盈利證據。
每筆僅使用進場前完成歷史推導訊號、stop與風險數量，核對共享gross/stoprisk/margin准入、cash/PnL、ID與每日兩筆；共同入場的成交價及退出時間完全相同，主要是數量改變而非訊號改善。本樣本沒有新增或漏掉進場，也沒有被縮小的原波段空單贏家：它們原已受連虧倍率限制；這不是未來不會縮小贏家的保證。共享equity導致的非目標數量變化與全部共同交易列於下方。
短線2024/2025為18/16筆、18/16個UTC活躍日、每日0.0492/0.0438筆，不強迫湊數。月度mark-to-market與所有指標如下。
2024/2025均為調參，重疊成本案例非獨立證據。固定BTC選樣、OHLC盤中路徑、固定滑價與深度、精度及最小量、未驗歷史margin級距、虛擬多lot交易所映射限制保留。未變更paper/testnet/live或送單。

## 2024 成本1：完整指標及取捨

```json
{
  "year": 2024,
  "cost": 1,
  "checks": "passed",
  "metrics": {
    "average_loss": -13.622148458238845,
    "average_win": 39.88779764205493,
    "cagr": 0.042612857169041396,
    "exposure": 0.2330108138873079,
    "fees": 86.84298310958896,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.021924097242473684,
    "maximum_margin_ratio": 0.023252979975666936,
    "net_funding": -37.51360431321577,
    "number_of_trades": 59,
    "profit_factor": 1.8707673605145858,
    "sharpe_ratio": 1.4406612436039126,
    "slippage": 43.421640254846324,
    "sortino_ratio": 2.127546665359632,
    "total_return": 0.04270220012706605,
    "win_rate": 0.3898305084745763
  },
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
    "swing/1": {
      "count": 33,
      "pnl": 415.5304681229101
    },
    "swing/-1": {
      "count": 8,
      "pnl": -78.81539207605398
    },
    "intraday/1": {
      "count": 12,
      "pnl": 165.42566606282676
    },
    "intraday/-1": {
      "count": 6,
      "pnl": -75.11874083901805
    }
  },
  "common_entries": [
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1711404000000,
      "parent_pnl": -12.247820911463347,
      "child_pnl": -12.262116593165908,
      "parent_quantity": 0.016022560886407987,
      "child_quantity": 0.01604126245235574
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1717426800000,
      "parent_pnl": -13.08604199910415,
      "child_pnl": -13.101316054180387,
      "parent_quantity": 0.014038647228296173,
      "child_quantity": 0.01405503316615084
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1725634800000,
      "parent_pnl": 2.0318630992578655,
      "child_pnl": 2.0342346940370644,
      "parent_quantity": 0.005088729316908462,
      "child_quantity": 0.005094668892210136
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1735070400000,
      "parent_pnl": -19.33539138150855,
      "child_pnl": -19.357959690008723,
      "parent_quantity": 0.011453305588981482,
      "child_quantity": 0.011466673910769172
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1735164000000,
      "parent_pnl": -24.159577074344593,
      "child_pnl": -24.18777618228554,
      "parent_quantity": 0.019899196697710685,
      "child_quantity": 0.01992242308093296
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1735596000000,
      "parent_pnl": -8.234196042895244,
      "child_pnl": -8.243807013414552,
      "parent_quantity": 0.0038671785235089764,
      "child_quantity": 0.003871692302217757
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1706486400000,
      "parent_pnl": 47.54849505127301,
      "child_pnl": 47.60399375227485,
      "parent_quantity": 0.042227691306232246,
      "child_quantity": 0.042276979554183636
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1715259600000,
      "parent_pnl": 28.672269270220802,
      "child_pnl": 28.705735601753577,
      "parent_quantity": 0.021817292533309808,
      "child_quantity": 0.021842757721927633
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1716501600000,
      "parent_pnl": 7.843048320571394,
      "child_pnl": 7.852202742666494,
      "parent_quantity": 0.012044458153960933,
      "child_quantity": 0.012058516470235604
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1721919600000,
      "parent_pnl": 35.064646992259135,
      "child_pnl": 35.105574520187396,
      "parent_quantity": 0.0189391123307163,
      "child_quantity": 0.01896121810149514
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1722376800000,
      "parent_pnl": -24.55519815990185,
      "child_pnl": -24.58385903758572,
      "parent_quantity": 0.020176887026955415,
      "child_quantity": 0.02020043753089984
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1726682400000,
      "parent_pnl": 82.870545890312,
      "child_pnl": 82.96727256154027,
      "parent_quantity": 0.023656676814268373,
      "child_quantity": 0.023684288935993697
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1727319600000,
      "parent_pnl": 36.39247799503274,
      "child_pnl": 36.43495537003239,
      "parent_quantity": 0.027463566598433593,
      "child_quantity": 0.027495622129727414
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1729713600000,
      "parent_pnl": 7.3756399587730215,
      "child_pnl": 7.3842488208690265,
      "parent_quantity": 0.017335267914519163,
      "child_quantity": 0.017355501674804045
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1733148000000,
      "parent_pnl": -24.67948417207865,
      "child_pnl": -24.708290116651007,
      "parent_quantity": 0.020356729402888386,
      "child_quantity": 0.020380489819223083
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1733752800000,
      "parent_pnl": -24.483232103126024,
      "child_pnl": -24.511808981880762,
      "parent_quantity": 0.01802759820017585,
      "child_quantity": 0.01804864004979095
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1734580800000,
      "parent_pnl": -12.715854017297481,
      "child_pnl": -12.730695988201672,
      "parent_quantity": 0.004641685585197132,
      "child_quantity": 0.004647103370137741
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1734703200000,
      "parent_pnl": 5.899450966547023,
      "child_pnl": 5.906336817821904,
      "parent_quantity": 0.00397222136743422,
      "child_quantity": 0.003976857752365997
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1705968000000,
      "parent_pnl": -23.232750533840917,
      "child_pnl": -11.616375266920459,
      "parent_quantity": 0.02148038050568708,
      "child_quantity": 0.01074019025284354
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1714507200000,
      "parent_pnl": -2.997924273753827,
      "child_pnl": -3.0014234571184253,
      "parent_quantity": 0.005287613380822826,
      "child_quantity": 0.005293785094012043
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1718107200000,
      "parent_pnl": -12.093014955477651,
      "child_pnl": -12.1071299473507,
      "parent_quantity": 0.008499091265908764,
      "child_quantity": 0.008509011422675978
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1718121600000,
      "parent_pnl": -10.460491631084645,
      "child_pnl": -10.472701138383238,
      "parent_quantity": 0.007719747241608992,
      "child_quantity": 0.007728757746431693
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1719244800000,
      "parent_pnl": -12.16470942019879,
      "child_pnl": -12.178908093998194,
      "parent_quantity": 0.009282065007506798,
      "child_quantity": 0.009292899052832008
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1720166400000,
      "parent_pnl": -9.39844696983729,
      "child_pnl": -9.40941685642777,
      "parent_quantity": 0.0038938832324651768,
      "child_quantity": 0.0038984281809650513
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1722844800000,
      "parent_pnl": -12.6428138099841,
      "child_pnl": -12.65757052820842,
      "parent_quantity": 0.003184556581145128,
      "child_quantity": 0.003188273602121918
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1725652800000,
      "parent_pnl": -7.363272361036235,
      "child_pnl": -7.371866787646782,
      "parent_quantity": 0.004897586920017794,
      "child_quantity": 0.0049033033935215594
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1704744000000,
      "parent_pnl": -24.44130449432212,
      "child_pnl": -24.44130449432212,
      "parent_quantity": 0.014839399386279178,
      "child_quantity": 0.014839399386279178
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1706443200000,
      "parent_pnl": -8.984627863946411,
      "child_pnl": -8.99511474002727,
      "parent_quantity": 0.01100429655844806,
      "child_quantity": 0.011017140795973861
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1706572800000,
      "parent_pnl": -8.65320819694146,
      "child_pnl": -8.663308239306856,
      "parent_quantity": 0.010845624174653214,
      "child_quantity": 0.010858283209447022
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1707350400000,
      "parent_pnl": 83.55030985674665,
      "child_pnl": 83.6478299498716,
      "parent_quantity": 0.011509578643125825,
      "child_quantity": 0.011523012646937789
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1707364800000,
      "parent_pnl": 86.66953868515412,
      "child_pnl": 86.77069954856879,
      "parent_quantity": 0.011377438400110605,
      "child_quantity": 0.011390718169559746
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1707465600000,
      "parent_pnl": 51.64465746966568,
      "child_pnl": 51.704937219848325,
      "parent_quantity": 0.009652569703684142,
      "child_quantity": 0.009663836202851078
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1709020800000,
      "parent_pnl": 121.67375368280462,
      "child_pnl": 121.81577153779928,
      "parent_quantity": 0.013128123354963914,
      "child_quantity": 0.013143446527485064
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1709121600000,
      "parent_pnl": 15.936427107262114,
      "child_pnl": 15.955028137686085,
      "parent_quantity": 0.009775189824801524,
      "child_quantity": 0.009786599446425456
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1710158400000,
      "parent_pnl": -26.706634731189702,
      "child_pnl": -26.7378067700547,
      "parent_quantity": 0.011299349023800719,
      "child_quantity": 0.011312537647169569
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1710172800000,
      "parent_pnl": -26.15301151508313,
      "child_pnl": -26.183537363794166,
      "parent_quantity": 0.010670754105140935,
      "child_quantity": 0.01068320903123074
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1712577600000,
      "parent_pnl": -12.655609472959714,
      "child_pnl": -12.670381126308108,
      "parent_quantity": 0.005896592514368958,
      "child_quantity": 0.005903475029252583
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1713830400000,
      "parent_pnl": -3.6967669135715844,
      "child_pnl": -3.701081787499527,
      "parent_quantity": 0.006512037888268377,
      "child_quantity": 0.006519638752255422
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1715817600000,
      "parent_pnl": -2.289348921918747,
      "child_pnl": -2.2920210546785604,
      "parent_quantity": 0.0057892484707170126,
      "child_quantity": 0.005796005693412597
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1716249600000,
      "parent_pnl": -12.518354333133084,
      "child_pnl": -12.532965782000604,
      "parent_quantity": 0.005892223555323319,
      "child_quantity": 0.005899100970748982
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1720958400000,
      "parent_pnl": 23.53079286147284,
      "child_pnl": 23.558258051190126,
      "parent_quantity": 0.0073111769261573565,
      "child_quantity": 0.007319710546869403
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1721016000000,
      "parent_pnl": 4.5131846443831485,
      "child_pnl": 4.51845244276193,
      "parent_quantity": 0.006596690086561369,
      "child_quantity": 0.006604389756767985
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1721030400000,
      "parent_pnl": 3.237030021855257,
      "child_pnl": 3.2408082899397295,
      "parent_quantity": 0.0066458936785067976,
      "child_quantity": 0.006653650779246911
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1721088000000,
      "parent_pnl": -6.142938933348858,
      "child_pnl": -6.150108984278277,
      "parent_quantity": 0.0027978312547552293,
      "child_quantity": 0.0028010968891374324
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1724457600000,
      "parent_pnl": -14.191232637250131,
      "child_pnl": -14.207796673107268,
      "parent_quantity": 0.010062815616492207,
      "child_quantity": 0.010074560955530467
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1726761600000,
      "parent_pnl": 3.4703193469858844,
      "child_pnl": 3.474369910849391,
      "parent_quantity": 0.0019125771573273752,
      "child_quantity": 0.001914809521310352
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1726776000000,
      "parent_pnl": -4.04018176055318,
      "child_pnl": -4.044897468995268,
      "parent_quantity": 0.0048674538301649055,
      "child_quantity": 0.004873135132264354
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1728892800000,
      "parent_pnl": 58.310014902047,
      "child_pnl": 58.378074471103204,
      "parent_quantity": 0.016286380467839548,
      "child_quantity": 0.016305389964544163
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1728907200000,
      "parent_pnl": 47.66769422513019,
      "child_pnl": 47.723332055652364,
      "parent_quantity": 0.015827264911786165,
      "child_quantity": 0.01584573852787157
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1730188800000,
      "parent_pnl": -9.203114947132653,
      "child_pnl": -9.213856841785377,
      "parent_quantity": 0.014644205442735035,
      "child_quantity": 0.014661298189380313
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1730232000000,
      "parent_pnl": -25.758308229060745,
      "child_pnl": -25.788373379286337,
      "parent_quantity": 0.01199512280912699,
      "child_quantity": 0.012009123541085928
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1730246400000,
      "parent_pnl": -8.294381920763383,
      "child_pnl": -8.304063140362846,
      "parent_quantity": 0.011730399607573614,
      "child_quantity": 0.011744091354068441
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1731225600000,
      "parent_pnl": 70.10071047941739,
      "child_pnl": 70.1825321725481,
      "parent_quantity": 0.006278126808883815,
      "child_quantity": 0.006285454651378977
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1731240000000,
      "parent_pnl": 61.86611728588032,
      "child_pnl": 61.9383275449367,
      "parent_quantity": 0.0060422940168343734,
      "child_quantity": 0.0060493465948106865
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1731340800000,
      "parent_pnl": 30.480792309988612,
      "child_pnl": 30.516369553324832,
      "parent_quantity": 0.003962198879919009,
      "child_quantity": 0.003966823566582787
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1732176000000,
      "parent_pnl": -11.153704729779243,
      "child_pnl": -11.166723356829232,
      "parent_quantity": 0.008141559032990053,
      "child_quantity": 0.008151061877401292
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1732190400000,
      "parent_pnl": -19.431255138244364,
      "child_pnl": -19.453935339118125,
      "parent_quantity": 0.007978120098381907,
      "child_quantity": 0.007987432176533266
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1733371200000,
      "parent_pnl": -13.213569153012177,
      "child_pnl": -13.228992058044176,
      "parent_quantity": 0.003325625848998219,
      "child_quantity": 0.003329507526313948
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1734321600000,
      "parent_pnl": -10.106258118155978,
      "child_pnl": -10.118054163371339,
      "parent_quantity": 0.004657858199071901,
      "child_quantity": 0.0046632948607206156
    }
  ],
  "missing_entries": [],
  "new_entries": [],
  "downsized_winners": [],
  "parent_monthly": [
    {
      "month": "2024-01",
      "start_equity": 10000,
      "end_equity": 9982.236603962221,
      "equity_change": -17.763396037778875,
      "return_fraction": -0.0017763396037778767,
      "closed_trade_pnl": -17.763396037777905
    },
    {
      "month": "2024-02",
      "start_equity": 9982.236603962221,
      "end_equity": 10286.484593455973,
      "equity_change": 304.24798949375145,
      "return_fraction": 0.03047893989739614,
      "closed_trade_pnl": 221.86450601156645
    },
    {
      "month": "2024-03",
      "start_equity": 10286.484593455973,
      "end_equity": 10276.603823606118,
      "equity_change": -9.880769849854914,
      "return_fraction": -0.0009605584648559873,
      "closed_trade_pnl": 72.50271363233054
    },
    {
      "month": "2024-04",
      "start_equity": 10276.603823606118,
      "end_equity": 10252.506761795512,
      "equity_change": -24.097061810605737,
      "return_fraction": -0.002344846821403457,
      "closed_trade_pnl": -16.352376386531297
    },
    {
      "month": "2024-05",
      "start_equity": 10252.506761795512,
      "end_equity": 10278.961137281569,
      "equity_change": 26.45437548605696,
      "return_fraction": 0.0025802836419124286,
      "closed_trade_pnl": 18.709690061986535
    },
    {
      "month": "2024-06",
      "start_equity": 10278.961137281569,
      "end_equity": 10231.156879275704,
      "equity_change": -47.80425800586454,
      "return_fraction": -0.004650689633651783,
      "closed_trade_pnl": -47.804258005865236
    },
    {
      "month": "2024-07",
      "start_equity": 10231.156879275704,
      "end_equity": 10257.405949732587,
      "equity_change": 26.24907045688269,
      "return_fraction": 0.0025656014042803044,
      "closed_trade_pnl": 26.249070456882386
    },
    {
      "month": "2024-08",
      "start_equity": 10257.405949732587,
      "end_equity": 10230.571903285356,
      "equity_change": -26.83404644723123,
      "return_fraction": -0.002616065560701597,
      "closed_trade_pnl": -26.83404644723423
    },
    {
      "month": "2024-09",
      "start_equity": 10230.571903285356,
      "end_equity": 10343.933655495353,
      "equity_change": 113.36175220999758,
      "return_fraction": 0.011080685740901153,
      "closed_trade_pnl": 113.36175220999908
    },
    {
      "month": "2024-10",
      "start_equity": 10343.933655495353,
      "end_equity": 10414.031199484345,
      "equity_change": 70.09754398899167,
      "return_fraction": 0.006776681514362837,
      "closed_trade_pnl": 70.09754398899344
    },
    {
      "month": "2024-11",
      "start_equity": 10414.031199484345,
      "end_equity": 10545.893859691607,
      "equity_change": 131.8626602072618,
      "return_fraction": 0.012662018932091401,
      "closed_trade_pnl": 131.8626602072627
    },
    {
      "month": "2024-12",
      "start_equity": 10545.893859691607,
      "end_equity": 10414.865748595734,
      "equity_change": -131.0281110958731,
      "return_fraction": -0.012424561904295972,
      "closed_trade_pnl": -131.02811109587168
    }
  ],
  "child_monthly": [
    {
      "month": "2024-01",
      "start_equity": 10000,
      "end_equity": 9993.887891011695,
      "equity_change": -6.112108988305408,
      "return_fraction": -0.0006112108988305387,
      "closed_trade_pnl": -6.112108988301854
    },
    {
      "month": "2024-02",
      "start_equity": 9993.887891011695,
      "end_equity": 10298.490999383144,
      "equity_change": 304.6031083714497,
      "return_fraction": 0.03047893989739503,
      "closed_trade_pnl": 222.1234667182887
    },
    {
      "month": "2024-03",
      "start_equity": 10298.490999383144,
      "end_equity": 10288.598696678444,
      "equity_change": -9.892302704700342,
      "return_fraction": -0.0009605584648559873,
      "closed_trade_pnl": 72.58733894847059
    },
    {
      "month": "2024-04",
      "start_equity": 10288.598696678444,
      "end_equity": 10264.473508727842,
      "equity_change": -24.125187950601685,
      "return_fraction": -0.002344846821403457,
      "closed_trade_pnl": -16.371462913807633
    },
    {
      "month": "2024-05",
      "start_equity": 10264.473508727842,
      "end_equity": 10290.958761815258,
      "equity_change": 26.485253087415913,
      "return_fraction": 0.0025802836419126507,
      "closed_trade_pnl": 18.731528050622483
    },
    {
      "month": "2024-06",
      "start_equity": 10290.958761815258,
      "end_equity": 10243.09870658135,
      "equity_change": -47.8600552339085,
      "return_fraction": -0.00465068963365145,
      "closed_trade_pnl": -47.86005523391252
    },
    {
      "month": "2024-07",
      "start_equity": 10243.09870658135,
      "end_equity": 10269.378415007139,
      "equity_change": 26.279708425789067,
      "return_fraction": 0.0025656014042805264,
      "closed_trade_pnl": 26.27970842578741
    },
    {
      "month": "2024-08",
      "start_equity": 10269.378415007139,
      "end_equity": 10242.513047805824,
      "equity_change": -26.865367201315166,
      "return_fraction": -0.002616065560701819,
      "closed_trade_pnl": -26.86536720131569
    },
    {
      "month": "2024-09",
      "start_equity": 10242.513047805824,
      "end_equity": 10356.007116085642,
      "equity_change": 113.49406827981875,
      "return_fraction": 0.011080685740901375,
      "closed_trade_pnl": 113.49406827981707
    },
    {
      "month": "2024-10",
      "start_equity": 10356.007116085642,
      "end_equity": 10426.186478071828,
      "equity_change": 70.17936198618554,
      "return_fraction": 0.006776681514362615,
      "closed_trade_pnl": 70.17936198619005
    },
    {
      "month": "2024-11",
      "start_equity": 10426.186478071828,
      "end_equity": 10558.203048646697,
      "equity_change": 132.01657057486955,
      "return_fraction": 0.01266201893209229,
      "closed_trade_pnl": 132.01657057486227
    },
    {
      "month": "2024-12",
      "start_equity": 10558.203048646697,
      "end_equity": 10427.02200127066,
      "equity_change": -131.1810473760379,
      "return_fraction": -0.012424561904295972,
      "closed_trade_pnl": -131.18104737603585
    }
  ]
}
```

## 2024 成本2：完整指標及取捨

```json
{
  "year": 2024,
  "cost": 2,
  "checks": "passed",
  "metrics": {
    "average_loss": -13.74337489373319,
    "average_win": 33.393711595121026,
    "cagr": 0.025901180064519913,
    "exposure": 0.2330108138873079,
    "fees": 153.58228957122265,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.024708957743533322,
    "maximum_margin_ratio": 0.023278162960788665,
    "net_funding": -34.12573828587469,
    "number_of_trades": 60,
    "profit_factor": 1.5104188974128465,
    "sharpe_ratio": 0.9747490034363662,
    "slippage": 76.79166883579968,
    "sortino_ratio": 1.4232015205404773,
    "total_return": 0.02595504956196648,
    "win_rate": 0.38333333333333336
  },
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
    "swing/1": {
      "count": 34,
      "pnl": 316.72926689199016
    },
    "swing/-1": {
      "count": 8,
      "pnl": -79.94598503829768
    },
    "intraday/1": {
      "count": 12,
      "pnl": 102.11432691417029
    },
    "intraday/-1": {
      "count": 6,
      "pnl": -79.34711314820717
    }
  },
  "common_entries": [
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1711404000000,
      "parent_pnl": -13.726610996773177,
      "child_pnl": -13.742743623287913,
      "parent_quantity": 0.014078877189329897,
      "child_quantity": 0.014095423827644022
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1717426800000,
      "parent_pnl": -14.264036425357835,
      "child_pnl": -14.280800677823132,
      "parent_quantity": 0.01251532888377837,
      "child_quantity": 0.012530037913315122
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1725634800000,
      "parent_pnl": 1.1156065805272652,
      "child_pnl": 1.1169177318599053,
      "parent_quantity": 0.004727079993663967,
      "child_quantity": 0.0047326356414535845
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1735070400000,
      "parent_pnl": -19.790708824966547,
      "child_pnl": -19.813968471066406,
      "parent_quantity": 0.009980161952253415,
      "child_quantity": 0.009991891448002239
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1735164000000,
      "parent_pnl": -24.129172516890804,
      "child_pnl": -24.157531077384473,
      "parent_quantity": 0.015970096153024412,
      "child_quantity": 0.015988865505248494
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1735596000000,
      "parent_pnl": -8.459045274443431,
      "child_pnl": -8.468987030505145,
      "parent_quantity": 0.0035126547087424164,
      "child_quantity": 0.00351678306544348
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1706486400000,
      "parent_pnl": 34.73928882418194,
      "child_pnl": 34.7801172538737,
      "parent_quantity": 0.034807462217861844,
      "child_quantity": 0.034848370770454926
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1715259600000,
      "parent_pnl": 21.161194116800104,
      "child_pnl": 21.18606446836557,
      "parent_quantity": 0.018768336255215727,
      "child_quantity": 0.018790394326153963
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1716501600000,
      "parent_pnl": 4.874045013199431,
      "child_pnl": 4.879773386199321,
      "parent_quantity": 0.01093317581555499,
      "child_quantity": 0.010946025370488374
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1721919600000,
      "parent_pnl": 27.188152501257704,
      "child_pnl": 27.22010622312191,
      "parent_quantity": 0.016438554950429576,
      "child_quantity": 0.01645787487342586
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1722376800000,
      "parent_pnl": -24.485305085282153,
      "child_pnl": -24.514082201653675,
      "parent_quantity": 0.017312948898133698,
      "child_quantity": 0.017333296479813423
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1726682400000,
      "parent_pnl": 66.72179358780221,
      "child_pnl": 66.800210450974,
      "parent_quantity": 0.020111620500920992,
      "child_quantity": 0.02013525730844938
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1727319600000,
      "parent_pnl": 25.614865291868817,
      "child_pnl": 25.644969959006033,
      "parent_quantity": 0.022610818567899295,
      "child_quantity": 0.02263739263568885
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1729713600000,
      "parent_pnl": 3.4051600878523867,
      "child_pnl": 3.40916210815683,
      "parent_quantity": 0.01512621538433009,
      "child_quantity": 0.015143992939433429
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1733148000000,
      "parent_pnl": -24.591265041118646,
      "child_pnl": -24.62016669022395,
      "parent_quantity": 0.01641387573701237,
      "child_quantity": 0.016433166654995484
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1733752800000,
      "parent_pnl": -24.394132137703203,
      "child_pnl": -24.422802100232303,
      "parent_quantity": 0.014751282986373812,
      "child_quantity": 0.01476861989051486
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1734580800000,
      "parent_pnl": -12.550530034947299,
      "child_pnl": -12.565280435731847,
      "parent_quantity": 0.004129339509934575,
      "child_quantity": 0.004134192644629077
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1734703200000,
      "parent_pnl": 4.31118763495525,
      "child_pnl": 4.31625449231473,
      "parent_quantity": 0.0036017948760419466,
      "child_quantity": 0.003606027997497168
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1705968000000,
      "parent_pnl": -23.393085151960275,
      "child_pnl": -11.696542575980137,
      "parent_quantity": 0.019465287635838643,
      "child_quantity": 0.009732643817919322
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1714507200000,
      "parent_pnl": -3.6468053624761754,
      "child_pnl": -3.651091383905543,
      "parent_quantity": 0.004892297297705201,
      "child_quantity": 0.004898047122270164
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1718107200000,
      "parent_pnl": -12.09592941644773,
      "child_pnl": -12.11014553371586,
      "parent_quantity": 0.007441446503874502,
      "child_quantity": 0.007450192295330572
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1718121600000,
      "parent_pnl": -10.638506963528641,
      "child_pnl": -10.651010199728557,
      "parent_quantity": 0.0068390126975203126,
      "child_quantity": 0.006847050459907879
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1719244800000,
      "parent_pnl": -12.154645016306759,
      "child_pnl": -12.168930140909866,
      "parent_quantity": 0.008131644118232502,
      "child_quantity": 0.008141201085902166
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1720166400000,
      "parent_pnl": -9.491831275635828,
      "child_pnl": -9.50298684556833,
      "parent_quantity": 0.0036787370444484042,
      "child_quantity": 0.0036830605945801865
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1722844800000,
      "parent_pnl": -12.53527227784159,
      "child_pnl": -12.550004746472535,
      "parent_quantity": 0.0030324607628189676,
      "child_quantity": 0.003036024756649542
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1725652800000,
      "parent_pnl": -7.606334031365569,
      "child_pnl": -7.615273612016853,
      "parent_quantity": 0.004565672221942993,
      "child_quantity": 0.004571038170228603
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1704744000000,
      "parent_pnl": -24.483508220879553,
      "child_pnl": -24.483508220879553,
      "parent_quantity": 0.013709875954589435,
      "child_quantity": 0.013709875954589435
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1706443200000,
      "parent_pnl": -9.334738832505387,
      "child_pnl": -9.345709774658024,
      "parent_quantity": 0.009901005854393206,
      "child_quantity": 0.009912642319476002
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1706572800000,
      "parent_pnl": -9.030433510775039,
      "child_pnl": -9.041046808633459,
      "parent_quantity": 0.009744404352365453,
      "child_quantity": 0.00975585676666219
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1707350400000,
      "parent_pnl": 72.92304961590104,
      "child_pnl": 73.0087546980983,
      "parent_quantity": 0.01024922027144991,
      "child_quantity": 0.010261265986356911
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1707364800000,
      "parent_pnl": 75.7598724560327,
      "child_pnl": 75.84891160250692,
      "parent_quantity": 0.010138729823847788,
      "child_quantity": 0.010150645681419644
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1707465600000,
      "parent_pnl": 45.345409679647055,
      "child_pnl": 45.39870328275788,
      "parent_quantity": 0.008714565767178231,
      "child_quantity": 0.008724807831646504
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1709020800000,
      "parent_pnl": 109.44386023157679,
      "child_pnl": 109.5724875323622,
      "parent_quantity": 0.012047046103375814,
      "child_quantity": 0.012061204769009825
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1709121600000,
      "parent_pnl": 13.23040402620097,
      "child_pnl": 13.245953470039929,
      "parent_quantity": 0.00912721727678401,
      "child_quantity": 0.00913794432277371
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1710158400000,
      "parent_pnl": -26.488540621564493,
      "child_pnl": -26.519672102806915,
      "parent_quantity": 0.010285906391651927,
      "child_quantity": 0.010297995223062758
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1710172800000,
      "parent_pnl": -25.982911359901934,
      "child_pnl": -26.013448584627927,
      "parent_quantity": 0.00975376746516474,
      "child_quantity": 0.009765230883751022
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1712577600000,
      "parent_pnl": -12.601436630416687,
      "child_pnl": -12.616246860760901,
      "parent_quantity": 0.00533768827293538,
      "child_quantity": 0.0053439615570970425
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1713830400000,
      "parent_pnl": -4.5162904919996265,
      "child_pnl": -4.521598402871188,
      "parent_quantity": 0.005884690262281624,
      "child_quantity": 0.005891606427544747
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1715817600000,
      "parent_pnl": -3.138492631937733,
      "child_pnl": -3.1421812430204126,
      "parent_quantity": 0.005286184252071902,
      "child_quantity": 0.005292397004531109
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1716249600000,
      "parent_pnl": -12.465674977878566,
      "child_pnl": -12.480325650118022,
      "parent_quantity": 0.005336082799201997,
      "child_quantity": 0.0053423541964807185
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1720958400000,
      "parent_pnl": 19.98442222615185,
      "child_pnl": 20.00790953995153,
      "parent_quantity": 0.00658876700369686,
      "child_quantity": 0.006596510657049335
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1721016000000,
      "parent_pnl": 2.9589730841524253,
      "child_pnl": 2.962450709302948,
      "parent_quantity": 0.005977914375289884,
      "child_quantity": 0.005984940105091387
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1721030400000,
      "parent_pnl": 1.7905007441532292,
      "child_pnl": 1.7926050858430018,
      "parent_quantity": 0.006016489367705265,
      "child_quantity": 0.006023560433966409
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1721088000000,
      "parent_pnl": -12.414109806817105,
      "child_pnl": -12.428699875485439,
      "parent_quantity": 0.005201489171831986,
      "child_quantity": 0.00520760238376386
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1721102400000,
      "parent_pnl": -0.574554870784208,
      "child_pnl": -0.5752301342665925,
      "parent_quantity": 0.00023899915385404614,
      "child_quantity": 0.0002392800450432518
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1724457600000,
      "parent_pnl": -14.858348284763466,
      "child_pnl": -14.875811020726522,
      "parent_quantity": 0.009283520345066062,
      "child_quantity": 0.009294431091098298
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1726761600000,
      "parent_pnl": 7.386633345739979,
      "child_pnl": 7.3953147163271,
      "parent_quantity": 0.004554077181895313,
      "child_quantity": 0.0045594295027494664
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1726776000000,
      "parent_pnl": -4.583281109513181,
      "child_pnl": -4.588667753191601,
      "parent_quantity": 0.004498611674322115,
      "child_quantity": 0.004503898807613341
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1728892800000,
      "parent_pnl": 48.56179968086585,
      "child_pnl": 48.618873446365605,
      "parent_quantity": 0.014364758271475288,
      "child_quantity": 0.014381640900423034
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1728907200000,
      "parent_pnl": 39.35166892975753,
      "child_pnl": 39.397918202627984,
      "parent_quantity": 0.013994067458032418,
      "child_quantity": 0.014010514421072016
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1730188800000,
      "parent_pnl": -10.866280069224013,
      "child_pnl": -10.87905100285088,
      "parent_quantity": 0.012922015892963669,
      "child_quantity": 0.01293720289405724
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1730232000000,
      "parent_pnl": -25.442356721285268,
      "child_pnl": -25.472258642359325,
      "parent_quantity": 0.010770799702594865,
      "child_quantity": 0.01078345841995111
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1730246400000,
      "parent_pnl": -9.754548984971754,
      "child_pnl": -9.766013322063516,
      "parent_quantity": 0.01055037222137567,
      "child_quantity": 0.010562771874478624
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1731225600000,
      "parent_pnl": 60.71301173080756,
      "child_pnl": 60.78436658620994,
      "parent_quantity": 0.005564031549531789,
      "child_quantity": 0.005570570850669269
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1731240000000,
      "parent_pnl": 53.590010006351335,
      "child_pnl": 53.65299333242929,
      "parent_quantity": 0.005368203648208049,
      "child_quantity": 0.005374512796513636
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1731340800000,
      "parent_pnl": 26.982835991838435,
      "child_pnl": 27.014548409088977,
      "parent_quantity": 0.0036325218207483388,
      "child_quantity": 0.0036367910550010357
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1732176000000,
      "parent_pnl": -12.221613102562396,
      "child_pnl": -12.235976933491818,
      "parent_quantity": 0.00736517945290727,
      "child_quantity": 0.007373835609139561
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1732190400000,
      "parent_pnl": -19.69167689132819,
      "child_pnl": -19.71482014706785,
      "parent_quantity": 0.0072221381073730665,
      "child_quantity": 0.007230626149814983
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1733371200000,
      "parent_pnl": -13.00126417107118,
      "child_pnl": -13.016544311168458,
      "parent_quantity": 0.0030396699394976494,
      "child_quantity": 0.003043242406137344
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1734321600000,
      "parent_pnl": -10.243673734705899,
      "child_pnl": -10.255712930873093,
      "parent_quantity": 0.004129285606626469,
      "child_quantity": 0.00413413867796943
    }
  ],
  "missing_entries": [],
  "new_entries": [],
  "downsized_winners": [],
  "parent_monthly": [
    {
      "month": "2024-01",
      "start_equity": 10000,
      "end_equity": 9968.497523108066,
      "equity_change": -31.50247689193384,
      "return_fraction": -0.003150247689193364,
      "closed_trade_pnl": -31.502476891938315
    },
    {
      "month": "2024-02",
      "start_equity": 9968.497523108066,
      "end_equity": 10236.60928945677,
      "equity_change": 268.1117663487039,
      "return_fraction": 0.02689590539870146,
      "closed_trade_pnl": 194.02833175158077
    },
    {
      "month": "2024-03",
      "start_equity": 10236.60928945677,
      "end_equity": 10219.002056139187,
      "equity_change": -17.60723331758345,
      "return_fraction": -0.0017200259206647805,
      "closed_trade_pnl": 56.47620127953816
    },
    {
      "month": "2024-04",
      "start_equity": 10219.002056139187,
      "end_equity": 10194.284097475651,
      "equity_change": -24.717958663535683,
      "return_fraction": -0.0024188231421957695,
      "closed_trade_pnl": -17.117727122416312
    },
    {
      "month": "2024-05",
      "start_equity": 10194.284097475651,
      "end_equity": 10208.668595174482,
      "equity_change": 14.384497698831183,
      "return_fraction": 0.001411035592228993,
      "closed_trade_pnl": 6.7842661577070595
    },
    {
      "month": "2024-06",
      "start_equity": 10208.668595174482,
      "end_equity": 10159.515477352837,
      "equity_change": -49.15311782164463,
      "return_fraction": -0.004814841167914752,
      "closed_trade_pnl": -49.15311782164097
    },
    {
      "month": "2024-07",
      "start_equity": 10159.515477352837,
      "end_equity": 10164.471724870027,
      "equity_change": 4.956247517189695,
      "return_fraction": 0.00048784290237446903,
      "closed_trade_pnl": 4.956247517195912
    },
    {
      "month": "2024-08",
      "start_equity": 10164.471724870027,
      "end_equity": 10137.078104307422,
      "equity_change": -27.393620562605065,
      "return_fraction": -0.0026950363289003354,
      "closed_trade_pnl": -27.393620562605058
    },
    {
      "month": "2024-09",
      "start_equity": 10137.078104307422,
      "end_equity": 10225.727387972473,
      "equity_change": 88.64928366505046,
      "return_fraction": 0.00874505283996796,
      "closed_trade_pnl": 88.64928366505953
    },
    {
      "month": "2024-10",
      "start_equity": 10225.727387972473,
      "end_equity": 10270.982830895464,
      "equity_change": 45.25544292299128,
      "return_fraction": 0.004425645355676133,
      "closed_trade_pnl": 45.25544292299474
    },
    {
      "month": "2024-11",
      "start_equity": 10270.982830895464,
      "end_equity": 10380.355398630572,
      "equity_change": 109.37256773510853,
      "return_fraction": 0.01064869541073632,
      "closed_trade_pnl": 109.37256773510676
    },
    {
      "month": "2024-12",
      "start_equity": 10380.355398630572,
      "end_equity": 10247.506794529685,
      "equity_change": -132.84860410088731,
      "return_fraction": -0.012798078582012096,
      "closed_trade_pnl": -132.84860410089175
    }
  ],
  "child_monthly": [
    {
      "month": "2024-01",
      "start_equity": 10000,
      "end_equity": 9980.21330987372,
      "equity_change": -19.78669012628052,
      "return_fraction": -0.001978669012627998,
      "closed_trade_pnl": -19.786690126277477
    },
    {
      "month": "2024-02",
      "start_equity": 9980.21330987372,
      "end_equity": 10248.64018291495,
      "equity_change": 268.4268730412314,
      "return_fraction": 0.026895905398702125,
      "closed_trade_pnl": 194.2563695833631
    },
    {
      "month": "2024-03",
      "start_equity": 10248.64018291495,
      "end_equity": 10231.012256148771,
      "equity_change": -17.62792676617937,
      "return_fraction": -0.0017200259206646695,
      "closed_trade_pnl": 56.54257669167938
    },
    {
      "month": "2024-04",
      "start_equity": 10231.012256148771,
      "end_equity": 10206.26524693551,
      "equity_change": -24.747009213260753,
      "return_fraction": -0.0024188231421957695,
      "closed_trade_pnl": -17.137845263632087
    },
    {
      "month": "2024-05",
      "start_equity": 10206.26524693551,
      "end_equity": 10220.666650462663,
      "equity_change": 14.40140352715207,
      "return_fraction": 0.001411035592228549,
      "closed_trade_pnl": 6.792239577520912
    },
    {
      "month": "2024-06",
      "start_equity": 10220.666650462663,
      "end_equity": 10171.455763910486,
      "equity_change": -49.21088655217682,
      "return_fraction": -0.004814841167914308,
      "closed_trade_pnl": -49.21088655217741
    },
    {
      "month": "2024-07",
      "start_equity": 10171.455763910486,
      "end_equity": 10176.417836411734,
      "equity_change": 4.962072501248258,
      "return_fraction": 0.0004878429023753572,
      "closed_trade_pnl": 4.962072501245352
    },
    {
      "month": "2024-08",
      "start_equity": 10176.417836411734,
      "end_equity": 10148.992020644537,
      "equity_change": -27.42581576719749,
      "return_fraction": -0.0026950363289002244,
      "closed_trade_pnl": -27.425815767199055
    },
    {
      "month": "2024-09",
      "start_equity": 10148.992020644537,
      "end_equity": 10237.745492137494,
      "equity_change": 88.75347149295703,
      "return_fraction": 0.008745052839968626,
      "closed_trade_pnl": 88.7534714929586
    },
    {
      "month": "2024-10",
      "start_equity": 10237.745492137494,
      "end_equity": 10283.054122927366,
      "equity_change": 45.30863078987204,
      "return_fraction": 0.004425645355676133,
      "closed_trade_pnl": 45.30863078987671
    },
    {
      "month": "2024-11",
      "start_equity": 10283.054122927366,
      "end_equity": 10392.555234174533,
      "equity_change": 109.5011112471675,
      "return_fraction": 0.010648695410736098,
      "closed_trade_pnl": 109.50111124716852
    },
    {
      "month": "2024-12",
      "start_equity": 10392.555234174533,
      "end_equity": 10259.550495619664,
      "equity_change": -133.00473855486962,
      "return_fraction": -0.012798078582012318,
      "closed_trade_pnl": -133.00473855487095
    }
  ]
}
```

## 2025 成本1：完整指標及取捨

```json
{
  "year": 2025,
  "cost": 1,
  "checks": "passed",
  "metrics": {
    "average_loss": -11.249139194154301,
    "average_win": 22.034110884730676,
    "cagr": -0.0031338877625407546,
    "exposure": 0.19803675379522886,
    "fees": 79.5105031782609,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.02363833115117908,
    "maximum_margin_ratio": 0.021957946303772773,
    "net_funding": -6.872312359763234,
    "number_of_trades": 59,
    "profit_factor": 0.9304003168247674,
    "sharpe_ratio": -0.1335008711959032,
    "slippage": 39.75527529428344,
    "sortino_ratio": -0.19282606381357484,
    "total_return": -0.003131746095627941,
    "win_rate": 0.3220338983050847
  },
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
    "swing/1": {
      "count": 24,
      "pnl": -31.90024449352619
    },
    "intraday/1": {
      "count": 5,
      "pnl": -40.88766469714743
    },
    "swing/-1": {
      "count": 19,
      "pnl": -33.54407867460787
    },
    "intraday/-1": {
      "count": 11,
      "pnl": 75.0145269089923
    }
  },
  "common_entries": [
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1741705200000,
      "parent_pnl": -24.077730112936617,
      "child_pnl": -24.115570155696652,
      "parent_quantity": 0.008806864113167555,
      "child_quantity": 0.008820704791381861
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1741748400000,
      "parent_pnl": -11.748553720227461,
      "child_pnl": -11.767017494555718,
      "parent_quantity": 0.0073722872210600235,
      "child_quantity": 0.007383873349086863
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1743555600000,
      "parent_pnl": -11.269241745273048,
      "child_pnl": -11.286952243210928,
      "parent_quantity": 0.012113439271780622,
      "child_quantity": 0.012132476492393404
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1743764400000,
      "parent_pnl": -6.460730423237053,
      "child_pnl": -6.470883968207013,
      "parent_quantity": 0.004955414821266194,
      "child_quantity": 0.004963202644613777
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1744412400000,
      "parent_pnl": -11.398393262591888,
      "child_pnl": -11.41630673227648,
      "parent_quantity": 0.009801234222322234,
      "child_quantity": 0.009816637631212273
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1750118400000,
      "parent_pnl": 9.277350996984723,
      "child_pnl": 9.29193108226598,
      "parent_quantity": 0.004797765681750324,
      "child_quantity": 0.004805305747101105
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1760277600000,
      "parent_pnl": -22.673447395401787,
      "child_pnl": -22.709080497647527,
      "parent_quantity": 0.017596164328765533,
      "child_quantity": 0.01762381808215051
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1760500800000,
      "parent_pnl": 2.2066511184558038,
      "child_pnl": 2.2101190438909337,
      "parent_quantity": 0.005996308501496797,
      "child_quantity": 0.0060057321709637585
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1760623200000,
      "parent_pnl": 71.62902351376209,
      "child_pnl": 71.74159414645493,
      "parent_quantity": 0.015254437594856844,
      "child_quantity": 0.015278411140874772
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1761930000000,
      "parent_pnl": -16.361301685927856,
      "child_pnl": -16.387014755743877,
      "parent_quantity": 0.008624390292515325,
      "child_quantity": 0.008637944198797903
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1763622000000,
      "parent_pnl": 95.77319339295813,
      "child_pnl": 95.92370848371864,
      "parent_quantity": 0.01556883772820485,
      "child_quantity": 0.015593305378709947
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1736438400000,
      "parent_pnl": -24.106420492644705,
      "child_pnl": -24.106420492644705,
      "parent_quantity": 0.00883985824278707,
      "child_quantity": 0.00883985824278707
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1743022800000,
      "parent_pnl": -4.287764940112167,
      "child_pnl": -4.294503499266942,
      "parent_quantity": 0.006936265624575903,
      "child_quantity": 0.006947166510440047
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1744772400000,
      "parent_pnl": 1.1320094871056758,
      "child_pnl": 1.1337885288673337,
      "parent_quantity": 0.01084844774642143,
      "child_quantity": 0.010865496933561541
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1747324800000,
      "parent_pnl": 6.376590571869566,
      "child_pnl": 6.386611884458875,
      "parent_quantity": 0.010551681630271223,
      "child_quantity": 0.010568264426166304
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1757098800000,
      "parent_pnl": -19.975747663190848,
      "child_pnl": -20.007141118561993,
      "parent_quantity": 0.017110606612288866,
      "child_quantity": 0.017137497273610445
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1740427200000,
      "parent_pnl": 39.00638558273115,
      "child_pnl": 39.00638558273115,
      "parent_quantity": 0.006185193010384345,
      "child_quantity": 0.006185193010384345
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1740484800000,
      "parent_pnl": 5.551410085973689,
      "child_pnl": 5.551410085973689,
      "parent_quantity": 0.003537799036787415,
      "child_quantity": 0.003537799036787415
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1741564800000,
      "parent_pnl": -24.31246822450156,
      "child_pnl": -12.15623411225078,
      "parent_quantity": 0.007434637550804175,
      "child_quantity": 0.0037173187754020874
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1741651200000,
      "parent_pnl": -6.929166396449063,
      "child_pnl": -3.4688186272453807,
      "parent_quantity": 0.005994180827182444,
      "child_quantity": 0.0030007543359130582
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1743998400000,
      "parent_pnl": -11.929801796030075,
      "child_pnl": -11.948550415935806,
      "parent_quantity": 0.004547671041720984,
      "child_quantity": 0.0045548180637147535
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1750622400000,
      "parent_pnl": -9.23009737794027,
      "child_pnl": -9.244603200450207,
      "parent_quantity": 0.003885255230435265,
      "child_quantity": 0.003891361213987854
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1754092800000,
      "parent_pnl": -3.732469972169586,
      "child_pnl": -3.7383358416965295,
      "parent_quantity": 0.0036974110500173755,
      "child_quantity": 0.003703221821696344
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1755504000000,
      "parent_pnl": -11.569182844823825,
      "child_pnl": -11.587364723742365,
      "parent_quantity": 0.006289895746567311,
      "child_quantity": 0.006299780811433884
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1755633600000,
      "parent_pnl": -11.61964620166139,
      "child_pnl": -11.637907387706134,
      "parent_quantity": 0.004242416754396671,
      "child_quantity": 0.0042490840453181696
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1755648000000,
      "parent_pnl": -4.771377023485478,
      "child_pnl": -4.7788756169885245,
      "parent_quantity": 0.004180173515380967,
      "child_quantity": 0.0041867429861668125
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1756180800000,
      "parent_pnl": -5.526440930355314,
      "child_pnl": -5.535126166053804,
      "parent_quantity": 0.0035782455104033384,
      "child_quantity": 0.0035838690040833686
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1758844800000,
      "parent_pnl": -5.874392902348753,
      "child_pnl": -5.883624971882363,
      "parent_quantity": 0.004372575223383774,
      "child_quantity": 0.004379447068555567
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1760155200000,
      "parent_pnl": -4.802076962171988,
      "child_pnl": -4.8096238030383525,
      "parent_quantity": 0.002027900973285098,
      "child_quantity": 0.0020310879788367968
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1760644800000,
      "parent_pnl": 0.23910359543670506,
      "child_pnl": 0.23947936550443844,
      "parent_quantity": 0.002998884389945935,
      "child_quantity": 0.003003597372150475
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1760659200000,
      "parent_pnl": -4.240689523433918,
      "child_pnl": -4.247354099876387,
      "parent_quantity": 0.0032158457248642916,
      "child_quantity": 0.0032208996788361892
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1762286400000,
      "parent_pnl": -10.267148268730935,
      "child_pnl": -10.28328389811502,
      "parent_quantity": 0.0029696636861086456,
      "child_quantity": 0.0029743307456835386
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1763121600000,
      "parent_pnl": 37.64719579198225,
      "child_pnl": 37.706361315139205,
      "parent_quantity": 0.002741079528435346,
      "child_quantity": 0.002745387350064633
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1763712000000,
      "parent_pnl": -6.453766433508532,
      "child_pnl": -6.463909034022028,
      "parent_quantity": 0.0025885867594593426,
      "child_quantity": 0.002592654926732859
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1765828800000,
      "parent_pnl": -20.49599518471932,
      "child_pnl": -10.26410312495267,
      "parent_quantity": 0.009827619174016236,
      "child_quantity": 0.004921532024464428
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1736150400000,
      "parent_pnl": -24.19673620982446,
      "child_pnl": -24.19673620982446,
      "parent_quantity": 0.013404767030289923,
      "child_quantity": 0.013404767030289923
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1737100800000,
      "parent_pnl": -3.5040986552370317,
      "child_pnl": -3.5040986552370317,
      "parent_quantity": 0.007418427707898628,
      "child_quantity": 0.007418427707898628
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1737129600000,
      "parent_pnl": -24.632084152616724,
      "child_pnl": -24.632084152616724,
      "parent_quantity": 0.007063961907030286,
      "child_quantity": 0.007063961907030286
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1742428800000,
      "parent_pnl": -10.71696640524471,
      "child_pnl": -10.733808959137049,
      "parent_quantity": 0.004411819584644216,
      "child_quantity": 0.004418753105410062
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1742803200000,
      "parent_pnl": -11.62902482476392,
      "child_pnl": -11.647300750051,
      "parent_quantity": 0.00810054634422091,
      "child_quantity": 0.008113276988621656
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1742817600000,
      "parent_pnl": -11.682345205918107,
      "child_pnl": -11.700704928369346,
      "parent_quantity": 0.007561358866483808,
      "child_quantity": 0.0075732421354418695
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1745222400000,
      "parent_pnl": 49.917980673254874,
      "child_pnl": 49.99643069800017,
      "parent_quantity": 0.0071614036544734305,
      "child_quantity": 0.007172658362422894
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1745352000000,
      "parent_pnl": 15.798249742279923,
      "child_pnl": 15.823077931771936,
      "parent_quantity": 0.004355725471727993,
      "child_quantity": 0.004362570836192502
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1745611200000,
      "parent_pnl": -0.9153867727728475,
      "child_pnl": -0.9168253749359789,
      "parent_quantity": 0.0009925775767821012,
      "child_quantity": 0.0009941374903525246
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1746705600000,
      "parent_pnl": 25.70907622174944,
      "child_pnl": 25.749480052965612,
      "parent_quantity": 0.009483771600266477,
      "child_quantity": 0.00949867609172797
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1746734400000,
      "parent_pnl": 6.894988043735175,
      "child_pnl": 6.905824058641105,
      "parent_quantity": 0.008313307374608935,
      "child_quantity": 0.00832637238966878
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1749513600000,
      "parent_pnl": -23.721412714377973,
      "child_pnl": -23.758692776378417,
      "parent_quantity": 0.011020564364125107,
      "child_quantity": 0.01103788404603956
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1752192000000,
      "parent_pnl": 2.8748871814640267,
      "child_pnl": 2.8794052923227573,
      "parent_quantity": 0.003945058505770733,
      "child_quantity": 0.003951258474864537
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1752206400000,
      "parent_pnl": -0.4635765087696627,
      "child_pnl": -0.46430505563982455,
      "parent_quantity": 0.0038229403221682725,
      "child_quantity": 0.0038289483729513547
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1752480000000,
      "parent_pnl": -11.863487794248122,
      "child_pnl": -11.882132196495004,
      "parent_quantity": 0.004671708562668527,
      "child_quantity": 0.00467905051936231
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1754884800000,
      "parent_pnl": -11.845032606111358,
      "child_pnl": -11.86364800458152,
      "parent_quantity": 0.004718022292019926,
      "child_quantity": 0.004725437034374602
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1755129600000,
      "parent_pnl": -7.859581857654315,
      "child_pnl": -7.871933807450856,
      "parent_quantity": 0.004006857849420032,
      "child_quantity": 0.004013154941033082
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1755144000000,
      "parent_pnl": -8.540795024994331,
      "child_pnl": -8.554217554752517,
      "parent_quantity": 0.0042062067357754255,
      "child_quantity": 0.004212817119810496
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1759334400000,
      "parent_pnl": 17.722039544354846,
      "child_pnl": 17.74989112052119,
      "parent_quantity": 0.004584577770995251,
      "child_quantity": 0.004591782794810928
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1759348800000,
      "parent_pnl": 16.845843382321753,
      "child_pnl": 16.87231794744587,
      "parent_quantity": 0.004366395854120715,
      "child_quantity": 0.004373257987928684
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1759377600000,
      "parent_pnl": 11.463626523579228,
      "child_pnl": 11.481642512453702,
      "parent_quantity": 0.004509139644324709,
      "child_quantity": 0.004516226111203101
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1759435200000,
      "parent_pnl": 1.9955115736874052,
      "child_pnl": 1.9986476767553552,
      "parent_quantity": 0.004230862180686415,
      "child_quantity": 0.0042375113126883945
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1761494400000,
      "parent_pnl": -13.441441926468933,
      "child_pnl": -13.46256620748996,
      "parent_quantity": 0.011155951045628186,
      "child_quantity": 0.011173483498339274
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1761537600000,
      "parent_pnl": -16.1425378861106,
      "child_pnl": -16.167907151444197,
      "parent_quantity": 0.01125821704219207,
      "child_quantity": 0.01127591021394373
    }
  ],
  "missing_entries": [],
  "new_entries": [],
  "downsized_winners": [],
  "parent_monthly": [
    {
      "month": "2025-01",
      "start_equity": 10000,
      "end_equity": 9923.56066048968,
      "equity_change": -76.43933951031977,
      "return_fraction": -0.0076439339510320226,
      "closed_trade_pnl": -76.43933951032292
    },
    {
      "month": "2025-02",
      "start_equity": 9923.56066048968,
      "end_equity": 9999.546724170432,
      "equity_change": 75.98606368075161,
      "return_fraction": 0.007657137017692328,
      "closed_trade_pnl": 0.0
    },
    {
      "month": "2025-03",
      "start_equity": 9999.546724170432,
      "end_equity": 9862.73443632824,
      "equity_change": -136.81228784219275,
      "return_fraction": -0.01368184894936253,
      "closed_trade_pnl": -60.82622416144876
    },
    {
      "month": "2025-04",
      "start_equity": 9862.73443632824,
      "end_equity": 9887.609122230975,
      "equity_change": 24.87468590273602,
      "return_fraction": 0.0025220881757814784,
      "closed_trade_pnl": 24.874685902735557
    },
    {
      "month": "2025-05",
      "start_equity": 9887.609122230975,
      "end_equity": 9926.589777068331,
      "equity_change": 38.98065483735627,
      "return_fraction": 0.003942374173116603,
      "closed_trade_pnl": 38.98065483735418
    },
    {
      "month": "2025-06",
      "start_equity": 9926.589777068331,
      "end_equity": 9902.915617972998,
      "equity_change": -23.67415909533338,
      "return_fraction": -0.0023849236874906588,
      "closed_trade_pnl": -23.674159095333522
    },
    {
      "month": "2025-07",
      "start_equity": 9902.915617972998,
      "end_equity": 9893.463440851445,
      "equity_change": -9.452177121553177,
      "return_fraction": -0.0009544842636443063,
      "closed_trade_pnl": -9.452177121553758
    },
    {
      "month": "2025-08",
      "start_equity": 9893.463440851445,
      "end_equity": 9827.998914390188,
      "equity_change": -65.46452646125726,
      "return_fraction": -0.006616947326145151,
      "closed_trade_pnl": -65.46452646125559
    },
    {
      "month": "2025-09",
      "start_equity": 9827.998914390188,
      "end_equity": 9802.14877382465,
      "equity_change": -25.850140565537004,
      "return_fraction": -0.00263025472333811,
      "closed_trade_pnl": -25.8501405655396
    },
    {
      "month": "2025-10",
      "start_equity": 9802.14877382465,
      "end_equity": 9855.123186386909,
      "equity_change": 52.974412562258294,
      "return_fraction": 0.005404367326449888,
      "closed_trade_pnl": 60.8016055580106
    },
    {
      "month": "2025-11",
      "start_equity": 9855.123186386909,
      "end_equity": 9963.288552179432,
      "equity_change": 108.16536579252352,
      "return_fraction": 0.01097554680411661,
      "closed_trade_pnl": 100.33817279677307
    },
    {
      "month": "2025-12",
      "start_equity": 9963.288552179432,
      "end_equity": 9942.792556994713,
      "equity_change": -20.495995184719504,
      "return_fraction": -0.0020571516199072715,
      "closed_trade_pnl": -20.49599518471932
    }
  ],
  "child_monthly": [
    {
      "month": "2025-01",
      "start_equity": 10000,
      "end_equity": 9923.56066048968,
      "equity_change": -76.43933951031977,
      "return_fraction": -0.0076439339510320226,
      "closed_trade_pnl": -76.43933951032292
    },
    {
      "month": "2025-02",
      "start_equity": 9923.56066048968,
      "end_equity": 9999.546724170432,
      "equity_change": 75.98606368075161,
      "return_fraction": 0.007657137017692328,
      "closed_trade_pnl": 0.0
    },
    {
      "month": "2025-03",
      "start_equity": 9999.546724170432,
      "end_equity": 9878.234497631807,
      "equity_change": -121.3122265386246,
      "return_fraction": -0.012131772557789522,
      "closed_trade_pnl": -45.32616285786803
    },
    {
      "month": "2025-04",
      "start_equity": 9878.234497631807,
      "end_equity": 9903.148276055887,
      "equity_change": 24.913778424079283,
      "return_fraction": 0.0025220881757819225,
      "closed_trade_pnl": 24.91377842407323
    },
    {
      "month": "2025-05",
      "start_equity": 9903.148276055887,
      "end_equity": 9942.190192051954,
      "equity_change": 39.04191599606747,
      "return_fraction": 0.003942374173116603,
      "closed_trade_pnl": 39.04191599606559
    },
    {
      "month": "2025-06",
      "start_equity": 9942.190192051954,
      "end_equity": 9918.47882715739,
      "equity_change": -23.711364894563303,
      "return_fraction": -0.0023849236874907698,
      "closed_trade_pnl": -23.711364894562642
    },
    {
      "month": "2025-07",
      "start_equity": 9918.47882715739,
      "end_equity": 9909.011795197586,
      "equity_change": -9.467031959804444,
      "return_fraction": -0.0009544842636436401,
      "closed_trade_pnl": -9.46703195981207
    },
    {
      "month": "2025-08",
      "start_equity": 9909.011795197586,
      "end_equity": 9843.444386094614,
      "equity_change": -65.5674091029723,
      "return_fraction": -0.0066169473261450396,
      "closed_trade_pnl": -65.56740910297225
    },
    {
      "month": "2025-09",
      "start_equity": 9843.444386094614,
      "end_equity": 9817.553620004168,
      "equity_change": -25.89076609044605,
      "return_fraction": -0.0026302547233385543,
      "closed_trade_pnl": -25.890766090444355
    },
    {
      "month": "2025-10",
      "start_equity": 9817.553620004168,
      "end_equity": 9870.611286013787,
      "equity_change": 53.057666009619425,
      "return_fraction": 0.005404367326449888,
      "closed_trade_pnl": 60.89716005353
    },
    {
      "month": "2025-11",
      "start_equity": 9870.611286013787,
      "end_equity": 9978.946642168676,
      "equity_change": 108.33535615488836,
      "return_fraction": 0.010975546804116831,
      "closed_trade_pnl": 100.49586211097693
    },
    {
      "month": "2025-12",
      "start_equity": 9978.946642168676,
      "end_equity": 9968.68253904372,
      "equity_change": -10.264103124955,
      "return_fraction": -0.0010285758099538578,
      "closed_trade_pnl": -10.26410312495267
    }
  ]
}
```

## 2025 成本2：完整指標及取捨

```json
{
  "year": 2025,
  "cost": 2,
  "checks": "passed",
  "metrics": {
    "average_loss": -10.833248480433307,
    "average_win": 19.396840260222167,
    "cagr": -0.012533539965786433,
    "exposure": 0.19803675379522886,
    "fees": 133.19079143639127,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.02721708357483832,
    "maximum_margin_ratio": 0.02198101376531773,
    "net_funding": -5.615940217311734,
    "number_of_trades": 59,
    "profit_factor": 0.7247227850695341,
    "sharpe_ratio": -0.6538251982153365,
    "slippage": 66.59547587024728,
    "sortino_ratio": -0.9294053613831386,
    "total_return": -0.012525015175441467,
    "win_rate": 0.288135593220339
  },
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
    "swing/1": {
      "count": 24,
      "pnl": -58.23541265309477
    },
    "intraday/1": {
      "count": 5,
      "pnl": -50.21956069057169
    },
    "swing/-1": {
      "count": 19,
      "pnl": -50.186019056685794
    },
    "intraday/-1": {
      "count": 11,
      "pnl": 33.39084064593016
    }
  },
  "common_entries": [
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1741705200000,
      "parent_pnl": -24.11304891567173,
      "child_pnl": -24.15216475207058,
      "parent_quantity": 0.008099917996362092,
      "child_quantity": 0.008113057565244395
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1741748400000,
      "parent_pnl": -11.819129616778415,
      "child_pnl": -11.838302436527737,
      "parent_quantity": 0.006413631190377435,
      "child_quantity": 0.0064240352893880056
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1743555600000,
      "parent_pnl": -11.46839550701374,
      "child_pnl": -11.486999371003675,
      "parent_quantity": 0.009669151323173832,
      "child_quantity": 0.009684836479480518
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1743764400000,
      "parent_pnl": -6.98159225962196,
      "child_pnl": -6.9929176967985684,
      "parent_quantity": 0.004495584201272394,
      "child_quantity": 0.0045028768724210844
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1744412400000,
      "parent_pnl": -11.532951385673407,
      "child_pnl": -11.551659971268514,
      "parent_quantity": 0.008153506608365403,
      "child_quantity": 0.008166733107912811
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1750118400000,
      "parent_pnl": 6.862905585538639,
      "child_pnl": 6.874038490922923,
      "parent_quantity": 0.004244752019672351,
      "child_quantity": 0.004251637794513017
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1760277600000,
      "parent_pnl": -22.900982362699015,
      "child_pnl": -22.9381320024068,
      "parent_quantity": 0.014104276305080876,
      "child_quantity": 0.014127156056472075
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1760500800000,
      "parent_pnl": 0.16930842604681878,
      "child_pnl": 0.1695830757071484,
      "parent_quantity": 0.005112223900522874,
      "child_quantity": 0.0051205168756015005
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1760623200000,
      "parent_pnl": 54.84190999494436,
      "child_pnl": 54.93087374177984,
      "parent_quantity": 0.01254739870288403,
      "child_quantity": 0.012567752910127178
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1761930000000,
      "parent_pnl": -17.08598854523034,
      "child_pnl": -17.113705186746145,
      "parent_quantity": 0.00767585685713605,
      "child_quantity": 0.0076883085202208434
    },
    {
      "sleeve": "intraday",
      "direction": -1,
      "entry_ms": 1763622000000,
      "parent_pnl": 77.36472682241686,
      "child_pnl": 77.49022675434227,
      "parent_quantity": 0.013145226115168114,
      "child_quantity": 0.013166550109323546
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1736438400000,
      "parent_pnl": -24.1807394194044,
      "child_pnl": -24.1807394194044,
      "parent_quantity": 0.008044342282342647,
      "child_quantity": 0.008044342282342647
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1743022800000,
      "parent_pnl": -5.316949344013958,
      "child_pnl": -5.325574421722249,
      "parent_quantity": 0.006046158910930581,
      "child_quantity": 0.006055966901766935
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1744772400000,
      "parent_pnl": -1.3110101110033447,
      "child_pnl": -1.3131368124917622,
      "parent_quantity": 0.008871159352183822,
      "child_quantity": 0.008885550017549353
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1747324800000,
      "parent_pnl": 1.363438717116724,
      "child_pnl": 1.365650467525607,
      "parent_quantity": 0.004648797999673005,
      "child_quantity": 0.00465633921201171
    },
    {
      "sleeve": "intraday",
      "direction": 1,
      "entry_ms": 1757098800000,
      "parent_pnl": -20.732129146837458,
      "child_pnl": -20.765760504478887,
      "parent_quantity": 0.013824599752629096,
      "child_quantity": 0.013847025816794397
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1740427200000,
      "parent_pnl": 32.68579240738208,
      "child_pnl": 32.68579240738208,
      "parent_quantity": 0.005416521209884448,
      "child_quantity": 0.005416521209884448
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1740484800000,
      "parent_pnl": 4.280077779814289,
      "child_pnl": 4.280077779814289,
      "parent_quantity": 0.0032814937822715985,
      "child_quantity": 0.0032814937822715985
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1741564800000,
      "parent_pnl": -24.33100296849602,
      "child_pnl": -12.16550148424801,
      "parent_quantity": 0.006918554519507397,
      "child_quantity": 0.0034592772597536983
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1741651200000,
      "parent_pnl": -7.883343893642267,
      "child_pnl": -3.9464989440220823,
      "parent_quantity": 0.005658990773607281,
      "child_quantity": 0.0028329604053278765
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1743998400000,
      "parent_pnl": -11.944793633758792,
      "child_pnl": -11.96417030384436,
      "parent_quantity": 0.004176680839758362,
      "child_quantity": 0.004183456190523401
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1750622400000,
      "parent_pnl": -9.455021034702499,
      "child_pnl": -9.47035883197711,
      "parent_quantity": 0.0035342199020083624,
      "child_quantity": 0.0035399530620068374
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1754092800000,
      "parent_pnl": -4.504573447556765,
      "child_pnl": -4.511880700929722,
      "parent_quantity": 0.0033361521177453757,
      "child_quantity": 0.0033415639750719144
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1755504000000,
      "parent_pnl": -11.624285456211327,
      "child_pnl": -11.643142202604082,
      "parent_quantity": 0.005315087541952301,
      "child_quantity": 0.005323709599472435
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1755633600000,
      "parent_pnl": -11.633509003946438,
      "child_pnl": -11.652380712643861,
      "parent_quantity": 0.0037748715087382637,
      "child_quantity": 0.0037809950502646376
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1755648000000,
      "parent_pnl": -5.518326218513228,
      "child_pnl": -5.527277966851394,
      "parent_quantity": 0.0037258073861247804,
      "child_quantity": 0.0037318513365467727
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1756180800000,
      "parent_pnl": -6.085678845936617,
      "child_pnl": -6.095550945435372,
      "parent_quantity": 0.003244353978878522,
      "child_quantity": 0.003249616922602549
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1758844800000,
      "parent_pnl": -6.505053565904466,
      "child_pnl": -6.515605968959747,
      "parent_quantity": 0.0038909279579424404,
      "child_quantity": 0.003897239764548688
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1760155200000,
      "parent_pnl": -5.161996995627966,
      "child_pnl": -5.1703707118958135,
      "parent_quantity": 0.0019063207721190492,
      "child_quantity": 0.0019094131778827
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1760644800000,
      "parent_pnl": -0.6724286566736907,
      "child_pnl": -0.6735194606369873,
      "parent_quantity": 0.002754825239588634,
      "child_quantity": 0.002759294076928788
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1760659200000,
      "parent_pnl": -4.832605092247936,
      "child_pnl": -4.840444473772434,
      "parent_quantity": 0.0029385325901256556,
      "child_quantity": 0.00294329943485152
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1762286400000,
      "parent_pnl": -10.329380972507863,
      "child_pnl": -10.346137143726006,
      "parent_quantity": 0.002744539776840602,
      "child_quantity": 0.0027489919292530405
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1763121600000,
      "parent_pnl": 34.384907142157736,
      "child_pnl": 34.44068583721482,
      "parent_quantity": 0.0025533015400685797,
      "child_quantity": 0.0025574434686014527
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1763712000000,
      "parent_pnl": -6.688705324797839,
      "child_pnl": -6.699555645058885,
      "parent_quantity": 0.002433524530394732,
      "child_quantity": 0.0024374721584087817
    },
    {
      "sleeve": "swing",
      "direction": -1,
      "entry_ms": 1765828800000,
      "parent_pnl": -20.706768950281894,
      "child_pnl": -10.370179584491108,
      "parent_quantity": 0.008824105614483425,
      "child_quantity": 0.0044192099749808455
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1736150400000,
      "parent_pnl": -24.306086900156675,
      "child_pnl": -24.306086900156675,
      "parent_quantity": 0.011570351481377502,
      "child_quantity": 0.011570351481377502
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1737100800000,
      "parent_pnl": -5.287066917304459,
      "child_pnl": -5.287066917304459,
      "parent_quantity": 0.006809471959371016,
      "child_quantity": 0.006809471959371016
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1737129600000,
      "parent_pnl": -24.648476396045336,
      "child_pnl": -24.648476396045336,
      "parent_quantity": 0.006496399693379584,
      "child_quantity": 0.006496399693379584
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1742428800000,
      "parent_pnl": -10.846041141092641,
      "child_pnl": -10.863635430903686,
      "parent_quantity": 0.004037494277098097,
      "child_quantity": 0.004044043841450436
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1742803200000,
      "parent_pnl": -11.722320174050482,
      "child_pnl": -11.741335950933234,
      "parent_quantity": 0.006918686027302386,
      "child_quantity": 0.006929909418906056
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1742817600000,
      "parent_pnl": -11.761799571442726,
      "child_pnl": -11.780879391228341,
      "parent_quantity": 0.006512595794302199,
      "child_quantity": 0.00652316043225042
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1745222400000,
      "parent_pnl": 41.57799796518997,
      "child_pnl": 41.645445187309655,
      "parent_quantity": 0.006208112022235679,
      "child_quantity": 0.00621818273104802
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1745352000000,
      "parent_pnl": 13.279449480162931,
      "child_pnl": 13.30099120950414,
      "parent_quantity": 0.003967445340480911,
      "child_quantity": 0.003973881272469533
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1745611200000,
      "parent_pnl": -4.6701152822387275,
      "child_pnl": -4.677691075162414,
      "parent_quantity": 0.0038693060086198304,
      "child_quantity": 0.0038755827404151166
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1746705600000,
      "parent_pnl": 20.454708390776545,
      "child_pnl": 20.487889720512097,
      "parent_quantity": 0.008494210435271614,
      "child_quantity": 0.008507989619599804
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1746734400000,
      "parent_pnl": 3.9428737757368153,
      "child_pnl": 3.9492698480913533,
      "parent_quantity": 0.0075275939627502605,
      "child_quantity": 0.00753980511592935
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1749513600000,
      "parent_pnl": -23.7564461959054,
      "child_pnl": -23.794983556571303,
      "parent_quantity": 0.009577534584410111,
      "child_quantity": 0.009593071121378893
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1752192000000,
      "parent_pnl": 1.341051445703886,
      "child_pnl": 1.3432268798074731,
      "parent_quantity": 0.003538857117208226,
      "child_quantity": 0.0035445977996295904
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1752206400000,
      "parent_pnl": -1.623544695505886,
      "child_pnl": -1.6261783860407393,
      "parent_quantity": 0.0034372790954064914,
      "child_quantity": 0.0034428549994418283
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1752480000000,
      "parent_pnl": -11.8702819951369,
      "child_pnl": -11.889537793528634,
      "parent_quantity": 0.0040870463726798084,
      "child_quantity": 0.004093676319719165
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1754884800000,
      "parent_pnl": -11.84821558098388,
      "child_pnl": -11.867435583560288,
      "parent_quantity": 0.004124717440093962,
      "child_quantity": 0.00413140849658966
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1755129600000,
      "parent_pnl": -8.29977431884552,
      "child_pnl": -8.313238091740393,
      "parent_quantity": 0.0035634590956506043,
      "child_quantity": 0.0035692396870427184
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1755144000000,
      "parent_pnl": -8.922226141369265,
      "child_pnl": -8.936699646535702,
      "parent_quantity": 0.0037203138903541223,
      "child_quantity": 0.003726348929307365
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1759334400000,
      "parent_pnl": 14.144456108438789,
      "child_pnl": 14.167401038921193,
      "parent_quantity": 0.004033377163713626,
      "child_quantity": 0.004039920049344663
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1759348800000,
      "parent_pnl": 13.516469345555725,
      "child_pnl": 13.538395565067006,
      "parent_quantity": 0.0038625885445270113,
      "child_quantity": 0.003868854379349986
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1759377600000,
      "parent_pnl": 8.658529344906272,
      "child_pnl": 8.672575084974014,
      "parent_quantity": 0.003968915181826863,
      "child_quantity": 0.003975353498170695
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1759435200000,
      "parent_pnl": 0.4035067720980826,
      "child_pnl": 0.404161334900922,
      "parent_quantity": 0.0037433308463153173,
      "child_quantity": 0.0037494032230389507
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1761494400000,
      "parent_pnl": -7.410535836382028,
      "child_pnl": -7.422557099575155,
      "parent_quantity": 0.004797733748010604,
      "child_quantity": 0.00480551656174888
    },
    {
      "sleeve": "swing",
      "direction": 1,
      "entry_ms": 1761537600000,
      "parent_pnl": -8.575055972116875,
      "child_pnl": -8.588966302896267,
      "parent_quantity": 0.004825487124123347,
      "child_quantity": 0.0048333149589837275
    }
  ],
  "missing_entries": [],
  "new_entries": [],
  "downsized_winners": [],
  "parent_monthly": [
    {
      "month": "2025-01",
      "start_equity": 10000,
      "end_equity": 9921.577630367088,
      "equity_change": -78.4223696329118,
      "return_fraction": -0.007842236963291227,
      "closed_trade_pnl": -78.42236963291087
    },
    {
      "month": "2025-02",
      "start_equity": 9921.577630367088,
      "end_equity": 9987.799988458288,
      "equity_change": 66.22235809119957,
      "return_fraction": 0.006674579442740303,
      "closed_trade_pnl": 0.0
    },
    {
      "month": "2025-03",
      "start_equity": 9987.799988458288,
      "end_equity": 9850.749864929092,
      "equity_change": -137.05012352919584,
      "return_fraction": -0.013721752907303708,
      "closed_trade_pnl": -70.82776543799187
    },
    {
      "month": "2025-04",
      "start_equity": 9850.749864929092,
      "end_equity": 9857.698454195135,
      "equity_change": 6.9485892660432,
      "return_fraction": 0.0007053868346389436,
      "closed_trade_pnl": 6.94858926604293
    },
    {
      "month": "2025-05",
      "start_equity": 9857.698454195135,
      "end_equity": 9883.459475078764,
      "equity_change": 25.76102088362859,
      "return_fraction": 0.0026132896033825848,
      "closed_trade_pnl": 25.761020883630085
    },
    {
      "month": "2025-06",
      "start_equity": 9883.459475078764,
      "end_equity": 9857.110913433695,
      "equity_change": -26.348561645068912,
      "return_fraction": -0.002665924994330937,
      "closed_trade_pnl": -26.34856164506926
    },
    {
      "month": "2025-07",
      "start_equity": 9857.110913433695,
      "end_equity": 9844.958138188756,
      "equity_change": -12.152775244938312,
      "return_fraction": -0.0012328942376387264,
      "closed_trade_pnl": -12.1527752449389
    },
    {
      "month": "2025-08",
      "start_equity": 9844.958138188756,
      "end_equity": 9776.52154917539,
      "equity_change": -68.43658901336676,
      "return_fraction": -0.00695143524764219,
      "closed_trade_pnl": -68.43658901336303
    },
    {
      "month": "2025-09",
      "start_equity": 9776.52154917539,
      "end_equity": 9749.28436646265,
      "equity_change": -27.237182712739013,
      "return_fraction": -0.0027859788960457044,
      "closed_trade_pnl": -27.237182712741923
    },
    {
      "month": "2025-10",
      "start_equity": 9749.28436646265,
      "end_equity": 9783.247009726323,
      "equity_change": 33.96264326367236,
      "return_fraction": 0.0034836037176741996,
      "closed_trade_pnl": 42.18057507624255
    },
    {
      "month": "2025-11",
      "start_equity": 9783.247009726323,
      "end_equity": 9869.110500660923,
      "equity_change": 85.86349093460012,
      "return_fraction": 0.00877658418000049,
      "closed_trade_pnl": 77.64555912203855
    },
    {
      "month": "2025-12",
      "start_equity": 9869.110500660923,
      "end_equity": 9848.403731710641,
      "equity_change": -20.706768950281912,
      "return_fraction": -0.002098139335748206,
      "closed_trade_pnl": -20.706768950281894
    }
  ],
  "child_monthly": [
    {
      "month": "2025-01",
      "start_equity": 10000,
      "end_equity": 9921.577630367088,
      "equity_change": -78.4223696329118,
      "return_fraction": -0.007842236963291227,
      "closed_trade_pnl": -78.42236963291087
    },
    {
      "month": "2025-02",
      "start_equity": 9921.577630367088,
      "end_equity": 9987.799988458288,
      "equity_change": 66.22235809119957,
      "return_fraction": 0.006674579442740303,
      "closed_trade_pnl": 0.0
    },
    {
      "month": "2025-03",
      "start_equity": 9987.799988458288,
      "end_equity": 9866.729607742629,
      "equity_change": -121.07038071565876,
      "return_fraction": -0.012121826714147854,
      "closed_trade_pnl": -54.848022624459546
    },
    {
      "month": "2025-04",
      "start_equity": 9866.729607742629,
      "end_equity": 9873.68946890888,
      "equity_change": 6.959861166251358,
      "return_fraction": 0.0007053868346396097,
      "closed_trade_pnl": 6.959861166244501
    },
    {
      "month": "2025-05",
      "start_equity": 9873.68946890888,
      "end_equity": 9899.492278945008,
      "equity_change": 25.802810036127994,
      "return_fraction": 0.0026132896033825848,
      "closed_trade_pnl": 25.80281003612906
    },
    {
      "month": "2025-06",
      "start_equity": 9899.492278945008,
      "end_equity": 9873.10097504738,
      "equity_change": -26.39130389762795,
      "return_fraction": -0.002665924994331159,
      "closed_trade_pnl": -26.39130389762549
    },
    {
      "month": "2025-07",
      "start_equity": 9873.10097504738,
      "end_equity": 9860.928485747618,
      "equity_change": -12.172489299762674,
      "return_fraction": -0.0012328942376388374,
      "closed_trade_pnl": -12.1724892997619
    },
    {
      "month": "2025-08",
      "start_equity": 9860.928485747618,
      "end_equity": 9792.38087989732,
      "equity_change": -68.54760585029726,
      "return_fraction": -0.006951435247641413,
      "closed_trade_pnl": -68.54760585030081
    },
    {
      "month": "2025-09",
      "start_equity": 9792.38087989732,
      "end_equity": 9765.099513423884,
      "equity_change": -27.28136647343672,
      "return_fraction": -0.0027859788960458154,
      "closed_trade_pnl": -27.281366473438634
    },
    {
      "month": "2025-10",
      "start_equity": 9765.099513423884,
      "end_equity": 9799.11725039231,
      "equity_change": 34.01773696842611,
      "return_fraction": 0.0034836037176746437,
      "closed_trade_pnl": 42.248999790166664
    },
    {
      "month": "2025-11",
      "start_equity": 9799.11725039231,
      "end_equity": 9885.120027830077,
      "equity_change": 86.00277743776678,
      "return_fraction": 0.008776584180000935,
      "closed_trade_pnl": 77.77151461602607
    },
    {
      "month": "2025-12",
      "start_equity": 9885.120027830077,
      "end_equity": 9874.749848245585,
      "equity_change": -10.37017958449178,
      "return_fraction": -0.001049069667874103,
      "closed_trade_pnl": -10.370179584491108
    }
  ]
}
```
