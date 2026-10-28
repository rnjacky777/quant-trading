# 移除1H通道退出：未採用，保留上一研究候選

2026-10-28。portfolio_directional_loss_guard → portfolio_sweep_context_exit。唯一exit變更：短線只因結構stop、4h反轉或24h上限退出，不再用1h反向10根通道；波段及原同方向連虧guard全部繼承。

## 事前證據與限制

父channel-only退出2024一般成本10筆約−46.24USDT、2025為8筆−5.67，但2025空單子組+16.03是贏家，不把全部退出都視為可刪的輸家。這只支持一次試驗，不等於不退出可回收損失。未延長24h（不同於已失敗48h），未掃channel根數。

## 全部期間及成本

每年10,000USDT，原訊號、結構初始stop、0.25%／0.125%風險、共享／同方向保護、gross/stoprisk/margin、每日總計2次均不變；實際1x。一般單邊費10bps／滑價5bps，雙成本20bps／10bps，含實際funding。父四筆完整快照（含guard trace）與輸入指紋重播一致後才跑子候選。

|年|成本倍數|父收益|候選收益|父回撤|候選回撤|交易數|
|---|---:|---:|---:|---:|---:|---:|
|2024|1|+3.570%|+3.389%|-3.081%|-3.276%|101|
|2024|2|+0.328%|+0.252%|-3.877%|-3.890%|101|
|2025|1|-2.454%|-2.297%|-4.381%|-4.609%|85|
|2025|2|-3.617%|-3.691%|-4.895%|-5.181%|85|

## 決策：不採用

只有2025一般成本−2.454%→−2.297%微升；2024一般成本+3.570%→+3.389%、雙成本+0.328%→+0.252%，2025雙成本−3.617%→−3.691%均退步，四組回撤亦全變大。仍保留父『結構止損＋同方向連虧保護』作下一輪研究基準，沒有新可用／實盤版本。

當初channel-only共同事件一般成本2024原淨−46.24→候選−70.86，10筆中3筆轉stop、7筆time_limit；2025為−5.67→−14.93，8筆中4筆stop、3筆time_limit、1筆4h signal退出。因此拿掉虧損退出不等於回收損失。2025一般年度微升，卻不是該退出群組實際改善，還受到其他事件數量與連虧風險路徑影響。共同事件的按父qty重算差額與qty差額是代數拆解，非獨立因果估計。

本輪停止，不再掃通道根數或延長持有到數字變好。尚未達各年10%目標；後續優先尋找能改善訊號本身的新證據，而非繼續堆出場補丁。

## 驗證及限制

238項pytest通過，新增多空對稱channel-only移除、4h反轉仍退出、原進場／stop／timestamp保留及前綴因果。父四筆完整快照（包含guard trace）重播一致；子交易事件及入場／stop與父相同，波段退出不變，方向guard所有輸入均由當時可知平倉重建，qty與planned risk重算一致；cash/PnL、ID、每日≤2、1x及gross/stoprisk/margin均核對。

2024／2025及14項經驗皆調參，不是未見驗證；重疊事件／成本案例非獨立樣本。保留固定BTC選樣、1h盤中順序、固定MMR2%非歷史級距、深度滑價、精度／最小單量及虛擬部位／交易所映射限制。未改live/paper/testnet、未下單。完整曲線交易data/perpetual-sweep-context-exit.json，審計data/context-exit-audit.json。

## 2024／成本1倍完整指標及共同事件

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding及頻率：

```json
{
  "year": 2024,
  "cost": 1,
  "checks": "passed",
  "metrics": {
    "average_loss": -15.198515207210752,
    "average_win": 34.11593875872119,
    "cagr": 0.03381931363196067,
    "exposure": 0.307455890722823,
    "fees": 180.77659727581394,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.03276313099052075,
    "maximum_margin_ratio": 0.02325297997566693,
    "net_funding": -42.139179654502,
    "number_of_trades": 101,
    "profit_factor": 1.3539393514543974,
    "sharpe_ratio": 0.959719091132264,
    "slippage": 90.38846168876043,
    "sortino_ratio": 1.4097494000964508,
    "total_return": 0.03388992147771108,
    "win_rate": 0.37623762376237624
  },
  "frequency": {
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
    "swing/1/stop_loss": {
      "count": 11,
      "pnl": -196.9093939735666
    },
    "intraday/-1/stop_loss": {
      "count": 6,
      "pnl": -106.05215704847987
    },
    "swing/-1/stop_loss": {
      "count": 6,
      "pnl": -84.02030004380151
    },
    "intraday/1/time_limit": {
      "count": 15,
      "pnl": 333.13805356545623
    },
    "swing/1/signal": {
      "count": 11,
      "pnl": -26.287004492927394
    },
    "swing/1/time_limit": {
      "count": 11,
      "pnl": 619.1470044252078
    },
    "intraday/1/stop_loss": {
      "count": 20,
      "pnl": -375.99289569622226
    },
    "intraday/-1/signal": {
      "count": 2,
      "pnl": -18.94407506057823
    },
    "intraday/-1/time_limit": {
      "count": 12,
      "pnl": 170.75722588122056
    },
    "swing/-1/signal": {
      "count": 2,
      "pnl": -10.337280890089279
    },
    "intraday/1/signal": {
      "count": 5,
      "pnl": 34.400038110908504
    }
  },
  "past_only_risk_trace_checks": 101,
  "common_events": [
    {
      "entry_timestamp_ms": 1704744000000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -24.44130449432212,
      "child_pnl": -24.44130449432212,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0
    },
    {
      "entry_timestamp_ms": 1706061600000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -23.231804563981935,
      "child_pnl": -23.231804563981935,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0
    },
    {
      "entry_timestamp_ms": 1705968000000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -23.232750533840917,
      "child_pnl": -23.232750533840917,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -3.552713678800501e-15,
      "quantity_delta": 3.552713678800501e-15
    },
    {
      "entry_timestamp_ms": 1706486400000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 47.45373136299877,
      "child_pnl": 47.45373136299877,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0
    },
    {
      "entry_timestamp_ms": 1706572800000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -12.183954938509274,
      "child_pnl": -12.183954938509274,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": -1.7763568394002505e-15
    },
    {
      "entry_timestamp_ms": 1706443200000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -6.87491331187834,
      "child_pnl": -6.87491331187834,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0
    },
    {
      "entry_timestamp_ms": 1707177600000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 11.144876965601142,
      "child_pnl": 11.144876965601142,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0
    },
    {
      "entry_timestamp_ms": 1707350400000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 83.43645643827757,
      "child_pnl": 83.43645643827757,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0
    },
    {
      "entry_timestamp_ms": 1707364800000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 86.55143471554155,
      "child_pnl": 86.55143471554155,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0
    },
    {
      "entry_timestamp_ms": 1707465600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 51.57428165886777,
      "child_pnl": 51.57428165886777,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0
    },
    {
      "entry_timestamp_ms": 1708398000000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -24.021143279106766,
      "child_pnl": -24.021143279106766,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0
    },
    {
      "entry_timestamp_ms": 1708455600000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 2.2663965922392957,
      "child_pnl": -24.333445529944452,
      "parent_exit": "signal",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -26.599842122183748,
      "quantity_delta": 0.0
    },
    {
      "entry_timestamp_ms": 1709020800000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 121.24854600562938,
      "child_pnl": 120.93136935248816,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 1.4210854715202004e-14,
      "quantity_delta": -0.31717665314123167
    },
    {
      "entry_timestamp_ms": 1709121600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 15.88073480758657,
      "child_pnl": 15.839192055268041,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.041542752318529
    },
    {
      "entry_timestamp_ms": 1710158400000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -26.613304281725473,
      "child_pnl": -26.543685972399796,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.06961830932567636
    },
    {
      "entry_timestamp_ms": 1710172800000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -26.0616157872382,
      "child_pnl": -25.993440651591907,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 3.552713678800501e-15,
      "quantity_delta": 0.06817513564628896
    },
    {
      "entry_timestamp_ms": 1710270000000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 11.382170011920993,
      "child_pnl": 5.676197575517831,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": -5.70597243640316
    },
    {
      "entry_timestamp_ms": 1710450000000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -25.214335416233528,
      "child_pnl": -25.13443304429471,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0799023719388181
    },
    {
      "entry_timestamp_ms": 1711220400000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -1.281240045463909,
      "child_pnl": -22.855867972755657,
      "parent_exit": "signal",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -21.647286740025873,
      "quantity_delta": 0.07265881273412589
    },
    {
      "entry_timestamp_ms": 1711404000000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -6.093514028905238,
      "child_pnl": -6.061360526030755,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.032153502874483486
    },
    {
      "entry_timestamp_ms": 1712260800000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 1.86341489174968,
      "child_pnl": 10.219250735491775,
      "parent_exit": "signal",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 8.410045572150032,
      "quantity_delta": -0.054209728407938584
    },
    {
      "entry_timestamp_ms": 1712577600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -12.602591470508099,
      "child_pnl": -12.54639396885546,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": 0.056197501652636817
    },
    {
      "entry_timestamp_ms": 1713830400000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -12.389703340974355,
      "child_pnl": -12.334455150504205,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": 0.05524819047014873
    },
    {
      "entry_timestamp_ms": 1713996000000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -24.12021441253937,
      "child_pnl": -24.01265750311461,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 3.552713678800501e-15,
      "quantity_delta": 0.10755690942475482
    },
    {
      "entry_timestamp_ms": 1714154400000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -11.956432540805267,
      "child_pnl": -11.903116392373098,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": 0.0533161484321667
    },
    {
      "entry_timestamp_ms": 1714280400000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 17.79653009576907,
      "child_pnl": 17.717171772379103,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.07935832338996818
    },
    {
      "entry_timestamp_ms": 1714507200000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -2.9774793706877305,
      "child_pnl": -2.9642021885901837,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": -4.440892098500626e-16,
      "quantity_delta": 0.013277182097547247
    },
    {
      "entry_timestamp_ms": 1715216400000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -11.751039185446535,
      "child_pnl": -11.69863892748454,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": 0.0524002579619971
    },
    {
      "entry_timestamp_ms": 1715259600000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 14.221942757862058,
      "child_pnl": 14.158524241637918,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": -0.06341851622413763
    },
    {
      "entry_timestamp_ms": 1715817600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -2.2679481365816874,
      "child_pnl": -2.257834897613981,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": -4.440892098500626e-16,
      "quantity_delta": 0.010113238967706994
    },
    {
      "entry_timestamp_ms": 1716249600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -12.401333021400449,
      "child_pnl": -12.34603297183557,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.05530004956487922
    },
    {
      "entry_timestamp_ms": 1716501600000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 7.769731670632316,
      "child_pnl": 7.735084867280582,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -8.881784197001252e-16,
      "quantity_delta": -0.03464680335173309
    },
    {
      "entry_timestamp_ms": 1716926400000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -12.00383468594352,
      "child_pnl": -11.950307161768839,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": 0.053527524174683094
    },
    {
      "entry_timestamp_ms": 1717426800000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -12.948431993909427,
      "child_pnl": -14.624690722137505,
      "parent_exit": "signal",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -1.741765285974214,
      "quantity_delta": 0.06550655774613645
    },
    {
      "entry_timestamp_ms": 1718121600000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -12.094482218665242,
      "child_pnl": -12.038485901626263,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 3.552713678800501e-15,
      "quantity_delta": 0.05599631703897501
    },
    {
      "entry_timestamp_ms": 1718107200000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -11.965847409251143,
      "child_pnl": -11.910446659301353,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": 0.055400749949788164
    },
    {
      "entry_timestamp_ms": 1719244800000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -12.034716830980672,
      "child_pnl": -11.978997222074897,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -3.552713678800501e-15,
      "quantity_delta": 0.05571960890577898
    },
    {
      "entry_timestamp_ms": 1720090800000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -12.062014344991024,
      "child_pnl": -12.00616835115853,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": 0.05584599383249511
    },
    {
      "entry_timestamp_ms": 1720166400000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -12.38820166713791,
      "child_pnl": -12.330845456631822,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": 0.05735621050608586
    },
    {
      "entry_timestamp_ms": 1720314000000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 42.70341256865959,
      "child_pnl": 42.505699778181395,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.19771279047819235
    },
    {
      "entry_timestamp_ms": 1720512000000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -23.64659952166057,
      "child_pnl": -23.552775764889972,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -7.105427357601002e-15,
      "quantity_delta": 0.09382375677060395
    },
    {
      "entry_timestamp_ms": 1720436400000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -12.59566603884036,
      "child_pnl": -11.912420396745915,
      "parent_exit": "signal",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.6278357114197188,
      "quantity_delta": 0.05540993067472577
    },
    {
      "entry_timestamp_ms": 1721088000000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -6.0720721969136,
      "child_pnl": -6.044325224589009,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": 0.027746972324592
    },
    {
      "entry_timestamp_ms": 1721124000000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 23.473635267239505,
      "child_pnl": 23.366370022855673,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.10726524438383223
    },
    {
      "entry_timestamp_ms": 1720958400000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 23.259334767241516,
      "child_pnl": 23.15304879152409,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.1062859757174266
    },
    {
      "entry_timestamp_ms": 1721016000000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 4.461119229091331,
      "child_pnl": 4.44073367572961,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.020385553361720987
    },
    {
      "entry_timestamp_ms": 1721030400000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 3.199686698751975,
      "child_pnl": 3.1850653939653095,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 4.440892098500626e-16,
      "quantity_delta": -0.014621304786666123
    },
    {
      "entry_timestamp_ms": 1721336400000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 87.43298574516315,
      "child_pnl": 87.03345152405113,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -2.842170943040401e-14,
      "quantity_delta": -0.3995342211119919
    },
    {
      "entry_timestamp_ms": 1721592000000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -7.28822033407215,
      "child_pnl": 7.8321631560019425,
      "parent_exit": "signal",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 15.15633767954216,
      "quantity_delta": -0.03595418946806728
    },
    {
      "entry_timestamp_ms": 1721725200000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -23.699953242817752,
      "child_pnl": -23.62659834734381,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 3.552713678800501e-15,
      "quantity_delta": 0.07335489547394047
    },
    {
      "entry_timestamp_ms": 1721919600000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 17.466805050825283,
      "child_pnl": 34.82548536016777,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": -3.552713678800501e-15,
      "quantity_delta": 17.35868030934249
    },
    {
      "entry_timestamp_ms": 1722027600000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -11.930797445943103,
      "child_pnl": -11.914185362241017,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.016612083702085556
    },
    {
      "entry_timestamp_ms": 1722117600000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -10.803460266733708,
      "child_pnl": -10.78841785343013,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": 0.015042413303580915
    },
    {
      "entry_timestamp_ms": 1722279600000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -12.110997671643148,
      "child_pnl": -12.094134682563944,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.016862989079204027
    },
    {
      "entry_timestamp_ms": 1722376800000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -12.169252215695966,
      "child_pnl": -12.152308114740864,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": 0.016944100955100794
    },
    {
      "entry_timestamp_ms": 1722844800000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -12.546243282309485,
      "child_pnl": -12.528774270326272,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.017469011983212823
    },
    {
      "entry_timestamp_ms": 1723032000000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -0.9166459228097008,
      "child_pnl": -6.675712698894554,
      "parent_exit": "signal",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -5.76837479797249,
      "quantity_delta": 0.009308021887637352
    },
    {
      "entry_timestamp_ms": 1723165200000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 3.497530237547892,
      "child_pnl": 3.4906785027347484,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -4.440892098500626e-16,
      "quantity_delta": -0.00685173481314294
    },
    {
      "entry_timestamp_ms": 1723255200000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -12.908001579342633,
      "child_pnl": -12.882714534547473,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": 0.02528704479515831
    },
    {
      "entry_timestamp_ms": 1723712400000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -11.817091384943097,
      "child_pnl": -11.79394145601237,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": 0.023149928930729757
    },
    {
      "entry_timestamp_ms": 1723759200000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 1.9948885714188376,
      "child_pnl": 1.9909805430260037,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": -2.220446049250313e-16,
      "quantity_delta": -0.003908028392833662
    },
    {
      "entry_timestamp_ms": 1723989600000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 52.239260509539946,
      "child_pnl": 52.136922706708816,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 7.105427357601002e-15,
      "quantity_delta": -0.10233780283113703
    },
    {
      "entry_timestamp_ms": 1724691600000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -23.668087785859306,
      "child_pnl": -23.621721507363134,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0463662784961727
    },
    {
      "entry_timestamp_ms": 1724457600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -14.127286279430123,
      "child_pnl": -14.09961063043162,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.027675648998503277
    },
    {
      "entry_timestamp_ms": 1724950800000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 35.73383156571978,
      "child_pnl": 35.66382824305586,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -7.105427357601002e-15,
      "quantity_delta": -0.07000332266391496
    },
    {
      "entry_timestamp_ms": 1725336000000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 62.09168002118901,
      "child_pnl": 61.97004112267699,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -7.105427357601002e-15,
      "quantity_delta": -0.12163889851201759
    },
    {
      "entry_timestamp_ms": 1725634800000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 4.074871223816952,
      "child_pnl": -0.5533618373815474,
      "parent_exit": "signal",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -4.629319236439927,
      "quantity_delta": 0.0010861752414271786
    },
    {
      "entry_timestamp_ms": 1725652800000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -7.3875510683984045,
      "child_pnl": -7.373078701499094,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.01447236689931053
    },
    {
      "entry_timestamp_ms": 1726682400000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 83.11430289817987,
      "child_pnl": 82.9140353855258,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 2.842170943040401e-14,
      "quantity_delta": -0.2002675126540936
    },
    {
      "entry_timestamp_ms": 1726761600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 3.480527010653113,
      "child_pnl": 3.472140530073423,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 4.440892098500626e-16,
      "quantity_delta": -0.008386480579690492
    },
    {
      "entry_timestamp_ms": 1726776000000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 5.834086549600153,
      "child_pnl": 5.820029065374742,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": -0.014057484225412864
    },
    {
      "entry_timestamp_ms": 1727319600000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 36.51288412421252,
      "child_pnl": 36.42490474848046,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -7.105427357601002e-15,
      "quantity_delta": -0.08797937573205417
    },
    {
      "entry_timestamp_ms": 1727697600000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -24.155957990401593,
      "child_pnl": -24.09775316338833,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -3.552713678800501e-15,
      "quantity_delta": 0.05820482701326668
    },
    {
      "entry_timestamp_ms": 1728892800000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 58.4011637750815,
      "child_pnl": 58.2604436415123,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 1.4210854715202004e-14,
      "quantity_delta": -0.14072013356921076
    },
    {
      "entry_timestamp_ms": 1728907200000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 47.74220726746218,
      "child_pnl": 47.6271703512555,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.11503691620667666
    },
    {
      "entry_timestamp_ms": 1729562400000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -8.237542855472896,
      "child_pnl": -8.217694139180724,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.019848716292171886
    },
    {
      "entry_timestamp_ms": 1729713600000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 3.6906776293479866,
      "child_pnl": 3.6817847817505815,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.008892847597405051
    },
    {
      "entry_timestamp_ms": 1730232000000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -25.7691772020555,
      "child_pnl": -25.707085253480503,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 3.552713678800501e-15,
      "quantity_delta": 0.06209194857499156
    },
    {
      "entry_timestamp_ms": 1730246400000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -25.701180301285344,
      "child_pnl": -25.63925219418782,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0619281070975255
    },
    {
      "entry_timestamp_ms": 1730188800000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -9.206998292534783,
      "child_pnl": -9.184813631378255,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.02218466115652795
    },
    {
      "entry_timestamp_ms": 1730412000000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -24.42461495160452,
      "child_pnl": -24.365762784007256,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 7.105427357601002e-15,
      "quantity_delta": 0.05885216759725864
    },
    {
      "entry_timestamp_ms": 1731225600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 69.8487309527204,
      "child_pnl": 69.68042741022317,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.16830354249722745
    },
    {
      "entry_timestamp_ms": 1731240000000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 61.64373730077513,
      "child_pnl": 61.49520404585442,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 7.105427357601002e-15,
      "quantity_delta": -0.14853325492071434
    },
    {
      "entry_timestamp_ms": 1731340800000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 30.371228005046575,
      "child_pnl": 30.298047215739178,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -1.0658141036401503e-14,
      "quantity_delta": -0.07318078930738636
    },
    {
      "entry_timestamp_ms": 1731888000000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -11.224996487538853,
      "child_pnl": 4.55682824803724,
      "parent_exit": "signal",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 15.79283113099013,
      "quantity_delta": -0.011006395414036696
    },
    {
      "entry_timestamp_ms": 1732291200000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -4.225119807806454,
      "child_pnl": -8.442524797737375,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -4.217404989930921
    },
    {
      "entry_timestamp_ms": 1732176000000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -11.101774720570102,
      "child_pnl": -11.091639129869677,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": 0.010135590700423691
    },
    {
      "entry_timestamp_ms": 1732190400000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -19.34078607144362,
      "child_pnl": -19.32312850800185,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 7.105427357601002e-15,
      "quantity_delta": 0.01765756344176239
    },
    {
      "entry_timestamp_ms": 1733148000000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -12.277346251937285,
      "child_pnl": -24.52239620705863,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -12.245049955121345
    },
    {
      "entry_timestamp_ms": 1733371200000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -13.162173908601144,
      "child_pnl": -13.129463153290903,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.03271075531024081
    },
    {
      "entry_timestamp_ms": 1733720400000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -12.16111631194892,
      "child_pnl": -12.130893394158756,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": 0.030222917790165837
    },
    {
      "entry_timestamp_ms": 1733752800000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -12.179833833856927,
      "child_pnl": -12.149564399109655,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": 0.03026943474726984
    },
    {
      "entry_timestamp_ms": 1733860800000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 32.370970891555444,
      "child_pnl": 32.29052225781595,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -7.105427357601002e-15,
      "quantity_delta": -0.0804486337394863
    },
    {
      "entry_timestamp_ms": 1734508800000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -24.59616195332356,
      "child_pnl": -24.53503534606151,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -3.552713678800501e-15,
      "quantity_delta": 0.06112660726205377
    },
    {
      "entry_timestamp_ms": 1734321600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -10.098200440588021,
      "child_pnl": -10.073104300240724,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.02509614034729779
    },
    {
      "entry_timestamp_ms": 1734580800000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -25.35170663826485,
      "child_pnl": -25.288702344422543,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -3.552713678800501e-15,
      "quantity_delta": 0.06300429384231165
    },
    {
      "entry_timestamp_ms": 1734645600000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -12.53563459658063,
      "child_pnl": -12.504480922514732,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": 0.03115367406589975
    },
    {
      "entry_timestamp_ms": 1734703200000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 5.86667450100718,
      "child_pnl": 5.852094587732988,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.014579913274192613
    },
    {
      "entry_timestamp_ms": 1735070400000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -19.22796684439332,
      "child_pnl": -19.18018132484861,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 3.552713678800501e-15,
      "quantity_delta": 0.04778551954470345
    },
    {
      "entry_timestamp_ms": 1735164000000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -24.025350084422204,
      "child_pnl": -11.98282103202587,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 3.552713678800501e-15,
      "quantity_delta": 12.04252905239633
    },
    {
      "entry_timestamp_ms": 1735596000000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -8.1884480835718,
      "child_pnl": -12.514702352585422,
      "parent_exit": "signal",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -4.342910266914126,
      "quantity_delta": 0.01665599790050365
    }
  ],
  "channel_only_comparison": {
    "count": 10,
    "parent_pnl": -46.23896619840027,
    "child_pnl": -70.8619593709141,
    "new_exit_counts": {
      "stop_loss": 3,
      "time_limit": 7
    },
    "events": [
      {
        "entry_timestamp_ms": 1708455600000,
        "sleeve": "intraday",
        "direction": 1,
        "parent_pnl": 2.2663965922392957,
        "child_pnl": -24.333445529944452,
        "parent_exit": "signal",
        "child_exit": "stop_loss",
        "repriced_parent_qty_delta": -26.599842122183748,
        "quantity_delta": 0.0
      },
      {
        "entry_timestamp_ms": 1711220400000,
        "sleeve": "intraday",
        "direction": -1,
        "parent_pnl": -1.281240045463909,
        "child_pnl": -22.855867972755657,
        "parent_exit": "signal",
        "child_exit": "stop_loss",
        "repriced_parent_qty_delta": -21.647286740025873,
        "quantity_delta": 0.07265881273412589
      },
      {
        "entry_timestamp_ms": 1712260800000,
        "sleeve": "intraday",
        "direction": -1,
        "parent_pnl": 1.86341489174968,
        "child_pnl": 10.219250735491775,
        "parent_exit": "signal",
        "child_exit": "time_limit",
        "repriced_parent_qty_delta": 8.410045572150032,
        "quantity_delta": -0.054209728407938584
      },
      {
        "entry_timestamp_ms": 1717426800000,
        "sleeve": "intraday",
        "direction": -1,
        "parent_pnl": -12.948431993909427,
        "child_pnl": -14.624690722137505,
        "parent_exit": "signal",
        "child_exit": "time_limit",
        "repriced_parent_qty_delta": -1.741765285974214,
        "quantity_delta": 0.06550655774613645
      },
      {
        "entry_timestamp_ms": 1720436400000,
        "sleeve": "intraday",
        "direction": -1,
        "parent_pnl": -12.59566603884036,
        "child_pnl": -11.912420396745915,
        "parent_exit": "signal",
        "child_exit": "time_limit",
        "repriced_parent_qty_delta": 0.6278357114197188,
        "quantity_delta": 0.05540993067472577
      },
      {
        "entry_timestamp_ms": 1721592000000,
        "sleeve": "intraday",
        "direction": 1,
        "parent_pnl": -7.28822033407215,
        "child_pnl": 7.8321631560019425,
        "parent_exit": "signal",
        "child_exit": "time_limit",
        "repriced_parent_qty_delta": 15.15633767954216,
        "quantity_delta": -0.03595418946806728
      },
      {
        "entry_timestamp_ms": 1723032000000,
        "sleeve": "intraday",
        "direction": -1,
        "parent_pnl": -0.9166459228097008,
        "child_pnl": -6.675712698894554,
        "parent_exit": "signal",
        "child_exit": "time_limit",
        "repriced_parent_qty_delta": -5.76837479797249,
        "quantity_delta": 0.009308021887637352
      },
      {
        "entry_timestamp_ms": 1725634800000,
        "sleeve": "intraday",
        "direction": -1,
        "parent_pnl": 4.074871223816952,
        "child_pnl": -0.5533618373815474,
        "parent_exit": "signal",
        "child_exit": "time_limit",
        "repriced_parent_qty_delta": -4.629319236439927,
        "quantity_delta": 0.0010861752414271786
      },
      {
        "entry_timestamp_ms": 1731888000000,
        "sleeve": "intraday",
        "direction": 1,
        "parent_pnl": -11.224996487538853,
        "child_pnl": 4.55682824803724,
        "parent_exit": "signal",
        "child_exit": "time_limit",
        "repriced_parent_qty_delta": 15.79283113099013,
        "quantity_delta": -0.011006395414036696
      },
      {
        "entry_timestamp_ms": 1735596000000,
        "sleeve": "intraday",
        "direction": -1,
        "parent_pnl": -8.1884480835718,
        "child_pnl": -12.514702352585422,
        "parent_exit": "signal",
        "child_exit": "stop_loss",
        "repriced_parent_qty_delta": -4.342910266914126,
        "quantity_delta": 0.01665599790050365
      }
    ]
  }
}
```

## 2024／成本2倍完整指標及共同事件

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding及頻率：

```json
{
  "year": 2024,
  "cost": 2,
  "checks": "passed",
  "metrics": {
    "average_loss": -14.75420097830632,
    "average_win": 27.339520520876814,
    "cagr": 0.002514797160705573,
    "exposure": 0.307455890722823,
    "fees": 296.77431211029995,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.038904499974369955,
    "maximum_margin_ratio": 0.02327816296078867,
    "net_funding": -37.34877616353837,
    "number_of_trades": 101,
    "profit_factor": 1.0262764015990653,
    "sharpe_ratio": 0.09611075674771874,
    "slippage": 148.38766376556993,
    "sortino_ratio": 0.1383423401351971,
    "total_return": 0.0025199675161651225,
    "win_rate": 0.3564356435643564
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
      "pnl": -201.26962182218136
    },
    "intraday/-1/stop_loss": {
      "count": 6,
      "pnl": -106.07649341934635
    },
    "swing/-1/stop_loss": {
      "count": 6,
      "pnl": -83.76734239258967
    },
    "intraday/1/time_limit": {
      "count": 14,
      "pnl": 185.1409123117799
    },
    "swing/1/signal": {
      "count": 11,
      "pnl": -39.678097184258085
    },
    "swing/1/time_limit": {
      "count": 11,
      "pnl": 538.902391041671
    },
    "intraday/1/stop_loss": {
      "count": 20,
      "pnl": -360.36631818146697
    },
    "intraday/-1/signal": {
      "count": 2,
      "pnl": -20.947491626869535
    },
    "intraday/-1/time_limit": {
      "count": 12,
      "pnl": 104.52902921142623
    },
    "swing/-1/signal": {
      "count": 2,
      "pnl": -11.102015024294282
    },
    "intraday/1/signal": {
      "count": 5,
      "pnl": 19.83472224778364
    }
  },
  "past_only_risk_trace_checks": 101,
  "common_events": [
    {
      "entry_timestamp_ms": 1704744000000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -24.483508220879553,
      "child_pnl": -24.483508220879553,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0
    },
    {
      "entry_timestamp_ms": 1706061600000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -23.49702112670379,
      "child_pnl": -23.49702112670379,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0
    },
    {
      "entry_timestamp_ms": 1705968000000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -23.393085151960275,
      "child_pnl": -23.393085151960275,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0
    },
    {
      "entry_timestamp_ms": 1706486400000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 34.67009803555131,
      "child_pnl": 34.67009803555131,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0
    },
    {
      "entry_timestamp_ms": 1706572800000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -12.195555155674795,
      "child_pnl": -12.195555155674795,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0
    },
    {
      "entry_timestamp_ms": 1706443200000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -7.4367912106032,
      "child_pnl": -7.4367912106032,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0
    },
    {
      "entry_timestamp_ms": 1707177600000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 4.333265599998563,
      "child_pnl": 4.333265599998563,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0
    },
    {
      "entry_timestamp_ms": 1707350400000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 72.77308405799236,
      "child_pnl": 72.77308405799236,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0
    },
    {
      "entry_timestamp_ms": 1707364800000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 75.60407299893645,
      "child_pnl": 75.60407299893645,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0
    },
    {
      "entry_timestamp_ms": 1707465600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 45.252157275955426,
      "child_pnl": 45.252157275955426,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0
    },
    {
      "entry_timestamp_ms": 1708398000000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -24.19316924795533,
      "child_pnl": -24.19316924795533,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0
    },
    {
      "entry_timestamp_ms": 1708455600000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -1.603206760031705,
      "child_pnl": -24.365709100694083,
      "parent_exit": "signal",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -22.762502340662376,
      "quantity_delta": -3.552713678800501e-15
    },
    {
      "entry_timestamp_ms": 1709020800000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 108.94097961361538,
      "child_pnl": 108.69584211922947,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -1.4210854715202004e-14,
      "quantity_delta": -0.24513749438590082
    },
    {
      "entry_timestamp_ms": 1709121600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 13.169612002431904,
      "child_pnl": 13.13997792258646,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": -0.029634079845441974
    },
    {
      "entry_timestamp_ms": 1710158400000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -26.366829146398295,
      "child_pnl": -26.307498869997502,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.059330276400793025
    },
    {
      "entry_timestamp_ms": 1710172800000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -25.86352318688376,
      "child_pnl": -25.805325442632608,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -3.552713678800501e-15,
      "quantity_delta": 0.058197744251156536
    },
    {
      "entry_timestamp_ms": 1710270000000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 4.4807671364863815,
      "child_pnl": 4.470684575886499,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": -0.010082560599884438
    },
    {
      "entry_timestamp_ms": 1710450000000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -25.066335473915913,
      "child_pnl": -25.009931550495118,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.056403923420795365
    },
    {
      "entry_timestamp_ms": 1711220400000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -5.659450407330381,
      "child_pnl": -23.19585611860671,
      "parent_exit": "signal",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -17.588718421111295,
      "quantity_delta": 0.052312709834968274
    },
    {
      "entry_timestamp_ms": 1711404000000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -6.814166398622833,
      "child_pnl": -6.787062678870713,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.02710371975211956
    },
    {
      "entry_timestamp_ms": 1712260800000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -0.39761229707456297,
      "child_pnl": 6.632300622967019,
      "parent_exit": "signal",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 7.056398606987768,
      "quantity_delta": -0.02648568694618625
    },
    {
      "entry_timestamp_ms": 1712577600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -12.519126818722054,
      "child_pnl": -12.477998207067602,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.04112861165445203
    },
    {
      "entry_timestamp_ms": 1713830400000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -12.32604357654763,
      "child_pnl": -12.285549293932204,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": 0.04049428261542687
    },
    {
      "entry_timestamp_ms": 1713996000000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -12.07190449438415,
      "child_pnl": -24.064490250477913,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": -11.992585756093765
    },
    {
      "entry_timestamp_ms": 1714154400000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -12.00386086609705,
      "child_pnl": -11.95014638375813,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -3.552713678800501e-15,
      "quantity_delta": 0.05371448233892373
    },
    {
      "entry_timestamp_ms": 1714280400000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 11.798208263386696,
      "child_pnl": 11.745414028559756,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.05279423482694057
    },
    {
      "entry_timestamp_ms": 1714507200000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -3.615794198942827,
      "child_pnl": -3.5996143618215175,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 4.440892098500626e-16,
      "quantity_delta": 0.016179837121308882
    },
    {
      "entry_timestamp_ms": 1715216400000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -11.851067403395767,
      "child_pnl": -11.798036636225266,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.053030767170501036
    },
    {
      "entry_timestamp_ms": 1715259600000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 10.478327947582905,
      "child_pnl": 10.431439869841888,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": -0.046888077741014555
    },
    {
      "entry_timestamp_ms": 1715817600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -3.104938821625538,
      "child_pnl": -3.0910449433676943,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.013893878257843717
    },
    {
      "entry_timestamp_ms": 1716249600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -12.332403709574534,
      "child_pnl": -12.277219074510546,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": 0.05518463506398952
    },
    {
      "entry_timestamp_ms": 1716501600000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 4.821936309753143,
      "child_pnl": 4.800359267529904,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 8.881784197001252e-16,
      "quantity_delta": -0.02157704222323975
    },
    {
      "entry_timestamp_ms": 1716926400000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -13.549341976679688,
      "child_pnl": -13.48871182622818,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": 0.060630150451510545
    },
    {
      "entry_timestamp_ms": 1717426800000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -14.092606984603808,
      "child_pnl": -15.575332556117402,
      "parent_exit": "signal",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -1.5527348332114794,
      "quantity_delta": 0.07000926169788535
    },
    {
      "entry_timestamp_ms": 1718121600000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -12.055775042107495,
      "child_pnl": -11.999977990900263,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.05579705120723233
    },
    {
      "entry_timestamp_ms": 1718107200000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -11.950556931869977,
      "child_pnl": -11.895246855599183,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": 0.05531007627079276
    },
    {
      "entry_timestamp_ms": 1719244800000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -12.006720522055414,
      "child_pnl": -11.9511505070659,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.055570014989513083
    },
    {
      "entry_timestamp_ms": 1720090800000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -12.030611086242608,
      "child_pnl": -11.974930499927018,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.055680586315590475
    },
    {
      "entry_timestamp_ms": 1720166400000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -12.295009496497373,
      "child_pnl": -12.238105210205251,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": 0.056904286292120076
    },
    {
      "entry_timestamp_ms": 1720314000000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 32.52407310418433,
      "child_pnl": 32.37354380464752,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 7.105427357601002e-15,
      "quantity_delta": -0.15052929953682082
    },
    {
      "entry_timestamp_ms": 1720512000000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -23.69386124940037,
      "child_pnl": -23.601215884366344,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0926453650340271
    },
    {
      "entry_timestamp_ms": 1720436400000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -13.670474418542861,
      "child_pnl": -13.046617771982975,
      "parent_exit": "signal",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.5631929686384325,
      "quantity_delta": 0.060663677921453996
    },
    {
      "entry_timestamp_ms": 1721088000000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -12.238823700057617,
      "child_pnl": -12.18284427613835,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.05597942391926658
    },
    {
      "entry_timestamp_ms": 1721102400000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -0.5664422080168532,
      "child_pnl": -0.5638513455887849,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0025908624280682746
    },
    {
      "entry_timestamp_ms": 1720958400000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 19.70224399328844,
      "child_pnl": 19.61212746773901,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.09011652554942984
    },
    {
      "entry_timestamp_ms": 1721016000000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 2.9171926520474694,
      "child_pnl": 2.9038496406498653,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 8.881784197001252e-16,
      "quantity_delta": -0.013343011397604965
    },
    {
      "entry_timestamp_ms": 1721030400000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 1.765219035720118,
      "child_pnl": 1.7571450616902047,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": -8.881784197001252e-16,
      "quantity_delta": -0.0080739740299125
    },
    {
      "entry_timestamp_ms": 1721336400000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 32.78622979285894,
      "child_pnl": 32.636268137942686,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -7.105427357601002e-15,
      "quantity_delta": -0.1499616549162468
    },
    {
      "entry_timestamp_ms": 1721592000000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -8.879853051334727,
      "child_pnl": 4.54683140000261,
      "parent_exit": "signal",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 13.447576863376838,
      "quantity_delta": -0.020892412039500208
    },
    {
      "entry_timestamp_ms": 1721725200000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -23.591027121604775,
      "child_pnl": -23.51457003787643,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 3.552713678800501e-15,
      "quantity_delta": 0.07645708372833937
    },
    {
      "entry_timestamp_ms": 1721919600000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 13.402550988719755,
      "child_pnl": 26.71822827263337,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 13.315677283913617
    },
    {
      "entry_timestamp_ms": 1722027600000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -11.844621803161436,
      "child_pnl": -11.822006991136785,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.022614812024650988
    },
    {
      "entry_timestamp_ms": 1722117600000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -11.71328140343668,
      "child_pnl": -11.690917358257979,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": 0.02236404517870305
    },
    {
      "entry_timestamp_ms": 1722279600000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -11.96419780226028,
      "child_pnl": -11.941354685036265,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -3.552713678800501e-15,
      "quantity_delta": 0.022843117224018883
    },
    {
      "entry_timestamp_ms": 1722376800000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -12.01138137282867,
      "child_pnl": -11.988448168508846,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 3.552713678800501e-15,
      "quantity_delta": 0.022933204319819822
    },
    {
      "entry_timestamp_ms": 1722844800000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -12.31328630509539,
      "child_pnl": -12.289776676858793,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": 0.02350962823659586
    },
    {
      "entry_timestamp_ms": 1723032000000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -2.597228470253322,
      "child_pnl": -7.41109348186922,
      "parent_exit": "signal",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -4.828042002554511,
      "quantity_delta": 0.01417699093861291
    },
    {
      "entry_timestamp_ms": 1723165200000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 1.9614757784532124,
      "child_pnl": 1.9567826666959263,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 2.220446049250313e-16,
      "quantity_delta": -0.004693111757286372
    },
    {
      "entry_timestamp_ms": 1723255200000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -14.1943910617865,
      "child_pnl": -14.160428947998824,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 3.552713678800501e-15,
      "quantity_delta": 0.03396211378767333
    },
    {
      "entry_timestamp_ms": 1723712400000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -11.725266351208933,
      "child_pnl": -11.697211971963137,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.028054379245796568
    },
    {
      "entry_timestamp_ms": 1723759200000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 0.7187955630162586,
      "child_pnl": 0.7170757416730975,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.0017198213431610654
    },
    {
      "entry_timestamp_ms": 1723989600000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 35.65586121070495,
      "child_pnl": 35.570549455493726,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.08531175521122236
    },
    {
      "entry_timestamp_ms": 1724691600000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -23.475290825396524,
      "child_pnl": -23.419122829549387,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.05616799584713661
    },
    {
      "entry_timestamp_ms": 1724457600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -14.609594599097314,
      "child_pnl": -14.574639051373806,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.03495554772350751
    },
    {
      "entry_timestamp_ms": 1724950800000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 26.68040670200886,
      "child_pnl": 26.6165700073334,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -3.552713678800501e-15,
      "quantity_delta": -0.06383669467545516
    },
    {
      "entry_timestamp_ms": 1725336000000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 47.160414746098546,
      "child_pnl": 47.04757669866773,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.11283804743081305
    },
    {
      "entry_timestamp_ms": 1725634800000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 2.2049445716094334,
      "child_pnl": -2.0345394837709536,
      "parent_exit": "signal",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -4.244363657665538,
      "quantity_delta": 0.004879602285150941
    },
    {
      "entry_timestamp_ms": 1725652800000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -7.520394282999049,
      "child_pnl": -7.5024006624727635,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.01799362052628517
    },
    {
      "entry_timestamp_ms": 1726682400000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 65.94349974179917,
      "child_pnl": 65.75783324708681,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -1.4210854715202004e-14,
      "quantity_delta": -0.18566649471235053
    },
    {
      "entry_timestamp_ms": 1726761600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 7.300470025383419,
      "child_pnl": 7.279915267375836,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.020554758007582663
    },
    {
      "entry_timestamp_ms": 1726776000000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 4.460440522911579,
      "child_pnl": 4.447881978703206,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": -0.012558544208371103
    },
    {
      "entry_timestamp_ms": 1727319600000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 25.325781064244165,
      "child_pnl": 25.254475340185536,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 3.552713678800501e-15,
      "quantity_delta": -0.07130572405863234
    },
    {
      "entry_timestamp_ms": 1727697600000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -23.85914633176395,
      "child_pnl": -23.791969974979857,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -7.105427357601002e-15,
      "quantity_delta": 0.06717635678409906
    },
    {
      "entry_timestamp_ms": 1728892800000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 47.924771855584794,
      "child_pnl": 47.789837791800565,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.1349340637842289
    },
    {
      "entry_timestamp_ms": 1728907200000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 38.83545848771781,
      "child_pnl": 38.726115740120356,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 7.105427357601002e-15,
      "quantity_delta": -0.10934274759745932
    },
    {
      "entry_timestamp_ms": 1729562400000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -10.478053961827792,
      "child_pnl": -10.448552592350637,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": 0.02950136947715265
    },
    {
      "entry_timestamp_ms": 1729713600000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 1.6785160830383155,
      "child_pnl": 1.6737901555598484,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": -2.220446049250313e-16,
      "quantity_delta": -0.004725927478466785
    },
    {
      "entry_timestamp_ms": 1730232000000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -25.078619710432772,
      "child_pnl": -25.0080098788028,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 7.105427357601002e-15,
      "quantity_delta": 0.07060983162996592
    },
    {
      "entry_timestamp_ms": 1730246400000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -25.014715851497726,
      "child_pnl": -24.944285943674245,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.07042990782348113
    },
    {
      "entry_timestamp_ms": 1730188800000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -10.710930143320374,
      "child_pnl": -10.680773101874207,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": 0.030157041446168265
    },
    {
      "entry_timestamp_ms": 1730412000000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -23.994276510179766,
      "child_pnl": -23.926719689109525,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.06755682107024086
    },
    {
      "entry_timestamp_ms": 1731225600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 59.612165238728124,
      "child_pnl": 59.44432486317298,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -7.105427357601002e-15,
      "quantity_delta": -0.1678403755551372
    },
    {
      "entry_timestamp_ms": 1731240000000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 52.61831756606249,
      "child_pnl": 52.4701686413254,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.14814892473708596
    },
    {
      "entry_timestamp_ms": 1731340800000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 26.493584025889646,
      "child_pnl": 26.418990307058944,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.07459371883070176
    },
    {
      "entry_timestamp_ms": 1731888000000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -13.100951136484483,
      "child_pnl": -0.09298044381822246,
      "parent_exit": "signal",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 13.007708163440036,
      "quantity_delta": 0.00026252922622398145
    },
    {
      "entry_timestamp_ms": 1732291200000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -5.2758655877427385,
      "child_pnl": -5.267713552645133,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.008152035097605648
    },
    {
      "entry_timestamp_ms": 1732176000000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -11.984633674444364,
      "child_pnl": -11.966115546428933,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": 0.018518128015433177
    },
    {
      "entry_timestamp_ms": 1732190400000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -19.30985148994859,
      "child_pnl": -19.280014758049784,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": -3.552713678800501e-15,
      "quantity_delta": 0.029836731898807756
    },
    {
      "entry_timestamp_ms": 1733148000000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -12.05096852729094,
      "child_pnl": -12.03234790158302,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.018620625707921334
    },
    {
      "entry_timestamp_ms": 1733371200000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -12.757688731918577,
      "child_pnl": -12.737976113282388,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.01971261863618956
    },
    {
      "entry_timestamp_ms": 1733720400000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -11.946679950324107,
      "child_pnl": -11.928220466731275,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -3.552713678800501e-15,
      "quantity_delta": 0.018459483592835113
    },
    {
      "entry_timestamp_ms": 1733752800000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -11.954468538845433,
      "child_pnl": -11.935997020668715,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": 0.018471518176719215
    },
    {
      "entry_timestamp_ms": 1733860800000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 25.779654371133823,
      "child_pnl": 25.739820784826026,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.039833586307796764
    },
    {
      "entry_timestamp_ms": 1734508800000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -24.089800701596946,
      "child_pnl": -24.05257820273911,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.03722249885783668
    },
    {
      "entry_timestamp_ms": 1734321600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -10.07738980402939,
      "child_pnl": -10.061818665226008,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.015571138803382567
    },
    {
      "entry_timestamp_ms": 1734580800000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -24.634938066694367,
      "child_pnl": -24.596873245593983,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -3.552713678800501e-15,
      "quantity_delta": 0.038064821100388
    },
    {
      "entry_timestamp_ms": 1734645600000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -12.203346390864855,
      "child_pnl": -12.18449031759458,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": 0.018856073270272944
    },
    {
      "entry_timestamp_ms": 1734703200000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 4.220861793855047,
      "child_pnl": 4.214339904145499,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.006521889709548034
    },
    {
      "entry_timestamp_ms": 1735070400000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -19.376063819471945,
      "child_pnl": -19.346124779198288,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.029939040273657014
    },
    {
      "entry_timestamp_ms": 1735164000000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -23.623630196030387,
      "child_pnl": -11.793564001651177,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 3.552713678800501e-15,
      "quantity_delta": 11.830066194379206
    },
    {
      "entry_timestamp_ms": 1735596000000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -8.281815600391742,
      "child_pnl": -12.16682929688155,
      "parent_exit": "signal",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -3.8895247050644404,
      "quantity_delta": 0.004511008574631603
    }
  ],
  "channel_only_comparison": {
    "count": 10,
    "parent_pnl": -66.07825455443816,
    "child_pnl": -86.70982623077148,
    "new_exit_counts": {
      "stop_loss": 3,
      "time_limit": 7
    },
    "events": [
      {
        "entry_timestamp_ms": 1708455600000,
        "sleeve": "intraday",
        "direction": 1,
        "parent_pnl": -1.603206760031705,
        "child_pnl": -24.365709100694083,
        "parent_exit": "signal",
        "child_exit": "stop_loss",
        "repriced_parent_qty_delta": -22.762502340662376,
        "quantity_delta": -3.552713678800501e-15
      },
      {
        "entry_timestamp_ms": 1711220400000,
        "sleeve": "intraday",
        "direction": -1,
        "parent_pnl": -5.659450407330381,
        "child_pnl": -23.19585611860671,
        "parent_exit": "signal",
        "child_exit": "stop_loss",
        "repriced_parent_qty_delta": -17.588718421111295,
        "quantity_delta": 0.052312709834968274
      },
      {
        "entry_timestamp_ms": 1712260800000,
        "sleeve": "intraday",
        "direction": -1,
        "parent_pnl": -0.39761229707456297,
        "child_pnl": 6.632300622967019,
        "parent_exit": "signal",
        "child_exit": "time_limit",
        "repriced_parent_qty_delta": 7.056398606987768,
        "quantity_delta": -0.02648568694618625
      },
      {
        "entry_timestamp_ms": 1717426800000,
        "sleeve": "intraday",
        "direction": -1,
        "parent_pnl": -14.092606984603808,
        "child_pnl": -15.575332556117402,
        "parent_exit": "signal",
        "child_exit": "time_limit",
        "repriced_parent_qty_delta": -1.5527348332114794,
        "quantity_delta": 0.07000926169788535
      },
      {
        "entry_timestamp_ms": 1720436400000,
        "sleeve": "intraday",
        "direction": -1,
        "parent_pnl": -13.670474418542861,
        "child_pnl": -13.046617771982975,
        "parent_exit": "signal",
        "child_exit": "time_limit",
        "repriced_parent_qty_delta": 0.5631929686384325,
        "quantity_delta": 0.060663677921453996
      },
      {
        "entry_timestamp_ms": 1721592000000,
        "sleeve": "intraday",
        "direction": 1,
        "parent_pnl": -8.879853051334727,
        "child_pnl": 4.54683140000261,
        "parent_exit": "signal",
        "child_exit": "time_limit",
        "repriced_parent_qty_delta": 13.447576863376838,
        "quantity_delta": -0.020892412039500208
      },
      {
        "entry_timestamp_ms": 1723032000000,
        "sleeve": "intraday",
        "direction": -1,
        "parent_pnl": -2.597228470253322,
        "child_pnl": -7.41109348186922,
        "parent_exit": "signal",
        "child_exit": "time_limit",
        "repriced_parent_qty_delta": -4.828042002554511,
        "quantity_delta": 0.01417699093861291
      },
      {
        "entry_timestamp_ms": 1725634800000,
        "sleeve": "intraday",
        "direction": -1,
        "parent_pnl": 2.2049445716094334,
        "child_pnl": -2.0345394837709536,
        "parent_exit": "signal",
        "child_exit": "time_limit",
        "repriced_parent_qty_delta": -4.244363657665538,
        "quantity_delta": 0.004879602285150941
      },
      {
        "entry_timestamp_ms": 1731888000000,
        "sleeve": "intraday",
        "direction": 1,
        "parent_pnl": -13.100951136484483,
        "child_pnl": -0.09298044381822246,
        "parent_exit": "signal",
        "child_exit": "time_limit",
        "repriced_parent_qty_delta": 13.007708163440036,
        "quantity_delta": 0.00026252922622398145
      },
      {
        "entry_timestamp_ms": 1735596000000,
        "sleeve": "intraday",
        "direction": -1,
        "parent_pnl": -8.281815600391742,
        "child_pnl": -12.16682929688155,
        "parent_exit": "signal",
        "child_exit": "stop_loss",
        "repriced_parent_qty_delta": -3.8895247050644404,
        "quantity_delta": 0.004511008574631603
      }
    ]
  }
}
```

## 2025／成本1倍完整指標及共同事件

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding及頻率：

```json
{
  "year": 2025,
  "cost": 1,
  "checks": "passed",
  "metrics": {
    "average_loss": -13.1642799744639,
    "average_win": 22.408130055032185,
    "cagr": -0.02298090226273153,
    "exposure": 0.24837347334779133,
    "fees": 138.05431365194647,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.046091323676200946,
    "maximum_margin_ratio": 0.022656983414202806,
    "net_funding": -5.022241371356488,
    "number_of_trades": 85,
    "profit_factor": 0.7092466032608545,
    "sharpe_ratio": -0.9313074024783559,
    "slippage": 69.02715243850565,
    "sortino_ratio": -1.3172013249815806,
    "total_return": -0.022965354709202024,
    "win_rate": 0.29411764705882354
  },
  "frequency": {
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
    "swing/1/stop_loss": {
      "count": 12,
      "pnl": -180.12620353873797
    },
    "intraday/1/stop_loss": {
      "count": 9,
      "pnl": -138.81240931811104
    },
    "intraday/-1/time_limit": {
      "count": 13,
      "pnl": 290.1870201914083
    },
    "swing/1/signal": {
      "count": 9,
      "pnl": 57.955229422719896
    },
    "intraday/1/time_limit": {
      "count": 4,
      "pnl": 11.672843969722601
    },
    "intraday/-1/stop_loss": {
      "count": 14,
      "pnl": -216.4185384347257
    },
    "intraday/1/signal": {
      "count": 2,
      "pnl": -17.285630636704933
    },
    "swing/-1/signal": {
      "count": 8,
      "pnl": 23.145287208184364
    },
    "swing/-1/stop_loss": {
      "count": 10,
      "pnl": -153.01164373122236
    },
    "swing/1/time_limit": {
      "count": 2,
      "pnl": 65.0031919532669
    },
    "intraday/-1/signal": {
      "count": 1,
      "pnl": -9.229896807559102
    },
    "swing/-1/time_limit": {
      "count": 1,
      "pnl": 37.26720262972971
    }
  },
  "past_only_risk_trace_checks": 85,
  "common_events": [
    {
      "entry_timestamp_ms": 1736150400000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -24.19673620982446,
      "child_pnl": -24.19673620982446,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0
    },
    {
      "entry_timestamp_ms": 1736326800000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -22.70615687998392,
      "child_pnl": -22.70615687998392,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0
    },
    {
      "entry_timestamp_ms": 1736438400000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -24.05155131058018,
      "child_pnl": -24.05155131058018,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0
    },
    {
      "entry_timestamp_ms": 1736733600000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 2.0940449817480125,
      "child_pnl": -5.159221207000065,
      "parent_exit": "signal",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -7.253266188748077,
      "quantity_delta": 0.0
    },
    {
      "entry_timestamp_ms": 1737129600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -24.58120160057521,
      "child_pnl": -24.563248575482515,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -3.552713678800501e-15,
      "quantity_delta": 0.017953025092698027
    },
    {
      "entry_timestamp_ms": 1737100800000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -3.4968602307058805,
      "child_pnl": -3.494306278279648,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": -4.440892098500626e-16,
      "quantity_delta": 0.0025539524262327973
    },
    {
      "entry_timestamp_ms": 1737428400000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 11.620852101266324,
      "child_pnl": 11.612364743619505,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.008487357646819405
    },
    {
      "entry_timestamp_ms": 1737568800000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -23.21603509417241,
      "child_pnl": -23.19907912646296,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.016955967709449737
    },
    {
      "entry_timestamp_ms": 1738029600000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -23.433757001313683,
      "child_pnl": -23.416642019129448,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.017114982184235572
    },
    {
      "entry_timestamp_ms": 1738476000000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -7.063576502737188,
      "child_pnl": -7.05841757811428,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": -8.881784197001252e-16,
      "quantity_delta": 0.005158924622908678
    },
    {
      "entry_timestamp_ms": 1738627200000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 25.888470157367532,
      "child_pnl": 25.869562360999435,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.01890779636809725
    },
    {
      "entry_timestamp_ms": 1740427200000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": 38.862117010674694,
      "child_pnl": 38.833733835060045,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.028383175614649758
    },
    {
      "entry_timestamp_ms": 1740484800000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": 5.530877704056257,
      "child_pnl": 5.52683819501113,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.0040395090451275095
    },
    {
      "entry_timestamp_ms": 1741564800000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -24.22254640730377,
      "child_pnl": -24.204855328139857,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.01769107916391377
    },
    {
      "entry_timestamp_ms": 1741698000000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -23.03431272799101,
      "child_pnl": -23.017489482279966,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.016823245711044876
    },
    {
      "entry_timestamp_ms": 1741651200000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -24.24053773803361,
      "child_pnl": -24.222833518795532,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.017704219238076746
    },
    {
      "entry_timestamp_ms": 1741748400000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -23.371368224180745,
      "child_pnl": -23.354298808006632,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.017069416174113172
    },
    {
      "entry_timestamp_ms": 1742284800000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -11.476219589850757,
      "child_pnl": -11.467837865408882,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": 0.008381724441873573
    },
    {
      "entry_timestamp_ms": 1742428800000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -11.919154123699617,
      "child_pnl": -11.910448899417098,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.008705224282518742
    },
    {
      "entry_timestamp_ms": 1742569200000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -4.206584493338578,
      "child_pnl": -4.203512189624923,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.003072303713655522
    },
    {
      "entry_timestamp_ms": 1742817600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -11.58601481170551,
      "child_pnl": -11.57755289767791,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": 0.008461914027602546
    },
    {
      "entry_timestamp_ms": 1743022800000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -4.252408846819979,
      "child_pnl": -11.692341317909648,
      "parent_exit": "signal",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -7.44847828278994,
      "quantity_delta": 0.008545811700271244
    },
    {
      "entry_timestamp_ms": 1742803200000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -11.533134100261956,
      "child_pnl": -11.524710807972824,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": 0.008423292289130302
    },
    {
      "entry_timestamp_ms": 1743440400000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -5.198252927434967,
      "child_pnl": -11.100096879647683,
      "parent_exit": "signal",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -5.918422173837947,
      "quantity_delta": 0.016578221625231038
    },
    {
      "entry_timestamp_ms": 1743555600000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -11.170378156854575,
      "child_pnl": -11.146967494997803,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.023410661856772208
    },
    {
      "entry_timestamp_ms": 1743764400000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -6.4040512776580245,
      "child_pnl": -6.3906297912168775,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.013421486441147046
    },
    {
      "entry_timestamp_ms": 1743998400000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -11.825143200417688,
      "child_pnl": -11.800360294683834,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": 0.024782905733855998
    },
    {
      "entry_timestamp_ms": 1744412400000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -11.298396644752223,
      "child_pnl": -11.274717684231842,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": 0.02367896052038354
    },
    {
      "entry_timestamp_ms": 1744772400000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 1.1220785154796593,
      "child_pnl": 1.1197268850931343,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 4.440892098500626e-16,
      "quantity_delta": -0.0023516303865254162
    },
    {
      "entry_timestamp_ms": 1745611200000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -2.754202325562586,
      "child_pnl": -2.748430121755009,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 8.881784197001252e-16,
      "quantity_delta": 0.005772203807576037
    },
    {
      "entry_timestamp_ms": 1745222400000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 49.480056737686446,
      "child_pnl": 49.37635739459582,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 7.105427357601002e-15,
      "quantity_delta": -0.10369934309063211
    },
    {
      "entry_timestamp_ms": 1745352000000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 15.659653757247648,
      "child_pnl": 15.626834558671083,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.0328191985765649
    },
    {
      "entry_timestamp_ms": 1746586800000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -11.434902855180681,
      "child_pnl": -11.41093780759244,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.02396504758824136
    },
    {
      "entry_timestamp_ms": 1746684000000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -9.249281271829911,
      "child_pnl": -9.229896807559102,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.019384464270808976
    },
    {
      "entry_timestamp_ms": 1746705600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 25.424950224407038,
      "child_pnl": 25.371665106923025,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 3.552713678800501e-15,
      "quantity_delta": -0.0532851174840161
    },
    {
      "entry_timestamp_ms": 1747324800000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 3.150868058791576,
      "child_pnl": 3.1442645306348846,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -4.440892098500626e-16,
      "quantity_delta": -0.006603528156690963
    },
    {
      "entry_timestamp_ms": 1749513600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -23.435418745445077,
      "child_pnl": -23.386303249441497,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 3.552713678800501e-15,
      "quantity_delta": 0.04911549600357645
    },
    {
      "entry_timestamp_ms": 1750118400000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 9.165499883193212,
      "child_pnl": 9.146291006331507,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": -0.019208876861705804
    },
    {
      "entry_timestamp_ms": 1750622400000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -11.865751963840905,
      "child_pnl": -11.840883951048395,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": 0.024868012792508054
    },
    {
      "entry_timestamp_ms": 1750694400000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -22.861752781767027,
      "child_pnl": -22.81383956376207,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 3.552713678800501e-15,
      "quantity_delta": 0.04791321800495396
    },
    {
      "entry_timestamp_ms": 1752480000000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -11.68977859703903,
      "child_pnl": -11.665279385815108,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0244992112239224
    },
    {
      "entry_timestamp_ms": 1752192000000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 2.8327921118672976,
      "child_pnl": 2.8268552011100923,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": -4.440892098500626e-16,
      "quantity_delta": -0.005936910757204927
    },
    {
      "entry_timestamp_ms": 1752206400000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -0.45678866487586145,
      "child_pnl": -0.45583133605285703,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": -1.6653345369377348e-16,
      "quantity_delta": 0.0009573288230045884
    },
    {
      "entry_timestamp_ms": 1753909200000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 2.436933179845871,
      "child_pnl": -10.227213058590653,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": -12.685625248468561,
      "quantity_delta": 0.021479010032036783
    },
    {
      "entry_timestamp_ms": 1754092800000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -4.825077689470639,
      "child_pnl": -4.808701349242637,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": -8.881784197001252e-16,
      "quantity_delta": 0.016376340228003272
    },
    {
      "entry_timestamp_ms": 1754884800000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -11.673138291083886,
      "child_pnl": -11.63351959549262,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.03961869559126541
    },
    {
      "entry_timestamp_ms": 1755144000000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -11.706220989259455,
      "child_pnl": -11.666490010808541,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": 0.03973097845091189
    },
    {
      "entry_timestamp_ms": 1755129600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -11.777727932333747,
      "child_pnl": -11.737754258924577,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": 0.039973673409171795
    },
    {
      "entry_timestamp_ms": 1755504000000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -11.392702204916043,
      "child_pnl": -11.354035310944322,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.03866689397172074
    },
    {
      "entry_timestamp_ms": 1755716400000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -22.315407978297515,
      "child_pnl": -11.119834680414428,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -3.552713678800501e-15,
      "quantity_delta": 11.19557329788309
    },
    {
      "entry_timestamp_ms": 1755633600000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -11.442395774844197,
      "child_pnl": -11.403560220622703,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": 0.03883555422149243
    },
    {
      "entry_timestamp_ms": 1755648000000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -11.474991747108993,
      "child_pnl": -11.436045561978267,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": 0.03894618513072423
    },
    {
      "entry_timestamp_ms": 1756256400000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -11.097399197652287,
      "child_pnl": -11.07251639067736,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": 0.024882806974925842
    },
    {
      "entry_timestamp_ms": 1756180800000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -11.56586926883324,
      "child_pnl": -11.539936049041119,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": 0.025933219792118933
    },
    {
      "entry_timestamp_ms": 1756724400000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -11.220271456910158,
      "child_pnl": -11.19511314333632,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.025158313573838242
    },
    {
      "entry_timestamp_ms": 1757098800000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -9.777045952603094,
      "child_pnl": -11.181011923809272,
      "parent_exit": "signal",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -1.4290925956940654,
      "quantity_delta": 0.025126624487887383
    },
    {
      "entry_timestamp_ms": 1758916800000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -4.347177480229282,
      "child_pnl": -4.3367851903852745,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 8.881784197001252e-16,
      "quantity_delta": 0.010392289844006974
    },
    {
      "entry_timestamp_ms": 1758844800000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -5.756249799032613,
      "child_pnl": -5.742489004448515,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": -8.881784197001252e-16,
      "quantity_delta": 0.013760794584098512
    },
    {
      "entry_timestamp_ms": 1759334400000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 17.3577624024278,
      "child_pnl": 17.316267225672338,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.041495176755461216
    },
    {
      "entry_timestamp_ms": 1759348800000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 16.49957648311389,
      "child_pnl": 16.46013287127708,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 3.552713678800501e-15,
      "quantity_delta": -0.03944361183681622
    },
    {
      "entry_timestamp_ms": 1759377600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 11.227991279922481,
      "child_pnl": 11.201149831585571,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": -0.02684144833691171
    },
    {
      "entry_timestamp_ms": 1759435200000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 1.9544937635800603,
      "child_pnl": 1.9498213834479394,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 4.440892098500626e-16,
      "quantity_delta": -0.004672380132121345
    },
    {
      "entry_timestamp_ms": 1760277600000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -11.103696946063236,
      "child_pnl": -11.077152633683923,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.026544312379312984
    },
    {
      "entry_timestamp_ms": 1760155200000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -4.7033701024611965,
      "child_pnl": -4.692126304486369,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.011243797974827885
    },
    {
      "entry_timestamp_ms": 1760328000000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -9.776316208985953,
      "child_pnl": 7.404571527277099,
      "parent_exit": "signal",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 17.19863139893114,
      "quantity_delta": -0.017743662668089577
    },
    {
      "entry_timestamp_ms": 1760500800000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 2.161591521212871,
      "child_pnl": 4.320556920890022,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 2.1589653996771507
    },
    {
      "entry_timestamp_ms": 1760623200000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 70.16636594934687,
      "child_pnl": 70.13949295424743,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.026872995099438413
    },
    {
      "entry_timestamp_ms": 1760644800000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": 0.23422112370403952,
      "child_pnl": 0.23413141942729218,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 8.326672684688674e-17,
      "quantity_delta": -8.970427674742654e-05
    },
    {
      "entry_timestamp_ms": 1760659200000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": 0.18259548680474053,
      "child_pnl": 0.18252555461492717,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 2.7755575615628914e-17,
      "quantity_delta": -6.9932189813382e-05
    },
    {
      "entry_timestamp_ms": 1761069600000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 28.909995510950314,
      "child_pnl": 38.79178040132277,
      "parent_exit": "signal",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 9.896647434721078,
      "quantity_delta": -0.014862544348623885
    },
    {
      "entry_timestamp_ms": 1761537600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -23.500820636596305,
      "child_pnl": -23.515729526125835,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.01490888952952929
    },
    {
      "entry_timestamp_ms": 1761494400000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -13.212142817034982,
      "child_pnl": -13.220524582963645,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": -0.008381765928660911
    },
    {
      "entry_timestamp_ms": 1761930000000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -16.069529141286974,
      "child_pnl": -16.07972362932054,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.010194488033565818
    },
    {
      "entry_timestamp_ms": 1762286400000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -11.757706229644437,
      "child_pnl": -11.765165302925704,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.007459073281266271
    },
    {
      "entry_timestamp_ms": 1762376400000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 56.340126931612886,
      "child_pnl": 56.37586903362248,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -7.105427357601002e-15,
      "quantity_delta": 0.03574210200959982
    },
    {
      "entry_timestamp_ms": 1762560000000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 15.289052815511457,
      "child_pnl": 15.298752170396218,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": 0.009699354884762812
    },
    {
      "entry_timestamp_ms": 1763622000000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 94.7463966455243,
      "child_pnl": 94.8065036342441,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -1.4210854715202004e-14,
      "quantity_delta": 0.06010698871980935
    },
    {
      "entry_timestamp_ms": 1763121600000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": 37.24357535478321,
      "child_pnl": 37.26720262972971,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.023627274946498744
    },
    {
      "entry_timestamp_ms": 1763712000000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -6.384574771960451,
      "child_pnl": -6.388625137751507,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": -8.881784197001252e-16,
      "quantity_delta": -0.004050365791055555
    },
    {
      "entry_timestamp_ms": 1764572400000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -22.520215196183173,
      "child_pnl": -11.267250995459136,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 11.252964200724037
    },
    {
      "entry_timestamp_ms": 1764748800000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -22.889920967632523,
      "child_pnl": -22.93066843494878,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -3.552713678800501e-15,
      "quantity_delta": -0.04074746731625467
    },
    {
      "entry_timestamp_ms": 1764882000000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -10.111107040077716,
      "child_pnl": -11.766880576665876,
      "parent_exit": "signal",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -1.6348639593958438,
      "quantity_delta": -0.020909577192316675
    },
    {
      "entry_timestamp_ms": 1765429200000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -11.46181090213197,
      "child_pnl": -11.480299321831149,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.018488419699178138
    },
    {
      "entry_timestamp_ms": 1765893600000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -11.469762166568445,
      "child_pnl": -11.488263412017004,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": -0.0185012454485598
    },
    {
      "entry_timestamp_ms": 1765828800000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -23.40621291234684,
      "child_pnl": -23.44396819304262,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -3.552713678800501e-15,
      "quantity_delta": -0.03775528069577305
    }
  ],
  "channel_only_comparison": {
    "count": 8,
    "parent_pnl": -5.6741573033775135,
    "child_pnl": -14.930413035023332,
    "new_exit_counts": {
      "time_limit": 3,
      "stop_loss": 4,
      "signal": 1
    },
    "events": [
      {
        "entry_timestamp_ms": 1736733600000,
        "sleeve": "intraday",
        "direction": -1,
        "parent_pnl": 2.0940449817480125,
        "child_pnl": -5.159221207000065,
        "parent_exit": "signal",
        "child_exit": "time_limit",
        "repriced_parent_qty_delta": -7.253266188748077,
        "quantity_delta": 0.0
      },
      {
        "entry_timestamp_ms": 1743022800000,
        "sleeve": "intraday",
        "direction": 1,
        "parent_pnl": -4.252408846819979,
        "child_pnl": -11.692341317909648,
        "parent_exit": "signal",
        "child_exit": "stop_loss",
        "repriced_parent_qty_delta": -7.44847828278994,
        "quantity_delta": 0.008545811700271244
      },
      {
        "entry_timestamp_ms": 1743440400000,
        "sleeve": "intraday",
        "direction": -1,
        "parent_pnl": -5.198252927434967,
        "child_pnl": -11.100096879647683,
        "parent_exit": "signal",
        "child_exit": "stop_loss",
        "repriced_parent_qty_delta": -5.918422173837947,
        "quantity_delta": 0.016578221625231038
      },
      {
        "entry_timestamp_ms": 1753909200000,
        "sleeve": "intraday",
        "direction": 1,
        "parent_pnl": 2.436933179845871,
        "child_pnl": -10.227213058590653,
        "parent_exit": "signal",
        "child_exit": "signal",
        "repriced_parent_qty_delta": -12.685625248468561,
        "quantity_delta": 0.021479010032036783
      },
      {
        "entry_timestamp_ms": 1757098800000,
        "sleeve": "intraday",
        "direction": 1,
        "parent_pnl": -9.777045952603094,
        "child_pnl": -11.181011923809272,
        "parent_exit": "signal",
        "child_exit": "stop_loss",
        "repriced_parent_qty_delta": -1.4290925956940654,
        "quantity_delta": 0.025126624487887383
      },
      {
        "entry_timestamp_ms": 1760328000000,
        "sleeve": "intraday",
        "direction": -1,
        "parent_pnl": -9.776316208985953,
        "child_pnl": 7.404571527277099,
        "parent_exit": "signal",
        "child_exit": "time_limit",
        "repriced_parent_qty_delta": 17.19863139893114,
        "quantity_delta": -0.017743662668089577
      },
      {
        "entry_timestamp_ms": 1761069600000,
        "sleeve": "intraday",
        "direction": -1,
        "parent_pnl": 28.909995510950314,
        "child_pnl": 38.79178040132277,
        "parent_exit": "signal",
        "child_exit": "time_limit",
        "repriced_parent_qty_delta": 9.896647434721078,
        "quantity_delta": -0.014862544348623885
      },
      {
        "entry_timestamp_ms": 1764882000000,
        "sleeve": "intraday",
        "direction": 1,
        "parent_pnl": -10.111107040077716,
        "child_pnl": -11.766880576665876,
        "parent_exit": "signal",
        "child_exit": "stop_loss",
        "repriced_parent_qty_delta": -1.6348639593958438,
        "quantity_delta": -0.020909577192316675
      }
    ]
  }
}
```

## 2025／成本2倍完整指標及共同事件

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding及頻率：

```json
{
  "year": 2025,
  "cost": 2,
  "checks": "passed",
  "metrics": {
    "average_loss": -12.680370938297596,
    "average_win": 19.532710046813587,
    "cagr": -0.03693918578822575,
    "exposure": 0.24837347334779133,
    "fees": 230.84399907016356,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.051808404703583166,
    "maximum_margin_ratio": 0.022681181786137806,
    "net_funding": -4.025296543916897,
    "number_of_trades": 85,
    "profit_factor": 0.5379137880701224,
    "sharpe_ratio": -1.7512652248640301,
    "slippage": 115.42198068260338,
    "sortino_ratio": -2.4203333319702622,
    "total_return": -0.036914374808280304,
    "win_rate": 0.25882352941176473
  },
  "frequency": {
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
    "swing/1/stop_loss": {
      "count": 12,
      "pnl": -177.51715925670595
    },
    "intraday/1/stop_loss": {
      "count": 9,
      "pnl": -139.75703408388537
    },
    "intraday/-1/time_limit": {
      "count": 13,
      "pnl": 201.6904941176461
    },
    "swing/1/signal": {
      "count": 9,
      "pnl": 43.169776810367495
    },
    "intraday/1/time_limit": {
      "count": 4,
      "pnl": 3.9012854690583048
    },
    "intraday/-1/stop_loss": {
      "count": 14,
      "pnl": -217.93299311752227
    },
    "intraday/1/signal": {
      "count": 2,
      "pnl": -20.23012712399162
    },
    "swing/-1/signal": {
      "count": 8,
      "pnl": 11.91135001511326
    },
    "swing/-1/stop_loss": {
      "count": 10,
      "pnl": -152.62732704123914
    },
    "swing/1/time_limit": {
      "count": 2,
      "pnl": 54.201835504316996
    },
    "intraday/-1/signal": {
      "count": 1,
      "pnl": -9.829110059571315
    },
    "swing/-1/time_limit": {
      "count": 1,
      "pnl": 33.875260683563994
    }
  },
  "past_only_risk_trace_checks": 85,
  "common_events": [
    {
      "entry_timestamp_ms": 1736150400000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -24.306086900156675,
      "child_pnl": -24.306086900156675,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -3.552713678800501e-15,
      "quantity_delta": 3.552713678800501e-15
    },
    {
      "entry_timestamp_ms": 1736326800000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -23.176498822491226,
      "child_pnl": -23.176498822491226,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0
    },
    {
      "entry_timestamp_ms": 1736438400000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -24.124560382280485,
      "child_pnl": -24.124560382280485,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0
    },
    {
      "entry_timestamp_ms": 1736733600000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 0.4047426016243412,
      "child_pnl": -6.003978703088547,
      "parent_exit": "signal",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -6.408721304712889,
      "quantity_delta": 0.0
    },
    {
      "entry_timestamp_ms": 1737129600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -24.592213156650054,
      "child_pnl": -24.57633966956813,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 3.552713678800501e-15,
      "quantity_delta": 0.015873487081918825
    },
    {
      "entry_timestamp_ms": 1737100800000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -5.274998523831063,
      "child_pnl": -5.2715936809894774,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": -8.881784197001252e-16,
      "quantity_delta": 0.003404842841586486
    },
    {
      "entry_timestamp_ms": 1737428400000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 9.275619387453158,
      "child_pnl": 9.269632271792368,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.005987115660790465
    },
    {
      "entry_timestamp_ms": 1737568800000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -23.469167590090056,
      "child_pnl": -23.454018993003988,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -3.552713678800501e-15,
      "quantity_delta": 0.015148597086071192
    },
    {
      "entry_timestamp_ms": 1738029600000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -23.595252831278955,
      "child_pnl": -23.580022850202162,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 3.552713678800501e-15,
      "quantity_delta": 0.0152299810767893
    },
    {
      "entry_timestamp_ms": 1738476000000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -7.883618574505239,
      "child_pnl": -7.878529950850092,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.00508862365514684
    },
    {
      "entry_timestamp_ms": 1738627200000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 19.69107377850802,
      "child_pnl": 19.678363820145936,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 3.552713678800501e-15,
      "quantity_delta": -0.012709958362087548
    },
    {
      "entry_timestamp_ms": 1740427200000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": 32.52558965514329,
      "child_pnl": 32.50459542725765,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 7.105427357601002e-15,
      "quantity_delta": -0.02099422788565164
    },
    {
      "entry_timestamp_ms": 1740484800000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": 4.259099850578972,
      "child_pnl": 4.256350737840392,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 8.881784197001252e-16,
      "quantity_delta": -0.0027491127385808056
    },
    {
      "entry_timestamp_ms": 1741564800000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -24.211749514527373,
      "child_pnl": -24.1961216045584,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -3.552713678800501e-15,
      "quantity_delta": 0.015627909968976894
    },
    {
      "entry_timestamp_ms": 1741698000000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -23.27452598599755,
      "child_pnl": -23.259503023841855,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.015022962155693875
    },
    {
      "entry_timestamp_ms": 1741651200000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -24.21706592991456,
      "child_pnl": -24.20143458836948,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -3.552713678800501e-15,
      "quantity_delta": 0.01563134154508461
    },
    {
      "entry_timestamp_ms": 1741748400000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -23.48503710445138,
      "child_pnl": -23.46987826410131,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.015158840350068203
    },
    {
      "entry_timestamp_ms": 1742284800000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -11.585917263044749,
      "child_pnl": -11.578438923993447,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -3.552713678800501e-15,
      "quantity_delta": 0.007478339051305127
    },
    {
      "entry_timestamp_ms": 1742428800000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -11.92264413247776,
      "child_pnl": -11.914948447001468,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.007695685476292624
    },
    {
      "entry_timestamp_ms": 1742569200000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -5.4191711755975875,
      "child_pnl": -5.415673273920226,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0034979016773615257
    },
    {
      "entry_timestamp_ms": 1742817600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -11.64997011171405,
      "child_pnl": -11.642450428597474,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.007519683116575138
    },
    {
      "entry_timestamp_ms": 1743022800000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -5.266396571971363,
      "child_pnl": -11.733465657180934,
      "parent_exit": "signal",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -6.4746475536894135,
      "quantity_delta": 0.007578468479842115
    },
    {
      "entry_timestamp_ms": 1742803200000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -11.61086607862333,
      "child_pnl": -11.603371635909488,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": 0.007494442713843696
    },
    {
      "entry_timestamp_ms": 1743440400000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -6.607876294180625,
      "child_pnl": -11.300374201956352,
      "parent_exit": "signal",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -4.707305220674191,
      "quantity_delta": 0.01480731289846382
    },
    {
      "entry_timestamp_ms": 1743555600000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -11.351662698070895,
      "child_pnl": -11.33133449909115,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.020328198979743917
    },
    {
      "entry_timestamp_ms": 1743764400000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -6.9105290603399965,
      "child_pnl": -6.898153903190746,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": 0.012375157149252303
    },
    {
      "entry_timestamp_ms": 1743998400000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -11.823211733984007,
      "child_pnl": -11.80203909988619,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.021172634097816
    },
    {
      "entry_timestamp_ms": 1744412400000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -11.415561484895424,
      "child_pnl": -11.39511885798669,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": 0.02044262690873566
    },
    {
      "entry_timestamp_ms": 1744772400000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -1.2976657950773456,
      "child_pnl": -1.2953419761626042,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 2.220446049250313e-16,
      "quantity_delta": 0.0023238189147412047
    },
    {
      "entry_timestamp_ms": 1745611200000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -11.800963867176932,
      "child_pnl": -11.779831073856219,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 3.552713678800501e-15,
      "quantity_delta": 0.021132793320710164
    },
    {
      "entry_timestamp_ms": 1745222400000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 41.15478998550978,
      "child_pnl": 41.081091287614434,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.07369869789534533
    },
    {
      "entry_timestamp_ms": 1745352000000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 13.14428258274593,
      "child_pnl": 13.120744216702562,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.02353836604336834
    },
    {
      "entry_timestamp_ms": 1746586800000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -11.50955301485341,
      "child_pnl": -11.488942070881867,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 3.552713678800501e-15,
      "quantity_delta": 0.02061094397153873
    },
    {
      "entry_timestamp_ms": 1746684000000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -9.84674329642446,
      "child_pnl": -9.829110059571315,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.017633236853145107
    },
    {
      "entry_timestamp_ms": 1746705600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 20.187297612849186,
      "child_pnl": 20.151146837966937,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": -3.552713678800501e-15,
      "quantity_delta": -0.03615077488224472
    },
    {
      "entry_timestamp_ms": 1747324800000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": 1.345077169054379,
      "child_pnl": 1.3426684473487673,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.0024087217056116828
    },
    {
      "entry_timestamp_ms": 1749513600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -23.436516063996667,
      "child_pnl": -23.39454669134948,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 3.552713678800501e-15,
      "quantity_delta": 0.041969372647184144
    },
    {
      "entry_timestamp_ms": 1750118400000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 6.770482237738533,
      "child_pnl": 6.758357872015367,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": -0.012124365723168218
    },
    {
      "entry_timestamp_ms": 1750622400000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -11.826610825708336,
      "child_pnl": -11.805432104624455,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.021178721083881413
    },
    {
      "entry_timestamp_ms": 1750694400000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -22.973912587550977,
      "child_pnl": -22.932771630596548,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.04114095695442899
    },
    {
      "entry_timestamp_ms": 1752480000000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -11.679748584063786,
      "child_pnl": -11.65883285924311,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": 0.02091572482067683
    },
    {
      "entry_timestamp_ms": 1752192000000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 1.319525831865969,
      "child_pnl": 1.3171628666878714,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 6.661338147750939e-16,
      "quantity_delta": -0.0023629651780983085
    },
    {
      "entry_timestamp_ms": 1752206400000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -1.5974846988696538,
      "child_pnl": -1.5946239737327796,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 2.220446049250313e-16,
      "quantity_delta": 0.002860725136873965
    },
    {
      "entry_timestamp_ms": 1753909200000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -1.7372396805780732,
      "child_pnl": -12.351597173141526,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": -10.636516023411975,
      "quantity_delta": 0.022158530848521707
    },
    {
      "entry_timestamp_ms": 1754092800000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -5.465559280691765,
      "child_pnl": -5.449780069924191,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.01577921076757338
    },
    {
      "entry_timestamp_ms": 1754884800000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -11.654700559496971,
      "child_pnl": -11.621053138049929,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0336474214470428
    },
    {
      "entry_timestamp_ms": 1755144000000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -11.676221593073251,
      "child_pnl": -11.642512039846581,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0337095532266698
    },
    {
      "entry_timestamp_ms": 1755129600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -11.738282046581746,
      "child_pnl": -11.704393323223359,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": 0.03388872335838933
    },
    {
      "entry_timestamp_ms": 1755504000000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -11.426757865941404,
      "child_pnl": -11.393768520936279,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.032989345005125514
    },
    {
      "entry_timestamp_ms": 1755716400000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -11.264706573139613,
      "child_pnl": -11.232185074401071,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.032521498738541155
    },
    {
      "entry_timestamp_ms": 1755633600000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -11.435824681018438,
      "child_pnl": -11.402809159884075,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": 0.03301552113436479
    },
    {
      "entry_timestamp_ms": 1755648000000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -11.463007024951889,
      "child_pnl": -11.429913027688722,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.033093997263167196
    },
    {
      "entry_timestamp_ms": 1756256400000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -11.21218830171662,
      "child_pnl": -11.17981842458374,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": 0.03236987713287931
    },
    {
      "entry_timestamp_ms": 1756180800000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -11.543959288757241,
      "child_pnl": -11.51063158021824,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.03332770853900158
    },
    {
      "entry_timestamp_ms": 1756724400000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -11.282336277236489,
      "child_pnl": -11.249763881087024,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.03257239614946528
    },
    {
      "entry_timestamp_ms": 1757098800000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -10.141822876467625,
      "child_pnl": -11.261509078367222,
      "parent_exit": "signal",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -1.1522926049155782,
      "quantity_delta": 0.032606403015980945
    },
    {
      "entry_timestamp_ms": 1758916800000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -5.632185301405825,
      "child_pnl": -5.615247772484466,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.01693752892135958
    },
    {
      "entry_timestamp_ms": 1758844800000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -6.371096828482279,
      "child_pnl": -6.3519371895467,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.01915963893557926
    },
    {
      "entry_timestamp_ms": 1759334400000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 13.845012017637101,
      "child_pnl": 13.803376261901807,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": -0.041635755735292435
    },
    {
      "entry_timestamp_ms": 1759348800000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 13.230319998914247,
      "child_pnl": 13.190532790996125,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.03978720791812229
    },
    {
      "entry_timestamp_ms": 1759377600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 8.475224633329677,
      "child_pnl": 8.449737303872284,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.02548732945739296
    },
    {
      "entry_timestamp_ms": 1759435200000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": 0.3949643638515654,
      "child_pnl": 0.39377659747357174,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 2.7755575615628914e-16,
      "quantity_delta": -0.0011877663779939485
    },
    {
      "entry_timestamp_ms": 1760277600000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -11.20807946224592,
      "child_pnl": -11.174373687331657,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.033705774914261966
    },
    {
      "entry_timestamp_ms": 1760155200000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -5.052715345967742,
      "child_pnl": -5.037520442440271,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.015194903527470771
    },
    {
      "entry_timestamp_ms": 1760328000000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -10.104287447564799,
      "child_pnl": 3.9428550200778,
      "parent_exit": "signal",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 14.059035481742974,
      "quantity_delta": -0.011893014100376131
    },
    {
      "entry_timestamp_ms": 1760500800000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 0.16574324709327923,
      "child_pnl": 0.330976027889217,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 1.3877787807814457e-16,
      "quantity_delta": 0.16523278079593762
    },
    {
      "entry_timestamp_ms": 1760623200000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 53.68708723832734,
      "child_pnl": 53.605342898308045,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": -7.105427357601002e-15,
      "quantity_delta": -0.08174434001928432
    },
    {
      "entry_timestamp_ms": 1760644800000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -0.6582691222045269,
      "child_pnl": -0.657266836967654,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0010022852368729573
    },
    {
      "entry_timestamp_ms": 1760659200000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -0.7646893073153507,
      "child_pnl": -0.7635249859494179,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.0011643213659328078
    },
    {
      "entry_timestamp_ms": 1761069600000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 22.267496072031054,
      "child_pnl": 30.838596065291117,
      "parent_exit": "signal",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 8.61812666161401,
      "quantity_delta": -0.04702666835394709
    },
    {
      "entry_timestamp_ms": 1761537600000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -11.680137307193778,
      "child_pnl": -11.672793049904048,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.007344257289730649
    },
    {
      "entry_timestamp_ms": 1761494400000,
      "sleeve": "swing",
      "direction": 1,
      "parent_pnl": -7.274312148602354,
      "child_pnl": -7.269738193808838,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.004573954793515966
    },
    {
      "entry_timestamp_ms": 1761930000000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -16.766213091441713,
      "child_pnl": -16.755670802470316,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.010542288971397085
    },
    {
      "entry_timestamp_ms": 1762286400000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -11.683775486836687,
      "child_pnl": -11.676428941925954,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 1.7763568394002505e-15,
      "quantity_delta": 0.007346544910731723
    },
    {
      "entry_timestamp_ms": 1762376400000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 38.615412598393675,
      "child_pnl": 38.59113193130792,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 7.105427357601002e-15,
      "quantity_delta": -0.02428066708576182
    },
    {
      "entry_timestamp_ms": 1762560000000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 7.0042840597984934,
      "child_pnl": 6.999879893741829,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 2.6645352591003757e-15,
      "quantity_delta": -0.004404166056667158
    },
    {
      "entry_timestamp_ms": 1763622000000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": 76.26599643754939,
      "child_pnl": 76.21804177010293,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.047954667446461485
    },
    {
      "entry_timestamp_ms": 1763121600000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": 33.89657423115739,
      "child_pnl": 33.875260683563994,
      "parent_exit": "time_limit",
      "child_exit": "time_limit",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": -0.021313547593393878
    },
    {
      "entry_timestamp_ms": 1763712000000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -6.593712631387968,
      "child_pnl": -6.5895666251565475,
      "parent_exit": "signal",
      "child_exit": "signal",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.004146006231420252
    },
    {
      "entry_timestamp_ms": 1764572400000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -11.333673305151256,
      "child_pnl": -11.326546898106407,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 3.552713678800501e-15,
      "quantity_delta": 0.007126407044845351
    },
    {
      "entry_timestamp_ms": 1764748800000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -22.910309511396896,
      "child_pnl": -22.89590392666671,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -3.552713678800501e-15,
      "quantity_delta": 0.014405584730191379
    },
    {
      "entry_timestamp_ms": 1764882000000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -10.252813428684203,
      "child_pnl": -11.661565696495558,
      "parent_exit": "signal",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -1.4160894611043364,
      "quantity_delta": 0.0073371932929813255
    },
    {
      "entry_timestamp_ms": 1765429200000,
      "sleeve": "intraday",
      "direction": 1,
      "parent_pnl": -11.449301842340622,
      "child_pnl": -11.440429631966104,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": -1.7763568394002505e-15,
      "quantity_delta": 0.008872210374519796
    },
    {
      "entry_timestamp_ms": 1765893600000,
      "sleeve": "intraday",
      "direction": -1,
      "parent_pnl": -11.45187693063749,
      "child_pnl": -11.443002724794134,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 0.0,
      "quantity_delta": 0.008874205843355298
    },
    {
      "entry_timestamp_ms": 1765828800000,
      "sleeve": "swing",
      "direction": -1,
      "parent_pnl": -23.226747116436886,
      "child_pnl": -23.208748413147344,
      "parent_exit": "stop_loss",
      "child_exit": "stop_loss",
      "repriced_parent_qty_delta": 3.552713678800501e-15,
      "quantity_delta": 0.01799870328953901
    }
  ],
  "channel_only_comparison": {
    "count": 8,
    "parent_pnl": -21.438197625791293,
    "child_pnl": -29.531039424861223,
    "new_exit_counts": {
      "time_limit": 3,
      "stop_loss": 4,
      "signal": 1
    },
    "events": [
      {
        "entry_timestamp_ms": 1736733600000,
        "sleeve": "intraday",
        "direction": -1,
        "parent_pnl": 0.4047426016243412,
        "child_pnl": -6.003978703088547,
        "parent_exit": "signal",
        "child_exit": "time_limit",
        "repriced_parent_qty_delta": -6.408721304712889,
        "quantity_delta": 0.0
      },
      {
        "entry_timestamp_ms": 1743022800000,
        "sleeve": "intraday",
        "direction": 1,
        "parent_pnl": -5.266396571971363,
        "child_pnl": -11.733465657180934,
        "parent_exit": "signal",
        "child_exit": "stop_loss",
        "repriced_parent_qty_delta": -6.4746475536894135,
        "quantity_delta": 0.007578468479842115
      },
      {
        "entry_timestamp_ms": 1743440400000,
        "sleeve": "intraday",
        "direction": -1,
        "parent_pnl": -6.607876294180625,
        "child_pnl": -11.300374201956352,
        "parent_exit": "signal",
        "child_exit": "stop_loss",
        "repriced_parent_qty_delta": -4.707305220674191,
        "quantity_delta": 0.01480731289846382
      },
      {
        "entry_timestamp_ms": 1753909200000,
        "sleeve": "intraday",
        "direction": 1,
        "parent_pnl": -1.7372396805780732,
        "child_pnl": -12.351597173141526,
        "parent_exit": "signal",
        "child_exit": "signal",
        "repriced_parent_qty_delta": -10.636516023411975,
        "quantity_delta": 0.022158530848521707
      },
      {
        "entry_timestamp_ms": 1757098800000,
        "sleeve": "intraday",
        "direction": 1,
        "parent_pnl": -10.141822876467625,
        "child_pnl": -11.261509078367222,
        "parent_exit": "signal",
        "child_exit": "stop_loss",
        "repriced_parent_qty_delta": -1.1522926049155782,
        "quantity_delta": 0.032606403015980945
      },
      {
        "entry_timestamp_ms": 1760328000000,
        "sleeve": "intraday",
        "direction": -1,
        "parent_pnl": -10.104287447564799,
        "child_pnl": 3.9428550200778,
        "parent_exit": "signal",
        "child_exit": "time_limit",
        "repriced_parent_qty_delta": 14.059035481742974,
        "quantity_delta": -0.011893014100376131
      },
      {
        "entry_timestamp_ms": 1761069600000,
        "sleeve": "intraday",
        "direction": -1,
        "parent_pnl": 22.267496072031054,
        "child_pnl": 30.838596065291117,
        "parent_exit": "signal",
        "child_exit": "time_limit",
        "repriced_parent_qty_delta": 8.61812666161401,
        "quantity_delta": -0.04702666835394709
      },
      {
        "entry_timestamp_ms": 1764882000000,
        "sleeve": "intraday",
        "direction": 1,
        "parent_pnl": -10.252813428684203,
        "child_pnl": -11.661565696495558,
        "parent_exit": "signal",
        "child_exit": "stop_loss",
        "repriced_parent_qty_delta": -1.4160894611043364,
        "quantity_delta": 0.0073371932929813255
      }
    ]
  }
}
```
